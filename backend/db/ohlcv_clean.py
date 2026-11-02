"""Pure helpers for the historical OHLCV loader: retry back-off and DataFrame cleaning.

Kept free of psycopg2 / yfinance / tqdm so it can be unit-tested offline.
"""
from __future__ import annotations

import logging
from typing import Mapping, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Retry configuration (seconds)
RETRY_CONFIG = {
    "max_retries": 5,
    "initial_backoff": 1.0,
    "max_backoff": 60.0,
    "backoff_factor": 2.0,
    "timeout": 30.0,
}

# Data validation thresholds
VALIDATION_CONFIG = {
    "min_records_per_stock": 200,  # At least 200 trading days in 5 years
    "max_price_change_pct": 500,  # Single-day change shouldn't exceed 500%
    "max_volume_change_pct": 1000,  # Volume spike threshold
    "min_date_range": 3.0,  # At least 3 years of data
}

PRICE_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def backoff_delay(attempt: int, config: Mapping[str, float] = RETRY_CONFIG) -> float:
    """Seconds to wait after failed `attempt` (0-based): exponential, capped at max_backoff."""
    return min(config["initial_backoff"] * (config["backoff_factor"] ** attempt), config["max_backoff"])


def clean_ohlcv(
    df: pd.DataFrame, ticker: str, config: Mapping[str, float] = VALIDATION_CONFIG
) -> Optional[pd.DataFrame]:
    """Drop NaN / inconsistent / outlier rows from a yfinance OHLCV frame.

    Returns None when fewer than `min_records_per_stock` valid rows remain. The
    returned frame keeps the helper column `pct_change` (abs. daily close change).
    """
    initial_count = len(df)
    df = df.dropna(subset=PRICE_COLUMNS)

    # Price consistency: High >= Low, Low <= Close <= High, positive Open/Close
    df = df[
        (df["High"] >= df["Low"])
        & (df["Close"] <= df["High"])
        & (df["Close"] >= df["Low"])
        & (df["Open"] > 0)
        & (df["Close"] > 0)
    ].copy()

    # Outliers: single-day close change above the threshold (trailing change only, no look-ahead)
    df["pct_change"] = df["Close"].pct_change().abs()
    df = df[df["pct_change"] <= config["max_price_change_pct"] / 100]

    df = df[df["Volume"] >= 0]

    if len(df) < config["min_records_per_stock"]:
        logger.warning(
            f'⚠️  {ticker}: Only {len(df)} valid records (min={config["min_records_per_stock"]})'
        )
        return None

    removed = initial_count - len(df)
    if removed > 0:
        logger.debug(f"Cleaned {ticker}: removed {removed} invalid rows, {len(df)} valid")

    return df
