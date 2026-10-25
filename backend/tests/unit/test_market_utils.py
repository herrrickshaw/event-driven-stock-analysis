"""Unit tests for db/market_utils.py: holiday calendar, currency conversion,
data-quality metrics, ticker suffix routing."""
from datetime import date

import pandas as pd
import pytest

from db.market_utils import (
    CurrencyConverter,
    DataQualityValidator,
    MarketConfig,
    MarketHolidayCalendar,
)


@pytest.mark.unit
class TestHolidayCalendar:
    # NYSE published 2024 holiday schedule
    NYSE_2024 = [date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 19), date(2024, 3, 29),
                 date(2024, 5, 27), date(2024, 6, 19), date(2024, 7, 4), date(2024, 9, 2),
                 date(2024, 11, 28), date(2024, 12, 25)]

    @pytest.mark.parametrize("d", NYSE_2024)
    def test_nyse_2024_holidays_are_closed(self, d):
        assert not MarketHolidayCalendar.is_trading_day("usa", d)

    def test_nyse_closed_for_national_day_of_mourning_2025_01_09(self):
        # NYSE closed 9 Jan 2025 for President Carter's national day of mourning
        assert not MarketHolidayCalendar.is_trading_day("usa", date(2025, 1, 9))

    @pytest.mark.parametrize("d", [date(2024, 5, 1), date(2025, 5, 1),     # Maharashtra Day
                                   date(2025, 2, 26),                       # Mahashivratri
                                   date(2025, 3, 14)])                      # Holi
    def test_nse_published_holidays_are_closed(self, d):
        assert not MarketHolidayCalendar.is_trading_day("india", d)

    def test_weekend_is_closed_and_ordinary_day_open(self):
        assert not MarketHolidayCalendar.is_trading_day("usa", date(2024, 7, 6))   # Saturday
        assert MarketHolidayCalendar.is_trading_day("usa", date(2024, 7, 5))       # Friday

    def test_next_and_prev_skip_weekend_and_holiday(self):
        # Thu 2024-07-04 holiday; Fri 5 open
        assert MarketHolidayCalendar.next_trading_day("usa", date(2024, 7, 3)) == date(2024, 7, 5)
        # Mon 2024-09-02 Labor Day -> previous is Fri 2024-08-30
        assert MarketHolidayCalendar.prev_trading_day("usa", date(2024, 9, 3)) == date(2024, 8, 30)

    def test_year_filter(self):
        h = MarketHolidayCalendar.get_holidays("usa", 2024)
        assert all(d.year == 2024 for d in h) and date(2024, 12, 25) in h

    def test_unknown_market_has_only_weekends(self):
        assert MarketHolidayCalendar.get_holidays("mars") == set()


@pytest.mark.unit
class TestCurrencyConverter:
    def test_to_usd(self):
        assert CurrencyConverter.convert_price(1000, "INR") == pytest.approx(12.0)
        assert CurrencyConverter.convert_price(100, "EUR") == pytest.approx(110.0)

    def test_from_usd(self):
        assert CurrencyConverter.convert_price(110, "USD", "EUR") == pytest.approx(100.0)

    def test_same_currency_is_identity(self):
        assert CurrencyConverter.convert_price(5, "JPY", "JPY") == 5

    def test_cross_rate_goes_through_usd(self):
        # 100 EUR -> 110 USD -> 110 / 0.012 INR
        assert CurrencyConverter.convert_price(100, "EUR", "INR") == pytest.approx(110 / 0.012)

    def test_unknown_currency_is_not_silently_treated_as_usd(self):
        with pytest.raises(ValueError):
            CurrencyConverter.convert_price(100, "CHF", "USD")

    def test_normalize_prices_defaults_missing_currency_to_usd(self):
        out = CurrencyConverter.normalize_prices({"RELIANCE": 2500.0, "AAPL": 180.0},
                                                 {"RELIANCE": "INR"})
        assert out == {"RELIANCE": pytest.approx(30.0), "AAPL": 180.0}


@pytest.mark.unit
class TestMarketConfig:
    @pytest.mark.parametrize("ticker,market,expected", [
        ("RELIANCE", "india", "RELIANCE.NS"),
        ("500325.BO", "india", "500325.BO"),
        ("AAPL", "usa", "AAPL"),
        ("7203", "japan", "7203.T"),
        ("005930", "korea", "005930.KS"),
        ("035720.KQ", "korea", "035720.KQ"),     # KOSDAQ: never "035720.KQ.KS"
        ("SAP.DE", "europe", "SAP.DE"),
        ("ENI.MI", "europe", "ENI.MI"),
        ("000001.SZ", "china", "000001.SZ"),
    ])
    def test_get_yfinance_ticker(self, ticker, market, expected):
        assert MarketConfig.get_yfinance_ticker(ticker, market) == expected

    @pytest.mark.parametrize("yf,market,expected", [
        ("RELIANCE.NS", "india", "RELIANCE"),
        ("7203.T", "japan", "7203"),
        ("AAPL", "usa", "AAPL"),
    ])
    def test_get_local_ticker(self, yf, market, expected):
        assert MarketConfig.get_local_ticker(yf, market) == expected


@pytest.mark.unit
class TestDataQuality:
    def test_clean_frame_scores_100(self):
        df = pd.DataFrame({"Close": [10.0, 10.5, 10.2], "Volume": [100, 110, 90]})
        m = DataQualityValidator.compute_metrics(df)
        assert (m.total_records, m.null_records, m.duplicate_records, m.outlier_records) == (3, 0, 0, 0)
        assert m.quality_score == 100.0
        assert DataQualityValidator.is_quality_acceptable(m)

    def test_nulls_duplicates_and_outliers_counted(self):
        df = pd.DataFrame({"Close": [10.0, 10.0, None, 100.0], "Volume": [100, 100, 100, 100]})
        m = DataQualityValidator.compute_metrics(df)
        assert m.null_records == 1
        assert m.duplicate_records == 1
        assert m.outlier_records == 1            # 10 -> 100 is +900 %
        assert m.completeness_pct == 75.0
        assert not DataQualityValidator.is_quality_acceptable(m)

    def test_empty_frame(self):
        m = DataQualityValidator.compute_metrics(pd.DataFrame({"Close": [], "Volume": []}))
        assert m.quality_score == 0 and m.completeness_pct == 0
