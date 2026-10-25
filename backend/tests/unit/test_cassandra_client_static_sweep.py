"""CassandraClient data-class regressions (static sweep 2026-10-25, mypy call-arg).

The driver is stubbed so this runs without a cluster and even when the
``backend/cassandra/`` directory shadows the ``cassandra`` driver package.
"""
import os
import sys
import types
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="module")
def cc():
    saved = {k: v for k, v in sys.modules.items() if k == "cassandra" or k.startswith("cassandra.")}
    fake = types.ModuleType("cassandra")
    for sub in ("cluster", "policies", "auth", "concurrent", "util"):
        m = types.ModuleType(f"cassandra.{sub}")
        m.__getattr__ = lambda name, _m=m: MagicMock(name=name)
        setattr(fake, sub, m)
        sys.modules[f"cassandra.{sub}"] = m
    sys.modules["cassandra"] = fake
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cassandra"))
    sys.modules.pop("cassandra_client", None)
    import cassandra_client as mod
    yield mod
    sys.path.pop(0)
    sys.modules.pop("cassandra_client", None)
    for k in [k for k in sys.modules if k == "cassandra" or k.startswith("cassandra.")]:
        del sys.modules[k]
    sys.modules.update(saved)


def _client(cc, rows=()):
    client = cc.CassandraClient.__new__(cc.CassandraClient)
    client.session = MagicMock()
    client.session.execute.return_value = list(rows)
    client._prepared_statements = {k: f"<{k}>" for k in ("insert_quote", "search_by_symbol", "search_by_name")}
    return client


def _quote(cc, **extra):
    base = dict(market="india", yf_ticker="RELIANCE.NS", cmp=2850.5, rsi=58.5, ema_50=2820.75,
                ema_200=2750.0, pe=26.5, pb=3.8, roe=12.5, opm=18.5, market_cap=1.75e6,
                volume=2_500_000, high_52w=3050.0, low_52w=2100.0, debt_to_equity=0.45)
    base.update(extra)
    return cc.QuoteSnapshot(**base)


def test_insert_quote_binds_all_22_columns(cc):
    """insert_quote read quote.open/high/low/close, which QuoteSnapshot did not define,
    so every insert raised AttributeError, was swallowed, and returned False."""
    client = _client(cc)
    assert client.insert_quote(_quote(cc)) is True
    (_stmt, values), _ = client.session.execute.call_args
    assert len(values) == 22
    assert values[2] == Decimal("2850.5")
    assert values[3:7] == [None, None, None, None]  # OHLC not supplied -> NULL


def test_quote_snapshot_accepts_ohlc_like_the_example_script(cc):
    q = _quote(cc, open=2840.0, high=2875.0, low=2835.0, close=2850.5)
    client = _client(cc)
    assert client.insert_quote(q) is True
    (_stmt, values), _ = client.session.execute.call_args
    assert values[3:7] == [Decimal("2840.0"), Decimal("2875.0"), Decimal("2835.0"), Decimal("2850.5")]


def test_search_by_symbol_returns_rows_from_the_search_table(cc):
    """instruments_by_symbol has no isin/country columns but Instrument requires them,
    so every search raised TypeError (swallowed) and returned []."""
    row = {"market": "india", "symbol": "TEST001", "yf_ticker": "TEST001.NS",
           "name": "Test Company Ltd", "exchange": "NSE"}
    found = _client(cc, [row]).search_by_symbol("india", "TEST001")
    assert [i.yf_ticker for i in found] == ["TEST001.NS"]
    assert found[0].isin is None and found[0].country == ""


def test_search_by_name_prefix_returns_rows_from_the_search_table(cc):
    row = {"market": "india", "name_lower": "test company ltd", "yf_ticker": "TEST001.NS",
           "symbol": "TEST001", "exchange": "NSE"}
    found = _client(cc, [row]).search_by_name_prefix("india", "Test")
    assert [i.name for i in found] == ["test company ltd"]
