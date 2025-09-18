from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, List

import pandas as pd
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database.market_data import MarketData
from app.models.schemas.market import (
    Candle,
    IndicatorResponse,
    IndicatorValue,
    MarketPrice,
    MarketStats,
    OHLCVResponse,
    OrderBook,
    SymbolMetadata,
    Ticker,
    Trade,
    DepthLevel,
)
from app.services.external import CoinGeckoClient, DexScreenerClient


SYMBOL_DETAILS: Dict[str, Dict[str, str]] = {
    "BTC": {
        "name": "Bitcoin",
        "description": "Bitcoin price data aggregated from CoinGecko with DexScreener liquidity context.",
    },
    "ETH": {
        "name": "Ethereum",
        "description": "Ethereum market data pulled from CoinGecko and DexScreener.",
    },
    "SOL": {
        "name": "Solana",
        "description": "Solana ecosystem pricing sourced from CoinGecko and DexScreener pairs.",
    },
    "ADA": {
        "name": "Cardano",
        "description": "Cardano market history fetched hourly from CoinGecko with on-chain sentiment via DexScreener.",
    },
    "XRP": {
        "name": "XRP",
        "description": "XRP consolidated spot data from CoinGecko and DexScreener feeds.",
    },
}


SYMBOL_METADATA: Dict[str, SymbolMetadata] = {
    symbol: SymbolMetadata(
        symbol=symbol,
        name=details.get("name", symbol),
        description=details.get("description"),
        sources=["database", "CoinGecko", "DexScreener"],
    )
    for symbol, details in SYMBOL_DETAILS.items()
}


coin_gecko_client = CoinGeckoClient(
    api_key=settings.COINGECKO_API_KEY,
    base_url=settings.COINGECKO_BASE_URL,
)
dex_screener_client = DexScreenerClient(base_url=settings.DEXSCREENER_BASE_URL)


def _fallback_price(symbol: str) -> MarketPrice:
    now = datetime.utcnow()
    base_price = 20000 + (hash(symbol) % 5000)
    return MarketPrice(
        symbol=symbol.upper(),
        price=float(base_price),
        change_24h=0.0,
        volume_24h=0.0,
        timestamp=now,
    )


def list_symbols() -> List[SymbolMetadata]:
    symbols = {symbol.upper(): metadata for symbol, metadata in SYMBOL_METADATA.items()}
    for symbol in settings.SUPPORTED_SYMBOLS:
        if symbol.upper() not in symbols:
            symbols[symbol.upper()] = SymbolMetadata(
                symbol=symbol.upper(),
                name=symbol.upper(),
                description=f"Synthetic metadata for {symbol.upper()}",
                sources=["database"],
            )
    return list(symbols.values())


def get_symbol(symbol: str) -> SymbolMetadata | None:
    symbol = symbol.upper()
    if symbol in SYMBOL_METADATA:
        return SYMBOL_METADATA[symbol]
    return SymbolMetadata(
        symbol=symbol,
        name=symbol,
        description=f"Synthetic metadata for {symbol}",
        sources=["database"],
    )


def _store_market_row(
    session: Session,
    *,
    symbol: str,
    timestamp: datetime,
    open_price: float,
    high_price: float,
    low_price: float,
    close_price: float,
    volume: float | None,
    market_cap: float | None,
    source: str,
) -> None:
    symbol = symbol.upper()
    timestamp = timestamp.replace(tzinfo=None)
    existing = (
        session.query(MarketData)
        .filter(and_(MarketData.symbol == symbol, MarketData.timestamp == timestamp))
        .first()
    )
    if existing:
        existing.open = open_price
        existing.high = high_price
        existing.low = low_price
        existing.close = close_price
        existing.volume = volume
        existing.market_cap = market_cap
        existing.source = source
    else:
        session.add(
            MarketData(
                symbol=symbol,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                market_cap=market_cap,
                source=source,
            )
        )


def fetch_market_history(
    session: Session,
    symbol: str,
    *,
    lookback_days: int | None = None,
) -> int:
    if not settings.ENABLE_EXTERNAL_MARKET_DATA:
        return 0

    lookback_days = lookback_days or settings.MARKET_DATA_LOOKBACK_DAYS
    candles = coin_gecko_client.fetch_market_chart(symbol, days=lookback_days, interval="hourly")
    inserted = 0
    if not candles:
        return inserted

    for candle in candles:
        _store_market_row(
            session,
            symbol=candle.symbol,
            timestamp=candle.timestamp,
            open_price=candle.open,
            high_price=candle.high,
            low_price=candle.low,
            close_price=candle.close,
            volume=candle.volume,
            market_cap=None,
            source="coingecko",
        )
        inserted += 1
    session.commit()
    return inserted


def _refresh_from_coin_gecko(session: Session, symbol: str) -> MarketPrice | None:
    if not settings.ENABLE_EXTERNAL_MARKET_DATA:
        return None

    price = coin_gecko_client.fetch_price(symbol)
    if not price:
        return None

    _store_market_row(
        session,
        symbol=price.symbol,
        timestamp=price.timestamp,
        open_price=price.price,
        high_price=price.price,
        low_price=price.price,
        close_price=price.price,
        volume=price.volume_24h,
        market_cap=price.market_cap,
        source="coingecko",
    )
    session.commit()
    return MarketPrice(
        symbol=price.symbol,
        price=price.price,
        change_24h=price.change_24h,
        volume_24h=price.volume_24h,
        timestamp=price.timestamp,
    )


def _refresh_from_dex_screener(session: Session, symbol: str) -> MarketPrice | None:
    if not settings.DEXSCREENER_ENABLED:
        return None

    pair = dex_screener_client.search_pair(symbol)
    if not pair or pair.price_usd is None:
        return None

    timestamp = pair.updated_at or datetime.utcnow()
    _store_market_row(
        session,
        symbol=symbol,
        timestamp=timestamp,
        open_price=pair.price_usd,
        high_price=pair.price_usd,
        low_price=pair.price_usd,
        close_price=pair.price_usd,
        volume=pair.volume_24h,
        market_cap=None,
        source="dexscreener",
    )
    session.commit()
    return MarketPrice(
        symbol=symbol.upper(),
        price=pair.price_usd,
        change_24h=None,
        volume_24h=pair.volume_24h,
        timestamp=timestamp,
    )


def _ensure_recent_price(session: Session, symbol: str) -> None:
    symbol = symbol.upper()
    record = (
        session.query(MarketData)
        .filter(MarketData.symbol == symbol)
        .order_by(desc(MarketData.timestamp))
        .first()
    )
    if record and record.timestamp >= datetime.utcnow() - timedelta(minutes=30):
        return

    refreshed = _refresh_from_coin_gecko(session, symbol)
    if refreshed:
        return
    _refresh_from_dex_screener(session, symbol)


def get_latest_price(session: Session, symbol: str) -> MarketPrice:
    symbol = symbol.upper()
    _ensure_recent_price(session, symbol)
    record = (
        session.query(MarketData)
        .filter(MarketData.symbol == symbol)
        .order_by(desc(MarketData.timestamp))
        .first()
    )
    if not record:
        return _fallback_price(symbol)

    change_24h = None
    volume_24h = float(record.volume or 0)
    if settings.ENABLE_EXTERNAL_MARKET_DATA:
        previous = (
            session.query(MarketData)
            .filter(
                MarketData.symbol == symbol,
                MarketData.timestamp <= record.timestamp - timedelta(hours=24),
            )
            .order_by(desc(MarketData.timestamp))
            .first()
        )
        if previous and previous.close:
            change_24h = (float(record.close) - float(previous.close)) / float(previous.close) * 100

    return MarketPrice(
        symbol=symbol,
        price=float(record.close),
        change_24h=change_24h,
        volume_24h=volume_24h,
        timestamp=record.timestamp,
    )


def get_all_prices(session: Session) -> List[MarketPrice]:
    prices: List[MarketPrice] = []
    for symbol in settings.SUPPORTED_SYMBOLS:
        prices.append(get_latest_price(session, symbol))
    return prices


def get_ticker(session: Session, symbol: str) -> Ticker:
    symbol = symbol.upper()
    _ensure_recent_price(session, symbol)

    window_start = datetime.utcnow() - timedelta(hours=24)
    data = (
        session.query(MarketData)
        .filter(MarketData.symbol == symbol, MarketData.timestamp >= window_start)
        .order_by(MarketData.timestamp.asc())
        .all()
    )
    if not data:
        price = get_latest_price(session, symbol)
        return Ticker(
            symbol=symbol,
            price=price.price,
            open=price.price,
            high=price.price,
            low=price.price,
            change_percent=0.0,
            volume=price.volume_24h,
            timestamp=price.timestamp,
        )

    prices = [float(item.close) for item in data]
    open_price = prices[0]
    close_price = prices[-1]
    high_price = max(prices)
    low_price = min(prices)
    change_percent = ((close_price - open_price) / open_price) * 100 if open_price else 0.0
    volume = sum(float(item.volume or 0) for item in data)
    return Ticker(
        symbol=symbol,
        price=close_price,
        open=open_price,
        high=high_price,
        low=low_price,
        change_percent=change_percent,
        volume=volume,
        timestamp=data[-1].timestamp,
    )


def _build_order_levels(price: float, liquidity_usd: float | None) -> List[DepthLevel]:
    if price <= 0:
        price = 1.0
    quantity_base = liquidity_usd / price / 10 if liquidity_usd else 5.0
    levels: List[DepthLevel] = []
    for depth in range(1, 6):
        step = price * 0.005 * depth
        quantity = max(quantity_base * (1 - depth * 0.1), 0.1)
        levels.append(DepthLevel(price=round(price - step, 2), quantity=float(quantity)))
    return levels


def get_order_book(symbol: str) -> OrderBook:
    base_price = 0.0
    liquidity = None
    pair = None
    if settings.DEXSCREENER_ENABLED:
        pair = dex_screener_client.search_pair(symbol)
    if pair and pair.price_usd:
        base_price = pair.price_usd
        liquidity = pair.liquidity_usd
    if not base_price:
        base_price = 20000 + (hash(symbol) % 5000)

    bids = _build_order_levels(base_price, liquidity)
    asks = [DepthLevel(price=round(base_price + (base_price * 0.005 * (i + 1)), 2), quantity=level.quantity) for i, level in enumerate(bids)]
    return OrderBook(symbol=symbol.upper(), bids=bids, asks=asks, timestamp=datetime.utcnow())


def get_recent_trades(symbol: str) -> List[Trade]:
    trades: List[Trade] = []
    if settings.DEXSCREENER_ENABLED:
        pair = dex_screener_client.search_pair(symbol)
        if pair and pair.transactions:
            now = datetime.utcnow()
            for window, stats in pair.transactions.items():
                buys = stats.get("buys", 0)
                sells = stats.get("sells", 0)
                trades.append(
                    Trade(
                        trade_id=f"{pair.pair_address}-{window}",
                        price=float(pair.price_usd or 0.0),
                        quantity=float(stats.get("volume", 0.0) or (buys + sells) or 0.0),
                        side="buy" if buys >= sells else "sell",
                        timestamp=now - timedelta(minutes=_window_to_minutes(window)),
                    )
                )
    if trades:
        return trades

    now = datetime.utcnow()
    fallback_trades: List[Trade] = []
    for i in range(10):
        fallback_trades.append(
            Trade(
                trade_id=f"{symbol}-{i}",
                price=float(20000 + (hash(symbol) % 5000) + i * 25),
                quantity=float(0.5 + i * 0.1),
                side="buy" if i % 2 == 0 else "sell",
                timestamp=now - timedelta(minutes=i * 3),
            )
        )
    return fallback_trades


def _window_to_minutes(window: str) -> int:
    mapping = {"m5": 5, "h1": 60, "h6": 360, "h24": 1440}
    return mapping.get(window, 60)


def _calculate_rsi(series: pd.Series, period: int = 14) -> float | None:
    if len(series) < period + 1:
        return None
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(to_replace=0, method="ffill")
    rsi = 100 - (100 / (1 + rs))
    value = rsi.iloc[-1]
    if pd.isna(value):
        return None
    return float(value)


def _calculate_macd(series: pd.Series) -> Dict[str, float]:
    if len(series) < 35:
        return {}
    ema_fast = series.ewm(span=12, adjust=False).mean()
    ema_slow = series.ewm(span=26, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return {
        "macd": float(macd.iloc[-1]),
        "signal": float(signal.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


def _calculate_bollinger(series: pd.Series, window: int = 20) -> Dict[str, float] | None:
    if len(series) < window:
        return None
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    mean = rolling_mean.iloc[-1]
    std = rolling_std.iloc[-1]
    if pd.isna(mean) or pd.isna(std):
        return None
    upper = float(mean + 2 * std)
    lower = float(mean - 2 * std)
    return {"middle": float(mean), "upper": upper, "lower": lower}


def calculate_indicators(session: Session, symbol: str, indicators: Iterable[str]) -> IndicatorResponse:
    symbol = symbol.upper()
    records = (
        session.query(MarketData)
        .filter(MarketData.symbol == symbol)
        .order_by(MarketData.timestamp.asc())
        .limit(500)
        .all()
    )
    if not records:
        latest = get_latest_price(session, symbol)
        return IndicatorResponse(symbol=symbol, indicators=[], timestamp=latest.timestamp)

    closes = pd.Series([float(record.close) for record in records], index=[record.timestamp for record in records])
    latest_timestamp = records[-1].timestamp
    indicator_values: List[IndicatorValue] = []
    requested = {item.lower() for item in indicators}

    if "rsi" in requested:
        value = _calculate_rsi(closes)
        if value is not None:
            indicator_values.append(IndicatorValue(name="rsi", value=value))

    if "macd" in requested:
        macd = _calculate_macd(closes)
        if macd:
            indicator_values.append(
                IndicatorValue(
                    name="macd",
                    value=macd["macd"],
                    metadata={"signal": macd["signal"], "histogram": macd["histogram"]},
                )
            )

    if "ema" in requested:
        if len(closes) >= 10:
            ema = closes.ewm(span=10, adjust=False).mean().iloc[-1]
            if not pd.isna(ema):
                indicator_values.append(IndicatorValue(name="ema", value=float(ema)))

    if "sma" in requested:
        if len(closes) >= 10:
            sma = closes.rolling(window=10).mean().iloc[-1]
            if not pd.isna(sma):
                indicator_values.append(IndicatorValue(name="sma", value=float(sma)))

    if "bb" in requested:
        bollinger = _calculate_bollinger(closes)
        if bollinger:
            indicator_values.append(
                IndicatorValue(name="bb", value=bollinger["middle"], metadata={"upper": bollinger["upper"], "lower": bollinger["lower"]})
            )

    return IndicatorResponse(symbol=symbol, indicators=indicator_values, timestamp=latest_timestamp)


def get_market_stats(session: Session) -> MarketStats:
    prices = get_all_prices(session)
    total_market_cap = 0.0
    total_volume = 0.0
    for price in prices:
        total_market_cap += (price.price or 0) * 1_000_000
        total_volume += price.volume_24h or 0.0

    bitcoin_price = next((p.price for p in prices if p.symbol == "BTC"), prices[0].price if prices else 0)
    dominance = 0.0
    if total_market_cap:
        dominance = (bitcoin_price * 1_000_000) / total_market_cap * 100

    sentiment = 50.0
    pair = dex_screener_client.search_pair("BTC") if settings.DEXSCREENER_ENABLED else None
    if pair and pair.transactions:
        buys = sum(stats.get("buys", 0) for stats in pair.transactions.values())
        sells = sum(stats.get("sells", 0) for stats in pair.transactions.values())
        total = buys + sells
        if total:
            sentiment = 50 + ((buys - sells) / total) * 50

    return MarketStats(
        total_market_cap=total_market_cap,
        total_volume=total_volume,
        bitcoin_dominance=dominance,
        sentiment_score=sentiment,
        timestamp=datetime.utcnow(),
    )


def _load_candles(session: Session, symbol: str, limit: int) -> List[MarketData]:
    symbol = symbol.upper()
    records = (
        session.query(MarketData)
        .filter(MarketData.symbol == symbol)
        .order_by(desc(MarketData.timestamp))
        .limit(limit)
        .all()
    )
    return list(reversed(records))


def get_ohlcv(session: Session, symbol: str, interval: str, limit: int) -> OHLCVResponse:
    if settings.ENABLE_EXTERNAL_MARKET_DATA:
        existing_count = (
            session.query(MarketData)
            .filter(MarketData.symbol == symbol.upper())
            .count()
        )
        if existing_count < limit:
            fetch_market_history(session, symbol)

    records = _load_candles(session, symbol, limit)
    candles = [
        Candle(
            timestamp=item.timestamp,
            open=float(item.open or item.close),
            high=float(item.high or item.close),
            low=float(item.low or item.close),
            close=float(item.close),
            volume=float(item.volume or 0.0),
        )
        for item in records
    ]
    return OHLCVResponse(symbol=symbol.upper(), interval=interval, candles=candles)
