from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWTError
from sqlalchemy.orm import Session

from backend.app.core.auth import AuthPrincipal, AuthService, decode_bearer_token, role_allows
from backend.app.core.config import settings
from backend.app.core.database import get_session

DbSession = Annotated[Session, Depends(get_session)]


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


def require_authenticated_user(
    session: DbSession,
    authorization: str | None = Header(default=None),
) -> AuthPrincipal:
    if not settings.auth_enabled:
        return AuthService.dev_principal(session)

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = decode_bearer_token(token)
        return AuthService.principal_from_claims(session, claims)
    except (PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentPrincipal = Annotated[AuthPrincipal, Depends(require_authenticated_user)]


def require_trader(principal: CurrentPrincipal) -> AuthPrincipal:
    if not role_allows(principal.role, "trader"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trader role required")
    return principal


def require_admin(principal: CurrentPrincipal) -> AuthPrincipal:
    if not role_allows(principal.role, "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return principal


def require_owner(principal: CurrentPrincipal) -> AuthPrincipal:
    if not role_allows(principal.role, "owner"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")
    return principal


TraderPrincipal = Annotated[AuthPrincipal, Depends(require_trader)]
AdminPrincipal = Annotated[AuthPrincipal, Depends(require_admin)]
OwnerPrincipal = Annotated[AuthPrincipal, Depends(require_owner)]
