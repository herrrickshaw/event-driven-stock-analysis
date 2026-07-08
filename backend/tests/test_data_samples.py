"""
Test data samples for manual testing and documentation.

This module contains realistic test data that can be used for:
- Manual API testing (copy-paste JSON payloads)
- Performance testing
- Documentation examples
- Debugging
"""

# ──────────────────────────────────────────────────────────────────────────────
# Portfolio Upload Payloads
# ──────────────────────────────────────────────────────────────────────────────

PORTFOLIO_INDIA_PAYLOAD = {
    "market": "india",
    "holdings": [
        {
            "yf_ticker": "RELIANCE.NS",
            "name": "Reliance Industries",
            "quantity": 100.0,
            "purchase_price": 2500.0,
            "purchase_date": "2023-01-15",
        },
        {
            "yf_ticker": "HDFCBANK.NS",
            "name": "HDFC Bank",
            "quantity": 50.0,
            "purchase_price": 1500.0,
            "purchase_date": "2023-03-20",
        },
        {
            "yf_ticker": "INFY.NS",
            "name": "Infosys",
            "quantity": 200.0,
            "purchase_price": 1350.0,
            "purchase_date": "2023-02-10",
        },
        {
            "yf_ticker": "TCS.NS",
            "name": "Tata Consultancy Services",
            "quantity": 75.0,
            "purchase_price": 3200.0,
            "purchase_date": "2023-04-05",
        },
    ],
}

PORTFOLIO_US_PAYLOAD = {
    "market": "us",
    "holdings": [
        {
            "yf_ticker": "AAPL",
            "name": "Apple Inc",
            "quantity": 50.0,
            "purchase_price": 150.0,
            "purchase_date": "2023-01-15",
        },
        {
            "yf_ticker": "MSFT",
            "name": "Microsoft",
            "quantity": 30.0,
            "purchase_price": 250.0,
            "purchase_date": "2023-02-20",
        },
        {
            "yf_ticker": "GOOGL",
            "name": "Alphabet Inc",
            "quantity": 20.0,
            "purchase_price": 100.0,
            "purchase_date": "2023-03-10",
        },
    ],
}

PORTFOLIO_GLOBAL_PAYLOAD = {
    "market": "global",
    "holdings": [
        # India
        {
            "yf_ticker": "RELIANCE.NS",
            "name": "Reliance Industries",
            "quantity": 100.0,
            "purchase_price": 2500.0,
            "purchase_date": "2023-01-15",
        },
        # US
        {
            "yf_ticker": "AAPL",
            "name": "Apple Inc",
            "quantity": 50.0,
            "purchase_price": 150.0,
            "purchase_date": "2023-01-15",
        },
        # Europe
        {
            "yf_ticker": "ADS.DE",
            "name": "Adidas AG",
            "quantity": 30.0,
            "purchase_price": 90.0,
            "purchase_date": "2023-02-20",
        },
        # Japan
        {
            "yf_ticker": "7203.T",
            "name": "Toyota Motor Corp",
            "quantity": 50.0,
            "purchase_price": 2000.0,
            "purchase_date": "2023-02-10",
        },
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# Watchlist Payloads
# ──────────────────────────────────────────────────────────────────────────────

WATCHLIST_ADD_INDIA = {
    "tickers": ["RELIANCE", "HDFCBANK", "INFY", "TCS", "LT"],
    "market": "india",
}

WATCHLIST_ADD_US = {
    "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    "market": "us",
}

WATCHLIST_ADD_MIXED = {
    "tickers": ["RELIANCE", "AAPL", "ADS.DE", "7203.T"],
    "market": "mixed",
}

# ──────────────────────────────────────────────────────────────────────────────
# Alert Event Examples
# ──────────────────────────────────────────────────────────────────────────────

ALERT_PRICE_UP = {
    "event_type": "PRICE_UP",
    "ticker": "RELIANCE",
    "market": "india",
    "data": {
        "old_price": 2800.0,
        "new_price": 2875.5,
        "change_pct": 2.7,
        "change_amount": 75.5,
    },
    "timestamp": "2024-01-15T10:30:00+00:00",
}

ALERT_RSI_OVERBOUGHT = {
    "event_type": "RSI_OVERBOUGHT",
    "ticker": "HDFCBANK",
    "market": "india",
    "data": {
        "rsi": 75.2,
        "threshold": 70,
        "price": 1680.5,
    },
    "timestamp": "2024-01-15T11:00:00+00:00",
}

ALERT_RSI_OVERSOLD = {
    "event_type": "RSI_OVERSOLD",
    "ticker": "INFY",
    "market": "india",
    "data": {
        "rsi": 28.5,
        "threshold": 30,
        "price": 1475.0,
    },
    "timestamp": "2024-01-15T11:30:00+00:00",
}

ALERT_VOLUME_SURGE = {
    "event_type": "VOLUME_SURGE",
    "ticker": "TCS",
    "market": "india",
    "data": {
        "current_volume": 85000000,
        "avg_volume": 40000000,
        "surge_pct": 112.5,
    },
    "timestamp": "2024-01-15T12:00:00+00:00",
}

ALERT_52W_HIGH = {
    "event_type": "HIGH_52W",
    "ticker": "AAPL",
    "market": "us",
    "data": {
        "current_price": 210.0,
        "high_52w": 209.5,
        "near_high": True,
    },
    "timestamp": "2024-01-15T12:30:00+00:00",
}

ALERT_52W_LOW = {
    "event_type": "LOW_52W",
    "ticker": "MSFT",
    "market": "us",
    "data": {
        "current_price": 340.0,
        "low_52w": 341.0,
        "near_low": True,
    },
    "timestamp": "2024-01-15T13:00:00+00:00",
}

# ──────────────────────────────────────────────────────────────────────────────
# Expected API Responses
# ──────────────────────────────────────────────────────────────────────────────

MARKETS_RESPONSE = [
    {
        "id": "india",
        "label": "India (NSE / BSE)",
        "exchange": "NSE/BSE",
        "yf_suffix": ".NS / .BO",
    },
    {
        "id": "us",
        "label": "United States (S&P 500)",
        "exchange": "NYSE/NASDAQ",
        "yf_suffix": "",
    },
    {
        "id": "europe",
        "label": "Europe (Euronext / Xetra)",
        "exchange": "Multi",
        "yf_suffix": ".PA / .DE / .AS …",
    },
    {
        "id": "japan",
        "label": "Japan (TSE)",
        "exchange": "TSE",
        "yf_suffix": ".T",
    },
    {
        "id": "korea",
        "label": "Korea (KRX)",
        "exchange": "KRX",
        "yf_suffix": ".KS / .KQ",
    },
    {
        "id": "china",
        "label": "China (SSE / SZSE)",
        "exchange": "SSE/SZSE",
        "yf_suffix": ".SS / .SZ",
    },
]

PORTFOLIO_HISTORY_RESPONSE = {
    "market": "india",
    "holdings_enriched": [
        {
            "yf_ticker": "RELIANCE.NS",
            "symbol": "RELIANCE",
            "name": "Reliance Industries",
            "quantity": 100.0,
            "purchase_price": 2500.0,
            "purchase_date": "2023-01-15",
            "cost_basis": 250000.0,
            "current_price": 2875.5,
            "current_value": 287550.0,
            "unrealised_pnl": 37550.0,
            "pnl_percentage": 15.02,
            "rsi": 62.3,
            "rsi_signal": "healthy",
            "pe": 24.5,
            "pb": 4.2,
            "roe": 18.5,
        },
        {
            "yf_ticker": "HDFCBANK.NS",
            "symbol": "HDFCBANK",
            "name": "HDFC Bank",
            "quantity": 50.0,
            "purchase_price": 1500.0,
            "purchase_date": "2023-03-20",
            "cost_basis": 75000.0,
            "current_price": 1680.5,
            "current_value": 84025.0,
            "unrealised_pnl": 9025.0,
            "pnl_percentage": 12.03,
            "rsi": 58.2,
            "rsi_signal": "healthy",
            "pe": 18.3,
            "pb": 2.8,
            "roe": 22.1,
        },
    ],
    "portfolio_value": 625000.0,
    "portfolio_cost_basis": 595000.0,
    "portfolio_pnl": 30000.0,
    "portfolio_return_pct": 5.04,
}

ALERTS_LATEST_RESPONSE = {
    "alerts": [
        ALERT_PRICE_UP,
        ALERT_RSI_OVERBOUGHT,
        ALERT_VOLUME_SURGE,
    ],
}

WATCHLIST_RESPONSE = {
    "watched": ["RELIANCE", "HDFCBANK", "INFY", "TCS", "LT"],
}

# ──────────────────────────────────────────────────────────────────────────────
# Load Test Scenarios
# ──────────────────────────────────────────────────────────────────────────────

LOAD_TEST_SCENARIOS = {
    "baseline": {
        "users": 500,
        "spawn_rate": 50,
        "duration_minutes": 5,
        "target_success_rate": 0.95,
        "target_p95_latency_ms": 150,
    },
    "normal": {
        "users": 1000,
        "spawn_rate": 50,
        "duration_minutes": 5,
        "target_success_rate": 0.90,
        "target_p95_latency_ms": 250,
    },
    "stress": {
        "users": 5000,
        "spawn_rate": 200,
        "duration_minutes": 3,
        "target_success_rate": 0.70,
        "target_p95_latency_ms": 800,
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Risk Metrics Examples
# ──────────────────────────────────────────────────────────────────────────────

RISK_METRICS_EXAMPLE = {
    "portfolio": {
        "daily_returns": [0.01, -0.02, 0.015, -0.005, 0.02],
        "daily_volatility": 0.0152,
        "annualized_volatility": 0.242,  # daily_vol * sqrt(252)
        "sharpe_ratio": 0.62,  # (return - risk_free) / volatility
        "var_95": -0.025,  # 95% confidence VaR
        "var_99": -0.035,  # 99% confidence VaR
        "max_drawdown": 0.05,
        "beta": 1.15,
    },
    "holdings": {
        "RELIANCE": {
            "daily_volatility": 0.020,
            "annualized_volatility": 0.318,
            "correlation_to_portfolio": 0.85,
            "beta_to_market": 1.20,
        },
        "HDFCBANK": {
            "daily_volatility": 0.015,
            "annualized_volatility": 0.238,
            "correlation_to_portfolio": 0.92,
            "beta_to_market": 1.05,
        },
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Rebalancing Scenarios
# ──────────────────────────────────────────────────────────────────────────────

REBALANCING_BEFORE = {
    "portfolio_value": 625000.0,
    "holdings": {
        "RELIANCE": {
            "quantity": 100,
            "current_price": 2875.5,
            "current_value": 287550.0,
            "current_allocation": 0.46,  # 46%
            "target_allocation": 0.40,  # 40%
            "drift": 0.06,  # 6% over target
        },
        "HDFCBANK": {
            "quantity": 50,
            "current_price": 1680.5,
            "current_value": 84025.0,
            "current_allocation": 0.134,  # 13.4%
            "target_allocation": 0.35,  # 35%
            "drift": -0.216,  # 21.6% under target
        },
        "INFY": {
            "quantity": 200,
            "current_price": 1475.0,
            "current_value": 295000.0,
            "current_allocation": 0.472,  # 47.2%
            "target_allocation": 0.25,  # 25%
            "drift": 0.222,  # 22.2% over target
        },
    },
}

REBALANCING_ACTIONS = {
    "rebalance_threshold": 0.05,  # 5% drift triggers rebalance
    "actions": [
        {
            "action": "SELL",
            "ticker": "INFY",
            "quantity": 27,
            "reason": "Drift exceeds threshold (22.2% over target)",
        },
        {
            "action": "SELL",
            "ticker": "RELIANCE",
            "quantity": 3,
            "reason": "Drift exceeds threshold (6% over target)",
        },
        {
            "action": "BUY",
            "ticker": "HDFCBANK",
            "quantity": 68,
            "reason": "Drift exceeds threshold (21.6% under target)",
        },
    ],
}

REBALANCING_AFTER = {
    "portfolio_value": 625000.0,
    "holdings": {
        "RELIANCE": {
            "quantity": 97,
            "current_allocation": 0.4,  # 40%
            "drift": 0.0,
        },
        "HDFCBANK": {
            "quantity": 118,
            "current_allocation": 0.35,  # 35%
            "drift": 0.0,
        },
        "INFY": {
            "quantity": 173,
            "current_allocation": 0.25,  # 25%
            "drift": 0.0,
        },
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Error Response Examples
# ──────────────────────────────────────────────────────────────────────────────

ERROR_INVALID_MARKET = {
    "detail": 'Unknown market "invalid". Choose from: india, us, europe, japan, korea, china'
}

ERROR_UNSUPPORTED_FORMAT = {
    "detail": 'Unsupported type ".txt". Upload .xlsx, .xls, or .pdf.'
}

ERROR_EMPTY_HOLDINGS = {
    "detail": "holdings list is empty"
}

ERROR_FILE_TOO_LARGE = {
    "detail": "File exceeds 20 MB."
}

# ──────────────────────────────────────────────────────────────────────────────
# Curl Command Examples
# ──────────────────────────────────────────────────────────────────────────────

CURL_LIST_MARKETS = """
curl -X GET http://localhost:8000/api/portfolio/markets \\
  -H "Accept: application/json"
"""

CURL_FETCH_PORTFOLIO_HISTORY = """
curl -X POST http://localhost:8000/api/portfolio/history \\
  -H "Content-Type: application/json" \\
  -d '{
    "market": "india",
    "holdings": [
      {
        "yf_ticker": "RELIANCE.NS",
        "quantity": 100,
        "purchase_price": 2500,
        "purchase_date": "2023-01-15"
      },
      {
        "yf_ticker": "HDFCBANK.NS",
        "quantity": 50,
        "purchase_price": 1500,
        "purchase_date": "2023-03-20"
      }
    ]
  }'
"""

CURL_ADD_WATCHLIST = """
curl -X POST http://localhost:8000/api/alerts/portfolio \\
  -H "Content-Type: application/json" \\
  -d '{
    "tickers": ["RELIANCE", "HDFCBANK", "INFY"],
    "market": "india"
  }'
"""

CURL_GET_ALERTS = """
curl -X GET "http://localhost:8000/api/alerts/latest?limit=20" \\
  -H "Accept: application/json"
"""

CURL_TRIGGER_ALERT = """
curl -X POST "http://localhost:8000/api/alerts/trigger/RELIANCE?market=india" \\
  -H "Accept: application/json"
"""

# ──────────────────────────────────────────────────────────────────────────────
# Python Requests Examples
# ──────────────────────────────────────────────────────────────────────────────

PYTHON_REQUESTS_EXAMPLE = """
import requests

BASE_URL = "http://localhost:8000"

# List markets
response = requests.get(f"{BASE_URL}/api/portfolio/markets")
markets = response.json()

# Fetch portfolio history
portfolio = {
    "market": "india",
    "holdings": [
        {
            "yf_ticker": "RELIANCE.NS",
            "quantity": 100,
            "purchase_price": 2500,
            "purchase_date": "2023-01-15",
        }
    ]
}
response = requests.post(f"{BASE_URL}/api/portfolio/history", json=portfolio)
history = response.json()

# Add to watchlist
watchlist = {
    "tickers": ["RELIANCE", "HDFCBANK"],
    "market": "india",
}
response = requests.post(f"{BASE_URL}/api/alerts/portfolio", json=watchlist)

# Get alerts
response = requests.get(f"{BASE_URL}/api/alerts/latest?limit=10")
alerts = response.json()
"""
