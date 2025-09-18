from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Meta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")
    request_id: Optional[str] = None
    status_code: Optional[int] = None


class Pagination(BaseModel):
    page: int = 1
    per_page: int = 50
    total: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: Meta = Field(default_factory=Meta)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    meta: Meta = Field(default_factory=Meta)
