"""Placeholder client for a direct PostgreSQL connectivity check, separate
from the SQLAlchemy engine in `models/base.py` (which the app actually uses
for its own tables). Exists so `db.postgres_client` is importable and
patchable -- `tests/conftest.py` mocks it to simulate the store being up
or down.
"""


def is_available() -> bool:
    return False


def connect() -> bool:
    return False


def close() -> None:
    return None
