from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db, get_current_active_user
from app.core.config import settings
from app.core.responses import success_response
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    decode_token,
)
from app.models.database.user import User
from app.models.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.models.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        plan=user.plan,
        is_active=user.is_active,
        email_verified=user.email_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _token_response(user: User) -> TokenPair:
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=_serialize_user(user),
    )


@router.post("/register", summary="Register a new user")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )
    user = User(email=payload.email, password_hash=get_password_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(_token_response(user).model_dump())


@router.post("/login", summary="Login and obtain tokens")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return success_response(_token_response(user).model_dump())


@router.post("/refresh", summary="Refresh access token")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    data = decode_token(payload.refresh_token)
    user_id = data.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return success_response(_token_response(user).model_dump())


@router.post("/logout", summary="Logout user")
def logout():
    return success_response({"message": "Logged out"})


@router.get("/me", summary="Get current user")
def me(current_user: User = Depends(get_current_active_user)) -> dict:
    return success_response(_serialize_user(current_user).model_dump())


@router.post("/forgot-password", summary="Trigger password reset process")
def forgot_password(payload: ForgotPasswordRequest):
    # In production this would send an email. Here we return a dummy response.
    return success_response(
        {"message": f"Password reset email sent to {payload.email}"}
    )


@router.post("/reset-password", summary="Reset password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.token)
    user_id = data.get("sub")
    user = db.query(User).filter(User.id == user_id).first() if user_id else None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    user.password_hash = get_password_hash(payload.password)
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()
    return success_response({"message": "Password updated"})
