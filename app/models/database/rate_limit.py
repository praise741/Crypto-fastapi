from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database.common import BaseModel


class RateLimit(BaseModel):
    __tablename__ = "rate_limits"

    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    plan_limit: Mapped[int] = mapped_column(Integer, nullable=False)
