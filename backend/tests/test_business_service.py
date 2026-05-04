from datetime import UTC, date, datetime
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.core.database import Base
from backend.app.schemas.business import (
    CandidateCreate,
    CandidatePlanCreate,
    CandidateUpdate,
    ExitAlertEvaluationRequest,
    PositionCreate,
)
from backend.app.schemas.ingestion import AccountETFUniverseRefreshRequest, ETFUniverseSeedResponse
from backend.app.schemas.outcome import ScannerOutcomeRecalculateRequest
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


def _bar(*, symbol: str, ts: datetime, close: float, high: float, low: float) -> db.Bar:
    return db.Bar(
        symbol_id=symbol,
        timeframe="1d",
        ts=ts,
        open=close - 1,
        high=high,
        low=low,
        close=close,
        volume=1_000_000,
        source="test",
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
    assert BusinessService.count_candidates(session, principal, decision="candidate") == 1


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
    assert BusinessService.count_candidates(session, principal) == 3


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
    session.add(
        db.ScannerOutcome(
            outcome_id="outcome_old_a",
            account_id="acct_a",
            candidate_id="cand_old_a",
            symbol_id="SPY",
            timeframe="1d",
            detected_ts=datetime(2026, 4, 26, tzinfo=UTC),
            evaluation_status="pending",
        )
    )
    session.add(
        db.ScannerOutcome(
            outcome_id="outcome_old_b",
            account_id="acct_b",
            candidate_id="cand_old_b",
            symbol_id="QQQ",
            timeframe="1d",
            detected_ts=datetime(2026, 4, 26, tzinfo=UTC),
            evaluation_status="pending",
        )
    )
    session.commit()

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
    assert session.get(db.ScannerOutcome, "outcome_old_a") is None
    assert session.get(db.ScannerOutcome, "outcome_old_b") is not None


def test_scanner_outcomes_are_account_scoped_and_summarized(session) -> None:
    principal_a = _principal("user_a", "acct_a")
    principal_b = _principal("user_b", "acct_b")
    for principal, candidate_id, symbol in (
        (principal_a, "cand_a1", "SPY"),
        (principal_a, "cand_a2", "QQQ"),
        (principal_b, "cand_b1", "IWM"),
    ):
        BusinessService.create_candidate(
            session,
            principal,
            CandidateCreate(
                candidate_id=candidate_id,
                symbol_id=symbol,
                scan_date=date(2026, 4, 26),
                strategy_name="oneil_core_us_etf",
                decision="candidate",
            ),
        )
    session.add(
        db.ScannerOutcome(
            outcome_id="outcome_a1",
            account_id="acct_a",
            candidate_id="cand_a1",
            symbol_id="SPY",
            timeframe="1d",
            detected_ts=datetime(2026, 4, 26, tzinfo=UTC),
            evaluation_status="matured_60d",
            triggered_entry=True,
            stopped_out=False,
            false_breakout=False,
            forward_return_20d=0.12,
            forward_return_60d=0.18,
            mfe_20d=0.16,
            mfe_60d=0.24,
            mae_20d=-0.03,
            mae_60d=-0.04,
        )
    )
    session.add(
        db.ScannerOutcome(
            outcome_id="outcome_a2",
            account_id="acct_a",
            candidate_id="cand_a2",
            symbol_id="QQQ",
            timeframe="1d",
            detected_ts=datetime(2026, 4, 27, tzinfo=UTC),
            evaluation_status="pending",
            triggered_entry=True,
            stopped_out=True,
            false_breakout=True,
            forward_return_20d=-0.02,
        )
    )
    session.add(
        db.ScannerOutcome(
            outcome_id="outcome_b1",
            account_id="acct_b",
            candidate_id="cand_b1",
            symbol_id="IWM",
            timeframe="1d",
            detected_ts=datetime(2026, 4, 28, tzinfo=UTC),
            evaluation_status="matured_60d",
            triggered_entry=True,
            stopped_out=False,
            false_breakout=False,
            forward_return_20d=0.2,
        )
    )
    session.commit()

    outcomes = BusinessService.list_scanner_outcomes(session, principal_a)
    summary = BusinessService.scanner_outcome_summary(session, principal_a)

    assert [row.outcome_id for row in outcomes] == ["outcome_a2", "outcome_a1"]
    assert BusinessService.count_scanner_outcomes(session, principal_a) == 2
    assert BusinessService.count_scanner_outcomes(session, principal_a, symbol="spy") == 1
    assert BusinessService.get_candidate_outcome(session, principal_a, "cand_a1").outcome_id == "outcome_a1"
    assert summary.total == 2
    assert summary.pending_count == 1
    assert summary.matured_count == 1
    assert summary.triggered_count == 2
    assert summary.false_breakout_count == 1
    assert summary.positive_20d_count == 1
    assert summary.trigger_rate == 1
    assert summary.false_breakout_rate == 0.5
    assert summary.positive_20d_rate == 0.5
    assert summary.avg_forward_return_20d == 0.05

    with pytest.raises(ValueError):
        BusinessService.get_candidate_outcome(session, principal_a, "cand_b1")


def test_recalculate_scanner_outcomes_backfills_existing_candidates(session) -> None:
    principal = _principal("user_a", "acct_a")
    detected_ts = datetime(2026, 4, 26)
    setup_id = "pasetup_spy_1d_2026-04-26_breakout"
    session.add(
        db.PASetup(
            setup_id=setup_id,
            symbol_id="SPY",
            timeframe="1d",
            detected_ts=detected_ts,
            setup_type="breakout",
            setup_grade="A",
            pa_quality_score=82,
            entry_plan={"trigger_price": 105},
            exit_plan={"initial_stop": 95},
        )
    )
    session.add(_bar(symbol="SPY", ts=detected_ts, close=100, high=101, low=99))
    for index in range(1, 21):
        session.add(
            _bar(
                symbol="SPY",
                ts=detected_ts + timedelta(days=index),
                close=100 + index,
                high=101 + index,
                low=99 + index,
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
            pa_setup_id=setup_id,
            decision="candidate",
            entry_trigger=105,
            initial_stop=95,
        ),
    )

    response = BusinessService.recalculate_scanner_outcomes(
        session,
        principal,
        ScannerOutcomeRecalculateRequest(),
    )
    outcome = session.get(db.ScannerOutcome, "outcome_cand_spy")

    assert response.account_id == "acct_a"
    assert response.candidates_scanned == 1
    assert response.outcomes_written == 1
    assert response.status_counts == {"matured_20d": 1}
    assert response.symbols_processed == ["SPY"]
    assert outcome is not None
    assert outcome.evaluation_status == "matured_20d"
    assert outcome.forward_return_20d == 0.2

    with pytest.raises(ValueError, match="Candidate not found: missing"):
        BusinessService.recalculate_scanner_outcomes(
            session,
            principal,
            ScannerOutcomeRecalculateRequest(candidate_id="missing"),
        )


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
                    "score": 82,
                    "total_score": 82,
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
    assert detail.scanner_decision.decision == "candidate"
    assert detail.scanner_decision.score == detail.scanner_decision.total_score == 82


def test_create_candidate_plan_from_candidate_is_planned_and_idempotent(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_spy_plan",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            setup_type="breakout",
            decision="candidate",
            entry_trigger=450.14,
            initial_stop=410.5,
        ),
    )

    position = BusinessService.create_candidate_plan(
        session,
        principal,
        "cand_spy_plan",
        CandidatePlanCreate(quantity=3),
    )
    duplicate = BusinessService.create_candidate_plan(
        session,
        principal,
        "cand_spy_plan",
        CandidatePlanCreate(quantity=10),
    )

    assert position.position_id == "plan_cand_spy_plan"
    assert position.symbol_id == "SPY"
    assert position.status == "planned"
    assert position.entry_price == 450.14
    assert position.initial_stop == 410.5
    assert position.current_stop == 410.5
    assert position.quantity == 3
    assert duplicate.position_id == position.position_id
    assert duplicate.quantity == 3
    assert BusinessService.count_positions(session, principal) == 1
    assert BusinessService.count_positions(session, principal, status="planned") == 1
    assert BusinessService.dashboard_summary(session, principal).open_position_count == 0


def test_create_candidate_plan_requires_entry_and_stop(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_missing_plan",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            decision="candidate",
        ),
    )

    with pytest.raises(ValueError, match="missing entry trigger or initial stop"):
        BusinessService.create_candidate_plan(
            session,
            principal,
            "cand_missing_plan",
            CandidatePlanCreate(),
        )


def test_evaluate_exit_alerts_for_planned_entry_is_idempotent(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_plan",
            symbol_id="SPY",
            asset_type="etf",
            status="planned",
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )
    session.add(_bar(symbol="SPY", ts=datetime(2026, 4, 27), close=99, high=101, low=98))
    session.commit()

    response = BusinessService.evaluate_exit_alerts(
        session,
        principal,
        ExitAlertEvaluationRequest(),
    )
    duplicate = BusinessService.evaluate_exit_alerts(
        session,
        principal,
        ExitAlertEvaluationRequest(),
    )

    assert response.positions_evaluated == 1
    assert response.alerts_created == 1
    assert response.alerts[0].position_id == "pos_spy_plan"
    assert response.alerts[0].action == "review_entry"
    assert response.alerts[0].reason == "planned_entry_trigger_reached"
    assert response.alerts[0].new_stop == 90
    assert duplicate.alerts_created == 0
    assert duplicate.duplicate_alerts == 1
    assert BusinessService.count_exit_alerts(session, principal, acknowledged=False) == 1


def test_evaluate_exit_alerts_for_open_position_stop_and_trim(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_qqq_open",
            symbol_id="QQQ",
            asset_type="etf",
            status="open",
            entry_price=100,
            initial_stop=95,
            current_stop=95,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_iwm_open",
            symbol_id="IWM",
            asset_type="etf",
            status="open",
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )
    session.add(_bar(symbol="QQQ", ts=datetime(2026, 4, 27), close=94, high=97, low=93))
    session.add(_bar(symbol="IWM", ts=datetime(2026, 4, 27), close=121, high=122, low=119))
    session.commit()

    response = BusinessService.evaluate_exit_alerts(
        session,
        principal,
        ExitAlertEvaluationRequest(),
    )
    reasons = {alert.reason for alert in response.alerts}

    assert response.positions_evaluated == 2
    assert response.alerts_created == 2
    assert reasons == {"daily_close_below_current_stop", "first_trim_target_reached_2r"}
    assert {alert.action for alert in response.alerts} == {"exit", "trim"}


def test_evaluate_exit_alerts_uses_latest_pa_fact_for_ma_support(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_smh_open",
            symbol_id="SMH",
            asset_type="etf",
            status="open",
            entry_price=100,
            initial_stop=80,
            current_stop=80,
        ),
    )
    ts = datetime(2026, 4, 27)
    session.add(_bar(symbol="SMH", ts=ts, close=95, high=96, low=94))
    session.add(
        db.PAFact(
            fact_id="pafact_smh_1d_2026-04-27",
            symbol_id="SMH",
            timeframe="1d",
            ts=ts,
            facts={"sma_20": 100, "sma_50": 98},
        )
    )
    session.commit()

    response = BusinessService.evaluate_exit_alerts(
        session,
        principal,
        ExitAlertEvaluationRequest(position_id="pos_smh_open"),
    )

    assert response.alerts_created == 1
    assert response.alerts[0].action == "review_exit"
    assert response.alerts[0].reason == "close_below_20_50ma_support"
