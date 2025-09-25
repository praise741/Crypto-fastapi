from fastapi.testclient import TestClient

from app.services.health import HealthStatus


def test_health_endpoints(client: TestClient, monkeypatch):
    fake_status = {
        "database": HealthStatus(name="database", status="healthy"),
        "redis": HealthStatus(name="redis", status="healthy"),
    }

    def fake_checks(_):
        return fake_status

    monkeypatch.setattr("app.api.v1.endpoints.health.run_health_checks", fake_checks)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"

    detailed = client.get("/api/v1/health/detailed")
    assert detailed.status_code == 200
    detailed_data = detailed.json()
    assert detailed_data["success"] is True
    assert detailed_data["data"]["services"]["database"]["status"] == "healthy"
