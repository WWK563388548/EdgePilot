from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.core.database import Base
from backend.app.schemas.business import CandidateCreate, CandidateUpdate
from backend.app.services.business_service import BusinessService


def _principal(user_id: str, account_id: str) -> AuthPrincipal:
    return AuthPrincipal(
        user_id=user_id,
        account_id=account_id,
        role="owner",
        external_subject=user_id,
        email_verified=True,
    )


@pytest.fixture
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-04-26 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db_session:
        for user_id, account_id in (("user_a", "acct_a"), ("user_b", "acct_b")):
            db_session.add(db.User(user_id=user_id, external_subject=user_id))
            db_session.add(db.Account(account_id=account_id, name=account_id))
            db_session.add(
                db.AccountMembership(account_id=account_id, user_id=user_id, role="owner")
            )
        db_session.commit()
        yield db_session


def test_candidate_queries_are_scoped_by_account(session) -> None:
    principal_a = _principal("user_a", "acct_a")
    principal_b = _principal("user_b", "acct_b")

    BusinessService.create_candidate(
        session,
        principal_a,
        CandidateCreate(
            candidate_id="cand_a",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="breakout",
        ),
    )
    BusinessService.create_candidate(
        session,
        principal_b,
        CandidateCreate(
            candidate_id="cand_b",
            symbol_id="QQQ",
            scan_date=date(2026, 4, 26),
            strategy_name="breakout",
        ),
    )

    assert [row.candidate_id for row in BusinessService.list_candidates(session, principal_a)] == [
        "cand_a"
    ]
    assert [row.candidate_id for row in BusinessService.list_candidates(session, principal_b)] == [
        "cand_b"
    ]

    with pytest.raises(ValueError):
        BusinessService.update_candidate(
            session,
            principal_a,
            "cand_b",
            CandidateUpdate(decision="watch"),
        )
