"""Unit tests for the in-process EventBus and PortfolioMonitor (the implemented
'event-driven' core)."""
import asyncio
from datetime import timezone

import pytest

from events.event_bus import EventBus, MarketEvent
from events.portfolio_monitor import PortfolioMonitor


def ev(t="PRICE_CROSS", ticker="RELIANCE"):
    return MarketEvent(type=t, ticker=ticker, market="india", data={"p": 1})


@pytest.mark.unit
class TestEventBus:
    def test_routes_by_type_and_wildcard(self):
        bus, got = EventBus(), []
        bus.subscribe("PRICE_CROSS", lambda e: got.append(("typed", e.ticker)))
        bus.subscribe("*", lambda e: got.append(("all", e.ticker)))
        bus.subscribe("RSI", lambda e: got.append(("rsi", e.ticker)))
        asyncio.run(bus.publish(ev()))
        assert got == [("typed", "RELIANCE"), ("all", "RELIANCE")]

    def test_async_callbacks_are_awaited(self):
        bus, got = EventBus(), []

        async def cb(e):
            await asyncio.sleep(0)
            got.append(e.ticker)
        bus.subscribe("*", cb)
        asyncio.run(bus.publish(ev()))
        assert got == ["RELIANCE"]

    def test_history_is_bounded_and_ordered(self):
        bus = EventBus(max_history=3)
        for i in range(5):
            asyncio.run(bus.publish(ev(ticker=f"T{i}")))
        assert [e.ticker for e in bus.history] == ["T2", "T3", "T4"]

    def test_history_records_events_without_subscribers(self):
        bus = EventBus()
        asyncio.run(bus.publish(ev()))
        assert len(bus.history) == 1

    def test_history_property_is_a_copy(self):
        bus = EventBus()
        asyncio.run(bus.publish(ev()))
        bus.history.clear()
        assert len(bus.history) == 1

    def test_unsubscribe(self):
        bus, got = EventBus(), []
        cb = got.append
        bus.subscribe("*", cb)
        bus.unsubscribe("*", cb)
        bus.unsubscribe("*", cb)            # second call is a no-op
        bus.unsubscribe("NEVER", cb)        # unknown type is a no-op
        asyncio.run(bus.publish(ev()))
        assert got == []

    def test_subscriber_may_unsubscribe_itself_during_publish(self):
        bus, got = EventBus(), []

        def once(e):
            got.append(e)
            bus.unsubscribe("*", once)
        bus.subscribe("*", once)
        bus.subscribe("*", lambda e: got.append("second"))
        asyncio.run(bus.publish(ev()))
        assert len(got) == 2

    def test_event_timestamp_defaults_to_utc(self):
        assert ev().timestamp.tzinfo == timezone.utc


@pytest.mark.unit
class TestPortfolioMonitor:
    def test_add_remove_and_query(self):
        m = PortfolioMonitor()
        m.add_tickers(["RELIANCE", "TCS"], "india")
        m.add_tickers(["AAPL"], "us")
        assert m.watched() == ["RELIANCE", "TCS", "AAPL"]
        assert m.is_monitoring("TCS")
        m.remove_ticker("TCS")
        m.remove_ticker("NOT_THERE")
        assert not m.is_monitoring("TCS")
        assert m.watched() == ["RELIANCE", "AAPL"]

    def test_re_adding_updates_market_without_duplicating(self):
        m = PortfolioMonitor()
        m.add_tickers(["SHEL"], "uk")
        m.add_tickers(["SHEL"], "europe")
        assert m.watched() == ["SHEL"] and m._watched["SHEL"] == "europe"
