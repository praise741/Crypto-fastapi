from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

import httpx


COINGECKO_IDS: Dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "XRP": "ripple",
}


@dataclass
class CoinGeckoPrice:
    symbol: str
    price: float
    change_24h: float | None
    volume_24h: float | None
    market_cap: float | None
    timestamp: datetime


@dataclass
class CoinGeckoCandle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class CoinGeckoClient:
    """Lightweight HTTP client for the public CoinGecko API."""

    def __init__(
        self,
        api_key: str | None,
        base_url: str = "https://api.coingecko.com/api/v3",
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"accept": "application/json"}
        if self.api_key:
            headers["x_cg_pro_api_key"] = self.api_key
        return headers

    def _resolve_symbol(self, symbol: str) -> str | None:
        return COINGECKO_IDS.get(symbol.upper())

    def fetch_price(self, symbol: str) -> Optional[CoinGeckoPrice]:
        coin_id = self._resolve_symbol(symbol)
        if not coin_id:
            return None

        url = f"{self.base_url}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
        }
        try:
            response = httpx.get(
                url, headers=self._headers(), params=params, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        payload = response.json()
        entry = payload.get(coin_id)
        if not entry:
            return None

        return CoinGeckoPrice(
            symbol=symbol.upper(),
            price=float(entry.get("usd", 0.0)),
            change_24h=float(entry.get("usd_24h_change", 0.0))
            if entry.get("usd_24h_change") is not None
            else None,
            volume_24h=float(entry.get("usd_24h_vol", 0.0))
            if entry.get("usd_24h_vol") is not None
            else None,
            market_cap=float(entry.get("usd_market_cap", 0.0))
            if entry.get("usd_market_cap") is not None
            else None,
            timestamp=datetime.utcnow(),
        )

    def fetch_market_chart(
        self,
        symbol: str,
        days: int = 7,
        interval: str = "hourly",
    ) -> List[CoinGeckoCandle]:
        coin_id = self._resolve_symbol(symbol)
        if not coin_id:
            return []

        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": str(days),
            "interval": interval,
        }
        try:
            response = httpx.get(
                url, headers=self._headers(), params=params, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        payload = response.json()
        prices: List[List[float]] = payload.get("prices", [])
        volumes_lookup: Dict[int, float] = {
            int(point[0]): float(point[1])
            for point in payload.get("total_volumes", [])
            if len(point) == 2
        }

        candles: List[CoinGeckoCandle] = []
        previous_price: float | None = None
        for entry in prices:
            if len(entry) != 2:
                continue
            timestamp_ms, close_price = entry
            dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc).replace(
                tzinfo=None
            )
            if previous_price is None:
                open_price = close_price
            else:
                open_price = previous_price
            high_price = max(open_price, close_price)
            low_price = min(open_price, close_price)
            volume = volumes_lookup.get(int(timestamp_ms), 0.0)
            candles.append(
                CoinGeckoCandle(
                    symbol=symbol.upper(),
                    timestamp=dt,
                    open=float(open_price),
                    high=float(high_price),
                    low=float(low_price),
                    close=float(close_price),
                    volume=float(volume),
                )
            )
            previous_price = close_price

        return candles

    def fetch_supported_symbols(self) -> Iterable[str]:
        return COINGECKO_IDS.keys()
