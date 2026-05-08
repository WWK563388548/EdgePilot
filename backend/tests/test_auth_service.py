from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.core.auth import AuthService
from backend.app.core.database import Base
from backend.app.models import Account, AccountMembership, Tenant, TenantDataCapability, TenantMembership, User


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-04-29 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return session_factory()


def test_principal_from_claims_fetches_missing_email_verification(monkeypatch) -> None:
    monkeypatch.setattr(
        AuthService,
        "fetch_user_profile",
        lambda external_subject: {
            "email": "user@example.com",
            "email_verified": True,
            "name": "Verified User",
        },
    )

    with _session() as session:
        principal = AuthService.principal_from_claims(session, {"sub": "auth0|user_1"})

        assert principal.email == "user@example.com"
        assert principal.display_name == "Verified User"
        assert principal.email_verified is True
        assert principal.tenant_id
        assert session.get(User, principal.user_id) is not None
        assert session.get(Tenant, principal.tenant_id) is not None
        assert session.get(Account, principal.account_id).tenant_id == principal.tenant_id
        assert session.get(TenantMembership, (principal.tenant_id, principal.user_id)) is not None
        assert session.get(AccountMembership, (principal.account_id, principal.user_id)) is not None
        assert session.query(TenantDataCapability).filter_by(tenant_id=principal.tenant_id).count() >= 1


def test_principal_from_claims_applies_role_downgrades(monkeypatch) -> None:
    monkeypatch.setattr(AuthService, "fetch_user_profile", lambda external_subject: {})

    with _session() as session:
        owner = AuthService.principal_from_claims(
            session,
            {
                "sub": "auth0|user_1",
                "https://edgepilot/account_id": "acct_1",
                "https://edgepilot/tenant_id": "tenant_1",
                "https://edgepilot/role": "owner",
            },
        )
        viewer = AuthService.principal_from_claims(
            session,
            {
                "sub": "auth0|user_1",
                "https://edgepilot/account_id": "acct_1",
                "https://edgepilot/tenant_id": "tenant_1",
                "https://edgepilot/role": "viewer",
            },
        )

        assert owner.role == "owner"
        assert viewer.role == "viewer"
        assert session.get(AccountMembership, ("acct_1", viewer.user_id)).role == "viewer"
        assert session.get(TenantMembership, ("tenant_1", viewer.user_id)).role == "viewer"
