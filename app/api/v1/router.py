from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    analytics,
    auth,
    dashboard,
    gas,
    health,
    indices,
    insights,
    market,
    news,
    portfolio,
    predictions,
    token_health,
    web3,
    websocket,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(analytics.router)
api_router.include_router(market.router)
api_router.include_router(predictions.router)
api_router.include_router(predictions.models_router)
api_router.include_router(dashboard.router)
api_router.include_router(indices.router)
api_router.include_router(alerts.router)
api_router.include_router(health.router)
api_router.include_router(token_health.router)
api_router.include_router(portfolio.router)
api_router.include_router(insights.router)
api_router.include_router(web3.router)
api_router.include_router(news.router)
api_router.include_router(gas.router)
api_router.include_router(websocket.router)
