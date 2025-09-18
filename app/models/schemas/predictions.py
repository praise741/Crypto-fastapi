from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ConfidenceInterval(BaseModel):
    lower: float
    upper: float
    confidence: float


class PredictionFactor(BaseModel):
    name: str
    impact: float


class PredictionItem(BaseModel):
    horizon: str
    predicted_price: float
    confidence_interval: Optional[ConfidenceInterval] = None
    probability: dict | None = None
    factors: List[PredictionFactor] | None = None
    model_version: str | None = None
    generated_at: datetime


class PredictionResponse(BaseModel):
    symbol: str
    current_price: float | None = None
    predictions: List[PredictionItem]


class BatchPredictionRequest(BaseModel):
    symbols: List[str]
    horizons: List[str]


class PredictionHistoryItem(BaseModel):
    prediction_time: datetime
    horizon: str
    predicted_price: float
    actual_price: float | None = None
    accuracy_score: float | None = None


class PredictionHistoryResponse(BaseModel):
    symbol: str
    items: List[PredictionHistoryItem]
