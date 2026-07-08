# Event-Driven Stock Analysis API - Project Structure

Complete FastAPI backend scaffold with 12 REST endpoints across 6 services.

## Project Tree

```
event-driven-stock-analysis/
├── app/
│   ├── __init__.py                    # App package init
│   └── main.py                        # FastAPI app factory, config, middleware, exception handlers
├── config/
│   ├── __init__.py
│   └── settings.py                    # Pydantic Settings - environment configuration
├── models/
│   ├── __init__.py                    # Imports all ORM models
│   ├── base.py                        # SQLAlchemy engine, SessionLocal, Base declarative
│   ├── portfolio.py                   # Portfolio, Holding, Benchmark models
│   └── risk.py                        # RiskMetric, Exposure, Correlation models
│   (RebalanceEvent, Alert, AlertEvent, Report in __init__.py)
├── schemas/
│   ├── __init__.py                    # Imports all Pydantic schemas
│   ├── portfolio.py                   # PortfolioSnapshot, Returns, Benchmark schemas
│   ├── risk.py                        # Volatility, VaR, Correlation, Exposure schemas
│   ├── rebalance.py                   # Rebalance schedule, drift, execution schemas
│   ├── alert.py                       # Alert status, trigger schemas
│   └── report.py                      # Daily report, monthly report schemas
├── services/
│   ├── __init__.py                    # Imports all service classes
│   ├── portfolio_analyzer.py          # PortfolioAnalyzerService (3 methods)
│   ├── risk_calculator.py             # RiskCalculatorService (6 methods)
│   ├── rebalancing_engine.py          # RebalancingEngineService (5 methods)
│   ├── alert_engine.py                # AlertEngineService (8 methods)
│   └── reporting.py                   # ReportingService (7 methods)
├── routers/
│   ├── __init__.py                    # Imports all routers
│   ├── portfolio.py                   # 3 endpoints: snapshot, returns, benchmark
│   ├── risk.py                        # 4 endpoints: volatility, var, correlation, exposure
│   ├── rebalance.py                   # 3 endpoints: schedule, drift, execute
│   ├── alerts.py                      # 2 endpoints: status, trigger
│   └── reports.py                     # 2 endpoints: daily, monthly
├── utils/
│   ├── __init__.py                    # Imports utilities
│   ├── errors.py                      # Custom exception classes (8 types)
│   └── logging.py                     # JSON logging configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures and configuration
│   ├── unit/
│   │   ├── __init__.py
│   │   └── test_portfolio_service.py   # Sample unit tests
│   └── integration/
│       ├── __init__.py
│       └── test_portfolio_endpoints.py # Sample integration tests
├── main.py                            # Application entry point
├── requirements.txt                   # Python dependencies (17 packages)
├── .env.example                       # Environment variables template
├── pytest.ini                         # Pytest configuration
├── README.md                          # Complete documentation
└── PROJECT_STRUCTURE.md               # This file
```

## File Count Summary

- **Total Files**: 41
- **Python Files**: 33
- **Configuration Files**: 3
- **Documentation**: 2
- **Test Files**: 5

## API Endpoints (12 Total)

### Portfolio Analysis (3)
```
POST /api/portfolio/snapshot   # Get portfolio snapshot
POST /api/portfolio/returns    # Get portfolio returns
POST /api/portfolio/benchmark  # Compare with benchmark
```

### Risk Calculation (4)
```
POST /api/risk/volatility      # Calculate volatility
POST /api/risk/var             # Calculate VaR
POST /api/risk/correlation     # Calculate correlations
POST /api/risk/exposure        # Calculate exposure
```

### Rebalancing (3)
```
POST /api/rebalance/schedule   # Schedule rebalancing
POST /api/rebalance/drift      # Check drift
POST /api/rebalance/execute    # Execute rebalancing
```

### Alerts (2)
```
POST /api/alerts/status        # Get alert status
POST /api/alerts/trigger       # Trigger alerts
```

### Reporting (2)
```
POST /api/reports/daily        # Generate daily report
POST /api/reports/monthly      # Generate monthly report
```

## Database Schema

### 11 SQLAlchemy Models

**Portfolio Management:**
- `Portfolio` - User portfolio container
- `Holding` - Individual asset position
- `Benchmark` - Benchmark indices

**Risk Analysis:**
- `RiskMetric` - Volatility, VaR, beta, Sharpe
- `Exposure` - Sector, geography, currency exposure
- `Correlation` - Pairwise correlations

**Operations:**
- `RebalanceEvent` - Rebalancing operations
- `Alert` - Alert configurations
- `AlertEvent` - Triggered alerts
- `Report` - Generated reports

All models include:
- Timestamps (created_at, updated_at)
- Proper indexing
- Foreign key relationships
- Cascade delete where appropriate

## ORM Models Detail

### Portfolio
```python
id, name, user_id, description, currency
created_at, updated_at
relationships: holdings[], benchmarks[], rebalance_history[]
```

### Holding
```python
id, portfolio_id, symbol, market, quantity, purchase_price, current_price
weight, added_at, updated_at
relationship: portfolio
```

### RiskMetric
```python
id, portfolio_id, metric_type, value
calculated_at, lookback_period
indices: (portfolio_id, metric_type)
```

### RebalanceEvent
```python
id, portfolio_id, event_type, target_weights, executed_at
status, created_at
relationship: portfolio
```

### Alert
```python
id, portfolio_id, alert_type, trigger_condition
threshold_value, is_active
created_at, updated_at
```

## Pydantic Schemas (15 Total)

**Portfolio Schemas (5):**
- PortfolioSnapshotResponse
- PortfolioReturnsResponse
- BenchmarkComparison
- HoldingCreate, HoldingResponse, etc.

**Risk Schemas (4):**
- VolatilityResponse
- VaRResponse
- CorrelationMatrixResponse
- ExposureResponse

**Rebalance Schemas (4):**
- RebalanceScheduleRequest
- RebalanceDriftRequest
- RebalanceDriftResponse
- RebalanceExecutionResponse

**Alert Schemas (3):**
- AlertStatusResponse
- AlertTriggerRequest
- AlertTriggerResponse

**Report Schemas (2):**
- DailyReportResponse
- MonthlyReportResponse

## Services Architecture

Each service is a stateless class with database session dependency injection:

### PortfolioAnalyzerService (3 methods)
- `get_portfolio_snapshot()` - Current portfolio metrics
- `calculate_returns()` - Returns for any period
- `compare_with_benchmark()` - Benchmark comparison

### RiskCalculatorService (6 methods)
- `calculate_volatility()` - Portfolio volatility
- `calculate_var()` - Value at Risk metrics
- `calculate_correlations()` - Correlation matrix
- `calculate_exposure()` - Exposure breakdown
- `calculate_beta()` - Beta coefficient
- `calculate_sharpe_ratio()` - Sharpe ratio

### RebalancingEngineService (5 methods)
- `schedule_rebalancing()` - Schedule operations
- `calculate_drift()` - Drift analysis
- `execute_rebalancing()` - Execute trades
- `get_rebalance_actions()` - Trade actions
- `estimate_rebalancing_costs()` - Cost estimation

### AlertEngineService (8 methods)
- `get_alert_status()` - Alert summary
- `trigger_alerts()` - Check and trigger
- `check_drift_alert()` - Drift check
- `check_volatility_alert()` - Volatility check
- `check_correlation_alert()` - Correlation check
- `check_loss_alert()` - Loss check
- `check_concentration_alert()` - Concentration check
- `acknowledge_alert()` - Mark acknowledged

### ReportingService (7 methods)
- `generate_daily_report()` - Daily metrics
- `generate_monthly_report()` - Monthly metrics
- `calculate_daily_performance()` - Daily performance
- `calculate_monthly_performance()` - Monthly performance
- `identify_top_movers()` - Top gains/losses
- `calculate_sector_performance()` - By sector
- `save_report_to_db()` - Persistence

## Error Handling (8 Custom Exceptions)

```python
APIError                    # Base (400)
PortfolioNotFoundError      # 404
HoldingNotFoundError        # 404
ValidationError             # 422
InvalidWeightsError         # 422
InsufficientDataError       # 400
DatabaseError               # 500
ExternalServiceError        # 503
CalculationError            # 500
```

## Configuration Management

**Environment Variables** (via Pydantic Settings):
- `APP_NAME` - Application name
- `APP_VERSION` - Version string
- `DEBUG` - Debug mode
- `DATABASE_URL` - PostgreSQL connection string
- `API_PREFIX` - API route prefix
- `CORS_ORIGINS` - Allowed origins
- `LOG_LEVEL` - Logging level
- `LOG_FORMAT` - JSON or text
- `RISK_FREE_RATE` - Risk calculations
- `CONFIDENCE_LEVEL` - VaR confidence
- `LOOKBACK_PERIOD` - Historical lookback

## FastAPI Features

**Middleware:**
- CORS middleware with configurable origins
- Exception handling with custom responses
- Structured JSON logging

**Event Handlers:**
- Startup: Database initialization, logging
- Shutdown: Cleanup logging

**Documentation:**
- Auto-generated Swagger UI at /docs
- ReDoc at /redoc
- OpenAPI schema at /openapi.json

**Health Check:**
- GET /api/health
- GET / (root with docs links)

## Testing Structure

**Fixtures (conftest.py):**
- `test_db` - In-memory SQLite
- `db_session` - Test session
- `test_app` - FastAPI app
- `client` - TestClient
- `sample_portfolio` - Test portfolio
- `sample_holdings` - Test holdings

**Test Organization:**
- `tests/unit/` - Unit tests for services
- `tests/integration/` - Integration tests for endpoints
- Sample test files with patterns and TODOs

**Pytest Configuration:**
- Markers: unit, integration, slow
- Test discovery patterns
- pytest.ini with configuration

## Dependencies (requirements.txt)

**Web Framework:**
- fastapi==0.104.1
- uvicorn[standard]==0.24.0

**Database:**
- sqlalchemy==2.0.23
- psycopg2-binary==2.9.9
- alembic==1.13.0

**Data Validation:**
- pydantic==2.5.0
- pydantic-settings==2.1.0

**Data Processing:**
- pandas==2.1.3
- numpy==1.26.2
- scipy==1.11.4

**Security:**
- python-jose[cryptography]==3.3.0
- passlib[bcrypt]==1.7.4

**Testing:**
- pytest==7.4.3
- pytest-asyncio==0.21.1

**Utilities:**
- python-dotenv==1.0.0
- python-multipart==0.0.6
- httpx==0.25.2

## Development Workflow

1. **Install:** `pip install -r requirements.txt`
2. **Configure:** `cp .env.example .env` and edit
3. **Initialize:** `python -c "from models import init_db; init_db()"`
4. **Run:** `uvicorn main:app --reload`
5. **Test:** `pytest` or `pytest -v`
6. **Docs:** Visit `http://localhost:8000/docs`

## Implementation Roadmap

All endpoints have TODO comments for implementation:

- [ ] Implement portfolio snapshot calculation
- [ ] Implement returns calculation
- [ ] Implement benchmark comparison
- [ ] Implement volatility calculation
- [ ] Implement VaR calculation
- [ ] Implement correlation matrix
- [ ] Implement exposure calculation
- [ ] Implement rebalancing logic
- [ ] Implement drift detection
- [ ] Implement alert triggering
- [ ] Implement report generation
- [ ] Add data fetchers (yfinance, etc.)
- [ ] Add authentication/JWT
- [ ] Add WebSocket support
- [ ] Add background tasks
- [ ] Add email notifications

## Architecture Highlights

- **Clean Separation**: Routers → Services → Models
- **Dependency Injection**: FastAPI native DI for sessions
- **Type Safety**: Full Pydantic + SQLAlchemy typing
- **Error Handling**: Custom exceptions with proper HTTP codes
- **Logging**: Structured JSON logs for production
- **Testing**: Fixtures, mocks, and test client ready
- **Scalability**: Service layer can be extended independently
- **Documentation**: Auto-generated + README + code comments

## Next Steps

1. Implement each TODO in service methods
2. Add data fetchers for yfinance/APIs
3. Create alembic migrations
4. Add authentication and authorization
5. Add background task queue (Celery)
6. Add WebSocket support for real-time updates
7. Add caching layer (Redis)
8. Add email/notification service
9. Deploy with Docker
10. Set up CI/CD pipeline
