from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    generate_latest,
)

from app.api.v1.dependencies import get_db
from app.core.config import settings
from app.core.responses import success_response
from app.services.health import run_health_checks

router = APIRouter(prefix="/health", tags=["Health"])

REGISTRY = CollectorRegistry()
REQUEST_COUNTER = Counter(
    "market_matrix_requests_total", "Total API requests", registry=REGISTRY
)
FEATURE_GAUGE = Gauge(
    "market_matrix_features_enabled",
    "Feature flag status",
    ["feature"],
    registry=REGISTRY,
)


@router.get("", summary="Service health overview")
def health_basic(db=Depends(get_db)):
    checks = run_health_checks(db)
    all_healthy = all(status.status == "healthy" for status in checks.values())
    data = {
        "status": "healthy" if all_healthy else "degraded",
        "services": {name: status.status for name, status in checks.items()},
    }
    return success_response(data)


@router.get("/detailed", summary="Detailed dependency check")
def health_detailed(db=Depends(get_db)):
    checks = run_health_checks(db)
    services = {
        name: {"status": status.status, "details": status.details}
        for name, status in checks.items()
    }
    metrics = {
        "features": list(settings.enabled_features),
        "timestamp": datetime.utcnow().isoformat(),
    }
    return success_response(
        {"status": "healthy", "services": services, "metrics": metrics}
    )


@router.get("/status", summary="Timestamped status")
def status(db=Depends(get_db)):
    checks = run_health_checks(db)
    return success_response(
        {
            "status": "healthy"
            if all(s.status == "healthy" for s in checks.values())
            else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@router.get("/metrics", summary="Prometheus metrics", response_class=Response)
def metrics():
    registry = REGISTRY
    for feature in [
        "predictions",
        "dashboard",
        "advanced_tools",
        "web3_health",
        "portfolio",
        "insights",
    ]:
        FEATURE_GAUGE.labels(feature=feature).set(
            1 if getattr(settings, f"FEATURE_{feature.upper()}") else 0
        )
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
