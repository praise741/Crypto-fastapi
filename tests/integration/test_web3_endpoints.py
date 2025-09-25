from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings


def test_web3_health_endpoint(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "FEATURE_WEB3_HEALTH", True)

    monkeypatch.setattr(
        "app.api.v1.endpoints.web3.get_web3_health",
        lambda symbol: type(
            "MockHealth",
            (),
            {
                "symbol": symbol.upper(),
                "liquidity": 100000.0,
                "vol24h": 500000.0,
                "tx_per_hour": 12.0,
                "pools": [],
                "last_updated": __import__("datetime").datetime.utcnow(),
            },
        )(),
    )

    response = client.get("/api/v1/web3/health", params={"symbol": "ETH"})
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["symbol"] == "ETH"
    assert body["liquidity"] == 100000.0
