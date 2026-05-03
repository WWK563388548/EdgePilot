from fastapi import APIRouter, HTTPException, Query, status

from backend.app.api.dependencies import DbSession, TraderPrincipal, VerifiedPrincipal
from backend.app.schemas.business import (
    Candidate,
    CandidateCreate,
    CandidateDetail,
    CandidateUpdate,
    DashboardSummary,
    ExitAlert,
    ExitAlertCreate,
    ExitAlertUpdate,
    JournalTrade,
    JournalTradeCreate,
    Position,
    PositionCreate,
    PositionStatus,
    PositionUpdate,
)
from backend.app.schemas.ingestion import AccountETFUniverseRefreshRequest, ETFUniverseSeedResponse
from backend.app.schemas.pa import AccountETFOneilScannerRequest, ETFOneilScannerResponse
from backend.app.services.business_service import BusinessService

router = APIRouter(prefix="/api", tags=["business"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(session: DbSession, principal: VerifiedPrincipal) -> DashboardSummary:
    return BusinessService.dashboard_summary(session=session, principal=principal)


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
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[Candidate]:
    return BusinessService.list_candidates(
        session=session,
        principal=principal,
        decision=decision,
        limit=limit,
        offset=offset,
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
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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


@router.get("/exit-alerts", response_model=list[ExitAlert])
def list_exit_alerts(
    session: DbSession,
    principal: VerifiedPrincipal,
    acknowledged: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ExitAlert]:
    return BusinessService.list_exit_alerts(
        session=session,
        principal=principal,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset,
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
