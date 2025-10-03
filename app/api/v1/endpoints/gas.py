"""
Gas fee tracker endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.responses import success_response
from app.services.gas_tracker import (
    estimate_transaction_cost,
    get_current_gas_prices,
    get_gas_history,
    get_optimal_gas_timing,
)

router = APIRouter(prefix="/gas", tags=["Gas Tracker"])


@router.get("/prices")
async def get_gas_prices():
    """
    Get current Ethereum gas prices in Gwei.

    Returns prices for four tiers:
    - **slow**: Low priority, cheaper
    - **standard**: Normal priority
    - **fast**: High priority, faster confirmation
    - **instant**: Highest priority, fastest confirmation
    """
    gas_prices = await get_current_gas_prices()

    return success_response(gas_prices.to_dict())


@router.get("/estimate")
async def estimate_gas_cost(
    gas_limit: int = Query(21000, ge=21000, le=10000000, description="Gas limit"),
    tier: str = Query(
        "standard",
        pattern="^(slow|standard|fast|instant)$",
        description="Priority tier",
    ),
    eth_price: float = Query(None, ge=0, description="Current ETH price in USD"),
):
    """
    Estimate transaction cost in ETH and USD.

    - **gas_limit**: Gas limit for transaction (default: 21000 for simple transfer)
    - **tier**: Priority tier (slow/standard/fast/instant)
    - **eth_price**: Current ETH price in USD (optional, for USD cost calculation)
    """
    estimate = await estimate_transaction_cost(
        gas_limit=gas_limit,
        tier=tier,
        eth_price_usd=eth_price,
    )

    return success_response(estimate.to_dict())


@router.get("/history")
async def get_gas_price_history(
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
):
    """
    Get historical gas price data.

    - **hours**: Number of hours of history (1-168, default: 24)
    """
    history = await get_gas_history(hours=hours)

    return success_response(
        {
            "history": [price.to_dict() for price in history],
            "count": len(history),
        }
    )


@router.get("/timing")
async def get_gas_timing_recommendation():
    """
    Get recommendation on optimal timing for transactions based on gas price trends.

    Returns:
    - **recommendation**: Human-readable recommendation
    - **timing**: "now", "wait", or "neutral"
    - **current_gwei**: Current gas price
    - **average_gwei**: 24h average gas price
    - **difference_percent**: How much current differs from average
    """
    timing = await get_optimal_gas_timing()

    return success_response(timing)
