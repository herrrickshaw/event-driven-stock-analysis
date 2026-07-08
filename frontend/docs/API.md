# API Documentation

This document describes the expected backend API endpoints for the Event-Driven Stock Dashboard.

## Base URL

```
http://localhost:8000/api
```

Configure via `REACT_APP_API_URL` in `.env.local`.

## Authentication

Currently no authentication implemented. Add Bearer token handling if needed:

```tsx
// In src/services/api.ts
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

## Response Format

All successful responses follow this format:

```json
{
  "success": true,
  "data": { /* actual data */ },
  "timestamp": "2024-07-08T10:30:00Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error message",
  "timestamp": "2024-07-08T10:30:00Z"
}
```

## Endpoints

### Performance

#### GET `/api/performance/metrics`

Fetch portfolio performance metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "cagr": 12.5,
    "sharpe_ratio": 1.45,
    "ytd_return": 8.3,
    "total_return": 45.2,
    "start_date": "2022-01-01",
    "end_date": "2024-07-08"
  },
  "timestamp": "2024-07-08T10:30:00Z"
}
```

#### GET `/api/performance/historical?market=india&days=365`

Fetch historical performance data.

**Query Parameters:**
- `market` (optional): Filter by market
- `days` (optional): Number of days back (default: 365)

**Response:**
```json
{
  "success": true,
  "data": [
    { "date": "2024-01-01", "value": 100000 },
    { "date": "2024-01-02", "value": 102000 },
    ...
  ],
  "timestamp": "2024-07-08T10:30:00Z"
}
```

### Risk

#### GET `/api/risk/metrics`

Fetch risk metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "volatility": 14.2,
    "var_95": -15000,
    "var_99": -22000,
    "max_drawdown": -12.3,
    "sharpe_ratio": 1.45,
    "sortino_ratio": 1.8,
    "calmar_ratio": 1.2
  },
  "timestamp": "2024-07-08T10:30:00Z"
}
```

#### GET `/api/risk/correlation`

Fetch asset correlation matrix.

**Response:**
```json
{
  "success": true,
  "data": {
    "markets": ["india", "us", "europe", "japan", "korea"],
    "data": [
      [1.0, 0.45, 0.38, 0.42, 0.35],
      [0.45, 1.0, 0.72, 0.55, 0.48],
      [0.38, 0.72, 1.0, 0.42, 0.38],
      [0.42, 0.55, 0.42, 1.0, 0.45],
      [0.35, 0.48, 0.38, 0.45, 1.0]
    ],
    "timestamp": "2024-07-08T10:30:00Z"
  }
}
```

#### GET `/api/risk/var`

Fetch Value at Risk data.

**Response:**
```json
{
  "success": true,
  "data": [
    { "date": "2024-01-01", "var_95": -15000, "var_99": -22000 },
    ...
  ],
  "timestamp": "2024-07-08T10:30:00Z"
}
```

### Rebalancing

#### GET `/api/rebalancing/schedule`

Fetch rebalancing schedule.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "1",
      "scheduled_date": "2024-07-15",
      "frequency": "quarterly",
      "status": "completed",
      "target_allocation": {
        "india": 30,
        "us": 40,
        "europe": 20,
        "japan": 5,
        "korea": 5
      },
      "actual_allocation": {
        "india": 31,
        "us": 39,
        "europe": 20,
        "japan": 5,
        "korea": 5
      },
      "drift_tolerance": 2
    }
  ],
  "timestamp": "2024-07-08T10:30:00Z"
}
```

#### GET `/api/rebalancing/drift`

Fetch current allocation drift.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "market": "india",
      "target": 30,
      "current": 32.5,
      "drift": 2.5,
      "threshold_exceeded": true
    },
    ...
  ],
  "timestamp": "2024-07-08T10:30:00Z"
}
```

#### POST `/api/rebalancing/{scheduleId}/execute`

Execute a rebalancing operation.

**Path Parameters:**
- `scheduleId`: Schedule ID to execute

**Response:**
```json
{
  "success": true,
  "data": {
    "schedule_id": "1",
    "status": "in-progress",
    "execution_id": "exec-123",
    "trades": 12,
    "estimated_completion": "2024-07-15T14:30:00Z"
  },
  "timestamp": "2024-07-08T10:30:00Z"
}
```

### Markets

#### GET `/api/markets/performance?market=india`

Fetch performance for all or specific markets.

**Query Parameters:**
- `market` (optional): Market code (india, us, europe, japan, korea, uk, brazil, china)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "market": "india",
      "current_value": 375000,
      "gain_loss": 18750,
      "gain_loss_pct": 5.3,
      "ytd_return": 8.5,
      "allocation_pct": 30,
      "top_holdings": [
        {
          "symbol": "RELIANCE",
          "name": "Reliance Industries",
          "shares": 100,
          "current_price": 2750.5,
          "change_pct": 5.2,
          "allocation_pct": 25.3
        }
      ]
    },
    ...
  ],
  "timestamp": "2024-07-08T10:30:00Z"
}
```

#### GET `/api/markets/{market}/details`

Fetch detailed information for a specific market.

**Path Parameters:**
- `market`: Market code

**Response:**
```json
{
  "success": true,
  "data": {
    "market": "india",
    "total_value": 375000,
    "holding_count": 45,
    "top_10_concentration": 45.3,
    "volatility": 14.2,
    "sharpe_ratio": 1.25,
    "sector_breakdown": {
      "Technology": 25,
      "Finance": 20,
      "Energy": 15,
      ...
    }
  },
  "timestamp": "2024-07-08T10:30:00Z"
}
```

#### GET `/api/markets/{market}/holdings?limit=10`

Fetch top holdings for a market.

**Path Parameters:**
- `market`: Market code

**Query Parameters:**
- `limit` (optional): Number of holdings to return (default: 10)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "RELIANCE",
      "name": "Reliance Industries",
      "shares": 100,
      "current_price": 2750.5,
      "change_pct": 5.2,
      "allocation_pct": 25.3
    },
    ...
  ],
  "timestamp": "2024-07-08T10:30:00Z"
}
```

### KPIs

#### GET `/api/kpis/scorecard`

Fetch KPI scorecard.

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-07-08T10:30:00Z",
    "health_score": 78,
    "alerts_count": 3,
    "kpis": [
      {
        "id": "1",
        "name": "Portfolio Value",
        "value": 1250000,
        "unit": "$",
        "target": 1300000,
        "change_pct": 5.2,
        "trend": "up",
        "sparkline": [1000, 1050, 1100, 1120, 1180, 1250],
        "alert": null
      },
      ...
    ]
  },
  "timestamp": "2024-07-08T10:30:00Z"
}
```

#### GET `/api/kpis/{kpiId}/history?days=30`

Fetch KPI history.

**Path Parameters:**
- `kpiId`: KPI identifier

**Query Parameters:**
- `days` (optional): Number of days back (default: 30)

**Response:**
```json
{
  "success": true,
  "data": [
    { "date": "2024-06-08", "value": 1000000 },
    { "date": "2024-06-09", "value": 1020000 },
    ...
  ],
  "timestamp": "2024-07-08T10:30:00Z"
}
```

### Portfolio

#### GET `/api/portfolio/summary`

Fetch portfolio summary.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_value": 1250000,
    "total_cost": 1100000,
    "total_gain": 150000,
    "total_gain_pct": 13.6,
    "holding_count": 128,
    "by_market": {
      "india": 30,
      "us": 40,
      "europe": 20,
      "japan": 5,
      "korea": 5
    }
  },
  "timestamp": "2024-07-08T10:30:00Z"
}
```

#### GET `/api/portfolio/positions`

Fetch all portfolio positions.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "RELIANCE",
      "market": "india",
      "shares": 100,
      "cost_basis": 2500,
      "current_price": 2750.5,
      "allocation": 25.3
    },
    ...
  ],
  "timestamp": "2024-07-08T10:30:00Z"
}
```

### Alerts

#### GET `/api/alerts?limit=10`

Fetch alerts.

**Query Parameters:**
- `limit` (optional): Number of alerts to return (default: 10)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "alert-1",
      "type": "allocation_drift",
      "severity": "warning",
      "message": "India allocation exceeded threshold by 2.5pp",
      "action_required": true,
      "timestamp": "2024-07-08T10:15:00Z"
    },
    ...
  ],
  "timestamp": "2024-07-08T10:30:00Z"
}
```

#### POST `/api/alerts/{alertId}/dismiss`

Dismiss an alert.

**Path Parameters:**
- `alertId`: Alert ID to dismiss

**Response:**
```json
{
  "success": true,
  "data": { "dismissed_at": "2024-07-08T10:30:00Z" },
  "timestamp": "2024-07-08T10:30:00Z"
}
```

### Health

#### GET `/api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-07-08T10:30:00Z",
  "version": "1.0.0"
}
```

## WebSocket

### Connection

```
ws://localhost:8000/ws
```

### Message Format

All messages use this format:

```json
{
  "type": "message_type",
  "data": { /* message payload */ },
  "timestamp": "2024-07-08T10:30:00Z"
}
```

### Client Messages

#### Subscribe
```json
{
  "type": "subscribe",
  "data": {
    "market": "india",
    "symbols": ["RELIANCE", "TCS", "INFY"]
  }
}
```

#### Unsubscribe
```json
{
  "type": "unsubscribe",
  "data": {
    "market": "india",
    "symbols": ["RELIANCE"]
  }
}
```

#### Ping
```json
{
  "type": "ping",
  "data": { "timestamp": "2024-07-08T10:30:00Z" }
}
```

### Server Messages

#### Price Update
```json
{
  "type": "price_update",
  "data": {
    "symbol": "RELIANCE",
    "market": "india",
    "price": 2750.5,
    "change_pct": 1.2,
    "volume": 1500000,
    "timestamp": "2024-07-08T10:30:00Z"
  }
}
```

#### KPI Update
```json
{
  "type": "kpi_update",
  "data": {
    "kpi_id": "1",
    "name": "Portfolio Value",
    "value": 1250000,
    "change_pct": 5.2,
    "timestamp": "2024-07-08T10:30:00Z"
  }
}
```

#### Alert
```json
{
  "type": "alert",
  "data": {
    "id": "alert-1",
    "type": "allocation_drift",
    "severity": "warning",
    "message": "India allocation exceeded threshold",
    "timestamp": "2024-07-08T10:30:00Z"
  }
}
```

#### Rebalance Status
```json
{
  "type": "rebalance_status",
  "data": {
    "schedule_id": "1",
    "status": "in-progress",
    "progress": 45,
    "trades_executed": 6,
    "total_trades": 12,
    "timestamp": "2024-07-08T10:30:00Z"
  }
}
```

#### Market Data
```json
{
  "type": "market_data",
  "data": {
    "market": "india",
    "current_value": 375000,
    "gain_loss_pct": 5.3,
    "timestamp": "2024-07-08T10:30:00Z"
  }
}
```

## Error Handling

### HTTP Errors

```json
{
  "success": false,
  "error": "Not found",
  "timestamp": "2024-07-08T10:30:00Z"
}
```

HTTP Status Codes:
- `200` - OK
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

### WebSocket Errors

```json
{
  "type": "error",
  "data": {
    "code": "SUBSCRIPTION_FAILED",
    "message": "Invalid market code"
  }
}
```

## Rate Limiting

Recommended rate limits:
- API calls: 100/minute per endpoint
- WebSocket: 1000 messages/minute
- Historical data: 1GB/day

## Versioning

Current API version: `v1`

To support versioning, prefix endpoints:
```
/api/v1/performance/metrics
/api/v1/risk/metrics
...
```

## Mock Data for Development

Use the included mock data in dashboard components for development without a backend:

```tsx
const mockPerformanceData = [
  { date: '2024-01', value: 100 },
  { date: '2024-02', value: 105 },
  ...
]
```

## Testing Endpoints

### cURL Examples

```bash
# Get performance metrics
curl http://localhost:8000/api/performance/metrics

# Get risk metrics
curl http://localhost:8000/api/risk/metrics

# Get market performance
curl http://localhost:8000/api/markets/performance

# WebSocket test (requires wscat)
wscat -c ws://localhost:8000/ws
```

## Backend Implementation Notes

Implement these endpoints in your backend to fully integrate with the dashboard:

1. Use timestamps consistently (ISO 8601)
2. Return proper HTTP status codes
3. Include `success` field in all responses
4. Implement WebSocket authentication if needed
5. Consider caching frequently accessed data
6. Add request validation and sanitization
7. Implement proper error logging
8. Add rate limiting for production

---

For frontend implementation details, see `src/services/api.ts` and `src/services/websocket.ts`.
