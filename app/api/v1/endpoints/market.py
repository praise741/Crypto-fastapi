from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_active_api_key, get_db
from app.core.http import apply_cache_headers
from app.core.responses import error_response, success_response
from app.services.market_data import (
    calculate_indicators,
    get_cached_latest_price,
    get_cached_ohlcv,
    get_cached_prices,
    get_market_stats,
    get_order_book,
    get_recent_trades,
    get_symbol,
    get_ticker,
    list_symbols,
    track_symbol,
)
from app.services.security import APIKeyInfo
from app.models.schemas.market import TrackSymbolRequest, TrackSymbolResponse

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/symbols")
def symbols(db: Session = Depends(get_db)):
    return success_response(
        {"symbols": [symbol.model_dump() for symbol in list_symbols(db)]}
    )


@router.get("/symbols/{symbol}")
def symbol_detail(symbol: str, db: Session = Depends(get_db)):
    metadata = get_symbol(db, symbol)
    if not metadata:
        raise HTTPException(status_code=404, detail="Symbol not supported")
    return success_response({"symbol": metadata.model_dump()})


@router.get("/prices")
def prices(response: Response, db: Session = Depends(get_db)):
    data = [price.model_dump() for price in get_cached_prices(db)]
    apply_cache_headers(response, 30)
    return success_response({"prices": data})


@router.get("/{symbol}/price")
def price(symbol: str, response: Response, db: Session = Depends(get_db)):
    if not get_symbol(db, symbol):
        return JSONResponse(
            status_code=404,
            content=error_response("SYMBOL_NOT_FOUND", "Symbol not supported"),
        )
    data = get_cached_latest_price(db, symbol)
    apply_cache_headers(response, 30)
    return success_response(data.model_dump())


@router.get("/{symbol}/ticker")
def ticker(symbol: str, db: Session = Depends(get_db)):
    if not get_symbol(db, symbol):
        return JSONResponse(
            status_code=404,
            content=error_response("SYMBOL_NOT_FOUND", "Symbol not supported"),
        )
    data = get_ticker(db, symbol)
    return success_response(data.model_dump())


@router.get("/{symbol}/depth")
def depth(symbol: str):
    data = get_order_book(symbol)
    return success_response(data.model_dump())


@router.get("/{symbol}/trades")
def trades(symbol: str):
    trade_data = [trade.model_dump() for trade in get_recent_trades(symbol)]
    return success_response({"symbol": symbol.upper(), "trades": trade_data})


@router.get("/{symbol}/ohlcv")
def ohlcv(
    symbol: str,
    response: Response,
    interval: str = Query("1h", description="Candle interval"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    if not get_symbol(db, symbol):
        return JSONResponse(
            status_code=404,
            content=error_response("SYMBOL_NOT_FOUND", "Symbol not supported"),
        )
    data = get_cached_ohlcv(db, symbol, interval, limit)
    apply_cache_headers(response, 300)
    return success_response(data.model_dump())


@router.get("/{symbol}/indicators")
def indicators(
    symbol: str,
    indicator_set: str = Query(
        "RSI,MACD,SMA,EMA,BOLL",
        alias="set",
        description="Comma separated list of indicators",
    ),
    db: Session = Depends(get_db),
):
    allowed = {"rsi", "macd", "sma", "ema", "boll"}
    requested = [
        item.strip().lower() for item in indicator_set.split(",") if item.strip()
    ]
    invalid = [item for item in requested if item not in allowed]
    if invalid:
        raise HTTPException(
            status_code=400, detail=f"Unsupported indicators: {', '.join(invalid)}"
        )
    data = calculate_indicators(db, symbol, requested)
    return success_response(data.model_dump())


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return success_response(get_market_stats(db).model_dump())


@router.get("/{symbol}/stats")
def symbol_stats(symbol: str, response: Response, db: Session = Depends(get_db)):
    if not get_symbol(db, symbol):
        return JSONResponse(
            status_code=404,
            content=error_response("SYMBOL_NOT_FOUND", "Symbol not supported"),
        )
    latest = get_cached_latest_price(db, symbol)
    ticker = get_ticker(db, symbol)
    apply_cache_headers(response, 30)
    return success_response(
        {"price": latest.model_dump(), "ticker": ticker.model_dump()}
    )


@router.post("/symbols/{symbol}/track", status_code=status.HTTP_201_CREATED)
def track_symbol_endpoint(
    symbol: str,
    payload: TrackSymbolRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    api_key: APIKeyInfo = Depends(get_active_api_key),
):
    metadata = track_symbol(
        db,
        symbol,
        source=payload.source if payload else None,
        notes=payload.notes if payload else None,
        added_by_api_key_id=api_key.id,
    )
    response = TrackSymbolResponse(symbol=metadata)
    return success_response(response.model_dump())
