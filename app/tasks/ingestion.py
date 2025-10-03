from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from redis import Redis
from rq import Queue
from sqlalchemy import func

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.database.market_data import MarketData
from app.services.market_data import (
    calculate_indicators as service_calculate_indicators,
)
from app.services.market_data import fetch_market_history
from app.services.prediction import get_predictions


redis_connection = Redis.from_url(settings.REDIS_URL)
queue = Queue("crypto_tasks", connection=redis_connection)


def fetch_market_data(symbol: str, lookback_days: int | None = None) -> None:
    """Fetch live market data for a symbol and persist it."""

    session = SessionLocal()
    try:
        fetch_market_history(session, symbol, lookback_days=lookback_days)
    finally:
        session.close()


def fetch_all_symbols(lookback_days: int | None = None) -> None:
    for symbol in settings.SUPPORTED_SYMBOLS:
        queue.enqueue(fetch_market_data, symbol, lookback_days)


def calculate_indicators(symbol: str, indicators: Iterable[str] | None = None) -> None:
    session = SessionLocal()
    try:
        indicator_list = list(indicators or ["rsi", "macd", "ema", "sma", "bb"])
        service_calculate_indicators(session, symbol, indicator_list)
    finally:
        session.close()


def cleanup_old_data(days: int = 30) -> None:
    cutoff = datetime.utcnow() - timedelta(days=days)
    session = SessionLocal()
    try:
        session.query(MarketData).filter(MarketData.timestamp < cutoff).delete()
        session.commit()
    finally:
        session.close()


def validate_data_integrity() -> None:
    session = SessionLocal()
    try:
        duplicates = (
            session.query(
                MarketData.symbol,
                MarketData.timestamp,
                func.count(MarketData.id).label("count"),
            )
            .group_by(MarketData.symbol, MarketData.timestamp)
            .having(func.count(MarketData.id) > 1)
            .all()
        )
        for symbol, timestamp, _ in duplicates:
            (
                session.query(MarketData)
                .filter(
                    MarketData.symbol == symbol,
                    MarketData.timestamp == timestamp,
                )
                .order_by(MarketData.id)
                .offset(1)
                .delete(synchronize_session=False)
            )
        session.commit()
    finally:
        session.close()


def generate_predictions(symbol: str) -> None:
    session = SessionLocal()
    try:
        get_predictions(session, symbol)
    finally:
        session.close()


def bootstrap_all() -> None:
    """Fetch data and generate predictions for all supported symbols."""

    for symbol in settings.SUPPORTED_SYMBOLS:
        fetch_market_data(symbol)
        generate_predictions(symbol)
