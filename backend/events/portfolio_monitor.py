"""Tracks which tickers are currently being watched for alerts.

This is the live watchlist behind `POST/GET/DELETE /api/alerts/portfolio` --
deliberately separate from the `Portfolio`/`Holding` database models: those
represent what a user owns, this represents what the event pipeline should
currently be watching (a superset that could include names on a user's
radar without a position, or filtered down to only liquid/large holdings).
"""
from __future__ import annotations

from typing import Dict, List


class PortfolioMonitor:
    def __init__(self):
        self._watched: Dict[str, str] = {}  # ticker -> market

    def add_tickers(self, tickers: List[str], market: str) -> None:
        for ticker in tickers:
            self._watched[ticker] = market

    def remove_ticker(self, ticker: str) -> None:
        self._watched.pop(ticker, None)

    def is_monitoring(self, ticker: str) -> bool:
        return ticker in self._watched

    def watched(self) -> List[str]:
        return list(self._watched.keys())


# Process-wide singleton used by the alerts router.
monitor = PortfolioMonitor()
