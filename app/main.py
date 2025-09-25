from __future__ import annotations

from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.middleware.authentication import setup_api_key_middleware
from app.api.middleware.cors import setup_cors
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.responses import success_response


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

    setup_cors(app)
    setup_api_key_middleware(app)
    app.add_middleware(RateLimitMiddleware)

    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["Root"])
    async def root():
        return success_response({"message": "Welcome to the CryptoPrediction API", "version": settings.VERSION})

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    return app


app = create_app()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(title=settings.APP_NAME, version=settings.VERSION, routes=app.routes)
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
