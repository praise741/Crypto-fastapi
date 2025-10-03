from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import httpx
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis import get_redis_client


@dataclass
class HealthStatus:
    name: str
    status: str
    details: Dict[str, str] | None = None


def _check_database(session: Session) -> HealthStatus:
    try:
        session.execute("SELECT 1")
        return HealthStatus(name="database", status="healthy")
    except Exception as exc:  # pragma: no cover - defensive
        return HealthStatus(
            name="database", status="degraded", details={"error": str(exc)}
        )


def _check_redis() -> HealthStatus:
    try:
        client: Redis = get_redis_client()
        client.ping()
        return HealthStatus(name="redis", status="healthy")
    except Exception as exc:  # pragma: no cover
        return HealthStatus(
            name="redis", status="degraded", details={"error": str(exc)}
        )


def _check_http_endpoint(name: str, url: str) -> HealthStatus:
    try:
        response = httpx.get(url, timeout=5.0)
        if response.status_code < 500:
            return HealthStatus(name=name, status="healthy")
        return HealthStatus(
            name=name, status="degraded", details={"status": str(response.status_code)}
        )
    except Exception as exc:  # pragma: no cover
        return HealthStatus(name=name, status="degraded", details={"error": str(exc)})


def run_health_checks(session: Session) -> Dict[str, HealthStatus]:
    checks = {
        "database": _check_database(session),
        "redis": _check_redis(),
        "coingecko": _check_http_endpoint(
            "coingecko", f"{settings.COINGECKO_BASE_URL}/ping"
        ),
        "binance": _check_http_endpoint("binance", f"{settings.BINANCE_BASE_URL}/ping"),
    }
    if settings.DEXSCREENER_ENABLED:
        checks["dexscreener"] = _check_http_endpoint(
            "dexscreener", f"{settings.DEXSCREENER_BASE_URL}/search?q=eth"
        )
    return checks
