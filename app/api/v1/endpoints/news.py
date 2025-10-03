"""
News and trending topics endpoints.
"""

from __future__ import annotations


from fastapi import APIRouter, Query

from app.core.responses import success_response
from app.services.news import get_crypto_news, get_trending_topics

router = APIRouter(prefix="/news", tags=["News"])


@router.get("")
async def get_news(
    limit: int = Query(20, ge=1, le=100, description="Number of news items"),
    symbols: str = Query(None, description="Comma-separated list of symbols to filter"),
):
    """
    Get latest crypto news from multiple sources.

    - **limit**: Number of news items to return (1-100)
    - **symbols**: Optional filter by crypto symbols (e.g., "BTC,ETH")
    """
    symbol_list = None
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

    news_items = await get_crypto_news(limit=limit, symbols=symbol_list)

    return success_response(
        {
            "news": [item.to_dict() for item in news_items],
            "count": len(news_items),
        }
    )


@router.get("/trending")
async def get_trending(
    limit: int = Query(10, ge=1, le=50, description="Number of trending topics"),
):
    """
    Get trending topics and hashtags in crypto.

    - **limit**: Number of trending topics to return (1-50)
    """
    topics = await get_trending_topics(limit=limit)

    return success_response(
        {
            "trending": [topic.to_dict() for topic in topics],
            "count": len(topics),
        }
    )
