from fastapi import HTTPException, status

from app.core.config import settings


def require_feature(feature: str) -> None:
    flag_name = f"FEATURE_{feature.upper()}"
    enabled = getattr(settings, flag_name, False)
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature '{feature}' is disabled",
        )
