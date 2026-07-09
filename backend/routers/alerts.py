"""
Alert management API endpoints.

Portfolio-level (DB-backed, drift/volatility/correlation/loss/concentration
thresholds against a stored Portfolio -- see services.AlertEngineService):
- POST   /api/alerts/status              - Get alert status
- POST   /api/alerts/trigger              - Trigger alert checks

Live watchlist + event pipeline (in-process EventBus/PortfolioMonitor --
see events/event_bus.py, events/portfolio_monitor.py):
- POST   /api/alerts/portfolio            - Add tickers to the live watchlist
- GET    /api/alerts/portfolio            - Get the live watchlist
- DELETE /api/alerts/portfolio/{ticker}   - Remove a ticker from the watchlist
- GET    /api/alerts/latest               - Latest events from the EventBus history
- POST   /api/alerts/trigger/{ticker}     - Manually publish a market event for one ticker
- GET    /api/alerts/stream               - SSE stream of live market events
"""
import json
from typing import Any, AsyncGenerator, Dict, List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from models import get_db
from services import AlertEngineService
from schemas.alert import (
    AlertStatusResponse,
    AlertTriggerRequest,
    AlertTriggerResponse,
    WatchlistAddRequest,
)
from events.event_bus import MarketEvent, bus
from events.portfolio_monitor import monitor
from utils import PortfolioNotFoundError, get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.post(
    "/status",
    response_model=AlertStatusResponse,
    summary="Get Alert Status",
    description="Get current status of all alerts for a portfolio",
)
async def get_alert_status(
    portfolio_id: int = Query(..., ge=1, description="Portfolio ID"),
    db: Session = Depends(get_db),
) -> AlertStatusResponse:
    """
    Get alert status for portfolio.

    Args:
        portfolio_id: Portfolio identifier

    Returns:
        AlertStatusResponse with alert summary
    """
    service = AlertEngineService(db)

    logger.info(f"Fetching alert status for portfolio_id={portfolio_id}")

    # TODO: Call service to get alert status
    # status = service.get_alert_status(portfolio_id)
    # return status

    raise NotImplementedError("Endpoint not yet implemented")


@router.post(
    "/trigger",
    response_model=AlertTriggerResponse,
    summary="Trigger Alert Checks",
    description="Check and trigger all active alerts for a portfolio",
)
async def trigger_alerts(
    request: AlertTriggerRequest,
    db: Session = Depends(get_db),
) -> AlertTriggerResponse:
    """
    Trigger alert checks for portfolio.

    Args:
        request: AlertTriggerRequest with check parameters

    Returns:
        AlertTriggerResponse with triggered alerts
    """
    service = AlertEngineService(db)

    logger.info(
        f"Triggering alerts for portfolio_id={request.portfolio_id}, types={request.alert_types}"
    )

    # TODO: Call service to trigger alerts
    # response = service.trigger_alerts(
    #     request.portfolio_id,
    #     request.alert_types,
    # )
    # return response

    raise NotImplementedError("Endpoint not yet implemented")


# ─────────────────────────────────────────────────────────────────────────
# Live watchlist + event pipeline
# ─────────────────────────────────────────────────────────────────────────


@router.post("/portfolio", summary="Add tickers to the live watchlist")
async def add_to_watchlist(payload: WatchlistAddRequest) -> Dict[str, Any]:
    monitor.add_tickers(payload.tickers, payload.market)
    logger.info(f"Added to watchlist: {payload.tickers} ({payload.market})")
    return {"watched": monitor.watched(), "added": payload.tickers}


@router.get("/portfolio", summary="Get the live watchlist")
async def get_watchlist() -> Dict[str, Any]:
    return {"watched": monitor.watched()}


@router.delete("/portfolio/{ticker}", summary="Remove a ticker from the watchlist")
async def remove_from_watchlist(ticker: str) -> Dict[str, Any]:
    monitor.remove_ticker(ticker)
    logger.info(f"Removed from watchlist: {ticker}")
    return {"watched": monitor.watched()}


def get_alerts(limit: int = 20) -> List[Dict[str, Any]]:
    """Most recent EventBus events, newest first."""
    events = bus.history[-limit:]
    return [
        {
            "event_type": e.type,
            "ticker": e.ticker,
            "market": e.market,
            "data": e.data,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in reversed(events)
    ]


@router.get("/latest", summary="Get latest events from the EventBus history")
async def latest_alerts(limit: int = Query(20, ge=1, le=500)) -> Dict[str, Any]:
    return {"alerts": get_alerts(limit)}


@router.post("/trigger/{ticker}", summary="Manually publish a market event for one ticker")
async def manual_trigger(ticker: str, market: str = Query("india")) -> Dict[str, Any]:
    event = MarketEvent(type="MANUAL_TRIGGER", ticker=ticker, market=market, data={})
    await bus.publish(event)
    return {"status": "triggered", "ticker": ticker}


async def subscribe_sse() -> AsyncGenerator[str, None]:
    """Async generator yielding Server-Sent-Events lines for every event
    published on the bus, for as long as the client stays connected."""
    import asyncio

    queue: "asyncio.Queue[MarketEvent]" = asyncio.Queue()

    def _on_event(event: MarketEvent) -> None:
        queue.put_nowait(event)

    bus.subscribe("*", _on_event)
    try:
        while True:
            event = await queue.get()
            payload = {
                "event_type": event.type,
                "ticker": event.ticker,
                "market": event.market,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
            }
            yield f"event: {event.type}\ndata: {json.dumps(payload)}\n\n"
    finally:
        bus.unsubscribe("*", _on_event)


@router.get("/stream", summary="SSE stream of live market events")
async def stream_alerts() -> StreamingResponse:
    return StreamingResponse(subscribe_sse(), media_type="text/event-stream")
