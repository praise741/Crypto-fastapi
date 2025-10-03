from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.database.user import User
from app.services.security import APIKeyInfo


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials") from exc
    user_id: str | None = payload.get("sub") if isinstance(payload, dict) else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def get_optional_api_key(request: Request) -> str | None:
    return getattr(request.state, "api_key", None)


def get_active_api_key(request: Request) -> APIKeyInfo:
    api_key = getattr(request.state, "api_key", None)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key required")
    return api_key
