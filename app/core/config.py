from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    APP_NAME: str = "CryptoPrediction API"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "sqlite:///./crypto.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "insecure-development-key"
    JWT_SECRET: str = "insecure-development-jwt"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    COINGECKO_API_KEY: str | None = None
    BINANCE_API_KEY: str | None = None
    ALPHA_VANTAGE_KEY: str | None = None
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

    ENABLE_EXTERNAL_MARKET_DATA: bool = False
    MARKET_DATA_LOOKBACK_DAYS: int = 30
    MARKET_DATA_PROVIDER: str = "coingecko"
    DEXSCREENER_ENABLED: bool = True
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    DEXSCREENER_BASE_URL: str = "https://api.dexscreener.com/latest/dex"
    SIMPLE_BOOTSTRAP: bool = False


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
