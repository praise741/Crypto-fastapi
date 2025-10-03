from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

from app.core.cache import cache_result
from app.core.config import settings
from app.models.database.market_data import MarketData
from app.services.external import DexScreenerClient, CoinGeckoClient


dex_client = DexScreenerClient(base_url=settings.DEXSCREENER_BASE_URL)
coingecko_client = CoinGeckoClient(api_key=settings.COINGECKO_API_KEY)


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Calculate ratio with zero-division protection."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _calculate_liquidity_score(symbol: str) -> float:
    """
    Calculate liquidity health score (0-100).
    Higher scores indicate better liquidity.
    """
    pair = dex_client.search_pair(symbol)
    if not pair:
        return 50.0  # Neutral if no data
    
    liquidity = pair.liquidity or {}
    usd_liquidity = float(liquidity.get("usd", 0))
    
    # Liquidity scoring thresholds
    if usd_liquidity >= 1_000_000:
        return 100.0
    elif usd_liquidity >= 500_000:
        return 85.0
    elif usd_liquidity >= 100_000:
        return 70.0
    elif usd_liquidity >= 50_000:
        return 55.0
    elif usd_liquidity >= 10_000:
        return 40.0
    elif usd_liquidity > 0:
        return 25.0
    else:
        return 10.0


def _calculate_volume_score(symbol: str) -> float:
    """
    Calculate volume health score (0-100).
    Considers both 24h volume and consistency.
    """
    pair = dex_client.search_pair(symbol)
    if not pair:
        return 50.0
    
    volume_24h = pair.volume_24h or 0.0
    
    # Volume scoring thresholds
    if volume_24h >= 10_000_000:
        return 100.0
    elif volume_24h >= 5_000_000:
        return 90.0
    elif volume_24h >= 1_000_000:
        return 75.0
    elif volume_24h >= 500_000:
        return 60.0
    elif volume_24h >= 100_000:
        return 45.0
    elif volume_24h >= 10_000:
        return 30.0
    elif volume_24h > 0:
        return 15.0
    else:
        return 5.0


def _calculate_holder_distribution_score(symbol: str) -> float:
    """
    Calculate holder distribution score (0-100).
    Better distribution = lower whale concentration.
    """
    # For free tier, use approximation based on transaction patterns
    pair = dex_client.search_pair(symbol)
    if not pair:
        return 50.0
    
    txns = pair.transactions or {}
    h24 = txns.get("h24", {})
    
    buys = float(h24.get("buys", 0))
    sells = float(h24.get("sells", 0))
    total_txns = buys + sells
    
    # More transactions = better distribution (proxy)
    if total_txns >= 1000:
        return 90.0
    elif total_txns >= 500:
        return 75.0
    elif total_txns >= 200:
        return 60.0
    elif total_txns >= 50:
        return 45.0
    elif total_txns >= 10:
        return 30.0
    elif total_txns > 0:
        return 20.0
    else:
        return 10.0


def _calculate_volatility_score(db: Session, symbol: str) -> float:
    """
    Calculate volatility score (0-100).
    Lower volatility = higher score (more stable).
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)
    records = (
        db.query(MarketData)
        .filter(MarketData.symbol == symbol.upper(), MarketData.timestamp >= cutoff)
        .order_by(MarketData.timestamp.asc())
        .all()
    )
    
    if len(records) < 2:
        return 50.0
    
    prices = [float(record.close) for record in records]
    avg_price = sum(prices) / len(prices)
    
    # Calculate price volatility (coefficient of variation)
    variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
    std_dev = variance ** 0.5
    cv = _safe_ratio(std_dev, avg_price) * 100
    
    # Score: lower volatility = higher score
    if cv <= 2:
        return 100.0
    elif cv <= 5:
        return 85.0
    elif cv <= 10:
        return 70.0
    elif cv <= 20:
        return 50.0
    elif cv <= 40:
        return 30.0
    else:
        return 10.0


def _calculate_age_score(symbol: str) -> float:
    """
    Calculate token age score (0-100).
    Older tokens generally more established.
    """
    # For free tier, use first_seen from DexScreener or default
    pair = dex_client.search_pair(symbol)
    if not pair or not pair.pair_created_at:
        return 50.0  # Unknown age, neutral score
    
    try:
        created_at = datetime.fromisoformat(pair.pair_created_at.replace("Z", "+00:00"))
        age_days = (datetime.utcnow() - created_at).days
        
        # Age scoring
        if age_days >= 365:
            return 100.0
        elif age_days >= 180:
            return 85.0
        elif age_days >= 90:
            return 70.0
        elif age_days >= 30:
            return 55.0
        elif age_days >= 7:
            return 40.0
        elif age_days >= 1:
            return 25.0
        else:
            return 10.0  # Very new, high risk
    except Exception:
        return 50.0


def _detect_red_flags(db: Session, symbol: str) -> List[str]:
    """
    Detect potential scam red flags.
    Returns list of warning messages.
    """
    red_flags: List[str] = []
    
    # Check liquidity
    pair = dex_client.search_pair(symbol)
    if pair:
        liquidity = pair.liquidity or {}
        usd_liquidity = float(liquidity.get("usd", 0))
        
        if usd_liquidity < 10_000:
            red_flags.append("Very low liquidity - high rug pull risk")
        
        # Check transaction patterns
        txns = pair.transactions or {}
        h24 = txns.get("h24", {})
        buys = float(h24.get("buys", 0))
        sells = float(h24.get("sells", 0))
        total_txns = buys + sells
        
        if total_txns < 10:
            red_flags.append("Extremely low trading activity")
        
        # Check buy/sell pressure imbalance
        if total_txns > 0:
            sell_ratio = _safe_ratio(sells, total_txns)
            if sell_ratio > 0.8:
                red_flags.append("Heavy selling pressure - potential dump")
        
        # Check age
        if pair.pair_created_at:
            try:
                created_at = datetime.fromisoformat(pair.pair_created_at.replace("Z", "+00:00"))
                age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
                
                if age_hours < 24:
                    red_flags.append("Token less than 24 hours old - extreme risk")
            except Exception:
                pass
    
    # Check price volatility
    cutoff = datetime.utcnow() - timedelta(hours=24)
    records = (
        db.query(MarketData)
        .filter(MarketData.symbol == symbol.upper(), MarketData.timestamp >= cutoff)
        .limit(50)
        .all()
    )
    
    if len(records) >= 10:
        prices = [float(record.close) for record in records]
        max_price = max(prices)
        min_price = min(prices)
        
        if min_price > 0:
            price_swing = _safe_ratio(max_price - min_price, min_price) * 100
            if price_swing > 100:
                red_flags.append(f"Extreme price volatility: {price_swing:.1f}% swing in 24h")
    
    return red_flags


def _classify_health_level(overall_score: float) -> str:
    """Classify token health based on overall score."""
    if overall_score >= 80:
        return "excellent"
    elif overall_score >= 65:
        return "good"
    elif overall_score >= 50:
        return "moderate"
    elif overall_score >= 35:
        return "poor"
    else:
        return "critical"


def _generate_recommendation(overall_score: float, red_flags: List[str]) -> str:
    """Generate investment recommendation based on health analysis."""
    if len(red_flags) >= 3:
        return "AVOID - Multiple red flags detected. High scam risk."
    elif overall_score >= 75 and len(red_flags) == 0:
        return "SAFE - Strong fundamentals. Low risk for investment."
    elif overall_score >= 60:
        return "MODERATE - Decent fundamentals but exercise caution."
    elif overall_score >= 40:
        return "RISKY - Weak fundamentals. Only for experienced traders."
    else:
        return "DANGEROUS - Critical issues detected. Avoid unless you understand the risks."


def calculate_token_health(db: Session, symbol: str) -> Dict:
    """
    Calculate comprehensive token health score.
    
    Returns a dictionary with:
    - overall_score: 0-100 health score
    - health_level: excellent/good/moderate/poor/critical
    - components: individual metric scores
    - red_flags: list of warnings
    - recommendation: investment recommendation
    """
    symbol = symbol.upper()
    
    # Calculate individual component scores
    liquidity_score = _calculate_liquidity_score(symbol)
    volume_score = _calculate_volume_score(symbol)
    holder_score = _calculate_holder_distribution_score(symbol)
    volatility_score = _calculate_volatility_score(db, symbol)
    age_score = _calculate_age_score(symbol)
    
    # Weighted average for overall score
    weights = {
        "liquidity": 0.30,    # Most important - prevents rug pulls
        "volume": 0.25,       # Trading activity
        "volatility": 0.20,   # Price stability
        "holder_distribution": 0.15,  # Whale concentration
        "age": 0.10,          # Establishment
    }
    
    overall_score = (
        liquidity_score * weights["liquidity"]
        + volume_score * weights["volume"]
        + holder_score * weights["holder_distribution"]
        + volatility_score * weights["volatility"]
        + age_score * weights["age"]
    )
    
    # Detect red flags
    red_flags = _detect_red_flags(db, symbol)
    
    # Classify health level
    health_level = _classify_health_level(overall_score)
    
    # Generate recommendation
    recommendation = _generate_recommendation(overall_score, red_flags)
    
    return {
        "symbol": symbol,
        "overall_score": round(overall_score, 2),
        "health_level": health_level,
        "components": {
            "liquidity": round(liquidity_score, 2),
            "volume": round(volume_score, 2),
            "holder_distribution": round(holder_score, 2),
            "volatility": round(volatility_score, 2),
            "age": round(age_score, 2),
        },
        "red_flags": red_flags,
        "recommendation": recommendation,
        "analyzed_at": datetime.utcnow().isoformat(),
    }


def get_cached_token_health(db: Session, symbol: str) -> Dict:
    """Get token health with caching."""
    cache_key = f"token_health:{symbol.upper()}"
    
    def _loader() -> Dict:
        return calculate_token_health(db, symbol)
    
    return cache_result(cache_key, 600, _loader)  # 10-minute cache


def compare_tokens(db: Session, symbols: List[str]) -> List[Dict]:
    """Compare health scores across multiple tokens."""
    results = []
    for symbol in symbols:
        try:
            health = get_cached_token_health(db, symbol)
            results.append(health)
        except Exception:
            # Skip tokens that fail
            continue
    
    # Sort by overall score descending
    results.sort(key=lambda x: x["overall_score"], reverse=True)
    return results
