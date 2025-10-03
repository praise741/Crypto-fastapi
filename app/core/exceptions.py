from typing import Any, Dict

from fastapi import HTTPException, status


class ApplicationError(HTTPException):
    """Base application error providing a consistent payload."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message, "details": details or {}},
        )


class NotFoundError(ApplicationError):
    def __init__(
        self, message: str = "Resource not found", details: Dict[str, Any] | None = None
    ) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "NOT_FOUND", message, details)


class UnauthorizedError(ApplicationError):
    def __init__(
        self, message: str = "Unauthorized", details: Dict[str, Any] | None = None
    ) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", message, details)


class RateLimitError(ApplicationError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMIT_EXCEEDED", message, details
        )


class ValidationError(ApplicationError):
    def __init__(
        self, message: str = "Invalid request", details: Dict[str, Any] | None = None
    ) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, "BAD_REQUEST", message, details)


class ServiceUnavailableError(ApplicationError):
    def __init__(
        self,
        message: str = "Service unavailable",
        details: Dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_503_SERVICE_UNAVAILABLE, "SERVICE_UNAVAILABLE", message, details
        )
