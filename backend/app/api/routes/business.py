from fastapi import APIRouter, HTTPException, Query, status

from backend.app.api.dependencies import CurrentPrincipal, DbSession, TraderPrincipal
from backend.app.schemas.business import (
    Candidate,
    CandidateCreate,
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
from backend.app.services.business_service import BusinessService

router = APIRouter(prefix="/api", tags=["business"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(session: DbSession, principal: CurrentPrincipal) -> DashboardSummary:
    return BusinessService.dashboard_summary(session=session, principal=principal)


@router.post("/candidates", response_model=Candidate, status_code=status.HTTP_201_CREATED)
def create_candidate(
    request: CandidateCreate,
    session: DbSession,
    principal: TraderPrincipal,
) -> Candidate:
    return BusinessService.create_candidate(session=session, principal=principal, request=request)


@router.get("/candidates", response_model=list[Candidate])
def list_candidates(
    session: DbSession,
    principal: CurrentPrincipal,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Candidate]:
    return BusinessService.list_candidates(session=session, principal=principal, limit=limit)


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
    principal: CurrentPrincipal,
    status_filter: PositionStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Position]:
    return BusinessService.list_positions(
        session=session,
        principal=principal,
        status=status_filter,
        limit=limit,
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
    principal: CurrentPrincipal,
    acknowledged: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ExitAlert]:
    return BusinessService.list_exit_alerts(
        session=session,
        principal=principal,
        acknowledged=acknowledged,
        limit=limit,
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
    principal: CurrentPrincipal,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[JournalTrade]:
    return BusinessService.list_journal_trades(session=session, principal=principal, limit=limit)
