from __future__ import annotations

from datetime import datetime, timedelta
from statistics import fmean
from typing import Dict, Iterable, List

import pandas as pd
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.cache import cache_result
from app.models.database.market_data import MarketData
from app.models.schemas.analytics import (
    CorrelationEntry,
    CorrelationMatrix,
    MomentumEntry,
    PatternSignal,
    PerformanceEntry,
    TrendSignal,
    VolatilityMetric,
)
from app.services.market_data import list_symbols

CORRELATION_WINDOW_HOURS = 72
VOLATILITY_WINDOW_HOURS = 24
PERFORMANCE_WINDOW_HOURS = 72
PATTERN_WINDOW_HOURS = 48
MOMENTUM_SHORT_WINDOW = 6
MOMENTUM_LONG_WINDOW = 18


def _load_close_prices(session: Session, symbols: Iterable[str], window_hours: int) -> Dict[str, List[float]]:
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    closes: Dict[str, List[float]] = {}
    for symbol in symbols:
        rows = (
            session.query(MarketData)
            .filter(MarketData.symbol == symbol.upper(), MarketData.timestamp >= cutoff)
            .order_by(MarketData.timestamp.asc())
            .all()
        )
        if rows:
            closes[symbol.upper()] = [float(row.close) for row in rows]
    return closes


def _load_series(session: Session, symbol: str, window_hours: int) -> pd.Series | None:
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    rows = (
        session.query(MarketData)
        .filter(MarketData.symbol == symbol.upper(), MarketData.timestamp >= cutoff)
        .order_by(MarketData.timestamp.asc())
        .all()
    )
    if not rows:
        return None
    closes = [float(row.close) for row in rows]
    index = [row.timestamp for row in rows]
    return pd.Series(closes, index=index)


def _recent_timestamp(series: pd.Series) -> datetime:
    value = series.index[-1]
    return value.to_pydatetime() if hasattr(value, "to_pydatetime") else value


def _classify_pattern(series: pd.Series) -> tuple[str, float]:
    if len(series) < 5:
        return "consolidation", 0.35

    recent = series.tail(8)
    momentum = recent.diff().dropna()
    if momentum.empty:
        return "consolidation", 0.35

    gains = (momentum > 0).sum()
    losses = (momentum < 0).sum()
    slope = fmean(momentum) if momentum.any() else 0.0
    magnitude = abs(slope) / max(float(recent.iloc[-2] or 1.0), 1.0)

    if gains and not losses:
        return "breakout", min(round(magnitude * 4, 2), 0.95)
    if losses and not gains:
        return "breakdown", min(round(magnitude * 4, 2), 0.95)

    swing = recent.max() - recent.min()
    range_ratio = swing / max(float(recent.mean() or 1.0), 1.0)
    if range_ratio < 0.01:
        return "consolidation", 0.4
    if abs(slope) < (range_ratio / 2):
        return "range_bound", min(round(range_ratio * 3, 2), 0.9)
    return "mean_reversion", min(round((range_ratio + magnitude) * 2, 2), 0.9)


def _compute_correlation(session: Session) -> CorrelationMatrix:
    symbols = [symbol.symbol for symbol in list_symbols(session)][:8]
    series = _load_close_prices(session, symbols, CORRELATION_WINDOW_HOURS)
    if len(series) < 2:
        entries = [CorrelationEntry(symbol=symbol, correlation=1.0) for symbol in symbols]
        return CorrelationMatrix(base_symbol=symbols[0] if symbols else "BTC", entries=entries, window_hours=CORRELATION_WINDOW_HOURS)

    df = pd.DataFrame({key: values for key, values in series.items()})
    df = df.dropna(axis=1, how="all")
    if df.empty:
        entries = [CorrelationEntry(symbol=symbol, correlation=1.0) for symbol in series.keys()]
        return CorrelationMatrix(base_symbol="BTC", entries=entries, window_hours=CORRELATION_WINDOW_HOURS)

    base_symbol = df.columns[0]
    correlations = df.corr().get(base_symbol, pd.Series())
    entries = [
        CorrelationEntry(symbol=col, correlation=float(round(corr, 4)))
        for col, corr in correlations.items()
    ]
    return CorrelationMatrix(base_symbol=base_symbol, entries=entries, window_hours=CORRELATION_WINDOW_HOURS)


def correlation_matrix(session: Session) -> CorrelationMatrix:
    def _loader() -> Dict[str, List[dict]]:
        matrix = _compute_correlation(session)
        return matrix.model_dump()

    payload = cache_result("analytics:correlations", 300, _loader)
    return CorrelationMatrix(**payload)


def volatility_metrics(session: Session) -> List[VolatilityMetric]:
    def _loader() -> List[dict]:
        symbols = [symbol.symbol for symbol in list_symbols(session)][:8]
        series = _load_close_prices(session, symbols, VOLATILITY_WINDOW_HOURS)
        metrics: List[VolatilityMetric] = []
        for symbol, values in series.items():
            if len(values) < 2:
                continue
            vol = float(pd.Series(values).pct_change().std() or 0.0)
            metrics.append(VolatilityMetric(symbol=symbol, volatility=round(vol, 4), window_hours=VOLATILITY_WINDOW_HOURS))
        if not metrics:
            metrics = [VolatilityMetric(symbol=symbol, volatility=0.0, window_hours=VOLATILITY_WINDOW_HOURS) for symbol in symbols]
        return [metric.model_dump() for metric in metrics]

    payload = cache_result("analytics:volatility", 300, _loader)
    return [VolatilityMetric(**item) for item in payload]


def trend_signals(session: Session) -> List[TrendSignal]:
    def _loader() -> List[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=VOLATILITY_WINDOW_HOURS)
        rows = (
            session.query(MarketData)
            .filter(MarketData.timestamp >= cutoff)
            .order_by(MarketData.symbol.asc(), desc(MarketData.timestamp))
            .all()
        )
        grouped: Dict[str, List[MarketData]] = {}
        for row in rows:
            grouped.setdefault(row.symbol, []).append(row)
        signals: List[TrendSignal] = []
        for symbol, values in grouped.items():
            if len(values) < 2:
                continue
            latest = values[0]
            earlier = values[-1]
            change = float(latest.close) - float(earlier.close)
            trend = "bullish" if change > 0 else "bearish" if change < 0 else "sideways"
            score = round(abs(change) / float(earlier.close or 1) * 100, 2)
            signals.append(
                TrendSignal(symbol=symbol, trend=trend, score=score, updated_at=latest.timestamp)
            )
        if not signals:
            now = datetime.utcnow()
            signals = [
                TrendSignal(symbol="BTC", trend="sideways", score=0.0, updated_at=now),
                TrendSignal(symbol="ETH", trend="sideways", score=0.0, updated_at=now),
            ]
        return [signal.model_dump() for signal in signals]

    payload = cache_result("analytics:trends", 300, _loader)
    return [TrendSignal(**item) for item in payload]


def pattern_signals(session: Session) -> List[PatternSignal]:
    def _loader() -> List[dict]:
        signals: List[PatternSignal] = []
        for metadata in list_symbols(session):
            series = _load_series(session, metadata.symbol, PATTERN_WINDOW_HOURS)
            if series is None or len(series) < 3:
                continue
            pattern, confidence = _classify_pattern(series)
            signals.append(
                PatternSignal(
                    symbol=metadata.symbol,
                    pattern=pattern,
                    confidence=round(confidence, 2),
                    detected_at=_recent_timestamp(series),
                )
            )

        if not signals:
            now = datetime.utcnow()
            signals = [
                PatternSignal(symbol="BTC", pattern="consolidation", confidence=0.35, detected_at=now)
            ]
        ordered = sorted(signals, key=lambda item: item.confidence, reverse=True)
        return [signal.model_dump() for signal in ordered]

    payload = cache_result("analytics:patterns", 600, _loader)
    return [PatternSignal(**item) for item in payload]


def performance_leaders(session: Session) -> List[PerformanceEntry]:
    def _loader() -> List[dict]:
        symbols = [symbol.symbol for symbol in list_symbols(session)]
        entries: List[PerformanceEntry] = []
        for symbol in symbols:
            series = _load_series(session, symbol, PERFORMANCE_WINDOW_HOURS)
            if series is None or len(series) < 2:
                continue
            start = float(series.iloc[0])
            end = float(series.iloc[-1])
            if not start:
                continue
            change = ((end - start) / start) * 100
            entries.append(
                PerformanceEntry(symbol=symbol, return_percent=round(change, 2), period=f"{PERFORMANCE_WINDOW_HOURS}h")
            )

        if not entries:
            entries = [PerformanceEntry(symbol="BTC", return_percent=0.0, period=f"{PERFORMANCE_WINDOW_HOURS}h")]

        ordered = sorted(entries, key=lambda item: item.return_percent, reverse=True)[:10]
        return [entry.model_dump() for entry in ordered]

    payload = cache_result("analytics:top_performers", 300, _loader)
    return [PerformanceEntry(**item) for item in payload]


def momentum_leaders(session: Session) -> List[MomentumEntry]:
    def _loader() -> List[dict]:
        symbols = [symbol.symbol for symbol in list_symbols(session)]
        entries: List[MomentumEntry] = []
        for symbol in symbols:
            series = _load_series(session, symbol, PERFORMANCE_WINDOW_HOURS)
            if series is None or len(series) < 3:
                continue
            short = series.rolling(window=MOMENTUM_SHORT_WINDOW, min_periods=2).mean()
            long = series.rolling(window=MOMENTUM_LONG_WINDOW, min_periods=2).mean()
            short_value = float(short.iloc[-1]) if not pd.isna(short.iloc[-1]) else float(series.iloc[-1])
            long_value = float(long.iloc[-1]) if not pd.isna(long.iloc[-1]) else float(series.mean())
            if not long_value:
                continue
            momentum_ratio = (short_value - long_value) / long_value
            score = round(momentum_ratio * 100, 2)
            if score >= 3:
                classification = "strong"
            elif score >= 1:
                classification = "moderate"
            elif score <= -1.5:
                classification = "weak"
            else:
                classification = "neutral"
            entries.append(
                MomentumEntry(symbol=symbol, momentum_score=score, classification=classification)
            )

        if not entries:
            entries = [MomentumEntry(symbol="BTC", momentum_score=0.0, classification="neutral")]

        ordered = sorted(entries, key=lambda item: item.momentum_score, reverse=True)[:8]
        return [entry.model_dump() for entry in ordered]

    payload = cache_result("analytics:momentum", 300, _loader)
    return [MomentumEntry(**item) for item in payload]
