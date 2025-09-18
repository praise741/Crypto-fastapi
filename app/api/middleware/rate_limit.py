from __future__ import annotations

import json
import time
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.responses import error_response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 120, window: int = 60) -> None:
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.counters: Dict[str, Tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        identifier = f"{request.client.host}:{request.url.path}"
        now = time.time()
        count, start = self.counters.get(identifier, (0, now))

        if now - start > self.window:
            count = 0
            start = now

        count += 1
        self.counters[identifier] = (count, start)

        if count > self.limit:
            payload = error_response(
                code="RATE_LIMIT_EXCEEDED",
                message="Rate limit exceeded. Try again later.",
                status_code=429,
                details={"limit": self.limit, "window": self.window},
            )
            return Response(content=json.dumps(payload), status_code=429, media_type="application/json")

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(self.limit - count, 0))
        response.headers["X-RateLimit-Reset"] = str(int(start + self.window))
        return response
