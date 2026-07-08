"""
Portfolio and Holdings ORM models.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Portfolio(Base):
    """Portfolio model representing an investor's portfolio."""

    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    benchmarks = relationship("Benchmark", back_populates="portfolio", cascade="all, delete-orphan")
    rebalance_history = relationship("RebalanceEvent", back_populates="portfolio", cascade="all, delete-orphan")


class Holding(Base):
    """Individual holding in a portfolio."""

    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    market = Column(String, nullable=False)  # e.g., 'india', 'us', 'europe'
    quantity = Column(Numeric(15, 6), nullable=False)
    purchase_price = Column(Numeric(15, 2), nullable=False)
    current_price = Column(Numeric(15, 2), nullable=False)
    weight = Column(Float, nullable=True)  # Portfolio weight %
    added_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="holdings")


class Benchmark(Base):
    """Benchmark indices for portfolio comparison."""

    __tablename__ = "benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    symbol = Column(String, nullable=False)
    market = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="benchmarks")
