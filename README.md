# Event-Driven Stock Analysis

Architecture blueprint plus a partly implemented FastAPI/React backend for monitoring and rebalancing a
multi-market equity portfolio (India, USA, Europe, Japan, Korea, UK, Brazil, China). It contains the design
documents, an in-process market-event bus with a live watchlist, an offline OHLCV history loader for PostgreSQL,
Kubernetes manifests and a React dashboard skeleton.

> Status: research-only / work in progress. The event bus, watchlist and OHLCV loader are working code; the
> portfolio, risk, rebalancing, alert and reporting services are signature-only stubs that raise
> `NotImplementedError`. Educational use only; not investment advice. The performance targets in the
> design documents are design goals, not backtested results.

## What it does
- Publishes and subscribes to market events in-process (`backend/events/event_bus.py`) with a bounded history.
- Keeps a live watchlist of tickers per market (`backend/events/portfolio_monitor.py`), exposed via `/api/alerts/*`
  including a Server-Sent-Events stream.
- Loads up to 5 years of daily OHLCV from yfinance into PostgreSQL with retry/back-off, validation and
  resumable progress (`backend/db/load_historical_data.py`).
- Provides market holiday calendars, approximate FX conversion, ticker-suffix mapping and data-quality metrics
  (`backend/db/market_utils.py`).
- Defines the REST surface (portfolio, risk, rebalance, alerts, reports routers) and Pydantic schemas for the
  planned services.
- Documents the target TOGAF architecture, workflows, deployment (Kubernetes) and dashboard design.

> New here? See [How to use this repo with AI](HOW_TO_USE_WITH_AI.md) or the [Colab notebook](https://colab.research.google.com/github/herrrickshaw/event-driven-stock-analysis/blob/main/notebooks/colab_test.ipynb).

## Quick start
```bash
git clone https://github.com/herrrickshaw/event-driven-stock-analysis.git
cd event-driven-stock-analysis
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt pytest
pytest                        # offline tests: event bus, OHLCV cleaning, market utils
```
Running the API (`cd backend && uvicorn main:app --reload`) additionally needs a PostgreSQL database
configured through `DATABASE_URL` (the app creates its tables on start-up). Data files are stored with Git LFS,
which is currently unreachable; clone with `GIT_LFS_SKIP_SMUDGE=1` (see `DATA_ACCESS.md`).

## How it works
| Stage | Module | Output |
|---|---|---|
| Load history | `backend/db/load_historical_data.py` (+ `ohlcv_clean.py`) | rows in PostgreSQL `ohlcv_history` |
| Detect / publish events | `backend/routers/alerts.py` -> `events/event_bus.py` | `MarketEvent` in history, SSE stream |
| Track watchlist | `events/portfolio_monitor.py` | tickers per market |
| Portfolio services | `backend/services/*` | stubs (to be implemented) |
| API | `backend/app/main.py`, `backend/routers/*` | REST under `/api/...` |
| UI | `frontend/` (React + Vite + TypeScript) | dashboard skeleton |

The bus is a single-process pub/sub (no Kafka): enough for one API instance and its SSE endpoint.
`ohlcv_clean.py` holds the pure cleaning and back-off logic so it can be tested without a database or network.

## Repository layout
| Path | Purpose |
|---|---|
| `backend/app`, `backend/routers`, `backend/schemas` | FastAPI app, routes, request/response models |
| `backend/events` | event bus and watchlist |
| `backend/db` | historical loader, cleaning helpers, market utilities, placeholder store clients |
| `backend/services`, `backend/models` | service stubs and SQLAlchemy models |
| `backend/cassandra` | Cassandra client, schema and init script for the planned live store |
| `backend/tests` | earlier test suite (needs PostgreSQL; not run in CI) |
| `tests/` | offline pytest suite and golden baseline used by this README's `pytest` command |
| `frontend/` | React dashboard skeleton |
| `infrastructure/k8s` | Kubernetes manifests |
| `data/market_data` | gzipped per-market OHLCV samples (Git LFS) and `SCHEMA.json` |
| `docs/` | design documents, including the original README (`docs/PROJECT_OVERVIEW.md`) |

## Data sources
| Source | What is taken | Access route | Licence / caveat |
|---|---|---|---|
| Yahoo Finance via `yfinance` | daily OHLCV | `yf.download` in the loader | unofficial API; personal/educational use; subject to Yahoo terms |
| Bundled samples | `data/market_data/*_ohlcv.csv.gz` | Git LFS | LFS currently unreachable; see `DATA_ACCESS.md` |

## Configuration
- `DATABASE_URL` and other settings: `backend/config/settings.py` (pydantic-settings, `.env` supported).
- Loader flags: `--markets`, `--resume`, `--only-missing`, `--dry-run`, `--db-host/--db-port/--db-user/--db-password/--db-name`,
  `--log-level`. `--market-file`, `--batch-size` and `--validate-only` are accepted but not yet used.
- No secrets are committed; pass database credentials via flags or environment.

## Testing
```bash
pytest -q            # from the repo root; offline, no database or network
```

## Limitations and known issues
- Most services (`backend/services/*`) are stubs; their routes fail until implemented.
- Loader starter stock lists use bare tickers without an exchange qualifier (e.g. `RELIANCE`, `AAPL`), and
  `--db-user` defaults to a personal username; both should be made explicit.
- The cleaner always drops the first row of a series (its `pct_change` is NaN) and measures changes across gaps
  left by earlier row removals.
- The existing `.github/workflows/ci-cd.yml` refers to paths (`requirements.txt`, `tests/backend`) that do not exist.
- Statistics in `docs/PROJECT_OVERVIEW.md` (stock counts, CAGR/Sharpe targets) are unverified design claims.

## Related repositories
- [`herrrickshaw/repo-data-dedup`](https://github.com/herrrickshaw/repo-data-dedup): LFS inventory and migration plan (see `DATA_ACCESS.md`).

## Licence
MIT (see `LICENSE`).
