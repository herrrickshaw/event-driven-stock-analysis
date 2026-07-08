"""
Pydantic request/response schemas.
"""
from .portfolio import (
    PortfolioCreate,
    PortfolioResponse,
    PortfolioSnapshotResponse,
    PortfolioReturnsResponse,
    BenchmarkComparison,
)
from .risk import (
    VolatilityResponse,
    VaRResponse,
    CorrelationMatrixResponse,
    ExposureResponse,
)
from .rebalance import (
    RebalanceScheduleRequest,
    RebalanceDriftRequest,
    RebalanceDriftResponse,
    RebalanceExecutionResponse,
)
from .alert import (
    AlertStatusResponse,
    AlertTriggerRequest,
    AlertTriggerResponse,
)
from .report import (
    DailyReportResponse,
    MonthlyReportResponse,
    ReportSummary,
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
