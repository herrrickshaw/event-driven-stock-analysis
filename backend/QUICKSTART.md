# Quick Start Guide

Get the FastAPI backend running in 5 minutes.

## Prerequisites

- Python 3.10+
- PostgreSQL 13+ (or SQLite for testing)
- pip or poetry

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your database URL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/stock_analysis
```

For local testing with SQLite:
```env
DATABASE_URL=sqlite:///./test.db
```

## 3. Initialize Database

```bash
python -c "from models import init_db; init_db()"
```

This creates all tables defined in the models.

## 4. Start the Server

```bash
uvicorn main:app --reload
```

Or use Python directly:
```bash
python main.py
```

Server will start at `http://localhost:8000`

## 5. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Try the API

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Get API Info
```bash
curl http://localhost:8000/
```

All endpoints currently return `NotImplementedError` with a note that implementation is pending. Start implementing by finding the `TODO` comments in:
- `routers/*.py` - Endpoint stubs
- `services/*.py` - Service method stubs
- Add your logic inside the TODO sections

## Project Structure Overview

```
├── app/main.py               # FastAPI app setup
├── config/settings.py        # Configuration
├── models/                   # SQLAlchemy ORM
├── schemas/                  # Pydantic schemas
├── services/                 # Business logic
├── routers/                  # API endpoints
└── utils/                    # Utilities & errors
```

## Available Endpoints

### Portfolio Analysis (3)
- `POST /api/portfolio/snapshot` - Portfolio snapshot
- `POST /api/portfolio/returns` - Portfolio returns
- `POST /api/portfolio/benchmark` - Benchmark comparison

### Risk Calculation (4)
- `POST /api/risk/volatility` - Portfolio volatility
- `POST /api/risk/var` - Value at Risk
- `POST /api/risk/correlation` - Correlation matrix
- `POST /api/risk/exposure` - Exposure breakdown

### Rebalancing (3)
- `POST /api/rebalance/schedule` - Schedule rebalancing
- `POST /api/rebalance/drift` - Check drift
- `POST /api/rebalance/execute` - Execute rebalancing

### Alerts (2)
- `POST /api/alerts/status` - Alert status
- `POST /api/alerts/trigger` - Trigger alerts

### Reporting (2)
- `POST /api/reports/daily` - Daily report
- `POST /api/reports/monthly` - Monthly report

## Running Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# With coverage
pytest --cov=.

# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration
```

## Development Workflow

1. **Add a model**: Edit `models/__init__.py`
2. **Add a schema**: Edit `schemas/*.py`
3. **Add a service method**: Edit `services/*.py`
4. **Add an endpoint**: Edit `routers/*.py`
5. **Write tests**: Add to `tests/unit/` or `tests/integration/`
6. **Run server**: `uvicorn main:app --reload`

## Common Tasks

### Add a New Endpoint

1. Define request/response in `schemas/`
2. Add service method in `services/`
3. Add router endpoint in `routers/`
4. Test with pytest

Example (adding a new risk endpoint):
```python
# In schemas/risk.py
class MyRiskMetricResponse(BaseModel):
    portfolio_id: int
    metric_value: float

# In services/risk_calculator.py
def calculate_my_metric(self, portfolio_id: int) -> MyRiskMetricResponse:
    # TODO: Implement calculation
    raise NotImplementedError()

# In routers/risk.py
@router.post("/my-metric", response_model=MyRiskMetricResponse)
async def calculate_my_metric(portfolio_id: int, db: Session = Depends(get_db)):
    service = RiskCalculatorService(db)
    return service.calculate_my_metric(portfolio_id)
```

### Connect to PostgreSQL

1. Install PostgreSQL
2. Create database:
```sql
CREATE DATABASE stock_analysis;
```

3. Set connection string in `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/stock_analysis
```

4. Initialize tables:
```bash
python -c "from models import init_db; init_db()"
```

### Enable Debug Mode

Set in `.env`:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

Then restart the server.

## Troubleshooting

### Port Already in Use
```bash
# Change port
uvicorn main:app --port 8001
```

### Database Connection Error
- Check `DATABASE_URL` in `.env`
- Verify PostgreSQL is running
- Check credentials and permissions

### Import Errors
- Ensure you're in project root directory
- Run `pip install -r requirements.txt`
- Check Python version is 3.10+

### Tests Fail
- Use SQLite for tests (default in conftest.py)
- Run `pytest -v` for detailed output
- Check that dependencies are installed

## Next Steps

1. Read `README.md` for full documentation
2. Check `PROJECT_STRUCTURE.md` for detailed architecture
3. Implement the TODO endpoints
4. Add authentication (see utils/errors.py)
5. Integrate with yfinance or other data sources
6. Add background tasks with Celery
7. Deploy with Docker

## Documentation

- **README.md** - Complete API and architecture documentation
- **PROJECT_STRUCTURE.md** - Detailed project structure and organization
- **CLAUDE.md** - Development notes (if in your repo)

## Support

For issues or questions:
1. Check the endpoint documentation in `/docs`
2. Review the service docstrings
3. Look at test examples in `tests/`
4. Read the README for architectural details

Happy coding!
