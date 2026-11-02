"""Market calendar / currency / ticker helpers (pure, offline)."""
from __future__ import annotations

from datetime import date

from db.market_utils import CurrencyConverter, MarketConfig, MarketHolidayCalendar


def test_module_importable_and_weekend_is_not_trading_day():
    assert not MarketHolidayCalendar.is_trading_day("usa", date(2025, 1, 4))  # Saturday


def test_christmas_closed_and_next_day_skips_it():
    assert not MarketHolidayCalendar.is_trading_day("usa", date(2024, 12, 25))
    assert MarketHolidayCalendar.next_trading_day("usa", date(2024, 12, 24)) == date(2024, 12, 26)


def test_unknown_market_has_no_holidays():
    assert MarketHolidayCalendar.get_holidays("mars") == set()


def test_currency_round_trip_directions():
    assert CurrencyConverter.convert_price(1000, "INR", "USD") == 1000 * 0.012
    assert CurrencyConverter.convert_price(5, "USD", "EUR") == 5 / 1.10
    assert CurrencyConverter.convert_price(5, "USD", "XXX") == 5  # unknown currency passes through


def test_ticker_suffix_rules():
    assert MarketConfig.get_yfinance_ticker("RELIANCE", "india") == "RELIANCE.NS"
    assert MarketConfig.get_yfinance_ticker("AAPL", "usa") == "AAPL"
    assert MarketConfig.get_yfinance_ticker("ADS.DE", "europe") == "ADS.DE"
    assert MarketConfig.get_local_ticker("7203.T", "japan") == "7203"
