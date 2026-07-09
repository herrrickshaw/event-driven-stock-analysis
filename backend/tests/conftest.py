"""
Pytest configuration and shared fixtures for E2E tests.

Provides:
- Database fixtures (Cassandra, PostgreSQL mocks)
- API client fixtures
- Sample portfolio and market data
- Event bus fixtures
- Alert simulation fixtures
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator, Dict, Any, List
from unittest import mock

import pytest
import pytest_asyncio
import pytz
from fastapi.testclient import TestClient
from pydantic import BaseModel

# ──────────────────────────────────────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def logger():
    """Configure pytest logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    return logging.getLogger('test')


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI & Database Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_cassandra():
    """Mock Cassandra client for testing without database."""
    with mock.patch('db.cassandra_client') as mock_cass:
        mock_cass.is_available.return_value = True
        mock_cass.connect.return_value = True
        mock_cass.close.return_value = None
        yield mock_cass


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL connection for testing."""
    with mock.patch('db.postgres_client') as mock_pg:
        mock_pg.is_available.return_value = True
        mock_pg.connect.return_value = True
        mock_pg.close.return_value = None
        yield mock_pg


@pytest.fixture
def test_client(mock_cassandra, mock_postgres):
    """FastAPI test client with mocked database."""
    from main import app
    return TestClient(app)


# ──────────────────────────────────────────────────────────────────────────────
# Market Data Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_tickers() -> Dict[str, List[str]]:
    """Sample tickers across all markets."""
    return {
        'india': ['RELIANCE', 'HDFCBANK', 'INFY', 'TCS', 'LT'],
        'us': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
        'europe': ['ADS.DE', 'RIO.L', 'MC.PA', 'NOKIA.HE', 'UNA.MI'],
        'japan': ['7203.T', '9984.T', '6981.T', '8001.T', '3382.T'],
        'korea': ['005930.KS', '000660.KS', '035420.KQ', '051910.KQ', '096770.KQ'],
        'china': ['600519.SS', '000858.SZ', '000651.SZ', '600276.SS', '603501.SS'],
    }


@pytest.fixture
def sample_quotes() -> Dict[str, Dict[str, float]]:
    """Sample real-world-like OHLCV data."""
    now = datetime.now(timezone.utc)
    base_time = (now - timedelta(days=100)).isoformat()

    return {
        'RELIANCE.NS': {
            'open': 2850.0,
            'high': 2900.0,
            'low': 2800.0,
            'close': 2875.5,
            'volume': 45000000,
            'rsi': 62.3,
            'rsi_signal': 'healthy',
            'ema_50': 2850.0,
            'pe': 24.5,
            'pb': 4.2,
            'roe': 18.5,
            'opm': 12.3,
            'market_cap': 2850000000000,  # ₹285 trillion
            'high_52w': 3050.0,
            'low_52w': 2500.0,
            'debt_to_equity': 0.45,
            'date': base_time,
        },
        'HDFCBANK.NS': {
            'open': 1650.0,
            'high': 1700.0,
            'low': 1630.0,
            'close': 1680.5,
            'volume': 38000000,
            'rsi': 58.2,
            'rsi_signal': 'healthy',
            'ema_50': 1670.0,
            'pe': 18.3,
            'pb': 2.8,
            'roe': 22.1,
            'opm': 35.2,
            'market_cap': 1650000000000,
            'high_52w': 1900.0,
            'low_52w': 1500.0,
            'debt_to_equity': 0.85,
            'date': base_time,
        },
        'INFY': {
            'open': 1450.0,
            'high': 1500.0,
            'low': 1420.0,
            'close': 1475.0,
            'volume': 28000000,
            'rsi': 55.1,
            'rsi_signal': 'neutral',
            'ema_50': 1460.0,
            'pe': 22.5,
            'pb': 6.2,
            'roe': 28.3,
            'opm': 21.1,
            'market_cap': 750000000000,
            'high_52w': 1650.0,
            'low_52w': 1200.0,
            'debt_to_equity': 0.15,
            'date': base_time,
        },
        'AAPL': {
            'open': 195.5,
            'high': 198.0,
            'low': 194.0,
            'close': 196.8,
            'volume': 52000000,
            'rsi': 61.4,
            'rsi_signal': 'healthy',
            'ema_50': 195.0,
            'pe': 32.1,
            'pb': 48.5,
            'roe': 152.3,
            'opm': 30.2,
            'market_cap': 3000000000000,
            'high_52w': 210.0,
            'low_52w': 170.0,
            'debt_to_equity': 1.95,
            'date': base_time,
        },
    }


@pytest.fixture
def sample_price_history() -> Dict[str, List[Dict[str, Any]]]:
    """Generate 100 days of price history for testing."""
    now = datetime.now(timezone.utc)
    history = {}

    for ticker in ['RELIANCE.NS', 'HDFCBANK.NS', 'AAPL', 'MSFT']:
        ticker_history = []
        price = 2800.0 if 'RELIANCE' in ticker else 1650.0 if 'HDFC' in ticker else 180.0

        for i in range(100, 0, -1):
            date = (now - timedelta(days=i)).date()
            # Simple random walk
            price += (hash(f"{ticker}_{i}") % 100 - 50) / 100
            ticker_history.append({
                'date': date.isoformat(),
                'close': round(price, 2),
                'volume': 30000000 + (hash(f"{ticker}_{i}") % 10000000),
            })
        history[ticker] = ticker_history

    return history


# ──────────────────────────────────────────────────────────────────────────────
# Portfolio Fixtures
# ──────────────────────────────────────────────────────────────────────────────

class HoldingData(BaseModel):
    """Test holding data."""
    yf_ticker: str
    symbol: str
    name: str
    quantity: float
    purchase_price: float
    purchase_date: str
    market: str = 'india'


@pytest.fixture
def sample_holding() -> HoldingData:
    """Single test holding."""
    return HoldingData(
        yf_ticker='RELIANCE.NS',
        symbol='RELIANCE',
        name='Reliance Industries Limited',
        quantity=100.0,
        purchase_price=2500.0,
        purchase_date='2023-01-15',
        market='india',
    )


@pytest.fixture
def sample_portfolio_india() -> List[HoldingData]:
    """Sample diversified India portfolio."""
    return [
        HoldingData(
            yf_ticker='RELIANCE.NS',
            symbol='RELIANCE',
            name='Reliance Industries',
            quantity=100.0,
            purchase_price=2500.0,
            purchase_date='2023-01-15',
        ),
        HoldingData(
            yf_ticker='HDFCBANK.NS',
            symbol='HDFCBANK',
            name='HDFC Bank',
            quantity=50.0,
            purchase_price=1500.0,
            purchase_date='2023-03-20',
        ),
        HoldingData(
            yf_ticker='INFY.NS',
            symbol='INFY',
            name='Infosys',
            quantity=200.0,
            purchase_price=1350.0,
            purchase_date='2023-02-10',
        ),
        HoldingData(
            yf_ticker='TCS.NS',
            symbol='TCS',
            name='Tata Consultancy Services',
            quantity=75.0,
            purchase_price=3200.0,
            purchase_date='2023-04-05',
        ),
        HoldingData(
            yf_ticker='LT.NS',
            symbol='LT',
            name='Larsen & Toubro',
            quantity=30.0,
            purchase_price=2000.0,
            purchase_date='2023-05-12',
        ),
    ]


@pytest.fixture
def sample_portfolio_us() -> List[HoldingData]:
    """Sample diversified US portfolio."""
    return [
        HoldingData(
            yf_ticker='AAPL',
            symbol='AAPL',
            name='Apple Inc',
            quantity=50.0,
            purchase_price=150.0,
            purchase_date='2023-01-15',
            market='us',
        ),
        HoldingData(
            yf_ticker='MSFT',
            symbol='MSFT',
            name='Microsoft Corporation',
            quantity=30.0,
            purchase_price=250.0,
            purchase_date='2023-02-20',
            market='us',
        ),
        HoldingData(
            yf_ticker='GOOGL',
            symbol='GOOGL',
            name='Alphabet Inc',
            quantity=20.0,
            purchase_price=100.0,
            purchase_date='2023-03-10',
            market='us',
        ),
    ]


@pytest.fixture
def sample_portfolio_global() -> List[HoldingData]:
    """Sample global multi-market portfolio."""
    india = [
        HoldingData(
            yf_ticker='RELIANCE.NS',
            symbol='RELIANCE',
            name='Reliance Industries',
            quantity=100.0,
            purchase_price=2500.0,
            purchase_date='2023-01-15',
        ),
    ]
    us = [
        HoldingData(
            yf_ticker='AAPL',
            symbol='AAPL',
            name='Apple Inc',
            quantity=50.0,
            purchase_price=150.0,
            purchase_date='2023-01-15',
            market='us',
        ),
    ]
    europe = [
        HoldingData(
            yf_ticker='ADS.DE',
            symbol='ADS',
            name='Adidas AG',
            quantity=30.0,
            purchase_price=90.0,
            purchase_date='2023-02-20',
            market='europe',
        ),
    ]
    return india + us + europe


# ──────────────────────────────────────────────────────────────────────────────
# Risk Metrics Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_returns_series() -> Dict[str, List[float]]:
    """Generate daily returns for volatility/VaR testing."""
    import random
    random.seed(42)

    return {
        'RELIANCE.NS': [random.gauss(0.001, 0.02) for _ in range(252)],  # ~1% annual vol
        'HDFCBANK.NS': [random.gauss(0.0005, 0.015) for _ in range(252)],
        'INFY.NS': [random.gauss(0.002, 0.025) for _ in range(252)],
        'AAPL': [random.gauss(0.001, 0.018) for _ in range(252)],
    }


@pytest.fixture
def sample_correlation_matrix() -> Dict[str, Dict[str, float]]:
    """Sample correlation matrix between assets."""
    return {
        'RELIANCE.NS': {'RELIANCE.NS': 1.0, 'HDFCBANK.NS': 0.75, 'INFY.NS': 0.65, 'AAPL': 0.35},
        'HDFCBANK.NS': {'RELIANCE.NS': 0.75, 'HDFCBANK.NS': 1.0, 'INFY.NS': 0.70, 'AAPL': 0.40},
        'INFY.NS': {'RELIANCE.NS': 0.65, 'HDFCBANK.NS': 0.70, 'INFY.NS': 1.0, 'AAPL': 0.50},
        'AAPL': {'RELIANCE.NS': 0.35, 'HDFCBANK.NS': 0.40, 'INFY.NS': 0.50, 'AAPL': 1.0},
    }


# ──────────────────────────────────────────────────────────────────────────────
# Alert & Event Fixtures
# ──────────────────────────────────────────────────────────────────────────────

class AlertEvent(BaseModel):
    """Test alert event."""
    event_type: str  # PRICE_UP | PRICE_DOWN | RSI_OVERBOUGHT | RSI_OVERSOLD | VOLUME_SURGE
    ticker: str
    market: str
    data: Dict[str, Any]
    timestamp: str


@pytest.fixture
def sample_alert_events() -> List[AlertEvent]:
    """Generate sample alert events."""
    now = datetime.now(timezone.utc)
    return [
        AlertEvent(
            event_type='PRICE_UP',
            ticker='RELIANCE',
            market='india',
            data={'old_price': 2800.0, 'new_price': 2875.5, 'change_pct': 2.7},
            timestamp=(now - timedelta(seconds=60)).isoformat(),
        ),
        AlertEvent(
            event_type='RSI_OVERBOUGHT',
            ticker='HDFCBANK',
            market='india',
            data={'rsi': 75.2, 'threshold': 70},
            timestamp=(now - timedelta(seconds=120)).isoformat(),
        ),
        AlertEvent(
            event_type='VOLUME_SURGE',
            ticker='INFY',
            market='india',
            data={'current_volume': 85000000, 'avg_volume': 40000000, 'surge_pct': 112.5},
            timestamp=(now - timedelta(seconds=180)).isoformat(),
        ),
        AlertEvent(
            event_type='RSI_OVERSOLD',
            ticker='AAPL',
            market='us',
            data={'rsi': 28.5, 'threshold': 30},
            timestamp=(now - timedelta(seconds=240)).isoformat(),
        ),
    ]


@pytest.fixture
def sample_rebalancing_scenarios() -> List[Dict[str, Any]]:
    """Generate rebalancing test scenarios."""
    return [
        {
            'name': 'quarterly_rebalance',
            'portfolio': {
                'RELIANCE': {'quantity': 100, 'current_price': 2875.5, 'target_allocation': 0.40},
                'HDFCBANK': {'quantity': 50, 'current_price': 1680.5, 'target_allocation': 0.35},
                'INFY': {'quantity': 200, 'current_price': 1475.0, 'target_allocation': 0.25},
            },
            'portfolio_value': 625000.0,
            'rebalance_threshold': 0.05,  # 5% deviation triggers rebalance
            'expected_actions': ['buy_infy', 'sell_reliance'],
        },
        {
            'name': 'drift_correction',
            'portfolio': {
                'AAPL': {'quantity': 50, 'current_price': 196.8, 'target_allocation': 0.50},
                'MSFT': {'quantity': 30, 'current_price': 350.0, 'target_allocation': 0.50},
            },
            'portfolio_value': 20490.0,
            'rebalance_threshold': 0.03,
            'expected_actions': ['buy_msft', 'sell_aapl'],
        },
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Database Consistency Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_cassandra_rows() -> List[Dict[str, Any]]:
    """Sample rows for Cassandra ↔ PostgreSQL consistency tests."""
    return [
        {
            'market': 'india',
            'yf_ticker': 'RELIANCE.NS',
            'symbol': 'RELIANCE',
            'name': 'Reliance Industries Limited',
            'exchange': 'NSE',
            'country': 'INDIA',
            'cmp': 2875.5,
            'rsi': 62.3,
            'volume': 45000000,
            'market_cap': 2850000000000,
            'seeded_at': datetime.now(timezone.utc).isoformat(),
        },
        {
            'market': 'us',
            'yf_ticker': 'AAPL',
            'symbol': 'AAPL',
            'name': 'Apple Inc',
            'exchange': 'NASDAQ',
            'country': 'USA',
            'cmp': 196.8,
            'rsi': 61.4,
            'volume': 52000000,
            'market_cap': 3000000000000,
            'seeded_at': datetime.now(timezone.utc).isoformat(),
        },
    ]


@pytest.fixture
def sample_postgres_rows() -> List[Dict[str, Any]]:
    """Sample PostgreSQL rows for consistency validation."""
    return [
        {
            'id': 1,
            'market': 'india',
            'ticker': 'RELIANCE',
            'yf_ticker': 'RELIANCE.NS',
            'name': 'Reliance Industries Limited',
            'exchange': 'NSE',
            'last_price': 2875.5,
            'last_rsi': 62.3,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        },
        {
            'id': 2,
            'market': 'us',
            'ticker': 'AAPL',
            'yf_ticker': 'AAPL',
            'name': 'Apple Inc',
            'exchange': 'NASDAQ',
            'last_price': 196.8,
            'last_rsi': 61.4,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        },
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Test Data Files
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    data_dir = Path(__file__).parent / 'data'
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def sample_excel_file(test_data_dir, sample_portfolio_india) -> Path:
    """Generate test Excel file with portfolio."""
    try:
        import openpyxl
        from openpyxl import Workbook
    except ImportError:
        pytest.skip("openpyxl not installed")

    wb = Workbook()
    ws = wb.active
    ws.title = 'Portfolio'

    # Header
    ws.append(['Symbol', 'Quantity', 'Purchase Price', 'Purchase Date', 'Name'])

    # Data
    for holding in sample_portfolio_india:
        ws.append([
            holding.symbol,
            holding.quantity,
            holding.purchase_price,
            holding.purchase_date,
            holding.name,
        ])

    file_path = test_data_dir / 'portfolio.xlsx'
    wb.save(file_path)
    yield file_path
    file_path.unlink(missing_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Event Bus Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def event_bus():
    """Fresh EventBus instance for each test."""
    from events.event_bus import EventBus
    return EventBus(max_history=200)


@pytest.fixture
def event_capture():
    """Capture events published to EventBus."""
    events = []

    def capture_callback(event):
        events.append(event)

    return {'events': events, 'callback': capture_callback}


@pytest.fixture
def portfolio_monitor_mock():
    """Mock portfolio monitor for testing."""
    with mock.patch('events.portfolio_monitor.monitor') as m:
        m.add_tickers.return_value = None
        m.remove_ticker.return_value = None
        m.watched.return_value = ['RELIANCE', 'HDFCBANK', 'INFY']
        m.is_monitoring.return_value = True
        yield m


# ──────────────────────────────────────────────────────────────────────────────
# Test Utilities
# ──────────────────────────────────────────────────────────────────────────────

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line('markers', 'slow: marks tests as slow (deselect with "-m not slow")')
    config.addinivalue_line('markers', 'integration: marks tests as integration tests')
    config.addinivalue_line('markers', 'unit: marks tests as unit tests')
    config.addinivalue_line('markers', 'load: marks tests as load tests')
    config.addinivalue_line('markers', 'data_quality: marks tests as data quality tests')
