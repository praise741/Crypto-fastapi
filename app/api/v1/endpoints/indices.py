from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.core.responses import success_response
from app.services.indices import get_index, get_index_history, list_indices

router = APIRouter(prefix="/indices", tags=["Indices"])


@router.get("")
def read_indices(db: Session = Depends(get_db)):
    indices = [index.model_dump() for index in list_indices(db)]
    return success_response({"indices": indices})


@router.get("/{slug}")
def read_index(slug: str, db: Session = Depends(get_db)):
    index = get_index(db, slug)
    if not index:
        raise HTTPException(status_code=404, detail="Index not found")
    return success_response(index.model_dump())


@router.get("/{slug}/history")
def index_history(slug: str, db: Session = Depends(get_db)):
    history = get_index_history(db, slug)
    if not history:
        raise HTTPException(status_code=404, detail="Index not found")
    return success_response(history.model_dump())
