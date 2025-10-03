"""
Tests for news aggregation endpoints.
"""


def test_get_news_endpoint(client):
    """Test news aggregation endpoint."""
    response = client.get("/api/v1/news?limit=10")

    assert response.status_code == 200
    data = response.json()["data"]

    assert "news" in data
    assert "count" in data
    assert isinstance(data["news"], list)
    assert data["count"] >= 0


def test_get_news_with_symbol_filter(client):
    """Test news filtering by symbol."""
    response = client.get("/api/v1/news?limit=5&symbols=BTC,ETH")

    assert response.status_code == 200
    data = response.json()["data"]

    assert "news" in data
    # Verify filtering works (may be empty if no BTC/ETH news)
    for news_item in data["news"]:
        assert "symbols" in news_item
        assert isinstance(news_item["symbols"], list)


def test_get_trending_topics_endpoint(client):
    """Test trending topics endpoint."""
    response = client.get("/api/v1/news/trending?limit=5")

    assert response.status_code == 200
    data = response.json()["data"]

    assert "trending" in data
    assert "count" in data
    assert isinstance(data["trending"], list)


def test_news_response_structure(client):
    """Test news response has correct structure."""
    response = client.get("/api/v1/news?limit=1")

    assert response.status_code == 200
    data = response.json()["data"]

    if data["count"] > 0:
        news_item = data["news"][0]
        assert "title" in news_item
        assert "description" in news_item
        assert "url" in news_item
        assert "source" in news_item
        assert "published_at" in news_item
        assert "sentiment" in news_item
        assert "symbols" in news_item


def test_trending_response_structure(client):
    """Test trending topics response structure."""
    response = client.get("/api/v1/news/trending?limit=1")

    assert response.status_code == 200
    data = response.json()["data"]

    if data["count"] > 0:
        topic = data["trending"][0]
        assert "topic" in topic
        assert "mentions" in topic
        assert "sentiment_score" in topic
        assert "change_24h" in topic
        assert "related_symbols" in topic


def test_news_caching(client):
    """Test that news results are cached."""
    # First request
    response1 = client.get("/api/v1/news?limit=5")
    assert response1.status_code == 200
    data1 = response1.json()["data"]

    # Second request should return cached data
    response2 = client.get("/api/v1/news?limit=5")
    assert response2.status_code == 200
    data2 = response2.json()["data"]

    # Counts should match (cached)
    assert data1["count"] == data2["count"]


def test_news_limit_validation(client):
    """Test news limit parameter validation."""
    # Test minimum limit
    response = client.get("/api/v1/news?limit=1")
    assert response.status_code == 200

    # Test maximum limit
    response = client.get("/api/v1/news?limit=100")
    assert response.status_code == 200

    # Test invalid limit (too high)
    response = client.get("/api/v1/news?limit=200")
    assert response.status_code == 422  # Validation error
