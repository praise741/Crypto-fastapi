from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.core.http import apply_cache_headers
from app.core.responses import success_response
from app.services.analytics import (
    correlation_matrix,
    momentum_leaders,
    pattern_signals,
    performance_leaders,
    trend_signals,
    volatility_metrics,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/correlations")
def correlations(response: Response, db: Session = Depends(get_db)):
    matrix = correlation_matrix(db)
    apply_cache_headers(response, 300)
    return success_response(matrix.model_dump())


@router.get("/volatility")
def volatility(response: Response, db: Session = Depends(get_db)):
    metrics = [metric.model_dump() for metric in volatility_metrics(db)]
    apply_cache_headers(response, 300)
    return success_response({"metrics": metrics})


@router.get("/trends")
def trends(db: Session = Depends(get_db)):
    signals = [signal.model_dump() for signal in trend_signals(db)]
    return success_response({"signals": signals})


@router.get("/patterns")
def patterns(db: Session = Depends(get_db)):
    signals = [signal.model_dump() for signal in pattern_signals(db)]
    return success_response({"signals": signals})


@router.get("/top-performers")
def top_performers(response: Response, db: Session = Depends(get_db)):
    entries = [entry.model_dump() for entry in performance_leaders(db)]
    apply_cache_headers(response, 300)
    return success_response({"assets": entries})


@router.get("/momentum")
def momentum(response: Response, db: Session = Depends(get_db)):
    entries = [entry.model_dump() for entry in momentum_leaders(db)]
    apply_cache_headers(response, 300)
    return success_response({"leaders": entries})
