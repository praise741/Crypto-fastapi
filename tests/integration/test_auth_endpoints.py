from fastapi.testclient import TestClient


def test_register_and_login_flow(client: TestClient):
    payload = {"email": "newuser@example.com", "password": "password123"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]

    login_response = client.post("/api/v1/auth/login", json=payload)
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["success"] is True
    token = login_data["data"]["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["success"] is True
    assert me_data["data"]["email"] == payload["email"]
