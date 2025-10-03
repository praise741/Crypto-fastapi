"""
Gas fee tracker using public Ethereum APIs (no API key required).
Uses Etherscan's free public API for gas prices.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List
import logging

import httpx

logger = logging.getLogger(__name__)


class GasPrice:
    """Represents current gas prices."""

    def __init__(
        self,
        slow: float,
        standard: float,
        fast: float,
        instant: float,
        timestamp: datetime,
    ):
        self.slow = slow
        self.standard = standard
        self.fast = fast
        self.instant = instant
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            "slow": self.slow,
            "standard": self.standard,
            "fast": self.fast,
            "instant": self.instant,
            "timestamp": self.timestamp.isoformat(),
        }


class GasEstimate:
    """Represents estimated transaction cost."""

    def __init__(
        self,
        gas_limit: int,
        tier: str,
        gas_price_gwei: float,
        eth_cost: float,
        usd_cost: float | None = None,
    ):
        self.gas_limit = gas_limit
        self.tier = tier
        self.gas_price_gwei = gas_price_gwei
        self.eth_cost = eth_cost
        self.usd_cost = usd_cost

    def to_dict(self) -> dict:
        return {
            "gas_limit": self.gas_limit,
            "tier": self.tier,
            "gas_price_gwei": self.gas_price_gwei,
            "eth_cost": self.eth_cost,
            "usd_cost": self.usd_cost,
        }


# Cache for gas data
_gas_cache: GasPrice | None = None
_gas_cache_expiry: datetime | None = None
_gas_history: List[GasPrice] = []

CACHE_TTL_SECONDS = 30  # 30 seconds for gas prices


async def fetch_gas_prices_etherscan() -> GasPrice | None:
    """Fetch gas prices from Etherscan (free, no API key needed for basic queries)."""
    try:
        # Etherscan gas oracle endpoint
        url = "https://api.etherscan.io/api?module=gastracker&action=gasoracle"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()

                if data.get("status") == "1" and data.get("result"):
                    result = data["result"]

                    # Parse gas prices (in Gwei)
                    safe_gas = float(result.get("SafeGasPrice", 20))
                    propose_gas = float(result.get("ProposeGasPrice", 30))
                    fast_gas = float(result.get("FastGasPrice", 40))

                    return GasPrice(
                        slow=safe_gas,
                        standard=propose_gas,
                        fast=fast_gas,
                        instant=fast_gas * 1.2,  # Estimate instant as 20% higher
                        timestamp=datetime.utcnow(),
                    )
    except Exception as e:
        logger.error(f"Error fetching Etherscan gas prices: {e}")

    return None


async def fetch_gas_prices_fallback() -> GasPrice:
    """Fallback gas prices based on historical averages."""
    return GasPrice(
        slow=20.0,
        standard=30.0,
        fast=40.0,
        instant=50.0,
        timestamp=datetime.utcnow(),
    )


async def get_current_gas_prices() -> GasPrice:
    """
    Get current Ethereum gas prices.

    Returns:
        GasPrice object with slow/standard/fast/instant tiers
    """
    global _gas_cache, _gas_cache_expiry, _gas_history

    now = datetime.utcnow()

    # Check cache
    if _gas_cache and _gas_cache_expiry and _gas_cache_expiry > now:
        return _gas_cache

    # Fetch fresh data
    gas_price = await fetch_gas_prices_etherscan()

    if not gas_price:
        gas_price = await fetch_gas_prices_fallback()

    # Update cache
    _gas_cache = gas_price
    _gas_cache_expiry = now + timedelta(seconds=CACHE_TTL_SECONDS)

    # Add to history (keep last 24 hours)
    _gas_history.append(gas_price)
    cutoff_time = now - timedelta(hours=24)
    _gas_history[:] = [g for g in _gas_history if g.timestamp > cutoff_time]

    return gas_price


async def estimate_transaction_cost(
    gas_limit: int = 21000,
    tier: str = "standard",
    eth_price_usd: float | None = None,
) -> GasEstimate:
    """
    Estimate transaction cost in ETH and USD.

    Args:
        gas_limit: Gas limit for transaction (default: 21000 for simple transfer)
        tier: Gas price tier (slow/standard/fast/instant)
        eth_price_usd: Current ETH price in USD (optional)

    Returns:
        GasEstimate object with cost breakdown
    """
    gas_prices = await get_current_gas_prices()

    # Get gas price for tier
    tier_prices = {
        "slow": gas_prices.slow,
        "standard": gas_prices.standard,
        "fast": gas_prices.fast,
        "instant": gas_prices.instant,
    }

    gas_price_gwei = tier_prices.get(tier.lower(), gas_prices.standard)

    # Calculate cost in ETH (1 Gwei = 0.000000001 ETH)
    eth_cost = (gas_limit * gas_price_gwei) / 1_000_000_000

    # Calculate USD cost if ETH price provided
    usd_cost = None
    if eth_price_usd:
        usd_cost = eth_cost * eth_price_usd

    return GasEstimate(
        gas_limit=gas_limit,
        tier=tier,
        gas_price_gwei=gas_price_gwei,
        eth_cost=eth_cost,
        usd_cost=usd_cost,
    )


async def get_gas_history(hours: int = 24) -> List[GasPrice]:
    """
    Get historical gas prices.

    Args:
        hours: Number of hours of history to return

    Returns:
        List of GasPrice objects
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    return [g for g in _gas_history if g.timestamp > cutoff_time]


async def get_optimal_gas_timing() -> dict:
    """
    Analyze gas history to suggest optimal timing for transactions.

    Returns:
        Dictionary with recommendations
    """
    if len(_gas_history) < 10:
        return {
            "recommendation": "Insufficient data for analysis",
            "current_vs_average": "unknown",
        }

    # Calculate averages
    avg_standard = sum(g.standard for g in _gas_history) / len(_gas_history)
    current = _gas_cache.standard if _gas_cache else avg_standard

    # Compare current to average
    diff_percent = ((current - avg_standard) / avg_standard) * 100

    if diff_percent < -10:
        recommendation = "Good time to transact - gas prices below average"
        timing = "now"
    elif diff_percent > 10:
        recommendation = "Consider waiting - gas prices above average"
        timing = "wait"
    else:
        recommendation = "Gas prices near average"
        timing = "neutral"

    return {
        "recommendation": recommendation,
        "timing": timing,
        "current_gwei": current,
        "average_gwei": avg_standard,
        "difference_percent": round(diff_percent, 2),
    }
