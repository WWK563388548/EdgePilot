from datetime import UTC, date, datetime
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.core.database import Base
from backend.app.schemas.business import (
    AccountRiskSettingsUpdate,
    AutomationJobRunRequest,
    CandidateCreate,
    CandidatePlanCreate,
    CandidateUpdate,
    ExitAlertCreate,
    ExitAlertEvaluationRequest,
    ExitAlertEvaluationResponse,
    ExitAlertUpdate,
    NotificationPreferencesUpdate,
    PositionActivate,
    PositionClose,
    PositionCreate,
    PositionReduce,
    PositionStopUpdate,
)
from backend.app.schemas.ingestion import (
    AccountETFUniverseRefreshRequest,
    ETFUniverseSeedResponse,
    ETFUniverseSeedSymbolResult,
)
from backend.app.schemas.outcome import ScannerOutcomeRecalculateRequest, ScannerOutcomeRecalculateResponse
from backend.app.schemas.pa import AccountETFOneilScannerRequest, ETFOneilScannerResponse
from backend.app.services.business_service import BusinessService
from backend.app.services.data_source_service import DataSourceResolution


def _principal(user_id: str, account_id: str) -> AuthPrincipal:
    return AuthPrincipal(
        user_id=user_id,
        account_id=account_id,
        tenant_id=f"tenant_{account_id}",
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


def test_candidate_queries_can_filter_by_strategy(session) -> None:
    principal = _principal("user_a", "acct_a")

    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_rotation",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="etf_rotation_us_etf",
            decision="candidate",
        ),
    )
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_oneil",
            symbol_id="QQQ",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            decision="candidate",
        ),
    )

    assert [
        row.candidate_id
        for row in BusinessService.list_candidates(
            session,
            principal,
            strategy_name="etf_rotation_us_etf",
        )
    ] == ["cand_rotation"]
    assert (
        BusinessService.count_candidates(
            session,
            principal,
            strategy_name="oneil_core_us_etf",
        )
        == 1
    )


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


def test_candidate_detail_includes_latest_strat_signal(session) -> None:
    principal = _principal("user_a", "acct_a")
    detected_ts = datetime(2026, 4, 26, tzinfo=UTC)
    for offset, ohlc in enumerate(
        (
            (98, 100, 90, 98),
            (100, 102, 97, 101),
            (101, 101.5, 99, 101),
        )
    ):
        session.add(
            db.Bar(
                symbol_id="SPY",
                timeframe="1d",
                ts=(detected_ts - timedelta(days=2 - offset)).replace(tzinfo=None),
                open=ohlc[0],
                high=ohlc[1],
                low=ohlc[2],
                close=ohlc[3],
                volume=1_000_000,
                source="test",
            )
        )
    session.add(
        db.PAFact(
            fact_id="pafact_spy_1d_2026-04-26",
            symbol_id="SPY",
            timeframe="1d",
            ts=detected_ts,
            facts={"sma_20": 101, "distance_to_sma_20_pct": 0.0198},
        )
    )
    session.add(
        db.PASetup(
            setup_id="pasetup_spy_1d_2026-04-26_breakout",
            symbol_id="SPY",
            timeframe="1d",
            detected_ts=detected_ts,
            setup_type="breakout",
            entry_plan={"trigger_price": 105.0},
            validation_status="shadow_only",
        )
    )
    session.add(
        db.StratSignal(
            signal_id="strat_spy_1d_2026-04-26",
            symbol_id="SPY",
            timeframe="1d",
            ts=detected_ts,
            bar_type="2U",
            previous_bar_type="1",
            pattern="inside_breakout",
            direction="long",
            trigger_price=104.0,
            trigger_stop=96.0,
            timeframe_continuity={"1d": "bullish"},
            can_create_trade_alone=False,
        )
    )
    session.flush()
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_spy",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            pa_setup_id="pasetup_spy_1d_2026-04-26_breakout",
            decision="candidate",
        ),
    )

    detail = BusinessService.get_candidate_detail(session, principal, "cand_spy")

    assert detail.strat_signal is not None
    assert detail.strat_signal.pattern == "inside_breakout"
    assert detail.strat_signal.can_create_trade_alone is False
    assert detail.strat_plan is not None
    assert detail.strat_plan.status == "armed"
    assert detail.strat_plan.pattern == "2-1-2_continuation"
    assert detail.strat_plan.order_type == "buy_stop_limit"


def test_account_risk_settings_default_and_update(session) -> None:
    principal = _principal("user_a", "acct_a")

    defaults = BusinessService.get_account_risk_settings(session, principal)
    updated = BusinessService.update_account_risk_settings(
        session,
        principal,
        AccountRiskSettingsUpdate(
            account_equity=25_000,
            max_risk_per_trade_pct=0.01,
            max_total_risk_pct=0.03,
            max_open_positions=4,
            max_risk_distance_pct=0.08,
            shadow_only_requires_paper=False,
        ),
    )

    assert defaults.account_equity == 10_000
    assert defaults.max_risk_per_trade_pct == 0.005
    assert updated.account_equity == 25_000
    assert updated.max_risk_per_trade_pct == 0.01
    assert updated.max_total_risk_pct == 0.03
    assert updated.max_open_positions == 4
    assert updated.max_risk_distance_pct == 0.08
    assert updated.shadow_only_requires_paper is False


def test_notification_preferences_default_and_update(session) -> None:
    principal = _principal("user_a", "acct_a")

    defaults = BusinessService.get_notification_preferences(session, principal)
    updated = BusinessService.update_notification_preferences(
        session,
        principal,
        NotificationPreferencesUpdate(
            email_enabled=True,
            email_to="alerts@example.com",
            min_severity="warning",
            event_preferences={"scanner_candidates_updated": False},
        ),
    )

    assert defaults.in_app_enabled is True
    assert defaults.email_enabled is False
    assert updated.email_enabled is True
    assert updated.email_to == "alerts@example.com"
    assert updated.min_severity == "warning"
    assert updated.event_preferences["scanner_candidates_updated"] is False


def test_notification_table_availability_is_cached_per_session(session, monkeypatch) -> None:
    from backend.app.services.business import notifications

    calls = 0

    class FakeInspector:
        def has_table(self, table_name: str) -> bool:
            return table_name in {
                "notification_preferences",
                "notification_events",
                "notification_delivery_logs",
            }

    def fake_inspect(connection) -> FakeInspector:
        nonlocal calls
        calls += 1
        return FakeInspector()

    monkeypatch.setattr(notifications, "inspect", fake_inspect)

    assert BusinessService._notification_tables_available(session) is True
    assert BusinessService._notification_tables_available(session) is True
    assert calls == 1


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
    notifications = BusinessService.list_notifications(session, principal_a)
    scan_notifications = [
        row for row in notifications if row.event_type == "scanner_candidates_updated"
    ]
    assert len(scan_notifications) == 1
    assert scan_notifications[0].metadata_json["source"] == "manual_scan"


def test_account_scanner_notifies_even_when_no_candidates(session, monkeypatch) -> None:
    from backend.app.services import business_service

    principal = _principal("user_a", "acct_a")

    def _fake_scan(db_session, request):
        assert request.account_id == "acct_a"
        return ETFOneilScannerResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            symbols_scanned=["IWM"],
            facts_written=0,
            setups_written=0,
            candidates_written=0,
            decision_counts={},
        )

    monkeypatch.setattr(
        business_service.ETFScannerService,
        "run_us_etf_oneil_core_for_session",
        _fake_scan,
    )

    response = BusinessService.run_account_oneil_core_scanner(
        session,
        principal,
        AccountETFOneilScannerRequest(symbols=["iwm"], recalculate_facts=False),
    )

    assert response.candidates_written == 0
    notifications = BusinessService.list_notifications(session, principal)
    scan_notifications = [
        row for row in notifications if row.event_type == "scanner_candidates_updated"
    ]
    assert len(scan_notifications) == 1
    assert scan_notifications[0].metadata_json["candidates_written"] == 0


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

    monkeypatch.setattr(
        business_service.DataSourceService,
        "polygon_client_for_tenant",
        lambda db_session, request_principal: (
            object(),
            DataSourceResolution(
                provider="polygon",
                capability_key="market_data.us_etf_daily",
                source="env",
                api_key="secret",
            ),
        ),
    )
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
    notifications = BusinessService.list_notifications(session, principal)
    refresh_notifications = [
        row for row in notifications if row.event_type == "scanner_candidates_updated"
    ]
    assert len(refresh_notifications) == 1
    assert refresh_notifications[0].metadata_json["source"] == "market_refresh_scan"
    assert refresh_notifications[0].metadata_json["data_source"]["provider"] == "polygon"
    assert refresh_notifications[0].metadata_json["candidates_written"] == 1


def test_rotation_refresh_scans_only_successfully_refreshed_symbols(
    session,
    monkeypatch,
) -> None:
    from backend.app.services import business_service

    principal = _principal("user_a", "acct_a")
    captured_symbols: list[str] = []

    monkeypatch.setattr(
        business_service.DataSourceService,
        "polygon_client_for_tenant",
        lambda db_session, request_principal: (
            object(),
            DataSourceResolution(
                provider="polygon",
                capability_key="market_data.us_etf_daily",
                source="env",
                api_key="secret",
            ),
        ),
    )

    def _fake_seed(*, session, client, request):
        return ETFUniverseSeedResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            from_date=request.from_date,
            to_date=request.to_date,
            symbols_requested=["SPY", "QQQ"],
            bars_written=260,
            facts_written=260,
            symbol_results=[
                ETFUniverseSeedSymbolResult(symbol="SPY", status="success", bars_written=260),
                ETFUniverseSeedSymbolResult(
                    symbol="QQQ",
                    status="failed",
                    error_message="Polygon returned no bars",
                ),
            ],
        )

    def _fake_rotation_scan(db_session, request):
        captured_symbols.extend(request.symbols or [])
        return ETFOneilScannerResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            symbols_scanned=request.symbols or [],
            facts_written=0,
            setups_written=1,
            candidates_written=1,
            decision_counts={"candidate": 1},
            latest_scan_date=date(2026, 5, 9),
            latest_bar_date=date(2026, 5, 9),
        )

    monkeypatch.setattr(
        business_service.ETFSeedService,
        "seed_us_etf_universe_for_session",
        _fake_seed,
    )
    monkeypatch.setattr(
        business_service.ETFScannerService,
        "run_us_etf_rotation_for_session",
        _fake_rotation_scan,
    )

    response = BusinessService.refresh_account_etf_rotation_universe(
        session,
        principal,
        AccountETFUniverseRefreshRequest(symbols=["spy", "qqq"]),
    )

    assert captured_symbols == ["SPY"]
    assert response.candidates_written == 1
    assert response.symbols_requested == ["SPY", "QQQ"]
    assert response.skipped_symbols == ["QQQ"]
    notifications = BusinessService.list_notifications(session, principal)
    assert notifications[0].metadata_json["symbols_succeeded"] == 1
    assert notifications[0].metadata_json["symbols_failed"] == 1


def test_rotation_refresh_seeds_benchmark_without_scanning_it(
    session,
    monkeypatch,
) -> None:
    from backend.app.services import business_service

    principal = _principal("user_a", "acct_a")
    seeded_symbols: list[str] = []
    scanned_symbols: list[str] = []

    monkeypatch.setattr(
        business_service.DataSourceService,
        "polygon_client_for_tenant",
        lambda db_session, request_principal: (
            object(),
            DataSourceResolution(
                provider="polygon",
                capability_key="market_data.us_etf_daily",
                source="env",
                api_key="secret",
            ),
        ),
    )

    def _fake_seed(*, session, client, request):
        seeded_symbols.extend(request.symbols or [])
        return ETFUniverseSeedResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            from_date=request.from_date,
            to_date=request.to_date,
            symbols_requested=request.symbols or [],
            bars_written=520,
            facts_written=520,
            symbol_results=[
                ETFUniverseSeedSymbolResult(symbol="QQQ", status="success", bars_written=260),
                ETFUniverseSeedSymbolResult(symbol="SPY", status="success", bars_written=260),
            ],
        )

    def _fake_rotation_scan(db_session, request):
        scanned_symbols.extend(request.symbols or [])
        return ETFOneilScannerResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            symbols_scanned=request.symbols or [],
            facts_written=0,
            setups_written=1,
            candidates_written=1,
            decision_counts={"candidate": 1},
        )

    monkeypatch.setattr(
        business_service.ETFSeedService,
        "seed_us_etf_universe_for_session",
        _fake_seed,
    )
    monkeypatch.setattr(
        business_service.ETFScannerService,
        "run_us_etf_rotation_for_session",
        _fake_rotation_scan,
    )

    BusinessService.refresh_account_etf_rotation_universe(
        session,
        principal,
        AccountETFUniverseRefreshRequest(symbols=["qqq"]),
    )

    assert seeded_symbols == ["QQQ", "SPY"]
    assert scanned_symbols == ["QQQ"]


def test_account_refresh_blocks_before_deleting_when_data_source_missing(
    session,
    monkeypatch,
) -> None:
    from backend.app.core.config import settings

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
    monkeypatch.setattr(settings, "polygon_api_key", "")

    with pytest.raises(ValueError, match="Data source unavailable"):
        BusinessService.refresh_account_oneil_core_universe(
            session,
            principal,
            AccountETFUniverseRefreshRequest(symbols=["iwm"]),
        )

    assert [row.candidate_id for row in BusinessService.list_candidates(session, principal)] == [
        "cand_old"
    ]


def test_account_refresh_blocks_when_runtime_capability_is_stale(session, monkeypatch) -> None:
    from backend.app.core.config import settings

    principal = _principal("user_a", "acct_a")
    monkeypatch.setattr(settings, "polygon_api_key", "")
    session.add(db.Tenant(tenant_id=principal.tenant_id, name="Tenant A"))
    session.add(
        db.TenantApiKey(
            credential_id="cred_polygon",
            tenant_id=principal.tenant_id,
            provider="polygon",
            label="Polygon",
            status="configured",
            encrypted_payload="secret",
        )
    )
    session.add(
        db.TenantDataCapability(
            capability_id="cap_polygon",
            tenant_id=principal.tenant_id,
            capability_key="market_data.us_etf_daily",
            provider="polygon",
            market="US",
            asset_type="etf",
            timeframe="1d",
            status="stale",
            source="tenant_credential",
            reason="Polygon HTTP error: 500",
        )
    )
    session.commit()

    with pytest.raises(ValueError, match="Data source unavailable"):
        BusinessService.refresh_account_oneil_core_universe(
            session,
            principal,
            AccountETFUniverseRefreshRequest(symbols=["iwm"]),
        )

    capability = session.query(db.TenantDataCapability).filter_by(
        tenant_id=principal.tenant_id,
        capability_key="market_data.us_etf_daily",
    ).one()
    assert capability.status == "stale"


def test_run_automation_job_records_successful_steps(session, monkeypatch) -> None:
    principal = _principal("user_a", "acct_a")

    def _fake_refresh(db_session, request_principal, request):
        assert request_principal.account_id == "acct_a"
        assert request.symbols == ["SPY"]
        return ETFUniverseSeedResponse(
            account_id=request_principal.account_id,
            timeframe=request.timeframe,
            from_date=request.from_date,
            to_date=request.to_date,
            symbols_requested=request.symbols or [],
            bars_written=2,
            facts_written=2,
            setups_written=1,
            candidates_written=1,
            decision_counts={"candidate": 1},
            latest_scan_date=date(2026, 5, 4),
            latest_bar_date=date(2026, 5, 4),
        )

    def _fake_outcomes(db_session, request_principal, request):
        assert request.strategy_name == "oneil_core_us_etf"
        return ScannerOutcomeRecalculateResponse(
            account_id=request_principal.account_id,
            candidates_scanned=1,
            outcomes_written=1,
            status_counts={"pending": 1},
            symbols_processed=["SPY"],
        )

    def _fake_alerts(db_session, request_principal, request):
        return ExitAlertEvaluationResponse(
            account_id=request_principal.account_id,
            positions_evaluated=1,
            alerts_created=1,
            symbols_processed=["SPY"],
        )

    monkeypatch.setattr(BusinessService, "refresh_account_oneil_core_universe", _fake_refresh)
    monkeypatch.setattr(BusinessService, "recalculate_scanner_outcomes", _fake_outcomes)
    monkeypatch.setattr(BusinessService, "evaluate_exit_alerts", _fake_alerts)

    run = BusinessService.run_automation_job(
        session,
        principal,
        AutomationJobRunRequest(symbols=["spy"]),
    )

    assert run.status == "succeeded"
    assert run.records_written == 8
    assert run.error_message is None
    assert [step["name"] for step in run.metadata_json["steps"]] == [
        "market_refresh_scan",
        "scanner_outcomes",
        "exit_alerts",
    ]
    assert BusinessService.count_job_runs(session, principal, status="succeeded") == 1
    assert BusinessService.list_job_runs(session, principal)[0].run_id == run.run_id


def test_run_automation_job_preserves_refresh_failure_capability_status(
    session,
    monkeypatch,
) -> None:
    principal = _principal("user_a", "acct_a")

    def _fake_refresh(db_session, request_principal, request):
        return ETFUniverseSeedResponse(
            account_id=request_principal.account_id,
            timeframe=request.timeframe,
            from_date=request.from_date,
            to_date=request.to_date,
            symbols_requested=["SPY"],
            bars_written=0,
            facts_written=0,
            setups_written=0,
            candidates_written=0,
            symbol_results=[
                ETFUniverseSeedSymbolResult(
                    symbol="SPY",
                    status="failed",
                    error_message="Polygon HTTP error: 500",
                )
            ],
        )

    monkeypatch.setattr(BusinessService, "refresh_account_oneil_core_universe", _fake_refresh)

    run = BusinessService.run_automation_job(
        session,
        principal,
        AutomationJobRunRequest(
            symbols=["spy"],
            recalculate_outcomes=False,
            evaluate_alerts=False,
        ),
    )
    summary = run.metadata_json["steps"][0]["summary"]
    capability = session.query(db.TenantDataCapability).filter_by(
        tenant_id=principal.tenant_id,
        capability_key="market_data.us_etf_daily",
    ).one()

    assert run.status == "succeeded"
    assert summary["symbols_failed"] == 1
    assert summary["data_source"]["status"] == "stale"
    assert summary["error_summary"] == "SPY: Polygon HTTP error: 500"
    assert capability.status == "stale"


def test_run_automation_job_persists_failure(session, monkeypatch) -> None:
    principal = _principal("user_a", "acct_a")

    def _fake_refresh(db_session, request_principal, request):
        raise RuntimeError("polygon unavailable")

    monkeypatch.setattr(BusinessService, "refresh_account_oneil_core_universe", _fake_refresh)

    run = BusinessService.run_automation_job(
        session,
        principal,
        AutomationJobRunRequest(symbols=["spy"], recalculate_outcomes=False, evaluate_alerts=False),
    )

    assert run.status == "failed"
    assert run.error_message == "polygon unavailable"
    assert run.records_written == 0
    assert run.metadata_json["steps"][0]["status"] == "failed"
    assert BusinessService.count_job_runs(session, principal, status="failed") == 1


def test_run_automation_job_uses_scan_step_id_for_non_refresh_failure(
    session,
    monkeypatch,
) -> None:
    principal = _principal("user_a", "acct_a")

    def _fake_scan(db_session, request_principal, request):
        raise RuntimeError("rotation scan failed")

    monkeypatch.setattr(BusinessService, "run_account_etf_rotation_scanner", _fake_scan)

    run = BusinessService.run_automation_job(
        session,
        principal,
        AutomationJobRunRequest(
            symbols=["spy"],
            strategy_name="etf_rotation_us_etf",
            refresh_market_data=False,
            recalculate_outcomes=False,
            evaluate_alerts=False,
        ),
    )

    assert run.status == "failed"
    assert run.metadata_json["steps"][0]["name"] == "etf_rotation_scan"
    assert run.metadata_json["steps"][0]["status"] == "failed"


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

    assert BusinessService.get_candidate_plan(session, principal, "cand_spy_plan") is None

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
    assert (
        BusinessService.get_candidate_plan(session, principal, "cand_spy_plan").position_id
        == position.position_id
    )
    notifications = BusinessService.list_notifications(session, principal, acknowledged=False)
    notification_types = [row.event_type for row in notifications]
    assert notification_types.count("candidate_plan_created") == 1
    assert "scanner_candidate_created" in notification_types
    assert BusinessService.count_positions(session, principal) == 1
    assert BusinessService.count_positions(session, principal, status="planned") == 1
    assert BusinessService.dashboard_summary(session, principal).open_position_count == 0


def test_create_candidate_plan_works_when_notification_tables_are_unavailable(
    session,
    monkeypatch,
) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_no_notification_tables",
            symbol_id="IWM",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            setup_type="breakout",
            decision="candidate",
            entry_trigger=280.09,
            initial_stop=264.54,
        ),
    )
    monkeypatch.setattr(
        BusinessService,
        "_notification_tables_available",
        staticmethod(lambda _session: False),
    )

    position = BusinessService.create_candidate_plan(
        session,
        principal,
        "cand_no_notification_tables",
        CandidatePlanCreate(quantity=1),
    )

    assert position.position_id == "plan_cand_no_notification_tables"
    assert position.quantity == 1
    assert BusinessService.list_notifications(session, principal) == []
    assert BusinessService.count_notifications(session, principal, acknowledged=False) == 0
    preferences = BusinessService.get_notification_preferences(session, principal)
    assert preferences.in_app_enabled is True
    assert preferences.email_enabled is False


def test_create_candidate_plan_backfills_missing_legacy_plan_quantity(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_legacy_plan",
            symbol_id="IWM",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            setup_type="breakout",
            decision="candidate",
            entry_trigger=280.09,
            initial_stop=264.54,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="plan_cand_legacy_plan",
            symbol_id="IWM",
            asset_type="etf",
            strategy_name="oneil_core_us_etf",
            status="planned",
            entry_price=280.09,
            initial_stop=264.54,
            current_stop=264.54,
        ),
    )

    preview = BusinessService.preview_candidate_plan(session, principal, "cand_legacy_plan")
    repaired = BusinessService.create_candidate_plan(
        session,
        principal,
        "cand_legacy_plan",
        CandidatePlanCreate(),
    )

    assert preview.planned_quantity == 3
    assert preview.planned_risk_amount == 46.65
    assert preview.portfolio_before.total_risk_amount == 0
    assert preview.portfolio_after_plan.total_risk_amount == 46.65
    assert repaired.quantity == 3
    assert repaired.risk_amount == 46.65
    assert BusinessService.get_portfolio_risk(session, principal).total_risk_amount == 46.65


def test_candidate_plan_preview_sizes_quantity_and_guardrails(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.update_account_risk_settings(
        session,
        principal,
        AccountRiskSettingsUpdate(
            account_equity=20_000,
            max_risk_per_trade_pct=0.01,
            max_open_positions=1,
            max_risk_distance_pct=0.05,
        ),
    )
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_spy_sized",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            setup_type="breakout",
            decision="candidate",
            entry_trigger=100,
            initial_stop=90,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_open_guardrail",
            symbol_id="QQQ",
            asset_type="etf",
            status="open",
            entry_price=100,
            quantity=1,
            initial_stop=90,
            current_stop=90,
        ),
    )

    preview = BusinessService.preview_candidate_plan(
        session,
        principal,
        "cand_spy_sized",
    )
    position = BusinessService.create_candidate_plan(
        session,
        principal,
        "cand_spy_sized",
        CandidatePlanCreate(),
    )

    assert preview.max_risk_amount == 200
    assert preview.risk_per_unit == 10
    assert preview.suggested_quantity == 20
    assert preview.planned_risk_amount == 200
    assert preview.planned_risk_pct == 0.01
    assert {notice.code for notice in preview.guardrails} == {
        "risk_distance_wide",
        "max_open_positions_reached",
    }
    assert position.quantity == 20
    assert position.risk_amount == 200
    assert position.risk_pct == 0.01


def test_portfolio_risk_summary_and_candidate_preview_after_plan(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.update_account_risk_settings(
        session,
        principal,
        AccountRiskSettingsUpdate(
            account_equity=10_000,
            max_risk_per_trade_pct=0.005,
            max_total_risk_pct=0.02,
            max_open_positions=3,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_risk",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
            entry_price=100,
            quantity=10,
            initial_stop=95,
            current_stop=95,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_qqq_risk",
            symbol_id="QQQ",
            asset_type="etf",
            status="planned",
            entry_price=200,
            quantity=4,
            initial_stop=190,
            current_stop=190,
        ),
    )
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_iwm_risk",
            symbol_id="IWM",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            decision="candidate",
            entry_trigger=100,
            initial_stop=90,
        ),
    )

    summary = BusinessService.get_portfolio_risk(session, principal)
    preview = BusinessService.preview_candidate_plan(session, principal, "cand_iwm_risk")

    assert summary.total_risk_amount == 90
    assert summary.total_risk_pct == 0.009
    assert summary.remaining_risk_amount == 110
    assert summary.planned_risk_amount == 40
    assert summary.open_risk_amount == 50
    assert summary.highest_symbol_risk.symbol_id == "SPY"
    assert preview.portfolio_before is not None
    assert preview.portfolio_after_plan is not None
    assert preview.portfolio_before.total_risk_amount == 90
    assert preview.portfolio_after_plan.total_risk_amount == 140
    assert preview.portfolio_after_plan.remaining_risk_amount == 60


def test_candidate_plan_blocks_when_portfolio_risk_budget_exceeded(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.update_account_risk_settings(
        session,
        principal,
        AccountRiskSettingsUpdate(
            account_equity=10_000,
            max_risk_per_trade_pct=0.01,
            max_total_risk_pct=0.01,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_budget",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
            entry_price=100,
            quantity=5,
            initial_stop=90,
            current_stop=90,
        ),
    )
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_budget_block",
            symbol_id="IWM",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            decision="candidate",
            entry_trigger=100,
            initial_stop=90,
        ),
    )

    preview = BusinessService.preview_candidate_plan(session, principal, "cand_budget_block")
    with pytest.raises(ValueError, match="portfolio_risk_budget_exceeded"):
        BusinessService.create_candidate_plan(
            session,
            principal,
            "cand_budget_block",
            CandidatePlanCreate(),
        )

    assert preview.portfolio_after_plan.total_risk_amount == 150
    assert "portfolio_risk_budget_exceeded" in {notice.code for notice in preview.guardrails}


def test_candidate_plan_blocks_invalid_stop(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_invalid_stop",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            decision="candidate",
            entry_trigger=100,
            initial_stop=101,
        ),
    )

    preview = BusinessService.preview_candidate_plan(session, principal, "cand_invalid_stop")
    with pytest.raises(ValueError, match="stop_not_below_entry"):
        BusinessService.create_candidate_plan(
            session,
            principal,
            "cand_invalid_stop",
            CandidatePlanCreate(),
        )

    assert preview.guardrails[0].level == "block"
    assert preview.guardrails[0].code == "stop_not_below_entry"


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


def test_candidate_plan_prefers_armed_strat_trigger(session) -> None:
    principal = _principal("user_a", "acct_a")
    detected_ts = datetime(2026, 4, 26, tzinfo=UTC)
    session.add(
        db.PASetup(
            setup_id="pasetup_spy_armed_strat",
            symbol_id="SPY",
            timeframe="1d",
            detected_ts=detected_ts,
            setup_type="breakout",
            entry_plan={
                "trigger_price": 105.0,
                "scanner_decision": {
                    "decision": "candidate",
                    "strat_confirmation": {
                        "status": "armed",
                        "trigger_price": 110.0,
                    },
                },
            },
            exit_plan={"initial_stop": 100.0},
            validation_status="shadow_only",
        )
    )
    session.flush()
    BusinessService.create_candidate(
        session,
        principal,
        CandidateCreate(
            candidate_id="cand_armed_strat_plan",
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="oneil_core_us_etf",
            pa_setup_id="pasetup_spy_armed_strat",
            entry_trigger=105.0,
            initial_stop=100.0,
            decision="candidate",
        ),
    )

    preview = BusinessService.preview_candidate_plan(
        session,
        principal,
        "cand_armed_strat_plan",
    )

    assert preview.entry_price == 110.0


def test_activate_position_moves_planned_to_open(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_activate",
            symbol_id="SPY",
            asset_type="etf",
            status="planned",
            entry_price=100,
            quantity=2,
            initial_stop=90,
            current_stop=90,
        ),
    )

    activated = BusinessService.activate_position(
        session,
        principal,
        "pos_spy_activate",
        PositionActivate(
            entry_price=101.25,
            quantity=3,
            entry_date=datetime(2026, 4, 27, tzinfo=UTC),
        ),
    )

    assert activated.status == "open"
    assert activated.entry_price == 101.25
    assert activated.quantity == 3
    assert activated.entry_date.replace(tzinfo=UTC) == datetime(2026, 4, 27, tzinfo=UTC)
    assert activated.current_stop == 90
    assert activated.current_r == 0
    assert BusinessService.dashboard_summary(session, principal).open_position_count == 1


def test_activate_position_requires_planned_status(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_open",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )

    with pytest.raises(ValueError, match="must be planned"):
        BusinessService.activate_position(
            session,
            principal,
            "pos_spy_open",
            PositionActivate(entry_price=101),
        )


def test_activate_position_requires_quantity_and_valid_stop(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_no_qty",
            symbol_id="SPY",
            asset_type="etf",
            status="planned",
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_bad_stop",
            symbol_id="SPY",
            asset_type="etf",
            status="planned",
            entry_price=100,
            quantity=1,
            initial_stop=101,
            current_stop=101,
        ),
    )

    with pytest.raises(ValueError, match="quantity is required"):
        BusinessService.activate_position(
            session,
            principal,
            "pos_spy_no_qty",
            PositionActivate(entry_price=101),
        )
    with pytest.raises(ValueError, match="stop must be below entry"):
        BusinessService.activate_position(
            session,
            principal,
            "pos_spy_bad_stop",
            PositionActivate(entry_price=101),
        )


def test_update_position_stop_allows_active_positions(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_stop",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )

    updated = BusinessService.update_position_stop(
        session,
        principal,
        "pos_spy_stop",
        PositionStopUpdate(new_stop=96),
    )

    assert updated.current_stop == 96
    assert updated.initial_stop == 90


def test_cancel_position_marks_planned_as_cancelled_and_removes_risk(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_cancel",
            symbol_id="SPY",
            asset_type="etf",
            status="planned",
            entry_price=100,
            quantity=3,
            initial_stop=90,
            current_stop=90,
        ),
    )
    BusinessService.create_exit_alert(
        session,
        principal,
        ExitAlertCreate(
            alert_id="alert_pos_spy_cancel_entry",
            position_id="pos_spy_cancel",
            action="enter",
            acknowledged=False,
        ),
    )

    cancelled = BusinessService.cancel_position(session, principal, "pos_spy_cancel")

    assert cancelled.status == "cancelled"
    assert cancelled.quantity == 0
    assert cancelled.risk_amount == 0
    assert BusinessService.get_portfolio_risk(session, principal).active_position_count == 0
    assert BusinessService.count_exit_alerts(session, principal) == 0


def test_cancel_position_requires_planned_status(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_cancel_open",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
            entry_price=100,
            quantity=3,
            initial_stop=90,
            current_stop=90,
        ),
    )

    with pytest.raises(ValueError, match="Only planned positions"):
        BusinessService.cancel_position(session, principal, "pos_spy_cancel_open")


def test_reduce_position_marks_trim_and_updates_realized_pnl(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_reduce",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
            entry_price=100,
            quantity=10,
            initial_stop=90,
            current_stop=90,
        ),
    )

    reduced = BusinessService.reduce_position(
        session,
        principal,
        "pos_spy_reduce",
        PositionReduce(exit_price=120, quantity=4, current_stop=100),
    )

    assert reduced.status == "reduce"
    assert reduced.quantity == 6
    assert reduced.current_stop == 100
    assert reduced.realized_pnl == 80
    assert reduced.current_r == 2
    journal_rows = BusinessService.list_journal_trades(session, principal)
    assert len(journal_rows) == 1
    assert journal_rows[0].position_id == "pos_spy_reduce"
    assert journal_rows[0].quantity == 4
    assert journal_rows[0].net_pnl == 80
    assert journal_rows[0].r_multiple == 2
    assert journal_rows[0].exit_reason == "trim"
    assert BusinessService.dashboard_summary(session, principal).open_position_count == 1


def test_reduce_position_requires_quantity(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_reduce_no_qty",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
            entry_price=100,
            quantity=10,
            initial_stop=90,
            current_stop=90,
        ),
    )

    with pytest.raises(ValueError, match="Reduced quantity is required"):
        BusinessService.reduce_position(
            session,
            principal,
            "pos_spy_reduce_no_qty",
            PositionReduce(exit_price=120),
        )


def test_close_position_creates_journal_trade(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_close",
            symbol_id="SPY",
            asset_type="etf",
            strategy_name="oneil_core_us_etf",
            status="open",
            entry_date=datetime(2026, 4, 27, tzinfo=UTC),
            entry_price=100,
            quantity=3,
            initial_stop=90,
            current_stop=95,
        ),
    )

    response = BusinessService.close_position(
        session,
        principal,
        "pos_spy_close",
        PositionClose(
            exit_price=115,
            exit_date=datetime(2026, 5, 1, tzinfo=UTC),
            exit_reason="manual_review",
            notes="Follow-through faded.",
        ),
    )

    assert response.position.status == "closed"
    assert response.position.quantity == 0
    assert response.position.realized_pnl == 45
    assert response.position.current_r == 1.5
    assert response.journal_trade.trade_id == "trade_pos_spy_close"
    assert response.journal_trade.position_id == "pos_spy_close"
    assert response.journal_trade.symbol_id == "SPY"
    assert response.journal_trade.net_pnl == 45
    assert response.journal_trade.r_multiple == 1.5
    assert response.journal_trade.exit_reason == "manual_review"
    assert BusinessService.count_journal_trades(session, principal) == 1
    assert BusinessService.dashboard_summary(session, principal).open_position_count == 0


def test_close_position_after_reduce_keeps_journal_legs_separate(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_reduce_then_close",
            symbol_id="SPY",
            asset_type="etf",
            strategy_name="oneil_core_us_etf",
            status="open",
            entry_date=datetime(2026, 4, 27, tzinfo=UTC),
            entry_price=100,
            quantity=10,
            initial_stop=90,
            current_stop=90,
        ),
    )

    BusinessService.reduce_position(
        session,
        principal,
        "pos_spy_reduce_then_close",
        PositionReduce(exit_price=120, quantity=4, current_stop=100),
    )
    response = BusinessService.close_position(
        session,
        principal,
        "pos_spy_reduce_then_close",
        PositionClose(exit_price=115, exit_reason="manual_review"),
    )

    assert response.position.status == "closed"
    assert response.position.realized_pnl == 170
    assert response.journal_trade.net_pnl == 90
    journal_rows = BusinessService.list_journal_trades(session, principal)
    assert len(journal_rows) == 2
    assert sum(row.net_pnl or 0 for row in journal_rows) == 170


def test_close_position_requires_active_position(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_planned_close",
            symbol_id="SPY",
            asset_type="etf",
            status="planned",
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )

    with pytest.raises(ValueError, match="must be activated"):
        BusinessService.close_position(
            session,
            principal,
            "pos_spy_planned_close",
            PositionClose(exit_price=101),
        )


def test_close_position_rejects_cancelled_or_mismatched_quantity(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_cancelled_close",
            symbol_id="SPY",
            asset_type="etf",
            status="cancelled",
            entry_price=100,
            quantity=0,
            initial_stop=90,
            current_stop=90,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_spy_close_qty",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
            entry_price=100,
            quantity=3,
            initial_stop=90,
            current_stop=90,
        ),
    )

    with pytest.raises(ValueError, match="Cancelled positions"):
        BusinessService.close_position(
            session,
            principal,
            "pos_spy_cancelled_close",
            PositionClose(exit_price=101),
        )
    with pytest.raises(ValueError, match="smaller than current"):
        BusinessService.close_position(
            session,
            principal,
            "pos_spy_close_qty",
            PositionClose(exit_price=101, quantity=2),
        )
    with pytest.raises(ValueError, match="exceeds current"):
        BusinessService.close_position(
            session,
            principal,
            "pos_spy_close_qty",
            PositionClose(exit_price=101, quantity=4),
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
    notifications = BusinessService.list_notifications(
        session,
        principal,
        acknowledged=False,
    )
    assert [row.event_type for row in notifications] == ["position_entry_triggered"]
    assert notifications[0].metadata_json["symbol_id"] == "SPY"

    BusinessService.update_exit_alert(
        session,
        principal,
        response.alerts[0].alert_id,
        ExitAlertUpdate(acknowledged=True),
    )

    assert BusinessService.count_notifications(session, principal, acknowledged=False) == 0
    assert BusinessService.count_notifications(session, principal, acknowledged=True) == 1


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
    assert max(alert.level for alert in response.alerts if alert.reason == "daily_close_below_current_stop") == 4


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


def test_evaluate_exit_alerts_v2_adds_breakeven_time_and_failed_breakout_rules(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_breakeven",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_time_stop",
            symbol_id="QQQ",
            asset_type="etf",
            status="open",
            entry_date=datetime(2026, 4, 1),
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_failed_breakout",
            symbol_id="IWM",
            asset_type="etf",
            status="open",
            entry_date=datetime(2026, 4, 25),
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )
    session.add(_bar(symbol="SPY", ts=datetime(2026, 4, 27), close=111, high=112, low=110))
    session.add(_bar(symbol="QQQ", ts=datetime(2026, 4, 27), close=103, high=104, low=102))
    session.add(_bar(symbol="IWM", ts=datetime(2026, 4, 27), close=99, high=101, low=98))
    session.add(
        db.PAFact(
            fact_id="pafact_iwm_1d_2026-04-27",
            symbol_id="IWM",
            timeframe="1d",
            ts=datetime(2026, 4, 27),
            facts={"relative_volume": 1.5},
        )
    )
    session.commit()

    response = BusinessService.evaluate_exit_alerts(
        session,
        principal,
        ExitAlertEvaluationRequest(),
    )
    reasons = {alert.reason for alert in response.alerts}

    assert "move_stop_to_breakeven_after_1r" in reasons
    assert "time_stop_no_progress_20d" in reasons
    assert "failed_breakout_heavy_volume" in reasons


def test_evaluate_exit_alerts_v2_adds_trailing_and_market_context_rules(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_trail",
            symbol_id="SMH",
            asset_type="etf",
            status="open",
            entry_price=100,
            initial_stop=90,
            current_stop=100,
        ),
    )
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_market",
            symbol_id="SOXX",
            asset_type="etf",
            status="open",
            entry_price=100,
            initial_stop=90,
            current_stop=90,
        ),
    )
    session.add(_bar(symbol="SMH", ts=datetime(2026, 4, 27), close=125, high=126, low=124))
    session.add(_bar(symbol="SOXX", ts=datetime(2026, 4, 27), close=99, high=100, low=98))
    session.add(
        db.PAFact(
            fact_id="pafact_smh_1d_2026-04-27",
            symbol_id="SMH",
            timeframe="1d",
            ts=datetime(2026, 4, 27),
            facts={"sma_20": 115},
        )
    )
    session.add(
        db.PAFact(
            fact_id="pafact_soxx_1d_2026-04-27",
            symbol_id="SOXX",
            timeframe="1d",
            ts=datetime(2026, 4, 27),
            facts={"sma_20": 105},
        )
    )
    session.add(
        db.MarketContextSnapshot(
            market="global",
            snapshot_ts=datetime(2026, 4, 27),
            risk_level="shock",
            us_bias="bearish",
        )
    )
    session.commit()

    response = BusinessService.evaluate_exit_alerts(
        session,
        principal,
        ExitAlertEvaluationRequest(),
    )
    reasons = {alert.reason for alert in response.alerts}

    assert "trail_stop_to_20ma_after_profit" in reasons
    assert "market_regime_risk_off" in reasons


def test_snoozed_exit_alerts_are_hidden_until_due(session) -> None:
    principal = _principal("user_a", "acct_a")
    BusinessService.create_position(
        session,
        principal,
        PositionCreate(
            position_id="pos_snooze",
            symbol_id="SPY",
            asset_type="etf",
            status="open",
        ),
    )
    alert = BusinessService.create_exit_alert(
        session,
        principal,
        ExitAlertCreate(
            alert_id="alert_snoozed",
            position_id="pos_snooze",
            level=1,
            action="review_exit",
            snoozed_until=datetime(2099, 5, 1, tzinfo=UTC),
        ),
    )

    visible = BusinessService.list_exit_alerts(session, principal, acknowledged=False)
    included = BusinessService.list_exit_alerts(
        session,
        principal,
        acknowledged=False,
        include_snoozed=True,
    )

    assert alert.snoozed_until.replace(tzinfo=UTC) == datetime(2099, 5, 1, tzinfo=UTC)
    assert visible == []
    assert [row.alert_id for row in included] == ["alert_snoozed"]
