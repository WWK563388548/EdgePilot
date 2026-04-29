import httpx
from fastapi import APIRouter, HTTPException, status

from backend.app.api.dependencies import CurrentPrincipal
from backend.app.core.auth import AuthService
from backend.app.schemas.auth import AuthMeResponse, VerificationEmailResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=AuthMeResponse)
def get_me(principal: CurrentPrincipal) -> AuthMeResponse:
    return AuthMeResponse(
        user_id=principal.user_id,
        account_id=principal.account_id,
        role=principal.role,
        email=principal.email,
        display_name=principal.display_name,
        email_verified=principal.email_verified,
    )


@router.post("/resend-verification", response_model=VerificationEmailResponse)
def resend_verification_email(principal: CurrentPrincipal) -> VerificationEmailResponse:
    if principal.email_verified:
        return VerificationEmailResponse(status="already_verified")

    try:
        response = AuthService.resend_verification_email(principal.external_subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to request Auth0 verification email",
        ) from exc

    return VerificationEmailResponse(status=response.get("status", "pending"), job_id=response.get("id"))
