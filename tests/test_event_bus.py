"""EventBus / PortfolioMonitor behaviour (in-process, no I/O)."""
from __future__ import annotations

import asyncio

from events.event_bus import EventBus, MarketEvent
from events.portfolio_monitor import PortfolioMonitor


def _run(coro):
    return asyncio.run(coro)


def test_sync_and_async_subscribers_and_wildcard():
    bus = EventBus()
    seen = []

    async def async_cb(event):
        seen.append(("async", event.type))

    bus.subscribe("price", lambda e: seen.append(("sync", e.type)))
    bus.subscribe("*", async_cb)
    _run(bus.publish(MarketEvent("price", "AAPL", "usa")))
    _run(bus.publish(MarketEvent("rsi", "AAPL", "usa")))
    assert seen == [("sync", "price"), ("async", "price"), ("async", "rsi")]


def test_history_is_bounded_and_ordered():
    bus = EventBus(max_history=2)
    for kind in ("a", "b", "c"):
        _run(bus.publish(MarketEvent(kind, "X", "india")))
    assert [e.type for e in bus.history] == ["b", "c"]


def test_unsubscribe_unknown_callback_is_noop():
    bus = EventBus()
    bus.unsubscribe("nothing", lambda e: None)


def test_portfolio_monitor_watchlist():
    monitor = PortfolioMonitor()
    monitor.add_tickers(["RELIANCE", "TCS"], "india")
    monitor.remove_ticker("RELIANCE")
    monitor.remove_ticker("MISSING")
    assert monitor.watched() == ["TCS"]
    assert monitor.is_monitoring("TCS") and not monitor.is_monitoring("RELIANCE")
