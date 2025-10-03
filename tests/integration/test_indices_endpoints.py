from fastapi.testclient import TestClient


def test_indices_shortcuts(client: TestClient):
    response = client.get("/api/v1/indices/altseason")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["index"] == "altseason"

    fg_response = client.get("/api/v1/indices/fear-greed")
    assert fg_response.status_code == 200
    fg_payload = fg_response.json()
    assert fg_payload["success"] is True
    assert fg_payload["data"]["index"] == "fear-greed"

    dominance_response = client.get("/api/v1/indices/dominance")
    assert dominance_response.status_code == 200
    dominance_payload = dominance_response.json()
    assert dominance_payload["success"] is True
    assert dominance_payload["data"]["index"] == "dominance"
