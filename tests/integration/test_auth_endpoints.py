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


def test_register_rejects_overlong_password(client: TestClient):
    payload = {"email": "oversized@example.com", "password": "x" * 80}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_rejects_short_password(client: TestClient):
    payload = {"email": "short@example.com", "password": "123"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_rejects_invalid_email(client: TestClient):
    payload = {"email": "invalid-email", "password": "validpassword123"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_login_fails_with_wrong_credentials(client: TestClient):
    # First register a user
    payload = {"email": "test@example.com", "password": "validpassword123"}
    client.post("/api/v1/auth/register", json=payload)

    # Try to login with wrong password
    wrong_payload = {"email": "test@example.com", "password": "wrongpassword"}
    response = client.post("/api/v1/auth/login", json=wrong_payload)
    assert response.status_code == 401
    assert response.json()["error"]["detail"] == "Incorrect email or password"


def test_login_fails_with_nonexistent_user(client: TestClient):
    payload = {"email": "nonexistent@example.com", "password": "password123"}
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["error"]["detail"] == "Incorrect email or password"


def test_protected_endpoints_require_token(client: TestClient):
    # Try to access protected endpoint without token
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_register_duplicate_email_fails(client: TestClient):
    payload = {"email": "duplicate@example.com", "password": "validpassword123"}

    # Register first time
    response1 = client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 200

    # Try to register same email again
    response2 = client.post("/api/v1/auth/register", json=payload)
    assert response2.status_code == 400
    assert "User already exists" in response2.json()["error"]["detail"]


def test_token_validation(client: TestClient):
    payload = {"email": "token@example.com", "password": "validpassword123"}

    # Register and login
    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post("/api/v1/auth/login", json=payload)

    token = login_response.json()["data"]["access_token"]

    # Valid token should work
    valid_headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=valid_headers)
    assert response.status_code == 200

    # Invalid token should fail
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=invalid_headers)
    assert response.status_code == 401
