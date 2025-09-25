from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Sequence

import pandas as pd
from prophet import Prophet
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database.market_data import MarketData
from app.models.database.prediction import Prediction
from app.models.schemas.predictions import (
    BatchPredictionRequest,
    ConfidenceInterval,
    PredictionFactor,
    PredictionHistoryItem,
    PredictionHistoryResponse,
    PredictionItem,
    PredictionResponse,
)

from app.models.ml.metadata import MODEL_REGISTRY, ModelMetadata
from app.services.market_data import fetch_market_history, get_latest_price

HORIZON_TO_HOURS: Dict[str, int] = {
    "1h": 1,
    "4h": 4,
    "24h": 24,
    "1d": 24,
    "7d": 24 * 7,
}

MODEL_VERSION = "prophet-1.1.5"
MIN_HISTORY_POINTS = 48


def _format_horizon(hours: int) -> str:
    for key, value in HORIZON_TO_HOURS.items():
        if value == hours:
            return key
    return f"{hours}h"


def _build_prediction_item(record: Prediction, include_confidence: bool, include_factors: bool) -> PredictionItem:
    confidence = None
    if include_confidence and record.confidence_lower is not None and record.confidence_upper is not None:
        confidence = ConfidenceInterval(
            lower=float(record.confidence_lower),
            upper=float(record.confidence_upper),
            confidence=float(record.confidence_score or 0.8),
        )

    probability = None
    if record.accuracy_score is not None:
        probability = {
            "up": float(max(min(record.accuracy_score, 0.99), 0.01)),
            "down": float(max(min(1 - record.accuracy_score, 0.99), 0.01)),
        }

    factors = None
    if include_factors and record.features_used:
        factors = [
            PredictionFactor(name=key, impact=float(value))
            for key, value in sorted(record.features_used.items())
        ]

    return PredictionItem(
        horizon=_format_horizon(record.horizon_hours),
        predicted_price=float(record.predicted_price),
        confidence_interval=confidence,
        probability=probability,
        factors=factors,
        model_version=record.model_version,
        generated_at=record.prediction_time,
    )


def _group_by_horizon(records: Sequence[Prediction]) -> Dict[int, Prediction]:
    grouped: Dict[int, Prediction] = {}
    for record in records:
        if record.horizon_hours not in grouped:
            grouped[record.horizon_hours] = record
    return grouped


def _needs_refresh(records: Sequence[Prediction], target_hours: Sequence[int]) -> bool:
    if not records:
        return True
    grouped = _group_by_horizon(records)
    if not set(target_hours).issubset(grouped.keys()):
        return True
    latest_time = max(record.prediction_time for record in grouped.values())
    return latest_time < datetime.utcnow() - timedelta(minutes=45)


def _fallback_prediction_response(
    symbol: str,
    horizons: Sequence[str] | None,
    include_confidence: bool,
    include_factors: bool,
) -> PredictionResponse:
    now = datetime.utcnow()
    items = []
    for idx, horizon in enumerate(horizons or ["24h"]):
        confidence = (
            ConfidenceInterval(lower=19000, upper=21000, confidence=0.8) if include_confidence else None
        )
        factors = (
            [PredictionFactor(name="momentum", impact=0.25), PredictionFactor(name="volatility", impact=0.15)]
            if include_factors
            else None
        )
        items.append(
            PredictionItem(
                horizon=horizon,
                predicted_price=20000 + idx * 75,
                confidence_interval=confidence,
                probability={"up": 0.55, "down": 0.45},
                factors=factors,
                model_version="simulated",
                generated_at=now,
            )
        )
    return PredictionResponse(symbol=symbol, current_price=20000.0, predictions=items)


def _prepare_training_frame(records: Sequence[MarketData]) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "ds": [record.timestamp for record in records],
            "y": [float(record.close) for record in records],
        }
    )
    df = df.dropna(subset=["ds", "y"]).drop_duplicates(subset="ds")
    df = df.sort_values("ds")
    return df


def _compute_probability(predicted: float, current_price: float) -> float:
    if current_price <= 0:
        return 0.5
    delta = (predicted - current_price) / current_price
    probability_up = 0.5 + max(min(delta * 0.75, 0.45), -0.45)
    return max(min(probability_up, 0.98), 0.02)


def _confidence_score(lower: float, upper: float, baseline: float) -> float:
    width = abs(upper - lower)
    if baseline <= 0:
        return 0.6
    ratio = width / baseline
    score = 1 - min(max(ratio, 0.0), 1.0)
    return max(0.55, min(score, 0.95))


def _persist_prediction(
    db: Session,
    *,
    symbol: str,
    horizon: int,
    generated_at: datetime,
    predicted: float,
    lower: float,
    upper: float,
    features: Dict[str, float],
    probability_up: float,
    confidence_score: float,
    model_version: str,
) -> None:
    db.add(
        Prediction(
            symbol=symbol,
            prediction_time=generated_at,
            horizon_hours=horizon,
            predicted_price=predicted,
            confidence_lower=lower,
            confidence_upper=upper,
            confidence_score=confidence_score,
            model_version=model_version,
            features_used=features,
            actual_price=None,
            accuracy_score=probability_up,
        )
    )


def _generate_moving_average_predictions(
    db: Session,
    symbol: str,
    target_hours: Sequence[int],
    df: pd.DataFrame,
    current_price: float,
    generated_at: datetime,
) -> None:
    for horizon in target_hours:
        window = min(len(df), max(24, horizon * 3))
        window_series = df["y"].tail(window)
        predicted = float(window_series.mean())
        std = float(window_series.std() or max(current_price * 0.02, 1.0))
        lower = predicted - std
        upper = predicted + std
        probability_up = _compute_probability(predicted, current_price)
        confidence_score = _confidence_score(lower, upper, current_price)
        features = {"moving_average": predicted, "volatility": std}
        _persist_prediction(
            db,
            symbol=symbol,
            horizon=horizon,
            generated_at=generated_at,
            predicted=predicted,
            lower=lower,
            upper=upper,
            features=features,
            probability_up=probability_up,
            confidence_score=confidence_score,
            model_version="prophet-ma-fallback",
        )


def _generate_prophet_predictions(db: Session, symbol: str, target_hours: Sequence[int]) -> None:
    symbol = symbol.upper()
    fetch_market_history(db, symbol)
    limit = max(len(target_hours) * 24, settings.MARKET_DATA_LOOKBACK_DAYS * 24, 200)
    records = (
        db.query(MarketData)
        .filter(MarketData.symbol == symbol)
        .order_by(MarketData.timestamp.desc())
        .limit(limit)
        .all()
    )
    records = list(reversed(records))
    if len(records) < MIN_HISTORY_POINTS:
        return

    df = _prepare_training_frame(records)
    if len(df) < MIN_HISTORY_POINTS:
        return

    current_price = float(df["y"].iloc[-1])
    generated_at = datetime.utcnow()
    if settings.SIMPLE_BOOTSTRAP:
        _generate_moving_average_predictions(db, symbol, target_hours, df, current_price, generated_at)
        db.commit()
        return

    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_mode="multiplicative",
        interval_width=0.8,
    )
    try:
        model.fit(df)
    except Exception:
        _generate_moving_average_predictions(db, symbol, target_hours, df, current_price, generated_at)
        db.commit()
        return

    max_horizon = max(target_hours)
    try:
        future = model.make_future_dataframe(periods=max_horizon, freq="H", include_history=False)
        forecast = model.predict(future)
    except Exception:
        _generate_moving_average_predictions(db, symbol, target_hours, df, current_price, generated_at)
        db.commit()
        return
    base_time = df["ds"].iloc[-1]
    forecast["horizon_hours"] = ((forecast["ds"] - base_time) / pd.Timedelta(hours=1)).round().astype(int)

    for horizon in target_hours:
        horizon_frame = forecast[forecast["horizon_hours"] == horizon]
        if horizon_frame.empty:
            continue
        row = horizon_frame.iloc[0]
        predicted = float(row["yhat"])
        lower = float(row.get("yhat_lower", predicted))
        upper = float(row.get("yhat_upper", predicted))
        probability_up = _compute_probability(predicted, current_price)
        confidence_score = _confidence_score(lower, upper, current_price)
        features = {
            "trend": float(row.get("trend", 0.0)),
            "weekly": float(row.get("weekly", 0.0)),
            "daily": float(row.get("daily", 0.0)),
        }

        _persist_prediction(
            db,
            symbol=symbol,
            horizon=horizon,
            generated_at=generated_at,
            predicted=predicted,
            lower=lower,
            upper=upper,
            features=features,
            probability_up=probability_up,
            confidence_score=confidence_score,
            model_version=MODEL_VERSION,
        )

    db.commit()


def get_predictions(
    db: Session,
    symbol: str,
    horizons: Sequence[str] | None = None,
    include_confidence: bool = True,
    include_factors: bool = False,
) -> PredictionResponse:
    symbol = symbol.upper()
    target_hours = [HORIZON_TO_HOURS.get(h, 24) for h in horizons] if horizons else list(HORIZON_TO_HOURS.values())
    target_hours = list(dict.fromkeys(target_hours))
    records = (
        db.query(Prediction)
        .filter(Prediction.symbol == symbol, Prediction.horizon_hours.in_(target_hours))
        .order_by(desc(Prediction.prediction_time))
        .all()
    )
    if _needs_refresh(records, target_hours):
        _generate_prophet_predictions(db, symbol, target_hours)
        records = (
            db.query(Prediction)
            .filter(Prediction.symbol == symbol, Prediction.horizon_hours.in_(target_hours))
            .order_by(desc(Prediction.prediction_time))
            .all()
        )

    grouped = _group_by_horizon(records)
    if not grouped:
        return _fallback_prediction_response(symbol, horizons, include_confidence, include_factors)

    ordered_predictions: List[PredictionItem] = []
    for horizon in target_hours:
        record = grouped.get(horizon)
        if record:
            ordered_predictions.append(
                _build_prediction_item(record, include_confidence, include_factors)
            )

    if not ordered_predictions:
        return _fallback_prediction_response(symbol, horizons, include_confidence, include_factors)

    current_price = get_latest_price(db, symbol).price
    return PredictionResponse(
        symbol=symbol,
        current_price=float(current_price),
        predictions=ordered_predictions,
    )


def get_batch_predictions(db: Session, payload: BatchPredictionRequest, include_confidence: bool = True) -> List[PredictionResponse]:
    responses = []
    for symbol in payload.symbols:
        responses.append(
            get_predictions(
                db,
                symbol=symbol,
                horizons=payload.horizons,
                include_confidence=include_confidence,
                include_factors=False,
            )
        )
    return responses


def get_prediction_history(
    db: Session,
    symbol: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    include_accuracy: bool = True,
    limit: int | None = None,
) -> PredictionHistoryResponse:
    symbol = symbol.upper()
    query = db.query(Prediction).filter(Prediction.symbol == symbol)
    if start_date:
        query = query.filter(Prediction.prediction_time >= start_date)
    if end_date:
        query = query.filter(Prediction.prediction_time <= end_date)
    query = query.order_by(desc(Prediction.prediction_time))
    if limit:
        query = query.limit(limit)
    records = query.all()
    items = [
        PredictionHistoryItem(
            prediction_time=record.prediction_time,
            horizon=_format_horizon(record.horizon_hours),
            predicted_price=float(record.predicted_price),
            actual_price=float(record.actual_price) if record.actual_price is not None else None,
            accuracy_score=float(record.accuracy_score) if include_accuracy and record.accuracy_score is not None else None,
        )
        for record in records
    ]
    return PredictionHistoryResponse(symbol=symbol, items=items)


def list_models() -> List[ModelMetadata]:
    return list(MODEL_REGISTRY.values())


def get_model(model_id: str) -> ModelMetadata | None:
    return MODEL_REGISTRY.get(model_id)

