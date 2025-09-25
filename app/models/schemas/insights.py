from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class InsightComponent(BaseModel):
    name: str
    value: float
    trend: float | None = None


class InsightSummary(BaseModel):
    symbol: str
    window: str
    proxy_score: float = Field(ge=-1.0, le=1.0)
    reddit_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    score_avg: float = Field(ge=-1.0, le=1.0)
    score_trend: float | None = Field(default=None, ge=-1.0, le=1.0)
    counts_by_source: dict[str, int]
    components: List[InsightComponent]


class InsightEventView(BaseModel):
    id: str
    ts: datetime
    source: str
    asset_symbol: str
    text_excerpt: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)


class InsightEventsResponse(BaseModel):
    symbol: str
    events: List[InsightEventView]
