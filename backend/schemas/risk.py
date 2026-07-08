"""
Pydantic schemas for risk endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class VolatilityResponse(BaseModel):
    """Portfolio volatility metrics."""

    portfolio_id: int
    annualized_volatility: float = Field(..., description="Standard deviation annualized")
    daily_volatility: float
    volatility_trend: List[float] = Field(..., description="Last 30 days volatility")
    interpretation: str
    lookback_period: int = Field(default=252, description="Trading days")
    calculated_at: datetime


class VaRResponse(BaseModel):
    """Value at Risk (VaR) metrics."""

    portfolio_id: int
    var_95: float = Field(..., description="VaR at 95% confidence level")
    var_99: float = Field(..., description="VaR at 99% confidence level")
    cvar_95: float = Field(..., description="Conditional VaR at 95% confidence")
    cvar_99: float = Field(..., description="Conditional VaR at 99% confidence")
    period: str = Field(default="1d", description="Time horizon")
    currency: str
    calculated_at: datetime


class CorrelationPair(BaseModel):
    """Pairwise correlation between two holdings."""

    symbol_1: str
    symbol_2: str
    correlation: float = Field(..., ge=-1, le=1)
    interpretation: str


class CorrelationMatrixResponse(BaseModel):
    """Correlation matrix for portfolio holdings."""

    portfolio_id: int
    correlations: List[CorrelationPair]
    average_correlation: float
    diversification_score: float = Field(..., description="0-1, higher is better")
    calculated_at: datetime


class SectorExposure(BaseModel):
    """Sector exposure."""

    sector: str
    percentage: float = Field(..., ge=0, le=100)
    value: float


class GeographyExposure(BaseModel):
    """Geographic exposure."""

    geography: str
    country_code: str
    percentage: float = Field(..., ge=0, le=100)
    value: float


class ExposureResponse(BaseModel):
    """Portfolio exposure breakdown."""

    portfolio_id: int
    sectors: List[SectorExposure]
    geographies: List[GeographyExposure]
    asset_classes: Dict[str, float]
    currency_exposure: Dict[str, float]
    top_10_holdings_concentration: float = Field(
        ..., description="Percentage of portfolio in top 10 holdings"
    )
    largest_holding_concentration: float
    calculated_at: datetime
