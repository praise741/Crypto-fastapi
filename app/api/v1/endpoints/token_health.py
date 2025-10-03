from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.core.http import apply_cache_headers
from app.core.responses import success_response
from app.services.token_health import compare_tokens, get_cached_token_health


router = APIRouter(prefix="/token-health", tags=["Token Health"])


@router.get("/{symbol}")
def get_token_health(
    http_response: Response,
    symbol: str,
    db: Session = Depends(get_db),
):
    """
    Get comprehensive health score for a token.

    **Solves Market Matrix Problem #3: Falling into Scams & Weak Projects**

    Analyzes:
    - **Liquidity**: Prevents rug pulls (30% weight)
    - **Trading Volume**: Activity and market interest (25% weight)
    - **Holder Distribution**: Whale concentration risk (15% weight)
    - **Price Volatility**: Stability indicator (20% weight)
    - **Token Age**: Establishment and maturity (10% weight)

    Returns:
    - Overall health score (0-100)
    - Health level classification
    - Individual component scores
    - Red flags warnings
    - Investment recommendation

    Example response:
    ```json
    {
      "symbol": "BTC",
      "overall_score": 87.5,
      "health_level": "excellent",
      "components": {
        "liquidity": 100.0,
        "volume": 100.0,
        "holder_distribution": 75.0,
        "volatility": 70.0,
        "age": 100.0
      },
      "red_flags": [],
      "recommendation": "SAFE - Strong fundamentals. Low risk for investment.",
      "analyzed_at": "2024-01-15T10:00:00Z"
    }
    ```
    """
    health = get_cached_token_health(db, symbol)
    apply_cache_headers(http_response, 600)
    return success_response(health)


@router.post("/compare")
def compare_token_health(
    symbols: List[str],
    http_response: Response,
    db: Session = Depends(get_db),
):
    """
    Compare health scores across multiple tokens.

    **Use Case**: Quickly identify the safest investment among alternatives.

    Request body:
    ```json
    ["BTC", "ETH", "SHIB", "DOGE"]
    ```

    Returns tokens sorted by health score (best to worst).
    Maximum 20 tokens per request.
    """
    if not symbols or len(symbols) > 20:
        return success_response({"error": "Provide 1-20 symbols"}, status_code=400)

    comparison = compare_tokens(db, symbols)
    apply_cache_headers(http_response, 600)
    return success_response({"tokens": comparison})


@router.get("/{symbol}/quick")
def quick_health_check(
    symbol: str,
    db: Session = Depends(get_db),
):
    """
    Quick health check - returns only score and recommendation.

    **Fast Response**: Returns minimal data for quick decisions.

    Perfect for:
    - Mobile apps
    - Quick scans
    - Trading bots
    """
    health = get_cached_token_health(db, symbol)
    return success_response(
        {
            "symbol": health["symbol"],
            "score": health["overall_score"],
            "level": health["health_level"],
            "recommendation": health["recommendation"],
        }
    )
