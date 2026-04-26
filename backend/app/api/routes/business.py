from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.dependencies import require_ingestion_admin
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
AdminToken = Annotated[None, Depends(require_ingestion_admin)]


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary() -> DashboardSummary:
    return BusinessService.dashboard_summary()


@router.post("/candidates", response_model=Candidate, status_code=status.HTTP_201_CREATED)
def create_candidate(request: CandidateCreate, _admin: AdminToken = None) -> Candidate:
    return BusinessService.create_candidate(request)


@router.get("/candidates", response_model=list[Candidate])
def list_candidates(limit: int = Query(default=100, ge=1, le=500)) -> list[Candidate]:
    return BusinessService.list_candidates(limit=limit)


@router.patch("/candidates/{candidate_id}", response_model=Candidate)
def update_candidate(
    candidate_id: str,
    request: CandidateUpdate,
    _admin: AdminToken = None,
) -> Candidate:
    try:
        return BusinessService.update_candidate(candidate_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/positions", response_model=Position, status_code=status.HTTP_201_CREATED)
def create_position(request: PositionCreate, _admin: AdminToken = None) -> Position:
    return BusinessService.create_position(request)


@router.get("/positions", response_model=list[Position])
def list_positions(
    status_filter: PositionStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Position]:
    return BusinessService.list_positions(status=status_filter, limit=limit)


@router.patch("/positions/{position_id}", response_model=Position)
def update_position(
    position_id: str,
    request: PositionUpdate,
    _admin: AdminToken = None,
) -> Position:
    try:
        return BusinessService.update_position(position_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/exit-alerts", response_model=ExitAlert, status_code=status.HTTP_201_CREATED)
def create_exit_alert(request: ExitAlertCreate, _admin: AdminToken = None) -> ExitAlert:
    return BusinessService.create_exit_alert(request)


@router.get("/exit-alerts", response_model=list[ExitAlert])
def list_exit_alerts(
    acknowledged: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ExitAlert]:
    return BusinessService.list_exit_alerts(acknowledged=acknowledged, limit=limit)


@router.patch("/exit-alerts/{alert_id}", response_model=ExitAlert)
def update_exit_alert(
    alert_id: str,
    request: ExitAlertUpdate,
    _admin: AdminToken = None,
) -> ExitAlert:
    try:
        return BusinessService.update_exit_alert(alert_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/journal/trades", response_model=JournalTrade, status_code=status.HTTP_201_CREATED)
def create_journal_trade(request: JournalTradeCreate, _admin: AdminToken = None) -> JournalTrade:
    return BusinessService.create_journal_trade(request)


@router.get("/journal/trades", response_model=list[JournalTrade])
def list_journal_trades(limit: int = Query(default=100, ge=1, le=500)) -> list[JournalTrade]:
    return BusinessService.list_journal_trades(limit=limit)
