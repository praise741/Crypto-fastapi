from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database.common import BaseModel


class TrackedSymbol(BaseModel):
    """Symbols that have been explicitly onboarded by administrators."""

    __tablename__ = "tracked_symbols"

    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    added_by_api_key_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("api_keys.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
