from fastapi import APIRouter, HTTPException, Query, status

from backend.app.api.dependencies import DbSession, TraderPrincipal, VerifiedPrincipal
from backend.app.schemas.common import CountResponse
from backend.app.schemas.business import (
    AccountRiskSettings,
    AccountRiskSettingsUpdate,
    AutomationJobRunRequest,
    Candidate,
    CandidateCreate,
    CandidateDetail,
    CandidatePlanCreate,
    CandidatePlanPreview,
    CandidateUpdate,
    DashboardSummary,
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
    PositionStatus,
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
from backend.app.schemas.pa import (
    AccountETFRotationScannerRequest,
    AccountETFOneilScannerRequest,
    ETFOneilScannerResponse,
)
from backend.app.services.business_service import BusinessService
from backend.app.services.execution_import_service import ExecutionImportService

router = APIRouter(prefix="/api", tags=["business"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(session: DbSession, principal: VerifiedPrincipal) -> DashboardSummary:
    return BusinessService.dashboard_summary(session=session, principal=principal)


@router.get("/settings/risk", response_model=AccountRiskSettings)
def get_account_risk_settings(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> AccountRiskSettings:
    return BusinessService.get_account_risk_settings(session=session, principal=principal)


@router.patch("/settings/risk", response_model=AccountRiskSettings)
def update_account_risk_settings(
    request: AccountRiskSettingsUpdate,
    session: DbSession,
    principal: TraderPrincipal,
) -> AccountRiskSettings:
    return BusinessService.update_account_risk_settings(
        session=session,
        principal=principal,
        request=request,
    )


@router.get("/settings/notifications", response_model=NotificationPreferences)
def get_notification_preferences(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> NotificationPreferences:
    return BusinessService.get_notification_preferences(session=session, principal=principal)


@router.patch("/settings/notifications", response_model=NotificationPreferences)
def update_notification_preferences(
    request: NotificationPreferencesUpdate,
    session: DbSession,
    principal: TraderPrincipal,
) -> NotificationPreferences:
    return BusinessService.update_notification_preferences(
        session=session,
        principal=principal,
        request=request,
    )


@router.get("/risk/portfolio", response_model=PortfolioRiskSummary)
def get_portfolio_risk(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> PortfolioRiskSummary:
    return BusinessService.get_portfolio_risk(session=session, principal=principal)


@router.post("/jobs/automation/run", response_model=JobRun)
def run_automation_job(
    request: AutomationJobRunRequest,
    session: DbSession,
    principal: TraderPrincipal,
) -> JobRun:
    return BusinessService.run_automation_job(session=session, principal=principal, request=request)


@router.get("/jobs/runs", response_model=list[JobRun])
def list_job_runs(
    session: DbSession,
    principal: VerifiedPrincipal,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[JobRun]:
    return BusinessService.list_job_runs(
        session=session,
        principal=principal,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/jobs/runs/count", response_model=CountResponse)
def count_job_runs(
    session: DbSession,
    principal: VerifiedPrincipal,
    status_filter: str | None = Query(default=None, alias="status"),
) -> CountResponse:
    return CountResponse(
        total=BusinessService.count_job_runs(
            session=session,
            principal=principal,
            status=status_filter,
        )
    )


@router.post(
    "/execution/imports/csv",
    response_model=ExecutionImportResult,
    status_code=status.HTTP_201_CREATED,
)
def import_execution_csv(
    request: ExecutionCSVImportRequest,
    session: DbSession,
    principal: TraderPrincipal,
) -> ExecutionImportResult:
    return ExecutionImportService.import_csv(session=session, principal=principal, request=request)


@router.get("/execution/imports", response_model=list[ExecutionImport])
def list_execution_imports(
    session: DbSession,
    principal: VerifiedPrincipal,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ExecutionImport]:
    return ExecutionImportService.list_imports(
        session=session,
        principal=principal,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/execution/imports/count", response_model=CountResponse)
def count_execution_imports(
    session: DbSession,
    principal: VerifiedPrincipal,
    status_filter: str | None = Query(default=None, alias="status"),
) -> CountResponse:
    return CountResponse(
        total=ExecutionImportService.count_imports(
            session=session,
            principal=principal,
            status=status_filter,
        )
    )


@router.get("/execution/fills", response_model=list[ExecutionFill])
def list_execution_fills(
    session: DbSession,
    principal: VerifiedPrincipal,
    symbol_id: str | None = None,
    position_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    reconciliation_status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ExecutionFill]:
    return ExecutionImportService.list_fills(
        session=session,
        principal=principal,
        symbol_id=symbol_id,
        position_id=position_id,
        status=status_filter,
        reconciliation_status=reconciliation_status,
        limit=limit,
        offset=offset,
    )


@router.get("/execution/fills/count", response_model=CountResponse)
def count_execution_fills(
    session: DbSession,
    principal: VerifiedPrincipal,
    symbol_id: str | None = None,
    position_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    reconciliation_status: str | None = None,
) -> CountResponse:
    return CountResponse(
        total=ExecutionImportService.count_fills(
            session=session,
            principal=principal,
            symbol_id=symbol_id,
            position_id=position_id,
            status=status_filter,
            reconciliation_status=reconciliation_status,
        )
    )


@router.post("/execution/fills/{fill_id}/reconcile", response_model=ExecutionFillReconciliationResult)
def reconcile_execution_fill(
    fill_id: str,
    request: ExecutionFillReconcileRequest,
    session: DbSession,
    principal: TraderPrincipal,
) -> ExecutionFillReconciliationResult:
    try:
        return ExecutionImportService.reconcile_fill(
            session=session,
            principal=principal,
            fill_id=fill_id,
            request=request,
        )
    except ValueError as exc:
        status_code = 404 if str(exc).startswith(("Execution fill not found", "Target position not found")) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/candidates", response_model=Candidate, status_code=status.HTTP_201_CREATED)
def create_candidate(
    request: CandidateCreate,
    session: DbSession,
    principal: TraderPrincipal,
) -> Candidate:
    try:
        return BusinessService.create_candidate(session=session, principal=principal, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/candidates", response_model=list[Candidate])
def list_candidates(
    session: DbSession,
    principal: VerifiedPrincipal,
    decision: str | None = None,
    strategy_name: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[Candidate]:
    return BusinessService.list_candidates(
        session=session,
        principal=principal,
        decision=decision,
        strategy_name=strategy_name,
        limit=limit,
        offset=offset,
    )


@router.get("/candidates/count", response_model=CountResponse)
def count_candidates(
    session: DbSession,
    principal: VerifiedPrincipal,
    decision: str | None = None,
    strategy_name: str | None = None,
) -> CountResponse:
    return CountResponse(
        total=BusinessService.count_candidates(
            session=session,
            principal=principal,
            decision=decision,
            strategy_name=strategy_name,
        )
    )


@router.post(
    "/candidates/scanners/us-etf/oneil-core",
    response_model=ETFOneilScannerResponse,
)
def run_account_us_etf_oneil_core_scanner(
    session: DbSession,
    principal: TraderPrincipal,
    request: AccountETFOneilScannerRequest | None = None,
) -> ETFOneilScannerResponse:
    try:
        return BusinessService.run_account_oneil_core_scanner(
            session=session,
            principal=principal,
            request=request or AccountETFOneilScannerRequest(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/candidates/scanners/us-etf/oneil-core/refresh",
    response_model=ETFUniverseSeedResponse,
)
def refresh_account_us_etf_oneil_core_scanner(
    session: DbSession,
    principal: TraderPrincipal,
    request: AccountETFUniverseRefreshRequest | None = None,
) -> ETFUniverseSeedResponse:
    try:
        return BusinessService.refresh_account_oneil_core_universe(
            session=session,
            principal=principal,
            request=request or AccountETFUniverseRefreshRequest(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/candidates/scanners/us-etf/rotation",
    response_model=ETFOneilScannerResponse,
)
def run_account_us_etf_rotation_scanner(
    session: DbSession,
    principal: TraderPrincipal,
    request: AccountETFRotationScannerRequest | None = None,
) -> ETFOneilScannerResponse:
    try:
        return BusinessService.run_account_etf_rotation_scanner(
            session=session,
            principal=principal,
            request=request or AccountETFRotationScannerRequest(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/candidates/scanners/us-etf/rotation/refresh",
    response_model=ETFUniverseSeedResponse,
)
def refresh_account_us_etf_rotation_scanner(
    session: DbSession,
    principal: TraderPrincipal,
    request: AccountETFUniverseRefreshRequest | None = None,
) -> ETFUniverseSeedResponse:
    try:
        return BusinessService.refresh_account_etf_rotation_universe(
            session=session,
            principal=principal,
            request=request or AccountETFUniverseRefreshRequest(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/candidates/outcomes", response_model=list[ScannerOutcome])
def list_scanner_outcomes(
    session: DbSession,
    principal: VerifiedPrincipal,
    evaluation_status: str | None = None,
    symbol: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ScannerOutcome]:
    return BusinessService.list_scanner_outcomes(
        session=session,
        principal=principal,
        evaluation_status=evaluation_status,
        symbol=symbol,
        limit=limit,
        offset=offset,
    )


@router.get("/candidates/outcomes/count", response_model=CountResponse)
def count_scanner_outcomes(
    session: DbSession,
    principal: VerifiedPrincipal,
    evaluation_status: str | None = None,
    symbol: str | None = None,
) -> CountResponse:
    return CountResponse(
        total=BusinessService.count_scanner_outcomes(
            session=session,
            principal=principal,
            evaluation_status=evaluation_status,
            symbol=symbol,
        )
    )


@router.get("/candidates/outcomes/summary", response_model=ScannerOutcomeSummary)
def get_scanner_outcome_summary(
    session: DbSession,
    principal: VerifiedPrincipal,
    evaluation_status: str | None = None,
    symbol: str | None = None,
) -> ScannerOutcomeSummary:
    return BusinessService.scanner_outcome_summary(
        session=session,
        principal=principal,
        evaluation_status=evaluation_status,
        symbol=symbol,
    )


@router.post("/candidates/outcomes/recalculate", response_model=ScannerOutcomeRecalculateResponse)
def recalculate_scanner_outcomes(
    session: DbSession,
    principal: TraderPrincipal,
    request: ScannerOutcomeRecalculateRequest | None = None,
) -> ScannerOutcomeRecalculateResponse:
    try:
        return BusinessService.recalculate_scanner_outcomes(
            session=session,
            principal=principal,
            request=request or ScannerOutcomeRecalculateRequest(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/candidates/{candidate_id}/outcome", response_model=ScannerOutcome)
def get_candidate_outcome(
    candidate_id: str,
    session: DbSession,
    principal: VerifiedPrincipal,
) -> ScannerOutcome:
    try:
        return BusinessService.get_candidate_outcome(
            session=session,
            principal=principal,
            candidate_id=candidate_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/candidates/{candidate_id}", response_model=CandidateDetail)
def get_candidate_detail(
    candidate_id: str,
    session: DbSession,
    principal: VerifiedPrincipal,
) -> CandidateDetail:
    try:
        return BusinessService.get_candidate_detail(
            session=session,
            principal=principal,
            candidate_id=candidate_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/candidates/{candidate_id}", response_model=Candidate)
def update_candidate(
    candidate_id: str,
    request: CandidateUpdate,
    session: DbSession,
    principal: TraderPrincipal,
) -> Candidate:
    try:
        return BusinessService.update_candidate(
            session=session,
            principal=principal,
            candidate_id=candidate_id,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/positions", response_model=Position, status_code=status.HTTP_201_CREATED)
def create_position(
    request: PositionCreate,
    session: DbSession,
    principal: TraderPrincipal,
) -> Position:
    return BusinessService.create_position(session=session, principal=principal, request=request)


@router.post(
    "/candidates/{candidate_id}/plan",
    response_model=Position,
    status_code=status.HTTP_201_CREATED,
)
def create_candidate_plan(
    candidate_id: str,
    request: CandidatePlanCreate,
    session: DbSession,
    principal: TraderPrincipal,
) -> Position:
    try:
        return BusinessService.create_candidate_plan(
            session=session,
            principal=principal,
            candidate_id=candidate_id,
            request=request,
        )
    except ValueError as exc:
        status_code = 404 if str(exc).startswith("Candidate not found") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/candidates/{candidate_id}/plan", response_model=Position | None)
def get_candidate_plan(
    candidate_id: str,
    session: DbSession,
    principal: VerifiedPrincipal,
) -> Position | None:
    try:
        return BusinessService.get_candidate_plan(
            session=session,
            principal=principal,
            candidate_id=candidate_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/candidates/{candidate_id}/plan-preview", response_model=CandidatePlanPreview)
def preview_candidate_plan(
    candidate_id: str,
    session: DbSession,
    principal: VerifiedPrincipal,
) -> CandidatePlanPreview:
    try:
        return BusinessService.preview_candidate_plan(
            session=session,
            principal=principal,
            candidate_id=candidate_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/positions", response_model=list[Position])
def list_positions(
    session: DbSession,
    principal: VerifiedPrincipal,
    status_filter: PositionStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[Position]:
    return BusinessService.list_positions(
        session=session,
        principal=principal,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/positions/count", response_model=CountResponse)
def count_positions(
    session: DbSession,
    principal: VerifiedPrincipal,
    status_filter: PositionStatus | None = Query(default=None, alias="status"),
) -> CountResponse:
    return CountResponse(
        total=BusinessService.count_positions(
            session=session,
            principal=principal,
            status=status_filter,
        )
    )


@router.patch("/positions/{position_id}", response_model=Position)
def update_position(
    position_id: str,
    request: PositionUpdate,
    session: DbSession,
    principal: TraderPrincipal,
) -> Position:
    try:
        return BusinessService.update_position(
            session=session,
            principal=principal,
            position_id=position_id,
            request=request,
        )
    except ValueError as exc:
        status_code = 404 if str(exc).startswith("Position not found") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/positions/{position_id}/activate", response_model=Position)
def activate_position(
    position_id: str,
    request: PositionActivate,
    session: DbSession,
    principal: TraderPrincipal,
) -> Position:
    try:
        return BusinessService.activate_position(
            session=session,
            principal=principal,
            position_id=position_id,
            request=request,
        )
    except ValueError as exc:
        status_code = 404 if str(exc).startswith("Position not found") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/positions/{position_id}/stop", response_model=Position)
def update_position_stop(
    position_id: str,
    request: PositionStopUpdate,
    session: DbSession,
    principal: TraderPrincipal,
) -> Position:
    try:
        return BusinessService.update_position_stop(
            session=session,
            principal=principal,
            position_id=position_id,
            request=request,
        )
    except ValueError as exc:
        status_code = 404 if str(exc).startswith("Position not found") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/positions/{position_id}/cancel", response_model=Position)
def cancel_position(
    position_id: str,
    session: DbSession,
    principal: TraderPrincipal,
) -> Position:
    try:
        return BusinessService.cancel_position(
            session=session,
            principal=principal,
            position_id=position_id,
        )
    except ValueError as exc:
        status_code = 404 if str(exc).startswith("Position not found") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/positions/{position_id}/reduce", response_model=Position)
def reduce_position(
    position_id: str,
    request: PositionReduce,
    session: DbSession,
    principal: TraderPrincipal,
) -> Position:
    try:
        return BusinessService.reduce_position(
            session=session,
            principal=principal,
            position_id=position_id,
            request=request,
        )
    except ValueError as exc:
        status_code = 404 if str(exc).startswith("Position not found") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/positions/{position_id}/close", response_model=PositionCloseResponse)
def close_position(
    position_id: str,
    request: PositionClose,
    session: DbSession,
    principal: TraderPrincipal,
) -> PositionCloseResponse:
    try:
        return BusinessService.close_position(
            session=session,
            principal=principal,
            position_id=position_id,
            request=request,
        )
    except ValueError as exc:
        status_code = 404 if str(exc).startswith("Position not found") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/exit-alerts", response_model=ExitAlert, status_code=status.HTTP_201_CREATED)
def create_exit_alert(
    request: ExitAlertCreate,
    session: DbSession,
    principal: TraderPrincipal,
) -> ExitAlert:
    try:
        return BusinessService.create_exit_alert(session=session, principal=principal, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/exit-alerts/evaluate", response_model=ExitAlertEvaluationResponse)
def evaluate_exit_alerts(
    request: ExitAlertEvaluationRequest,
    session: DbSession,
    principal: TraderPrincipal,
) -> ExitAlertEvaluationResponse:
    try:
        return BusinessService.evaluate_exit_alerts(
            session=session,
            principal=principal,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/exit-alerts", response_model=list[ExitAlert])
def list_exit_alerts(
    session: DbSession,
    principal: VerifiedPrincipal,
    acknowledged: bool | None = None,
    include_snoozed: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ExitAlert]:
    return BusinessService.list_exit_alerts(
        session=session,
        principal=principal,
        acknowledged=acknowledged,
        include_snoozed=include_snoozed,
        limit=limit,
        offset=offset,
    )


@router.get("/exit-alerts/count", response_model=CountResponse)
def count_exit_alerts(
    session: DbSession,
    principal: VerifiedPrincipal,
    acknowledged: bool | None = None,
    include_snoozed: bool = False,
) -> CountResponse:
    return CountResponse(
        total=BusinessService.count_exit_alerts(
            session=session,
            principal=principal,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
        )
    )


@router.patch("/exit-alerts/{alert_id}", response_model=ExitAlert)
def update_exit_alert(
    alert_id: str,
    request: ExitAlertUpdate,
    session: DbSession,
    principal: TraderPrincipal,
) -> ExitAlert:
    try:
        return BusinessService.update_exit_alert(
            session=session,
            principal=principal,
            alert_id=alert_id,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/notifications", response_model=list[NotificationEvent])
def list_notifications(
    session: DbSession,
    principal: VerifiedPrincipal,
    read: bool | None = None,
    acknowledged: bool | None = None,
    include_snoozed: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[NotificationEvent]:
    return BusinessService.list_notifications(
        session=session,
        principal=principal,
        read=read,
        acknowledged=acknowledged,
        include_snoozed=include_snoozed,
        limit=limit,
        offset=offset,
    )


@router.get("/notifications/count", response_model=CountResponse)
def count_notifications(
    session: DbSession,
    principal: VerifiedPrincipal,
    read: bool | None = None,
    acknowledged: bool | None = None,
    include_snoozed: bool = False,
) -> CountResponse:
    return CountResponse(
        total=BusinessService.count_notifications(
            session=session,
            principal=principal,
            read=read,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
        )
    )


@router.patch("/notifications/{notification_id}", response_model=NotificationEvent)
def update_notification(
    notification_id: str,
    request: NotificationEventUpdate,
    session: DbSession,
    principal: TraderPrincipal,
) -> NotificationEvent:
    try:
        return BusinessService.update_notification(
            session=session,
            principal=principal,
            notification_id=notification_id,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/journal/trades", response_model=JournalTrade, status_code=status.HTTP_201_CREATED)
def create_journal_trade(
    request: JournalTradeCreate,
    session: DbSession,
    principal: TraderPrincipal,
) -> JournalTrade:
    try:
        return BusinessService.create_journal_trade(session=session, principal=principal, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/journal/trades", response_model=list[JournalTrade])
def list_journal_trades(
    session: DbSession,
    principal: VerifiedPrincipal,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[JournalTrade]:
    return BusinessService.list_journal_trades(
        session=session,
        principal=principal,
        limit=limit,
        offset=offset,
    )


@router.get("/journal/trades/count", response_model=CountResponse)
def count_journal_trades(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> CountResponse:
    return CountResponse(
        total=BusinessService.count_journal_trades(
            session=session,
            principal=principal,
        )
    )
