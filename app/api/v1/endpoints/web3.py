from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.core.features import require_feature
from app.core.responses import success_response
from app.services.web3 import get_web3_health


router = APIRouter(prefix="/web3", tags=["Web3"])


@router.get("/health")
def web3_health(symbol: str = Query(..., min_length=1)):
    require_feature("web3_health")
    try:
        health = get_web3_health(symbol)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    return success_response(
        {
            "symbol": health.symbol,
            "liquidity": health.liquidity,
            "vol24h": health.vol24h,
            "txPerHour": health.tx_per_hour,
            "pools": [
                {
                    "address": pool.address,
                    "chain": pool.chain,
                    "liquidity": pool.liquidity_usd,
                    "price": pool.price_usd,
                }
                for pool in health.pools
            ],
            "lastUpdated": health.last_updated.isoformat(),
        }
    )
