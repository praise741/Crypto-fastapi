import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.dependencies import get_current_active_user, get_db
from app.core.database import Base
import app.models.database  # noqa: F401
from app.core.security import get_password_hash
from app.main import app
from app.models.database.user import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    assert 'users' in Base.metadata.tables
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db() -> Session:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def override_current_user():
    with TestingSessionLocal() as session:
        user = session.query(User).first()
        if not user:
            user = User(email="autouser@example.com", password_hash=get_password_hash("password123"))
            session.add(user)
            session.commit()
            session.refresh(user)
        return user


app.dependency_overrides[get_current_active_user] = override_current_user


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(client: TestClient) -> dict:
    with TestingSessionLocal() as session:
        user = User(email="tester@example.com", password_hash=get_password_hash("password123"))
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"id": user.id, "email": user.email, "password": "password123"}
