"""OHLCV cleaning, retry back-off and fetcher retry logic -- fully offline."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from db.ohlcv_clean import RETRY_CONFIG, backoff_delay, clean_ohlcv


def _frame(n=250, seed=1):
    rng = np.random.RandomState(seed)
    close = 100 + np.abs(rng.randn(n)).cumsum() * 0.1
    return pd.DataFrame(
        {"Open": close, "High": close * 1.01, "Low": close * 0.99, "Close": close, "Volume": 1000.0},
        index=pd.date_range("2022-01-03", periods=n, freq="B"),
    )


def test_backoff_is_exponential_and_capped():
    delays = [backoff_delay(i) for i in range(8)]
    assert delays[:4] == [1.0, 2.0, 4.0, 8.0]
    assert max(delays) == RETRY_CONFIG["max_backoff"]


def test_clean_drops_nan_and_inconsistent_rows():
    df = _frame()
    df.iloc[3, df.columns.get_loc("Close")] = np.nan
    df.iloc[7, df.columns.get_loc("High")] = df.iloc[7]["Low"] - 1  # High < Low
    out = clean_ohlcv(df, "T")
    # 250 rows - 2 bad rows - the first row (its pct_change is NaN, so it never passes the filter)
    assert out is not None and len(out) == 247
    assert "pct_change" in out.columns


def test_clean_returns_none_when_too_few_rows():
    assert clean_ohlcv(_frame(n=50), "T") is None


def test_clean_drops_price_spike():
    df = _frame()
    df.iloc[100:, df.columns.get_loc("Close")] *= 10  # +900% jump on one day
    df.iloc[100:, df.columns.get_loc("High")] *= 10
    df.iloc[100:, df.columns.get_loc("Low")] *= 10
    df.iloc[100:, df.columns.get_loc("Open")] *= 10
    out = clean_ohlcv(df, "T")
    # 250 - first row - the spike day itself
    assert out is not None and len(out) == 248


def test_fetcher_retries_then_succeeds():
    pytest.importorskip("psycopg2")
    pytest.importorskip("tqdm")
    from db.load_historical_data import HistoricalDataFetcher

    calls, sleeps = [], []

    def flaky(ticker, **kwargs):
        calls.append(ticker)
        if len(calls) < 3:
            raise OSError("boom")
        return _frame(5)

    fetcher = HistoricalDataFetcher(None, "india", download=flaky, sleep=sleeps.append)
    df = fetcher.fetch_ohlcv("TCS.NS", pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-02-01").date())
    assert df is not None and len(calls) == 3 and sleeps == [1.0, 2.0]


def test_fetcher_gives_up_after_max_retries():
    pytest.importorskip("psycopg2")
    pytest.importorskip("tqdm")
    from db.load_historical_data import HistoricalDataFetcher

    sleeps = []

    def always_fail(ticker, **kwargs):
        raise OSError("down")

    fetcher = HistoricalDataFetcher(None, "usa", download=always_fail, sleep=sleeps.append)
    assert fetcher.fetch_ohlcv("AAPL", None, None) is None
    assert len(sleeps) == RETRY_CONFIG["max_retries"] - 1


def test_fetcher_empty_frame_returns_none():
    pytest.importorskip("psycopg2")
    pytest.importorskip("tqdm")
    from db.load_historical_data import HistoricalDataFetcher

    fetcher = HistoricalDataFetcher(None, "usa", download=lambda t, **k: pd.DataFrame(), sleep=lambda s: None)
    assert fetcher.fetch_ohlcv("AAPL", None, None) is None


def test_importing_loader_does_not_create_log_file(tmp_path):
    """Importing must not touch the filesystem (logging is configured in main())."""
    import subprocess
    import sys
    from pathlib import Path

    backend = Path(__file__).resolve().parents[1] / "backend"
    code = "import db.load_historical_data"
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        check=True,
        env={"PYTHONPATH": str(backend), "PATH": ""},
        capture_output=True,
    )
    assert not list(tmp_path.iterdir())
