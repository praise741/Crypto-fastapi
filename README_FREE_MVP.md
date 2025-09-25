# Market Matrix – Free Tier Backend

Market Matrix is a FastAPI backend focused on free-only market intelligence. This build delivers:

- Hardened predictions and market data APIs backed by Prophet and public market feeds.
- Portfolio CSV ingestion with valuation, allocation and performance snapshots (flag-gated).
- Community insights powered by on-chain sentiment proxies and optional Reddit/VADER analysis (flag-gated).
- DexScreener-based Web3 health metrics with caching and graceful degradation.
- Observability endpoints (`/health`, `/metrics`) with dependency checks and Prometheus output.
- Redis-backed burst rate-limiting and WebSocket feeds supporting multi-symbol subscriptions.

All functionality works with free APIs (CoinGecko, Binance public, DexScreener) and open-source libraries only.

## Getting Started

1. **Install dependencies**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. **Copy the sample environment**

```bash
cp .env.sample .env
```

Populate optional keys as needed:

- `COINGECKO_API_KEY` (optional, improves rate limits)
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` (optional community ingestion)
- `OPENAI_API_KEY` (optional summarisation – default off)

Feature flags toggle modules (`FEATURE_*`). Defaults keep paid integrations disabled. Enable portfolio/insights by flipping to `1`.

3. **Start local services**

Ensure Redis is running (for rate limiting and task queues). For development you can run:

```bash
redis-server --save "" --appendonly no
```

Launch the API:

```bash
uvicorn app.main:app --reload
```

4. **Run migrations / bootstrap (SQLite dev example)**

```bash
python scripts/migrate.py
python scripts/bootstrap_simple.py  # optional sample data
```

### Background workers

RQ tasks (predictions refresh, nightly portfolio snapshots, optional Reddit ingestion) can be launched with:

```bash
rq worker -u $REDIS_URL market_matrix
```

Schedule recurring jobs (cron-style) via `rq-scheduler` or your preferred scheduler referencing `PORTFOLIO_SNAPSHOT_SCHEDULE_CRON`.

## Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `FEATURE_PREDICTIONS` | 1 | Enable forecasting endpoints & websockets |
| `FEATURE_DASHBOARD` | 1 | Dashboard metadata & market websockets |
| `FEATURE_ADVANCED_TOOLS` | 1 | Technical indicators, depth, trades |
| `FEATURE_WEB3_HEALTH` | 1 | DexScreener health endpoint |
| `FEATURE_PORTFOLIO` | 0 | CSV portfolio upload, holdings, allocation |
| `FEATURE_INSIGHTS` | 0 | Community insights API |
| `FEATURE_WALLET` | 0 | Reserved (kept disabled) |

## Smoke Test Commands

```bash
# Health
curl -s http://localhost:8000/api/v1/health | jq

# Predictions
curl -s "http://localhost:8000/api/v1/predictions?symbol=BTC&horizon=4h" | jq
websocat ws://localhost:8000/api/v1/ws/predictions

# Market tools
curl -s "http://localhost:8000/api/v1/market/BTC/indicators?set=RSI,MACD,SMA" | jq
curl -s "http://localhost:8000/api/v1/market/BTC/depth" | jq
curl -s "http://localhost:8000/api/v1/market/BTC/trades?limit=50" | jq

# Web3 health
curl -s "http://localhost:8000/api/v1/web3/health?symbol=BTC" | jq

# Portfolio (enable FEATURE_PORTFOLIO=1)
curl -F "file=@samples/holdings_example.csv" http://localhost:8000/api/v1/portfolio/upload
curl -s http://localhost:8000/api/v1/portfolio/holdings | jq
curl -s "http://localhost:8000/api/v1/portfolio/performance?window=30d" | jq
curl -s http://localhost:8000/api/v1/portfolio/allocation | jq

# Insights (enable FEATURE_INSIGHTS=1)
curl -s "http://localhost:8000/api/v1/insights/summary?symbol=BTC&window=24h" | jq
curl -s "http://localhost:8000/api/v1/insights/events?symbol=BTC&limit=10" | jq
```

## Testing

```bash
pytest
```

This suite covers authentication, health checks, predictions, portfolio ingestion, insights and web3 health endpoints.

## Notes

- All external network calls gracefully degrade; cached results are served when vendors fail.
- WebSockets accept subscription messages: `{ "action": "subscribe", "symbols": ["BTC", "ETH"] }` and stream updates per topic.
- Rate limiting is configured via `REQUEST_RATE_LIMITS` (path:requests/window). Defaults throttle predictions (60/min) and portfolio uploads (5/min).
- Optional Reddit ingestion requires PRAW credentials; summarisation stays disabled unless `TRANSFORMERS_LOCAL=1` and models are available locally.
