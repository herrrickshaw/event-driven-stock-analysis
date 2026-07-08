-- Cassandra Schema for Event-Driven Stock Analysis
-- Keyspace: herrrickshaw (distributed across 6-node cluster)
-- Replication: RF=3 for high availability

-- Create keyspace with RF=3 and NetworkTopologyStrategy
CREATE KEYSPACE IF NOT EXISTS herrrickshaw
  WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 3}
  AND durable_writes = true;

-- Instruments table: stock metadata indexed by market and yfinance ticker
CREATE TABLE IF NOT EXISTS herrrickshaw.instruments (
  market TEXT,                    -- 'india', 'us', 'europe', 'japan', 'korea', 'china'
  yf_ticker TEXT,                 -- yfinance ticker (bare NSE, pre-suffixed others)
  name TEXT,                       -- stock name
  symbol TEXT,                     -- native symbol
  isin TEXT,                        -- ISIN identifier
  exchange TEXT,                   -- exchange name (NSE, NASDAQ, LSE, etc.)
  country TEXT,                    -- ISO 3166-1 alpha-2 country code
  sector TEXT,                     -- sector classification
  industry TEXT,                   -- industry classification
  market_cap_inr DECIMAL,          -- market cap in INR (India), or NULL
  created_at TIMESTAMP,            -- insertion timestamp
  updated_at TIMESTAMP,            -- last update timestamp

  PRIMARY KEY ((market), yf_ticker)
) WITH CLUSTERING ORDER BY (yf_ticker ASC)
   AND compaction = {'class': 'SizeTieredCompactionStrategy', 'min_threshold': 4}
   AND compression = {'class': 'LZ4Compressor'}
   AND default_time_to_live = 0;

-- Instruments search by symbol (secondary partition)
CREATE TABLE IF NOT EXISTS herrrickshaw.instruments_by_symbol (
  market TEXT,
  symbol TEXT,                     -- native ticker symbol
  yf_ticker TEXT,                  -- pointer to instruments table
  name TEXT,
  exchange TEXT,

  PRIMARY KEY ((market, symbol), yf_ticker)
) WITH CLUSTERING ORDER BY (yf_ticker ASC)
   AND compaction = {'class': 'SizeTieredCompactionStrategy'}
   AND compression = {'class': 'LZ4Compressor'};

-- Instruments search by name (prefix search via token-aware partitioning)
CREATE TABLE IF NOT EXISTS herrrickshaw.instruments_by_name (
  market TEXT,
  name_lower TEXT,                 -- lowercase name for case-insensitive search
  yf_ticker TEXT,                  -- pointer to instruments table
  symbol TEXT,
  exchange TEXT,

  PRIMARY KEY ((market, name_lower), yf_ticker)
) WITH CLUSTERING ORDER BY (yf_ticker ASC)
   AND compaction = {'class': 'SizeTieredCompactionStrategy'}
   AND compression = {'class': 'LZ4Compressor'};

-- Stock quotes: latest OHLCV + technical + fundamental metrics
CREATE TABLE IF NOT EXISTS herrrickshaw.stock_quotes (
  market TEXT,
  yf_ticker TEXT,
  cmp DECIMAL,                     -- current market price
  open DECIMAL,                    -- open price
  high DECIMAL,                    -- day high
  low DECIMAL,                     -- day low
  close DECIMAL,                   -- last close
  volume BIGINT,                   -- volume traded

  -- Technical indicators
  rsi DECIMAL,                     -- 14-period RSI
  rsi_signal TEXT,                 -- 'overbought' | 'oversold' | 'neutral'
  ema_50 DECIMAL,                  -- 50-period EMA
  ema_200 DECIMAL,                 -- 200-period EMA
  high_52w DECIMAL,                -- 52-week high
  low_52w DECIMAL,                 -- 52-week low

  -- Fundamental metrics
  pe DECIMAL,                      -- price-to-earnings ratio
  pb DECIMAL,                      -- price-to-book ratio
  roe DECIMAL,                     -- return on equity (%)
  opm DECIMAL,                     -- operating profit margin (%)
  market_cap DECIMAL,              -- market cap in billions
  debt_to_equity DECIMAL,          -- D/E ratio

  -- Metadata
  last_updated TIMESTAMP,          -- latest data timestamp (UTC)
  data_source TEXT,                -- 'yfinance' | 'screener.in' | 'nse_api'

  PRIMARY KEY ((market), yf_ticker)
) WITH CLUSTERING ORDER BY (yf_ticker ASC)
   AND default_time_to_live = 86400          -- 24h TTL for quote freshness
   AND compaction = {'class': 'TimeWindowCompactionStrategy',
                     'compaction_window_unit': 'HOURS',
                     'compaction_window_size': 24}
   AND compression = {'class': 'LZ4Compressor'};

-- Price history: time-series OHLCV for charting and backtesting
CREATE TABLE IF NOT EXISTS herrrickshaw.price_history (
  yf_ticker TEXT,
  price_date DATE,                 -- partition by date for time-series access
  open DECIMAL,
  high DECIMAL,
  low DECIMAL,
  close DECIMAL,
  volume BIGINT,
  adjusted_close DECIMAL,          -- dividend/split adjusted

  PRIMARY KEY ((yf_ticker), price_date)
) WITH CLUSTERING ORDER BY (price_date DESC)
   AND compaction = {'class': 'TimeWindowCompactionStrategy',
                     'compaction_window_unit': 'DAYS',
                     'compaction_window_size': 7}
   AND compression = {'class': 'LZ4Compressor'};

-- Seed status: track bulk fetch progress per market
CREATE TABLE IF NOT EXISTS herrrickshaw.seed_status (
  market TEXT,
  seeded_at TIMESTAMP,             -- last seed/refresh timestamp
  row_count INT,                   -- instrument count
  phase1_complete BOOLEAN,         -- OHLCV + RSI completed
  phase2_complete BOOLEAN,         -- Fundamentals (PE, ROE, etc.) completed
  last_error TEXT,                 -- last error message if any

  PRIMARY KEY (market)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_stock_quotes_rsi ON herrrickshaw.stock_quotes (rsi);
CREATE INDEX IF NOT EXISTS idx_stock_quotes_pe ON herrrickshaw.stock_quotes (pe);
CREATE INDEX IF NOT EXISTS idx_stock_quotes_market_cap ON herrrickshaw.stock_quotes (market_cap);
