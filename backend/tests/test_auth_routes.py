from backend.app.api.routes.auth import get_me, resend_verification_email
from backend.app.core.auth import AuthPrincipal


def _principal(email_verified: bool = False) -> AuthPrincipal:
    return AuthPrincipal(
        user_id="user_1",
        account_id="acct_1",
        tenant_id="tenant_1",
        role="owner",
        external_subject="auth0|user_1",
        email="user@example.com",
        display_name="User",
        email_verified=email_verified,
    )


def test_get_me_returns_principal() -> None:
    response = get_me(_principal(email_verified=True))

    assert response.email == "user@example.com"
    assert response.tenant_id == "tenant_1"
    assert response.email_verified is True


def test_resend_verification_email(monkeypatch) -> None:
    from backend.app.api.routes import auth as auth_route

    monkeypatch.setattr(
        auth_route.AuthService,
        "resend_verification_email",
        lambda external_subject: {"status": "pending", "id": "job_1"},
    )

    response = resend_verification_email(_principal(email_verified=False))

    assert response.status == "pending"
    assert response.job_id == "job_1"
