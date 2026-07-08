# Alert System Integration Guide

## Overview

This document provides a complete integration guide for the multi-market alert system designed for the investment analytics platform. The system provides:

- **Real-time alerts** for price breaches, portfolio changes, trading signals
- **Multi-channel routing** (Email, Slack, Push, SMS) with automatic retry/escalation
- **Alert deduplication** to prevent alert fatigue
- **Persistent history tracking** in SQLite with audit trail
- **Configurable rules** via JSON schema (no code changes needed)
- **Frequency capping** and active-hour filtering
- **Escalation policies** for unacknowledged alerts

---

## System Architecture

```
Market Data Input
    ↓
Rule Engine (Evaluation)
    ├─ Check enabled rules
    ├─ Evaluate conditions
    ├─ Dedup check
    └─ Generate AlertContext
    ↓
Alert Engine
    ├─ Generate Alert ID
    ├─ Create AlertRecord
    └─ Route to channels
    ↓
Channel Routers
    ├─ EmailRouter → SMTP/Gmail
    ├─ SlackRouter → Webhooks
    ├─ PushRouter → FCM
    └─ SMSRouter → Twilio
    ↓
History DB (SQLite)
    ├─ alert_history (facts)
    ├─ alert_actions (audit trail)
    ├─ channel_delivery_log (per-channel status)
    └─ alert_dedup (fingerprints)
```

---

## Configuration Files

### Directory Structure

```
~/.alert_system/
├── config.json                  # Main alert configuration
├── rules.json                   # User-defined overrides (optional)
├── templates.json               # Custom templates (optional)
├── alerts.db                    # SQLite history
├── alerts.db-backup             # Daily backup
├── logs/
│   ├── alert_engine.log
│   ├── routing_delivery.log
│   └── errors.log
└── backups/
    └── alerts_YYYY-MM-DD.db     # Daily backups
```

### Primary Config: config.json

See `alert_config_example.json` for a complete working example. Key sections:

```json
{
  "alert_system": {
    "version": "1.0.0",
    "enabled": true,
    "rules": [...],                    # Array of alert rules
    "routing_config": {...},           # Channel configuration
    "alert_templates": {...},          # Message templates
    "alert_history_config": {...},     # Database settings
    "deduplication": {...},            # Dedup strategy
    "escalation_policy": {...},        # Escalation rules
    "monitoring": {...}                # Health checks
  }
}
```

---

## Rule Definition

### Rule Schema

```json
{
  "rule_id": "alert_price_breach_reliance",
  "rule_name": "RELIANCE Price Target - 2950",
  "category": "PRICE_BREACH",
  "enabled": true,
  "severity": "RED",
  "market": "india",
  "ticker": "RELIANCE",
  "conditions": {
    "current_price": {
      "operator": ">=",
      "value": 2950
    }
  },
  "dedupe_window_minutes": 5,
  "routing": ["email", "slack", "push"],
  "channels": {
    "email": {
      "enabled": true,
      "recipients": ["user@example.com"],
      "template": "price_breach"
    },
    "slack": {
      "enabled": true,
      "channel": "#trading-alerts",
      "mentions": ["@channel"]
    }
  },
  "escalation": {
    "enabled": true,
    "if_not_acknowledged": "1h",
    "escalate_to": ["slack", "sms"]
  },
  "active_hours": {
    "enabled": true,
    "tz": "Asia/Kolkata",
    "start": "09:15",
    "end": "15:30",
    "weekdays": [0, 1, 2, 3, 4]
  },
  "frequency_cap": {
    "max_per_day": 10,
    "cooldown_minutes": 5
  }
}
```

### Supported Alert Categories

| Category | Trigger Type | Use Case |
|----------|---|---|
| `PRICE_BREACH` | Price > or < target | Monitor specific price levels |
| `VOLUME_SPIKE` | Vol > 2x moving avg | Unusual trading activity |
| `RSI_EXTREME` | RSI > 80 or < 20 | Overbought/oversold conditions |
| `SCANNER_HIT` | Signal score threshold | Darvas/Piotroski signals |
| `HIGH_52W` | Price within 5% of high | Breakout monitoring |
| `POSITION_LOSS` | Single position loss % | Portfolio risk management |
| `PORTFOLIO_DRAWDOWN` | Portfolio loss % | Portfolio-level alerts |
| `DIVIDEND_EX_DATE` | Ex-date within N days | Corporate actions |
| `HOLDINGS_ALERT` | Delisting/corporate action | Holdings status changes |
| `BROKER_CONNECTION_ERROR` | API connection lost | System health |
| `OPTION_CHAIN_STALE` | Data age > threshold | Data freshness check |
| `PARITY_OPPORTUNITY` | Mispricing > threshold | Arbitrage opportunities |
| `DATA_SYNC_LAG` | DB update lag > threshold | Data pipeline health |
| `TRADE_EXECUTED` | Order filled | Trade confirmations |
| `POSITION_EXPIRY_WARNING` | < 2 DTE with open pos | Derivative management |
| `MARGIN_WARNING` | Margin % > threshold | Risk management |
| `DIGEST` | Scheduled summary | Daily/weekly reports |

### Condition Operators

```json
"conditions": {
  "field_name": {
    "operator": ">=",      // >=, <=, >, <, ==, !=, in_range, contains
    "value": 2950
  }
}
```

---

## Severity Levels

| Level | Response Time | Persistence | Frequency | Use Case |
|-------|---|---|---|---|
| RED | Immediate | 90 days | Max 5min gap | Critical (losses > 10%, broker down) |
| YELLOW | 5-15 min | 30 days | Max 30min gap | Warning (losses > 5%, signals) |
| INFO | Batch (daily) | 7 days | Once/day | Informational (daily digest) |

---

## Channel Configuration

### Email (Gmail/SMTP)

```json
"email": {
  "enabled": true,
  "provider": "gmail",
  "from_address": "trading-alerts@portfolio.local",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "auth": {
    "use_oauth": true,
    "credential_file": "~/.config/gmail_oauth.json"
  },
  "rate_limit": {
    "max_per_hour": 100,
    "max_per_day": 500
  },
  "retry_policy": {
    "max_attempts": 3,
    "backoff_seconds": [5, 30, 300]
  }
}
```

**Setup:**
1. Create Gmail app password (2FA enabled account)
2. Save credentials to `~/.config/gmail_oauth.json`
3. Or use OAuth2: Configure Google Cloud project + OAuth consent screen

### Slack (Webhooks)

```json
"slack": {
  "enabled": true,
  "webhook_urls": {
    "trading-alerts": "https://hooks.slack.com/services/xxx/yyy/zzz",
    "portfolio-monitoring": "https://hooks.slack.com/services/aaa/bbb/ccc"
  },
  "rate_limit": {
    "max_per_hour": 200
  }
}
```

**Setup:**
1. Create Slack workspace and channels
2. Create incoming webhooks for each channel (Slack API → Incoming Webhooks)
3. Add webhook URLs to config
4. Test with: `curl -X POST https://hooks.slack.com/... -d '{"text":"test"}'`

### Push Notifications (FCM)

```json
"push": {
  "enabled": true,
  "provider": "firebase_cloud_messaging",
  "credentials": "~/.config/fcm_service_account.json",
  "rate_limit": {
    "max_per_hour": 300
  }
}
```

**Setup:**
1. Create Firebase project
2. Generate service account key
3. Save to `~/.config/fcm_service_account.json`
4. Register device tokens during app startup

### SMS (Twilio)

```json
"sms": {
  "enabled": false,
  "provider": "twilio",
  "account_sid": "env:TWILIO_ACCOUNT_SID",
  "auth_token": "env:TWILIO_AUTH_TOKEN",
  "from_number": "+1234567890",
  "rate_limit": {
    "max_per_day": 20
  }
}
```

**Setup:**
1. Create Twilio account
2. Get account SID & auth token
3. Set env vars: `export TWILIO_ACCOUNT_SID=...`
4. Verify phone numbers in Twilio console

---

## Integration with FastAPI Backend

### Example Route: Evaluate Market Data

```python
from fastapi import APIRouter, HTTPException
from datetime import datetime
from alert_system_implementation import AlertEngine, AlertContext, AlertSeverity

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
alert_engine = AlertEngine()

@router.post("/evaluate")
async def evaluate_alert(ticker: str, current_price: float, market: str = "india"):
    """Evaluate alert conditions for a ticker"""
    
    # Example: RELIANCE price breach alert
    context = AlertContext(
        rule_id="alert_price_breach_reliance",
        ticker=ticker,
        market=market,
        severity=AlertSeverity.RED,
        category="PRICE_BREACH",
        trigger_value=current_price,
        threshold_value=2950.0,
        condition_met=f"price {current_price} >= threshold 2950.0",
        triggered_at=datetime.utcnow(),
        metadata={"source": "api", "timestamp": datetime.utcnow().isoformat()}
    )
    
    alert_id = alert_engine.evaluate_and_fire(context)
    
    return {
        "alert_id": alert_id,
        "fired": alert_id is not None,
        "ticker": ticker,
        "price": current_price
    }

@router.get("/rules")
async def list_rules(enabled_only: bool = False):
    """List all alert rules"""
    rules = alert_engine.config_manager.get_enabled_rules() if enabled_only else \
            alert_engine.config_manager.config["alert_system"]["rules"]
    return {"rules": rules}

@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, updates: dict):
    """Update alert rule"""
    try:
        alert_engine.config_manager.update_rule(rule_id, updates)
        return {"success": True, "rule_id": rule_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/acknowledge/{alert_id}")
async def acknowledge(alert_id: str, user: str = "system"):
    """Acknowledge alert"""
    alert_engine.acknowledge_alert(alert_id, user)
    return {"alert_id": alert_id, "acknowledged": True}

@router.get("/history")
async def get_history(ticker: str = None, severity: str = None, days: int = 7):
    """Query alert history"""
    alerts = alert_engine.history_db.query_alerts(
        ticker=ticker,
        severity=severity,
        days_back=days
    )
    return {"count": len(alerts), "alerts": alerts}

@router.post("/cleanup")
async def cleanup():
    """Cleanup old alerts"""
    deleted = alert_engine.cleanup()
    return {"deleted": deleted}
```

### Integration with Daily Scanner

```python
# In scanners/daily_scanner.py

from alert_system_implementation import AlertEngine, AlertContext, AlertSeverity
from datetime import datetime

class DailyScanner:
    def __init__(self):
        self.alert_engine = AlertEngine()
    
    def scan_instrument(self, ticker, market, darvas_score, piotroski_score, current_price):
        """Scan single instrument and fire alerts if needed"""
        
        # Alert 1: Darvas BUY signal
        if darvas_score >= 5:
            context = AlertContext(
                rule_id="alert_scanner_hit_darvas",
                ticker=ticker,
                market=market,
                severity=AlertSeverity.INFO,
                category="SCANNER_HIT",
                trigger_value=darvas_score,
                threshold_value=5.0,
                condition_met=f"darvas_score {darvas_score} >= 5",
                triggered_at=datetime.utcnow(),
                metadata={"darvas_score": darvas_score, "piotroski_score": piotroski_score}
            )
            alert_id = self.alert_engine.evaluate_and_fire(context)
        
        # Alert 2: Piotroski BUY signal
        if piotroski_score >= 6:
            context = AlertContext(
                rule_id="alert_scanner_hit_piotroski",
                ticker=ticker,
                market=market,
                severity=AlertSeverity.INFO,
                category="SCANNER_HIT",
                trigger_value=piotroski_score,
                threshold_value=6.0,
                condition_met=f"piotroski_score {piotroski_score} >= 6",
                triggered_at=datetime.utcnow(),
                metadata={"darvas_score": darvas_score, "piotroski_score": piotroski_score}
            )
            alert_id = self.alert_engine.evaluate_and_fire(context)
```

---

## Testing & Validation

### 1. Configuration Validation

```bash
# Validate config JSON against schema
python -c "
import json
from jsonschema import validate

with open('alert_configuration_schema.json') as f:
    schema = json.load(f)

with open('~/.alert_system/config.json') as f:
    config = json.load(f)

validate(instance=config, schema=schema)
print('Config is valid!')
"
```

### 2. Test Rule Firing

```python
from alert_system_implementation import AlertEngine, AlertContext, AlertSeverity
from datetime import datetime

engine = AlertEngine()

# Test price breach alert
context = AlertContext(
    rule_id="alert_price_breach_reliance",
    ticker="RELIANCE",
    market="india",
    severity=AlertSeverity.RED,
    category="PRICE_BREACH",
    trigger_value=2950.50,
    threshold_value=2950.00,
    condition_met="price >= threshold",
    triggered_at=datetime.utcnow(),
    metadata={"test": True}
)

alert_id = engine.evaluate_and_fire(context)
print(f"Alert fired: {alert_id}")
```

### 3. Test Channel Delivery

```bash
# Test email
python -m alert_system_implementation \
  --test-channel email \
  --recipient user@example.com

# Test Slack
python -m alert_system_implementation \
  --test-channel slack \
  --channel "#test-alerts"
```

### 4. Query Alert History

```python
from alert_system_implementation import AlertHistoryDB

db = AlertHistoryDB()

# Get all alerts for RELIANCE in last 7 days
alerts = db.query_alerts(ticker="RELIANCE", severity="RED", days_back=7)
for alert in alerts:
    print(f"{alert['alert_id']} | {alert['triggered_at']} | {alert['delivery_status']}")

# Get unacknowledged RED alerts
alerts = db.query_alerts(severity="RED", acknowledged=False)
print(f"Unacknowledged RED alerts: {len(alerts)}")
```

---

## Production Deployment

### 1. Environment Setup

```bash
# Create alert system directory
mkdir -p ~/.alert_system/logs ~/.alert_system/backups

# Copy config files
cp alert_config_example.json ~/.alert_system/config.json
cp alert_configuration_schema.json ~/.alert_system/schema.json

# Set up Gmail OAuth
# (Follow Gmail API setup guide)
cp gmail_oauth.json ~/.config/gmail_oauth.json

# Set up Slack webhooks
# (Paste webhook URLs into config.json)

# Set env vars for Twilio (if using SMS)
export TWILIO_ACCOUNT_SID="..."
export TWILIO_AUTH_TOKEN="..."
```

### 2. Scheduled Cleanup

Create cron job for daily alert cleanup:

```bash
# Add to crontab -e
0 2 * * * python -c "from alert_system_implementation import AlertEngine; AlertEngine().cleanup()" >> ~/.alert_system/logs/cleanup.log 2>&1
```

### 3. Database Backup

```bash
# Daily backup
0 3 * * * cp ~/.alert_system/alerts.db ~/.alert_system/backups/alerts_$(date +\%Y-\%m-\%d).db
```

### 4. Logging & Monitoring

```python
# Configure logging in FastAPI startup
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('~/.alert_system/logs/alert_engine.log'),
        logging.StreamHandler()
    ]
)
```

### 5. Health Checks

```python
# Periodic health check endpoint
@router.get("/api/alerts/health")
async def health():
    """Alert system health check"""
    try:
        # Check database
        alerts_count = len(alert_engine.history_db.query_alerts(days_back=1))
        
        # Check routing
        routing_status = {
            'email': alert_engine.config_manager.get_routing_config('email')['enabled'],
            'slack': alert_engine.config_manager.get_routing_config('slack')['enabled'],
        }
        
        return {
            "status": "healthy",
            "alerts_24h": alerts_count,
            "routing": routing_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500
```

---

## API Reference

### Alert Management

```
POST   /api/alerts/evaluate           # Evaluate and fire alert
GET    /api/alerts/rules              # List rules
POST   /api/alerts/rules              # Create rule
GET    /api/alerts/rules/{rule_id}    # Get rule
PUT    /api/alerts/rules/{rule_id}    # Update rule
DELETE /api/alerts/rules/{rule_id}    # Delete rule
POST   /api/alerts/rules/{rule_id}/toggle  # Enable/disable

GET    /api/alerts/history            # Query alert history
GET    /api/alerts/history/{alert_id} # Get alert details
POST   /api/alerts/{alert_id}/acknowledge   # Acknowledge
POST   /api/alerts/{alert_id}/dismiss       # Dismiss

GET    /api/alerts/stats              # Statistics
GET    /api/alerts/health             # Health check
POST   /api/alerts/cleanup            # Run cleanup
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Alerts not firing | 1. Check rule `enabled: true`<br>2. Verify conditions syntax<br>3. Check dedup window not blocking<br>4. Verify active_hours (if set) |
| Email not sent | 1. Check Gmail OAuth credentials<br>2. Verify SMTP settings<br>3. Check rate limits<br>4. Check logs for SMTP errors |
| Slack notifications failing | 1. Verify webhook URLs in config<br>2. Test webhook with curl<br>3. Check channel exists<br>4. Verify rate limits |
| High alert volume | 1. Increase dedupe_window_minutes<br>2. Raise threshold values<br>3. Set frequency_cap max_per_day<br>4. Enable active_hours filtering |
| Database growing too large | 1. Run cleanup cron job<br>2. Reduce retention_policy days<br>3. Archive old alerts to backup<br>4. Run `vacuum` on SQLite |

---

## Files Provided

1. **alert_system_spec.md** — Complete system specification
2. **alert_configuration_schema.json** — JSON Schema for validation
3. **alert_system_implementation.py** — Python implementation (AlertEngine, HistoryDB, Routers)
4. **alert_config_example.json** — Complete working example configuration
5. **ALERT_SYSTEM_INTEGRATION_GUIDE.md** — This file

---

## Next Steps

1. **Setup**: Copy example config to `~/.alert_system/config.json`
2. **Configure**: Edit config with your email/Slack/SMS credentials
3. **Test**: Run test alert via `POST /api/alerts/test/{rule_id}`
4. **Integrate**: Call `alert_engine.evaluate_and_fire()` from market data flow
5. **Monitor**: Check `/api/alerts/history` and `/api/alerts/health`
6. **Deploy**: Set up cron jobs for cleanup & backups

---

## Support

For issues or feature requests, refer to:
- Schema validation errors: Check `alert_configuration_schema.json` for valid fields
- Integration issues: See "Integration with FastAPI Backend" section
- Channel setup: Follow provider-specific setup guides above
- Database issues: Run `sqlite3 ~/.alert_system/alerts.db ".schema"` to inspect

