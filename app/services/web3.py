from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

from app.core.config import settings
from app.services.external import DexScreenerClient


@dataclass
class Web3Pool:
    address: str
    chain: str
    liquidity_usd: float | None
    price_usd: float | None


@dataclass
class Web3Health:
    symbol: str
    liquidity: float | None
    vol24h: float | None
    tx_per_hour: float
    pools: List[Web3Pool]
    last_updated: datetime


dex_client = DexScreenerClient(base_url=settings.DEXSCREENER_BASE_URL)
_cache: Dict[str, Web3Health] = {}
_cache_expiry: Dict[str, datetime] = {}


def _from_pair(symbol: str, pair) -> Web3Health:
    txns = pair.transactions or {}
    h1 = txns.get("h1", {})
    total_tx = float(h1.get("buys", 0) + h1.get("sells", 0))
    tx_per_hour = total_tx
    pool = Web3Pool(
        address=pair.pair_address,
        chain=pair.chain_id,
        liquidity_usd=pair.liquidity_usd,
        price_usd=pair.price_usd,
    )
    return Web3Health(
        symbol=symbol.upper(),
        liquidity=pair.liquidity_usd,
        vol24h=pair.volume_24h,
        tx_per_hour=tx_per_hour,
        pools=[pool],
        last_updated=datetime.utcnow(),
    )


def get_web3_health(symbol: str) -> Web3Health:
    symbol = symbol.upper()
    now = datetime.utcnow()
    cached = _cache.get(symbol)
    expiry = _cache_expiry.get(symbol)
    if cached and expiry and expiry > now:
        return cached

    pair = dex_client.search_pair(symbol)
    if pair:
        health = _from_pair(symbol, pair)
        _cache[symbol] = health
        _cache_expiry[symbol] = now + timedelta(seconds=settings.CACHE_TTL_SECONDS)
        return health

    if cached:
        return cached

    return Web3Health(
        symbol=symbol,
        liquidity=None,
        vol24h=None,
        tx_per_hour=0.0,
        pools=[],
        last_updated=now,
    )
