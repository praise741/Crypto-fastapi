from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.core.features import require_feature
from app.core.http import apply_cache_headers
from app.core.responses import success_response
from app.models.schemas.predictions import BatchPredictionRequest
from app.services.prediction import (
    get_cached_predictions,
    get_batch_predictions,
    get_model,
    get_prediction_history,
    list_models,
)


router = APIRouter(prefix="/predictions", tags=["Predictions"])
models_router = APIRouter(prefix="/models", tags=["Models"])


@router.get("")
def query_predictions(
    http_response: Response,
    symbol: str = Query(..., min_length=1),
    horizon: List[str] | None = Query(None, alias="horizon"),
    include_confidence: bool = Query(True),
    include_factors: bool = Query(False),
    db: Session = Depends(get_db),
):
    require_feature("predictions")
    prediction = get_cached_predictions(
        db,
        symbol=symbol,
        horizons=horizon,
        include_confidence=include_confidence,
        include_factors=include_factors,
    )
    apply_cache_headers(http_response, 3600)
    return success_response(prediction.model_dump())


@router.get("/{symbol}")
def read_predictions(
    http_response: Response,
    symbol: str,
    horizons: List[str] | None = Query(None),
    include_confidence: bool = Query(True),
    include_factors: bool = Query(False),
    db: Session = Depends(get_db),
):
    require_feature("predictions")
    prediction = get_cached_predictions(
        db,
        symbol=symbol,
        horizons=horizons,
        include_confidence=include_confidence,
        include_factors=include_factors,
    )
    apply_cache_headers(http_response, 3600)
    return success_response(prediction.model_dump())


@router.post("/batch")
def batch_predictions(
    payload: BatchPredictionRequest,
    http_response: Response,
    db: Session = Depends(get_db),
):
    require_feature("predictions")
    responses = [item.model_dump() for item in get_batch_predictions(db, payload)]
    apply_cache_headers(http_response, 3600)
    return success_response({"predictions": responses})


@router.get("/history")
def prediction_history_query(
    symbol: str = Query(..., min_length=1),
    limit: int = Query(100, ge=1, le=500),
    include_accuracy: bool = Query(True),
    db: Session = Depends(get_db),
):
    require_feature("predictions")
    response = get_prediction_history(
        db,
        symbol=symbol,
        include_accuracy=include_accuracy,
        limit=limit,
    )
    return success_response(response.model_dump())


@router.get("/{symbol}/history")
def prediction_history(
    symbol: str,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    include_accuracy: bool = Query(True),
    db: Session = Depends(get_db),
):
    require_feature("predictions")
    response = get_prediction_history(
        db,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        include_accuracy=include_accuracy,
    )
    return success_response(response.model_dump())


@models_router.get("")
def list_model_metadata():
    models = [
        {
            "model_id": model.model_id,
            "version": model.version,
            "symbol": model.symbol,
            "type": model.model_type,
            "metrics": model.metrics,
            "features": model.features,
            "last_updated": model.last_updated.isoformat(),
        }
        for model in list_models()
    ]
    return success_response({"models": models})


@models_router.get("/{model_id}")
def model_detail(model_id: str):
    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return success_response(
        {
            "model_id": model.model_id,
            "version": model.version,
            "symbol": model.symbol,
            "type": model.model_type,
            "metrics": model.metrics,
            "features": model.features,
            "last_updated": model.last_updated.isoformat(),
        }
    )


@models_router.get("/{model_id}/metrics")
def model_metrics(model_id: str):
    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return success_response({"model_id": model.model_id, "metrics": model.metrics})
