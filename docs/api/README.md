# CryptoPrediction API Documentation

The FastAPI application exposes a fully documented OpenAPI schema at `/api/v1/openapi.json` and interactive documentation via Swagger UI at `/api/v1/docs`.

## Quick Start

```bash
uvicorn app.main:app --reload --port 8000
```

### Live data quick start

1. Copy the environment template and enable external data providers:

   ```bash
   cp .env.example .env
   echo "ENABLE_EXTERNAL_MARKET_DATA=true" >> .env
   ```

2. Bootstrap market history and Prophet predictions:

   ```bash
   python scripts/bootstrap_simple.py
   ```

3. Launch the API (Docker or local `uvicorn`). The `/market` and `/predictions` endpoints will now serve CoinGecko/DexScreener
   powered responses with Prophet-generated forecasts.

## Notable Endpoints

- `POST /api/v1/auth/register` – Register a new user and receive JWT tokens.
- `GET /api/v1/market/prices` – Retrieve current market prices for supported symbols.
- `GET /api/v1/predictions/{symbol}` – Fetch AI driven predictions for a symbol.
- `GET /api/v1/indices` – Overview of custom market indices.
- `GET /api/v1/alerts` – Manage user specific market alerts.
- `WS /api/v1/ws/market` – Subscribe to live market updates.
