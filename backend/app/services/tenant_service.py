from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal, AuthService
from backend.app.schemas.tenant import (
    LegalAcknowledgement,
    LegalAcknowledgementCreate,
    TenantApiKey,
    TenantApiKeyCreate,
    TenantMember,
)


class TenantService:
    @staticmethod
    def current_tenant(session: Session, principal: AuthPrincipal) -> db.Tenant:
        tenant = session.get(db.Tenant, principal.tenant_id)
        if tenant is None:
            raise ValueError("Tenant not found")
        AuthService.ensure_tenant_foundation(session=session, tenant_id=tenant.tenant_id)
        session.commit()
        return tenant

    @staticmethod
    def list_members(session: Session, principal: AuthPrincipal) -> list[TenantMember]:
        TenantService.current_tenant(session, principal)
        statement = (
            select(db.TenantMembership, db.User)
            .join(db.User, db.User.user_id == db.TenantMembership.user_id)
            .where(db.TenantMembership.tenant_id == principal.tenant_id)
            .order_by(db.TenantMembership.created_at.desc())
        )
        return [
            TenantMember(
                tenant_id=membership.tenant_id,
                user_id=membership.user_id,
                role=membership.role,
                email=user.email,
                display_name=user.display_name,
                created_at=membership.created_at,
            )
            for membership, user in session.execute(statement).all()
        ]

    @staticmethod
    def list_acknowledgements(
        session: Session,
        principal: AuthPrincipal,
    ) -> list[db.LegalAcknowledgement]:
        TenantService.current_tenant(session, principal)
        statement = (
            select(db.LegalAcknowledgement)
            .where(
                db.LegalAcknowledgement.tenant_id == principal.tenant_id,
                db.LegalAcknowledgement.user_id == principal.user_id,
            )
            .order_by(db.LegalAcknowledgement.acknowledged_at.desc())
        )
        return list(session.scalars(statement))

    @staticmethod
    def acknowledge_legal_document(
        session: Session,
        principal: AuthPrincipal,
        request: LegalAcknowledgementCreate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LegalAcknowledgement:
        TenantService.current_tenant(session, principal)
        acknowledgement = db.LegalAcknowledgement(
            acknowledgement_id=f"ack_{uuid4().hex}",
            tenant_id=principal.tenant_id,
            user_id=principal.user_id,
            document_key=request.document_key,
            document_version=request.document_version,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=request.metadata_json,
        )
        session.add(acknowledgement)
        session.commit()
        session.refresh(acknowledgement)
        return LegalAcknowledgement.model_validate(acknowledgement)

    @staticmethod
    def list_api_keys(session: Session, principal: AuthPrincipal) -> list[TenantApiKey]:
        TenantService.current_tenant(session, principal)
        statement = (
            select(db.TenantApiKey)
            .where(db.TenantApiKey.tenant_id == principal.tenant_id)
            .order_by(db.TenantApiKey.created_at.desc())
        )
        return [TenantService._api_key_response(row) for row in session.scalars(statement)]

    @staticmethod
    def create_api_key(
        session: Session,
        principal: AuthPrincipal,
        request: TenantApiKeyCreate,
    ) -> TenantApiKey:
        TenantService.current_tenant(session, principal)
        credential = db.TenantApiKey(
            credential_id=f"cred_{uuid4().hex}",
            tenant_id=principal.tenant_id,
            provider=request.provider,
            label=request.label,
            status="configured" if request.encrypted_payload else "missing",
            encrypted_payload=request.encrypted_payload,
            key_fingerprint=request.key_fingerprint,
            metadata_json=request.metadata_json,
        )
        session.add(credential)
        session.flush([credential])
        AuthService.ensure_tenant_foundation(session=session, tenant_id=principal.tenant_id)
        session.commit()
        session.refresh(credential)
        return TenantService._api_key_response(credential)

    @staticmethod
    def list_data_capabilities(
        session: Session,
        principal: AuthPrincipal,
    ) -> list[db.TenantDataCapability]:
        TenantService.current_tenant(session, principal)
        statement = (
            select(db.TenantDataCapability)
            .where(db.TenantDataCapability.tenant_id == principal.tenant_id)
            .order_by(db.TenantDataCapability.capability_key)
        )
        return list(session.scalars(statement))

    @staticmethod
    def list_job_states(session: Session, principal: AuthPrincipal) -> list[db.TenantJobState]:
        TenantService.current_tenant(session, principal)
        statement = (
            select(db.TenantJobState)
            .where(db.TenantJobState.tenant_id == principal.tenant_id)
            .order_by(db.TenantJobState.job_type)
        )
        return list(session.scalars(statement))

    @staticmethod
    def _api_key_response(row: db.TenantApiKey) -> TenantApiKey:
        return TenantApiKey(
            credential_id=row.credential_id,
            tenant_id=row.tenant_id,
            provider=row.provider,
            label=row.label,
            status=row.status,
            key_fingerprint=row.key_fingerprint,
            has_encrypted_payload=bool(row.encrypted_payload),
            last_verified_at=row.last_verified_at,
            metadata_json=row.metadata_json,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
