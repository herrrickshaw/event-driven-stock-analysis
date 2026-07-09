"""In-process pub/sub bus for market events.

This is the platform's namesake "event-driven" core: services detect
conditions (a price crossing a threshold, an RSI signal, a manual trigger)
and publish a `MarketEvent`; anything subscribed to that event type -- or to
the wildcard `'*'` -- is invoked. A bounded history is kept so polling
consumers (e.g. `GET /api/alerts/latest`) don't need a subscription.

Not a distributed message broker (no Kafka here) -- a single-process bus
scoped to one API server instance, which is what the alerts router and its
SSE stream need.
"""
from __future__ import annotations

import inspect
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, List


@dataclass
class MarketEvent:
    type: str
    ticker: str
    market: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """Subscribe by event type (or '*' for every type); publish() invokes
    every matching subscriber, awaiting async callbacks and calling sync
    callbacks directly."""

    def __init__(self, max_history: int = 100):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: Deque[MarketEvent] = deque(maxlen=max_history)

    def subscribe(self, event_type: str, callback: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        subscribers = self._subscribers.get(event_type, [])
        if callback in subscribers:
            subscribers.remove(callback)

    async def publish(self, event: MarketEvent) -> None:
        self._history.append(event)
        callbacks = self._subscribers.get(event.type, []) + self._subscribers.get("*", [])
        for callback in callbacks:
            result = callback(event)
            if inspect.isawaitable(result):
                await result

    @property
    def history(self) -> List[MarketEvent]:
        return list(self._history)


# Process-wide singleton used by the alerts router and any service that
# needs to publish market events (alert_engine, portfolio_analyzer, ...).
bus = EventBus()
