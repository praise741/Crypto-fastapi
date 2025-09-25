from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class PortfolioUploadResult(BaseModel):
    account_id: str
    imported_rows: int
    skipped_rows: int


class PortfolioHoldingView(BaseModel):
    asset_symbol: str
    quantity: Decimal
    cost_basis: Decimal | None = None
    market_price: Decimal | None = None
    market_value: Decimal | None = None
    pnl_abs: Decimal | None = None
    pnl_pct: Decimal | None = None


class PortfolioHoldingsResponse(BaseModel):
    account_id: str
    updated_at: datetime
    holdings: List[PortfolioHoldingView]
    totals: dict[str, Decimal]


class PortfolioAllocationItem(BaseModel):
    asset_symbol: str
    weight_pct: float = Field(ge=0, le=100)
    market_value: Decimal


class PortfolioAllocationResponse(BaseModel):
    account_id: str
    allocation: List[PortfolioAllocationItem]
    totals: dict[str, Decimal]


class PortfolioPerformancePoint(BaseModel):
    ts: datetime
    total_value: Decimal
    pnl_abs: Decimal
    pnl_pct: Decimal


class PortfolioPerformanceResponse(BaseModel):
    user_id: str
    window: str
    points: List[PortfolioPerformancePoint]
