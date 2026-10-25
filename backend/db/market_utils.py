"""
Market utilities for event-driven stock analysis.

Provides:
- Market holidays handling for date alignment
- Currency conversion and normalization
- Data quality metrics and validation
- Market-specific configurations
"""

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# MARKET HOLIDAYS (cached per market)
# ═════════════════════════════════════════════════════════════════════════════

class MarketHolidayCalendar:
    """Manage trading holidays for each market"""

    _HOLIDAYS_CACHE: Dict[str, Set[date]] = {}

    # Hardcoded holidays for major markets (2021-2026)
    _HARDCODED_HOLIDAYS = {
        'india': [
            # 2024
            (2024, 1, 26), (2024, 3, 8), (2024, 3, 25), (2024, 3, 29),
            (2024, 4, 11), (2024, 4, 17), (2024, 4, 21), (2024, 5, 23),
            (2024, 8, 15), (2024, 8, 26), (2024, 9, 16), (2024, 10, 2),
            (2024, 10, 12), (2024, 10, 31), (2024, 11, 1), (2024, 11, 15),
            (2024, 12, 25),
            # 2025
            (2025, 1, 26), (2025, 3, 8), (2025, 3, 25), (2025, 4, 11),
            (2025, 4, 18), (2025, 4, 21), (2025, 5, 23), (2025, 8, 15),
            (2025, 8, 29), (2025, 9, 16), (2025, 10, 2), (2025, 10, 20),
            (2025, 10, 31), (2025, 11, 5), (2025, 12, 25),
        ],
        'usa': [
            # 2024
            (2024, 1, 1), (2024, 1, 15), (2024, 2, 19), (2024, 3, 29),
            (2024, 5, 27), (2024, 6, 19), (2024, 7, 4), (2024, 9, 2),
            (2024, 11, 28), (2024, 12, 25),
            # 2025
            (2025, 1, 1), (2025, 1, 20), (2025, 2, 17), (2025, 4, 18),
            (2025, 5, 26), (2025, 6, 19), (2025, 7, 4), (2025, 9, 1),
            (2025, 11, 27), (2025, 12, 25),
        ],
        'uk': [
            # 2024
            (2024, 1, 1), (2024, 3, 29), (2024, 4, 1), (2024, 5, 6),
            (2024, 5, 27), (2024, 8, 26), (2024, 12, 25), (2024, 12, 26),
            # 2025
            (2025, 1, 1), (2025, 4, 18), (2025, 4, 21), (2025, 5, 5),
            (2025, 5, 26), (2025, 8, 25), (2025, 12, 25), (2025, 12, 26),
        ],
        'japan': [
            # 2024
            (2024, 1, 1), (2024, 1, 8), (2024, 2, 11), (2024, 2, 12),
            (2024, 3, 20), (2024, 4, 29), (2024, 5, 3), (2024, 5, 4),
            (2024, 5, 5), (2024, 5, 6), (2024, 7, 15), (2024, 8, 11),
            (2024, 9, 16), (2024, 9, 22), (2024, 9, 23), (2024, 10, 14),
            (2024, 11, 3), (2024, 11, 23),
            # 2025
            (2025, 1, 1), (2025, 1, 13), (2025, 2, 11), (2025, 3, 20),
            (2025, 4, 29), (2025, 5, 3), (2025, 5, 4), (2025, 5, 5),
            (2025, 5, 6), (2025, 7, 21), (2025, 8, 11), (2025, 9, 15),
            (2025, 9, 23), (2025, 10, 13), (2025, 11, 3), (2025, 11, 23),
        ],
        'korea': [
            # 2024
            (2024, 1, 1), (2024, 2, 9), (2024, 2, 10), (2024, 2, 11),
            (2024, 2, 12), (2024, 3, 1), (2024, 4, 10), (2024, 5, 5),
            (2024, 5, 15), (2024, 6, 6), (2024, 8, 15), (2024, 9, 16),
            (2024, 9, 17), (2024, 9, 18), (2024, 10, 3), (2024, 10, 9),
            (2024, 12, 25),
            # 2025
            (2025, 1, 1), (2025, 1, 29), (2025, 1, 30), (2025, 1, 31),
            (2025, 2, 1), (2025, 3, 1), (2025, 4, 10), (2025, 5, 5),
            (2025, 5, 15), (2025, 6, 6), (2025, 8, 15), (2025, 9, 3),
            (2025, 9, 4), (2025, 10, 3), (2025, 10, 9), (2025, 12, 25),
        ],
        'europe': [
            # Major Europe holidays (Germany/France/UK)
            # 2024
            (2024, 1, 1), (2024, 3, 29), (2024, 4, 1), (2024, 5, 1),
            (2024, 5, 9), (2024, 5, 19), (2024, 5, 30), (2024, 8, 15),
            (2024, 11, 1), (2024, 11, 11), (2024, 12, 25), (2024, 12, 26),
            # 2025
            (2025, 1, 1), (2025, 4, 18), (2025, 4, 21), (2025, 5, 1),
            (2025, 5, 8), (2025, 5, 29), (2025, 6, 9), (2025, 8, 15),
            (2025, 11, 1), (2025, 11, 11), (2025, 12, 25), (2025, 12, 26),
        ],
        'china': [
            # 2024
            (2024, 1, 1), (2024, 2, 10), (2024, 2, 11), (2024, 2, 12),
            (2024, 2, 13), (2024, 2, 14), (2024, 2, 15), (2024, 2, 16),
            (2024, 2, 17), (2024, 4, 4), (2024, 4, 5), (2024, 4, 6),
            (2024, 6, 10), (2024, 9, 15), (2024, 9, 16), (2024, 9, 17),
            (2024, 10, 1), (2024, 10, 2), (2024, 10, 3), (2024, 10, 4),
            (2024, 10, 5), (2024, 10, 6), (2024, 10, 7),
            # 2025
            (2025, 1, 1), (2025, 1, 29), (2025, 1, 30), (2025, 1, 31),
            (2025, 2, 1), (2025, 2, 2), (2025, 2, 3), (2025, 2, 4),
            (2025, 4, 4), (2025, 4, 5), (2025, 4, 6), (2025, 6, 10),
            (2025, 10, 1), (2025, 10, 2), (2025, 10, 3), (2025, 10, 4),
            (2025, 10, 5), (2025, 10, 6), (2025, 10, 7),
        ],
        'brazil': [
            # 2024
            (2024, 1, 1), (2024, 2, 12), (2024, 2, 13), (2024, 2, 14),
            (2024, 2, 15), (2024, 3, 29), (2024, 4, 21), (2024, 5, 1),
            (2024, 5, 30), (2024, 9, 7), (2024, 10, 12), (2024, 11, 2),
            (2024, 11, 15), (2024, 11, 20), (2024, 12, 25),
            # 2025
            (2025, 1, 1), (2025, 3, 4), (2025, 3, 5), (2025, 3, 6),
            (2025, 3, 7), (2025, 4, 18), (2025, 4, 21), (2025, 5, 1),
            (2025, 6, 19), (2025, 9, 7), (2025, 10, 12), (2025, 11, 2),
            (2025, 11, 15), (2025, 11, 20), (2025, 12, 25),
        ]
    }

    @classmethod
    def get_holidays(cls, market: str, year: int = None) -> Set[date]:
        """Get holidays for a market, cached"""
        cache_key = f'{market}_{year or "all"}'

        if cache_key not in cls._HOLIDAYS_CACHE:
            holidays = set()

            # Load from hardcoded data
            if market in cls._HARDCODED_HOLIDAYS:
                for y, m, d in cls._HARDCODED_HOLIDAYS[market]:
                    if year is None or y == year:
                        holidays.add(date(y, m, d))

            cls._HOLIDAYS_CACHE[cache_key] = holidays

        return cls._HOLIDAYS_CACHE[cache_key]

    @classmethod
    def is_trading_day(cls, market: str, check_date: date) -> bool:
        """Check if a date is a trading day (not holiday or weekend)"""
        # Weekends
        if check_date.weekday() >= 5:  # Saturday=5, Sunday=6
            # Special markets that trade weekends (none in standard markets)
            return False

        holidays = cls.get_holidays(market)
        return check_date not in holidays

    @classmethod
    def next_trading_day(cls, market: str, from_date: date) -> date:
        """Get the next trading day from a given date"""
        current = from_date + timedelta(days=1)
        while not cls.is_trading_day(market, current):
            current += timedelta(days=1)
        return current

    @classmethod
    def prev_trading_day(cls, market: str, from_date: date) -> date:
        """Get the previous trading day from a given date"""
        current = from_date - timedelta(days=1)
        while not cls.is_trading_day(market, current):
            current -= timedelta(days=1)
        return current


# ═════════════════════════════════════════════════════════════════════════════
# CURRENCY CONVERSION & NORMALIZATION
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class CurrencyRate:
    """Currency conversion rate"""
    from_currency: str
    to_currency: str
    rate: float
    date: date

    def convert(self, amount: float) -> float:
        """Convert amount using this rate"""
        return amount * self.rate


class CurrencyConverter:
    """Convert prices to base currency (USD)"""

    # Approximate rates as of 2024 (can be replaced with live API)
    _APPROXIMATE_RATES = {
        ('INR', 'USD'): 0.012,   # 1 INR ≈ 0.012 USD
        ('EUR', 'USD'): 1.10,    # 1 EUR ≈ 1.10 USD
        ('GBP', 'USD'): 1.27,    # 1 GBP ≈ 1.27 USD
        ('JPY', 'USD'): 0.0067,  # 1 JPY ≈ 0.0067 USD
        ('KRW', 'USD'): 0.00077, # 1 KRW ≈ 0.00077 USD
        ('BRL', 'USD'): 0.20,    # 1 BRL ≈ 0.20 USD
        ('CNY', 'USD'): 0.14,    # 1 CNY ≈ 0.14 USD
    }

    @classmethod
    def convert_price(cls, amount: float, from_currency: str, to_currency: str = 'USD') -> float:
        """Convert price from one currency to another"""
        if from_currency == to_currency:
            return amount

        def to_usd_rate(cur: str) -> float:
            if cur == 'USD':
                return 1.0
            rate = cls._APPROXIMATE_RATES.get((cur, 'USD'))
            if rate is None:
                # Returning the amount unconverted would silently price e.g.
                # CHF as USD; refuse instead.
                raise ValueError(f"No conversion rate for {cur}")
            return rate

        # Every pair goes through USD (the table only stores X->USD), so
        # EUR->INR is EUR->USD->INR rather than an unconverted passthrough.
        return amount * to_usd_rate(from_currency) / to_usd_rate(to_currency)

    @classmethod
    def normalize_prices(cls, prices_dict: Dict[str, float], currencies: Dict[str, str]) -> Dict[str, float]:
        """Normalize prices to USD"""
        normalized = {}
        for ticker, price in prices_dict.items():
            currency = currencies.get(ticker, 'USD')
            normalized[ticker] = cls.convert_price(price, currency, 'USD')
        return normalized


# ═════════════════════════════════════════════════════════════════════════════
# DATA QUALITY METRICS
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class DataQualityMetrics:
    """Quality metrics for a dataset"""
    total_records: int
    null_records: int
    duplicate_records: int
    outlier_records: int
    valid_records: int
    completeness_pct: float
    duplicate_pct: float
    outlier_pct: float

    @property
    def quality_score(self) -> float:
        """0-100 quality score"""
        return (self.valid_records / self.total_records * 100) if self.total_records > 0 else 0


class DataQualityValidator:
    """Validate and assess data quality"""

    @staticmethod
    def compute_metrics(df, price_col='Close', volume_col='Volume') -> DataQualityMetrics:
        """Compute quality metrics for a DataFrame"""
        total = len(df)
        if total == 0:
            # pct_change() on an empty Series raises in pandas 2.1
            return DataQualityMetrics(0, 0, 0, 0, 0, 0, 0, 0)

        # Null values
        null_mask = df[[price_col, volume_col]].isnull().any(axis=1)
        null_count = null_mask.sum()

        # Duplicates
        dup_count = df.duplicated().sum()

        # Outliers (price change > 500% or volume spike > 1000%)
        if price_col in df.columns:
            pct_change = df[price_col].pct_change().abs()
            price_outliers = (pct_change > 5.0).sum()  # 500%
        else:
            price_outliers = 0

        if volume_col in df.columns:
            vol_change = df[volume_col].pct_change().abs()
            vol_outliers = (vol_change > 10.0).sum()  # 1000%
        else:
            vol_outliers = 0

        outlier_count = max(price_outliers, vol_outliers)

        valid = total - null_count - dup_count - outlier_count

        return DataQualityMetrics(
            total_records=total,
            null_records=null_count,
            duplicate_records=dup_count,
            outlier_records=outlier_count,
            valid_records=max(valid, 0),
            completeness_pct=((total - null_count) / total * 100) if total > 0 else 0,
            duplicate_pct=(dup_count / total * 100) if total > 0 else 0,
            outlier_pct=(outlier_count / total * 100) if total > 0 else 0,
        )

    @staticmethod
    def is_quality_acceptable(metrics: DataQualityMetrics, min_completeness=95.0,
                            max_duplicates=1.0, max_outliers=2.0) -> bool:
        """Check if data quality is acceptable"""
        return (
            metrics.completeness_pct >= min_completeness and
            metrics.duplicate_pct <= max_duplicates and
            metrics.outlier_pct <= max_outliers
        )


# ═════════════════════════════════════════════════════════════════════════════
# MARKET-SPECIFIC CONFIGURATIONS
# ═════════════════════════════════════════════════════════════════════════════

class MarketConfig:
    """Market-specific configurations and routing"""

    TICKER_SUFFIXES = {
        'india': '.NS',      # NSE, .BO for BSE
        'usa': '',           # No suffix
        'europe': 'varies',  # .DE, .L, .PA, etc. embedded
        'japan': '.T',       # Tokyo Stock Exchange
        'korea': '.KS',      # KOSPI, .KQ for KOSDAQ
        'uk': '.L',          # London
        'brazil': '',        # Brazilian stocks often no suffix
        'china': '.SS',      # Shanghai, .SZ for Shenzhen
    }

    @staticmethod
    def get_yfinance_ticker(ticker: str, market: str) -> str:
        """Convert local ticker to yfinance format"""
        suffix = MarketConfig.TICKER_SUFFIXES.get(market, '')

        # Some tickers already have suffixes embedded
        if any(ticker.endswith(s) for s in ['.NS', '.BO', '.L', '.DE', '.PA', '.T', '.KS', '.KQ', '.SS', '.SZ']):
            return ticker

        if suffix and suffix != 'varies':
            return f'{ticker}{suffix}'

        return ticker

    @staticmethod
    def get_local_ticker(yf_ticker: str, market: str) -> str:
        """Strip yfinance suffix to get local ticker"""
        suffix = MarketConfig.TICKER_SUFFIXES.get(market, '')

        if suffix and suffix != 'varies':
            if yf_ticker.endswith(suffix):
                return yf_ticker[:-len(suffix)]

        return yf_ticker


# ═════════════════════════════════════════════════════════════════════════════
# MARKET STATISTICS
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class MarketStatistics:
    """Statistics for a market's historical data"""
    market: str
    total_stocks: int
    total_records: int
    avg_records_per_stock: float
    date_range_years: float
    price_range: Tuple[float, float]  # (min, max)
    volume_range: Tuple[int, int]     # (min, max)

    def summary(self) -> str:
        """Pretty print summary"""
        return f"""
Market: {self.market}
  Total stocks: {self.total_stocks:,}
  Total records: {self.total_records:,}
  Avg records/stock: {self.avg_records_per_stock:.0f}
  Date range: {self.date_range_years:.1f} years
  Price range: ${self.price_range[0]:.2f} - ${self.price_range[1]:.2f}
  Volume range: {self.volume_range[0]:,} - {self.volume_range[1]:,}
        """


if __name__ == '__main__':
    # Test examples
    print("Testing MarketHolidayCalendar...")
    print(f"Is 2024-12-25 a trading day in USA? {MarketHolidayCalendar.is_trading_day('usa', date(2024, 12, 25))}")
    print(f"Is 2024-12-24 a trading day in USA? {MarketHolidayCalendar.is_trading_day('usa', date(2024, 12, 24))}")

    print("\nTesting CurrencyConverter...")
    print(f"1000 INR = {CurrencyConverter.convert_price(1000, 'INR', 'USD'):.2f} USD")
    print(f"100 EUR = {CurrencyConverter.convert_price(100, 'EUR', 'USD'):.2f} USD")

    print("\nTesting MarketConfig...")
    print(f"India ticker RELIANCE -> {MarketConfig.get_yfinance_ticker('RELIANCE', 'india')}")
    print(f"USA ticker AAPL -> {MarketConfig.get_yfinance_ticker('AAPL', 'usa')}")
    print(f"Japan ticker 7203 -> {MarketConfig.get_yfinance_ticker('7203', 'japan')}")
