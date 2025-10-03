from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


MAX_PASSWORD_BYTES = 72


class TokenError(Exception):
    """Raised when an access or refresh token is invalid."""


class SecurityService:
    """Utility helpers for hashing passwords and generating tokens."""

    def __init__(self) -> None:
        self._secret_key = settings.JWT_SECRET
        self._algorithm = "HS256"
        self._access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self._refresh_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > MAX_PASSWORD_BYTES:
            raise ValueError("Password must be at most 72 bytes")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    def _create_token(self, subject: str, expires_delta: timedelta) -> str:
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        payload = {"sub": subject, "exp": expire, "iat": now}
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_access_token(self, subject: str) -> str:
        return self._create_token(subject, self._access_expires)

    def create_refresh_token(self, subject: str) -> str:
        return self._create_token(subject, self._refresh_expires)

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except JWTError as exc:  # pragma: no cover - pass-through for clarity
            raise TokenError(str(exc)) from exc


security_service = SecurityService()


def get_password_hash(password: str) -> str:
    return security_service.get_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return security_service.verify_password(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    return security_service.create_access_token(subject)


def create_refresh_token(subject: str) -> str:
    return security_service.create_refresh_token(subject)


def decode_token(token: str) -> Dict[str, Any]:
    return security_service.decode_token(token)
