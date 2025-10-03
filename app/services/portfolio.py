from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO
from typing import Dict, Iterable, List, Tuple

from sqlalchemy.orm import Session

from app.models.database.portfolio import (
    PortfolioAccount,
    PortfolioHolding,
    PortfolioSnapshot,
)
from app.models.schemas.portfolio import (
    PortfolioAllocationItem,
    PortfolioAllocationResponse,
    PortfolioHoldingView,
    PortfolioHoldingsResponse,
    PortfolioPerformancePoint,
    PortfolioPerformanceResponse,
    PortfolioUploadResult,
)
from app.services.market_data import get_latest_price


REQUIRED_FIELDS = {"asset_symbol", "quantity"}
OPTIONAL_FIELDS = {"cost_basis"}
FIELD_ALIASES = {
    "asset": "asset_symbol",
    "symbol": "asset_symbol",
    "ticker": "asset_symbol",
    "qty": "quantity",
    "amount": "quantity",
    "cost": "cost_basis",
    "price_paid": "cost_basis",
}


def _normalise_headers(headers: Iterable[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for header in headers:
        canonical = FIELD_ALIASES.get(header.strip().lower(), header.strip().lower())
        mapping[header] = canonical
    return mapping


def _parse_decimal(value: str | float | int | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    value = value.strip()
    if not value:
        return None
    try:
        return Decimal(value)
    except Exception:  # pragma: no cover - defensive
        return None


def _aggregate_rows(rows: Iterable[dict]) -> Tuple[List[dict], int]:
    aggregated: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {"quantity": Decimal(0), "cost_basis": Decimal(0)}
    )
    skipped = 0
    for row in rows:
        symbol_raw = row.get("asset_symbol")
        quantity_raw = row.get("quantity")
        if not symbol_raw or quantity_raw in (None, ""):
            skipped += 1
            continue
        symbol = str(symbol_raw).upper().strip()
        quantity = _parse_decimal(quantity_raw)
        if quantity is None:
            skipped += 1
            continue
        cost_basis_value = _parse_decimal(row.get("cost_basis"))
        data = aggregated[symbol]
        data["quantity"] += quantity
        if cost_basis_value is not None:
            data["cost_basis"] += cost_basis_value
    normalized_rows = []
    for symbol, data in aggregated.items():
        normalized_rows.append(
            {
                "asset_symbol": symbol,
                "quantity": data["quantity"],
                "cost_basis": data["cost_basis"] if data["cost_basis"] != 0 else None,
            }
        )
    return normalized_rows, skipped


def parse_portfolio_csv(content: bytes) -> Tuple[List[dict], int]:
    text = content.decode("utf-8")
    reader = csv.DictReader(StringIO(text))
    header_map = _normalise_headers(reader.fieldnames or [])
    normalised_rows: List[dict] = []
    for row in reader:
        normalised: Dict[str, str] = {}
        for key, value in row.items():
            canonical = header_map.get(key)
            if canonical:
                normalised[canonical] = value
        normalised_rows.append(normalised)
    return _aggregate_rows(normalised_rows)


def _get_or_create_csv_account(session: Session, user_id: str) -> PortfolioAccount:
    account = (
        session.query(PortfolioAccount)
        .filter(PortfolioAccount.user_id == user_id, PortfolioAccount.type == "CSV")
        .first()
    )
    if account:
        return account
    account = PortfolioAccount(user_id=user_id, name="CSV Portfolio", type="CSV")
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def upsert_holdings_from_csv(
    session: Session, user_id: str, content: bytes
) -> PortfolioUploadResult:
    rows, skipped = parse_portfolio_csv(content)
    if not rows:
        raise ValueError("No valid rows found in CSV upload")

    account = _get_or_create_csv_account(session, user_id)
    session.query(PortfolioHolding).filter(
        PortfolioHolding.account_id == account.id
    ).delete()
    imported = 0
    for row in rows:
        holding = PortfolioHolding(
            account_id=account.id,
            asset_symbol=row["asset_symbol"],
            quantity=row["quantity"],
            cost_basis=row.get("cost_basis"),
        )
        session.add(holding)
        imported += 1
    session.commit()
    record_snapshot(session, user_id)
    return PortfolioUploadResult(
        account_id=account.id, imported_rows=imported, skipped_rows=skipped
    )


def _convert_decimal(value: Decimal | float | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _compute_holdings_totals(
    holdings: List[PortfolioHoldingView],
) -> Dict[str, Decimal]:
    total_value = sum((holding.market_value or Decimal("0")) for holding in holdings)
    total_cost = sum(
        (_convert_decimal(holding.cost_basis) or Decimal("0"))
        for holding in holdings
        if holding.cost_basis
    )
    total_quantity = sum(holding.quantity for holding in holdings)
    return {
        "total_value": total_value.quantize(Decimal("0.01"))
        if total_value
        else Decimal("0"),
        "total_cost": total_cost.quantize(Decimal("0.01"))
        if total_cost
        else Decimal("0"),
        "total_quantity": total_quantity,
    }


def fetch_holdings(session: Session, user_id: str) -> PortfolioHoldingsResponse:
    account = (
        session.query(PortfolioAccount)
        .filter(PortfolioAccount.user_id == user_id, PortfolioAccount.type == "CSV")
        .first()
    )
    if not account:
        return PortfolioHoldingsResponse(
            account_id="",
            updated_at=datetime.utcnow(),
            holdings=[],
            totals={
                "total_value": Decimal("0"),
                "total_cost": Decimal("0"),
                "total_quantity": Decimal("0"),
            },
        )

    holdings_models = (
        session.query(PortfolioHolding)
        .filter(PortfolioHolding.account_id == account.id)
        .order_by(PortfolioHolding.asset_symbol.asc())
        .all()
    )
    holdings: List[PortfolioHoldingView] = []
    for model in holdings_models:
        market_price = get_latest_price(session, model.asset_symbol)
        price_decimal = Decimal(str(market_price.price)) if market_price else None
        market_value = (
            price_decimal * Decimal(model.quantity)
            if price_decimal is not None
            else None
        )
        cost_basis = Decimal(model.cost_basis) if model.cost_basis is not None else None
        pnl_abs = None
        pnl_pct = None
        if market_value is not None and cost_basis is not None and cost_basis != 0:
            pnl_abs = market_value - cost_basis
            pnl_pct = float((pnl_abs / cost_basis) * 100)
        holdings.append(
            PortfolioHoldingView(
                asset_symbol=model.asset_symbol,
                quantity=Decimal(model.quantity),
                cost_basis=cost_basis,
                market_price=price_decimal,
                market_value=market_value,
                pnl_abs=pnl_abs,
                pnl_pct=pnl_pct,
            )
        )
    totals = _compute_holdings_totals(holdings)
    return PortfolioHoldingsResponse(
        account_id=account.id,
        updated_at=account.updated_at,
        holdings=holdings,
        totals=totals,
    )


def compute_allocation(session: Session, user_id: str) -> PortfolioAllocationResponse:
    holdings_response = fetch_holdings(session, user_id)
    total_value = holdings_response.totals.get("total_value", Decimal("0"))
    allocation: List[PortfolioAllocationItem] = []
    for holding in holdings_response.holdings:
        market_value = holding.market_value or Decimal("0")
        if total_value > 0:
            weight = float((market_value / total_value) * 100)
        else:
            weight = 0.0
        allocation.append(
            PortfolioAllocationItem(
                asset_symbol=holding.asset_symbol,
                market_value=market_value,
                weight_pct=round(weight, 2),
            )
        )
    return PortfolioAllocationResponse(
        account_id=holdings_response.account_id,
        allocation=allocation,
        totals=holdings_response.totals,
    )


def record_snapshot(session: Session, user_id: str) -> PortfolioSnapshot:
    holdings = fetch_holdings(session, user_id)
    total_value = _convert_decimal(holdings.totals.get("total_value"))
    total_cost = _convert_decimal(holdings.totals.get("total_cost"))
    pnl_abs = total_value - total_cost
    pnl_pct = float((pnl_abs / total_cost) * 100) if total_cost else 0.0
    snapshot = PortfolioSnapshot(
        user_id=user_id,
        total_value=total_value,
        pnl_abs=pnl_abs,
        pnl_pct=pnl_pct,
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


WINDOW_TO_DAYS = {"7d": 7, "30d": 30, "90d": 90}


def get_performance(
    session: Session, user_id: str, window: str
) -> PortfolioPerformanceResponse:
    days = WINDOW_TO_DAYS.get(window)
    if days is None:
        raise ValueError("Unsupported window")
    cutoff = datetime.utcnow() - timedelta(days=days)
    snapshots = (
        session.query(PortfolioSnapshot)
        .filter(PortfolioSnapshot.user_id == user_id, PortfolioSnapshot.ts >= cutoff)
        .order_by(PortfolioSnapshot.ts.asc())
        .all()
    )
    points = [
        PortfolioPerformancePoint(
            ts=record.ts,
            total_value=Decimal(record.total_value),
            pnl_abs=Decimal(record.pnl_abs),
            pnl_pct=Decimal(record.pnl_pct),
        )
        for record in snapshots
    ]
    return PortfolioPerformanceResponse(user_id=user_id, window=window, points=points)
