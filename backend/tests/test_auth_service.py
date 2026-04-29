from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.core.auth import AuthService
from backend.app.core.database import Base
from backend.app.models import AccountMembership, User


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
        assert session.get(User, principal.user_id) is not None
        assert session.get(AccountMembership, (principal.account_id, principal.user_id)) is not None
