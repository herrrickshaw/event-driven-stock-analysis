"""
Database models package.
"""
from .base import Base, engine, SessionLocal, get_db, init_db
from .portfolio import Portfolio, Holding, Benchmark
from .risk import RiskMetric, Exposure, Correlation
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime


class RebalanceEvent(Base):
    """Rebalancing events and drift tracking."""

    __tablename__ = "rebalance_events"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # scheduled, drift_trigger, manual
    target_weights = Column(String, nullable=True)  # JSON
    executed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, executed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="rebalance_history")


class Alert(Base):
    """Alert configurations and history."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    alert_type = Column(String, nullable=False)  # drift, volatility, correlation, loss
    trigger_condition = Column(String, nullable=False)  # JSON condition
    threshold_value = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertEvent(Base):
    """Triggered alert events."""

    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    severity = Column(String)  # info, warning, critical
    message = Column(String)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)


class Report(Base):
    """Generated reports."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    report_type = Column(String, nullable=False)  # daily, monthly, quarterly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    content = Column(String, nullable=True)  # JSON or HTML
    generated_at = Column(DateTime, default=datetime.utcnow)


__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "Portfolio",
    "Holding",
    "Benchmark",
    "RiskMetric",
    "Exposure",
    "Correlation",
    "RebalanceEvent",
    "Alert",
    "AlertEvent",
    "Report",
]
