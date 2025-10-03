from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx


@dataclass
class DexScreenerPair:
    symbol: str
    pair_address: str
    chain_id: str
    price_usd: float | None
    liquidity_usd: float | None
    volume_24h: float | None
    transactions: Dict[str, Dict[str, int]]
    updated_at: datetime | None


class DexScreenerClient:
    """Utility for retrieving lightweight metrics from DexScreener."""

    def __init__(
        self,
        base_url: str = "https://api.dexscreener.com/latest/dex",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, params: Dict[str, str]) -> Dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = httpx.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def search_pair(self, symbol: str) -> Optional[DexScreenerPair]:
        try:
            payload = self._request("search", {"q": symbol})
        except httpx.HTTPError:
            return None

        pairs = payload.get("pairs") or []
        if not pairs:
            return None

        pair = pairs[0]
        price = pair.get("priceUsd")
        liquidity = None
        if isinstance(pair.get("liquidity"), dict):
            liquidity = pair["liquidity"].get("usd")
        volume = None
        if isinstance(pair.get("volume"), dict):
            volume = pair["volume"].get("h24")
        updated_at = None
        if pair.get("pairCreatedAt"):
            updated_at = datetime.fromtimestamp(
                pair["pairCreatedAt"] / 1000.0, tz=timezone.utc
            ).replace(tzinfo=None)
        return DexScreenerPair(
            symbol=pair.get("baseToken", {}).get("symbol", symbol).upper(),
            pair_address=pair.get("pairAddress", ""),
            chain_id=pair.get("chainId", ""),
            price_usd=float(price) if price is not None else None,
            liquidity_usd=float(liquidity) if liquidity is not None else None,
            volume_24h=float(volume) if volume is not None else None,
            transactions=pair.get("txns", {}),
            updated_at=updated_at,
        )
