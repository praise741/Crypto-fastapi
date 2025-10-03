import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.middleware.authentication import API_KEY_HEADER
from app.api.v1.dependencies import get_current_active_user, get_db
from app.core.database import Base
import app.models.database  # noqa: F401
from app.core.security import decode_token, get_password_hash
from app.main import app
from app.models.database.user import User
from app.services.security import create_api_key_for_user

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import app.core.database as core_database

core_database.SessionLocal = TestingSessionLocal
core_database.engine = engine


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


def override_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except Exception:  # pragma: no cover - invalid token fallback
            payload = {}
        user_id = payload.get("sub") if isinstance(payload, dict) else None
        if user_id:
            with TestingSessionLocal() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    return user

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
    with TestingSessionLocal() as session:
        user = session.query(User).first()
        if not user:
            user = User(email="client@example.com", password_hash=get_password_hash("password123"))
            session.add(user)
            session.commit()
            session.refresh(user)
        _, raw_key = create_api_key_for_user(session, user.id, name="test-client")

    with TestClient(app) as test_client:
        test_client.headers.update({API_KEY_HEADER: raw_key})
        yield test_client


@pytest.fixture
def test_user(client: TestClient) -> dict:
    with TestingSessionLocal() as session:
        user = User(email="tester@example.com", password_hash=get_password_hash("password123"))
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"id": user.id, "email": user.email, "password": "password123"}
