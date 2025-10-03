"""
News aggregation service using free public APIs.
Uses CoinGecko (no API key required) for crypto news.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class NewsItem:
    """Represents a single news article."""

    def __init__(
        self,
        title: str,
        description: str,
        url: str,
        source: str,
        published_at: datetime,
        sentiment: str = "neutral",
        symbols: List[str] | None = None,
    ):
        self.title = title
        self.description = description
        self.url = url
        self.source = source
        self.published_at = published_at
        self.sentiment = sentiment
        self.symbols = symbols or []

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat(),
            "sentiment": self.sentiment,
            "symbols": self.symbols,
        }


class TrendingTopic:
    """Represents a trending topic/hashtag."""

    def __init__(
        self,
        topic: str,
        mentions: int,
        sentiment_score: float,
        change_24h: float,
        related_symbols: List[str] | None = None,
    ):
        self.topic = topic
        self.mentions = mentions
        self.sentiment_score = sentiment_score
        self.change_24h = change_24h
        self.related_symbols = related_symbols or []

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "mentions": self.mentions,
            "sentiment_score": self.sentiment_score,
            "change_24h": self.change_24h,
            "related_symbols": self.related_symbols,
        }


# Cache for news data
_news_cache: List[NewsItem] = []
_news_cache_expiry: datetime | None = None
_trending_cache: List[TrendingTopic] = []
_trending_cache_expiry: datetime | None = None

CACHE_TTL_SECONDS = 300  # 5 minutes for news


def _analyze_sentiment(text: str) -> str:
    """Simple sentiment analysis based on keywords."""
    text_lower = text.lower()

    positive_words = [
        "bullish",
        "surge",
        "rally",
        "gain",
        "up",
        "rise",
        "boost",
        "growth",
        "profit",
        "win",
    ]
    negative_words = [
        "bearish",
        "crash",
        "drop",
        "fall",
        "down",
        "loss",
        "decline",
        "dump",
        "scam",
        "hack",
    ]

    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


def _extract_symbols(text: str) -> List[str]:
    """Extract crypto symbols from text."""
    common_symbols = [
        "BTC",
        "ETH",
        "USDT",
        "BNB",
        "SOL",
        "ADA",
        "DOGE",
        "XRP",
        "DOT",
        "MATIC",
    ]
    symbols_found = []

    text_upper = text.upper()
    for symbol in common_symbols:
        if symbol in text_upper:
            symbols_found.append(symbol)

    return symbols_found


async def fetch_coingecko_news() -> List[NewsItem]:
    """Fetch news from CoinGecko (free, no API key needed)."""
    news_items = []

    try:
        # CoinGecko doesn't have a dedicated news endpoint in free tier
        # So we'll create news from trending coins and market updates
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get trending coins
            trending_url = f"{settings.COINGECKO_BASE_URL}/search/trending"
            response = await client.get(trending_url)

            if response.status_code == 200:
                data = response.json()
                coins = data.get("coins", [])[:5]  # Top 5 trending

                for coin_data in coins:
                    coin = coin_data.get("item", {})
                    symbol = coin.get("symbol", "").upper()
                    name = coin.get("name", "")
                    market_cap_rank = coin.get("market_cap_rank")

                    title = f"{name} ({symbol}) is Trending"
                    description = f"{name} is currently trending in the crypto market. Market cap rank: #{market_cap_rank or 'N/A'}"

                    news_item = NewsItem(
                        title=title,
                        description=description,
                        url=f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                        source="CoinGecko Trending",
                        published_at=datetime.utcnow(),
                        sentiment="positive",
                        symbols=[symbol] if symbol else [],
                    )
                    news_items.append(news_item)

    except Exception as e:
        logger.error(f"Error fetching CoinGecko news: {e}")

    return news_items


async def fetch_generic_crypto_news() -> List[NewsItem]:
    """Generate news items from market data (fallback)."""
    news_items = []

    # Add some general market news based on common topics
    general_news = [
        {
            "title": "Bitcoin Market Update",
            "description": "Latest Bitcoin price movements and market trends. Check the dashboard for real-time data.",
            "symbols": ["BTC"],
            "sentiment": "neutral",
        },
        {
            "title": "Ethereum Network Activity",
            "description": "Ethereum network shows steady transaction volume. Monitor gas fees for optimal timing.",
            "symbols": ["ETH"],
            "sentiment": "neutral",
        },
        {
            "title": "Altcoin Market Analysis",
            "description": "Various altcoins showing interesting price movements. Use our prediction tools for insights.",
            "symbols": ["ADA", "SOL", "DOT"],
            "sentiment": "neutral",
        },
    ]

    for news_data in general_news:
        news_item = NewsItem(
            title=news_data["title"],
            description=news_data["description"],
            url="https://www.coingecko.com",
            source="Market Matrix Analysis",
            published_at=datetime.utcnow(),
            sentiment=news_data["sentiment"],
            symbols=news_data["symbols"],
        )
        news_items.append(news_item)

    return news_items


async def get_crypto_news(
    limit: int = 20, symbols: List[str] | None = None
) -> List[NewsItem]:
    """
    Get aggregated crypto news from multiple free sources.

    Args:
        limit: Maximum number of news items to return
        symbols: Filter by specific crypto symbols (optional)

    Returns:
        List of news items
    """
    global _news_cache, _news_cache_expiry

    now = datetime.utcnow()

    # Check cache
    if _news_cache and _news_cache_expiry and _news_cache_expiry > now:
        news = _news_cache
    else:
        # Fetch fresh news
        all_news = []

        # Try CoinGecko trending
        coingecko_news = await fetch_coingecko_news()
        all_news.extend(coingecko_news)

        # Add generic news
        generic_news = await fetch_generic_crypto_news()
        all_news.extend(generic_news)

        # Update cache
        _news_cache = all_news
        _news_cache_expiry = now + timedelta(seconds=CACHE_TTL_SECONDS)
        news = all_news

    # Filter by symbols if provided
    if symbols:
        symbols_upper = [s.upper() for s in symbols]
        news = [
            item
            for item in news
            if any(symbol in item.symbols for symbol in symbols_upper)
        ]

    # Return limited results
    return news[:limit]


async def get_trending_topics(limit: int = 10) -> List[TrendingTopic]:
    """
    Get trending topics and hashtags in crypto.

    Args:
        limit: Maximum number of topics to return

    Returns:
        List of trending topics
    """
    global _trending_cache, _trending_cache_expiry

    now = datetime.utcnow()

    # Check cache
    if _trending_cache and _trending_cache_expiry and _trending_cache_expiry > now:
        return _trending_cache[:limit]

    # Fetch fresh trending data
    topics = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get trending coins from CoinGecko
            trending_url = f"{settings.COINGECKO_BASE_URL}/search/trending"
            response = await client.get(trending_url)

            if response.status_code == 200:
                data = response.json()
                coins = data.get("coins", [])

                for idx, coin_data in enumerate(coins[:limit]):
                    coin = coin_data.get("item", {})
                    symbol = coin.get("symbol", "").upper()
                    score = coin.get("score", 0)

                    # Create trending topic
                    topic = TrendingTopic(
                        topic=f"#{symbol}",
                        mentions=1000 - (idx * 100),  # Simulated based on rank
                        sentiment_score=0.7 if score > 3 else 0.5,
                        change_24h=10.0 - (idx * 1.5),  # Simulated trend
                        related_symbols=[symbol],
                    )
                    topics.append(topic)

    except Exception as e:
        logger.error(f"Error fetching trending topics: {e}")

        # Fallback trending topics
        topics = [
            TrendingTopic("#BTC", 5000, 0.8, 15.0, ["BTC"]),
            TrendingTopic("#ETH", 3500, 0.7, 12.0, ["ETH"]),
            TrendingTopic("#DeFi", 2000, 0.6, 8.0, ["UNI", "AAVE"]),
        ]

    # Update cache
    _trending_cache = topics
    _trending_cache_expiry = now + timedelta(seconds=CACHE_TTL_SECONDS)

    return topics[:limit]
