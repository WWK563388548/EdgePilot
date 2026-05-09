from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from backend.app.api.routes.business import (
    activate_position,
    cancel_position,
    get_account_risk_settings,
    get_notification_preferences,
    count_candidates,
    count_execution_fills,
    count_execution_imports,
    count_exit_alerts,
    count_journal_trades,
    count_job_runs,
    count_notifications,
    count_positions,
    create_candidate,
    create_candidate_plan,
    create_exit_alert,
    close_position,
    evaluate_exit_alerts,
    import_execution_csv,
    create_journal_trade,
    create_position,
    get_dashboard_summary,
    get_candidate_plan,
    get_portfolio_risk,
    preview_candidate_plan,
    get_candidate_outcome,
    reconcile_execution_fill,
    get_scanner_outcome_summary,
    get_candidate_detail,
    list_job_runs,
    list_scanner_outcomes,
    list_candidates,
    list_execution_fills,
    list_execution_imports,
    list_exit_alerts,
    list_journal_trades,
    list_notifications,
    list_positions,
    reduce_position,
    refresh_account_us_etf_oneil_core_scanner,
    recalculate_scanner_outcomes,
    run_automation_job,
    run_account_us_etf_oneil_core_scanner,
    update_candidate,
    update_account_risk_settings,
    update_exit_alert,
    update_notification,
    update_notification_preferences,
    update_position,
    update_position_stop,
    count_scanner_outcomes,
)
from backend.app.api.dependencies import require_verified_user
from backend.app.core.auth import AuthPrincipal
from backend.app.main import app
from backend.app.schemas.business import (
    AccountRiskSettings,
    AccountRiskSettingsUpdate,
    AutomationJobRunRequest,
    Candidate,
    CandidateCreate,
    CandidateDetail,
    CandidatePASetup,
    CandidatePlanCreate,
    CandidatePlanPreview,
    CandidateUpdate,
    DashboardSummary,
    DataFreshnessSummary,
    ExecutionCSVImportRequest,
    ExecutionFill,
    ExecutionFillReconcileRequest,
    ExecutionFillReconciliationResult,
    ExecutionImport,
    ExecutionImportResult,
    ExitAlert,
    ExitAlertCreate,
    ExitAlertEvaluationRequest,
    ExitAlertEvaluationResponse,
    ExitAlertUpdate,
    JournalTrade,
    JournalTradeCreate,
    JobRun,
    MarketContextSummary,
    NotificationEvent,
    NotificationEventUpdate,
    NotificationPreferences,
    NotificationPreferencesUpdate,
    Position,
    PositionActivate,
    PositionClose,
    PositionCloseResponse,
    PositionCreate,
    PositionReduce,
    PositionStopUpdate,
    PositionUpdate,
    PortfolioRiskSummary,
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
        tenant_id="tenant_local",
        role="owner",
        external_subject="local-dev",
        email_verified=True,
    )


def _job_run() -> JobRun:
    return JobRun(
        run_id="job_1",
        account_id="acct_local",
        job_type="market_refresh_scan",
        status="succeeded",
        trigger="manual",
        records_written=4,
        metadata_json={"steps": []},
        started_at=datetime(2026, 5, 6, tzinfo=UTC),
        completed_at=datetime(2026, 5, 6, tzinfo=UTC),
        duration_ms=10,
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


def _notification() -> NotificationEvent:
    return NotificationEvent(
        notification_id="notif_1",
        account_id="acct_local",
        event_type="position_entry_triggered",
        severity="action_required",
        source_type="exit_alert",
        source_id="alert_1",
        target_view="alerts",
        target_id="alert_1",
        metadata_json={"symbol_id": "SPY"},
        created_at=datetime(2026, 4, 26, tzinfo=UTC),
    )


def _trade() -> JournalTrade:
    return JournalTrade(
        trade_id="trade_1",
        symbol_id="SPY",
        entry_ts=datetime(2026, 4, 20, tzinfo=UTC),
        exit_ts=datetime(2026, 4, 26, tzinfo=UTC),
        net_pnl=120.0,
    )


def _execution_import() -> ExecutionImport:
    return ExecutionImport(
        import_id="exec_import_1",
        account_id="acct_local",
        broker="edgepilot_generic_csv",
        status="completed",
        rows_total=1,
        rows_imported=1,
        created_at=datetime(2026, 4, 26, tzinfo=UTC),
    )


def _execution_fill() -> ExecutionFill:
    return ExecutionFill(
        fill_id="exec_fill_1",
        import_id="exec_import_1",
        account_id="acct_local",
        position_id="pos_1",
        idempotency_key="exec_key_1",
        broker="edgepilot_generic_csv",
        symbol_id="SPY",
        asset_type="etf",
        side="buy",
        quantity=1,
        price=421,
        executed_at=datetime(2026, 4, 26, tzinfo=UTC),
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
        lambda session, principal, decision, strategy_name, limit, offset: [_candidate()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "count_candidates",
        lambda session, principal, decision, strategy_name: 1,
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


def test_automation_job_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    captured = {}

    def _fake_run(session, principal, request):
        captured["account_id"] = principal.account_id
        captured["symbols"] = request.symbols
        return _job_run()

    monkeypatch.setattr(business_route.BusinessService, "run_automation_job", _fake_run)
    monkeypatch.setattr(
        business_route.BusinessService,
        "list_job_runs",
        lambda session, principal, status, limit, offset: [_job_run()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "count_job_runs",
        lambda session, principal, status: 1,
    )

    run = run_automation_job(
        session=None,
        principal=_principal(),
        request=AutomationJobRunRequest(symbols=["spy"]),
    )

    assert captured == {"account_id": "acct_local", "symbols": ["SPY"]}
    assert run.status == "succeeded"
    assert list_job_runs(session=None, principal=_principal(), status_filter="succeeded")[0].run_id == "job_1"
    assert count_job_runs(session=None, principal=_principal(), status_filter="succeeded").total == 1


def test_execution_import_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    captured = {}

    def _fake_import(session, principal, request):
        captured["account_id"] = principal.account_id
        captured["csv_text"] = request.csv_text
        return ExecutionImportResult(import_record=_execution_import(), fills=[_execution_fill()])

    monkeypatch.setattr(business_route.ExecutionImportService, "import_csv", _fake_import)
    monkeypatch.setattr(
        business_route.ExecutionImportService,
        "list_imports",
        lambda session, principal, status, limit, offset: [_execution_import()],
    )
    monkeypatch.setattr(
        business_route.ExecutionImportService,
        "count_imports",
        lambda session, principal, status: 1,
    )
    monkeypatch.setattr(
        business_route.ExecutionImportService,
        "list_fills",
        lambda session, principal, symbol_id, position_id, status, reconciliation_status, limit, offset: [_execution_fill()],
    )
    monkeypatch.setattr(
        business_route.ExecutionImportService,
        "count_fills",
        lambda session, principal, symbol_id, position_id, status, reconciliation_status: 1,
    )
    monkeypatch.setattr(
        business_route.ExecutionImportService,
        "reconcile_fill",
        lambda session, principal, fill_id, request: ExecutionFillReconciliationResult(
            fill=_execution_fill(),
            message=f"{fill_id}:{request.action}",
        ),
    )

    result = import_execution_csv(
        session=None,
        principal=_principal(),
        request=ExecutionCSVImportRequest(csv_text="symbol,side,quantity,price,executed_at"),
    )

    assert captured == {
        "account_id": "acct_local",
        "csv_text": "symbol,side,quantity,price,executed_at",
    }
    assert result.import_record.import_id == "exec_import_1"
    assert list_execution_imports(session=None, principal=_principal())[0].import_id == "exec_import_1"
    assert count_execution_imports(session=None, principal=_principal()).total == 1
    assert list_execution_fills(session=None, principal=_principal())[0].fill_id == "exec_fill_1"
    assert count_execution_fills(session=None, principal=_principal()).total == 1
    reconciled = reconcile_execution_fill(
        fill_id="exec_fill_1",
        session=None,
        principal=_principal(),
        request=ExecutionFillReconcileRequest(action="confirm_position"),
    )
    assert reconciled.message == "exec_fill_1:confirm_position"


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
        "get_candidate_plan",
        lambda session, principal, candidate_id: _position().model_copy(
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
    monkeypatch.setattr(
        business_route.BusinessService,
        "activate_position",
        lambda session, principal, position_id, request: _position().model_copy(
            update={"position_id": position_id, "status": "open", "entry_price": request.entry_price}
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_position_stop",
        lambda session, principal, position_id, request: _position().model_copy(
            update={"position_id": position_id, "current_stop": request.new_stop}
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "cancel_position",
        lambda session, principal, position_id: _position().model_copy(
            update={"position_id": position_id, "status": "cancelled", "quantity": 0}
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "reduce_position",
        lambda session, principal, position_id, request: _position().model_copy(
            update={"position_id": position_id, "status": "reduce", "current_stop": request.current_stop}
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "close_position",
        lambda session, principal, position_id, request: PositionCloseResponse(
            position=_position().model_copy(update={"position_id": position_id, "status": "closed"}),
            journal_trade=_trade().model_copy(update={"position_id": position_id}),
        ),
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
    assert (
        get_candidate_plan(
            "cand_1",
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
    activated = activate_position(
        "pos_1",
        PositionActivate(entry_price=421),
        session=None,
        principal=_principal(),
    )
    assert activated.status == "open"
    assert activated.entry_price == 421
    assert (
        update_position_stop(
            "pos_1",
            PositionStopUpdate(new_stop=430),
            session=None,
            principal=_principal(),
        ).current_stop
        == 430
    )
    assert (
        cancel_position(
            "pos_1",
            session=None,
            principal=_principal(),
        ).status
        == "cancelled"
    )
    assert (
        reduce_position(
            "pos_1",
            PositionReduce(exit_price=450, quantity=1, current_stop=430),
            session=None,
            principal=_principal(),
        ).status
        == "reduce"
    )
    closed = close_position(
        "pos_1",
        PositionClose(exit_price=460, exit_reason="manual_review"),
        session=None,
        principal=_principal(),
    )
    assert closed.position.status == "closed"
    assert closed.journal_trade.position_id == "pos_1"


def test_risk_settings_and_plan_preview_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "get_account_risk_settings",
        lambda session, principal: AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=20_000,
            max_risk_per_trade_pct=0.01,
            max_total_risk_pct=0.02,
            max_open_positions=3,
            max_risk_distance_pct=0.1,
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_account_risk_settings",
        lambda session, principal, request: AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=request.account_equity or 10_000,
            max_risk_per_trade_pct=request.max_risk_per_trade_pct or 0.005,
            max_total_risk_pct=request.max_total_risk_pct or 0.02,
            max_open_positions=request.max_open_positions or 3,
            max_risk_distance_pct=request.max_risk_distance_pct or 0.12,
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "get_portfolio_risk",
        lambda session, principal: PortfolioRiskSummary(
            account_id=principal.account_id,
            account_equity=20_000,
            max_total_risk_pct=0.02,
            max_total_risk_amount=400,
            max_open_positions=3,
            active_position_count=1,
            total_risk_amount=120,
            total_risk_pct=0.006,
            remaining_risk_amount=280,
            remaining_risk_pct=0.014,
            planned_risk_amount=0,
            open_risk_amount=120,
            reduced_risk_amount=0,
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "preview_candidate_plan",
        lambda session, principal, candidate_id: CandidatePlanPreview(
            account_id=principal.account_id,
            candidate_id=candidate_id,
            entry_price=100,
            initial_stop=90,
            risk_per_unit=10,
            risk_distance_pct=0.1,
            account_equity=20_000,
            max_risk_per_trade_pct=0.01,
            max_risk_amount=200,
            suggested_quantity=20,
            planned_quantity=20,
            planned_risk_amount=200,
            planned_risk_pct=0.01,
            max_open_positions=3,
            active_position_count=1,
            guardrails=[],
        ),
    )

    settings = get_account_risk_settings(session=None, principal=_principal())
    updated = update_account_risk_settings(
        AccountRiskSettingsUpdate(account_equity=30_000),
        session=None,
        principal=_principal(),
    )
    preview = preview_candidate_plan("cand_1", session=None, principal=_principal())
    portfolio = get_portfolio_risk(session=None, principal=_principal())

    assert settings.account_equity == 20_000
    assert updated.account_equity == 30_000
    assert preview.suggested_quantity == 20
    assert preview.candidate_id == "cand_1"
    assert portfolio.remaining_risk_amount == 280


def test_notification_preference_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "get_notification_preferences",
        lambda session, principal: NotificationPreferences(
            account_id=principal.account_id,
            in_app_enabled=True,
            email_enabled=False,
            sms_enabled=False,
            min_severity="info",
            event_preferences={},
        ),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_notification_preferences",
        lambda session, principal, request: NotificationPreferences(
            account_id=principal.account_id,
            in_app_enabled=True,
            email_enabled=request.email_enabled or False,
            sms_enabled=False,
            min_severity=request.min_severity or "info",
            email_to=request.email_to,
            event_preferences=request.event_preferences or {},
        ),
    )

    defaults = get_notification_preferences(session=None, principal=_principal())
    updated = update_notification_preferences(
        NotificationPreferencesUpdate(
            email_enabled=True,
            email_to="alerts@example.com",
            min_severity="warning",
        ),
        session=None,
        principal=_principal(),
    )

    assert defaults.in_app_enabled is True
    assert updated.email_enabled is True
    assert updated.email_to == "alerts@example.com"
    assert updated.min_severity == "warning"


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
        lambda session, principal, acknowledged, include_snoozed, limit, offset: [_alert()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "count_exit_alerts",
        lambda session, principal, acknowledged, include_snoozed: 1,
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


def test_notification_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "list_notifications",
        lambda session, principal, read, acknowledged, include_snoozed, limit, offset: [
            _notification()
        ],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "count_notifications",
        lambda session, principal, read, acknowledged, include_snoozed: 1,
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_notification",
        lambda session, principal, notification_id, request: _notification(),
    )

    assert list_notifications(
        session=None,
        principal=_principal(),
        read=False,
        acknowledged=False,
        limit=10,
        offset=20,
    )[0].event_type == "position_entry_triggered"
    assert (
        count_notifications(
            session=None,
            principal=_principal(),
            read=False,
            acknowledged=False,
        ).total
        == 1
    )
    assert (
        update_notification(
            "notif_1",
            NotificationEventUpdate(acknowledged=True),
            session=None,
            principal=_principal(),
        ).notification_id
        == "notif_1"
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
        tenant_id=principal.tenant_id,
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
