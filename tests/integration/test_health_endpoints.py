from fastapi.testclient import TestClient


def test_health_endpoints(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"

    detailed = client.get("/api/v1/health/detailed")
    assert detailed.status_code == 200
    detailed_data = detailed.json()
    assert detailed_data["success"] is True
    assert detailed_data["data"]["services"]["database"] == "healthy"
