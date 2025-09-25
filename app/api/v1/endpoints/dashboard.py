from __future__ import annotations

from fastapi import APIRouter

from app.core.features import require_feature
from app.core.responses import success_response


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

WIDGETS = [
    {
        "name": "priceTicker",
        "description": "Latest price, change and volume",
        "endpoint": "/market/{symbol}/price",
        "schema": {
            "symbol": "string",
            "price": "float",
            "change_24h": "float",
            "volume_24h": "float",
            "timestamp": "datetime",
        },
    },
    {
        "name": "ohlcv",
        "description": "OHLCV candles",
        "endpoint": "/market/{symbol}/ohlcv",
        "schema": {
            "candles": ["timestamp", "open", "high", "low", "close", "volume"],
        },
    },
    {
        "name": "indicators",
        "description": "Technical indicators (RSI, MACD, SMA, EMA, BOLL)",
        "endpoint": "/market/{symbol}/indicators",
        "schema": {
            "indicators": ["name", "value", "metadata"],
        },
    },
    {
        "name": "orderBook",
        "description": "Aggregated market depth",
        "endpoint": "/market/{symbol}/depth",
        "schema": {
            "bids": ["price", "quantity"],
            "asks": ["price", "quantity"],
            "timestamp": "datetime",
        },
    },
    {
        "name": "recentTrades",
        "description": "Recent executed trades",
        "endpoint": "/market/{symbol}/trades",
        "schema": {
            "trades": ["trade_id", "price", "quantity", "side", "timestamp"],
        },
    },
    {
        "name": "predictions",
        "description": "Model predictions per horizon",
        "endpoint": "/predictions?symbol={symbol}",
        "schema": {
            "predictions": ["horizon", "predicted_price", "confidence_interval", "probability"],
        },
    },
]


@router.get("/metadata")
def dashboard_metadata():
    require_feature("dashboard")
    return success_response({"widgets": WIDGETS, "websockets": ["/ws/market", "/ws/predictions"]})
