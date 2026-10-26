"""
Cassandra client wrapper for event-driven stock analysis platform.
Provides connection pooling, CRUD operations, retry logic, and health checks.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import threading

from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import (
    RoundRobinPolicy,
    ExponentialBackoffRetryPolicy,
    ConstantSpeculativeExecutionPolicy,
)
from cassandra.auth import PlainTextAuthProvider
from cassandra.concurrent import execute_concurrent_with_args
from cassandra.util import Date
import cassandra.cluster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class QuoteSnapshot:
    """Quote data structure for stock prices and metrics."""
    market: str
    yf_ticker: str
    cmp: Optional[float]
    rsi: Optional[float]
    ema_50: Optional[float]
    ema_200: Optional[float]
    pe: Optional[float]
    pb: Optional[float]
    roe: Optional[float]
    opm: Optional[float]
    market_cap: Optional[float]
    volume: Optional[int]
    high_52w: Optional[float]
    low_52w: Optional[float]
    debt_to_equity: Optional[float]
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    last_updated: Optional[datetime] = None
    data_source: str = 'yfinance'


@dataclass
class Instrument:
    """Instrument metadata."""
    market: str
    yf_ticker: str
    name: str
    symbol: str
    isin: Optional[str]
    exchange: str
    country: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap_inr: Optional[float] = None


@dataclass
class PriceBar:
    """OHLCV price bar."""
    yf_ticker: str
    price_date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None


class CassandraClient:
    """
    Production-grade Cassandra client for event-driven stock analysis.

    Features:
    - Connection pooling with automatic reconnection
    - Retry logic with exponential backoff
    - Health checks and node monitoring
    - Batch insert/update operations
    - Type-safe prepared statements
    - Concurrent query execution
    """

    def __init__(
        self,
        hosts: List[str],
        port: int = 9042,
        keyspace: str = 'herrrickshaw',
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_pool_size: int = 20,
        min_pool_size: int = 5,
        session_timeout: int = 30,
    ):
        """
        Initialize Cassandra client.

        Args:
            hosts: List of Cassandra node IPs/hostnames
            port: Cassandra port (default 9042)
            keyspace: Keyspace to use (default 'herrrickshaw')
            username: Auth username (if required)
            password: Auth password (if required)
            max_pool_size: Max connections per host
            min_pool_size: Min connections per host
            session_timeout: Session timeout in seconds
        """
        self.hosts = hosts
        self.port = port
        self.keyspace = keyspace
        self.session = None
        self.cluster = None
        self._prepared_statements = {}
        self._lock = threading.RLock()

        # Retry policy: exponential backoff, max 5 retries
        retry_policy = ExponentialBackoffRetryPolicy(
            base_delay=0.1,
            max_delay=10.0,
            max_retries=5
        )

        # Execution profile with speculative execution
        profile = ExecutionProfile(
            load_balancing_policy=RoundRobinPolicy(),
            retry_policy=retry_policy,
            speculative_execution_policy=ConstantSpeculativeExecutionPolicy(
                delay=0.5,
                max_attempts=2
            ),
            request_timeout=session_timeout,
        )

        # Auth provider if credentials provided
        auth_provider = None
        if username and password:
            auth_provider = PlainTextAuthProvider(username, password)

        try:
            # Create cluster with connection pooling
            self.cluster = Cluster(
                contact_points=hosts,
                port=port,
                auth_provider=auth_provider,
                max_schema_agreement_wait_seconds=10,
                control_connection_timeout=10,
                metadata_refresh_enabled=True,
                metrics_enabled=True,
            )

            # Set execution profile
            self.cluster.execution_profiles[EXEC_PROFILE_DEFAULT] = profile

            # Connect to cluster and set keyspace
            self.session = self.cluster.connect(keyspace)
            self.session.default_timeout = session_timeout
            self.session.row_factory = cassandra.cluster.dict_factory

            logger.info(
                f"Connected to Cassandra cluster: {hosts} "
                f"(keyspace={keyspace})"
            )

            # Prepare common statements
            self._prepare_statements()

            # Verify cluster health
            self.check_health()

        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {e}")
            raise

    def _prepare_statements(self) -> None:
        """Prepare commonly used CQL statements for performance."""
        statements = {
            'insert_instrument': """
                INSERT INTO instruments
                (market, yf_ticker, name, symbol, isin, exchange, country,
                 sector, industry, market_cap_inr, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            'insert_quote': """
                INSERT INTO stock_quotes
                (market, yf_ticker, cmp, open, high, low, close, volume,
                 rsi, rsi_signal, ema_50, ema_200, high_52w, low_52w,
                 pe, pb, roe, opm, market_cap, debt_to_equity, last_updated, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            'insert_price_bar': """
                INSERT INTO price_history
                (yf_ticker, price_date, open, high, low, close, volume, adjusted_close)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            'select_instrument': """
                SELECT * FROM instruments WHERE market = ? AND yf_ticker = ?
            """,
            'select_quote': """
                SELECT * FROM stock_quotes WHERE market = ? AND yf_ticker = ?
            """,
            'select_price_history': """
                SELECT * FROM price_history WHERE yf_ticker = ? AND price_date >= ? AND price_date <= ?
            """,
            'select_instruments_by_market': """
                SELECT * FROM instruments WHERE market = ?
            """,
            'select_quotes_by_market': """
                SELECT * FROM stock_quotes WHERE market = ?
            """,
            'select_seed_status': """
                SELECT * FROM seed_status WHERE market = ?
            """,
            'insert_seed_status': """
                INSERT INTO seed_status
                (market, seeded_at, row_count, phase1_complete, phase2_complete, last_error)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
            'search_by_symbol': """
                SELECT * FROM instruments_by_symbol WHERE market = ? AND symbol = ?
            """,
            'search_by_name': """
                SELECT * FROM instruments_by_name WHERE market = ? AND name_lower = ?
            """,
        }

        with self._lock:
            for key, cql in statements.items():
                try:
                    self._prepared_statements[key] = self.session.prepare(cql)
                    logger.debug(f"Prepared statement: {key}")
                except Exception as e:
                    logger.warning(f"Failed to prepare {key}: {e}")

    def check_health(self) -> Dict[str, Any]:
        """
        Check cluster health and node connectivity.

        Returns:
            Dictionary with cluster status
        """
        if not self.session or self.cluster.is_shutdown:
            return {'healthy': False, 'error': 'Session not connected'}

        try:
            health = {
                'healthy': True,
                'nodes': [],
                'data_centers': [],
            }

            # Check connected nodes
            for node in self.cluster.metadata.all_hosts():
                node_info = {
                    'ip': node.address,
                    'rack': node.rack,
                    'datacenter': node.datacenter,
                    'is_up': node.is_up,
                }
                health['nodes'].append(node_info)

            # Check data center info
            for dc, host_list in self.cluster.metadata.get_replicas(
                self.keyspace, bytes()
            ):
                health['data_centers'].append(dc)

            logger.info(f"Cluster health check passed: {len(health['nodes'])} nodes")
            return health

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'healthy': False, 'error': str(e)}

    def reconnect(self, retries: int = 3) -> bool:
        """
        Attempt to reconnect to the cluster.

        Args:
            retries: Number of retry attempts

        Returns:
            True if reconnection successful
        """
        for attempt in range(retries):
            try:
                logger.warning(f"Reconnection attempt {attempt + 1}/{retries}")

                if self.session:
                    self.session.shutdown()
                if self.cluster:
                    self.cluster.shutdown()

                self.__init__(
                    hosts=self.hosts,
                    port=self.port,
                    keyspace=self.keyspace,
                )
                logger.info("Reconnection successful")
                return True

            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

        return False

    # ============= INSERT/UPDATE OPERATIONS =============

    def insert_instrument(self, instrument: Instrument) -> bool:
        """Insert or update instrument metadata."""
        try:
            stmt = self._prepared_statements['insert_instrument']
            now = datetime.utcnow()

            self.session.execute(stmt, [
                instrument.market,
                instrument.yf_ticker,
                instrument.name,
                instrument.symbol,
                instrument.isin,
                instrument.exchange,
                instrument.country,
                instrument.sector,
                instrument.industry,
                Decimal(str(instrument.market_cap_inr)) if instrument.market_cap_inr else None,
                now,
                now,
            ])
            return True

        except Exception as e:
            logger.error(f"Failed to insert instrument {instrument.yf_ticker}: {e}")
            return False

    def insert_instruments_batch(self, instruments: List[Instrument]) -> Tuple[int, int]:
        """
        Batch insert instruments.

        Args:
            instruments: List of Instrument objects

        Returns:
            Tuple of (successful, failed) counts
        """
        if not instruments:
            return 0, 0

        stmt = self._prepared_statements['insert_instrument']
        now = datetime.utcnow()

        # Build argument list
        args = []
        for instr in instruments:
            args.append([
                instr.market,
                instr.yf_ticker,
                instr.name,
                instr.symbol,
                instr.isin,
                instr.exchange,
                instr.country,
                instr.sector,
                instr.industry,
                Decimal(str(instr.market_cap_inr)) if instr.market_cap_inr else None,
                now,
                now,
            ])

        try:
            results = execute_concurrent_with_args(
                self.session,
                stmt,
                args,
                concurrency=32,
                raise_on_first_error=False,
            )

            successful = sum(1 for success, _ in results if success)
            failed = len(results) - successful

            if failed > 0:
                logger.warning(f"Batch insert: {successful} OK, {failed} failed")
            else:
                logger.info(f"Batch insert: {successful} instruments")

            return successful, failed

        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            return 0, len(instruments)

    def insert_quote(self, quote: QuoteSnapshot) -> bool:
        """Insert or update stock quote."""
        try:
            stmt = self._prepared_statements['insert_quote']
            last_updated = quote.last_updated or datetime.utcnow()

            # Determine RSI signal
            rsi_signal = 'neutral'
            if quote.rsi:
                if quote.rsi > 70:
                    rsi_signal = 'overbought'
                elif quote.rsi < 30:
                    rsi_signal = 'oversold'

            self.session.execute(stmt, [
                quote.market,
                quote.yf_ticker,
                Decimal(str(quote.cmp)) if quote.cmp else None,
                Decimal(str(quote.open)) if quote.open else None,
                Decimal(str(quote.high)) if quote.high else None,
                Decimal(str(quote.low)) if quote.low else None,
                Decimal(str(quote.close)) if quote.close else None,
                quote.volume,
                Decimal(str(quote.rsi)) if quote.rsi else None,
                rsi_signal,
                Decimal(str(quote.ema_50)) if quote.ema_50 else None,
                Decimal(str(quote.ema_200)) if quote.ema_200 else None,
                Decimal(str(quote.high_52w)) if quote.high_52w else None,
                Decimal(str(quote.low_52w)) if quote.low_52w else None,
                Decimal(str(quote.pe)) if quote.pe else None,
                Decimal(str(quote.pb)) if quote.pb else None,
                Decimal(str(quote.roe)) if quote.roe else None,
                Decimal(str(quote.opm)) if quote.opm else None,
                Decimal(str(quote.market_cap)) if quote.market_cap else None,
                Decimal(str(quote.debt_to_equity)) if quote.debt_to_equity else None,
                last_updated,
                quote.data_source,
            ])
            return True

        except Exception as e:
            logger.error(f"Failed to insert quote {quote.yf_ticker}: {e}")
            return False

    def insert_quotes_batch(self, quotes: List[QuoteSnapshot]) -> Tuple[int, int]:
        """Batch insert stock quotes."""
        if not quotes:
            return 0, 0

        stmt = self._prepared_statements['insert_quote']
        args = []

        for quote in quotes:
            last_updated = quote.last_updated or datetime.utcnow()
            rsi_signal = 'neutral'
            if quote.rsi:
                if quote.rsi > 70:
                    rsi_signal = 'overbought'
                elif quote.rsi < 30:
                    rsi_signal = 'oversold'

            args.append([
                quote.market,
                quote.yf_ticker,
                Decimal(str(quote.cmp)) if quote.cmp else None,
                Decimal(str(quote.open)) if quote.open else None,
                Decimal(str(quote.high)) if quote.high else None,
                Decimal(str(quote.low)) if quote.low else None,
                Decimal(str(quote.close)) if quote.close else None,
                quote.volume,
                Decimal(str(quote.rsi)) if quote.rsi else None,
                rsi_signal,
                Decimal(str(quote.ema_50)) if quote.ema_50 else None,
                Decimal(str(quote.ema_200)) if quote.ema_200 else None,
                Decimal(str(quote.high_52w)) if quote.high_52w else None,
                Decimal(str(quote.low_52w)) if quote.low_52w else None,
                Decimal(str(quote.pe)) if quote.pe else None,
                Decimal(str(quote.pb)) if quote.pb else None,
                Decimal(str(quote.roe)) if quote.roe else None,
                Decimal(str(quote.opm)) if quote.opm else None,
                Decimal(str(quote.market_cap)) if quote.market_cap else None,
                Decimal(str(quote.debt_to_equity)) if quote.debt_to_equity else None,
                last_updated,
                quote.data_source,
            ])

        try:
            results = execute_concurrent_with_args(
                self.session,
                stmt,
                args,
                concurrency=32,
                raise_on_first_error=False,
            )

            successful = sum(1 for success, _ in results if success)
            failed = len(results) - successful

            if failed > 0:
                logger.warning(f"Batch quotes insert: {successful} OK, {failed} failed")
            else:
                logger.info(f"Batch quotes insert: {successful} quotes")

            return successful, failed

        except Exception as e:
            logger.error(f"Batch quotes insert failed: {e}")
            return 0, len(quotes)

    def insert_price_bar(self, bar: PriceBar) -> bool:
        """Insert OHLCV price bar."""
        try:
            stmt = self._prepared_statements['insert_price_bar']
            price_date = Date.from_datetime(bar.price_date)

            self.session.execute(stmt, [
                bar.yf_ticker,
                price_date,
                Decimal(str(bar.open)),
                Decimal(str(bar.high)),
                Decimal(str(bar.low)),
                Decimal(str(bar.close)),
                bar.volume,
                Decimal(str(bar.adjusted_close)) if bar.adjusted_close else None,
            ])
            return True

        except Exception as e:
            logger.error(f"Failed to insert price bar {bar.yf_ticker}: {e}")
            return False

    def insert_price_bars_batch(self, bars: List[PriceBar]) -> Tuple[int, int]:
        """Batch insert price history."""
        if not bars:
            return 0, 0

        stmt = self._prepared_statements['insert_price_bar']
        args = []

        for bar in bars:
            price_date = Date.from_datetime(bar.price_date)
            args.append([
                bar.yf_ticker,
                price_date,
                Decimal(str(bar.open)),
                Decimal(str(bar.high)),
                Decimal(str(bar.low)),
                Decimal(str(bar.close)),
                bar.volume,
                Decimal(str(bar.adjusted_close)) if bar.adjusted_close else None,
            ])

        try:
            results = execute_concurrent_with_args(
                self.session,
                stmt,
                args,
                concurrency=32,
                raise_on_first_error=False,
            )

            successful = sum(1 for success, _ in results if success)
            failed = len(results) - successful

            logger.info(f"Price bars batch insert: {successful} inserted, {failed} failed")
            return successful, failed

        except Exception as e:
            logger.error(f"Price bars batch insert failed: {e}")
            return 0, len(bars)

    # ============= READ OPERATIONS =============

    def get_instrument(self, market: str, yf_ticker: str) -> Optional[Instrument]:
        """Fetch instrument by market and yfinance ticker."""
        try:
            stmt = self._prepared_statements['select_instrument']
            rows = self.session.execute(stmt, [market, yf_ticker])

            if not rows:
                return None

            row = rows[0]
            return Instrument(
                market=row['market'],
                yf_ticker=row['yf_ticker'],
                name=row['name'],
                symbol=row['symbol'],
                isin=row.get('isin'),
                exchange=row['exchange'],
                country=row['country'],
                sector=row.get('sector'),
                industry=row.get('industry'),
                market_cap_inr=float(row['market_cap_inr']) if row.get('market_cap_inr') else None,
            )

        except Exception as e:
            logger.error(f"Failed to fetch instrument {yf_ticker}: {e}")
            return None

    def get_quote(self, market: str, yf_ticker: str) -> Optional[QuoteSnapshot]:
        """Fetch latest stock quote."""
        try:
            stmt = self._prepared_statements['select_quote']
            rows = self.session.execute(stmt, [market, yf_ticker])

            if not rows:
                return None

            row = rows[0]
            return QuoteSnapshot(
                market=row['market'],
                yf_ticker=row['yf_ticker'],
                cmp=float(row['cmp']) if row.get('cmp') else None,
                rsi=float(row['rsi']) if row.get('rsi') else None,
                ema_50=float(row['ema_50']) if row.get('ema_50') else None,
                ema_200=float(row['ema_200']) if row.get('ema_200') else None,
                pe=float(row['pe']) if row.get('pe') else None,
                pb=float(row['pb']) if row.get('pb') else None,
                roe=float(row['roe']) if row.get('roe') else None,
                opm=float(row['opm']) if row.get('opm') else None,
                market_cap=float(row['market_cap']) if row.get('market_cap') else None,
                volume=row.get('volume'),
                high_52w=float(row['high_52w']) if row.get('high_52w') else None,
                low_52w=float(row['low_52w']) if row.get('low_52w') else None,
                debt_to_equity=float(row['debt_to_equity']) if row.get('debt_to_equity') else None,
                open=float(row['open']) if row.get('open') else None,
                high=float(row['high']) if row.get('high') else None,
                low=float(row['low']) if row.get('low') else None,
                close=float(row['close']) if row.get('close') else None,
                last_updated=row.get('last_updated'),
                data_source=row.get('data_source', 'yfinance'),
            )

        except Exception as e:
            logger.error(f"Failed to fetch quote {yf_ticker}: {e}")
            return None

    def get_price_history(
        self,
        yf_ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[PriceBar]:
        """Fetch price history for date range."""
        try:
            stmt = self._prepared_statements['select_price_history']
            start = Date.from_datetime(start_date)
            end = Date.from_datetime(end_date)

            rows = self.session.execute(stmt, [yf_ticker, start, end])

            bars = []
            for row in rows:
                bars.append(PriceBar(
                    yf_ticker=row['yf_ticker'],
                    price_date=row['price_date'],
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=row['volume'],
                    adjusted_close=float(row['adjusted_close']) if row.get('adjusted_close') else None,
                ))

            logger.info(f"Fetched {len(bars)} price bars for {yf_ticker}")
            return bars

        except Exception as e:
            logger.error(f"Failed to fetch price history {yf_ticker}: {e}")
            return []

    def get_instruments_by_market(self, market: str) -> List[Instrument]:
        """Fetch all instruments for a market."""
        try:
            stmt = self._prepared_statements['select_instruments_by_market']
            rows = self.session.execute(stmt, [market])

            instruments = []
            for row in rows:
                instruments.append(Instrument(
                    market=row['market'],
                    yf_ticker=row['yf_ticker'],
                    name=row['name'],
                    symbol=row['symbol'],
                    isin=row.get('isin'),
                    exchange=row['exchange'],
                    country=row['country'],
                    sector=row.get('sector'),
                    industry=row.get('industry'),
                ))

            logger.info(f"Fetched {len(instruments)} instruments for market={market}")
            return instruments

        except Exception as e:
            logger.error(f"Failed to fetch instruments for market {market}: {e}")
            return []

    def get_quotes_by_market(self, market: str) -> List[QuoteSnapshot]:
        """Fetch all quotes for a market."""
        try:
            stmt = self._prepared_statements['select_quotes_by_market']
            rows = self.session.execute(stmt, [market])

            quotes = []
            for row in rows:
                quotes.append(QuoteSnapshot(
                    market=row['market'],
                    yf_ticker=row['yf_ticker'],
                    cmp=float(row['cmp']) if row.get('cmp') else None,
                    rsi=float(row['rsi']) if row.get('rsi') else None,
                    ema_50=float(row['ema_50']) if row.get('ema_50') else None,
                    ema_200=float(row['ema_200']) if row.get('ema_200') else None,
                    pe=float(row['pe']) if row.get('pe') else None,
                    pb=float(row['pb']) if row.get('pb') else None,
                    roe=float(row['roe']) if row.get('roe') else None,
                    opm=float(row['opm']) if row.get('opm') else None,
                    market_cap=float(row['market_cap']) if row.get('market_cap') else None,
                    volume=row.get('volume'),
                    high_52w=float(row['high_52w']) if row.get('high_52w') else None,
                    low_52w=float(row['low_52w']) if row.get('low_52w') else None,
                    debt_to_equity=float(row['debt_to_equity']) if row.get('debt_to_equity') else None,
                    open=float(row['open']) if row.get('open') else None,
                    high=float(row['high']) if row.get('high') else None,
                    low=float(row['low']) if row.get('low') else None,
                    close=float(row['close']) if row.get('close') else None,
                    last_updated=row.get('last_updated'),
                ))

            logger.info(f"Fetched {len(quotes)} quotes for market={market}")
            return quotes

        except Exception as e:
            logger.error(f"Failed to fetch quotes for market {market}: {e}")
            return []

    # ============= SEED STATUS OPERATIONS =============

    def get_seed_status(self, market: str) -> Optional[Dict[str, Any]]:
        """Fetch seed status for market."""
        try:
            stmt = self._prepared_statements['select_seed_status']
            rows = self.session.execute(stmt, [market])

            if not rows:
                return None

            row = rows[0]
            return {
                'market': row['market'],
                'seeded_at': row.get('seeded_at'),
                'row_count': row.get('row_count'),
                'phase1_complete': row.get('phase1_complete', False),
                'phase2_complete': row.get('phase2_complete', False),
                'last_error': row.get('last_error'),
            }

        except Exception as e:
            logger.error(f"Failed to fetch seed status for {market}: {e}")
            return None

    def update_seed_status(
        self,
        market: str,
        row_count: int,
        phase1_complete: bool = False,
        phase2_complete: bool = False,
        last_error: Optional[str] = None,
    ) -> bool:
        """Update seed status for market."""
        try:
            stmt = self._prepared_statements['insert_seed_status']
            now = datetime.utcnow()

            self.session.execute(stmt, [
                market,
                now,
                row_count,
                phase1_complete,
                phase2_complete,
                last_error,
            ])
            logger.info(f"Updated seed status for {market}: {row_count} rows")
            return True

        except Exception as e:
            logger.error(f"Failed to update seed status for {market}: {e}")
            return False

    # ============= SEARCH OPERATIONS =============

    def search_by_symbol(self, market: str, symbol: str) -> List[Instrument]:
        """Search instruments by symbol."""
        try:
            stmt = self._prepared_statements['search_by_symbol']
            rows = self.session.execute(stmt, [market, symbol])

            instruments = []
            for row in rows:
                instruments.append(Instrument(
                    market=row['market'],
                    yf_ticker=row['yf_ticker'],
                    name=row.get('name') or row.get('name_lower', ''),
                    symbol=row['symbol'],
                    isin=row.get('isin'),
                    exchange=row['exchange'],
                    country=row.get('country', ''),
                ))

            logger.info(f"Found {len(instruments)} instruments for symbol={symbol}")
            return instruments

        except Exception as e:
            logger.error(f"Failed to search by symbol {symbol}: {e}")
            return []

    def search_by_name_prefix(self, market: str, name_prefix: str) -> List[Instrument]:
        """Search instruments by name prefix (case-insensitive)."""
        try:
            stmt = self._prepared_statements['search_by_name']
            name_lower = name_prefix.lower()
            rows = self.session.execute(stmt, [market, name_lower])

            instruments = []
            for row in rows:
                instruments.append(Instrument(
                    market=row['market'],
                    yf_ticker=row['yf_ticker'],
                    name=row.get('name') or row.get('name_lower', ''),
                    symbol=row['symbol'],
                    isin=row.get('isin'),
                    exchange=row['exchange'],
                    country=row.get('country', ''),
                ))

            logger.info(f"Found {len(instruments)} instruments for name prefix={name_prefix}")
            return instruments

        except Exception as e:
            logger.error(f"Failed to search by name {name_prefix}: {e}")
            return []

    # ============= LIFECYCLE =============

    def shutdown(self) -> None:
        """Gracefully shutdown client and close connections."""
        try:
            if self.session:
                self.session.shutdown()
                logger.info("Session closed")

            if self.cluster:
                self.cluster.shutdown()
                logger.info("Cluster shutdown")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown()
        except:
            pass
