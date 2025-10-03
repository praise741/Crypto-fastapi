from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database.common import BaseModel


class MarketData(BaseModel):
    __tablename__ = "market_data"
    __table_args__ = (
        Index("idx_market_data_symbol_timestamp", "symbol", "timestamp"),
        Index("idx_market_data_timestamp", "timestamp"),
    )

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open: Mapped[float | None] = mapped_column(DECIMAL(20, 8), nullable=True)
    high: Mapped[float | None] = mapped_column(DECIMAL(20, 8), nullable=True)
    low: Mapped[float | None] = mapped_column(DECIMAL(20, 8), nullable=True)
    close: Mapped[float] = mapped_column(DECIMAL(20, 8), nullable=False)
    volume: Mapped[float | None] = mapped_column(DECIMAL(20, 8), nullable=True)
    market_cap: Mapped[float | None] = mapped_column(DECIMAL(20, 2), nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
