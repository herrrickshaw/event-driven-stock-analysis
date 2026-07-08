# Event-Driven Stock Analysis API

A comprehensive FastAPI backend for portfolio analysis, risk management, rebalancing, alerting, and reporting across multiple global markets.

## Project Structure

```
event-driven-stock-analysis/
├── app/                      # FastAPI application package
│   ├── __init__.py
│   └── main.py              # App factory and configuration
├── config/                  # Configuration management
│   ├── __init__.py
│   └── settings.py          # Pydantic settings
├── models/                  # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── base.py             # Database setup, session factory
│   ├── portfolio.py        # Portfolio, Holding, Benchmark models
│   ├── risk.py             # Risk metrics models
│   └── (RebalanceEvent, Alert, Report in __init__.py)
├── schemas/                 # Pydantic request/response schemas
│   ├── __init__.py
│   ├── portfolio.py        # Portfolio schemas
│   ├── risk.py             # Risk calculation schemas
│   ├── rebalance.py        # Rebalancing schemas
│   ├── alert.py            # Alert schemas
│   └── report.py           # Report schemas
├── services/               # Business logic services
│   ├── __init__.py
│   ├── portfolio_analyzer.py      # Portfolio analysis
│   ├── risk_calculator.py         # Risk metrics
│   ├── rebalancing_engine.py      # Rebalancing logic
│   ├── alert_engine.py            # Alert management
│   └── reporting.py               # Report generation
├── routers/                # API route handlers
│   ├── __init__.py
│   ├── portfolio.py       # /api/portfolio/* endpoints
│   ├── risk.py            # /api/risk/* endpoints
│   ├── rebalance.py       # /api/rebalance/* endpoints
│   ├── alerts.py          # /api/alerts/* endpoints
│   └── reports.py         # /api/reports/* endpoints
├── utils/                 # Utilities
│   ├── __init__.py
│   ├── errors.py          # Custom exceptions
│   └── logging.py         # Logging configuration
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Features

### 6 Core Services

#### 1. Portfolio Analyzer (3 endpoints)
- **GET /api/portfolio/snapshot** - Current portfolio value, returns, and holdings
- **POST /api/portfolio/returns** - Calculate returns for specified period
- **POST /api/portfolio/benchmark** - Compare performance against benchmark index

#### 2. Risk Calculator (4 endpoints)
- **POST /api/risk/volatility** - Annualized portfolio volatility (standard deviation)
- **POST /api/risk/var** - Value at Risk (VaR) at 95% and 99% confidence levels
- **POST /api/risk/correlation** - Pairwise correlation matrix between holdings
- **POST /api/risk/exposure** - Portfolio exposure breakdown by sector, geography, currency

#### 3. Rebalancing Engine (3 endpoints)
- **POST /api/rebalance/schedule** - Schedule periodic rebalancing with target weights
- **POST /api/rebalance/drift** - Calculate drift from target allocation
- **POST /api/rebalance/execute** - Execute rebalancing trades

#### 4. Alert Engine (2 endpoints)
- **POST /api/alerts/status** - Get all active alerts and their status
- **POST /api/alerts/trigger** - Check conditions and trigger alerts (drift, volatility, correlation, loss)

#### 5. Reporting (2 endpoints)
- **POST /api/reports/daily** - Comprehensive daily report with performance and risk metrics
- **POST /api/reports/monthly** - Monthly report with trends, transactions, and benchmarking

#### 6. System Health
- **GET /api/health** - System health check
- **GET /** - API information and documentation links

## Database Models

### Core Models
- **Portfolio** - User portfolio container
- **Holding** - Individual stock/asset position
- **Benchmark** - Benchmark indices for comparison

### Risk Models
- **RiskMetric** - Calculated volatility, VaR, beta, Sharpe ratio
- **Exposure** - Sector, geography, currency, asset class exposures
- **Correlation** - Pairwise correlations between holdings

### Operations Models
- **RebalanceEvent** - Scheduled and executed rebalancing operations
- **Alert** - Alert configurations (drift, volatility, correlation, loss thresholds)
- **AlertEvent** - Triggered alert events with severity levels
- **Report** - Generated daily/monthly reports

## Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 13+
- pip/poetry

### Setup

1. **Clone and install dependencies:**
```bash
cd event-driven-stock-analysis
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database URL and settings
```

3. **Initialize database:**
```bash
python -c "from models import init_db; init_db()"
```

4. **Run the application:**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc docs: `http://localhost:8000/redoc`

## API Endpoints Summary

### Portfolio Analysis (3 endpoints)
```
POST /api/portfolio/snapshot   - Get current portfolio value and metrics
POST /api/portfolio/returns    - Calculate returns for specified period  
POST /api/portfolio/benchmark  - Compare against benchmark index
```

### Risk Calculation (4 endpoints)
```
POST /api/risk/volatility      - Portfolio volatility (annualized)
POST /api/risk/var             - Value at Risk metrics
POST /api/risk/correlation     - Correlation matrix of holdings
POST /api/risk/exposure        - Exposure breakdown by sector/geography/currency
```

### Rebalancing (3 endpoints)
```
POST /api/rebalance/schedule   - Schedule rebalancing with target weights
POST /api/rebalance/drift      - Check drift from target allocation
POST /api/rebalance/execute    - Execute rebalancing trades
```

### Alerts (2 endpoints)
```
POST /api/alerts/status        - Get all active alerts and status
POST /api/alerts/trigger       - Trigger alert checks
```

### Reporting (2 endpoints)
```
POST /api/reports/daily        - Generate daily report
POST /api/reports/monthly      - Generate monthly report
```

## Supported Markets

- **India** - NSE/BSE equities
- **US** - NYSE/NASDAQ equities
- **Europe** - 17 exchanges (London, Frankfurt, Euronext, etc.)
- **Japan** - TSE equities
- **Korea** - KOSPI/KOSDAQ equities

## Configuration

All settings are configured via environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/stock_analysis

# API
API_PREFIX=/api
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Risk Calculations
RISK_FREE_RATE=0.05
CONFIDENCE_LEVEL=0.95
LOOKBACK_PERIOD=252
```

## Architecture

### Layered Architecture
```
HTTP Request
    ↓
Routers (API Endpoints) - Input validation, request parsing
    ↓
Services (Business Logic) - Core calculations and operations
    ↓
Models (Database) - Data persistence
    ↓
PostgreSQL Database
```

### Key Design Patterns
- **Dependency Injection** - FastAPI dependency injection for database sessions
- **Service Layer** - Business logic isolated in services
- **Pydantic Schemas** - Strict input/output validation
- **Error Handling** - Custom exceptions with proper HTTP status codes
- **Structured Logging** - JSON-formatted logs for production

## Error Handling

The API uses custom exception classes for consistent error responses:

- `PortfolioNotFoundError` (404) - Portfolio doesn't exist
- `HoldingNotFoundError` (404) - Holding not found
- `ValidationError` (422) - Invalid input data
- `InvalidWeightsError` (422) - Portfolio weights don't sum to 100%
- `InsufficientDataError` (400) - Not enough data for calculation
- `DatabaseError` (500) - Database operation failed
- `ExternalServiceError` (503) - Third-party service unavailable
- `CalculationError` (500) - Calculation failed

## Development

### Adding a New Endpoint

1. **Define Pydantic schema** in `schemas/`
2. **Create service method** in `services/`
3. **Add router endpoint** in `routers/`
4. **Implement service logic** (TODO stubs provided)

### Testing

```bash
pytest
pytest -v --cov=.
```

### Type Checking

```bash
mypy .
```

## Implementation Roadmap

All endpoint stubs are in place with TODO comments:

- [ ] Portfolio Analyzer - Implement snapshot, returns, benchmark comparison
- [ ] Risk Calculator - Implement volatility, VaR, correlations, exposure
- [ ] Rebalancing Engine - Implement scheduling, drift detection, execution
- [ ] Alert Engine - Implement alert triggering for all condition types
- [ ] Reporting - Implement daily/monthly report generation
- [ ] Data Fetchers - Implement yfinance/external data integration
- [ ] Authentication - Add JWT auth and user management
- [ ] Event System - Add event-driven updates via WebSockets

## Dependencies

Key dependencies in `requirements.txt`:
- **fastapi** - Web framework
- **sqlalchemy** - ORM for database
- **pydantic** - Data validation
- **pandas** - Data manipulation
- **numpy/scipy** - Numerical calculations
- **psycopg2** - PostgreSQL adapter

## License

MIT
