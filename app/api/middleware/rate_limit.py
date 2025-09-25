from __future__ import annotations

import json
import time
from typing import Dict, List, Tuple

from fastapi import Request, Response
from redis import Redis
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis import get_redis_client
from app.core.responses import error_response


RateRule = Tuple[str, int, int]


def _parse_rules() -> List[RateRule]:
    rules: List[RateRule] = []
    for entry in settings.REQUEST_RATE_LIMITS:
        try:
            path, config = entry.split(":", 1)
            limit_str, window_str = config.split("/")
            rules.append((path.strip(), int(limit_str), int(window_str)))
        except ValueError:
            continue
    return rules


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.rules = _parse_rules()
        self.redis: Redis | None = None
        try:
            client = get_redis_client()
            client.ping()
            self.redis = client
        except Exception:  # pragma: no cover - fallback for tests
            self.redis = None
        self.counters: Dict[str, Tuple[int, float]] = {}

    def _match_rule(self, path: str) -> RateRule | None:
        for rule_path, limit, window in self.rules:
            if path.startswith(rule_path) or path.startswith(f"{settings.API_V1_STR}{rule_path}"):
                return rule_path, limit, window
        return None

    def _consume_redis(self, rule: RateRule, identifier: str) -> Tuple[bool, int, int]:
        assert self.redis is not None
        key = f"ratelimit:{rule[0]}:{identifier}"
        limit, window = rule[1], rule[2]
        count = self.redis.incr(key)
        if count == 1:
            self.redis.expire(key, window)
        remaining = max(limit - count, 0)
        ttl = self.redis.ttl(key)
        if ttl <= 0:
            ttl = window
        reset = int(time.time()) + ttl
        return count <= limit, remaining, reset

    def _consume_memory(self, rule: RateRule, identifier: str) -> Tuple[bool, int, int]:
        limit, window = rule[1], rule[2]
        now = time.time()
        count, start = self.counters.get(identifier, (0, now))
        if now - start > window:
            count = 0
            start = now
        count += 1
        self.counters[identifier] = (count, start)
        remaining = max(limit - count, 0)
        reset = int(start + window)
        return count <= limit, remaining, reset

    async def dispatch(self, request: Request, call_next) -> Response:
        match = self._match_rule(request.url.path)
        if not match:
            return await call_next(request)

        identifier = request.client.host or "anonymous"
        if self.redis:
            allowed, remaining, reset = self._consume_redis(match, identifier)
        else:
            allowed, remaining, reset = self._consume_memory(match, f"{identifier}:{match[0]}")

        if not allowed:
            payload = error_response(
                code="RATE_LIMIT_EXCEEDED",
                message="Rate limit exceeded. Try again later.",
                status_code=429,
                details={"limit": match[1], "window": match[2]},
            )
            return Response(content=json.dumps(payload), status_code=429, media_type="application/json")

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(match[1])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)
        return response
