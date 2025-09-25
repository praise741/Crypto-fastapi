from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database.common import BaseModel


class PortfolioAccount(BaseModel):
    __tablename__ = "portfolio_accounts"

    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(Enum("CSV", name="portfolio_account_type"), nullable=False)

    holdings: Mapped[list["PortfolioHolding"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", lazy="selectin"
    )


class PortfolioHolding(BaseModel):
    __tablename__ = "portfolio_holdings"

    account_id: Mapped[str] = mapped_column(ForeignKey("portfolio_accounts.id", ondelete="CASCADE"), nullable=False)
    asset_symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(precision=24, scale=10), nullable=False)
    cost_basis: Mapped[float | None] = mapped_column(Numeric(precision=24, scale=10), nullable=True)

    account: Mapped[PortfolioAccount] = relationship(back_populates="holdings")


class PortfolioSnapshot(BaseModel):
    __tablename__ = "portfolio_snapshots"

    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    total_value: Mapped[float] = mapped_column(Numeric(precision=24, scale=10), nullable=False)
    pnl_abs: Mapped[float] = mapped_column(Numeric(precision=24, scale=10), nullable=False)
    pnl_pct: Mapped[float] = mapped_column(Numeric(precision=12, scale=6), nullable=False)


Index(
    "ix_portfolio_holdings_user_asset",
    PortfolioHolding.account_id,
    PortfolioHolding.asset_symbol,
)
