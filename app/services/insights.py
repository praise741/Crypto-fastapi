from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import desc
from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.core.config import settings
from app.models.database.insight import InsightEvent
from app.models.schemas.insights import (
    InsightComponent,
    InsightEventView,
    InsightEventsResponse,
    InsightSummary,
)
from app.services.external import DexScreenerClient


analyzer = SentimentIntensityAnalyzer()
dex_client = DexScreenerClient(base_url=settings.DEXSCREENER_BASE_URL)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_proxy_components(symbol: str) -> Dict[str, float]:
    pair = dex_client.search_pair(symbol)
    if not pair:
        return {
            "buy_sell_ratio": 0.0,
            "vol_change_24h": 0.0,
            "tx_velocity": 0.0,
        }
    txns = pair.transactions or {}
    h24 = txns.get("h24", {})
    h1 = txns.get("h1", {})
    buys_24 = float(h24.get("buys", 0))
    sells_24 = float(h24.get("sells", 0))
    total_24 = buys_24 + sells_24
    ratio = _safe_ratio(buys_24 - sells_24, total_24)
    total_1h = float(h1.get("buys", 0) + h1.get("sells", 0))
    tx_velocity = total_1h
    vol_change = 0.0
    if pair.volume_24h:
        # crude approximation: compare 1h extrapolated volume with 24h
        vol_change = _safe_ratio(total_1h * 24 - total_24, total_24)
    return {
        "buy_sell_ratio": max(min(ratio, 1.0), -1.0),
        "vol_change_24h": max(min(vol_change, 1.0), -1.0),
        "tx_velocity": total_1h,
    }


def compute_proxy_score(components: Dict[str, float]) -> float:
    score = 0.6 * components.get("buy_sell_ratio", 0.0) + 0.4 * components.get("vol_change_24h", 0.0)
    return max(min(score, 1.0), -1.0)


def generate_proxy_events(symbol: str, components: Dict[str, float]) -> List[InsightEvent]:
    events: List[InsightEvent] = []
    ratio = components.get("buy_sell_ratio", 0.0)
    vol_change = components.get("vol_change_24h", 0.0)
    timestamp = datetime.utcnow()
    if abs(ratio) >= 0.2:
        direction = "Buy" if ratio > 0 else "Sell"
        text = f"{direction} pressure {ratio * 100:.1f}% vs sells in last 24h"
        events.append(
            InsightEvent(
                ts=timestamp,
                source="PROXY",
                asset_symbol=symbol.upper(),
                text_excerpt=text,
                sentiment_score=ratio,
                meta={"component": "buy_sell_ratio"},
            )
        )
    if abs(vol_change) >= 0.15:
        text = f"Volume momentum {vol_change * 100:.1f}% vs 24h baseline"
        events.append(
            InsightEvent(
                ts=timestamp,
                source="PROXY",
                asset_symbol=symbol.upper(),
                text_excerpt=text,
                sentiment_score=vol_change,
                meta={"component": "vol_change_24h"},
            )
        )
    return events


def refresh_proxy_insights(session: Session, symbol: str) -> List[InsightEvent]:
    components = compute_proxy_components(symbol)
    events = generate_proxy_events(symbol, components)
    for event in events:
        session.add(event)
    session.commit()
    return events


def summarise_insights(session: Session, symbol: str, window: str) -> InsightSummary:
    components = compute_proxy_components(symbol)
    proxy_score = compute_proxy_score(components)
    window_minutes = 24 * 60
    if window.endswith("h"):
        window_minutes = int(window[:-1]) * 60
    elif window.endswith("d"):
        window_minutes = int(window[:-1]) * 24 * 60
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

    events = (
        session.query(InsightEvent)
        .filter(
            InsightEvent.asset_symbol == symbol.upper(),
            InsightEvent.ts >= cutoff,
        )
        .order_by(desc(InsightEvent.ts))
        .all()
    )
    reddit_scores = [float(event.sentiment_score) for event in events if event.source == "REDDIT"]
    reddit_score = sum(reddit_scores) / len(reddit_scores) if reddit_scores else None
    combined_scores = [proxy_score] + reddit_scores
    avg_score = sum(combined_scores) / len(combined_scores) if combined_scores else 0.0
    counts = {"PROXY": 0, "REDDIT": 0}
    for event in events:
        counts[event.source] = counts.get(event.source, 0) + 1
    insight_components = [
        InsightComponent(name=name, value=value)
        for name, value in components.items()
    ]
    return InsightSummary(
        symbol=symbol.upper(),
        window=window,
        proxy_score=proxy_score,
        reddit_score=reddit_score,
        score_avg=max(min(avg_score, 1.0), -1.0),
        score_trend=None,
        counts_by_source=counts,
        components=insight_components,
    )


def list_events(session: Session, symbol: str, limit: int = 50) -> InsightEventsResponse:
    records = (
        session.query(InsightEvent)
        .filter(InsightEvent.asset_symbol == symbol.upper())
        .order_by(desc(InsightEvent.ts))
        .limit(limit)
        .all()
    )
    events = [
        InsightEventView(
            id=record.id,
            ts=record.ts,
            source=record.source,
            asset_symbol=record.asset_symbol,
            text_excerpt=record.text_excerpt,
            sentiment_score=float(record.sentiment_score),
        )
        for record in records
    ]
    return InsightEventsResponse(symbol=symbol.upper(), events=events)


def ingest_reddit_post(session: Session, symbol: str, text: str) -> InsightEvent:
    sentiment = analyzer.polarity_scores(text)["compound"]
    event = InsightEvent(
        ts=datetime.utcnow(),
        source="REDDIT",
        asset_symbol=symbol.upper(),
        text_excerpt=text[:480],
        sentiment_score=sentiment,
        meta={"length": len(text)},
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
