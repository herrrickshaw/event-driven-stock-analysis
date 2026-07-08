"""
Pydantic schemas for rebalancing endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class RebalanceScheduleRequest(BaseModel):
    """Request to schedule portfolio rebalancing."""

    portfolio_id: int
    rebalance_type: str = Field(..., description="quarterly, semi-annual, annual, threshold-based")
    target_weights: Dict[str, float] = Field(..., description="Symbol -> weight percentage")
    frequency: Optional[str] = None
    next_rebalance_date: Optional[datetime] = None


class RebalanceDriftRequest(BaseModel):
    """Request to check portfolio drift."""

    portfolio_id: int
    drift_threshold_pct: float = Field(default=5.0, description="Drift threshold in percentage")


class DriftPosition(BaseModel):
    """Individual position drift."""

    symbol: str
    market: str
    target_weight: float
    current_weight: float
    drift_pct: float
    requires_rebalance: bool


class RebalanceDriftResponse(BaseModel):
    """Portfolio drift analysis."""

    portfolio_id: int
    total_drift: float = Field(..., description="Sum of absolute drifts")
    requires_rebalancing: bool
    drift_threshold: float
    positions: List[DriftPosition]
    last_rebalance_date: Optional[datetime]
    analysis_date: datetime


class RebalanceAction(BaseModel):
    """Single rebalancing action."""

    symbol: str
    market: str
    action: str = Field(..., description="buy or sell")
    current_quantity: float
    target_quantity: float
    quantity_change: float
    estimated_cost: float


class RebalanceExecutionResponse(BaseModel):
    """Response from rebalancing execution."""

    rebalance_event_id: int
    portfolio_id: int
    status: str = Field(..., description="pending, executing, executed, failed")
    actions: List[RebalanceAction]
    total_cost: float
    execution_timestamp: datetime
    messages: List[str] = []


class RebalanceHistoryResponse(BaseModel):
    """Historical rebalancing event."""

    event_id: int
    portfolio_id: int
    event_type: str
    status: str
    executed_at: Optional[datetime]
    created_at: datetime
