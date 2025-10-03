from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Callable, TypeVar

from redis import Redis

from app.core.redis import get_redis_client

logger = logging.getLogger("app.cache")

T = TypeVar("T")


def _serialize(value: Any) -> str:
    def _default(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)!r} is not JSON serializable")

    return json.dumps(value, default=_default)


def _deserialize(payload: str) -> Any:
    return json.loads(payload)


def _get_client() -> Redis | None:
    try:
        return get_redis_client()
    except Exception as exc:  # pragma: no cover - defensive safeguard
        logger.debug("Redis connection unavailable: %s", exc)
        return None


def get_cached_value(key: str) -> Any | None:
    client = _get_client()
    if not client:
        return None
    try:
        payload = client.get(key)
    except Exception as exc:  # pragma: no cover - defensive safeguard
        logger.warning("Redis get failed for %s: %s", key, exc)
        return None
    if payload is None:
        return None
    try:
        return _deserialize(payload)
    except json.JSONDecodeError:
        logger.warning("Unable to decode cached payload for key %s", key)
        return None


def set_cached_value(key: str, value: Any, ttl_seconds: int) -> None:
    client = _get_client()
    if not client:
        return
    try:
        client.setex(key, ttl_seconds, _serialize(value))
    except Exception as exc:  # pragma: no cover - defensive safeguard
        logger.warning("Redis set failed for %s: %s", key, exc)


def cache_result(key: str, ttl_seconds: int, loader: Callable[[], T]) -> T:
    cached = get_cached_value(key)
    if cached is not None:
        return cached
    value = loader()
    set_cached_value(key, value, ttl_seconds)
    return value


def invalidate_cache(*keys: str) -> None:
    if not keys:
        return
    client = _get_client()
    if not client:
        return
    for key in keys:
        try:
            client.delete(key)
        except Exception as exc:  # pragma: no cover - defensive safeguard
            logger.warning("Redis delete failed for %s: %s", key, exc)


def invalidate_prefixes(*prefixes: str) -> None:
    client = _get_client()
    if not client:
        return
    for prefix in prefixes:
        if not prefix:
            continue
        pattern = f"{prefix}*"
        try:
            for key in client.scan_iter(pattern):
                client.delete(key)
        except Exception as exc:  # pragma: no cover - defensive safeguard
            logger.warning("Redis scan/delete failed for prefix %s: %s", prefix, exc)
