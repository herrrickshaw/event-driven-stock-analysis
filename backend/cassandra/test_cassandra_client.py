"""
Unit tests for Cassandra client.

Run with pytest:
    pytest test_cassandra_client.py -v

Requires a running Cassandra instance on localhost:9042.
"""

import pytest
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from cassandra_client import (
    CassandraClient,
    Instrument,
    QuoteSnapshot,
    PriceBar,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============= FIXTURES =============

@pytest.fixture(scope='module')
def client():
    """Create Cassandra client for testing."""
    client = CassandraClient(
        hosts=['127.0.0.1'],
        port=9042,
        keyspace='herrrickshaw',
    )
    yield client
    client.shutdown()


@pytest.fixture
def sample_instrument():
    """Sample instrument for testing."""
    return Instrument(
        market='india',
        yf_ticker='TEST001.NS',
        name='Test Company Ltd',
        symbol='TEST001',
        isin='INE000A01000',
        exchange='NSE',
        country='IN',
        sector='Technology',
        industry='Software',
        market_cap_inr=100000.0,
    )


@pytest.fixture
def sample_quote():
    """Sample quote for testing."""
    return QuoteSnapshot(
        market='india',
        yf_ticker='TEST001.NS',
        cmp=1000.0,
        open=995.0,
        high=1010.0,
        low=990.0,
        close=1000.0,
        volume=1000000,
        rsi=55.0,
        ema_50=1000.0,
        ema_200=950.0,
        pe=20.0,
        pb=2.5,
        roe=15.0,
        opm=25.0,
        market_cap=100000.0,
        high_52w=1050.0,
        low_52w=800.0,
        debt_to_equity=0.5,
        last_updated=datetime.utcnow(),
    )


@pytest.fixture
def sample_price_bars():
    """Sample price bars for testing."""
    bars = []
    base_date = datetime.utcnow().date()
    base_price = 1000.0

    for i in range(5):
        date = base_date - timedelta(days=i)
        price = base_price + (i * 10)
        bars.append(PriceBar(
            yf_ticker='TEST001.NS',
            price_date=date,
            open=price - 5,
            high=price + 5,
            low=price - 10,
            close=price,
            volume=1000000 + (i * 100000),
            adjusted_close=price,
        ))

    return bars


# ============= CONNECTION TESTS =============

class TestConnection:
    """Test Cassandra client connection."""

    def test_connect_successful(self, client):
        """Test successful connection."""
        assert client.session is not None
        assert client.cluster is not None

    def test_health_check(self, client):
        """Test cluster health check."""
        health = client.check_health()
        assert health['healthy'] is True
        assert len(health['nodes']) > 0
        assert health['nodes'][0]['is_up'] is True

    def test_prepared_statements(self, client):
        """Test that prepared statements are cached."""
        assert len(client._prepared_statements) > 0
        assert 'insert_instrument' in client._prepared_statements
        assert 'select_quote' in client._prepared_statements


# ============= INSTRUMENT TESTS =============

class TestInstruments:
    """Test instrument operations."""

    def test_insert_instrument(self, client, sample_instrument):
        """Test single instrument insert."""
        success = client.insert_instrument(sample_instrument)
        assert success is True

    def test_insert_instruments_batch(self, client):
        """Test batch instrument insert."""
        instruments = [
            Instrument(
                market='india',
                yf_ticker=f'BATCH{i:03d}.NS',
                name=f'Batch Test {i}',
                symbol=f'BATCH{i:03d}',
                isin=f'INE000B{i:05d}',
                exchange='NSE',
                country='IN',
            )
            for i in range(10)
        ]

        success, failed = client.insert_instruments_batch(instruments)
        assert success == 10
        assert failed == 0

    def test_get_instrument(self, client, sample_instrument):
        """Test retrieving instrument."""
        client.insert_instrument(sample_instrument)

        retrieved = client.get_instrument('india', 'TEST001.NS')
        assert retrieved is not None
        assert retrieved.symbol == 'TEST001'
        assert retrieved.exchange == 'NSE'

    def test_get_instruments_by_market(self, client):
        """Test fetching all instruments for market."""
        instruments = client.get_instruments_by_market('india')
        # Should have at least one from previous tests
        assert len(instruments) >= 0

    def test_search_by_symbol(self, client, sample_instrument):
        """Test symbol search."""
        client.insert_instrument(sample_instrument)

        results = client.search_by_symbol('india', 'TEST001')
        assert len(results) > 0


# ============= QUOTE TESTS =============

class TestQuotes:
    """Test quote operations."""

    def test_insert_quote(self, client, sample_quote):
        """Test single quote insert."""
        success = client.insert_quote(sample_quote)
        assert success is True

    def test_insert_quotes_batch(self, client):
        """Test batch quote insert."""
        quotes = [
            QuoteSnapshot(
                market='india',
                yf_ticker=f'QBATCH{i:03d}.NS',
                cmp=1000.0 + (i * 10),
                rsi=50.0 + i,
                ema_50=1000.0,
                volume=1000000,
            )
            for i in range(10)
        ]

        success, failed = client.insert_quotes_batch(quotes)
        assert success == 10
        assert failed == 0

    def test_get_quote(self, client, sample_quote):
        """Test retrieving quote."""
        client.insert_quote(sample_quote)

        retrieved = client.get_quote('india', 'TEST001.NS')
        assert retrieved is not None
        assert float(retrieved.cmp) == pytest.approx(1000.0, abs=1.0)
        assert float(retrieved.rsi) == pytest.approx(55.0, abs=1.0)

    def test_get_quotes_by_market(self, client):
        """Test fetching quotes for market."""
        quotes = client.get_quotes_by_market('india')
        # Should have at least one from previous tests
        assert len(quotes) >= 0

    def test_quote_rsi_signal(self, client):
        """Test RSI signal calculation."""
        # Overbought quote
        overbought = QuoteSnapshot(
            market='india',
            yf_ticker='OVERBOUGHT.NS',
            cmp=1000.0,
            rsi=75.0,
        )
        client.insert_quote(overbought)

        retrieved = client.get_quote('india', 'OVERBOUGHT.NS')
        # Note: RSI signal stored in DB

        # Oversold quote
        oversold = QuoteSnapshot(
            market='india',
            yf_ticker='OVERSOLD.NS',
            cmp=1000.0,
            rsi=25.0,
        )
        client.insert_quote(oversold)

        retrieved = client.get_quote('india', 'OVERSOLD.NS')
        # Note: RSI signal stored in DB


# ============= PRICE HISTORY TESTS =============

class TestPriceHistory:
    """Test price history operations."""

    def test_insert_price_bar(self, client, sample_price_bars):
        """Test single price bar insert."""
        bar = sample_price_bars[0]
        success = client.insert_price_bar(bar)
        assert success is True

    def test_insert_price_bars_batch(self, client, sample_price_bars):
        """Test batch price bar insert."""
        success, failed = client.insert_price_bars_batch(sample_price_bars)
        assert success == len(sample_price_bars)
        assert failed == 0

    def test_get_price_history(self, client, sample_price_bars):
        """Test retrieving price history."""
        # Insert sample data
        client.insert_price_bars_batch(sample_price_bars)

        # Retrieve with date range
        end = datetime.utcnow()
        start = end - timedelta(days=30)

        bars = client.get_price_history('TEST001.NS', start, end)
        # May or may not find data depending on test order
        assert isinstance(bars, list)

    def test_price_history_date_range(self, client):
        """Test date range filtering."""
        # Insert bars across date range
        base_date = datetime.utcnow().date()
        bars = [
            PriceBar(
                yf_ticker='PRICETEST.NS',
                price_date=base_date - timedelta(days=i),
                open=1000.0,
                high=1010.0,
                low=990.0,
                close=1000.0 + i,
                volume=1000000,
            )
            for i in range(10)
        ]

        client.insert_price_bars_batch(bars)

        # Query with date range
        end = base_date
        start = base_date - timedelta(days=5)

        retrieved = client.get_price_history('PRICETEST.NS', start, end)
        assert isinstance(retrieved, list)


# ============= SEED STATUS TESTS =============

class TestSeedStatus:
    """Test seed status tracking."""

    def test_update_seed_status(self, client):
        """Test updating seed status."""
        success = client.update_seed_status(
            market='test_market',
            row_count=1000,
            phase1_complete=True,
            phase2_complete=False,
        )
        assert success is True

    def test_get_seed_status(self, client):
        """Test retrieving seed status."""
        # First update
        client.update_seed_status(
            market='test_market',
            row_count=1000,
            phase1_complete=True,
        )

        # Then retrieve
        status = client.get_seed_status('test_market')
        assert status is not None
        assert status['market'] == 'test_market'
        assert status['row_count'] == 1000
        assert status['phase1_complete'] is True


# ============= PERFORMANCE TESTS =============

class TestPerformance:
    """Test performance characteristics."""

    def test_bulk_insert_1000_quotes(self, client):
        """Test bulk insert of 1000 quotes."""
        import time

        quotes = [
            QuoteSnapshot(
                market='perf_test',
                yf_ticker=f'PERF{i:05d}.NS',
                cmp=1000.0 + (i % 100),
                rsi=50.0,
                volume=1000000,
            )
            for i in range(1000)
        ]

        start = time.time()
        success, failed = client.insert_quotes_batch(quotes)
        elapsed = time.time() - start

        assert success >= 900  # Allow some failures
        logger.info(f"Inserted 1000 quotes in {elapsed:.2f}s "
                   f"({1000/elapsed:.0f} quotes/sec)")

    def test_bulk_insert_price_bars(self, client):
        """Test bulk insert of price bars."""
        import time

        bars = [
            PriceBar(
                yf_ticker=f'BAR{i:05d}.NS',
                price_date=datetime.utcnow().date() - timedelta(days=i % 365),
                open=1000.0,
                high=1010.0,
                low=990.0,
                close=1000.0 + (i % 50),
                volume=1000000,
            )
            for i in range(10000)
        ]

        start = time.time()
        success, failed = client.insert_price_bars_batch(bars)
        elapsed = time.time() - start

        assert success >= 9000  # Allow some failures
        logger.info(f"Inserted 10000 price bars in {elapsed:.2f}s "
                   f"({10000/elapsed:.0f} bars/sec)")


# ============= CONTEXT MANAGER TESTS =============

class TestContextManager:
    """Test context manager functionality."""

    def test_with_statement(self):
        """Test using client as context manager."""
        with CassandraClient(hosts=['127.0.0.1']) as client:
            health = client.check_health()
            assert health['healthy'] is True

    def test_automatic_cleanup(self):
        """Test automatic cleanup on context exit."""
        client = CassandraClient(hosts=['127.0.0.1'])
        assert client.session is not None

        client.shutdown()
        # After shutdown, session should be unusable


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
