from datetime import datetime
from typing import List

from pydantic import BaseModel


class CorrelationEntry(BaseModel):
    symbol: str
    correlation: float


class CorrelationMatrix(BaseModel):
    base_symbol: str
    entries: List[CorrelationEntry]
    window_hours: int


class VolatilityMetric(BaseModel):
    symbol: str
    volatility: float
    window_hours: int


class TrendSignal(BaseModel):
    symbol: str
    trend: str
    score: float
    updated_at: datetime


class PatternSignal(BaseModel):
    symbol: str
    pattern: str
    confidence: float
    detected_at: datetime


class PerformanceEntry(BaseModel):
    symbol: str
    return_percent: float
    period: str


class MomentumEntry(BaseModel):
    symbol: str
    momentum_score: float
    classification: str
