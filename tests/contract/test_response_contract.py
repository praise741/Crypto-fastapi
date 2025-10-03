from fastapi.testclient import TestClient


def test_success_envelope_contains_meta(client: TestClient):
    response = client.get("/api/v1/market/prices")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "data" in payload
    assert "meta" in payload
    assert "timestamp" in payload["meta"]
    assert payload["meta"]["version"]
    assert response.headers.get("Cache-Control") == "public, max-age=30"


def test_error_format_consistency(client: TestClient):
    response = client.get("/api/v1/market/unknown/price")
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert "error" in payload
    assert "code" in payload["error"]
    assert "message" in payload["error"]
