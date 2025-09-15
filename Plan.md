15# Product Requirements Document: CryptoPrediction API Backend

## 1. Executive Summary

### 1.1 Product Vision
Build a robust, scalable REST API backend for a crypto price prediction platform that provides AI-powered price forecasts, market sentiment analysis, and real-time market data. This API will be consumed by a separate frontend team.

### 1.2 Success Metrics
- **API Performance**: <500ms response time (p95)
- **Prediction Accuracy**: 60%+ for 24h forecasts
- **Uptime**: 99.5% availability
- **Documentation**: 100% OpenAPI coverage
- **Rate Limiting**: Support 10,000 req/min

### 1.3 Development Approach
**API-first development with comprehensive documentation and testing**. Every endpoint must be documented and tested before handoff to frontend team.

---

## 2. Technical Architecture

### 2.1 Core Stack
```yaml
Backend:
  - Framework: FastAPI (Python 3.11+)
  - Database: PostgreSQL 15 with JSON support
  - Cache: Redis 7.0
  - Task Queue: Python RQ (simpler than Celery)
  - API Documentation: OpenAPI 3.0 / Swagger
  
Data & ML:
  - Market Data: CCXT library
  - ML Framework: scikit-learn, Prophet, XGBoost
  - Feature Store: PostgreSQL with scheduled jobs
  - Model Registry: PostgreSQL + S3/local storage
  
Infrastructure:
  - Deployment: Railway or Render (managed hosting)
  - Container: Docker
  - Monitoring: Sentry + Prometheus
  - CI/CD: GitHub Actions
  - API Gateway: Cloudflare (DDoS protection)
```

### 2.2 Project Structure
```
crypto-prediction-api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── market.py
│   │   │   │   ├── predictions.py
│   │   │   │   ├── indices.py
│   │   │   │   ├── alerts.py
│   │   │   │   └── websocket.py
│   │   │   ├── dependencies.py
│   │   │   └── router.py
│   │   └── middleware/
│   │       ├── rate_limit.py
│   │       ├── cors.py
│   │       └── authentication.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── database/
│   │   ├── schemas/       # Pydantic models
│   │   └── ml/
│   ├── services/
│   │   ├── market_data.py
│   │   ├── prediction.py
│   │   ├── indicators.py
│   │   └── alerts.py
│   ├── tasks/
│   │   ├── ingestion.py
│   │   ├── training.py
│   │   └── calculations.py
│   └── main.py
├── ml/
│   ├── models/
│   ├── training/
│   └── evaluation/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/
├── docs/
│   ├── api/
│   └── integration_guide.md
├── scripts/
│   ├── migrate.py
│   └── seed.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 3. API Development Phases

### Phase 1: Core API Infrastructure (Week 1)

#### 3.1.1 Authentication & Authorization Endpoints
```python
# Authentication endpoints with JWT
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password

# Response format
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "plan": "free|pro|enterprise"
  }
}
```

#### 3.1.2 Database Schema
```sql
-- Core tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    plan VARCHAR(20) DEFAULT 'free',
    api_key VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(255),
    requests INT DEFAULT 0,
    window_start TIMESTAMP DEFAULT NOW(),
    plan_limit INT NOT NULL
);

-- Market data tables
CREATE TABLE market_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(20, 8),
    high DECIMAL(20, 8),
    low DECIMAL(20, 8),
    close DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8),
    market_cap DECIMAL(20, 2),
    source VARCHAR(50),
    UNIQUE(symbol, timestamp, source)
);

CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);

-- Predictions table
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    prediction_time TIMESTAMP NOT NULL,
    horizon_hours INT NOT NULL,
    predicted_price DECIMAL(20, 8) NOT NULL,
    confidence_lower DECIMAL(20, 8),
    confidence_upper DECIMAL(20, 8),
    confidence_score DECIMAL(3, 2),
    model_version VARCHAR(50),
    features_used JSONB,
    actual_price DECIMAL(20, 8), -- filled after prediction time passes
    accuracy_score DECIMAL(3, 2) -- calculated post-facto
);

CREATE INDEX idx_predictions_symbol_created ON predictions(symbol, created_at DESC);
```

#### 3.1.3 Health & Monitoring Endpoints
```python
GET /api/v1/health          # Basic health check
GET /api/v1/health/detailed # Detailed system status
GET /api/v1/metrics         # Prometheus metrics
GET /api/v1/status          # Service dependencies status

# Detailed health response
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ml_service": "healthy",
    "data_ingestion": "healthy"
  },
  "metrics": {
    "uptime_seconds": 86400,
    "total_requests": 1000000,
    "active_users": 150
  }
}
```

#### 3.1.4 API Documentation Requirements
```python
# Every endpoint must include:
- OpenAPI/Swagger documentation
- Request/response schemas
- Error response examples
- Rate limiting information
- Authentication requirements
- Example cURL commands

# Documentation endpoint
GET /api/v1/docs        # Swagger UI
GET /api/v1/redoc       # ReDoc UI
GET /api/v1/openapi.json # OpenAPI schema
```

### Phase 2: Market Data API (Week 2)

#### 3.2.1 Market Data Endpoints
```python
# Symbol management
GET  /api/v1/symbols                # List all supported symbols
GET  /api/v1/symbols/{symbol}       # Symbol details and metadata
POST /api/v1/symbols/{symbol}/track # Start tracking a symbol (admin)

# Current market data
GET /api/v1/market/prices           # Current prices for all symbols
GET /api/v1/market/{symbol}/price   # Current price for symbol
GET /api/v1/market/{symbol}/ticker  # 24h ticker data
GET /api/v1/market/{symbol}/depth   # Order book depth

# Historical data
GET /api/v1/market/{symbol}/ohlcv   # OHLCV candles
  Query params:
    - interval: 1m, 5m, 15m, 1h, 4h, 1d
    - start_time: ISO timestamp
    - end_time: ISO timestamp
    - limit: max 1000

GET /api/v1/market/{symbol}/trades  # Recent trades

# Technical indicators
GET /api/v1/market/{symbol}/indicators
  Query params:
    - indicators: rsi,macd,bb,ema,sma (comma-separated)
    - period: number of candles
    - interval: timeframe

# Market statistics
GET /api/v1/market/stats            # Global market statistics
GET /api/v1/market/{symbol}/stats   # Symbol-specific stats
```

#### 3.2.2 WebSocket Endpoints
```python
# WebSocket connections for real-time data
WS /api/v1/ws/market      # Real-time market updates
WS /api/v1/ws/predictions # Real-time prediction updates

# WebSocket message format
{
  "type": "price_update",
  "symbol": "BTC",
  "data": {
    "price": 45000.50,
    "change_24h": 2.5,
    "volume_24h": 1000000000,
    "timestamp": "2024-01-15T10:00:00Z"
  }
}

# Subscription message
{
  "action": "subscribe",
  "channels": ["price:BTC", "price:ETH", "predictions:*"]
}
```

#### 3.2.3 Data Ingestion Tasks
```python
# Background tasks (Python RQ)
- fetch_market_data(symbol: str, source: str)
- fetch_all_symbols()
- calculate_indicators(symbol: str)
- cleanup_old_data(days: int)
- validate_data_integrity()

# Scheduling
- Real-time prices: every 30 seconds
- OHLCV: every 5 minutes
- Technical indicators: every 15 minutes
- Market stats: every hour
```

### Phase 3: ML Predictions API (Week 3)

#### 3.3.1 Prediction Endpoints
```python
# Get predictions
GET /api/v1/predictions/{symbol}
  Query params:
    - horizon: 1h, 4h, 24h, 7d
    - include_confidence: boolean
    - include_factors: boolean

# Response format
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
      "model_version": "v2.1.0",
      "generated_at": "2024-01-15T10:00:00Z"
    }
  ]
}

# Batch predictions
POST /api/v1/predictions/batch
  Body: {
    "symbols": ["BTC", "ETH", "SOL"],
    "horizons": ["1h", "24h"]
  }

# Historical predictions (for accuracy tracking)
GET /api/v1/predictions/{symbol}/history
  Query params:
    - start_date: ISO date
    - end_date: ISO date
    - include_accuracy: boolean
```

#### 3.3.2 Model Information Endpoints
```python
# Model metadata and performance
GET /api/v1/models                    # List all models
GET /api/v1/models/{model_id}         # Model details
GET /api/v1/models/{model_id}/metrics # Model performance metrics

# Response format
{
  "model_id": "prophet_btc_v2",
  "version": "2.1.0",
  "symbol": "BTC",
  "type": "prophet",
  "metrics": {
    "mae": 0.045,
    "mape": 0.032,
    "directional_accuracy": 0.65,
    "last_updated": "2024-01-15T00:00:00Z",
    "training_samples": 10000,
    "validation_period": "30d"
  },
  "features": [
    "price_momentum",
    "volume_patterns",
    "rsi",
    "market_dominance"
  ]
}
```

### Phase 4: Market Indices & Analytics API (Week 4)

#### 3.4.1 Custom Indices Endpoints
```python
# Market indices
GET /api/v1/indices                   # List all indices
GET /api/v1/indices/altseason         # Altseason index
GET /api/v1/indices/fear-greed        # Fear & Greed index
GET /api/v1/indices/dominance         # Market dominance
GET /api/v1/indices/{index_id}/history # Historical index values

# Index response format
{
  "index": "fear_greed",
  "value": 65,
  "classification": "greed",
  "components": {
    "volatility": 70,
    "momentum": 65,
    "volume": 60,
    "social": 65
  },
  "timestamp": "2024-01-15T10:00:00Z",
  "change_24h": 5
}
```

#### 3.4.2 Analytics Endpoints
```python
# Market analytics
GET /api/v1/analytics/correlations    # Asset correlations
GET /api/v1/analytics/volatility      # Volatility metrics
GET /api/v1/analytics/trends          # Trend analysis
GET /api/v1/analytics/patterns        # Pattern detection

# Performance analytics
GET /api/v1/analytics/top-performers  # Best performing assets
GET /api/v1/analytics/momentum        # Momentum leaders
```

### Phase 5: Alerts & Notifications API (Week 5)

#### 3.5.1 Alert Management Endpoints
```python
# CRUD operations for alerts
GET    /api/v1/alerts                 # List user's alerts
POST   /api/v1/alerts                 # Create alert
GET    /api/v1/alerts/{alert_id}      # Get alert details
PUT    /api/v1/alerts/{alert_id}      # Update alert
DELETE /api/v1/alerts/{alert_id}      # Delete alert

# Alert creation body
{
  "type": "price_cross",
  "symbol": "BTC",
  "condition": {
    "operator": "greater_than",
    "value": 50000,
    "check_interval": "1m"
  },
  "notification": {
    "channels": ["email", "webhook"],
    "webhook_url": "https://example.com/webhook",
    "message_template": "BTC crossed above $50,000"
  },
  "active": true
}

# Alert types supported
- price_cross (above/below)
- percentage_change (1h, 24h, 7d)
- prediction_confidence (high confidence predictions)
- pattern_detection (technical patterns)
- index_threshold (fear/greed extremes)
```

#### 3.5.2 Notification History
```python
GET /api/v1/notifications              # User's notifications
POST /api/v1/notifications/mark-read   # Mark as read
GET /api/v1/notifications/stats        # Notification statistics
```

---

## 4. API Contract & Documentation

### 4.1 Standard Response Format
```json
{
  "success": true,
  "data": { },
  "meta": {
    "timestamp": "2024-01-15T10:00:00Z",
    "version": "1.0.0",
    "request_id": "uuid"
  }
}
```

### 4.2 Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_at": "2024-01-15T10:01:00Z"
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:00:00Z",
    "request_id": "uuid"
  }
}
```

### 4.3 Standard Error Codes
```python
# HTTP status codes and error codes
400 - BAD_REQUEST
401 - UNAUTHORIZED
403 - FORBIDDEN
404 - NOT_FOUND
429 - RATE_LIMIT_EXCEEDED
500 - INTERNAL_ERROR
503 - SERVICE_UNAVAILABLE

# Custom error codes
INVALID_SYMBOL
INVALID_TIMEFRAME
INSUFFICIENT_DATA
MODEL_NOT_READY
PREDICTION_FAILED
INVALID_API_KEY
SUBSCRIPTION_REQUIRED
```

### 4.4 Rate Limiting Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248060
X-RateLimit-Reset-After: 60
```

### 4.5 Pagination Format
```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 500,
    "total_pages": 10,
    "has_next": true,
    "has_prev": false
  },
  "links": {
    "first": "/api/v1/endpoint?page=1",
    "last": "/api/v1/endpoint?page=10",
    "next": "/api/v1/endpoint?page=2",
    "prev": null
  }
}
```

---

## 5. API Testing Strategy

### 5.1 Test Categories
```python
tests/
├── unit/              # Individual function tests
│   ├── test_auth.py
│   ├── test_models.py
│   └── test_services.py
├── integration/       # API endpoint tests
│   ├── test_market_endpoints.py
│   ├── test_prediction_endpoints.py
│   └── test_websocket.py
├── load/             # Performance tests
│   ├── test_concurrent_users.py
│   └── test_rate_limiting.py
└── contract/         # API contract tests
    └── test_response_formats.py
```

### 5.2 Testing Requirements
```python
# Minimum coverage requirements
- Unit tests: 90% coverage
- Integration tests: All endpoints
- Load tests: 1000 concurrent users
- Contract tests: All response formats

# Test data management
fixtures/
├── market_data.json
├── predictions.json
├── users.json
└── models/

# Testing tools
- pytest for unit/integration
- locust for load testing
- hypothesis for property testing
- pytest-asyncio for async tests
```

### 5.3 API Testing Checklist
- [ ] All endpoints return correct status codes
- [ ] Response format matches documentation
- [ ] Error responses are consistent
- [ ] Rate limiting works correctly
- [ ] Authentication/authorization enforced
- [ ] Pagination works correctly
- [ ] Filtering and sorting work
- [ ] WebSocket connections stable
- [ ] Database transactions handle failures
- [ ] External API failures handled gracefully

---

## 6. Security & Performance

### 6.1 Security Requirements
```python
# API Security measures
- JWT token authentication
- API key authentication (for programmatic access)
- Rate limiting per user/IP
- Input validation on all endpoints
- SQL injection prevention
- XSS protection
- CORS configuration
- Request signing for webhooks
- Encryption for sensitive data
- Audit logging for all actions
```

### 6.2 Performance Requirements
```yaml
Response times (p95):
  - GET endpoints: < 500ms
  - POST endpoints: < 1000ms
  - WebSocket latency: < 100ms
  - Prediction generation: < 2000ms

Throughput:
  - 10,000 requests/minute
  - 1,000 concurrent WebSocket connections
  - 100 predictions/second

Data ingestion:
  - 100 symbols updated/minute
  - 1M data points/day
```

### 6.3 Caching Strategy
```python
# Cache layers
1. CloudFlare CDN (60s for public data)
2. Redis cache:
   - Market prices: 30 seconds
   - OHLCV data: 5 minutes
   - Predictions: 1 hour
   - User sessions: 24 hours
3. Database query cache: 1 minute

# Cache headers
Cache-Control: public, max-age=60
ETag: "uuid"
Last-Modified: "timestamp"
```

---

## 7. Deployment & DevOps

### 7.1 Environment Variables
```bash
# .env.example
DATABASE_URL=postgresql://user:pass@localhost/cryptoapi
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
COINGECKO_API_KEY=
BINANCE_API_KEY=
ALPHA_VANTAGE_KEY=
SENTRY_DSN=
STRIPE_SECRET_KEY=
WEBHOOK_SECRET=
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 7.2 Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations
RUN python scripts/migrate.py

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.3 CI/CD Pipeline
```yaml
# .github/workflows/api-ci.yml
name: API CI/CD
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose up -d postgres redis
          pytest tests/ --cov=app --cov-report=xml
      - name: Type checking
        run: mypy app/
      - name: Linting
        run: ruff check app/

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          # Deploy to Railway/Render
          # Run database migrations
          # Update API documentation
```

---

## 8. API Integration Guide for Frontend Team

### 8.1 Getting Started
```bash
# Development API URL
https://api-dev.cryptoprediction.com

# Production API URL
https://api.cryptoprediction.com

# API Key Request
POST /api/v1/auth/register
{
  "email": "developer@example.com",
  "password": "secure_password"
}
```

### 8.2 Authentication Flow
```javascript
// 1. Login to get tokens
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { access_token, refresh_token } = await response.json();

// 2. Use access token for requests
const marketData = await fetch('/api/v1/market/BTC/price', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});

// 3. Refresh token when expired
const newTokens = await fetch('/api/v1/auth/refresh', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh_token })
});
```

### 8.3 WebSocket Connection
```javascript
// Connect to WebSocket
const ws = new WebSocket('wss://api.cryptoprediction.com/api/v1/ws/market');

// Authenticate
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: access_token
  }));
};

// Subscribe to channels
ws.send(JSON.stringify({
  action: 'subscribe',
  channels: ['price:BTC', 'predictions:BTC']
}));

// Handle messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### 8.4 Example Requests Collection
```bash
# Postman/Insomnia collection available at:
https://api.cryptoprediction.com/api/v1/docs/postman-collection.json

# OpenAPI specification:
https://api.cryptoprediction.com/api/v1/openapi.json
```

---

## 9. Monitoring & Maintenance

### 9.1 Health Monitoring
```python
# Automated health checks
### 9.2 Alerts Configuration
```yaml
Alert triggers:
  - API error rate > 1%
  - Response time p95 > 1s
  - Database connection pool exhausted
  - Redis memory > 80%
  - Data ingestion failure > 5 minutes
  - Prediction model accuracy < 50%
  - Disk usage > 80%
```

### 9.3 Backup Strategy
```bash
# Database backups
- Full backup: Daily at 02:00 UTC
- Incremental: Every 6 hours
- Retention: 30 days

# Model artifacts
- Backup after each training
- Version control in S3
- Retention: Last 10 versions
```

---

## 10. Launch Checklist

### 10.1 Pre-Launch (API Team)
- [ ] All endpoints implemented and tested
- [ ] OpenAPI documentation complete
- [ ] Postman collection created
- [ ] Rate limiting tested
- [ ] Security audit completed
- [ ] Load testing passed (1000 users)
- [ ] Monitoring dashboards configured
- [ ] Error tracking configured (Sentry)
- [ ] Backup procedures tested
- [ ] SSL certificates configured

### 10.2 Integration Testing (With Frontend Team)
- [ ] API sandbox environment provided
- [ ] Test accounts created
- [ ] WebSocket connections tested
- [ ] CORS configuration verified
- [ ] Rate limits communicated
- [ ] Error handling documented
- [ ] Performance benchmarks shared

### 10.3 Production Launch
- [ ] Production environment deployed
- [ ] DNS configured
- [ ] CDN enabled
- [ ] Monitoring alerts active
- [ ] On-call rotation scheduled
- [ ] Rollback procedure documented
- [ ] API status page live

---

## Appendix A: Quick Start for Development

```bash
# Clone repository
git clone https://github.com/yourorg/crypto-prediction-api
cd crypto-prediction-api

# Setup environment
cp .env.example .env
# Edit .env with your credentials

# Start services
docker-compose up -d

# Run migrations
python scripts/migrate.py

# Seed test data
python scripts/seed.py

# Start development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Access documentation
open http://localhost:8000/api/v1/docs
```

---

## Appendix B: API Versioning Strategy

```python
# Version in URL path
/api/v1/...  # Current version
/api/v2/...  # Future version

# Deprecation policy
- 6 months notice before deprecation
- Deprecation warnings in headers
- Migration guide provided

# Header-based versioning (alternative)
X-API-Version: 1.0
```
