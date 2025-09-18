from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.database.index import MarketIndex, MarketIndexValue
from app.models.schemas.indices import IndexHistoryItem, IndexHistoryResponse, IndexResponse

DEFAULT_INDICES = {
    "altseason": "Altseason Index",
    "fear-greed": "Fear & Greed Index",
    "dominance": "Market Dominance",
}


def _ensure_index(db: Session, slug: str, name: str) -> MarketIndex:
    index = db.query(MarketIndex).filter(MarketIndex.slug == slug).first()
    if index:
        return index
    index = MarketIndex(slug=slug, name=name)
    db.add(index)
    db.commit()
    db.refresh(index)
    value = MarketIndexValue(
        index_id=index.id,
        value=60,
        components={"volatility": 70, "momentum": 60, "volume": 55, "social": 50},
        classification="neutral",
        change_24h=2,
        timestamp=datetime.utcnow(),
    )
    db.add(value)
    db.commit()
    return index


def list_indices(db: Session) -> List[IndexResponse]:
    responses: List[IndexResponse] = []
    for slug, name in DEFAULT_INDICES.items():
        index = _ensure_index(db, slug, name)
        latest = (
            db.query(MarketIndexValue)
            .filter(MarketIndexValue.index_id == index.id)
            .order_by(desc(MarketIndexValue.timestamp))
            .first()
        )
        responses.append(
            IndexResponse(
                index=slug,
                value=float(latest.value if latest else 0),
                classification=latest.classification if latest else "neutral",
                components=latest.components if latest else {},
                timestamp=latest.timestamp if latest else datetime.utcnow(),
                change_24h=float(latest.change_24h or 0) if latest else 0,
            )
        )
    return responses


def get_index(db: Session, slug: str) -> IndexResponse | None:
    name = DEFAULT_INDICES.get(slug)
    if not name:
        return None
    index = _ensure_index(db, slug, name)
    latest = (
        db.query(MarketIndexValue)
        .filter(MarketIndexValue.index_id == index.id)
        .order_by(desc(MarketIndexValue.timestamp))
        .first()
    )
    if not latest:
        return None
    return IndexResponse(
        index=slug,
        value=float(latest.value),
        classification=latest.classification,
        components=latest.components,
        timestamp=latest.timestamp,
        change_24h=float(latest.change_24h or 0),
    )


def get_index_history(db: Session, slug: str) -> IndexHistoryResponse | None:
    name = DEFAULT_INDICES.get(slug)
    if not name:
        return None
    index = _ensure_index(db, slug, name)
    values = (
        db.query(MarketIndexValue)
        .filter(MarketIndexValue.index_id == index.id)
        .order_by(desc(MarketIndexValue.timestamp))
        .limit(30)
        .all()
    )
    items = [
        IndexHistoryItem(
            timestamp=value.timestamp,
            value=float(value.value),
            change_24h=float(value.change_24h or 0),
            components=value.components,
        )
        for value in values
    ]
    return IndexHistoryResponse(index=slug, items=items)
