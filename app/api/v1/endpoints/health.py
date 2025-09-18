from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from prometheus_client import CollectorRegistry, generate_latest

from app.core.responses import success_response
from app.api.v1.dependencies import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Basic health check")
def health_basic():
    return success_response({"status": "healthy"})


@router.get("/detailed", summary="Detailed service status")
def health_detailed(db=Depends(get_db)):
    # Placeholder statuses - in a real system check dependencies
    services = {
        "database": "healthy",
        "redis": "healthy",
        "ml_service": "healthy",
        "data_ingestion": "healthy",
    }
    metrics = {
        "uptime_seconds": 0,
        "total_requests": 0,
        "active_users": 0,
    }
    return success_response({"status": "healthy", "services": services, "metrics": metrics})


@router.get("/status", summary="Service dependency status")
def status():
    return success_response({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@router.get("/metrics", summary="Prometheus metrics", response_model=None)
def metrics():
    registry = CollectorRegistry()
    data = generate_latest(registry)
    return success_response({"metrics": data.decode("utf-8")})
