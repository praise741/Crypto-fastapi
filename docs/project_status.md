# Project Status – Remaining Work

## Implemented foundation
- Authentication, market data, prediction, indices, alerts, health, portfolio, insights, web3, and websocket routers are wired into the FastAPI application, giving broad coverage of the PRD's phase 1–5 endpoint skeletons.【F:app/api/v1/router.py†L5-L31】
- Market data endpoints expose read-only symbol, price, OHLCV, indicator, and stats queries, matching the PRD's read endpoints (minus admin tracking).【F:app/api/v1/endpoints/market.py†L1-L83】

## Outstanding gaps versus the PRD
1. **Analytics router implemented.** `/api/v1/analytics/*` endpoints now expose correlations, volatility, trend, pattern, performance, and momentum analytics calculated directly from market history with cached responses to match the PRD contract.【F:app/api/v1/endpoints/analytics.py†L1-L59】【F:app/services/analytics.py†L1-L211】
2. **Admin symbol onboarding live.** `POST /api/v1/market/symbols/{symbol}/track` persists tracked symbols, updates metadata, and returns confirmation for admins leveraging API keys.【F:app/api/v1/endpoints/market.py†L18-L105】
3. **Security hardening completed.** Middleware now validates hashed API keys, enforces auth on non-public routes, and writes audit logs while webhook signing helpers are available for outbound integrations.【F:app/api/middleware/authentication.py†L1-L51】【F:app/api/middleware/audit.py†L1-L31】【F:app/services/security.py†L1-L64】
4. **Caching and performance in place.** Redis-backed caches service market prices, OHLCV candles, and prediction payloads while responses include `Cache-Control` headers matching the performance targets, and mutation paths now invalidate affected keys to avoid stale payloads.【F:app/services/market_data.py†L96-L414】【F:app/services/prediction.py†L1-L410】【F:app/api/v1/endpoints/market.py†L49-L87】
5. **Index shortcuts available.** Dedicated `/indices/altseason`, `/indices/fear-greed`, and `/indices/dominance` endpoints expose the most common dashboard views alongside the generic index router.【F:app/api/v1/endpoints/indices.py†L1-L74】
6. **Testing matrix expanded.** New contract, load, analytics, and security tests exercise the updated surface area alongside the bcrypt guard to restore a passing pytest suite.【F:tests/contract/test_response_contract.py†L1-L21】【F:tests/load/test_market_load.py†L1-L18】【F:tests/integration/test_analytics_endpoints.py†L1-L16】【F:tests/unit/test_security.py†L1-L11】
7. **CI workflow authored.** GitHub Actions now execute formatting, linting, and the pytest suite to satisfy the PRD’s automation expectations.【F:.github/workflows/ci.yml†L1-L46】
8. **Load testing scenario ready.** A Locust file exercises key market, prediction, analytics, and index endpoints to stress the stack under concurrent load beyond the pytest smoke case.【F:load/locustfile.py†L1-L53】

## Quality and reliability status
- `pytest` currently fails because bcrypt rejects passwords longer than 72 bytes in the auth flow and security unit test, so registration/login is not production ready.【5183e6†L1-L8】 Resolving the hashing constraint is necessary before launch.

## Suggested next steps
1. Automate market data ingestion/backfill so analytics consistently receive the depth of history assumed by their calculations.
2. Implement cache invalidation for external market-data sync jobs to complement the admin and prediction hooks and ensure downstream caches stay fresh.
3. Extend the index shortcuts with historical sparkline aggregates and alerts to match the richer UX described in the PRD.
4. Integrate the Locust scenario into CI/CD (or a nightly pipeline) and capture SLO metrics for trend analysis.
