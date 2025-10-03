# Market Matrix - Complete Solution Documentation

## Overview

Market Matrix is a comprehensive crypto intelligence platform that solves three critical problems facing crypto investors:

1. **🔹 Overwhelming Information** - Filters noise and delivers clear, data-backed insights
2. **🔹 Uncertainty in Entry & Exit** - Provides timely predictions on when to invest and exit
3. **🔹 Falling into Scams & Weak Projects** - Exposes unhealthy tokens before they drain your wallet

---

## Problem #1: Overwhelming Information

### Solution: Multi-Source Intelligence Filtering

#### **Insights API** (`/api/v1/insights`)

Aggregates and filters market signals from multiple sources:

- **Proxy Score**: Real-time buy/sell ratio and volume momentum from DEX data
- **Sentiment Analysis**: Reddit posts analyzed with VADER sentiment scoring
- **Transaction Velocity**: 1-hour transaction rate to detect sudden activity

**Endpoints:**

```bash
# Get summarized insights for a token
GET /api/v1/insights/summary?symbol=BTC&window=24h

# Get raw insight events
GET /api/v1/insights/events?symbol=BTC&limit=50
```

**Response Example:**
```json
{
  "symbol": "BTC",
  "window": "24h",
  "proxy_score": 0.65,
  "reddit_score": 0.42,
  "score_avg": 0.54,
  "counts_by_source": {
    "PROXY": 12,
    "REDDIT": 45
  },
  "components": [
    {"name": "buy_sell_ratio", "value": 0.35},
    {"name": "vol_change_24h", "value": 0.18},
    {"name": "tx_velocity", "value": 142.0}
  ]
}
```

#### **Analytics API** (`/api/v1/analytics`)

Advanced market analysis to cut through noise:

**Endpoints:**

```bash
# Asset correlations
GET /api/v1/analytics/correlations

# Volatility metrics
GET /api/v1/analytics/volatility

# Trend signals (bullish/bearish/sideways)
GET /api/v1/analytics/trends

# Pattern detection (breakout, breakdown, consolidation, etc.)
GET /api/v1/analytics/patterns

# Top performers
GET /api/v1/analytics/top-performers

# Momentum leaders
GET /api/v1/analytics/momentum
```

**Key Features:**
- Correlation matrix to understand market movements
- Volatility scoring for risk assessment
- Pattern recognition (breakout, consolidation, mean reversion)
- Momentum classification (strong, moderate, weak, neutral)

---

## Problem #2: Uncertainty in Entry & Exit

### Solution: AI-Powered Predictions + Smart Alerts

#### **Predictions API** (`/api/v1/predictions`)

Uses Prophet ML model for price forecasting across multiple time horizons:

**Endpoints:**

```bash
# Get predictions for multiple horizons
GET /api/v1/predictions?symbol=BTC&horizon=1h&horizon=24h&horizon=7d&include_confidence=true&include_factors=true

# Get specific symbol predictions
GET /api/v1/predictions/BTC?horizons=4h,24h

# Batch predictions
POST /api/v1/predictions/batch
Body: {
  "symbols": ["BTC", "ETH", "SOL"],
  "horizons": ["1h", "24h"]
}

# Historical prediction accuracy
GET /api/v1/predictions/BTC/history?include_accuracy=true
```

**Response Example:**
```json
{
  "symbol": "BTC",
  "current_price": 45000.00,
  "predictions": [
    {
      "horizon": "24h",
      "predicted_price": 46500.00,
      "confidence_interval": {
        "lower": 45800.00,
        "upper": 47200.00,
        "confidence": 0.95
      },
      "probability": {
        "up": 0.65,
        "down": 0.35
      },
      "factors": [
        {"name": "momentum", "impact": 0.35},
        {"name": "volume", "impact": 0.25},
        {"name": "market_sentiment", "impact": 0.20}
      ],
      "model_version": "prophet-1.1.5",
      "generated_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

**Features:**
- Multiple time horizons: 1h, 4h, 24h, 7d
- Confidence intervals (95% confidence)
- Probability scoring (up/down likelihood)
- Factor importance breakdown
- Historical accuracy tracking

#### **Alerts API** (`/api/v1/alerts`)

Automated notifications for optimal entry/exit timing:

**Endpoints:**

```bash
# List user alerts
GET /api/v1/alerts

# Create alert
POST /api/v1/alerts
Body: {
  "type": "price_cross",
  "symbol": "BTC",
  "condition": {
    "operator": "greater_than",
    "value": 50000
  },
  "notification": {
    "channels": ["email", "webhook"],
    "message_template": "BTC crossed above $50,000"
  },
  "active": true
}

# Update alert
PUT /api/v1/alerts/{alert_id}

# Delete alert
DELETE /api/v1/alerts/{alert_id}

# Get notifications
GET /api/v1/notifications
```

**Alert Types:**
- Price thresholds (cross above/below)
- Percentage changes (1h, 24h, 7d)
- Prediction confidence triggers
- Pattern detection alerts

---

## Problem #3: Falling into Scams & Weak Projects

### Solution: Comprehensive Token Health Scoring

#### **Token Health API** (`/api/v1/token-health`) ⭐ NEW

Multi-factor risk assessment system to detect scams before you invest:

**Endpoints:**

```bash
# Get comprehensive health score
GET /api/v1/token-health/BTC

# Quick health check
GET /api/v1/token-health/BTC/quick

# Compare multiple tokens
POST /api/v1/token-health/compare
Body: ["BTC", "ETH", "SHIB", "SCAMTOKEN"]
```

**Health Score Components:**

| Component | Weight | Purpose |
|-----------|--------|---------|
| **Liquidity** | 30% | Prevents rug pulls - measures available trading liquidity |
| **Trading Volume** | 25% | Market interest and activity level |
| **Price Volatility** | 20% | Stability indicator - lower is better |
| **Holder Distribution** | 15% | Whale concentration risk |
| **Token Age** | 10% | Establishment and maturity |

**Scoring Thresholds:**

**Liquidity:**
- $1M+ = 100 (Excellent)
- $500K+ = 85 (Good)
- $100K+ = 70 (Moderate)
- $10K+ = 40 (Poor)
- <$10K = 10 (Critical) ⚠️

**Volume (24h):**
- $10M+ = 100
- $1M+ = 75
- $100K+ = 45
- <$10K = 15 ⚠️

**Age:**
- 1+ year = 100
- 90+ days = 70
- 7+ days = 40
- <24 hours = 10 ⚠️ EXTREME RISK

**Response Example:**
```json
{
  "symbol": "SCAMTOKEN",
  "overall_score": 22.5,
  "health_level": "critical",
  "components": {
    "liquidity": 10.0,
    "volume": 15.0,
    "holder_distribution": 20.0,
    "volatility": 10.0,
    "age": 10.0
  },
  "red_flags": [
    "Very low liquidity - high rug pull risk",
    "Extremely low trading activity",
    "Token less than 24 hours old - extreme risk",
    "Extreme price volatility: 245.3% swing in 24h"
  ],
  "recommendation": "AVOID - Multiple red flags detected. High scam risk.",
  "analyzed_at": "2024-01-15T10:00:00Z"
}
```

**Health Levels:**
- **Excellent** (80+): Strong fundamentals, low risk
- **Good** (65-79): Decent fundamentals, moderate risk
- **Moderate** (50-64): Exercise caution
- **Poor** (35-49): High risk, experienced traders only
- **Critical** (<35): Extreme risk, likely scam ⚠️

**Red Flag Detection:**
- Low liquidity (<$10K) = Rug pull risk
- Low trading activity (<10 txns/24h)
- Heavy selling pressure (>80% sells)
- Extreme volatility (>100% swing/24h)
- Very new tokens (<24h old)

---

## Integration Guide

### Quick Start

```bash
# 1. Get current price and prediction
GET /api/v1/predictions/BTC?horizon=24h

# 2. Check token health before investing
GET /api/v1/token-health/BTC

# 3. Get filtered market insights
GET /api/v1/insights/summary?symbol=BTC

# 4. Set alert for exit signal
POST /api/v1/alerts
Body: {
  "type": "prediction_confidence",
  "symbol": "BTC",
  "condition": { "threshold": 0.85, "direction": "down" }
}
```

### Use Cases

**1. Pre-Investment Due Diligence:**
```bash
# Step 1: Check token health
GET /api/v1/token-health/NEWTOKEN

# Step 2: Review insights sentiment
GET /api/v1/insights/summary?symbol=NEWTOKEN

# Step 3: Check price predictions
GET /api/v1/predictions/NEWTOKEN?horizon=24h&horizon=7d

# Decision: Invest only if:
# - Health score > 60
# - No critical red flags
# - Prediction trend is positive
# - Sentiment is neutral to positive
```

**2. Portfolio Monitoring:**
```bash
# Compare all holdings
POST /api/v1/token-health/compare
Body: ["BTC", "ETH", "SOL", "MATIC"]

# Monitor predictions
POST /api/v1/predictions/batch
Body: {"symbols": ["BTC", "ETH", "SOL"], "horizons": ["4h", "24h"]}

# Track momentum
GET /api/v1/analytics/momentum
```

**3. Exit Strategy:**
```bash
# Set trailing stop alert
POST /api/v1/alerts
Body: {
  "type": "percentage_change",
  "symbol": "BTC",
  "condition": { "change": -10, "window": "24h" }
}

# Monitor prediction confidence
GET /api/v1/predictions/BTC/history?include_accuracy=true

# Watch for bearish signals
GET /api/v1/analytics/trends
GET /api/v1/analytics/patterns
```

---

## API Rate Limits

```yaml
Free Tier:
  - Predictions: 60 requests/minute
  - Token Health: 100 requests/minute
  - Insights: 60 requests/minute
  - Analytics: 100 requests/minute
  - Alerts: 30 requests/minute
```

---

## WebSocket Feeds

Real-time updates for predictions and market data:

```javascript
// Connect
const ws = new WebSocket('wss://api.marketmatrix.com/api/v1/ws/predictions');

// Subscribe
ws.send(JSON.stringify({
  action: "subscribe",
  symbols: ["BTC", "ETH"]
}));

// Receive updates
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // update.type: "prediction_update" | "price_update"
  // update.symbol: "BTC"
  // update.data: { ... }
};
```

---

## Authentication

All endpoints require Bearer token authentication:

```bash
# Login
POST /api/v1/auth/login
Body: {"email": "user@example.com", "password": "secure_pass"}

# Use token
curl -H "Authorization: Bearer <access_token>" \
  https://api.marketmatrix.com/api/v1/token-health/BTC
```

---

## Error Handling

Standard error response format:

```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_DATA",
    "message": "Not enough market data to generate health score",
    "details": {
      "symbol": "NEWTOKEN",
      "data_points": 5,
      "required": 24
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:00:00Z",
    "request_id": "uuid"
  }
}
```

---

## Conclusion

Market Matrix provides a complete solution:

✅ **Problem #1 Solved**: Insights + Analytics APIs filter overwhelming information  
✅ **Problem #2 Solved**: Predictions + Alerts APIs guide entry/exit timing  
✅ **Problem #3 Solved**: Token Health API detects scams before you invest  

**Start building safer, smarter crypto investments today!**
