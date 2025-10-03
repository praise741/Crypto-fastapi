from datetime import datetime, timezone
from typing import Any, Dict

from app.core.config import settings


def build_meta(extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
    }
    if extra:
        meta.update(extra)
    return meta


def success_response(data: Any, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {"success": True, "data": data, "meta": build_meta(meta)}


def error_response(
    code: str,
    message: str,
    details: Dict[str, Any] | None = None,
    status_code: int | None = None,
) -> Dict[str, Any]:
    payload = {
        "success": False,
        "error": {"code": code, "message": message, "details": details or {}},
        "meta": build_meta({"status_code": status_code}),
    }
    return payload
