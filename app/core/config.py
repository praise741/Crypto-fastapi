from functools import lru_cache
from typing import List, Sequence

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    APP_NAME: str = "CryptoPrediction API"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.2.0"

    DATABASE_URL: str = "sqlite:///./crypto.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "insecure-development-key"
    JWT_SECRET: str = "insecure-development-jwt"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    COINGECKO_API_KEY: str | None = None
    BINANCE_API_KEY: str | None = None
    ALPHA_VANTAGE_KEY: str | None = None
    REDDIT_CLIENT_ID: str | None = None
    REDDIT_CLIENT_SECRET: str | None = None
    REDDIT_USER_AGENT: str = "market-matrix/0.1"
    TRANSFORMERS_LOCAL: bool = False
    OPENAI_API_KEY: str | None = None
    SENTRY_DSN: str | None = None
    STRIPE_SECRET_KEY: str | None = None
    WEBHOOK_SECRET: str | None = None

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    SUPPORTED_SYMBOLS: List[str] = ["BTC", "ETH", "SOL", "ADA", "XRP"]
    DEFAULT_TIMEZONE: str = "UTC"

    # Feature flags (defaults mirror free-tier scope)
    FEATURE_PREDICTIONS: bool = True
    FEATURE_DASHBOARD: bool = True
    FEATURE_ADVANCED_TOOLS: bool = True
    FEATURE_WEB3_HEALTH: bool = True
    FEATURE_PORTFOLIO: bool = False
    FEATURE_INSIGHTS: bool = False
    FEATURE_WALLET: bool = False

    DATA_LIVE: bool = False

    ENABLE_EXTERNAL_MARKET_DATA: bool = False
    MARKET_DATA_LOOKBACK_DAYS: int = 30
    MARKET_DATA_PROVIDER: str = "coingecko"
    DEXSCREENER_ENABLED: bool = True
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    DEXSCREENER_BASE_URL: str = "https://api.dexscreener.com/latest/dex"
    BINANCE_BASE_URL: str = "https://api.binance.com/api/v3"
    SIMPLE_BOOTSTRAP: bool = False

    REQUEST_RATE_LIMITS: List[str] = ["/predictions:60/60", "/portfolio/upload:5/60"]
    CACHE_TTL_SECONDS: int = 60

    INSIGHTS_DEFAULT_WINDOW: str = "24h"
    INSIGHTS_DEX_TREND_WINDOW_MINUTES: int = 120

    PORTFOLIO_SNAPSHOT_SCHEDULE_CRON: str = "0 2 * * *"

    COMMUNITY_SUBREDDITS: List[str] = ["CryptoCurrency", "Bitcoin", "CryptoMarkets"]

    PROMETHEUS_METRIC_NAMESPACE: str = "market_matrix"

    @computed_field
    @property
    def enabled_features(self) -> Sequence[str]:  # pragma: no cover - trivial
        flags = {
            "predictions": self.FEATURE_PREDICTIONS,
            "dashboard": self.FEATURE_DASHBOARD,
            "advanced_tools": self.FEATURE_ADVANCED_TOOLS,
            "web3_health": self.FEATURE_WEB3_HEALTH,
            "portfolio": self.FEATURE_PORTFOLIO,
            "insights": self.FEATURE_INSIGHTS,
            "wallet": self.FEATURE_WALLET,
        }
        return tuple(name for name, enabled in flags.items() if enabled)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
