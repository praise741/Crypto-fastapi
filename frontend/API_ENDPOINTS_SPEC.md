# Frontend API Endpoints Specification

This document details all API endpoints consumed by the frontend, including expected request/response structures for backend verification.

**Base URL:** `{API_BASE_URL}/api/v1`  
**Default Production URL:** `https://api.102-212-247-217.sslip.io`

---

## 1. Health Endpoints

### GET `/health`
**Used in:** `api-client.ts`  
**Purpose:** Check API health status

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy|degraded",
    "services": {
      "database": "healthy|degraded",
      "redis": "healthy|degraded",
      "coingecko": "healthy|degraded",
      "binance": "healthy|degraded",
      "dexscreener": "healthy|degraded"
    }
  },
  "meta": {
    "timestamp": "ISO8601",
    "version": "string"
  }
}
```

### GET `/health/detailed`
**Used in:** `api-client.ts`  
**Purpose:** Get detailed health status

---

## 2. Market Data Endpoints

### GET `/market/prices`
**Used in:** `analytics/page.tsx`, `dashboard/page.tsx`  
**Purpose:** Get current prices for all supported cryptocurrencies

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "prices": [
      {
        "symbol": "BTC",
        "price": 124957.0,
        "change_24h": 2.5,
        "volume_24h": 60922010248.97,
        "timestamp": "ISO8601"
      }
    ]
  },
  "meta": {
    "timestamp": "ISO8601",
    "version": "string"
  }
}
```

### GET `/market/trending`
**Used in:** `page.tsx` (Home page)  
**Purpose:** Get trending tokens

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "trending_tokens": [
      {
        "symbol": "string",
        "price": 0.0,
        "change_24h": 0.0,
        "volume_24h": 0.0,
        "trend_score": 0.0,
        "timestamp": "ISO8601"
      }
    ]
  }
}
```

### GET `/market/{symbol}/price`
**Used in:** `api-client.ts`  
**Purpose:** Get current price for a specific cryptocurrency

**Path Parameters:**
- `symbol`: Cryptocurrency symbol (BTC, ETH, SOL, BNB, ADA, XRP)

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC",
    "price": 124957.0,
    "change_24h": 2.5,
    "volume_24h": 60922010248.97,
    "timestamp": "ISO8601"
  }
}
```

### GET `/market/{symbol}/ticker`
**Used in:** `api-client.ts`  
**Purpose:** Get ticker data for a symbol

### GET `/market/{symbol}/ohlcv`
**Used in:** `api-client.ts`  
**Purpose:** Get OHLCV candlestick data

**Query Parameters:**
- `interval`: Time interval (1h, 4h, 1d)
- `start_time`: Optional start time
- `end_time`: Optional end time
- `limit`: Number of candles (default: 100)

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC",
    "interval": "1h",
    "candles": [
      {
        "timestamp": "ISO8601",
        "open": 124500.0,
        "high": 125000.0,
        "low": 124200.0,
        "close": 124800.0,
        "volume": 1000000.0
      }
    ]
  }
}
```

### GET `/market/{symbol}/indicators`
**Used in:** `api-client.ts`  
**Purpose:** Get technical indicators

**Query Parameters:**
- `set`: Indicator set
- `period`: Period
- `interval`: Time interval

### GET `/market/{symbol}/depth`
**Used in:** `api-client.ts`  
**Purpose:** Get market depth/order book

### GET `/market/{symbol}/trades`
**Used in:** `api-client.ts`  
**Purpose:** Get recent trades

**Query Parameters:**
- `limit`: Number of trades (default: 50)

---

## 3. Prediction Endpoints

### GET `/predictions/{symbol}`
**Used in:** `predictions/page.tsx`  
**Purpose:** Get AI predictions for a symbol

**Path Parameters:**
- `symbol`: Cryptocurrency symbol

**Query Parameters:**
- `horizons`: Comma-separated horizons (e.g., "1h,4h,24h,7d")
- `include_confidence`: boolean
- `include_factors`: boolean

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC",
    "current_price": 125000.0,
    "predictions": [
      {
        "horizon": "24h",
        "predicted_price": 127000.0,
        "confidence_interval": {
          "lower": 124000.0,
          "upper": 130000.0,
          "confidence": 0.85
        },
        "probability": {
          "up": 0.65,
          "down": 0.35
        },
        "factors": [
          {
            "name": "momentum",
            "impact": 0.35
          }
        ],
        "model_version": "v2.0",
        "generated_at": "ISO8601"
      }
    ]
  }
}
```

### POST `/predictions/by-contract`
**Used in:** `predictions/page.tsx`  
**Purpose:** Get predictions by contract address

**Request Body:**
```json
{
  "contract_address": "0x...",
  "chain_id": 1,
  "horizons": "1h,4h,24h,7d",
  "include_confidence": true,
  "include_factors": true
}
```

**Expected Response:** Same as GET `/predictions/{symbol}`

### POST `/predictions/batch`
**Used in:** `api-client.ts`  
**Purpose:** Get batch predictions for multiple symbols

**Request Body:**
```json
{
  "symbols": ["BTC", "ETH", "SOL"],
  "horizons": ["24h", "7d"]
}
```

### GET `/predictions/{symbol}/history`
**Used in:** `api-client.ts`  
**Purpose:** Get prediction history

**Query Parameters:**
- `start_date`: Start date
- `end_date`: End date

---

## 4. Contract Endpoints

### GET `/contracts/{contractAddress}`
**Used in:** `predictions/page.tsx`  
**Purpose:** Get contract/token data by address

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "token": {
      "symbol": "TOKEN"
    },
    "pricing": {
      "price_usd": 0.001234
    }
  }
}
```

### GET `/contracts/{contractAddress}/pairs`
**Used in:** `api-client.ts`  
**Purpose:** Get trading pairs for a contract

---

## 5. Token Analytics Endpoints

### POST `/token-analytics/analyze`
**Used in:** `token-health/page.tsx`  
**Purpose:** Analyze token by contract address

**Request Body:**
```json
{
  "contract_address": "0x...",
  "chain_id": "1"  // Optional - auto-detected
}
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "contract_address": "0x...",
    "symbol": "TOKEN",
    "name": "Token Name",
    "chain_id": "1",
    "chain_name": "Ethereum",
    "price_usd": 0.001234,
    "liquidity_usd": 500000.0,
    "volume_24h": 100000.0,
    "market_cap": 10000000.0,
    "holders_count": 5000,
    "contract_verified": true,
    "renounced_ownership": false,
    "mintable": false,
    "blacklist_function": false,
    "hidden_taxes": false,
    "honeypot_risk": false,
    "pump_dump_risk": 15.5,
    "buy_tax": 0.05,
    "sell_tax": 0.05,
    "transfer_tax": 0.0,
    "liquidity_locked": true,
    "liquidity_lock_percentage": 80.0,
    "lp_burned": false,
    "buys_24h": 150,
    "sells_24h": 120,
    "total_transactions_24h": 270,
    "overall_security_score": 75,
    "liquidity_score": 80,
    "contract_safety_score": 70,
    "holder_distribution_score": 65,
    "trading_activity_score": 85,
    "risk_level": "low|medium|high|critical",
    "warnings": ["Warning 1", "Warning 2"],
    "strengths": ["Strength 1", "Strength 2"],
    "recommendation": "SAFE TO TRADE|CAUTION|AVOID",
    "created_at": "ISO8601",
    "last_updated": "ISO8601",
    "data_sources": ["goplus", "dexscreener"],
    "tax_source": "goplus|0x|simulated",
    "tax_confidence": "high|low"
  }
}
```

### GET `/token-health/{symbol}`
**Used in:** `api-client.ts`  
**Purpose:** Get token health by symbol

---

## 6. Analytics Endpoints

### GET `/analytics/correlations`
**Used in:** `api-client.ts`  
**Purpose:** Get asset correlations

**Query Parameters:**
- `symbols`: Comma-separated symbols

### GET `/analytics/volatility`
**Used in:** `analytics/page.tsx`  
**Purpose:** Get volatility metrics

**Query Parameters:**
- `symbol`: Optional specific symbol

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "symbol": "BTC",
        "volatility": 0.0032,
        "window_hours": 24
      }
    ]
  }
}
```

### GET `/analytics/trends`
**Used in:** `analytics/page.tsx`  
**Purpose:** Get market trends

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "signals": [
      {
        "symbol": "BTC",
        "trend": "bullish|bearish|neutral",
        "score": 2.5,
        "updated_at": "ISO8601"
      }
    ]
  }
}
```

### GET `/analytics/top-performers`
**Used in:** `analytics/page.tsx`  
**Purpose:** Get top performing assets

**Query Parameters:**
- `limit`: Number of results (default: 10)

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "assets": [
      {
        "symbol": "SOL",
        "return_percent": 5.2,
        "current_price": 234.62,
        "change_24h": 0.49,
        "volume_24h": 7443261926.51,
        "performance_score": 92.1,
        "category": "gainer|loser",
        "period": "72h"
      }
    ]
  }
}
```

---

## 7. Indices Endpoints

### GET `/indices`
**Used in:** `api-client.ts`  
**Purpose:** Get all market indices

### GET `/indices/fear-greed`
**Used in:** `api-client.ts`  
**Purpose:** Get Fear & Greed index

### GET `/indices/altseason`
**Used in:** `api-client.ts`  
**Purpose:** Get Altseason index

### GET `/indices/dominance`
**Used in:** `api-client.ts`  
**Purpose:** Get BTC dominance data

---

## 8. Dashboard Endpoints

### GET `/dashboard`
**Used in:** `dashboard/page.tsx`  
**Purpose:** Get dashboard overview

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "metrics": {
      "total_market_cap": 2500000000000,
      "total_volume_24h": 171600000000,
      "btc_dominance": 56.85,
      "fear_greed_index": 65
    },
    "predictions": [
      {
        "symbol": "BTC",
        "current_price": 125000.0,
        "predicted_price": 127000.0,
        "horizon": "24h",
        "confidence": 0.85,
        "direction": "up|down"
      }
    ]
  }
}
```

### GET `/dashboard/metrics`
**Used in:** `analytics/page.tsx`  
**Purpose:** Get dashboard metrics

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "total_market_cap": 2500000000000,
    "total_volume_24h": 171600000000,
    "btc_dominance": 56.85,
    "fear_greed_index": 65
  }
}
```

---

## 9. Portfolio Endpoints

### POST `/portfolio/upload`
**Used in:** `portfolio/page.tsx`  
**Purpose:** Upload portfolio CSV file

**Request:** `multipart/form-data` with file

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "message": "Portfolio uploaded successfully",
    "holdings_count": 5
  }
}
```

### GET `/portfolio/holdings`
**Used in:** `portfolio/page.tsx`  
**Purpose:** Get portfolio holdings

**Expected Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "BTC",
      "amount": 0.5,
      "avg_buy_price": 45000.0,
      "current_price": 125000.0,
      "value": 62500.0,
      "profit_loss": 40000.0,
      "profit_loss_percentage": 177.78
    }
  ]
}
```

### GET `/portfolio/performance`
**Used in:** `portfolio/page.tsx`  
**Purpose:** Get portfolio performance

**Query Parameters:**
- `window`: Time window (default: "30d")

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "total_value": 100000.0,
    "total_invested": 60000.0,
    "total_profit_loss": 40000.0,
    "total_profit_loss_percentage": 66.67,
    "best_performer": "BTC",
    "worst_performer": "ADA",
    "daily_change": 2.5,
    "weekly_change": 8.3,
    "monthly_change": 15.2
  }
}
```

### GET `/portfolio/allocation`
**Used in:** `portfolio/page.tsx`  
**Purpose:** Get portfolio allocation

**Expected Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "BTC",
      "percentage": 60.5,
      "value": 62500.0
    }
  ]
}
```

---

## 10. Insights Endpoints

### GET `/insights/summary`
**Used in:** `api-client.ts`  
**Purpose:** Get insights summary

**Query Parameters:**
- `symbol`: Symbol to get insights for
- `window`: Time window (default: "24h")

### GET `/insights/events`
**Used in:** `api-client.ts`  
**Purpose:** Get insight events

**Query Parameters:**
- `symbol`: Symbol
- `limit`: Number of events (default: 10)

---

## 11. News Endpoints

### GET `/news`
**Used in:** `news/page.tsx`  
**Purpose:** Get crypto news articles

**Query Parameters:**
- `symbol`: Optional symbol filter
- `limit`: Number of articles (default: 50)

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "articles": [
      {
        "id": "unique-id",
        "title": "Article Title",
        "summary": "Article summary...",
        "url": "https://...",
        "source": "CryptoNews",
        "published_at": "ISO8601",
        "sentiment": "positive|negative|neutral",
        "symbols": ["BTC", "ETH"],
        "category": "Market|Technology|Regulation|DeFi"
      }
    ]
  }
}
```

**Alternative Response Structure:**
```json
{
  "success": true,
  "data": {
    "news": [...]  // Same structure as articles
  }
}
```

---

## 12. Alerts Endpoints

### GET `/alerts`
**Used in:** `api-client.ts`  
**Purpose:** Get user alerts

### POST `/alerts`
**Used in:** `api-client.ts`  
**Purpose:** Create a new alert

**Request Body:**
```json
{
  "symbol": "BTC",
  "condition": "above|below",
  "price": 130000.0,
  "notification_method": "email|push"
}
```

### PUT `/alerts/{id}`
**Used in:** `api-client.ts`  
**Purpose:** Update an alert

### DELETE `/alerts/{id}`
**Used in:** `api-client.ts`  
**Purpose:** Delete an alert

---

## 13. Auth Endpoints

### POST `/auth/login`
**Used in:** `api-client.ts`  
**Purpose:** User login

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "jwt-token",
    "refresh_token": "refresh-token",
    "user": {
      "id": "user-id",
      "email": "user@example.com"
    }
  }
}
```

### POST `/auth/register`
**Used in:** `api-client.ts`  
**Purpose:** User registration

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### POST `/auth/refresh`
**Used in:** `api-client.ts`  
**Purpose:** Refresh access token

**Request Body:**
```json
{
  "refresh_token": "refresh-token"
}
```

### GET `/auth/me`
**Used in:** `api-client.ts`  
**Purpose:** Get current user info

---

## 14. WebSocket Endpoint

### WS `/ws/market`
**Used in:** `websocket.ts`  
**Purpose:** Real-time market data streaming

**Connection URL:** `ws[s]://{API_HOST}/api/v1/ws/market`

**Subscribe Message:**
```json
{
  "action": "subscribe",
  "channels": ["price:BTC", "price:ETH", "trades:BTC"]
}
```

**Unsubscribe Message:**
```json
{
  "action": "unsubscribe",
  "channels": ["price:BTC"]
}
```

**Incoming Message Format:**
```json
{
  "type": "price|trade|depth",
  "symbol": "BTC",
  "data": { ... }
}
```

---

## Response Format Notes

All API responses follow this standard format:

```json
{
  "success": true|false,
  "data": { ... },
  "meta": {
    "timestamp": "ISO8601",
    "version": "string"
  },
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description"
  }
}
```

## Error Response Format

```json
{
  "success": false,
  "error": {
    "message": "Error description"
  }
}
```

Or with detail field:
```json
{
  "detail": "Error description"
}
```

---

## Headers

**Required Headers:**
- `Content-Type: application/json`

**Auth Headers (for protected routes):**
- `Authorization: Bearer {access_token}`

---

## CORS Configuration Expected

```json
{
  "allowed_origins": ["http://127.0.0.1:3002", "http://localhost:3002"],
  "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
  "allowed_headers": ["Content-Type", "Authorization", "X-Requested-With"],
  "credentials": true
}
```
