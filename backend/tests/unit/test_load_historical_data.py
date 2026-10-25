"""Unit tests for the pure parts of db/load_historical_data.py (no Postgres,
no yfinance: the fetcher gets a dummy db and DataFrames built in-test)."""
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from db.load_historical_data import (
    VALIDATION_CONFIG,
    HistoricalDataFetcher,
    LoadProgress,
    OHLCVRecord,
    StockListLoader,
)

N = VALIDATION_CONFIG["min_records_per_stock"] + 50


def ohlcv(n=N, close=100.0):
    idx = pd.bdate_range("2020-01-01", periods=n)
    c = np.full(n, close)
    return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c,
                         "Volume": np.full(n, 1000)}, index=idx)


@pytest.fixture
def fetcher():
    return HistoricalDataFetcher(db=None, market="usa")


@pytest.mark.unit
class TestValidateOHLCV:
    def test_clean_series_keeps_every_bar_including_the_first(self, fetcher):
        out = fetcher.validate_ohlcv(ohlcv(), "AAA")
        assert len(out) == N
        assert out.index[0] == pd.Timestamp("2020-01-01")

    def test_inconsistent_and_missing_rows_dropped(self, fetcher):
        df = ohlcv()
        df.iloc[10, df.columns.get_loc("High")] = 50.0      # high < low
        df.iloc[11, df.columns.get_loc("Close")] = np.nan
        df.iloc[12, df.columns.get_loc("Open")] = 0.0
        out = fetcher.validate_ohlcv(df, "AAA")
        assert len(out) == N - 3

    def test_spike_over_500pct_dropped(self, fetcher):
        df = ohlcv()
        i = 20
        for col, mult in (("Open", 1), ("High", 1.01), ("Low", 0.99), ("Close", 1)):
            df.iloc[i, df.columns.get_loc(col)] = 700.0 * mult
        out = fetcher.validate_ohlcv(df, "AAA")
        assert df.index[i] not in out.index

    def test_too_few_records_returns_none(self, fetcher):
        assert fetcher.validate_ohlcv(ohlcv(n=10), "AAA") is None

    def test_convert_to_records_with_adj_close_fallback(self, fetcher):
        df = ohlcv(n=2)
        recs = fetcher.convert_to_ohlcv_records(df, stock_id=7)
        assert recs[0] == OHLCVRecord(7, date(2020, 1, 1), 100.0, 101.0, 99.0, 100.0, 1000, 100.0)
        df["Adj Close"] = [90.0, 91.0]
        assert fetcher.convert_to_ohlcv_records(df, 7)[1].adj_close == 91.0
        assert recs[0].to_tuple()[:2] == (7, date(2020, 1, 1))


@pytest.mark.unit
class TestLoadProgress:
    def test_round_trip(self, tmp_path):
        p = LoadProgress(market="usa", total_stocks=10, completed_stocks=3,
                         failed_stocks=["X"])
        path = tmp_path / "sub" / "progress.json"
        p.save(path)
        q = LoadProgress.load(path)
        assert (q.market, q.total_stocks, q.completed_stocks, q.failed_stocks) == ("usa", 10, 3, ["X"])
        assert q.start_time == p.start_time

    def test_load_missing_is_none(self, tmp_path):
        assert LoadProgress.load(tmp_path / "nope.json") is None

    def test_eta(self):
        p = LoadProgress(market="usa", total_stocks=10, completed_stocks=5,
                         start_time=datetime.now() - timedelta(seconds=50))
        assert p.get_eta() in ("0:00:50", "0:00:49", "0:00:51")
        assert LoadProgress(market="usa", total_stocks=10).get_eta() is None


@pytest.mark.unit
def test_stock_list_from_csv(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text("Ticker,Name\nAAPL,Apple\n,Blank\nMSFT,\n")
    assert StockListLoader.load_from_csv(str(f), "usa") == [("AAPL", "Apple"), ("MSFT", "")]
    assert StockListLoader.load_from_csv(str(tmp_path / "missing.csv"), "usa") == []
