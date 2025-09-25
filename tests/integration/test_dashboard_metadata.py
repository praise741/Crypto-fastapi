from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings


def test_dashboard_metadata(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "FEATURE_DASHBOARD", True)
    response = client.get("/api/v1/dashboard/metadata")
    assert response.status_code == 200
    data = response.json()["data"]
    assert any(widget["name"] == "priceTicker" for widget in data["widgets"])
    assert "/ws/market" in data["websockets"]
