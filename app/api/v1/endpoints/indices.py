from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.core.http import apply_cache_headers
from app.core.responses import success_response
from app.services.indices import get_index, get_index_history, list_indices

router = APIRouter(prefix="/indices", tags=["Indices"])


@router.get("")
def read_indices(db: Session = Depends(get_db)):
    indices = [index.model_dump() for index in list_indices(db)]
    return success_response({"indices": indices})


def _get_index_or_404(slug: str, db: Session) -> dict:
    index = get_index(db, slug)
    if not index:
        raise HTTPException(status_code=404, detail="Index not found")
    return index.model_dump()


@router.get("/altseason")
def read_altseason(response: Response, db: Session = Depends(get_db)):
    payload = _get_index_or_404("altseason", db)
    apply_cache_headers(response, 300)
    return success_response(payload)


@router.get("/fear-greed")
def read_fear_greed(response: Response, db: Session = Depends(get_db)):
    payload = _get_index_or_404("fear-greed", db)
    apply_cache_headers(response, 300)
    return success_response(payload)


@router.get("/dominance")
def read_dominance(response: Response, db: Session = Depends(get_db)):
    payload = _get_index_or_404("dominance", db)
    apply_cache_headers(response, 300)
    return success_response(payload)


@router.get("/{slug}")
def read_index(slug: str, db: Session = Depends(get_db)):
    return success_response(_get_index_or_404(slug, db))


@router.get("/{slug}/history")
def index_history(slug: str, db: Session = Depends(get_db)):
    history = get_index_history(db, slug)
    if not history:
        raise HTTPException(status_code=404, detail="Index not found")
    return success_response(history.model_dump())
