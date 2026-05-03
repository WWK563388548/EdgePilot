from datetime import UTC, date, datetime
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.core.database import Base
from backend.app.schemas.business import CandidateCreate, CandidateUpdate
from backend.app.schemas.ingestion import AccountETFUniverseRefreshRequest, ETFUniverseSeedResponse
from backend.app.schemas.pa import AccountETFOneilScannerRequest, ETFOneilScannerResponse
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


def test_candidate_queries_support_offset_pagination(session) -> None:
    principal = _principal("user_a", "acct_a")
    for index, symbol in enumerate(("AAA", "BBB", "CCC")):
        BusinessService.create_candidate(
            session,
            principal,
            CandidateCreate(
                candidate_id=f"cand_{index}",
                symbol_id=symbol,
                scan_date=date(2026, 4, 26) + timedelta(days=index),
                strategy_name="breakout",
                decision="candidate",
            ),
        )

    assert [
        row.candidate_id
        for row in BusinessService.list_candidates(session, principal, limit=1, offset=1)
    ] == ["cand_1"]


def test_account_scanner_replaces_only_current_account_candidates(session, monkeypatch) -> None:
    from backend.app.services import business_service

    principal_a = _principal("user_a", "acct_a")
    principal_b = _principal("user_b", "acct_b")
    BusinessService.create_candidate(
        session,
        principal_a,
        CandidateCreate(
            candidate_id="cand_old_a",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            decision="candidate",
        ),
    )
    BusinessService.create_candidate(
        session,
        principal_b,
        CandidateCreate(
            candidate_id="cand_old_b",
            symbol_id="QQQ",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            decision="candidate",
        ),
    )

    def _fake_scan(db_session, request):
        assert request.account_id == "acct_a"
        db_session.add(
            db.Candidate(
                candidate_id="cand_new_a",
                account_id=request.account_id,
                symbol_id="IWM",
                scan_date=date(2026, 4, 27),
                strategy_name="oneil_core_us_etf",
                decision="candidate",
            )
        )
        return ETFOneilScannerResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            symbols_scanned=["IWM"],
            facts_written=0,
            setups_written=1,
            candidates_written=1,
        )

    monkeypatch.setattr(
        business_service.ETFScannerService,
        "run_us_etf_oneil_core_for_session",
        _fake_scan,
    )

    response = BusinessService.run_account_oneil_core_scanner(
        session,
        principal_a,
        AccountETFOneilScannerRequest(symbols=["iwm"], recalculate_facts=False),
    )

    assert response.account_id == "acct_a"
    assert [row.candidate_id for row in BusinessService.list_candidates(session, principal_a)] == [
        "cand_new_a"
    ]
    assert [row.candidate_id for row in BusinessService.list_candidates(session, principal_b)] == [
        "cand_old_b"
    ]


def test_account_refresh_replaces_current_account_candidates(session, monkeypatch) -> None:
    from backend.app.services import business_service

    principal = _principal("user_a", "acct_a")
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_old",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            decision="candidate",
        ),
    )

    def _fake_seed(*, session, client, request):
        assert request.account_id == "acct_a"
        session.add(
            db.Candidate(
                candidate_id="cand_refresh",
                account_id=request.account_id,
                symbol_id="IWM",
                scan_date=date(2026, 4, 27),
                strategy_name="oneil_core_us_etf",
                decision="candidate",
            )
        )
        return ETFUniverseSeedResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            from_date=request.from_date,
            to_date=request.to_date,
            symbols_requested=request.symbols or ["IWM"],
            bars_written=260,
            facts_written=260,
            setups_written=1,
            candidates_written=1,
        )

    monkeypatch.setattr(business_service.ETFSeedService, "_client", lambda: object())
    monkeypatch.setattr(
        business_service.ETFSeedService,
        "seed_us_etf_universe_for_session",
        _fake_seed,
    )

    response = BusinessService.refresh_account_oneil_core_universe(
        session,
        principal,
        AccountETFUniverseRefreshRequest(symbols=["iwm"]),
    )

    assert response.account_id == "acct_a"
    assert response.bars_written == 260
    assert [row.candidate_id for row in BusinessService.list_candidates(session, principal)] == [
        "cand_refresh"
    ]


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
