from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request

logger = logging.getLogger("app.audit")


def setup_audit_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def audit_logging(request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        response = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            logger.exception(
                "Request failed",
                extra={"method": request.method, "path": request.url.path},
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            api_key_id = getattr(request.state, "api_key_id", None)
            logger.info(
                "audit",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "api_key_id": api_key_id,
                },
            )
        return response
