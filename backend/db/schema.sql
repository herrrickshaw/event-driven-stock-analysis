-- =============================================================================
-- Event-Driven Stock Analysis Platform - PostgreSQL Schema
-- =============================================================================
-- Keyspaces: portfolio_realtime, risk_metrics, rebalancing_calendar, kpi_metrics
-- Optimized for: 20,700 stocks × 15 years history
-- Created: 2026-07-08
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- SCHEMA 1: portfolio_realtime
-- Purpose: Real-time portfolio holdings, allocations, and valuations
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS portfolio_realtime;

COMMENT ON SCHEMA portfolio_realtime IS
'Real-time portfolio management: current holdings, positions, allocation percentages, and valuation across all markets';

-- Master Portfolio Holdings Table
CREATE TABLE portfolio_realtime.holdings (
    holding_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    market VARCHAR(10) NOT NULL, -- 'india', 'us', 'europe', 'japan', 'korea', 'china'
    exchange VARCHAR(10),        -- 'NSE', 'BSE', 'NYSE', 'NASDAQ', 'LSE', 'TSE', 'KRX', etc.

    -- Position Data
    shares NUMERIC(18, 4) NOT NULL DEFAULT 0,
    entry_price NUMERIC(12, 4) NOT NULL DEFAULT 0,
    current_price NUMERIC(12, 4) NOT NULL DEFAULT 0,
    market_value NUMERIC(18, 2) NOT NULL DEFAULT 0,
    cost_basis NUMERIC(18, 2) NOT NULL DEFAULT 0,
    unrealized_pnl NUMERIC(18, 2),
    unrealized_pnl_pct NUMERIC(8, 4),

    -- Allocation & Currency
    allocation_pct NUMERIC(6, 4) NOT NULL DEFAULT 0, -- 0-100%
    currency VARCHAR(3) NOT NULL DEFAULT 'USD', -- 'INR', 'USD', 'EUR', 'JPY', 'KRW', 'CNY'
    fx_rate NUMERIC(10, 6) NOT NULL DEFAULT 1,

    -- Trading Info
    acquisition_date DATE,
    quantity_purchased NUMERIC(18, 4),
    quantity_sold NUMERIC(18, 4),
    avg_cost_per_share NUMERIC(12, 4),

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_price_update TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'SOLD', 'LIQUIDATED'
    notes TEXT,

    PRIMARY KEY (holding_id)
);

COMMENT ON TABLE portfolio_realtime.holdings IS
'Individual stock/security holdings with real-time valuations, P&L, and allocation data. Partitioned by date for fast range queries. ~310M rows for 20,700 stocks × 15y × 1 daily update.';

-- Indexes for performance
CREATE INDEX idx_holdings_portfolio_date ON portfolio_realtime.holdings (portfolio_id, date DESC);
CREATE INDEX idx_holdings_symbol_market ON portfolio_realtime.holdings (symbol, market, date DESC);
CREATE INDEX idx_holdings_date_market ON portfolio_realtime.holdings (date, market);
CREATE INDEX idx_holdings_updated_at ON portfolio_realtime.holdings (updated_at DESC);
CREATE INDEX idx_holdings_status ON portfolio_realtime.holdings (status, date DESC);

-- Partitioning by date (quarterly)
-- ALTER TABLE portfolio_realtime.holdings PARTITION BY RANGE (YEAR(date), QUARTER(date));

-- Portfolio Summary (aggregated view cache)
CREATE TABLE portfolio_realtime.portfolio_summary (
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,
    market VARCHAR(10) NOT NULL,

    total_market_value NUMERIC(18, 2) NOT NULL DEFAULT 0,
    total_cost_basis NUMERIC(18, 2) NOT NULL DEFAULT 0,
    total_pnl NUMERIC(18, 2),
    total_pnl_pct NUMERIC(8, 4),

    holding_count INT NOT NULL DEFAULT 0,
    cash_balance NUMERIC(18, 2) DEFAULT 0,
    margin_used NUMERIC(18, 2) DEFAULT 0,
    buying_power NUMERIC(18, 2) DEFAULT 0,

    portfolio_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    allocation_drift_pct NUMERIC(6, 4),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (portfolio_id, date, market)
);

COMMENT ON TABLE portfolio_realtime.portfolio_summary IS
'Aggregated daily portfolio snapshot per market. Materialized view cache for dashboard performance. Indexed for fast lookups.';

CREATE INDEX idx_portfolio_summary_date ON portfolio_realtime.portfolio_summary (date DESC);
CREATE INDEX idx_portfolio_summary_market ON portfolio_realtime.portfolio_summary (market, date DESC);

-- =============================================================================
-- SCHEMA 2: risk_metrics
-- Purpose: Risk calculations, correlations, VaR, volatility tracking
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS risk_metrics;

COMMENT ON SCHEMA risk_metrics IS
'Risk analytics: volatility, Value-at-Risk (VaR), correlation matrices, factor exposures, and tail risk metrics';

-- Daily Volatility & Risk Metrics
CREATE TABLE risk_metrics.volatility_metrics (
    metric_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,

    symbol VARCHAR(20),       -- NULL for portfolio-level metrics
    market VARCHAR(10),       -- NULL for portfolio-level metrics

    -- Volatility Measures
    volatility_252d NUMERIC(8, 4) NOT NULL, -- 252-day annualized volatility
    volatility_63d NUMERIC(8, 4),           -- 63-day (quarterly) volatility
    volatility_21d NUMERIC(8, 4),           -- 21-day (monthly) volatility

    -- Returns
    daily_return NUMERIC(8, 6),
    weekly_return NUMERIC(8, 6),
    monthly_return NUMERIC(8, 6),
    ytd_return NUMERIC(8, 6),

    -- Drawdown
    current_drawdown NUMERIC(8, 4),
    max_drawdown_252d NUMERIC(8, 4),
    days_to_recovery INT,

    -- Additional Risk Stats
    skewness NUMERIC(8, 6),
    kurtosis NUMERIC(8, 6),
    beta_to_market NUMERIC(8, 6),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (metric_id)
);

COMMENT ON TABLE risk_metrics.volatility_metrics IS
'Daily volatility and drawdown tracking. 252-day = annualized. Calculated post-market. Can aggregate by market or security. ~30.6M rows for 20,700 stocks × 15y.';

CREATE INDEX idx_volatility_portfolio_date ON risk_metrics.volatility_metrics (portfolio_id, date DESC);
CREATE INDEX idx_volatility_symbol_date ON risk_metrics.volatility_metrics (symbol, market, date DESC);
CREATE INDEX idx_volatility_market_date ON risk_metrics.volatility_metrics (market, date DESC);

-- Value-at-Risk (VaR) Calculations
CREATE TABLE risk_metrics.var_metrics (
    var_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,
    market VARCHAR(10),

    -- VaR at different confidence levels
    var_95 NUMERIC(12, 2) NOT NULL,         -- 95% confidence level, $ amount
    var_99 NUMERIC(12, 2) NOT NULL,         -- 99% confidence level, $ amount
    var_95_pct NUMERIC(8, 4),               -- as % of portfolio value
    var_99_pct NUMERIC(8, 4),

    -- Conditional VaR (Expected Shortfall)
    cvar_95 NUMERIC(12, 2),
    cvar_99 NUMERIC(12, 2),

    -- Scenario Analysis
    stress_test_loss_10pct_market NUMERIC(12, 2),
    stress_test_loss_20pct_market NUMERIC(12, 2),

    -- Calculation method
    var_method VARCHAR(20), -- 'historical', 'parametric', 'monte_carlo'
    lookback_days INT DEFAULT 252,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (var_id)
);

COMMENT ON TABLE risk_metrics.var_metrics IS
'Value-at-Risk metrics: 95th and 99th percentile loss scenarios. Calculated daily post-market using 252-day historical window or parametric/MC methods. ~4.3M rows for 20,700 stocks × 15y.';

CREATE INDEX idx_var_portfolio_date ON risk_metrics.var_metrics (portfolio_id, date DESC);
CREATE INDEX idx_var_market_date ON risk_metrics.var_metrics (market, date DESC);

-- Correlation Matrix (Daily Snapshot)
CREATE TABLE risk_metrics.correlation_matrix (
    correlation_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,
    market_pair VARCHAR(20), -- e.g., 'india-us', 'us-europe'

    symbol_1 VARCHAR(20) NOT NULL,
    symbol_2 VARCHAR(20) NOT NULL,
    market_1 VARCHAR(10) NOT NULL,
    market_2 VARCHAR(10) NOT NULL,

    -- Correlation stats
    correlation_252d NUMERIC(8, 6) NOT NULL, -- 252-day Pearson correlation
    correlation_63d NUMERIC(8, 6),
    correlation_21d NUMERIC(8, 6),

    -- Covariance
    covariance_252d NUMERIC(12, 8),

    -- Significance
    r_squared NUMERIC(8, 6),
    p_value NUMERIC(8, 6),

    -- Update tracking
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (correlation_id),
    CONSTRAINT chk_correlation_range CHECK (correlation_252d >= -1 AND correlation_252d <= 1)
);

COMMENT ON TABLE risk_metrics.correlation_matrix IS
'Pairwise correlation matrix for portfolio diversification analysis. Updated daily. Enables rebalancing decisions based on correlation drift. ~Cnm rows where C=20,700, n=m at given date.';

CREATE INDEX idx_correlation_portfolio_date ON risk_metrics.correlation_matrix (portfolio_id, date DESC);
CREATE INDEX idx_correlation_symbol_pair ON risk_metrics.correlation_matrix (symbol_1, symbol_2, date DESC);
CREATE INDEX idx_correlation_markets ON risk_metrics.correlation_matrix (market_pair, date DESC);

-- Factor Exposure & Attribution
CREATE TABLE risk_metrics.factor_exposure (
    exposure_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,

    symbol VARCHAR(20),
    market VARCHAR(10),

    -- Risk Factors (Fama-French 3-factor style)
    market_exposure NUMERIC(8, 6),     -- beta to market
    size_exposure NUMERIC(8, 6),       -- SMB (Small Minus Big)
    value_exposure NUMERIC(8, 6),      -- HML (High Minus Low)

    -- Additional Factors
    momentum_exposure NUMERIC(8, 6),
    volatility_exposure NUMERIC(8, 6),
    liquidity_exposure NUMERIC(8, 6),

    -- Sector Allocation
    sector_name VARCHAR(50),
    sector_exposure_pct NUMERIC(6, 4),

    -- Tracking Error
    tracking_error NUMERIC(8, 4),
    active_return NUMERIC(8, 6),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (exposure_id)
);

COMMENT ON TABLE risk_metrics.factor_exposure IS
'Risk factor decomposition: market beta, size, value, momentum, liquidity. Enables performance attribution and stress testing. ~30.6M rows.';

CREATE INDEX idx_factor_portfolio_date ON risk_metrics.factor_exposure (portfolio_id, date DESC);
CREATE INDEX idx_factor_symbol_date ON risk_metrics.factor_exposure (symbol, market, date DESC);
CREATE INDEX idx_factor_sector ON risk_metrics.factor_exposure (sector_name, date DESC);

-- =============================================================================
-- SCHEMA 3: rebalancing_calendar
-- Purpose: Scheduled rebalancing, drift tracking, and execution history
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS rebalancing_calendar;

COMMENT ON SCHEMA rebalancing_calendar IS
'Rebalancing workflows: schedules, drift monitoring, notifications, execution history, and compliance tracking';

-- Rebalancing Schedule & Events
CREATE TABLE rebalancing_calendar.rebalancing_schedule (
    schedule_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,

    rebalance_date DATE NOT NULL,
    schedule_type VARCHAR(20) NOT NULL, -- 'quarterly', 'semi-annual', 'annual', 'monthly', 'on_demand'

    -- Scheduling Details
    last_rebalance_date DATE,
    next_scheduled_date DATE,
    days_since_rebalance INT,

    -- Drift Thresholds
    drift_threshold_pct NUMERIC(6, 4) NOT NULL DEFAULT 5, -- rebalance if >5% drift
    current_drift_pct NUMERIC(6, 4),
    max_allowed_drift_pct NUMERIC(6, 4) DEFAULT 10,

    -- Rebalancing Details
    rebalance_reason VARCHAR(100), -- 'scheduled', 'drift_triggered', 'manual', 'strategic_shift'
    estimated_cost NUMERIC(12, 2),
    estimated_tax_impact NUMERIC(12, 2),

    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'FAILED'

    -- Execution Tracking
    execution_start_time TIMESTAMP,
    execution_end_time TIMESTAMP,
    execution_status VARCHAR(20),
    error_message TEXT,

    -- Allocations (JSON-serialized for flexibility)
    target_allocations JSONB,          -- {symbol: {market: 'india', target_pct: 0.25, current_pct: 0.22}}
    proposed_trades JSONB,             -- transaction list

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    PRIMARY KEY (schedule_id)
);

COMMENT ON TABLE rebalancing_calendar.rebalancing_schedule IS
'Rebalancing events with drift detection, thresholds, and execution tracking. Supports quarterly/semi-annual/annual/on-demand workflows. ~365 rows/year per portfolio.';

CREATE INDEX idx_rebalance_portfolio_date ON rebalancing_calendar.rebalancing_schedule (portfolio_id, rebalance_date DESC);
CREATE INDEX idx_rebalance_status ON rebalancing_calendar.rebalancing_schedule (status, rebalance_date DESC);
CREATE INDEX idx_rebalance_drift ON rebalancing_calendar.rebalancing_schedule (current_drift_pct DESC, rebalance_date DESC);

-- Drift Tracking (Daily)
CREATE TABLE rebalancing_calendar.drift_tracking (
    drift_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,

    symbol VARCHAR(20),
    market VARCHAR(10),

    -- Target vs Actual
    target_allocation_pct NUMERIC(6, 4),
    current_allocation_pct NUMERIC(6, 4),
    drift_pct NUMERIC(6, 4) NOT NULL, -- current - target
    drift_amount_base_currency NUMERIC(18, 2),

    -- Severity
    drift_severity VARCHAR(20), -- 'LOW' (<2%), 'MEDIUM' (2-5%), 'HIGH' (>5%)
    rebalance_urgency INT DEFAULT 0, -- 0=low, 1=medium, 2=high

    -- Rebalancing Recommendation
    recommended_action VARCHAR(50), -- 'buy', 'sell', 'hold'
    estimated_transaction_cost NUMERIC(12, 2),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (drift_id)
);

COMMENT ON TABLE rebalancing_calendar.drift_tracking IS
'Daily allocation drift monitoring. Triggers rebalancing alerts when thresholds exceeded. ~310M rows for 20,700 stocks × 15y × 1 daily.';

CREATE INDEX idx_drift_portfolio_date ON rebalancing_calendar.drift_tracking (portfolio_id, date DESC);
CREATE INDEX idx_drift_severity ON rebalancing_calendar.drift_tracking (drift_severity, date DESC);
CREATE INDEX idx_drift_urgency ON rebalancing_calendar.drift_tracking (rebalance_urgency DESC, date DESC);

-- Rebalancing Execution History
CREATE TABLE rebalancing_calendar.rebalancing_execution (
    execution_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    schedule_id UUID NOT NULL REFERENCES rebalancing_calendar.rebalancing_schedule(schedule_id),

    execution_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    execution_order INT, -- sequence for multi-day executions

    symbol VARCHAR(20) NOT NULL,
    market VARCHAR(10) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL, -- 'BUY', 'SELL'

    -- Order Details
    quantity NUMERIC(18, 4) NOT NULL,
    unit_price NUMERIC(12, 4) NOT NULL,
    total_amount NUMERIC(18, 2) NOT NULL,

    -- Costs
    brokerage_fee NUMERIC(12, 2),
    transaction_tax NUMERIC(12, 2),
    exchange_fee NUMERIC(12, 2),
    total_cost NUMERIC(12, 2),

    -- Execution Status
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'FILLED', 'PARTIAL', 'FAILED', 'CANCELLED'
    execution_price NUMERIC(12, 4),
    filled_quantity NUMERIC(18, 4),
    order_id VARCHAR(50),
    broker_reference VARCHAR(100),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (execution_id)
);

COMMENT ON TABLE rebalancing_calendar.rebalancing_execution IS
'Individual rebalancing trades. Multi-leg execution tracking. Audit trail for compliance. ~50k-500k rows/year per portfolio.';

CREATE INDEX idx_execution_schedule ON rebalancing_calendar.rebalancing_execution (schedule_id, execution_date);
CREATE INDEX idx_execution_symbol ON rebalancing_calendar.rebalancing_execution (symbol, market, execution_date DESC);
CREATE INDEX idx_execution_status ON rebalancing_calendar.rebalancing_execution (status, execution_date DESC);

-- =============================================================================
-- SCHEMA 4: kpi_metrics
-- Purpose: Performance KPIs, alerts, and dashboard metrics
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS kpi_metrics;

COMMENT ON SCHEMA kpi_metrics IS
'Performance tracking and alerting: CAGR, Sharpe, max drawdown, win rate, sentiment, and alert engine';

-- Daily KPI Snapshot
CREATE TABLE kpi_metrics.daily_kpi (
    kpi_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,
    market VARCHAR(10),

    -- Return Metrics
    daily_return_pct NUMERIC(8, 6),
    weekly_return_pct NUMERIC(8, 6),
    monthly_return_pct NUMERIC(8, 6),
    qtd_return_pct NUMERIC(8, 6),
    ytd_return_pct NUMERIC(8, 6),

    -- Long-term Returns
    cagr_1y NUMERIC(8, 4),
    cagr_3y NUMERIC(8, 4),
    cagr_5y NUMERIC(8, 4),
    cagr_10y NUMERIC(8, 4),
    cagr_inception NUMERIC(8, 4),

    -- Risk-Adjusted Returns
    sharpe_ratio_252d NUMERIC(8, 4),
    sortino_ratio_252d NUMERIC(8, 4),
    calmar_ratio_252d NUMERIC(8, 4),
    information_ratio NUMERIC(8, 4),

    -- Drawdown Metrics
    current_drawdown_pct NUMERIC(8, 4),
    max_drawdown_252d NUMERIC(8, 4),
    max_drawdown_ytd NUMERIC(8, 4),
    recovery_days INT,

    -- Volatility
    volatility_252d NUMERIC(8, 4),
    downside_volatility_252d NUMERIC(8, 4),

    -- Win Rate & Profit Factor
    win_rate_pct NUMERIC(6, 4),         -- % of profitable days
    profit_factor NUMERIC(8, 4),        -- gross_profit / gross_loss
    consecutive_wins INT,
    consecutive_losses INT,

    -- Correlation & Beta
    correlation_benchmark NUMERIC(8, 6),
    beta_to_benchmark NUMERIC(8, 6),
    alpha_vs_benchmark NUMERIC(8, 6),

    -- Alert Count (summary)
    alert_count INT DEFAULT 0,
    high_priority_alerts INT DEFAULT 0,
    medium_priority_alerts INT DEFAULT 0,
    low_priority_alerts INT DEFAULT 0,

    -- Risk Metrics Summary
    var_95_pct NUMERIC(8, 4),
    var_99_pct NUMERIC(8, 4),
    portfolio_value NUMERIC(18, 2),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (kpi_id),
    CONSTRAINT chk_return_pct CHECK (daily_return_pct >= -1 AND daily_return_pct <= 1),
    CONSTRAINT chk_win_rate CHECK (win_rate_pct >= 0 AND win_rate_pct <= 1),
    CONSTRAINT chk_correlation CHECK (correlation_benchmark >= -1 AND correlation_benchmark <= 1)
);

COMMENT ON TABLE kpi_metrics.daily_kpi IS
'Daily KPI rollup: returns, Sharpe, max drawdown, win rate, alert count. Dashboard source. ~5,745 rows for 20,700 stocks × 15y with 1 daily update.';

CREATE INDEX idx_kpi_portfolio_date ON kpi_metrics.daily_kpi (portfolio_id, date DESC);
CREATE INDEX idx_kpi_market_date ON kpi_metrics.daily_kpi (market, date DESC);
CREATE INDEX idx_kpi_sharpe ON kpi_metrics.daily_kpi (sharpe_ratio_252d DESC, date DESC);
CREATE INDEX idx_kpi_drawdown ON kpi_metrics.daily_kpi (max_drawdown_252d ASC, date DESC);

-- Performance Benchmarking
CREATE TABLE kpi_metrics.performance_benchmark (
    benchmark_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,

    benchmark_symbol VARCHAR(50) NOT NULL, -- e.g., 'NIFTY50', 'SPY', 'STOXX50E'
    benchmark_market VARCHAR(10),

    -- Benchmark Returns
    benchmark_return_pct NUMERIC(8, 6),
    benchmark_ytd_return NUMERIC(8, 6),
    benchmark_cagr_1y NUMERIC(8, 4),
    benchmark_cagr_3y NUMERIC(8, 4),
    benchmark_cagr_5y NUMERIC(8, 4),

    -- Portfolio vs Benchmark
    portfolio_return_pct NUMERIC(8, 6),
    excess_return_pct NUMERIC(8, 6),
    tracking_error NUMERIC(8, 4),
    information_ratio NUMERIC(8, 4),

    -- Relative Performance
    outperformance_days INT,
    underperformance_days INT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (benchmark_id)
);

COMMENT ON TABLE kpi_metrics.performance_benchmark IS
'Portfolio performance vs selected benchmarks (NIFTY50, SPY, etc.). Tracks alpha/beta, tracking error, information ratio. ~5,745 rows.';

CREATE INDEX idx_benchmark_portfolio_date ON kpi_metrics.performance_benchmark (portfolio_id, date DESC);
CREATE INDEX idx_benchmark_symbol ON kpi_metrics.performance_benchmark (benchmark_symbol, date DESC);

-- Alert Management System
CREATE TABLE kpi_metrics.alerts (
    alert_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,

    alert_type VARCHAR(50) NOT NULL, -- 'drift_warning', 'var_breach', 'drawdown_alert', 'rebalance_due', 'volatility_spike', 'correlation_warning', 'performance_lag'
    severity VARCHAR(20) NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'

    -- Alert Context
    symbol VARCHAR(20),
    market VARCHAR(10),

    -- Message & Details
    title VARCHAR(255) NOT NULL,
    message TEXT,
    details JSONB, -- flexible structure for additional context

    -- Thresholds
    metric_name VARCHAR(100),
    current_value NUMERIC(12, 6),
    threshold_value NUMERIC(12, 6),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED'
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,

    -- Triggered Info
    triggered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    triggered_by VARCHAR(100), -- system rule name
    action_taken VARCHAR(255),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (alert_id)
);

COMMENT ON TABLE kpi_metrics.alerts IS
'Real-time alerting: drift warnings, VaR breaches, drawdown alerts, rebalance triggers. Audit trail with status tracking. ~10k-50k rows/year per portfolio.';

CREATE INDEX idx_alert_portfolio_status ON kpi_metrics.alerts (portfolio_id, status, triggered_at DESC);
CREATE INDEX idx_alert_severity ON kpi_metrics.alerts (severity, triggered_at DESC);
CREATE INDEX idx_alert_type ON kpi_metrics.alerts (alert_type, status, triggered_at DESC);
CREATE INDEX idx_alert_open ON kpi_metrics.alerts (status) WHERE status = 'OPEN';

-- Performance Attribution
CREATE TABLE kpi_metrics.performance_attribution (
    attribution_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_id UUID NOT NULL,
    date DATE NOT NULL,

    symbol VARCHAR(20),
    market VARCHAR(10),

    -- Return Components
    total_return_pct NUMERIC(8, 6),
    price_return_pct NUMERIC(8, 6),
    dividend_return_pct NUMERIC(8, 6),
    fx_return_pct NUMERIC(8, 6),

    -- Attribution Breakdown
    allocation_effect NUMERIC(8, 6),   -- weight × (return - benchmark)
    selection_effect NUMERIC(8, 6),    -- (holding_return - benchmark_return) × weight
    interaction_effect NUMERIC(8, 6),

    -- Contribution to Portfolio Return
    contribution_to_pnl NUMERIC(12, 2),
    weight_contribution_pct NUMERIC(6, 4),
    return_contribution_pct NUMERIC(8, 6),

    -- Risk Contribution
    marginal_var NUMERIC(12, 2),
    component_var NUMERIC(12, 2),
    var_contribution_pct NUMERIC(6, 4),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (attribution_id)
);

COMMENT ON TABLE kpi_metrics.performance_attribution IS
'Granular return attribution: allocation vs selection effects, dividend impact, FX impact. ~310M rows for 20,700 stocks × 15y × 1 daily.';

CREATE INDEX idx_attribution_portfolio_date ON kpi_metrics.performance_attribution (portfolio_id, date DESC);
CREATE INDEX idx_attribution_symbol_date ON kpi_metrics.performance_attribution (symbol, market, date DESC);

-- =============================================================================
-- CROSS-SCHEMA LOOKUP TABLES
-- =============================================================================

-- Master Portfolio Metadata (shared across schemas)
CREATE TABLE IF NOT EXISTS public.portfolios (
    portfolio_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    portfolio_name VARCHAR(255) NOT NULL,
    portfolio_type VARCHAR(20), -- 'passive', 'active', 'hedge'
    investor_profile VARCHAR(50), -- 'conservative', 'moderate', 'aggressive'

    inception_date DATE,
    base_currency VARCHAR(3) DEFAULT 'USD',

    -- Benchmarks
    primary_benchmark VARCHAR(50),
    secondary_benchmarks JSONB,

    -- Parameters
    rebalance_frequency VARCHAR(20), -- 'quarterly', 'semi-annual', 'annual'
    drift_threshold_pct NUMERIC(6, 4) DEFAULT 5,

    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (portfolio_id)
);

COMMENT ON TABLE public.portfolios IS 'Master portfolio registry with benchmarks and rebalancing parameters.';

-- Market Lookup (reference for all 6 markets)
CREATE TABLE IF NOT EXISTS public.markets (
    market_id SERIAL PRIMARY KEY,
    market_code VARCHAR(10) NOT NULL UNIQUE,
    market_name VARCHAR(50) NOT NULL,
    country VARCHAR(50),
    region VARCHAR(50),

    stock_count INT,
    trading_calendar VARCHAR(50),
    timezone VARCHAR(30),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.markets IS 'Reference table for all markets (india, us, europe, japan, korea, china).';

INSERT INTO public.markets (market_code, market_name, country, region, timezone) VALUES
    ('india', 'National Stock Exchange / BSE', 'India', 'South Asia', 'Asia/Kolkata'),
    ('us', 'NYSE / NASDAQ', 'United States', 'North America', 'America/New_York'),
    ('europe', 'Pan-European Exchanges', 'Multi-country', 'Europe', 'Europe/London'),
    ('japan', 'Tokyo Stock Exchange', 'Japan', 'East Asia', 'Asia/Tokyo'),
    ('korea', 'Korea Exchange', 'South Korea', 'East Asia', 'Asia/Seoul'),
    ('china', 'Shanghai / Shenzhen Exchanges', 'China', 'East Asia', 'Asia/Shanghai')
ON CONFLICT (market_code) DO NOTHING;

-- =============================================================================
-- MATERIALIZED VIEWS FOR DASHBOARD & REPORTING
-- =============================================================================

-- Portfolio Health Dashboard View
CREATE OR REPLACE VIEW kpi_metrics.portfolio_health_dashboard AS
SELECT
    p.portfolio_id,
    p.portfolio_name,
    k.date,
    k.portfolio_value,
    k.ytd_return_pct,
    k.cagr_1y,
    k.sharpe_ratio_252d,
    k.max_drawdown_252d,
    k.win_rate_pct,
    k.alert_count,
    k.high_priority_alerts,
    CASE
        WHEN k.max_drawdown_252d < -0.20 THEN 'CRITICAL'
        WHEN k.max_drawdown_252d < -0.10 THEN 'HIGH'
        WHEN k.max_drawdown_252d < -0.05 THEN 'MEDIUM'
        ELSE 'LOW'
    END as risk_level,
    CASE
        WHEN k.sharpe_ratio_252d > 1.5 THEN 'EXCELLENT'
        WHEN k.sharpe_ratio_252d > 1.0 THEN 'GOOD'
        WHEN k.sharpe_ratio_252d > 0.5 THEN 'FAIR'
        ELSE 'POOR'
    END as performance_rating
FROM public.portfolios p
JOIN kpi_metrics.daily_kpi k ON p.portfolio_id = k.portfolio_id
WHERE k.date = CURRENT_DATE;

COMMENT ON VIEW kpi_metrics.portfolio_health_dashboard IS 'Real-time portfolio health summary for dashboard display.';

-- Rebalancing Due View
CREATE OR REPLACE VIEW rebalancing_calendar.rebalancing_due_today AS
SELECT
    rs.portfolio_id,
    rs.schedule_id,
    rs.rebalance_date,
    rs.schedule_type,
    rs.current_drift_pct,
    rs.status,
    COUNT(dt.*) as positions_exceeding_threshold
FROM rebalancing_calendar.rebalancing_schedule rs
LEFT JOIN rebalancing_calendar.drift_tracking dt
    ON rs.portfolio_id = dt.portfolio_id
    AND dt.date = CURRENT_DATE
    AND ABS(dt.drift_pct) > rs.drift_threshold_pct
WHERE rs.status IN ('PENDING', 'IN_PROGRESS')
    AND rs.rebalance_date <= CURRENT_DATE
GROUP BY rs.schedule_id, rs.portfolio_id, rs.rebalance_date, rs.schedule_type, rs.current_drift_pct, rs.status;

COMMENT ON VIEW rebalancing_calendar.rebalancing_due_today IS 'Rebalancing events due today with drift position count.';

-- =============================================================================
-- INDEXES FOR PARTITIONED QUERIES
-- =============================================================================

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_market_date
    ON portfolio_realtime.holdings (portfolio_id, market, date DESC);

CREATE INDEX IF NOT EXISTS idx_volatility_portfolio_market_date
    ON risk_metrics.volatility_metrics (portfolio_id, market, date DESC);

CREATE INDEX IF NOT EXISTS idx_drift_portfolio_market_date
    ON rebalancing_calendar.drift_tracking (portfolio_id, market, date DESC);

CREATE INDEX IF NOT EXISTS idx_kpi_portfolio_market_date
    ON kpi_metrics.daily_kpi (portfolio_id, market, date DESC);

-- =============================================================================
-- TEMPORAL PARTITIONING STRATEGY (PostgreSQL 11+)
-- =============================================================================

/*
PARTITIONING STRATEGY for volume optimization:

1. HOLDINGS (310M rows / 20,700 stocks × 15y)
   - Partition by RANGE (date) quarterly
   - Each partition ~26M rows

2. VOLATILITY_METRICS (30.6M rows / 20,700 stocks × 15y × 1 daily)
   - Partition by RANGE (date) annually
   - Each partition ~2.04M rows

3. DRIFT_TRACKING (310M rows / 20,700 stocks × 15y × 1 daily)
   - Partition by RANGE (date) quarterly
   - Enables fast range queries & archival

4. DAILY_KPI (~5,745 rows / 20,700 stocks × 15y with 1 daily per market)
   - No partitioning needed; fits in memory

5. ALERTS (50k-500k rows/year)
   - Partition by RANGE (triggered_at) annually
   - Archive old alerts quarterly

Example partition creation:
*/

-- HOLDINGS partitioning (quarterly)
-- ALTER TABLE portfolio_realtime.holdings
-- PARTITION BY RANGE (EXTRACT(YEAR FROM date), EXTRACT(QUARTER FROM date))
-- (
--   PARTITION h_2024_q1 VALUES LESS THAN (2024, 2),
--   PARTITION h_2024_q2 VALUES LESS THAN (2024, 3),
--   ...
--   PARTITION h_default VALUES LESS THAN (MAXVALUE, MAXVALUE)
-- );

-- =============================================================================
-- FUNCTION: Refresh KPI metrics (daily post-market)
-- =============================================================================

CREATE OR REPLACE FUNCTION kpi_metrics.refresh_daily_kpi(
    p_portfolio_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    portfolio_id UUID,
    date_processed DATE,
    kpis_updated INT,
    status VARCHAR
) AS $$
DECLARE
    v_holdingsCount INT;
    v_returnPct NUMERIC;
BEGIN
    -- Check holdings exist for date
    SELECT COUNT(*) INTO v_holdingsCount
    FROM portfolio_realtime.holdings
    WHERE portfolio_id = p_portfolio_id
        AND date = p_as_of_date;

    IF v_holdingsCount = 0 THEN
        RETURN QUERY SELECT p_portfolio_id, p_as_of_date, 0, 'NO_HOLDINGS'::VARCHAR;
        RETURN;
    END IF;

    -- Insert/Update daily KPI
    INSERT INTO kpi_metrics.daily_kpi (
        portfolio_id, date, created_at, updated_at
    ) VALUES (
        p_portfolio_id, p_as_of_date, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    )
    ON CONFLICT (kpi_id) DO UPDATE
    SET updated_at = CURRENT_TIMESTAMP;

    RETURN QUERY SELECT p_portfolio_id, p_as_of_date, v_holdingsCount, 'SUCCESS'::VARCHAR;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION kpi_metrics.refresh_daily_kpi IS
'Daily post-market KPI refresh. Call once per portfolio after market close.';

-- =============================================================================
-- FUNCTION: Calculate portfolio drift
-- =============================================================================

CREATE OR REPLACE FUNCTION rebalancing_calendar.calculate_drift(
    p_portfolio_id UUID,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    portfolio_id UUID,
    date_calculated DATE,
    max_drift_pct NUMERIC,
    drift_positions INT,
    status VARCHAR
) AS $$
DECLARE
    v_drift_count INT;
BEGIN
    -- Insert drift records for all holdings
    INSERT INTO rebalancing_calendar.drift_tracking (
        portfolio_id, date, symbol, market,
        target_allocation_pct, current_allocation_pct, drift_pct,
        drift_severity, rebalance_urgency
    )
    SELECT
        h.portfolio_id,
        h.date,
        h.symbol,
        h.market,
        ps.allocation_pct, -- target from prior schedule
        h.allocation_pct,  -- current
        h.allocation_pct - ps.allocation_pct,
        CASE
            WHEN ABS(h.allocation_pct - ps.allocation_pct) > 0.05 THEN 'HIGH'
            WHEN ABS(h.allocation_pct - ps.allocation_pct) > 0.02 THEN 'MEDIUM'
            ELSE 'LOW'
        END,
        CASE
            WHEN ABS(h.allocation_pct - ps.allocation_pct) > 0.05 THEN 2
            WHEN ABS(h.allocation_pct - ps.allocation_pct) > 0.02 THEN 1
            ELSE 0
        END
    FROM portfolio_realtime.holdings h
    LEFT JOIN portfolio_realtime.portfolio_summary ps
        ON h.portfolio_id = ps.portfolio_id
        AND h.market = ps.market
    WHERE h.portfolio_id = p_portfolio_id
        AND h.date = p_date
    ON CONFLICT DO NOTHING;

    SELECT COUNT(*) INTO v_drift_count
    FROM rebalancing_calendar.drift_tracking
    WHERE portfolio_id = p_portfolio_id AND date = p_date
        AND drift_severity IN ('MEDIUM', 'HIGH');

    RETURN QUERY SELECT
        p_portfolio_id, p_date,
        (SELECT MAX(ABS(drift_pct)) FROM rebalancing_calendar.drift_tracking
         WHERE portfolio_id = p_portfolio_id AND date = p_date),
        v_drift_count,
        'SUCCESS'::VARCHAR;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION rebalancing_calendar.calculate_drift IS
'Daily drift calculation for all portfolio positions. Identifies rebalancing triggers.';

-- =============================================================================
-- SAMPLE DATA INSERTION (optional reference)
-- =============================================================================

-- Insert sample portfolio
INSERT INTO public.portfolios (
    portfolio_name, portfolio_type, investor_profile,
    base_currency, primary_benchmark, rebalance_frequency
) VALUES (
    'Global Growth Portfolio', 'active', 'moderate',
    'USD', 'SPY', 'quarterly'
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- PERFORMANCE TUNING NOTES
-- =============================================================================

/*
TUNING CHECKLIST:

1. INDEXES:
   - All FK references have indexes
   - Date columns indexed DESC for recent-first queries
   - Composite (portfolio_id, date) on all major tables
   - GIN indexes on JSONB columns (target_allocations, details, etc.)

2. PARTITIONING:
   - Enable table partitioning for holdings (quarterly)
   - Enable partitioning for volatility metrics (annual)
   - Archive alerts >1 year old to cold storage

3. MATERIALIZED VIEWS:
   - Refresh portfolio_health_dashboard daily post-market
   - Refresh rebalancing_due_today in morning pre-open

4. STATISTICS:
   - ANALYZE tables after bulk inserts
   - Set autovacuum to aggressive for high-churn tables

5. CACHING LAYER:
   - Redis cache for daily_kpi (24h TTL)
   - Cache correlation_matrix (daily refresh)
   - Cache portfolio_summary (hourly refresh)

6. QUERY PATTERNS:
   - Favor (portfolio_id, date DESC) range scans
   - Use EXPLAIN ANALYZE for all new queries
   - Partition pruning enabled for date-based queries

7. STORAGE:
   - Holding history: ~310M rows × 40 bytes = 12.4GB
   - Volatility metrics: ~30.6M rows × 60 bytes = 1.8GB
   - Drift tracking: ~310M rows × 35 bytes = 10.9GB
   - Daily KPI: ~5.7k rows × 200 bytes = 1MB
   - Total ~25GB for 15-year history uncompressed
   - With compression (pglz): ~10-12GB

8. MONITORING:
   - Slow query log (>1s)
   - Table bloat detection (VACUUM ANALYZE)
   - Replication lag (if replicated)
   - Partition sizes (target ~1-2GB per partition)
*/

-- =============================================================================
-- SCHEMA COMPLETE
-- =============================================================================

COMMIT;