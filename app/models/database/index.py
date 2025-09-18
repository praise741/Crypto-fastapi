from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database.common import BaseModel


class MarketIndex(BaseModel):
    __tablename__ = "market_indices"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class MarketIndexValue(BaseModel):
    __tablename__ = "market_index_values"

    index_id: Mapped[str] = mapped_column(String(36), ForeignKey("market_indices.id"), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    components: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    change_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
