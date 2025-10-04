from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.core.features import require_feature
from app.core.http import apply_cache_headers
from app.core.responses import success_response
from app.services.market_data import get_cached_prices
from app.services.prediction import get_cached_predictions


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
            "predictions": [
                "horizon",
                "predicted_price",
                "confidence_interval",
                "probability",
            ],
        },
    },
]


@router.get("/metadata")
def dashboard_metadata():
    require_feature("dashboard")
    return success_response(
        {"widgets": WIDGETS, "websockets": ["/ws/market", "/ws/predictions"]}
    )


@router.get("")
def get_dashboard(response: Response, db: Session = Depends(get_db)):
    """
    Get aggregated dashboard data.
    
    Returns market overview, top predictions, and key metrics.
    Uses only free APIs (CoinGecko, Binance, DexScreener).
    """
    require_feature("dashboard")
    
    # Get market prices
    prices = get_cached_prices(db)
    
    # Calculate metrics
    total_market_cap = sum(p.market_cap or 0 for p in prices if p.market_cap)
    total_volume = sum(p.volume_24h or 0 for p in prices if p.volume_24h)
    
    # Get BTC for dominance calculation
    btc_price = next((p for p in prices if p.symbol == "BTC"), None)
    btc_dominance = 0
    if btc_price and btc_price.market_cap and total_market_cap > 0:
        btc_dominance = (btc_price.market_cap / total_market_cap) * 100
    
    # Get predictions for top symbols
    top_symbols = ["BTC", "ETH", "SOL", "BNB", "ADA"]
    predictions = []
    for symbol in top_symbols:
        try:
            pred = get_cached_predictions(db, symbol, horizons=["24h"], include_confidence=True, include_factors=False)
            if pred.predictions:
                first_pred = pred.predictions[0]
                predictions.append({
                    "symbol": symbol,
                    "current_price": pred.current_price,
                    "predicted_price": first_pred.predicted_price,
                    "horizon": first_pred.horizon,
                    "confidence": first_pred.confidence_interval.confidence if first_pred.confidence_interval else 0.5,
                    "direction": "up" if first_pred.predicted_price > pred.current_price else "down"
                })
        except:
            pass
    
    apply_cache_headers(response, 60)
    return success_response({
        "metrics": {
            "total_market_cap": total_market_cap,
            "total_volume_24h": total_volume,
            "btc_dominance": round(btc_dominance, 2),
            "fear_greed_index": 65  # Placeholder - can be enhanced with sentiment analysis
        },
        "predictions": predictions
    })


@router.get("/metrics")
def get_dashboard_metrics(response: Response, db: Session = Depends(get_db)):
    """
    Get dashboard metrics only.
    
    Fast endpoint for key market metrics.
    """
    require_feature("dashboard")
    
    prices = get_cached_prices(db)
    
    total_market_cap = sum(p.market_cap or 0 for p in prices if p.market_cap)
    total_volume = sum(p.volume_24h or 0 for p in prices if p.volume_24h)
    
    btc_price = next((p for p in prices if p.symbol == "BTC"), None)
    btc_dominance = 0
    if btc_price and btc_price.market_cap and total_market_cap > 0:
        btc_dominance = (btc_price.market_cap / total_market_cap) * 100
    
    apply_cache_headers(response, 60)
    return success_response({
        "total_market_cap": total_market_cap,
        "total_volume_24h": total_volume,
        "btc_dominance": round(btc_dominance, 2),
        "fear_greed_index": 65
    })
