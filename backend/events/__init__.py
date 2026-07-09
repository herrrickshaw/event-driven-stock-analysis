"""Event-driven core: an in-process pub/sub bus for market events, plus a
watchlist monitor that decides which tickers should be watched for alerts.
"""
from .event_bus import EventBus, MarketEvent, bus
from .portfolio_monitor import PortfolioMonitor, monitor

__all__ = ["EventBus", "MarketEvent", "bus", "PortfolioMonitor", "monitor"]
