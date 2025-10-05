from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status

from app.core.config import settings
from app.services.security import verify_api_key_from_pool

API_KEY_HEADER = "X-API-Key"
PUBLIC_PATHS: tuple[str, ...] = (
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    # Make all health endpoints public
    f"{settings.API_V1_STR}/health",
    f"{settings.API_V1_STR}/auth",
    f"{settings.API_V1_STR}/auth/register",
    f"{settings.API_V1_STR}/auth/login",
    f"{settings.API_V1_STR}/auth/refresh",
)


def _is_public(path: str) -> bool:
    normalized = path.rstrip("/") or "/"
    return any(
        normalized == route or normalized.startswith(f"{route}/")
        for route in PUBLIC_PATHS
    )


def setup_api_key_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def api_key_authentication(request: Request, call_next):
        path = request.url.path
        # Treat health endpoints as public first, then the general list
        if path.startswith(f"{settings.API_V1_STR}/health") or _is_public(path):
            return await call_next(request)

        api_key_header: Optional[str] = request.headers.get(API_KEY_HEADER)
        if not api_key_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key",
            )

        record = verify_api_key_from_pool(api_key_header)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )

        request.state.api_key = record
        request.state.api_key_id = record.id
        return await call_next(request)
