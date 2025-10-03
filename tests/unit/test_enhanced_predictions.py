"""
Tests for enhanced prediction features (sentiment, volume momentum, correlation).
"""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.services.prediction import (
    _compute_probability,
    _get_sentiment_factor,
    _get_volume_momentum,
    _get_market_correlation_factor,
)


def test_compute_probability_base():
    """Test base probability calculation without enhancements."""
    # Predicted higher than current (bullish)
    prob = _compute_probability(predicted=110.0, current_price=100.0)
    assert prob > 0.5  # Should be bullish
    assert prob <= 0.98

    # Predicted lower than current (bearish)
    prob = _compute_probability(predicted=90.0, current_price=100.0)
    assert prob < 0.5  # Should be bearish
    assert prob >= 0.02


def test_compute_probability_with_sentiment():
    """Test probability calculation with sentiment factor."""
    # Positive sentiment should increase probability
    prob_positive = _compute_probability(
        predicted=105.0,
        current_price=100.0,
        sentiment_factor=0.5,  # Positive sentiment
    )

    prob_neutral = _compute_probability(
        predicted=105.0,
        current_price=100.0,
        sentiment_factor=0.0,  # Neutral
    )

    assert prob_positive > prob_neutral


def test_compute_probability_with_volume_momentum():
    """Test probability calculation with volume momentum."""
    # Positive volume momentum should increase probability
    prob_momentum = _compute_probability(
        predicted=105.0,
        current_price=100.0,
        volume_momentum=0.5,  # Positive momentum
    )

    prob_neutral = _compute_probability(
        predicted=105.0,
        current_price=100.0,
        volume_momentum=0.0,  # No momentum
    )

    assert prob_momentum > prob_neutral


def test_compute_probability_combined_factors():
    """Test probability with multiple enhancement factors."""
    prob_enhanced = _compute_probability(
        predicted=105.0,
        current_price=100.0,
        sentiment_factor=0.8,  # Strong positive sentiment
        volume_momentum=0.6,  # Strong positive momentum
    )

    prob_base = _compute_probability(predicted=105.0, current_price=100.0)

    # Enhanced probability should be higher
    assert prob_enhanced > prob_base
    assert prob_enhanced <= 0.98  # Within bounds


def test_compute_probability_bounds():
    """Test that probability stays within bounds [0.02, 0.98]."""
    # Test extreme positive
    prob = _compute_probability(
        predicted=1000.0, current_price=100.0, sentiment_factor=1.0, volume_momentum=1.0
    )
    assert prob <= 0.98

    # Test extreme negative
    prob = _compute_probability(
        predicted=10.0, current_price=100.0, sentiment_factor=-1.0, volume_momentum=-1.0
    )
    assert prob >= 0.02


def test_get_volume_momentum_positive():
    """Test volume momentum calculation with increasing volume."""
    # Create mock DataFrame and records
    import pandas as pd

    # Recent volume increasing
    records = []
    for i in range(24):
        volume = 1000000 + (i * 50000)  # Increasing volume
        record = MagicMock()
        record.volume = volume
        records.append(record)

    df = pd.DataFrame({"y": [100] * 24})

    momentum = _get_volume_momentum(df, records)

    # Should be positive (increasing volume)
    assert momentum > 0
    assert -1.0 <= momentum <= 1.0


def test_get_volume_momentum_negative():
    """Test volume momentum with decreasing volume."""
    import pandas as pd

    # Recent volume decreasing
    records = []
    for i in range(24):
        volume = 2000000 - (i * 50000)  # Decreasing volume
        record = MagicMock()
        record.volume = volume
        records.append(record)

    df = pd.DataFrame({"y": [100] * 24})

    momentum = _get_volume_momentum(df, records)

    # Should be negative (decreasing volume)
    assert momentum < 0
    assert -1.0 <= momentum <= 1.0


def test_get_volume_momentum_insufficient_data():
    """Test volume momentum with insufficient data."""
    import pandas as pd

    records = []
    for i in range(5):  # Only 5 records
        record = MagicMock()
        record.volume = 1000000
        records.append(record)

    df = pd.DataFrame({"y": [100] * 5})

    momentum = _get_volume_momentum(df, records)

    # Should return 0 (insufficient data)
    assert momentum == 0.0


@patch("app.services.prediction.get_proxy_score")
def test_get_sentiment_factor_positive(mock_proxy):
    """Test sentiment factor extraction (positive)."""
    from unittest.mock import MagicMock

    # Mock proxy score
    mock_proxy.return_value = {"score": 75}  # 75 = positive sentiment

    mock_session = MagicMock()
    sentiment = _get_sentiment_factor(mock_session, "BTC")

    # Should be positive ((75-50)/50 = 0.5)
    assert sentiment > 0
    assert -1.0 <= sentiment <= 1.0


@patch("app.services.prediction.get_proxy_score")
def test_get_sentiment_factor_negative(mock_proxy):
    """Test sentiment factor extraction (negative)."""
    from unittest.mock import MagicMock

    # Mock proxy score
    mock_proxy.return_value = {"score": 25}  # 25 = negative sentiment

    mock_session = MagicMock()
    sentiment = _get_sentiment_factor(mock_session, "BTC")

    # Should be negative ((25-50)/50 = -0.5)
    assert sentiment < 0
    assert -1.0 <= sentiment <= 1.0


@patch("app.services.prediction.get_proxy_score")
def test_get_sentiment_factor_no_data(mock_proxy):
    """Test sentiment factor with no data."""
    from unittest.mock import MagicMock

    # Mock no proxy data
    mock_proxy.return_value = None

    mock_session = MagicMock()
    sentiment = _get_sentiment_factor(mock_session, "BTC")

    # Should return 0 (neutral)
    assert sentiment == 0.0


def test_get_market_correlation_btc_itself():
    """Test that BTC doesn't correlate with itself."""
    from unittest.mock import MagicMock

    mock_session = MagicMock()
    correlation = _get_market_correlation_factor(mock_session, "BTC")

    assert correlation == 0.0


def test_get_market_correlation_insufficient_data():
    """Test correlation with insufficient BTC data."""
    from unittest.mock import MagicMock

    mock_session = MagicMock()
    # Mock query that returns insufficient data
    mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

    correlation = _get_market_correlation_factor(mock_session, "ETH")

    # Should return 0 (insufficient data)
    assert correlation == 0.0


def test_get_market_correlation_with_btc_data():
    """Test market correlation when BTC data exists."""
    from unittest.mock import MagicMock

    # Create mock BTC records with upward trend
    now = datetime.utcnow()
    mock_records = []
    for i in range(24):
        record = MagicMock()
        record.close = 50000 + (i * 100)  # Upward trend
        record.timestamp = now - timedelta(hours=23 - i)
        mock_records.append(record)

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records

    correlation = _get_market_correlation_factor(mock_session, "ETH")

    # Should calculate correlation based on BTC trend
    # Note: correlation is dampened by 0.5 factor, so check bounds only
    assert -1.0 <= correlation <= 1.0
