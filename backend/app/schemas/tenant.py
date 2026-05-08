from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CapabilityStatus = Literal["available", "stale", "missing", "invalid", "fallback_used", "disabled"]
CredentialStatus = Literal["configured", "missing", "invalid", "disabled"]


class Tenant(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    name: str
    slug: str | None = None
    owner_user_id: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TenantMember(BaseModel):
    tenant_id: str
    user_id: str
    role: str
    email: str | None = None
    display_name: str | None = None
    created_at: datetime | None = None


class LegalAcknowledgementCreate(BaseModel):
    document_key: str = Field(default="private_beta_terms", min_length=1)
    document_version: str = Field(default="v1.5.1", min_length=1)
    metadata_json: dict[str, Any] | None = None


class LegalAcknowledgement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    acknowledgement_id: str
    tenant_id: str
    user_id: str
    document_key: str
    document_version: str
    acknowledged_at: datetime | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata_json: dict[str, Any] | None = None


class TenantApiKeyCreate(BaseModel):
    provider: str = Field(..., min_length=1)
    label: str | None = None
    encrypted_payload: str | None = None
    key_fingerprint: str | None = None
    metadata_json: dict[str, Any] | None = None


class TenantApiKey(BaseModel):
    credential_id: str
    tenant_id: str
    provider: str
    label: str | None = None
    status: CredentialStatus | str | None = None
    key_fingerprint: str | None = None
    has_encrypted_payload: bool = False
    last_verified_at: datetime | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TenantDataCapability(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    capability_id: str
    tenant_id: str
    capability_key: str
    provider: str | None = None
    market: str | None = None
    asset_type: str | None = None
    timeframe: str | None = None
    status: CapabilityStatus | str
    source: str | None = None
    reason: str | None = None
    last_checked_at: datetime | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TenantJobState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    job_type: str
    enabled: bool | None = None
    status: str | None = None
    rate_limit_per_minute: int | None = None
    next_allowed_at: datetime | None = None
    last_run_id: str | None = None
    metadata_json: dict[str, Any] | None = None
    updated_at: datetime | None = None
