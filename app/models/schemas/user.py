from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    id: str
    email: EmailStr
    plan: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserUpdatePlan(BaseModel):
    plan: str


class UserResponse(UserBase):
    pass
