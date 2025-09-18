from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class ModelMetadata:
    model_id: str
    version: str
    symbol: str
    model_type: str
    metrics: Dict[str, float]
    features: List[str]
    last_updated: datetime


MODEL_REGISTRY: Dict[str, ModelMetadata] = {
    "prophet_btc_v2": ModelMetadata(
        model_id="prophet_btc_v2",
        version="2.1.0",
        symbol="BTC",
        model_type="prophet",
        metrics={
            "mae": 0.045,
            "mape": 0.032,
            "directional_accuracy": 0.65,
        },
        features=["price_momentum", "volume_patterns", "rsi", "market_dominance"],
        last_updated=datetime.utcnow(),
    )
}
