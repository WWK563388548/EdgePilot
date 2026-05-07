from dataclasses import dataclass
from hashlib import sha256
from time import monotonic
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import httpx
import jwt
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models import (
    Account,
    AccountMembership,
    Tenant,
    TenantDataCapability,
    TenantJobState,
    TenantMembership,
    User,
)

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
    tenant_id: str
    role: str
    external_subject: str
    email: str | None = None
    display_name: str | None = None
    email_verified: bool = False


_jwks_client: PyJWKClient | None = None
_auth0_management_token: tuple[str, float] | None = None
_auth0_user_profile_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_AUTH0_USER_PROFILE_CACHE_SECONDS = 300


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


def _auth0_management_audience() -> str:
    return settings.auth0_management_audience or f"{settings.auth_issuer.rstrip('/')}/api/v2/"


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _claim_bool(claims: dict[str, Any], *keys: str) -> bool | None:
    for key in keys:
        if key in claims:
            return _optional_bool(claims.get(key))
    return None


def _get_auth0_management_token(client: httpx.Client) -> str:
    global _auth0_management_token

    now = monotonic()
    if _auth0_management_token and _auth0_management_token[1] > now:
        return _auth0_management_token[0]

    token_url = f"{settings.auth_issuer.rstrip('/')}/oauth/token"
    token_response = client.post(
        token_url,
        json={
            "grant_type": "client_credentials",
            "client_id": settings.auth0_management_client_id,
            "client_secret": settings.auth0_management_client_secret,
            "audience": _auth0_management_audience(),
        },
    )
    token_response.raise_for_status()
    token_body = token_response.json()
    access_token = token_body["access_token"]
    expires_in = int(token_body.get("expires_in", 3600))
    _auth0_management_token = (access_token, now + max(expires_in - 60, 60))
    return access_token


def _clear_auth0_management_token() -> None:
    global _auth0_management_token
    _auth0_management_token = None


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
        tenant_id = claims.get(settings.auth_tenant_claim)
        role = claims.get(settings.auth_role_claim) or settings.auth_default_role
        if role not in ROLE_ORDER:
            role = "viewer"

        email = claims.get(settings.auth_email_claim) or claims.get("email")
        display_name = (
            claims.get(settings.auth_display_name_claim)
            or claims.get("name")
            or claims.get("nickname")
            or email
        )
        email_verified = _claim_bool(
            claims,
            settings.auth_email_verified_claim,
            "email_verified",
        )
        if email_verified is None or not email:
            user_profile = AuthService.fetch_user_profile(subject)
            email = email or user_profile.get("email")
            display_name = display_name or user_profile.get("name") or user_profile.get("nickname")
            if email_verified is None:
                email_verified = _optional_bool(user_profile.get("email_verified"))
        user_id = _stable_id("user", subject)

        return AuthService.upsert_principal(
            session=session,
            user_id=user_id,
            external_subject=subject,
            tenant_id=tenant_id,
            account_id=account_id,
            role=role,
            email=email,
            display_name=display_name,
            email_verified=bool(email_verified),
        )

    @staticmethod
    def upsert_principal(
        session: Session,
        user_id: str,
        external_subject: str,
        tenant_id: str | None,
        account_id: str,
        role: str,
        email: str | None,
        display_name: str | None,
        email_verified: bool,
    ) -> AuthPrincipal:
        tenant = None
        account = session.get(Account, account_id)
        if account is not None and account.tenant_id:
            tenant_id = account.tenant_id
        tenant_id = tenant_id or _stable_id("tenant", account_id)

        tenant = session.get(Tenant, tenant_id)
        if tenant is None:
            tenant = Tenant(
                tenant_id=tenant_id,
                name=display_name or email or "EdgePilot Workspace",
                status="active",
            )
            session.add(tenant)

        if account is None:
            account = Account(
                account_id=account_id,
                tenant_id=tenant_id,
                name=display_name or email or "EdgePilot Account",
            )
            session.add(account)
        elif not account.tenant_id:
            account.tenant_id = tenant_id

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

        session.flush()
        if tenant.owner_user_id is None:
            tenant.owner_user_id = user.user_id

        tenant_membership = session.get(TenantMembership, (tenant_id, user.user_id))
        if tenant_membership is None:
            tenant_membership = TenantMembership(
                tenant_id=tenant_id,
                user_id=user.user_id,
                role=role,
            )
            session.add(tenant_membership)
        elif role_allows(role, tenant_membership.role):
            tenant_membership.role = role

        membership = session.get(AccountMembership, (account_id, user.user_id))
        if membership is None:
            membership = AccountMembership(
                account_id=account_id,
                user_id=user.user_id,
                role=role,
            )
            session.add(membership)
        elif role_allows(role, membership.role):
            membership.role = role

        AuthService.ensure_tenant_foundation(session=session, tenant_id=tenant_id)

        session.commit()
        return AuthPrincipal(
            user_id=user.user_id,
            account_id=account_id,
            tenant_id=tenant_id,
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
    def ensure_tenant_foundation(session: Session, tenant_id: str) -> None:
        default_capabilities = [
            {
                "capability_key": "market_data.us_etf_daily",
                "provider": "polygon",
                "market": "US",
                "asset_type": "etf",
                "timeframe": "1d",
                "status": "available" if settings.polygon_api_key else "missing",
                "source": "env",
                "reason": None if settings.polygon_api_key else "POLYGON_API_KEY is not configured",
            },
            {
                "capability_key": "execution_import.csv",
                "provider": "manual_csv",
                "market": "multi",
                "asset_type": "multi",
                "timeframe": None,
                "status": "disabled",
                "source": "planned",
                "reason": "CSV execution import is planned for the next implementation phase",
            },
            {
                "capability_key": "notifications.in_app",
                "provider": "edgepilot",
                "market": None,
                "asset_type": None,
                "timeframe": None,
                "status": "available",
                "source": "app",
                "reason": None,
            },
            {
                "capability_key": "broker_sync.read_only",
                "provider": "byok",
                "market": "multi",
                "asset_type": "multi",
                "timeframe": None,
                "status": "disabled",
                "source": "planned",
                "reason": "Read-only broker sync is deferred until CSV import is validated",
            },
        ]
        for item in default_capabilities:
            capability_id = _stable_id("cap", f"{tenant_id}:{item['capability_key']}")
            if session.get(TenantDataCapability, capability_id) is None:
                session.add(
                    TenantDataCapability(
                        capability_id=capability_id,
                        tenant_id=tenant_id,
                        **item,
                    )
                )

        if session.get(TenantJobState, (tenant_id, "market_refresh_scan")) is None:
            session.add(
                TenantJobState(
                    tenant_id=tenant_id,
                    job_type="market_refresh_scan",
                    enabled=True,
                    status="idle",
                    rate_limit_per_minute=2,
                    metadata_json={
                        "scope": "tenant",
                        "notes": "Foundation shell for per-tenant automation throttling",
                    },
                )
            )

    @staticmethod
    def fetch_user_profile(external_subject: str) -> dict[str, Any]:
        if not (
            settings.auth_issuer
            and settings.auth0_management_client_id
            and settings.auth0_management_client_secret
        ):
            return {}

        now = monotonic()
        cached = _auth0_user_profile_cache.get(external_subject)
        if cached and cached[0] > now:
            return cached[1]

        audience = _auth0_management_audience()
        try:
            with httpx.Client(timeout=10) as client:
                for attempt in range(2):
                    management_token = _get_auth0_management_token(client)
                    response = client.get(
                        f"{audience.rstrip('/')}/users/{quote(external_subject, safe='')}",
                        headers={"Authorization": f"Bearer {management_token}"},
                    )
                    if response.status_code in {401, 403} and attempt == 0:
                        _clear_auth0_management_token()
                        continue
                    response.raise_for_status()
                    profile = dict(response.json())
                    break
        except httpx.HTTPError:
            return {}

        _auth0_user_profile_cache[external_subject] = (
            now + _AUTH0_USER_PROFILE_CACHE_SECONDS,
            profile,
        )
        return profile

    @staticmethod
    def resend_verification_email(external_subject: str) -> dict[str, Any]:
        audience = _auth0_management_audience()
        if not (
            settings.auth_issuer
            and settings.auth0_management_client_id
            and settings.auth0_management_client_secret
        ):
            raise ValueError("Auth0 Management API credentials are not configured")

        with httpx.Client(timeout=10) as client:
            management_token = _get_auth0_management_token(client)
            job_response = client.post(
                f"{audience.rstrip('/')}/jobs/verification-email",
                headers={"Authorization": f"Bearer {management_token}"},
                json={"user_id": external_subject},
            )
            job_response.raise_for_status()
            return dict(job_response.json())
