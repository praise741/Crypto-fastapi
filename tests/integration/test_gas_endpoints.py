"""
Tests for gas fee tracker endpoints.
"""


def test_get_gas_prices_endpoint(client):
    """Test gas prices endpoint."""
    response = client.get("/api/v1/gas/prices")

    assert response.status_code == 200
    data = response.json()["data"]

    # Verify all gas tiers present
    assert "slow" in data
    assert "standard" in data
    assert "fast" in data
    assert "instant" in data
    assert "timestamp" in data

    # Verify all are numeric
    assert isinstance(data["slow"], (int, float))
    assert isinstance(data["standard"], (int, float))
    assert isinstance(data["fast"], (int, float))
    assert isinstance(data["instant"], (int, float))

    # Verify ordering (slow < standard < fast < instant)
    assert data["slow"] <= data["standard"]
    assert data["standard"] <= data["fast"]
    assert data["fast"] <= data["instant"]


def test_estimate_gas_cost_endpoint(client):
    """Test gas cost estimation endpoint."""
    response = client.get(
        "/api/v1/gas/estimate?gas_limit=21000&tier=standard&eth_price=2500"
    )

    assert response.status_code == 200
    data = response.json()["data"]

    assert "gas_limit" in data
    assert "tier" in data
    assert "gas_price_gwei" in data
    assert "eth_cost" in data
    assert "usd_cost" in data

    assert data["gas_limit"] == 21000
    assert data["tier"] == "standard"
    assert isinstance(data["eth_cost"], (int, float))
    assert isinstance(data["usd_cost"], (int, float))


def test_estimate_gas_cost_without_eth_price(client):
    """Test gas estimation without ETH price."""
    response = client.get("/api/v1/gas/estimate?gas_limit=50000&tier=fast")

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["gas_limit"] == 50000
    assert data["tier"] == "fast"
    assert "eth_cost" in data
    assert data["usd_cost"] is None  # No ETH price provided


def test_estimate_gas_cost_all_tiers(client):
    """Test gas estimation for all priority tiers."""
    tiers = ["slow", "standard", "fast", "instant"]

    for tier in tiers:
        response = client.get(f"/api/v1/gas/estimate?tier={tier}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["tier"] == tier


def test_estimate_gas_cost_invalid_tier(client):
    """Test invalid gas tier."""
    response = client.get("/api/v1/gas/estimate?tier=super_fast")
    assert response.status_code == 422  # Validation error


def test_get_gas_history_endpoint(client):
    """Test gas price history endpoint."""
    response = client.get("/api/v1/gas/history?hours=1")

    assert response.status_code == 200
    data = response.json()["data"]

    assert "history" in data
    assert "count" in data
    assert isinstance(data["history"], list)


def test_get_gas_timing_recommendation(client):
    """Test gas timing recommendation endpoint."""
    # Make a few requests to populate history
    for _ in range(3):
        client.get("/api/v1/gas/prices")

    response = client.get("/api/v1/gas/timing")

    assert response.status_code == 200
    data = response.json()["data"]

    assert "recommendation" in data
    # May not have all fields if insufficient data
    assert isinstance(data["recommendation"], str)


def test_gas_history_limit_validation(client):
    """Test gas history parameter validation."""
    # Valid hours
    response = client.get("/api/v1/gas/history?hours=24")
    assert response.status_code == 200

    # Maximum hours
    response = client.get("/api/v1/gas/history?hours=168")
    assert response.status_code == 200

    # Invalid hours (too high)
    response = client.get("/api/v1/gas/history?hours=200")
    assert response.status_code == 422


def test_gas_caching(client):
    """Test that gas prices are cached."""
    # First request
    response1 = client.get("/api/v1/gas/prices")
    assert response1.status_code == 200
    data1 = response1.json()["data"]

    # Second request should return cached data (within 30s TTL)
    response2 = client.get("/api/v1/gas/prices")
    assert response2.status_code == 200
    data2 = response2.json()["data"]

    # Timestamps should match (cached)
    assert data1["timestamp"] == data2["timestamp"]


def test_gas_estimate_complex_transaction(client):
    """Test gas estimation for complex contract interaction."""
    response = client.get(
        "/api/v1/gas/estimate?gas_limit=500000&tier=fast&eth_price=2500"
    )

    assert response.status_code == 200
    data = response.json()["data"]

    # Complex transaction should have higher costs
    assert data["gas_limit"] == 500000
    assert data["eth_cost"] > 0
    assert data["usd_cost"] > 0
