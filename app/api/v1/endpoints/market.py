from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.core.responses import success_response
from app.services.market_data import (
    calculate_indicators,
    get_all_prices,
    get_latest_price,
    get_market_stats,
    get_order_book,
    get_recent_trades,
    get_symbol,
    get_ticker,
    get_ohlcv,
    list_symbols,
)

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/symbols")
def symbols():
    return success_response({"symbols": [symbol.model_dump() for symbol in list_symbols()]})


@router.get("/symbols/{symbol}")
def symbol_detail(symbol: str):
    metadata = get_symbol(symbol)
    if not metadata:
        raise HTTPException(status_code=404, detail="Symbol not supported")
    return success_response({"symbol": metadata.model_dump()})


@router.get("/prices")
def prices(db: Session = Depends(get_db)):
    data = [price.model_dump() for price in get_all_prices(db)]
    return success_response({"prices": data})


@router.get("/{symbol}/price")
def price(symbol: str, db: Session = Depends(get_db)):
    data = get_latest_price(db, symbol)
    return success_response(data.model_dump())


@router.get("/{symbol}/ticker")
def ticker(symbol: str, db: Session = Depends(get_db)):
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
    interval: str = Query("1h", description="Candle interval"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    data = get_ohlcv(db, symbol, interval, limit)
    return success_response(data.model_dump())


@router.get("/{symbol}/indicators")
def indicators(
    symbol: str,
    indicators: str = Query("rsi,macd", description="Comma separated list of indicators"),
    db: Session = Depends(get_db),
):
    indicator_list: List[str] = [item.strip() for item in indicators.split(",") if item.strip()]
    data = calculate_indicators(db, symbol, indicator_list)
    return success_response(data.model_dump())


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return success_response(get_market_stats(db).model_dump())


@router.get("/{symbol}/stats")
def symbol_stats(symbol: str, db: Session = Depends(get_db)):
    latest = get_latest_price(db, symbol)
    ticker = get_ticker(db, symbol)
    return success_response({"price": latest.model_dump(), "ticker": ticker.model_dump()})
