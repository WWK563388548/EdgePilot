from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from backend.app.api.routes.business import (
    count_candidates,
    count_exit_alerts,
    count_journal_trades,
    count_positions,
    create_candidate,
    create_candidate_plan,
    create_exit_alert,
    evaluate_exit_alerts,
    create_journal_trade,
    create_position,
    get_dashboard_summary,
    get_candidate_outcome,
    get_scanner_outcome_summary,
    get_candidate_detail,
    list_scanner_outcomes,
    list_candidates,
    list_exit_alerts,
    list_journal_trades,
    list_positions,
    refresh_account_us_etf_oneil_core_scanner,
    recalculate_scanner_outcomes,
    run_account_us_etf_oneil_core_scanner,
    update_candidate,
    update_exit_alert,
    update_position,
    count_scanner_outcomes,
)
from backend.app.api.dependencies import require_verified_user
from backend.app.core.auth import AuthPrincipal
from backend.app.main import app
from backend.app.schemas.business import (
    Candidate,
    CandidateCreate,
    CandidateDetail,
    CandidatePASetup,
    CandidatePlanCreate,
    CandidateUpdate,
    DashboardSummary,
    DataFreshnessSummary,
    ExitAlert,
    ExitAlertCreate,
    ExitAlertEvaluationRequest,
    ExitAlertEvaluationResponse,
    ExitAlertUpdate,
    JournalTrade,
    JournalTradeCreate,
    MarketContextSummary,
    Position,
    PositionCreate,
    PositionUpdate,
)
from backend.app.schemas.ingestion import AccountETFUniverseRefreshRequest, ETFUniverseSeedResponse
from backend.app.schemas.outcome import (
    ScannerOutcome,
    ScannerOutcomeRecalculateRequest,
    ScannerOutcomeRecalculateResponse,
    ScannerOutcomeSummary,
)
from backend.app.schemas.pa import AccountETFOneilScannerRequest, ETFOneilScannerResponse


def _candidate() -> Candidate:
    return Candidate(
        candidate_id="cand_1",
        symbol_id="SPY",
        scan_date=date(2026, 4, 26),
        strategy_name="breakout",
        decision="watch",
        created_at=datetime(2026, 4, 26, tzinfo=UTC),
    )


def _principal() -> AuthPrincipal:
    return AuthPrincipal(
        user_id="user_local",
        account_id="acct_local",
        role="owner",
        external_subject="local-dev",
        email_verified=True,
    )


def _position() -> Position:
    return Position(
        position_id="pos_1",
        symbol_id="SPY",
        asset_type="etf",
        status="open",
        quantity=10,
        created_at=datetime(2026, 4, 26, tzinfo=UTC),
        updated_at=datetime(2026, 4, 26, tzinfo=UTC),
    )


def _alert() -> ExitAlert:
    return ExitAlert(
        alert_id="alert_1",
        position_id="pos_1",
        level=2,
        action="tighten_stop",
        acknowledged=False,
        alert_ts=datetime(2026, 4, 26, tzinfo=UTC),
    )


def _trade() -> JournalTrade:
    return JournalTrade(
        trade_id="trade_1",
        symbol_id="SPY",
        entry_ts=datetime(2026, 4, 20, tzinfo=UTC),
        exit_ts=datetime(2026, 4, 26, tzinfo=UTC),
        net_pnl=120.0,
    )


def _scanner_outcome() -> ScannerOutcome:
    return ScannerOutcome(
        outcome_id="outcome_1",
        account_id="acct_local",
        candidate_id="cand_1",
        symbol_id="SPY",
        timeframe="1d",
        detected_ts=datetime(2026, 4, 26, tzinfo=UTC),
        evaluation_status="matured_60d",
        bars_available=60,
        triggered_entry=True,
        stopped_out=False,
        false_breakout=False,
        forward_return_20d=0.12,
        forward_return_60d=0.18,
    )


def test_candidate_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "create_candidate",
        lambda session, principal, request: _candidate(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "list_candidates",
        lambda session, principal, decision, limit, offset: [_candidate()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "count_candidates",
        lambda session, principal, decision: 1,
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_candidate",
        lambda session, principal, candidate_id, request: _candidate(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "get_candidate_detail",
        lambda session, principal, candidate_id: CandidateDetail(
            candidate=_candidate(),
            pa_setup=CandidatePASetup(
                setup_id="pasetup_1",
                symbol_id="SPY",
                timeframe="1d",
                detected_ts=datetime(2026, 4, 26, tzinfo=UTC),
                setup_type="breakout",
                validation_status="shadow_only",
            ),
            score_breakdown={"total": 82},
        ),
    )

    assert create_candidate(
        CandidateCreate(
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="breakout",
        ),
        session=None,
        principal=_principal(),
    ).candidate_id == "cand_1"
    assert list_candidates(
        session=None,
        principal=_principal(),
        decision="candidate",
        limit=10,
        offset=20,
    )[0].symbol_id == "SPY"
    assert count_candidates(session=None, principal=_principal(), decision="candidate").total == 1
    assert (
        get_candidate_detail("cand_1", session=None, principal=_principal()).pa_setup.setup_id
        == "pasetup_1"
    )
    assert (
        update_candidate(
            "cand_1",
            CandidateUpdate(decision="candidate"),
            session=None,
            principal=_principal(),
        ).decision
        == "watch"
    )


def test_scanner_outcome_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "list_scanner_outcomes",
        lambda session, principal, evaluation_status, symbol, limit, offset: [_scanner_outcome()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "count_scanner_outcomes",
        lambda session, principal, evaluation_status, symbol: 1,
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "scanner_outcome_summary",
        lambda session, principal, evaluation_status, symbol: ScannerOutcomeSummary(
            total=1,
            pending_count=0,
            matured_count=1,
            triggered_count=1,
            stopped_count=0,
            false_breakout_count=0,
            positive_20d_count=1,
            positive_60d_count=1,
            trigger_rate=1,
            positive_20d_rate=1,
            positive_60d_rate=1,
            avg_forward_return_20d=0.12,
            avg_forward_return_60d=0.18,
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "get_candidate_outcome",
        lambda session, principal, candidate_id: _scanner_outcome(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "recalculate_scanner_outcomes",
        lambda session, principal, request: ScannerOutcomeRecalculateResponse(
            account_id=principal.account_id,
            candidates_scanned=1,
            outcomes_written=1,
            status_counts={"matured_20d": 1},
            symbols_processed=["SPY"],
        ),
    )

    assert (
        list_scanner_outcomes(
            session=None,
            principal=_principal(),
            evaluation_status="matured_60d",
            symbol="SPY",
            limit=10,
            offset=20,
        )[0].outcome_id
        == "outcome_1"
    )
    assert (
        count_scanner_outcomes(
            session=None,
            principal=_principal(),
            evaluation_status="matured_60d",
            symbol="SPY",
        ).total
        == 1
    )
    assert (
        get_scanner_outcome_summary(
            session=None,
            principal=_principal(),
            evaluation_status="matured_60d",
            symbol="SPY",
        ).avg_forward_return_20d
        == 0.12
    )
    assert (
        get_candidate_outcome(
            "cand_1",
            session=None,
            principal=_principal(),
        ).outcome_id
        == "outcome_1"
    )
    assert (
        recalculate_scanner_outcomes(
            session=None,
            principal=_principal(),
            request=ScannerOutcomeRecalculateRequest(symbol="spy"),
        ).status_counts
        == {"matured_20d": 1}
    )


def test_account_scanner_route_uses_principal_account(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    captured = {}

    def _fake_scan(session, principal, request):
        captured["account_id"] = principal.account_id
        captured["symbols"] = request.symbols
        return ETFOneilScannerResponse(
            account_id=principal.account_id,
            timeframe=request.timeframe,
            symbols_scanned=request.symbols or ["SPY"],
            facts_written=0,
            setups_written=1,
            candidates_written=1,
            candidates=[_candidate()],
        )

    monkeypatch.setattr(
        business_route.BusinessService,
        "run_account_oneil_core_scanner",
        _fake_scan,
    )

    response = run_account_us_etf_oneil_core_scanner(
        session=None,
        principal=_principal(),
        request=AccountETFOneilScannerRequest(symbols=["spy"]),
    )

    assert captured == {"account_id": "acct_local", "symbols": ["SPY"]}
    assert response.account_id == "acct_local"
    assert response.candidates_written == 1


def test_account_refresh_route_uses_principal_account(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    captured = {}

    def _fake_refresh(session, principal, request):
        captured["account_id"] = principal.account_id
        captured["symbols"] = request.symbols
        return ETFUniverseSeedResponse(
            account_id=principal.account_id,
            timeframe=request.timeframe,
            from_date=request.from_date,
            to_date=request.to_date,
            symbols_requested=request.symbols or ["SPY"],
            bars_written=260,
            facts_written=260,
            setups_written=1,
            candidates_written=1,
            candidates=[_candidate()],
        )

    monkeypatch.setattr(
        business_route.BusinessService,
        "refresh_account_oneil_core_universe",
        _fake_refresh,
    )

    response = refresh_account_us_etf_oneil_core_scanner(
        session=None,
        principal=_principal(),
        request=AccountETFUniverseRefreshRequest(symbols=["spy"]),
    )

    assert captured == {"account_id": "acct_local", "symbols": ["SPY"]}
    assert response.account_id == "acct_local"
    assert response.bars_written == 260


def test_create_candidate_route_maps_validation_error(monkeypatch) -> None:
    from fastapi import HTTPException
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "create_candidate",
        lambda session, principal, request: (_ for _ in ()).throw(
            ValueError("PA setup not found: missing_setup")
        ),
    )

    try:
        create_candidate(
            CandidateCreate(
                symbol_id="SPY",
                scan_date=date(2026, 4, 26),
                strategy_name="breakout",
                pa_setup_id="missing_setup",
            ),
            session=None,
            principal=_principal(),
        )
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "PA setup not found: missing_setup"
    else:
        raise AssertionError("Expected invalid pa_setup_id to be mapped to HTTPException")


def test_position_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "create_position",
        lambda session, principal, request: _position(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "create_candidate_plan",
        lambda session, principal, candidate_id, request: _position().model_copy(
            update={"position_id": f"plan_{candidate_id}", "status": "planned"}
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "list_positions",
        lambda session, principal, status, limit, offset: [_position()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "count_positions",
        lambda session, principal, status: 1,
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_position",
        lambda session, principal, position_id, request: _position(),
    )

    assert (
        create_position(
            PositionCreate(symbol_id="SPY", asset_type="etf"),
            session=None,
            principal=_principal(),
        ).position_id
        == "pos_1"
    )
    assert (
        create_candidate_plan(
            "cand_1",
            CandidatePlanCreate(),
            session=None,
            principal=_principal(),
        ).position_id
        == "plan_cand_1"
    )
    assert list_positions(
        session=None,
        principal=_principal(),
        status_filter="open",
        limit=10,
        offset=20,
    )[0].status == "open"
    assert count_positions(session=None, principal=_principal(), status_filter="open").total == 1
    assert (
        update_position(
            "pos_1",
            PositionUpdate(current_stop=420),
            session=None,
            principal=_principal(),
        ).symbol_id
        == "SPY"
    )


def test_exit_alert_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "create_exit_alert",
        lambda session, principal, request: _alert(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "evaluate_exit_alerts",
        lambda session, principal, request: ExitAlertEvaluationResponse(
            account_id=principal.account_id,
            positions_evaluated=1,
            alerts_created=1,
            symbols_processed=["SPY"],
            alerts=[_alert()],
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "list_exit_alerts",
        lambda session, principal, acknowledged, limit, offset: [_alert()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "count_exit_alerts",
        lambda session, principal, acknowledged: 1,
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_exit_alert",
        lambda session, principal, alert_id, request: _alert(),
    )

    assert (
        create_exit_alert(
            ExitAlertCreate(position_id="pos_1"),
            session=None,
            principal=_principal(),
        ).alert_id
        == "alert_1"
    )
    assert (
        evaluate_exit_alerts(
            ExitAlertEvaluationRequest(),
            session=None,
            principal=_principal(),
        ).alerts_created
        == 1
    )
    assert list_exit_alerts(
        session=None,
        principal=_principal(),
        acknowledged=False,
        limit=10,
        offset=20,
    )[0].level == 2
    assert count_exit_alerts(session=None, principal=_principal(), acknowledged=False).total == 1
    assert (
        update_exit_alert(
            "alert_1",
            ExitAlertUpdate(acknowledged=True),
            session=None,
            principal=_principal(),
        ).position_id
        == "pos_1"
    )


def test_journal_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "create_journal_trade",
        lambda session, principal, request: _trade(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "list_journal_trades",
        lambda session, principal, limit, offset: [_trade()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "count_journal_trades",
        lambda session, principal: 1,
    )

    assert (
        create_journal_trade(
            JournalTradeCreate(symbol_id="SPY"),
            session=None,
            principal=_principal(),
        ).trade_id
        == "trade_1"
    )
    assert list_journal_trades(
        session=None,
        principal=_principal(),
        limit=10,
        offset=20,
    )[0].net_pnl == 120.0
    assert count_journal_trades(session=None, principal=_principal()).total == 1


def test_dashboard_summary_route(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "dashboard_summary",
        lambda session, principal: DashboardSummary(
            market_context=MarketContextSummary(
                snapshot_ts=datetime(2026, 4, 26, tzinfo=UTC),
                risk_level="normal",
            ),
            risk_mode="normal",
            candidate_count=3,
            open_position_count=1,
            exit_alert_count=2,
            highest_exit_level=3,
            data_freshness=[
                DataFreshnessSummary(
                    dataset_key="bars:SPY:1d",
                    last_updated_at=datetime(2026, 4, 26, tzinfo=UTC),
                    source="polygon",
                )
            ],
        ),
    )

    response = get_dashboard_summary(session=None, principal=_principal())

    assert response.risk_mode == "normal"
    assert response.candidate_count == 3


def test_business_routes_require_bearer_token() -> None:
    client = TestClient(app)

    response = client.get("/api/candidates")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"


def test_unverified_email_is_rejected() -> None:
    from fastapi import HTTPException

    principal = _principal()
    principal = AuthPrincipal(
        user_id=principal.user_id,
        account_id=principal.account_id,
        role=principal.role,
        external_subject=principal.external_subject,
        email_verified=False,
    )

    try:
        require_verified_user(principal)
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail == "Email verification required"
    else:
        raise AssertionError("Expected unverified principal to be rejected")
