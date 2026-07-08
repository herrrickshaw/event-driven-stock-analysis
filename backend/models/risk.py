"""
Risk metrics and analysis ORM models.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class RiskMetric(Base):
    """Calculated risk metrics for a portfolio."""

    __tablename__ = "risk_metrics"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    metric_type = Column(String, nullable=False)  # volatility, var, correlation, beta, sharpe
    value = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    lookback_period = Column(Integer, default=252)  # trading days

    __table_args__ = ({"indexes": [("portfolio_id", "metric_type")]},)


class Exposure(Base):
    """Portfolio exposures (sector, geography, currency)."""

    __tablename__ = "exposures"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    exposure_type = Column(String, nullable=False)  # sector, geography, currency, asset_class
    category = Column(String, nullable=False)
    value = Column(Float, nullable=False)  # percentage
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Correlation(Base):
    """Pairwise correlations between holdings."""

    __tablename__ = "correlations"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    symbol_1 = Column(String, nullable=False)
    symbol_2 = Column(String, nullable=False)
    correlation_value = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
