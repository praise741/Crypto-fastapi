from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import httpx


@dataclass
class BinanceTicker:
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: datetime


@dataclass
class BinanceTrade:
    price: float
    qty: float
    quote_qty: float
    timestamp: datetime
    is_buyer_maker: bool


@dataclass
class BinanceDepthLevel:
    price: float
    quantity: float


class BinanceClient:
    """Client for Binance public market data endpoints."""

    def __init__(self, base_url: str = "https://api.binance.com/api/v3", timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, params: Optional[Dict[str, str]] = None) -> Optional[dict]:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError:
            return None
        return response.json()

    def fetch_ticker(self, symbol: str) -> Optional[BinanceTicker]:
        payload = self._request("/ticker/24hr", {"symbol": symbol.upper() + "USDT"})
        if not payload:
            return None
        return BinanceTicker(
            symbol=symbol.upper(),
            price=float(payload.get("lastPrice", 0.0)),
            bid=float(payload.get("bidPrice", 0.0)),
            ask=float(payload.get("askPrice", 0.0)),
            volume=float(payload.get("volume", 0.0)),
            timestamp=datetime.utcnow(),
        )

    def fetch_depth(self, symbol: str, limit: int = 50) -> Optional[dict]:
        payload = self._request("/depth", {"symbol": symbol.upper() + "USDT", "limit": str(limit)})
        if not payload:
            return None
        return payload

    def fetch_trades(self, symbol: str, limit: int = 200) -> List[BinanceTrade]:
        payload = self._request("/trades", {"symbol": symbol.upper() + "USDT", "limit": str(limit)})
        if not isinstance(payload, list):
            return []
        trades: List[BinanceTrade] = []
        for entry in payload:
            trades.append(
                BinanceTrade(
                    price=float(entry.get("price", 0.0)),
                    qty=float(entry.get("qty", 0.0)),
                    quote_qty=float(entry.get("quoteQty", 0.0)),
                    timestamp=datetime.fromtimestamp(entry.get("time", 0) / 1000.0),
                    is_buyer_maker=bool(entry.get("isBuyerMaker", False)),
                )
            )
        return trades
