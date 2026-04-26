from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from uuid import uuid4

import httpx
import jwt
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models import Account, AccountMembership, User

ROLE_ORDER = {
    "viewer": 0,
    "trader": 1,
    "admin": 2,
    "owner": 3,
}


@dataclass(frozen=True)
class AuthPrincipal:
    user_id: str
    account_id: str
    role: str
    external_subject: str
    email: str | None = None
    display_name: str | None = None
    email_verified: bool = False


_jwks_client: PyJWKClient | None = None


def role_allows(actual: str, required: str) -> bool:
    return ROLE_ORDER.get(actual, -1) >= ROLE_ORDER[required]


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{sha256(value.encode('utf-8')).hexdigest()[:24]}"


def _jwks_url() -> str:
    if settings.auth_jwks_url:
        return settings.auth_jwks_url
    if settings.auth_issuer:
        return f"{settings.auth_issuer.rstrip('/')}/.well-known/jwks.json"
    return ""


def decode_bearer_token(token: str) -> dict[str, Any]:
    global _jwks_client

    jwks_url = _jwks_url()
    if not jwks_url or not settings.auth_issuer or not settings.auth_audience:
        raise ValueError("Auth issuer, audience, and JWKS URL must be configured")

    if _jwks_client is None:
        _jwks_client = PyJWKClient(jwks_url)

    signing_key = _jwks_client.get_signing_key_from_jwt(token).key
    algorithms = [item.strip() for item in settings.auth_algorithms.split(",") if item.strip()]
    return jwt.decode(
        token,
        signing_key,
        algorithms=algorithms,
        audience=settings.auth_audience,
        issuer=settings.auth_issuer,
    )


class AuthService:
    @staticmethod
    def principal_from_claims(session: Session, claims: dict[str, Any]) -> AuthPrincipal:
        subject = claims.get("sub")
        if not subject:
            raise ValueError("Token is missing sub claim")

        account_id = claims.get(settings.auth_account_claim) or _stable_id("acct", subject)
        role = claims.get(settings.auth_role_claim) or settings.auth_default_role
        if role not in ROLE_ORDER:
            role = "viewer"

        email = claims.get("email")
        email_verified = bool(claims.get("email_verified"))
        display_name = claims.get("name") or claims.get("nickname") or email
        user_id = _stable_id("user", subject)

        return AuthService.upsert_principal(
            session=session,
            user_id=user_id,
            external_subject=subject,
            account_id=account_id,
            role=role,
            email=email,
            display_name=display_name,
            email_verified=email_verified,
        )

    @staticmethod
    def upsert_principal(
        session: Session,
        user_id: str,
        external_subject: str,
        account_id: str,
        role: str,
        email: str | None,
        display_name: str | None,
        email_verified: bool,
    ) -> AuthPrincipal:
        account = session.get(Account, account_id)
        if account is None:
            account = Account(account_id=account_id, name=display_name or email or "EdgePilot Account")
            session.add(account)

        user = session.scalar(select(User).where(User.external_subject == external_subject))
        if user is None:
            user = User(
                user_id=user_id,
                external_subject=external_subject,
                email=email,
                display_name=display_name,
            )
            session.add(user)
        else:
            user.email = email or user.email
            user.display_name = display_name or user.display_name

        membership = session.get(AccountMembership, (account_id, user.user_id))
        if membership is None:
            membership = AccountMembership(
                account_id=account_id,
                user_id=user.user_id,
                role=role,
            )
            session.add(membership)

        session.commit()
        return AuthPrincipal(
            user_id=user.user_id,
            account_id=account_id,
            role=membership.role,
            external_subject=external_subject,
            email=user.email,
            display_name=user.display_name,
            email_verified=email_verified,
        )

    @staticmethod
    def audit_id() -> str:
        return f"audit_{uuid4().hex}"

    @staticmethod
    def resend_verification_email(external_subject: str) -> dict[str, Any]:
        token_url = f"{settings.auth_issuer.rstrip('/')}/oauth/token"
        audience = settings.auth0_management_audience or (
            f"{settings.auth_issuer.rstrip('/')}/api/v2/"
        )
        if not (
            settings.auth_issuer
            and settings.auth0_management_client_id
            and settings.auth0_management_client_secret
        ):
            raise ValueError("Auth0 Management API credentials are not configured")

        with httpx.Client(timeout=10) as client:
            token_response = client.post(
                token_url,
                json={
                    "grant_type": "client_credentials",
                    "client_id": settings.auth0_management_client_id,
                    "client_secret": settings.auth0_management_client_secret,
                    "audience": audience,
                },
            )
            token_response.raise_for_status()
            management_token = token_response.json()["access_token"]

            job_response = client.post(
                f"{audience.rstrip('/')}/jobs/verification-email",
                headers={"Authorization": f"Bearer {management_token}"},
                json={"user_id": external_subject},
            )
            job_response.raise_for_status()
            return dict(job_response.json())
