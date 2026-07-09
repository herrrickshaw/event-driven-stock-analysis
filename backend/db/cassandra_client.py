"""Placeholder client for the Cassandra-backed live market-data store
(instruments/stock_quotes/price_history -- see docs/SCHEMA.md).

Not yet implemented against a real cluster. The FastAPI app's own tables
(portfolios, alerts, risk metrics, ...) use the SQLAlchemy models in
`models/`, which are unrelated to this. This module exists so
`db.cassandra_client` is importable and patchable -- `tests/conftest.py`
mocks it to simulate the store being up or down. Replace with a real
cassandra-driver-backed client when the live market-data pipeline
(see `load_historical_data.py`) is wired up to serve the API directly.
"""


def is_available() -> bool:
    return False


def connect() -> bool:
    return False


def close() -> None:
    return None
