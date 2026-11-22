"""
Pydantic request/response schemas.
"""

from .alert import (
    AlertStatusResponse,
    AlertTriggerRequest,
    AlertTriggerResponse,
)
from .portfolio import (
    BenchmarkComparison,
    PortfolioCreate,
    PortfolioResponse,
    PortfolioReturnsResponse,
    PortfolioSnapshotResponse,
)
from .rebalance import (
    RebalanceDriftRequest,
    RebalanceDriftResponse,
    RebalanceExecutionResponse,
    RebalanceScheduleRequest,
)
from .report import (
    DailyReportResponse,
    MonthlyReportResponse,
    ReportSummary,
)
from .risk import (
    CorrelationMatrixResponse,
    ExposureResponse,
    VaRResponse,
    VolatilityResponse,
)

__all__ = [
    # Portfolio
    "PortfolioCreate",
    "PortfolioResponse",
    "PortfolioSnapshotResponse",
    "PortfolioReturnsResponse",
    "BenchmarkComparison",
    # Risk
    "VolatilityResponse",
    "VaRResponse",
    "CorrelationMatrixResponse",
    "ExposureResponse",
    # Rebalance
    "RebalanceScheduleRequest",
    "RebalanceDriftRequest",
    "RebalanceDriftResponse",
    "RebalanceExecutionResponse",
    # Alert
    "AlertStatusResponse",
    "AlertTriggerRequest",
    "AlertTriggerResponse",
    # Report
    "DailyReportResponse",
    "MonthlyReportResponse",
    "ReportSummary",
]
