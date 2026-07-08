"""
Reporting API endpoints.

Endpoints:
- POST   /api/reports/daily   - Generate daily report
- POST   /api/reports/monthly - Generate monthly report
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from models import get_db
from services import ReportingService
from schemas.report import (
    DailyReportResponse,
    MonthlyReportResponse,
)
from utils import PortfolioNotFoundError, get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post(
    "/daily",
    response_model=DailyReportResponse,
    summary="Generate Daily Report",
    description="Generate comprehensive daily portfolio report",
)
async def generate_daily_report(
    portfolio_id: int = Query(..., ge=1, description="Portfolio ID"),
    db: Session = Depends(get_db),
) -> DailyReportResponse:
    """
    Generate daily report for portfolio.

    Args:
        portfolio_id: Portfolio identifier

    Returns:
        DailyReportResponse with daily metrics and analysis
    """
    service = ReportingService(db)

    logger.info(f"Generating daily report for portfolio_id={portfolio_id}")

    # TODO: Call service to generate daily report
    # report = service.generate_daily_report(portfolio_id)
    # return report

    raise NotImplementedError("Endpoint not yet implemented")


@router.post(
    "/monthly",
    response_model=MonthlyReportResponse,
    summary="Generate Monthly Report",
    description="Generate comprehensive monthly portfolio report",
)
async def generate_monthly_report(
    portfolio_id: int = Query(..., ge=1),
    month: str = Query(
        None,
        description="Month in YYYY-MM format (defaults to current month)",
    ),
    db: Session = Depends(get_db),
) -> MonthlyReportResponse:
    """
    Generate monthly report for portfolio.

    Args:
        portfolio_id: Portfolio identifier
        month: Month in YYYY-MM format

    Returns:
        MonthlyReportResponse with monthly metrics and analysis
    """
    service = ReportingService(db)

    logger.info(f"Generating monthly report for portfolio_id={portfolio_id}, month={month}")

    # TODO: Call service to generate monthly report
    # report = service.generate_monthly_report(portfolio_id, month)
    # return report

    raise NotImplementedError("Endpoint not yet implemented")
