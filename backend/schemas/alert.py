"""
Pydantic schemas for alert endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class AlertStatusResponse(BaseModel):
    """Status of all active alerts for a portfolio."""

    portfolio_id: int
    total_alerts: int
    active_alerts: int
    triggered_alerts: int
    critical_alerts: int
    warning_alerts: int
    alerts: List["AlertDetail"] = []
    last_checked: datetime


class AlertDetail(BaseModel):
    """Detailed alert information."""

    alert_id: int
    alert_type: str = Field(..., description="drift, volatility, correlation, loss, concentration")
    trigger_condition: str
    threshold_value: Optional[float] = None
    is_active: bool
    last_triggered: Optional[datetime] = None


class AlertTriggerRequest(BaseModel):
    """Request to manually trigger an alert check."""

    portfolio_id: int
    alert_types: Optional[List[str]] = None  # Specific alerts to check


class TriggeredAlert(BaseModel):
    """Information about a triggered alert."""

    alert_id: int
    portfolio_id: int
    alert_type: str
    severity: str = Field(..., description="info, warning, critical")
    message: str
    triggered_value: Optional[float] = None
    threshold_value: Optional[float] = None
    triggered_at: datetime
    acknowledged: bool


class AlertTriggerResponse(BaseModel):
    """Response from alert triggering."""

    portfolio_id: int
    triggered_alerts: List[TriggeredAlert]
    alert_count: int
    critical_count: int
    warning_count: int
    info_count: int
    triggered_at: datetime
