"""
Pydantic schemas for reporting endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class ReportMetric(BaseModel):
    """Individual metric in a report."""

    name: str
    value: float
    unit: Optional[str] = None
    interpretation: Optional[str] = None


class DailyReportResponse(BaseModel):
    """Daily portfolio report."""

    portfolio_id: int
    report_date: datetime
    period: str = "daily"

    # Performance metrics
    total_value: float
    daily_return: float
    daily_return_pct: float
    ytd_return_pct: float

    # Risk metrics
    daily_volatility: float
    var_95: float
    sharpe_ratio: float

    # Positions
    top_gainers: List[Dict[str, float]]
    top_losers: List[Dict[str, float]]
    sector_exposure: Dict[str, float]

    # Alerts
    active_alerts: int
    triggered_today: int

    # Recommendations
    recommendations: List[str] = []

    generated_at: datetime


class MonthlyReportResponse(BaseModel):
    """Monthly portfolio report."""

    portfolio_id: int
    report_month: str  # YYYY-MM format
    period: str = "monthly"

    # Performance metrics
    monthly_return: float
    monthly_return_pct: float
    ytd_return_pct: float
    cumulative_return_pct: Optional[float] = None

    # Risk metrics
    monthly_volatility: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    information_ratio: Optional[float] = None

    # Positions summary
    total_holdings: int
    new_positions: int
    closed_positions: int
    average_holding_period: float

    # Transactions
    total_buys: int
    total_sells: int
    total_dividends_received: float

    # Sector performance
    best_sector: str
    worst_sector: str
    sector_returns: Dict[str, float]

    # Rebalancing
    rebalances_executed: int
    portfolio_drift: float

    # Alerts summary
    total_alerts_triggered: int
    critical_alerts: int
    warning_alerts: int

    # Benchmark comparison
    benchmark_symbol: Optional[str] = None
    benchmark_return: Optional[float] = None
    outperformance: Optional[float] = None

    generated_at: datetime


class ReportSummary(BaseModel):
    """Summary of a report."""

    report_id: int
    portfolio_id: int
    report_type: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
