from typing import Optional

from fastapi import FastAPI, Request

from app.core.config import settings

API_KEY_HEADER = "X-API-Key"


def setup_api_key_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def api_key_authentication(request: Request, call_next):
        api_key: Optional[str] = request.headers.get(API_KEY_HEADER)
        request.state.api_key = api_key
        return await call_next(request)
