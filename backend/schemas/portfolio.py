"""
Pydantic schemas for portfolio endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class HoldingBase(BaseModel):
    """Base schema for holdings."""

    symbol: str = Field(..., min_length=1)
    market: str = Field(..., description="Market: india, us, europe, japan, korea")
    quantity: float = Field(..., gt=0)
    purchase_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)


class HoldingCreate(HoldingBase):
    """Schema for creating a holding."""

    pass


class HoldingResponse(HoldingBase):
    """Response schema for holdings."""

    id: int
    portfolio_id: int
    weight: Optional[float] = None
    added_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BenchmarkBase(BaseModel):
    """Base schema for benchmarks."""

    symbol: str = Field(..., min_length=1)
    market: str
    weight: float = Field(..., ge=0, le=100)


class BenchmarkCreate(BenchmarkBase):
    """Schema for creating benchmarks."""

    pass


class BenchmarkResponse(BenchmarkBase):
    """Response schema for benchmarks."""

    id: int
    portfolio_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PortfolioBase(BaseModel):
    """Base schema for portfolio."""

    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)


class PortfolioCreate(PortfolioBase):
    """Schema for creating portfolio."""

    pass


class PortfolioUpdate(BaseModel):
    """Schema for updating portfolio."""

    name: Optional[str] = None
    description: Optional[str] = None


class PortfolioResponse(PortfolioBase):
    """Response schema for portfolio."""

    id: int
    user_id: str
    holdings: List[HoldingResponse] = []
    benchmarks: List[BenchmarkResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioSnapshotResponse(BaseModel):
    """Portfolio snapshot with current metrics."""

    portfolio_id: int
    portfolio_name: str
    total_value: float
    total_invested: float
    total_return: float
    total_return_pct: float
    holdings_count: int
    currency: str
    last_updated: datetime


class PortfolioReturnsResponse(BaseModel):
    """Portfolio returns analysis."""

    portfolio_id: int
    period: str  # daily, weekly, monthly, ytd, 1y, 3y, 5y, all
    return_value: float
    return_pct: float
    benchmark_return_pct: Optional[float] = None
    outperformance: Optional[float] = None
    start_date: datetime
    end_date: datetime


class BenchmarkComparison(BaseModel):
    """Benchmark comparison response."""

    portfolio_id: int
    benchmark_symbol: str
    benchmark_return_pct: float
    portfolio_return_pct: float
    outperformance_pct: float
    correlation: float
    beta: float
    period: str
