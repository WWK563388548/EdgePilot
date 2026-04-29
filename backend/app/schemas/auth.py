from pydantic import BaseModel


class AuthMeResponse(BaseModel):
    user_id: str
    account_id: str
    role: str
    email: str | None
    display_name: str | None
    email_verified: bool


class VerificationEmailResponse(BaseModel):
    status: str
    job_id: str | None = None
