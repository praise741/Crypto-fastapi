from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database.common import BaseModel


class InsightEvent(BaseModel):
    __tablename__ = "insight_events"

    ts: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True, nullable=False
    )
    source: Mapped[str] = mapped_column(
        Enum("PROXY", "REDDIT", name="insight_event_source"), nullable=False
    )
    asset_symbol: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    text_excerpt: Mapped[str] = mapped_column(String(512), nullable=False)
    sentiment_score: Mapped[float] = mapped_column(
        Numeric(precision=6, scale=3), nullable=False
    )
    meta: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(String, "sqlite"), nullable=True
    )


Index("ix_insight_events_symbol_ts", InsightEvent.asset_symbol, InsightEvent.ts.desc())
Index("ix_insight_events_source", InsightEvent.source)
