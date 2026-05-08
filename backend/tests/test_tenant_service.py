from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.core.auth import AuthPrincipal, AuthService
from backend.app.core.config import settings
from backend.app.core.database import Base
from backend.app.models import LegalAcknowledgement, TenantDataCapability, TenantApiKey
from backend.app.schemas.tenant import LegalAcknowledgementCreate, TenantApiKeyCreate
from backend.app.services.tenant_service import TenantService


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-05-08 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return session_factory()


def _principal() -> AuthPrincipal:
    return AuthPrincipal(
        user_id="user_1",
        account_id="acct_1",
        tenant_id="tenant_1",
        role="owner",
        external_subject="auth0|user_1",
        email="user@example.com",
        display_name="User",
        email_verified=True,
    )


def test_principal_upsert_creates_tenant_foundation() -> None:
    with _session() as session:
        principal = AuthService.upsert_principal(
            session=session,
            user_id="user_1",
            external_subject="auth0|user_1",
            tenant_id="tenant_1",
            account_id="acct_1",
            role="owner",
            email="user@example.com",
            display_name="User",
            email_verified=True,
        )

        tenant = TenantService.current_tenant(session, principal)
        members = TenantService.list_members(session, principal)
        capabilities = TenantService.list_data_capabilities(session, principal)
        job_states = TenantService.list_job_states(session, principal)

        assert tenant.tenant_id == "tenant_1"
        assert members[0].user_id == "user_1"
        assert {row.capability_key for row in capabilities} >= {
            "market_data.us_etf_daily",
            "execution_import.csv",
            "notifications.in_app",
        }
        assert job_states[0].job_type == "market_refresh_scan"


def test_tenant_foundation_is_idempotent_by_capability_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "polygon_api_key", "")

    with _session() as session:
        principal = AuthService.upsert_principal(
            session=session,
            user_id="user_1",
            external_subject="auth0|user_1",
            tenant_id="tenant_1",
            account_id="acct_1",
            role="owner",
            email="user@example.com",
            display_name="User",
            email_verified=True,
        )
        session.query(TenantDataCapability).filter_by(
            tenant_id=principal.tenant_id,
            capability_key="market_data.us_etf_daily",
        ).delete()
        session.add(
            TenantDataCapability(
                capability_id="cap_migration_seeded",
                tenant_id=principal.tenant_id,
                capability_key="market_data.us_etf_daily",
                provider="polygon",
                market="US",
                asset_type="etf",
                timeframe="1d",
                status="available",
                source="migration",
            )
        )
        session.commit()

        AuthService.ensure_tenant_foundation(session=session, tenant_id=principal.tenant_id)
        session.commit()

        capability = session.query(TenantDataCapability).filter_by(
            tenant_id=principal.tenant_id,
            capability_key="market_data.us_etf_daily",
        ).one()
        assert (
            session.query(TenantDataCapability)
            .filter_by(
                tenant_id=principal.tenant_id,
                capability_key="market_data.us_etf_daily",
            )
            .count()
            == 1
        )
        assert capability.status == "missing"
        assert capability.source == "env_or_tenant_credential"


def test_legal_acknowledgement_and_api_key_are_tenant_scoped() -> None:
    with _session() as session:
        principal = AuthService.upsert_principal(
            session=session,
            user_id="user_1",
            external_subject="auth0|user_1",
            tenant_id="tenant_1",
            account_id="acct_1",
            role="owner",
            email="user@example.com",
            display_name="User",
            email_verified=True,
        )
        acknowledgement = TenantService.acknowledge_legal_document(
            session=session,
            principal=principal,
            request=LegalAcknowledgementCreate(document_key="beta_terms", document_version="v1"),
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
        credential = TenantService.create_api_key(
            session=session,
            principal=principal,
            request=TenantApiKeyCreate(
                provider="polygon",
                label="Polygon",
                encrypted_payload="ciphertext",
                key_fingerprint="fp_1",
            ),
        )

        assert acknowledgement.tenant_id == "tenant_1"
        assert session.query(LegalAcknowledgement).count() == 1
        assert credential.has_encrypted_payload is True
        assert session.query(TenantApiKey).filter_by(tenant_id="tenant_1").count() == 1


def test_polygon_credential_marks_market_data_capability_available(monkeypatch) -> None:
    monkeypatch.setattr(settings, "polygon_api_key", "")

    with _session() as session:
        principal = AuthService.upsert_principal(
            session=session,
            user_id="user_1",
            external_subject="auth0|user_1",
            tenant_id="tenant_1",
            account_id="acct_1",
            role="owner",
            email="user@example.com",
            display_name="User",
            email_verified=True,
        )
        capability = session.query(TenantDataCapability).filter_by(
            tenant_id=principal.tenant_id,
            capability_key="market_data.us_etf_daily",
        ).one()
        assert capability.status == "missing"

        TenantService.create_api_key(
            session=session,
            principal=principal,
            request=TenantApiKeyCreate(
                provider="polygon",
                label="Polygon",
                encrypted_payload="ciphertext",
                key_fingerprint="fp_1",
            ),
        )

        capability = session.query(TenantDataCapability).filter_by(
            tenant_id=principal.tenant_id,
            capability_key="market_data.us_etf_daily",
        ).one()
        assert capability.status == "available"
        assert capability.source == "tenant_credential"
