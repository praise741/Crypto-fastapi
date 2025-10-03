from fastapi.testclient import TestClient


def test_track_symbol_adds_metadata(client: TestClient):
    response = client.post("/api/v1/market/symbols/MATIC/track", json={"source": "admin", "notes": "Layer 2"})
    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["symbol"]["symbol"] == "MATIC"

    detail = client.get("/api/v1/market/symbols/MATIC")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["data"]["symbol"]["sources"]
    assert "admin" in detail_payload["data"]["symbol"]["sources"]
