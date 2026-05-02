from datetime import UTC, date, datetime

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


def test_candidate_queries_can_filter_by_decision(session) -> None:
    principal = _principal("user_a", "acct_a")

    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_ready",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="breakout",
            decision="candidate",
        ),
    )
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_watch",
            symbol_id="QQQ",
            scan_date=date(2026, 4, 26),
            strategy_name="breakout",
            decision="watch",
        ),
    )

    assert [
        row.candidate_id
        for row in BusinessService.list_candidates(session, principal, decision="candidate")
    ] == ["cand_ready"]


def test_dashboard_candidate_count_only_counts_candidates(session) -> None:
    principal = _principal("user_a", "acct_a")

    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_ready",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="breakout",
            decision="candidate",
        ),
    )
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_watch",
            symbol_id="QQQ",
            scan_date=date(2026, 4, 26),
            strategy_name="breakout",
            decision="watch",
        ),
    )

    assert BusinessService.dashboard_summary(session, principal).candidate_count == 1


def test_candidate_create_validates_pa_setup_id(session) -> None:
    principal = _principal("user_a", "acct_a")

    with pytest.raises(ValueError, match="PA setup not found: missing_setup"):
        BusinessService.create_candidate(
            session,
            principal,
            CandidateCreate(
                candidate_id="cand_bad_setup",
                symbol_id="SPY",
                scan_date=date(2026, 4, 26),
                strategy_name="oneil_core_us_etf",
                pa_setup_id="missing_setup",
            ),
        )

    assert BusinessService.list_candidates(session, principal) == []


def test_candidate_update_validates_pa_setup_id(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_spy",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
        ),
    )

    with pytest.raises(ValueError, match="PA setup not found: missing_setup"):
        BusinessService.update_candidate(
            session,
            principal,
            "cand_spy",
            CandidateUpdate(pa_setup_id="missing_setup"),
        )

    detail = BusinessService.get_candidate_detail(session, principal, "cand_spy")
    assert detail.candidate.pa_setup_id is None


def test_candidate_detail_includes_linked_pa_setup(session) -> None:
    principal = _principal("user_a", "acct_a")
    session.add(
        db.PASetup(
            setup_id="pasetup_spy_1d_2026-04-26_breakout",
            symbol_id="SPY",
            timeframe="1d",
            detected_ts=datetime(2026, 4, 26, tzinfo=UTC),
            setup_type="breakout",
            setup_grade="A",
            pa_quality_score=82,
            entry_plan={
                "trigger_price": 510.5,
                "score_breakdown": {"trend": 25, "total": 82},
                "scanner_decision": {
                    "decision": "candidate",
                    "passed_rules": [{"key": "trend_aligned"}],
                    "upgrade_conditions": ["break_above_trigger"],
                },
            },
            exit_plan={"initial_stop": 480},
            invalidation={"price_below": 480},
            validation_status="shadow_only",
            status="candidate",
        )
    )
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_spy",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            setup_type="breakout",
            pa_setup_id="pasetup_spy_1d_2026-04-26_breakout",
        ),
    )

    detail = BusinessService.get_candidate_detail(session, principal, "cand_spy")

    assert detail.candidate.pa_setup_id == "pasetup_spy_1d_2026-04-26_breakout"
    assert detail.pa_setup is not None
    assert detail.pa_setup.setup_grade == "A"
    assert detail.score_breakdown == {"trend": 25, "total": 82}
    assert detail.scanner_decision is not None
    assert detail.scanner_decision["decision"] == "candidate"
