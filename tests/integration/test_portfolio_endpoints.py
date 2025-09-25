from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient

from app.core.config import settings


CSV_CONTENT = "asset_symbol,quantity,cost_basis\nBTC,0.5,10000\nETH,2,3000\n"


def test_portfolio_upload_and_views(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "FEATURE_PORTFOLIO", True)

    files = {"file": ("holdings.csv", BytesIO(CSV_CONTENT.encode()), "text/csv")}
    upload = client.post("/api/v1/portfolio/upload", files=files)
    assert upload.status_code == 200
    payload = upload.json()["data"]
    assert payload["imported_rows"] == 2

    holdings = client.get("/api/v1/portfolio/holdings")
    assert holdings.status_code == 200
    holdings_data = holdings.json()["data"]
    assert len(holdings_data["holdings"]) == 2

    allocation = client.get("/api/v1/portfolio/allocation")
    assert allocation.status_code == 200
    allocation_data = allocation.json()["data"]
    assert len(allocation_data["allocation"]) == 2

    performance = client.get("/api/v1/portfolio/performance", params={"window": "30d"})
    assert performance.status_code == 200
    performance_data = performance.json()["data"]
    assert performance_data["window"] == "30d"
    assert len(performance_data["points"]) >= 1
