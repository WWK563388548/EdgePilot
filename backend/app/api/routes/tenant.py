from fastapi import APIRouter, HTTPException, Request, status

from backend.app.api.dependencies import AdminPrincipal, DbSession, VerifiedPrincipal
from backend.app.schemas.tenant import (
    DataSourceCheckResponse,
    LegalAcknowledgement,
    LegalAcknowledgementCreate,
    Tenant,
    TenantApiKey,
    TenantApiKeyCreate,
    TenantDataCapability,
    TenantJobState,
    TenantMember,
)
from backend.app.services.tenant_service import TenantService

router = APIRouter(prefix="/api", tags=["tenant"])


@router.get("/tenants/current", response_model=Tenant)
def get_current_tenant(session: DbSession, principal: VerifiedPrincipal) -> Tenant:
    try:
        return Tenant.model_validate(TenantService.current_tenant(session, principal))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/tenants/current/members", response_model=list[TenantMember])
def list_current_tenant_members(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> list[TenantMember]:
    return TenantService.list_members(session=session, principal=principal)


@router.get("/legal/acknowledgements", response_model=list[LegalAcknowledgement])
def list_legal_acknowledgements(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> list[LegalAcknowledgement]:
    return TenantService.list_acknowledgements(session=session, principal=principal)


@router.post(
    "/legal/acknowledgements",
    response_model=LegalAcknowledgement,
    status_code=status.HTTP_201_CREATED,
)
def acknowledge_legal_document(
    request_body: LegalAcknowledgementCreate,
    request: Request,
    session: DbSession,
    principal: VerifiedPrincipal,
) -> LegalAcknowledgement:
    return TenantService.acknowledge_legal_document(
        session=session,
        principal=principal,
        request=request_body,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/data-credentials", response_model=list[TenantApiKey])
def list_data_credentials(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> list[TenantApiKey]:
    return TenantService.list_api_keys(session=session, principal=principal)


@router.post(
    "/data-credentials",
    response_model=TenantApiKey,
    status_code=status.HTTP_201_CREATED,
)
def create_data_credential(
    request: TenantApiKeyCreate,
    session: DbSession,
    principal: AdminPrincipal,
) -> TenantApiKey:
    return TenantService.create_api_key(session=session, principal=principal, request=request)


@router.post("/data-credentials/{credential_id}/check", response_model=DataSourceCheckResponse)
def check_data_credential(
    credential_id: str,
    session: DbSession,
    principal: AdminPrincipal,
) -> DataSourceCheckResponse:
    try:
        return TenantService.check_api_key(
            session=session,
            principal=principal,
            credential_id=credential_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/data-capabilities", response_model=list[TenantDataCapability])
def list_data_capabilities(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> list[TenantDataCapability]:
    return TenantService.list_data_capabilities(session=session, principal=principal)


@router.post("/data-capabilities/{capability_key}/check", response_model=DataSourceCheckResponse)
def check_data_capability(
    capability_key: str,
    session: DbSession,
    principal: AdminPrincipal,
) -> DataSourceCheckResponse:
    try:
        return TenantService.check_data_capability(
            session=session,
            principal=principal,
            capability_key=capability_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/tenants/current/job-states", response_model=list[TenantJobState])
def list_tenant_job_states(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> list[TenantJobState]:
    return TenantService.list_job_states(session=session, principal=principal)
