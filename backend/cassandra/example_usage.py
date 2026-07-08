"""
Example usage of the Cassandra client for event-driven stock analysis.

Demonstrates:
- Connection pooling and health checks
- Batch insert operations
- Single and bulk queries
- Market-specific operations
- Seed status tracking
"""

import logging
from datetime import datetime, timedelta
from cassandra_client import (
    CassandraClient,
    Instrument,
    QuoteSnapshot,
    PriceBar,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_connect_and_health_check():
    """Example: Connect to Cassandra and verify cluster health."""
    print("\n=== Example 1: Connect and Health Check ===")

    # Connect to local Cassandra cluster (development)
    client = CassandraClient(
        hosts=['127.0.0.1'],  # Replace with your cluster nodes
        port=9042,
        keyspace='herrrickshaw',
    )

    # Check cluster health
    health = client.check_health()
    print(f"Cluster health: {health['healthy']}")
    print(f"Connected nodes: {len(health['nodes'])}")
    for node in health['nodes']:
        print(f"  - {node['ip']} (DC: {node['datacenter']}, Up: {node['is_up']})")

    return client


def example_seed_instruments(client: CassandraClient):
    """Example: Seed instruments into Cassandra."""
    print("\n=== Example 2: Seed Instruments ===")

    # Create sample instruments for India market
    instruments = [
        Instrument(
            market='india',
            yf_ticker='RELIANCE.NS',
            name='Reliance Industries',
            symbol='RELIANCE',
            isin='INE002A01018',
            exchange='NSE',
            country='IN',
            sector='Energy',
            industry='Oil & Gas',
            market_cap_inr=1750000.0,  # ~₹1.75 trillion
        ),
        Instrument(
            market='india',
            yf_ticker='HDFCBANK.NS',
            name='HDFC Bank',
            symbol='HDFCBANK',
            isin='INE001A01015',
            exchange='NSE',
            country='IN',
            sector='Financials',
            industry='Banking',
            market_cap_inr=800000.0,
        ),
        Instrument(
            market='india',
            yf_ticker='TCS.NS',
            name='Tata Consultancy Services',
            symbol='TCS',
            isin='INE467B01029',
            exchange='NSE',
            country='IN',
            sector='IT',
            industry='Software',
            market_cap_inr=620000.0,
        ),
    ]

    # Batch insert
    success, failed = client.insert_instruments_batch(instruments)
    print(f"Inserted {success} instruments, {failed} failed")

    # Update seed status
    client.update_seed_status(
        market='india',
        row_count=success,
        phase1_complete=True,
        phase2_complete=False,
    )
    print(f"Seed status updated for india market")


def example_insert_quotes(client: CassandraClient):
    """Example: Insert stock quotes."""
    print("\n=== Example 3: Insert Stock Quotes ===")

    # Create sample quotes
    quotes = [
        QuoteSnapshot(
            market='india',
            yf_ticker='RELIANCE.NS',
            cmp=2850.50,
            open=2840.00,
            high=2875.00,
            low=2835.00,
            close=2850.50,
            volume=2500000,
            rsi=58.5,
            ema_50=2820.75,
            ema_200=2750.00,
            high_52w=3050.00,
            low_52w=2100.00,
            pe=26.5,
            pb=3.8,
            roe=12.5,
            opm=18.5,
            market_cap=1750000.0,
            debt_to_equity=0.45,
            last_updated=datetime.utcnow(),
        ),
        QuoteSnapshot(
            market='india',
            yf_ticker='HDFCBANK.NS',
            cmp=1650.00,
            open=1640.00,
            high=1670.00,
            low=1635.00,
            close=1650.00,
            volume=3200000,
            rsi=62.0,
            ema_50=1620.00,
            ema_200=1500.00,
            high_52w=1850.00,
            low_52w=900.00,
            pe=22.5,
            pb=2.8,
            roe=14.2,
            opm=22.5,
            market_cap=800000.0,
            debt_to_equity=0.65,
            last_updated=datetime.utcnow(),
        ),
    ]

    # Batch insert quotes
    success, failed = client.insert_quotes_batch(quotes)
    print(f"Inserted {success} quotes, {failed} failed")


def example_insert_price_history(client: CassandraClient):
    """Example: Insert price history."""
    print("\n=== Example 4: Insert Price History ===")

    # Create 10 days of price history
    bars = []
    base_date = datetime.utcnow().date()
    base_price = 2850.0

    for i in range(10):
        date = base_date - timedelta(days=i)
        price = base_price + (i % 5) * 10  # Varying prices
        bars.append(PriceBar(
            yf_ticker='RELIANCE.NS',
            price_date=date,
            open=price - 5,
            high=price + 10,
            low=price - 10,
            close=price,
            volume=2500000 + (i * 100000),
            adjusted_close=price,
        ))

    # Batch insert
    success, failed = client.insert_price_bars_batch(bars)
    print(f"Inserted {success} price bars, {failed} failed")


def example_query_instrument(client: CassandraClient):
    """Example: Query single instrument."""
    print("\n=== Example 5: Query Single Instrument ===")

    instrument = client.get_instrument('india', 'RELIANCE.NS')
    if instrument:
        print(f"Symbol: {instrument.symbol}")
        print(f"Name: {instrument.name}")
        print(f"Exchange: {instrument.exchange}")
        print(f"Sector: {instrument.sector}")
    else:
        print("Instrument not found")


def example_query_quote(client: CassandraClient):
    """Example: Query stock quote."""
    print("\n=== Example 6: Query Stock Quote ===")

    quote = client.get_quote('india', 'RELIANCE.NS')
    if quote:
        print(f"CMP: ₹{quote.cmp}")
        print(f"RSI: {quote.rsi}")
        print(f"EMA-50: ₹{quote.ema_50}")
        print(f"P/E: {quote.pe}")
        print(f"Updated: {quote.last_updated}")
    else:
        print("Quote not found")


def example_query_price_history(client: CassandraClient):
    """Example: Query price history."""
    print("\n=== Example 7: Query Price History ===")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    bars = client.get_price_history('RELIANCE.NS', start_date, end_date)
    print(f"Fetched {len(bars)} price bars")
    if bars:
        for bar in bars[:3]:
            print(f"  {bar.price_date}: O={bar.open} H={bar.high} "
                  f"L={bar.low} C={bar.close} V={bar.volume}")


def example_market_scan(client: CassandraClient):
    """Example: Fetch all quotes for market scan."""
    print("\n=== Example 8: Market Scan (Fetch All Quotes) ===")

    quotes = client.get_quotes_by_market('india')
    print(f"Fetched {len(quotes)} quotes for India market")

    # Filter oversold stocks (RSI < 30)
    oversold = [q for q in quotes if q.rsi and q.rsi < 30]
    print(f"Oversold (RSI < 30): {len(oversold)}")
    for q in oversold:
        print(f"  {q.yf_ticker}: RSI={q.rsi}, CMP=₹{q.cmp}")

    # Filter near 52-week high
    near_high = [q for q in quotes if q.high_52w and q.cmp
                 and q.cmp > q.high_52w * 0.95]
    print(f"Near 52W high (>95%): {len(near_high)}")
    for q in near_high:
        print(f"  {q.yf_ticker}: {q.cmp:.0f} / {q.high_52w:.0f}")


def example_search_operations(client: CassandraClient):
    """Example: Search by symbol and name."""
    print("\n=== Example 9: Search Operations ===")

    # Search by symbol
    results = client.search_by_symbol('india', 'RELIANCE')
    print(f"Search by symbol 'RELIANCE': {len(results)} results")

    # Search by name prefix
    results = client.search_by_name_prefix('india', 'hdfc')
    print(f"Search by name prefix 'hdfc': {len(results)} results")


def example_seed_status(client: CassandraClient):
    """Example: Check and manage seed status."""
    print("\n=== Example 10: Seed Status ===")

    status = client.get_seed_status('india')
    if status:
        print(f"Market: {status['market']}")
        print(f"Row count: {status['row_count']}")
        print(f"Phase 1 complete: {status['phase1_complete']}")
        print(f"Phase 2 complete: {status['phase2_complete']}")
        print(f"Seeded at: {status['seeded_at']}")
    else:
        print("No seed status found")


def example_context_manager():
    """Example: Using client as context manager."""
    print("\n=== Example 11: Context Manager Usage ===")

    with CassandraClient(hosts=['127.0.0.1']) as client:
        health = client.check_health()
        print(f"Cluster health: {health['healthy']}")
        # Client automatically closes on exit


if __name__ == '__main__':
    # Connect to Cassandra
    client = example_connect_and_health_check()

    try:
        # Run examples
        example_seed_instruments(client)
        example_insert_quotes(client)
        example_insert_price_history(client)

        example_query_instrument(client)
        example_query_quote(client)
        example_query_price_history(client)

        example_market_scan(client)
        example_search_operations(client)
        example_seed_status(client)
        example_context_manager()

        print("\n=== All examples completed successfully ===")

    except Exception as e:
        logger.error(f"Error during examples: {e}")

    finally:
        # Cleanup
        client.shutdown()
