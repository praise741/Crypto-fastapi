from datetime import datetime, timedelta

import pytest

from app.core.config import settings
from app.models.database.market_data import MarketData
from app.services.prediction import MODEL_VERSION, get_predictions
from tests.conftest import TestingSessionLocal


@pytest.mark.parametrize("symbol", ["BTC"])
def test_get_predictions_trains_prophet(symbol: str) -> None:
    original_external = settings.ENABLE_EXTERNAL_MARKET_DATA
    original_dex = settings.DEXSCREENER_ENABLED
    original_simple = settings.SIMPLE_BOOTSTRAP
    settings.ENABLE_EXTERNAL_MARKET_DATA = False
    settings.DEXSCREENER_ENABLED = False
    settings.SIMPLE_BOOTSTRAP = True

    session = TestingSessionLocal()
    try:
        now = datetime.utcnow()
        for idx in range(120):
            timestamp = now - timedelta(hours=119 - idx)
            base_price = 20000 + idx * 5
            session.add(
                MarketData(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=base_price - 10,
                    high=base_price + 10,
                    low=base_price - 15,
                    close=base_price,
                    volume=1_000 + idx,
                    market_cap=400_000_000 + idx * 1000,
                    source="test",
                )
            )
        session.commit()

        response = get_predictions(session, symbol, horizons=["1h", "4h"], include_confidence=True, include_factors=True)
        assert response.symbol == symbol
        assert len(response.predictions) == 2
        assert all(item.model_version in {MODEL_VERSION, "prophet-ma-fallback"} for item in response.predictions)
        assert all(item.confidence_interval is not None for item in response.predictions)
        assert all(item.probability is not None for item in response.predictions)
    finally:
        session.close()
        settings.ENABLE_EXTERNAL_MARKET_DATA = original_external
        settings.DEXSCREENER_ENABLED = original_dex
        settings.SIMPLE_BOOTSTRAP = original_simple
