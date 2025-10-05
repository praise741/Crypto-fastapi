from fastapi.testclient import TestClient

from app.main import app


def test_health_public():
    """Test that health endpoint is accessible without API key."""
    with TestClient(app) as client:
        # Remove API key header to test public access
        r = client.get("/api/v1/health")
        assert r.status_code == 200
