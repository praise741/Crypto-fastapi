from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SymbolMetadata(BaseModel):
    symbol: str
    name: str
    description: Optional[str] = None
    sources: List[str] = Field(default_factory=list)


class TrackSymbolRequest(BaseModel):
    source: Optional[str] = None
    notes: Optional[str] = None


class TrackSymbolResponse(BaseModel):
    symbol: SymbolMetadata
    activated: bool = True


class MarketPrice(BaseModel):
    symbol: str
    price: float
    change_24h: float | None = None
    volume_24h: float | None = None
    timestamp: datetime


class Ticker(BaseModel):
    symbol: str
    price: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    change_percent: float | None = None
    volume: float | None = None
    timestamp: datetime


class DepthLevel(BaseModel):
    price: float
    quantity: float


class OrderBook(BaseModel):
    symbol: str
    bids: List[DepthLevel]
    asks: List[DepthLevel]
    timestamp: datetime


class Trade(BaseModel):
    trade_id: str
    price: float
    quantity: float
    side: str
    timestamp: datetime


class IndicatorValue(BaseModel):
    name: str
    value: float
    metadata: dict | None = None


class IndicatorResponse(BaseModel):
    symbol: str
    indicators: List[IndicatorValue]
    timestamp: datetime


class MarketStats(BaseModel):
    total_market_cap: float
    total_volume: float
    bitcoin_dominance: float | None = None
    sentiment_score: float | None = None
    timestamp: datetime


class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class OHLCVResponse(BaseModel):
    symbol: str
    interval: str
    candles: List[Candle]
