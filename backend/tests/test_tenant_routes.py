from datetime import UTC, datetime

from backend.app.api.routes.tenant import (
    create_data_credential,
    get_current_tenant,
    list_current_tenant_members,
    list_data_capabilities,
    list_data_credentials,
    list_legal_acknowledgements,
    list_tenant_job_states,
)
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.tenant import (
    LegalAcknowledgement,
    Tenant,
    TenantApiKey,
    TenantDataCapability,
    TenantJobState,
    TenantMember,
)


def _principal() -> AuthPrincipal:
    return AuthPrincipal(
        user_id="user_1",
        account_id="acct_1",
        tenant_id="tenant_1",
        role="owner",
        external_subject="auth0|user_1",
        email_verified=True,
    )


def test_tenant_routes_delegate_to_service(monkeypatch) -> None:
    from backend.app.api.routes import tenant as tenant_route

    now = datetime(2026, 5, 8, tzinfo=UTC)
    monkeypatch.setattr(
        tenant_route.TenantService,
        "current_tenant",
        lambda session, principal: Tenant(
            tenant_id=principal.tenant_id,
            name="Tenant",
            status="active",
            created_at=now,
        ),
    )
    monkeypatch.setattr(
        tenant_route.TenantService,
        "list_members",
        lambda session, principal: [
            TenantMember(tenant_id=principal.tenant_id, user_id=principal.user_id, role="owner")
        ],
    )
    monkeypatch.setattr(
        tenant_route.TenantService,
        "list_acknowledgements",
        lambda session, principal: [
            LegalAcknowledgement(
                acknowledgement_id="ack_1",
                tenant_id=principal.tenant_id,
                user_id=principal.user_id,
                document_key="beta_terms",
                document_version="v1",
            )
        ],
    )
    monkeypatch.setattr(
        tenant_route.TenantService,
        "list_api_keys",
        lambda session, principal: [
            TenantApiKey(
                credential_id="cred_1",
                tenant_id=principal.tenant_id,
                provider="polygon",
                has_encrypted_payload=True,
            )
        ],
    )
    monkeypatch.setattr(
        tenant_route.TenantService,
        "create_api_key",
        lambda session, principal, request: TenantApiKey(
            credential_id="cred_1",
            tenant_id=principal.tenant_id,
            provider=request.provider,
            has_encrypted_payload=bool(request.encrypted_payload),
        ),
    )
    monkeypatch.setattr(
        tenant_route.TenantService,
        "list_data_capabilities",
        lambda session, principal: [
            TenantDataCapability(
                capability_id="cap_1",
                tenant_id=principal.tenant_id,
                capability_key="market_data.us_etf_daily",
                status="available",
            )
        ],
    )
    monkeypatch.setattr(
        tenant_route.TenantService,
        "list_job_states",
        lambda session, principal: [
            TenantJobState(
                tenant_id=principal.tenant_id,
                job_type="market_refresh_scan",
                status="idle",
            )
        ],
    )

    principal = _principal()

    assert get_current_tenant(session=None, principal=principal).tenant_id == "tenant_1"
    assert list_current_tenant_members(session=None, principal=principal)[0].role == "owner"
    assert list_legal_acknowledgements(session=None, principal=principal)[0].document_key
    assert list_data_credentials(session=None, principal=principal)[0].provider == "polygon"
    assert list_data_capabilities(session=None, principal=principal)[0].status == "available"
    assert list_tenant_job_states(session=None, principal=principal)[0].job_type

    created = create_data_credential(
        request=tenant_route.TenantApiKeyCreate(provider="polygon", encrypted_payload="ciphertext"),
        session=None,
        principal=principal,
    )
    assert created.has_encrypted_payload is True
