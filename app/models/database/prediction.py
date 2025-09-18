from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database.common import BaseModel


class Prediction(BaseModel):
    __tablename__ = "predictions"

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    prediction_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_price: Mapped[float] = mapped_column(DECIMAL(20, 8), nullable=False)
    confidence_lower: Mapped[float | None] = mapped_column(DECIMAL(20, 8), nullable=True)
    confidence_upper: Mapped[float | None] = mapped_column(DECIMAL(20, 8), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(DECIMAL(3, 2), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    features_used: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actual_price: Mapped[float | None] = mapped_column(DECIMAL(20, 8), nullable=True)
    accuracy_score: Mapped[float | None] = mapped_column(DECIMAL(3, 2), nullable=True)
