from __future__ import annotations

from datetime import datetime

from rq import Queue
from redis import Redis

from app.core.config import settings

redis_connection = Redis.from_url(settings.REDIS_URL)
queue = Queue("crypto_tasks", connection=redis_connection)


def train_model(symbol: str, horizon: str) -> None:
    print(f"Training model for {symbol} horizon={horizon} at {datetime.utcnow().isoformat()}")


def evaluate_models() -> None:
    print("Evaluating models for accuracy and drift")


def schedule_training_jobs() -> None:
    for symbol in settings.SUPPORTED_SYMBOLS:
        for horizon in ("1h", "4h", "24h", "7d"):
            queue.enqueue(train_model, symbol, horizon)
