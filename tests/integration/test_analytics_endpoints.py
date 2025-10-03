from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.models.database.market_data import MarketData
from tests.conftest import TestingSessionLocal


def _seed_history() -> None:
    with TestingSessionLocal() as session:
        now = datetime.utcnow()
        for idx in range(0, 48):
            timestamp = now - timedelta(hours=47 - idx)
            session.add(
                MarketData(
                    symbol="BTC",
                    timestamp=timestamp,
                    open=20000 + idx * 5,
                    high=20000 + idx * 5 + 20,
                    low=20000 + idx * 5 - 20,
                    close=20000 + idx * 5,
                    volume=1_000 + idx * 10,
                    market_cap=400_000_000 + idx * 1000,
                    source="test",
                )
            )
            session.add(
                MarketData(
                    symbol="ETH",
                    timestamp=timestamp,
                    open=1200 + idx * 2,
                    high=1200 + idx * 2 + 8,
                    low=1200 + idx * 2 - 8,
                    close=1200 + idx * 2,
                    volume=500 + idx * 5,
                    market_cap=200_000_000 + idx * 500,
                    source="test",
                )
            )
        session.commit()


def test_correlations_endpoint(client: TestClient):
    _seed_history()
    response = client.get("/api/v1/analytics/correlations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["window_hours"] == 72
    assert payload["data"]["entries"]


def test_momentum_endpoint(client: TestClient):
    _seed_history()
    response = client.get("/api/v1/analytics/momentum")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["leaders"]
