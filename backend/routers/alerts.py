"""
Alert management API endpoints.

Endpoints:
- POST   /api/alerts/status  - Get alert status
- POST   /api/alerts/trigger - Trigger alert checks
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from models import get_db
from services import AlertEngineService
from schemas.alert import (
    AlertStatusResponse,
    AlertTriggerRequest,
    AlertTriggerResponse,
)
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
