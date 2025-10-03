from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings


def test_insights_endpoints(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "FEATURE_INSIGHTS", True)

    monkeypatch.setattr(
        "app.services.insights.compute_proxy_components",
        lambda symbol: {
            "buy_sell_ratio": 0.4,
            "vol_change_24h": 0.1,
            "tx_velocity": 12,
        },
    )

    summary = client.get("/api/v1/insights/summary", params={"symbol": "BTC"})
    assert summary.status_code == 200
    data = summary.json()["data"]
    assert data["proxy_score"] > 0
    assert data["counts_by_source"]["PROXY"] >= 0

    events = client.get("/api/v1/insights/events", params={"symbol": "BTC"})
    assert events.status_code == 200
    assert events.json()["data"]["events"] == []
