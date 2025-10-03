from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_active_user, get_db
from app.core.features import require_feature
from app.core.responses import success_response
from app.models.database.user import User
from app.services.portfolio import (
    compute_allocation,
    fetch_holdings,
    get_performance,
    upsert_holdings_from_csv,
)


router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/upload")
async def upload_portfolio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    require_feature("portfolio")
    content = await file.read()
    try:
        result = upsert_holdings_from_csv(db, current_user.id, content)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return success_response(result.model_dump())


@router.get("/holdings")
def get_holdings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    require_feature("portfolio")
    holdings = fetch_holdings(db, current_user.id)
    return success_response(holdings.model_dump())


@router.get("/allocation")
def get_allocation(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    require_feature("portfolio")
    allocation = compute_allocation(db, current_user.id)
    return success_response(allocation.model_dump())


@router.get("/performance")
def get_performance_view(
    window: str = Query("30d", pattern="^(7d|30d|90d)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    require_feature("portfolio")
    try:
        performance = get_performance(db, current_user.id, window)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return success_response(performance.model_dump())
