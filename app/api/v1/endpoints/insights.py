from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.core.features import require_feature
from app.core.responses import success_response
from app.services.insights import list_events, summarise_insights


router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/summary")
def get_insight_summary(
    symbol: str = Query(..., min_length=1),
    window: str = Query("24h"),
    db: Session = Depends(get_db),
):
    require_feature("insights")
    try:
        summary = summarise_insights(db, symbol, window)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    return success_response(summary.model_dump())


@router.get("/events")
def get_insight_events(
    symbol: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    require_feature("insights")
    events = list_events(db, symbol, limit)
    return success_response(events.model_dump())
