from datetime import datetime, timedelta
from random import random

from app.core.database import SessionLocal, init_db
from app.core.security import get_password_hash
from app.models.database.market_data import MarketData
from app.models.database.prediction import Prediction
from app.models.database.user import User


SAMPLE_PASSWORD = "password123"


def seed_users(session):
    if session.query(User).count() == 0:
        user = User(email="demo@example.com", password_hash=get_password_hash(SAMPLE_PASSWORD), plan="pro")
        session.add(user)
        session.commit()
        print("Seeded default user demo@example.com / password123")


def seed_market_data(session):
    for symbol in ["BTC", "ETH", "SOL"]:
        for i in range(10):
            session.add(
                MarketData(
                    symbol=symbol,
                    timestamp=datetime.utcnow() - timedelta(minutes=15 * i),
                    open=20000 + i * 10,
                    high=20100 + i * 10,
                    low=19900 + i * 10,
                    close=20050 + i * 10,
                    volume=1000 + i * 50,
                    market_cap=500_000_000 + i * 1_000_000,
                    source="seed",
                )
            )
    session.commit()
    print("Seeded market data")


def seed_predictions(session):
    for symbol in ["BTC", "ETH"]:
        for horizon in (1, 4, 24):
            session.add(
                Prediction(
                    symbol=symbol,
                    prediction_time=datetime.utcnow(),
                    horizon_hours=horizon,
                    predicted_price=20000 + random() * 1000,
                    confidence_lower=19500 + random() * 200,
                    confidence_upper=20500 + random() * 200,
                    confidence_score=0.8,
                    model_version="simulated",
                    features_used={"momentum": 0.3, "volume": 0.2},
                )
            )
    session.commit()
    print("Seeded predictions")


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        seed_users(session)
        seed_market_data(session)
        seed_predictions(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
