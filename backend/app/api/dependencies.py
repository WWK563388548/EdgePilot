from fastapi import Header, HTTPException, status

from backend.app.core.config import settings


def require_ingestion_admin(
    x_ingestion_admin_token: str | None = Header(default=None),
) -> None:
    if not settings.ingestion_admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="INGESTION_ADMIN_TOKEN is not configured",
        )

    if x_ingestion_admin_token != settings.ingestion_admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ingestion admin token",
        )
