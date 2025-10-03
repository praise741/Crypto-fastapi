from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import datetime
from typing import Tuple

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core import database
from app.models.database.api_key import APIKey

logger = logging.getLogger("app.security")

API_KEY_BYTES = 32


@dataclass(frozen=True)
class APIKeyInfo:
    id: str
    user_id: str
    name: str | None


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key() -> Tuple[str, str]:
    raw_key = secrets.token_urlsafe(API_KEY_BYTES)
    return raw_key, hash_api_key(raw_key)


def create_api_key_for_user(
    session: Session, user_id: str, *, name: str | None = None
) -> Tuple[APIKeyInfo, str]:
    raw_key, key_hash = generate_api_key()
    api_key = APIKey(user_id=user_id, key_hash=key_hash, name=name)
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    logger.info("Issued API key %s for user %s", api_key.id, user_id)
    return APIKeyInfo(
        id=api_key.id, user_id=api_key.user_id, name=api_key.name
    ), raw_key


def verify_api_key(session: Session, raw_key: str) -> APIKeyInfo | None:
    key_hash = hash_api_key(raw_key)
    record = (
        session.query(APIKey)
        .filter(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
        .first()
    )
    if not record:
        return None
    record.last_used = datetime.utcnow()
    session.add(record)
    session.commit()
    return APIKeyInfo(id=record.id, user_id=record.user_id, name=record.name)


def verify_api_key_from_pool(raw_key: str) -> APIKeyInfo | None:
    with database.SessionLocal() as session:
        return verify_api_key(session, raw_key)


def sign_webhook_payload(payload: bytes, *, secret: str | None = None) -> str:
    secret_key = (secret or settings.WEBHOOK_SECRET or "").encode("utf-8")
    digest = hmac.new(secret_key, payload, hashlib.sha256)
    return digest.hexdigest()


def verify_webhook_signature(
    payload: bytes, signature: str, *, secret: str | None = None
) -> bool:
    expected = sign_webhook_payload(payload, secret=secret)
    return hmac.compare_digest(expected, signature)
