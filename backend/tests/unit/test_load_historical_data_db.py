"""Offline tests for the database / fetch / orchestration layers of
db/load_historical_data.py. psycopg2, yfinance and the filesystem are faked;
progress files go to tmp_path."""

import logging
from datetime import date, timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd
import psycopg2
import pytest

import db.load_historical_data as ldh
from db.load_historical_data import (
    HistoricalDataFetcher,
    HistoricalDataLoader,
    LoadProgress,
    OHLCVRecord,
    PostgresClient,
    StockListLoader,
    StockMetadata,
)

RETRIES = ldh.RETRY_CONFIG["max_retries"]


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.closed = False

    def execute(self, *args):
        self.conn.executed.append(args)
        if self.conn.fail_execute:
            raise psycopg2.Error("boom")

    def fetchone(self):
        return self.conn.one

    def fetchall(self):
        return self.conn.rows

    def close(self):
        self.closed = True
        self.conn.cursors_closed += 1


class FakeConn:
    def __init__(self, one=None, rows=(), fail_execute=False):
        self.one = one
        self.rows = list(rows)
        self.fail_execute = fail_execute
        self.executed = []
        self.commits = 0
        self.rollbacks = 0
        self.closed = False
        self.cursors_closed = 0
        self.last_cursor = None

    def cursor(self):
        self.last_cursor = FakeCursor(self)
        return self.last_cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


@pytest.fixture
def no_sleep(monkeypatch):
    sleeps = []
    monkeypatch.setattr(ldh.time, "sleep", sleeps.append)
    return sleeps


def client_with(conn):
    c = PostgresClient()
    c.conn = conn
    return c


@pytest.mark.unit
class TestPostgresClientConnect:
    def test_defaults(self):
        c = PostgresClient()
        assert (c.dbname, c.user, c.password, c.host, c.port, c.conn) == (
            "market_data",
            "umashankar",
            "",
            "localhost",
            5432,
            None,
        )

    def test_success_passes_every_parameter(self, monkeypatch):
        seen = []
        sentinel = object()
        monkeypatch.setattr(ldh.psycopg2, "connect", lambda **kw: seen.append(kw) or sentinel)
        c = PostgresClient(dbname="d", user="u", password="p", host="h", port=1)
        assert c.connect() is True
        assert c.conn is sentinel
        assert seen == [{"dbname": "d", "user": "u", "password": "p", "host": "h", "port": 1}]

    def test_retries_with_exponential_backoff_then_succeeds(self, monkeypatch, no_sleep):
        calls = []

        def connect(**kw):
            calls.append(1)
            if len(calls) < 3:
                raise psycopg2.OperationalError("down")
            return object()

        monkeypatch.setattr(ldh.psycopg2, "connect", connect)
        assert PostgresClient().connect() is True
        assert len(calls) == 3
        cfg = ldh.RETRY_CONFIG
        assert no_sleep == [
            min(cfg["initial_backoff"] * cfg["backoff_factor"] ** i, cfg["max_backoff"]) for i in range(2)
        ]

    def test_gives_up_after_max_retries_without_final_sleep(self, monkeypatch, no_sleep):
        calls = []

        def connect(**kw):
            calls.append(1)
            raise psycopg2.OperationalError("down")

        monkeypatch.setattr(ldh.psycopg2, "connect", connect)
        assert PostgresClient().connect() is False
        assert len(calls) == RETRIES
        assert len(no_sleep) == RETRIES - 1

    def test_backoff_is_capped_at_max_backoff(self, monkeypatch, no_sleep):
        monkeypatch.setattr(ldh, "RETRY_CONFIG", dict(ldh.RETRY_CONFIG, max_retries=4, max_backoff=1.5))
        monkeypatch.setattr(ldh.psycopg2, "connect", lambda **kw: (_ for _ in ()).throw(psycopg2.Error("x")))
        assert PostgresClient().connect() is False
        assert no_sleep and max(no_sleep) == 1.5
        assert len(no_sleep) == 3

    def test_zero_retries_returns_false_without_connecting(self, monkeypatch):
        monkeypatch.setattr(ldh, "RETRY_CONFIG", dict(ldh.RETRY_CONFIG, max_retries=0))
        monkeypatch.setattr(ldh.psycopg2, "connect", lambda **kw: pytest.fail("must not connect"))
        assert PostgresClient().connect() is False

    def test_close_only_when_connected(self):
        conn = FakeConn()
        client_with(conn).close()
        assert conn.closed
        PostgresClient().close()  # conn None: no error


@pytest.mark.unit
class TestPostgresClientQueries:
    def test_execute_with_params_commits_and_closes_cursor(self):
        conn = FakeConn()
        cur = client_with(conn).execute("SELECT %s", (1,))
        assert conn.executed == [("SELECT %s", (1,))]
        assert conn.commits == 1 and cur.closed

    def test_execute_without_params_omits_them(self):
        conn = FakeConn()
        client_with(conn).execute("SELECT 1")
        assert conn.executed == [("SELECT 1",)]

    def test_execute_error_rolls_back_closes_and_reraises(self):
        conn = FakeConn(fail_execute=True)
        with pytest.raises(psycopg2.Error):
            client_with(conn).execute("SELECT 1")
        assert conn.rollbacks == 1 and conn.commits == 0 and conn.last_cursor.closed

    def test_execute_error_before_cursor_exists_still_rolls_back_and_raises(self):
        class Bad(FakeConn):
            def cursor(self):
                raise psycopg2.Error("no cursor")

        conn = Bad()
        with pytest.raises(psycopg2.Error):
            client_with(conn).execute("SELECT 1")
        assert conn.rollbacks == 1

    @pytest.mark.parametrize("method,args", [("get_stock_id", ("T", 1)), ("get_market_id", ("usa",))])
    def test_lookup_returns_first_column_or_none(self, method, args):
        assert getattr(client_with(FakeConn(one=(42,))), method)(*args) == 42
        assert getattr(client_with(FakeConn(one=None)), method)(*args) is None
        assert getattr(client_with(FakeConn(one=(0,))), method)(*args) == 0

    def test_lookup_passes_parameters_in_order(self):
        conn = FakeConn(one=(1,))
        client_with(conn).get_stock_id("AAA", 9)
        assert conn.executed[0][1] == ("AAA", 9)
        client_with(conn).get_market_id("usa")
        assert conn.executed[1][1] == ("usa",)

    @pytest.mark.parametrize("method,args", [("get_stock_id", ("T", 1)), ("get_market_id", ("usa",))])
    def test_lookup_db_error_returns_none(self, method, args):
        assert getattr(client_with(FakeConn(fail_execute=True)), method)(*args) is None

    def test_insert_stock_returns_id_and_binds_metadata_in_order(self):
        conn = FakeConn(one=(5,))
        meta = StockMetadata("AAA", "usa", name="Aaa", sector="S", industry="I", market_cap_usd=1.5, currency="USD")
        assert client_with(conn).insert_stock("AAA", 3, meta) == 5
        assert conn.executed[0][1] == ("AAA", "Aaa", 3, "S", "I", 1.5, "USD")
        assert conn.commits == 1 and conn.last_cursor.closed

    def test_insert_stock_no_row_returns_none(self):
        assert client_with(FakeConn(one=None)).insert_stock("A", 1, StockMetadata("A", "usa")) is None

    def test_insert_stock_error_rolls_back_and_returns_none(self):
        conn = FakeConn(fail_execute=True)
        assert client_with(conn).insert_stock("A", 1, StockMetadata("A", "usa")) is None
        assert conn.rollbacks == 1 and conn.commits == 0

    def test_bulk_insert_empty_is_noop(self, monkeypatch):
        monkeypatch.setattr(ldh, "execute_values", lambda *a, **k: pytest.fail("no insert for empty"))
        conn = FakeConn()
        assert client_with(conn).bulk_insert_ohlcv([]) == 0
        assert conn.commits == 0

    def test_bulk_insert_sends_tuples_and_commits(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            ldh, "execute_values", lambda cur, sql, data, page_size: calls.append((sql, data, page_size))
        )
        recs = [OHLCVRecord(1, date(2020, 1, i), 1.0, 2.0, 0.5, 1.5, 10, 1.4) for i in (1, 2)]
        conn = FakeConn()
        assert client_with(conn).bulk_insert_ohlcv(recs) == 2
        sql, data, page = calls[0]
        assert data == [r.to_tuple() for r in recs] and page == 1000
        assert "ON CONFLICT (stock_id, date) DO UPDATE" in sql
        assert conn.commits == 1 and conn.last_cursor.closed

    def test_bulk_insert_error_rolls_back_returns_zero(self, monkeypatch):
        def boom(*a, **k):
            raise psycopg2.Error("bad")

        monkeypatch.setattr(ldh, "execute_values", boom)
        conn = FakeConn()
        rec = OHLCVRecord(1, date(2020, 1, 1), 1, 1, 1, 1, 1, 1)
        assert client_with(conn).bulk_insert_ohlcv([rec]) == 0
        assert conn.rollbacks == 1 and conn.commits == 0

    def test_existing_dates_is_a_set_of_first_columns(self):
        conn = FakeConn(rows=[(date(2020, 1, 1),), (date(2020, 1, 2),), (date(2020, 1, 1),)])
        assert client_with(conn).get_existing_dates(4) == {date(2020, 1, 1), date(2020, 1, 2)}
        assert conn.executed[0][1] == (4,)

    def test_existing_dates_error_is_empty_set(self):
        assert client_with(FakeConn(fail_execute=True)).get_existing_dates(1) == set()


def frame(n=3):
    idx = pd.date_range("2020-01-01", periods=n)
    return pd.DataFrame({"Close": np.arange(1.0, n + 1)}, index=idx)


@pytest.mark.unit
class TestFetchOHLCV:
    def make(self, monkeypatch, download):
        monkeypatch.setattr(ldh, "HAS_YF", True)
        monkeypatch.setattr(ldh, "yf", SimpleNamespace(download=download), raising=False)
        monkeypatch.setattr(ldh.time, "sleep", lambda s: None)
        return HistoricalDataFetcher(db=None, market="usa")

    def test_unknown_market_keyerror(self):
        with pytest.raises(KeyError):
            HistoricalDataFetcher(db=None, market="mars")

    def test_init_loads_market_config(self):
        f = HistoricalDataFetcher(db="D", market="india")
        assert f.db == "D" and f.market == "india" and f.market_config["currency"] == "INR" and f.session is None

    def test_no_yfinance_returns_none(self, monkeypatch):
        monkeypatch.setattr(ldh, "HAS_YF", False)
        assert HistoricalDataFetcher(None, "usa").fetch_ohlcv("A", date(2020, 1, 1), date(2020, 2, 1)) is None

    def test_passes_dates_as_strings_and_timeout(self, monkeypatch):
        seen = []

        def download(ticker, **kw):
            seen.append((ticker, kw))
            return frame()

        f = self.make(monkeypatch, download)
        out = f.fetch_ohlcv("AAA", date(2020, 1, 1), date(2020, 2, 1))
        assert len(out) == 3
        assert seen == [
            (
                "AAA",
                {"start": "2020-01-01", "end": "2020-02-01", "progress": False, "timeout": ldh.RETRY_CONFIG["timeout"]},
            )
        ]

    def test_empty_frame_returns_none_without_retry(self, monkeypatch):
        calls = []
        f = self.make(monkeypatch, lambda *a, **k: calls.append(1) or pd.DataFrame())
        assert f.fetch_ohlcv("A", date(2020, 1, 1), date(2020, 2, 1)) is None
        assert len(calls) == 1

    def test_non_datetime_index_is_converted(self, monkeypatch):
        df = pd.DataFrame({"Close": [1.0, 2.0]}, index=["2020-01-01", "2020-01-02"])
        f = self.make(monkeypatch, lambda *a, **k: df)
        out = f.fetch_ohlcv("A", date(2020, 1, 1), date(2020, 2, 1))
        assert isinstance(out.index, pd.DatetimeIndex)
        assert out.index[0] == pd.Timestamp("2020-01-01")

    def test_retries_then_succeeds_with_sleeps(self, monkeypatch):
        calls, sleeps = [], []

        def download(*a, **k):
            calls.append(1)
            if len(calls) < RETRIES:
                raise RuntimeError("flaky")
            return frame()

        f = self.make(monkeypatch, download)
        monkeypatch.setattr(ldh.time, "sleep", sleeps.append)
        assert f.fetch_ohlcv("A", date(2020, 1, 1), date(2020, 2, 1)) is not None
        assert len(calls) == RETRIES and len(sleeps) == RETRIES - 1
        assert sleeps[0] == ldh.RETRY_CONFIG["initial_backoff"]
        assert sleeps[1] == ldh.RETRY_CONFIG["initial_backoff"] * ldh.RETRY_CONFIG["backoff_factor"]

    def test_gives_up_after_max_retries(self, monkeypatch):
        calls, sleeps = [], []

        def download(*a, **k):
            calls.append(1)
            raise RuntimeError("down")

        f = self.make(monkeypatch, download)
        monkeypatch.setattr(ldh.time, "sleep", sleeps.append)
        assert f.fetch_ohlcv("A", date(2020, 1, 1), date(2020, 2, 1)) is None
        assert len(calls) == RETRIES and len(sleeps) == RETRIES - 1

    def test_zero_retries_never_downloads(self, monkeypatch):
        f = self.make(monkeypatch, lambda *a, **k: pytest.fail("no download"))
        monkeypatch.setattr(ldh, "RETRY_CONFIG", dict(ldh.RETRY_CONFIG, max_retries=0))
        assert f.fetch_ohlcv("A", date(2020, 1, 1), date(2020, 2, 1)) is None


@pytest.mark.unit
class TestValidateBoundaries:
    @pytest.fixture
    def f(self):
        return HistoricalDataFetcher(None, "usa")

    def bars(self, n, **over):
        idx = pd.bdate_range("2020-01-01", periods=n)
        d = {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 10}
        d.update(over)
        return pd.DataFrame({k: np.full(n, v, dtype=float) for k, v in d.items()}, index=idx)

    def test_exactly_min_records_kept_one_less_rejected(self, f):
        m = ldh.VALIDATION_CONFIG["min_records_per_stock"]
        assert len(f.validate_ohlcv(self.bars(m), "A")) == m
        assert f.validate_ohlcv(self.bars(m - 1), "A") is None

    def test_close_equal_to_high_or_low_is_valid(self, f):
        m = ldh.VALIDATION_CONFIG["min_records_per_stock"]
        assert len(f.validate_ohlcv(self.bars(m, Close=101.0), "A")) == m
        assert len(f.validate_ohlcv(self.bars(m, Close=99.0), "A")) == m

    def test_high_equal_low_is_valid(self, f):
        m = ldh.VALIDATION_CONFIG["min_records_per_stock"]
        assert len(f.validate_ohlcv(self.bars(m, High=100.0, Low=100.0), "A")) == m

    def test_close_outside_range_and_nonpositive_dropped(self, f):
        m = ldh.VALIDATION_CONFIG["min_records_per_stock"]
        df = self.bars(m + 4)
        df.iloc[1, df.columns.get_loc("Close")] = 101.5  # above high
        df.iloc[2, df.columns.get_loc("Close")] = 98.5  # below low
        df.iloc[3, df.columns.get_loc("Open")] = -1.0
        df.iloc[4, df.columns.get_loc("Volume")] = -5.0
        out = f.validate_ohlcv(df, "A")
        assert len(out) == m  # 4 dropped
        assert df.index[1] not in out.index and df.index[4] not in out.index

    def test_zero_volume_is_kept(self, f):
        m = ldh.VALIDATION_CONFIG["min_records_per_stock"]
        assert len(f.validate_ohlcv(self.bars(m, Volume=0.0), "A")) == m

    def test_price_change_just_under_limit_kept_over_limit_dropped(self, f):
        m = ldh.VALIDATION_CONFIG["min_records_per_stock"]
        limit = ldh.VALIDATION_CONFIG["max_price_change_pct"] / 100  # 5.0 => 500%

        def with_jump(factor):
            df = self.bars(m + 5)
            for col in ("Open", "High", "Low", "Close"):
                df.iloc[m:, df.columns.get_loc(col)] = df[col].iloc[0] * factor
            return df

        kept = f.validate_ohlcv(with_jump(1 + limit - 0.01), "A")
        assert len(kept) == m + 5
        exactly_at_limit = f.validate_ohlcv(with_jump(1 + limit), "A")  # +500.0% is not "> 500%"
        assert len(exactly_at_limit) == m + 5
        dropped = f.validate_ohlcv(with_jump(1 + limit + 0.01), "A")
        assert len(dropped) == m + 4  # only the spike bar itself


@pytest.mark.unit
class TestStockListLoader:
    def test_csv_prefers_lowercase_then_titlecase_columns(self, tmp_path):
        p = tmp_path / "a.csv"
        p.write_text("ticker,name\nAAA,Alpha\nBBB,\n")
        assert StockListLoader.load_from_csv(str(p), "usa") == [("AAA", "Alpha"), ("BBB", "")]

    def test_csv_missing_name_column_gives_empty_name(self, tmp_path):
        p = tmp_path / "a.csv"
        p.write_text("Ticker\nAAA\n")
        assert StockListLoader.load_from_csv(str(p), "usa") == [("AAA", "")]

    def test_predefined_known_and_unknown(self):
        india = StockListLoader.load_predefined("india")
        assert ("RELIANCE", "Reliance Industries") in india and len(india) == 5
        assert ("AAPL", "Apple Inc") in StockListLoader.load_predefined("usa")
        assert StockListLoader.load_predefined("japan") == []


class FakeDB:
    def __init__(self, market_id=1, stock_id=10, existing=(), insert_result=11, inserted=None):
        self.market_id = market_id
        self.stock_id = stock_id
        self.existing = set(existing)
        self.insert_result = insert_result
        self.inserted = inserted
        self.bulk_calls = []
        self.insert_calls = []

    def get_market_id(self, name):
        return self.market_id

    def get_stock_id(self, ticker, market_id):
        return self.stock_id

    def insert_stock(self, ticker, market_id, metadata):
        self.insert_calls.append((ticker, market_id, metadata))
        return self.insert_result

    def get_existing_dates(self, stock_id):
        return self.existing

    def bulk_insert_ohlcv(self, records):
        self.bulk_calls.append(records)
        return len(records) if self.inserted is None else self.inserted


class FakeFetcher:
    def __init__(self, df=None, validated="same", raises=None):
        self.df = df if df is not None else frame(2).assign(Open=1.0, High=2.0, Low=0.5, Volume=5.0)
        self.validated = validated
        self.raises = raises
        self.fetch_args = []
        self.validate_args = []

    def fetch_ohlcv(self, ticker, start, end):
        self.fetch_args.append((ticker, start, end))
        if self.raises:
            raise self.raises
        return self.df

    def validate_ohlcv(self, df, ticker):
        self.validate_args.append(ticker)
        return df if self.validated == "same" else self.validated

    def convert_to_ohlcv_records(self, df, stock_id):
        return HistoricalDataFetcher(None, "usa").convert_to_ohlcv_records(df, stock_id)


@pytest.fixture
def in_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def make_loader(db, in_tmp, **kw):
    return HistoricalDataLoader(db, ["usa"], **kw)


@pytest.mark.unit
class TestLoaderInit:
    def test_defaults_and_five_year_window(self, in_tmp):
        loader = HistoricalDataLoader(FakeDB(), ["india"])
        assert (loader.workers, loader.batch_size, loader.resume) == (4, 500, False)
        assert loader.end_date == date.today()
        assert loader.start_date == loader.end_date - timedelta(days=365 * 5)
        assert (in_tmp / "data" / "progress").is_dir()


@pytest.mark.unit
class TestLoadStock:
    def run(self, loader, fetcher, dry_run=False, market="usa", name="Aaa"):
        return loader._load_stock("AAA", name, market, 1, fetcher, dry_run)

    def test_existing_stock_new_history_fetches_from_start_date(self, in_tmp):
        db, fetcher = FakeDB(), FakeFetcher()
        loader = make_loader(db, in_tmp)
        assert self.run(loader, fetcher) == 2
        assert fetcher.fetch_args == [("AAA", loader.start_date, loader.end_date)]
        assert len(db.bulk_calls[0]) == 2 and db.insert_calls == []

    def test_missing_stock_is_created_with_market_currency(self, in_tmp):
        db = FakeDB(stock_id=None, insert_result=77)
        loader = make_loader(db, in_tmp)
        assert self.run(loader, FakeFetcher(), market="india", name="Nm") == 2
        ticker, market_id, meta = db.insert_calls[0]
        assert (ticker, market_id) == ("AAA", 1)
        assert (meta.ticker, meta.market_name, meta.name, meta.currency) == ("AAA", "india", "Nm", "INR")
        assert {r.stock_id for r in db.bulk_calls[0]} == {77}

    def test_failed_stock_creation_returns_zero(self, in_tmp):
        db = FakeDB(stock_id=None, insert_result=None)
        fetcher = FakeFetcher()
        assert self.run(make_loader(db, in_tmp), fetcher) == 0
        assert fetcher.fetch_args == []

    def test_incremental_starts_day_after_latest_date(self, in_tmp):
        loader = make_loader(FakeDB(), in_tmp)
        last = loader.end_date - timedelta(days=10)
        loader.db.existing = {last - timedelta(days=5), last}
        fetcher = FakeFetcher()
        self.run(loader, fetcher)
        assert fetcher.fetch_args[0][1] == last + timedelta(days=1)

    def test_up_to_date_when_next_day_reaches_end_date(self, in_tmp):
        loader = make_loader(FakeDB(), in_tmp)
        fetcher = FakeFetcher()
        # latest = end - 1 -> fetch_start == end_date -> skip (>= boundary)
        loader.db.existing = {loader.end_date - timedelta(days=1)}
        assert self.run(loader, fetcher) == 0 and fetcher.fetch_args == []
        # latest = end - 2 -> fetch_start == end - 1 -> still fetches
        loader.db.existing = {loader.end_date - timedelta(days=2)}
        assert self.run(loader, fetcher) == 2 and len(fetcher.fetch_args) == 1

    def test_fetch_none_and_validation_none_return_zero(self, in_tmp):
        loader = make_loader(FakeDB(), in_tmp)

        class NoneFetcher(FakeFetcher):
            def fetch_ohlcv(self, *a):
                return None

        assert self.run(loader, NoneFetcher()) == 0
        assert self.run(loader, FakeFetcher(validated=None)) == 0
        assert loader.db.bulk_calls == []

    def test_dry_run_counts_records_without_inserting(self, in_tmp):
        db = FakeDB()
        assert self.run(make_loader(db, in_tmp), FakeFetcher(), dry_run=True) == 2
        assert db.bulk_calls == []

    def test_returns_db_inserted_count_not_record_count(self, in_tmp):
        assert self.run(make_loader(FakeDB(inserted=1), in_tmp), FakeFetcher()) == 1

    def test_any_exception_is_swallowed_as_zero(self, in_tmp):
        assert self.run(make_loader(FakeDB(), in_tmp), FakeFetcher(raises=RuntimeError("x"))) == 0


@pytest.mark.unit
class TestLoadMarket:
    @pytest.fixture(autouse=True)
    def quick(self, monkeypatch):
        monkeypatch.setattr(ldh, "HistoricalDataFetcher", lambda db, market: FakeFetcher())

    def test_unknown_market_in_db_returns_none(self, in_tmp):
        assert make_loader(FakeDB(market_id=None), in_tmp).load_market("usa") is None

    def test_market_without_predefined_stocks_returns_none(self, in_tmp):
        assert make_loader(FakeDB(), in_tmp).load_market("japan") is None

    def test_loads_all_predefined_stocks_and_saves_progress(self, in_tmp):
        db = FakeDB()
        loader = make_loader(db, in_tmp, workers=2)
        progress = loader.load_market("usa")
        assert progress.market == "usa" and progress.total_stocks == 5
        assert progress.completed_stocks == 5
        assert progress.total_records == 10 and progress.inserted_records == 10
        assert progress.failed_stocks == []
        saved = LoadProgress.load(in_tmp / "data" / "progress" / "usa_progress.json")
        assert saved.completed_stocks == 5 and saved.inserted_records == 10

    def test_zero_record_stocks_complete_but_add_nothing(self, in_tmp, monkeypatch):
        monkeypatch.setattr(ldh, "HistoricalDataFetcher", lambda db, market: FakeFetcher(validated=None))
        progress = make_loader(FakeDB(), in_tmp).load_market("usa")
        assert progress.completed_stocks == 5 and progress.total_records == 0 and progress.inserted_records == 0

    def test_future_exception_is_recorded_as_failure(self, in_tmp, monkeypatch):
        def explode(self, ticker, *a, **k):
            if ticker == "MSFT":
                raise RuntimeError("worker died")
            return 1

        monkeypatch.setattr(HistoricalDataLoader, "_load_stock", explode)
        progress = make_loader(FakeDB(), in_tmp).load_market("usa")
        assert progress.failed_stocks == ["MSFT"]
        assert progress.completed_stocks == 4 and progress.inserted_records == 4

    def test_only_missing_skips_previously_failed_tickers(self, in_tmp):
        loader = make_loader(FakeDB(), in_tmp, resume=True)
        prior = LoadProgress(market="usa", total_stocks=5, completed_stocks=0, failed_stocks=["AAPL"])
        prior.save(in_tmp / "data" / "progress" / "usa_progress.json")
        progress = loader.load_market("usa", only_missing=True)
        assert progress.completed_stocks == 4  # AAPL skipped

    def test_failed_tickers_not_skipped_without_only_missing(self, in_tmp):
        loader = make_loader(FakeDB(), in_tmp, resume=True)
        LoadProgress(market="usa", total_stocks=5, failed_stocks=["AAPL"]).save(
            in_tmp / "data" / "progress" / "usa_progress.json"
        )
        assert loader.load_market("usa").completed_stocks == 5

    def test_resume_continues_from_saved_counts_and_ignored_when_off(self, in_tmp):
        path = in_tmp / "data" / "progress" / "usa_progress.json"
        LoadProgress(market="usa", total_stocks=5, completed_stocks=100, inserted_records=1000).save(path)
        assert make_loader(FakeDB(), in_tmp, resume=True).load_market("usa").completed_stocks == 105
        LoadProgress(market="usa", total_stocks=5, completed_stocks=100).save(path)
        assert make_loader(FakeDB(), in_tmp, resume=False).load_market("usa").completed_stocks == 5

    def test_checkpoint_saved_every_ten_completions(self, in_tmp, monkeypatch):
        saves = []
        monkeypatch.setattr(LoadProgress, "save", lambda self, path: saves.append(self.completed_stocks))
        monkeypatch.setattr(
            StockListLoader, "load_predefined", staticmethod(lambda m: [(f"T{i}", "") for i in range(21)])
        )
        make_loader(FakeDB(), in_tmp).load_market("usa")
        assert saves == [10, 20, 21]  # two checkpoints + the final save


@pytest.mark.unit
class TestLoadAllMarkets:
    def test_summary_and_failure_isolation(self, in_tmp, monkeypatch, caplog):
        results = {
            "india": LoadProgress(market="india", total_stocks=1, inserted_records=1234, failed_stocks=["A", "B"]),
            "usa": None,
            "japan": RuntimeError("boom"),
            "korea": LoadProgress(market="korea", total_stocks=1, inserted_records=6),
        }

        def fake_load(self, market, only_missing, dry_run):
            r = results[market]
            if isinstance(r, Exception):
                raise r
            return r

        monkeypatch.setattr(HistoricalDataLoader, "load_market", fake_load)
        loader = HistoricalDataLoader(FakeDB(), ["india", "usa", "japan", "korea"])
        with caplog.at_level(logging.INFO, logger=ldh.logger.name):
            loader.load_all_markets()
        text = caplog.text
        assert "Total records inserted: 1,240" in text
        assert "Total failures: 2" in text
        assert "Markets processed: 2/4" in text
        assert "Failed to load market japan: boom" in text

    def test_flags_forwarded(self, in_tmp, monkeypatch):
        seen = []
        monkeypatch.setattr(
            HistoricalDataLoader,
            "load_market",
            lambda self, m, only_missing, dry_run: seen.append((m, only_missing, dry_run)),
        )
        HistoricalDataLoader(FakeDB(), ["india"]).load_all_markets(only_missing=True, dry_run=True)
        assert seen == [("india", True, True)]
        seen.clear()
        HistoricalDataLoader(FakeDB(), ["india"]).load_all_markets()
        assert seen == [("india", False, False)]


@pytest.mark.unit
class TestMainCLI:
    @pytest.fixture
    def env(self, monkeypatch, in_tmp):
        state = SimpleNamespace(clients=[], loaders=[], closed=0, connect_ok=True, logging=[])

        class FakeClient:
            def __init__(self, **kw):
                self.kw = kw
                state.clients.append(self)

            def connect(self):
                return state.connect_ok

            def close(self):
                state.closed += 1

        class FakeLoader:
            def __init__(self, **kw):
                self.kw = kw
                self.calls = []
                state.loaders.append(self)

            def load_all_markets(self, **kw):
                self.calls.append(kw)

        monkeypatch.setattr(ldh, "PostgresClient", FakeClient)
        monkeypatch.setattr(ldh, "HistoricalDataLoader", FakeLoader)
        monkeypatch.setattr(ldh, "setup_logging", lambda level=logging.INFO: state.logging.append(level))
        return state

    def argv(self, monkeypatch, *args):
        monkeypatch.setattr("sys.argv", ["prog", *args])

    def test_defaults(self, env, monkeypatch):
        self.argv(monkeypatch)
        ldh.main()
        assert env.clients[0].kw == {
            "dbname": "market_data",
            "user": "umashankar",
            "password": "",
            "host": "localhost",
            "port": 5432,
        }
        assert env.loaders[0].kw == {
            "db": env.clients[0],
            "markets": ["india"],
            "workers": 4,
            "batch_size": 500,
            "resume": False,
        }
        assert env.loaders[0].calls == [{"only_missing": False, "dry_run": False}]
        assert env.closed == 1 and env.logging == [logging.INFO]

    def test_all_flags_forwarded(self, env, monkeypatch):
        self.argv(
            monkeypatch, "--markets", "usa", "japan", "--workers", "8", "--batch-size", "10", "--resume",
            "--only-missing", "--dry-run", "--db-host", "h", "--db-port", "1", "--db-user", "u",
            "--db-password", "p", "--db-name", "d", "--log-level", "DEBUG",
        )  # fmt: skip
        ldh.main()
        assert env.clients[0].kw == {"dbname": "d", "user": "u", "password": "p", "host": "h", "port": 1}
        kw = env.loaders[0].kw
        assert (kw["markets"], kw["workers"], kw["batch_size"], kw["resume"]) == (["usa", "japan"], 8, 10, True)
        assert env.loaders[0].calls == [{"only_missing": True, "dry_run": True}]
        assert env.logging == [logging.DEBUG]

    @pytest.mark.parametrize(
        "flag,expected",
        [
            ("--dry-run", {"only_missing": False, "dry_run": True}),
            ("--only-missing", {"only_missing": True, "dry_run": False}),
        ],
    )
    def test_dry_run_and_only_missing_are_not_swapped(self, env, monkeypatch, flag, expected):
        self.argv(monkeypatch, flag)
        ldh.main()
        assert env.loaders[0].calls == [expected]

    def test_validate_only_skips_loading_but_closes(self, env, monkeypatch):
        self.argv(monkeypatch, "--validate-only")
        ldh.main()
        assert env.loaders == [] and env.closed == 1

    def test_connect_failure_exits_1_without_closing(self, env, monkeypatch):
        env.connect_ok = False
        self.argv(monkeypatch)
        with pytest.raises(SystemExit) as e:
            ldh.main()
        assert e.value.code == 1 and env.closed == 0 and env.loaders == []

    def test_db_closed_even_when_loader_raises(self, env, monkeypatch):
        class Boom:
            def __init__(self, **kw):
                pass

            def load_all_markets(self, **kw):
                raise RuntimeError("x")

        monkeypatch.setattr(ldh, "HistoricalDataLoader", Boom)
        self.argv(monkeypatch)
        with pytest.raises(RuntimeError):
            ldh.main()
        assert env.closed == 1

    def test_invalid_market_rejected(self, env, monkeypatch):
        self.argv(monkeypatch, "--markets", "mars")
        with pytest.raises(SystemExit) as e:
            ldh.main()
        assert e.value.code == 2


@pytest.mark.unit
def test_setup_logging_returns_logger_and_sets_level(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    captured = {}
    monkeypatch.setattr(ldh.logging, "basicConfig", lambda **kw: captured.update(kw))
    log = ldh.setup_logging(level=logging.WARNING)
    assert log.name == ldh.__name__
    assert captured["level"] == logging.WARNING
    assert len(captured["handlers"]) == 2
    for h in captured["handlers"]:
        h.close()
    assert (tmp_path / "load_historical_data.log").exists()
