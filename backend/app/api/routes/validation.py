from fastapi import APIRouter, HTTPException, Query, status

from backend.app.api.dependencies import DbSession, TraderPrincipal, VerifiedPrincipal
from backend.app.schemas.common import CountResponse
from backend.app.schemas.validation import (
    GoLiveGate,
    GoLiveGateEvaluateRequest,
    SignalFunnelSnapshot,
    SignalFunnelSnapshotCreate,
    SimulatedTrade,
    SimulatedTradeCreate,
    StrategyKillSwitch,
    StrategyKillSwitchUpdate,
    StrategyReadiness,
    TestRun,
    TestRunCreate,
)
from backend.app.services.validation_service import ValidationService

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.get("/strategies", response_model=list[StrategyReadiness])
def list_strategy_readiness(
    session: DbSession,
    principal: VerifiedPrincipal,
) -> list[StrategyReadiness]:
    return ValidationService.list_readiness(session=session, principal=principal)


@router.post("/strategies/{strategy_name}/evaluate", response_model=StrategyReadiness)
def evaluate_strategy_readiness(
    strategy_name: str,
    request: GoLiveGateEvaluateRequest,
    session: DbSession,
    principal: TraderPrincipal,
) -> StrategyReadiness:
    try:
        return ValidationService.evaluate_strategy(
            session=session,
            principal=principal,
            strategy_name=strategy_name,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.patch("/strategies/{strategy_name}/kill-switch", response_model=StrategyKillSwitch)
def update_strategy_kill_switch(
    strategy_name: str,
    request: StrategyKillSwitchUpdate,
    session: DbSession,
    principal: TraderPrincipal,
) -> StrategyKillSwitch:
    try:
        return ValidationService.update_kill_switch(
            session=session,
            principal=principal,
            strategy_name=strategy_name,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/gates", response_model=list[GoLiveGate])
def list_go_live_gates(
    session: DbSession,
    principal: VerifiedPrincipal,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[GoLiveGate]:
    return ValidationService.list_gates(
        session=session,
        principal=principal,
        limit=limit,
        offset=offset,
    )


@router.get("/test-runs", response_model=list[TestRun])
def list_test_runs(
    session: DbSession,
    principal: VerifiedPrincipal,
    strategy_name: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[TestRun]:
    return ValidationService.list_test_runs(
        session=session,
        principal=principal,
        strategy_name=strategy_name,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/test-runs/count", response_model=CountResponse)
def count_test_runs(
    session: DbSession,
    principal: VerifiedPrincipal,
    strategy_name: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
) -> CountResponse:
    return CountResponse(
        total=ValidationService.count_test_runs(
            session=session,
            principal=principal,
            strategy_name=strategy_name,
            status=status_filter,
        )
    )


@router.post("/test-runs", response_model=TestRun, status_code=status.HTTP_201_CREATED)
def create_test_run(
    request: TestRunCreate,
    session: DbSession,
    principal: TraderPrincipal,
) -> TestRun:
    try:
        return ValidationService.create_test_run(
            session=session,
            principal=principal,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/simulated-trades", response_model=list[SimulatedTrade])
def list_simulated_trades(
    session: DbSession,
    principal: VerifiedPrincipal,
    strategy_name: str | None = None,
    test_run_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[SimulatedTrade]:
    return ValidationService.list_simulated_trades(
        session=session,
        principal=principal,
        strategy_name=strategy_name,
        test_run_id=test_run_id,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/simulated-trades",
    response_model=SimulatedTrade,
    status_code=status.HTTP_201_CREATED,
)
def create_simulated_trade(
    request: SimulatedTradeCreate,
    session: DbSession,
    principal: TraderPrincipal,
) -> SimulatedTrade:
    try:
        return ValidationService.create_simulated_trade(
            session=session,
            principal=principal,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/funnel-snapshots", response_model=list[SignalFunnelSnapshot])
def list_funnel_snapshots(
    session: DbSession,
    principal: VerifiedPrincipal,
    strategy_name: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[SignalFunnelSnapshot]:
    return ValidationService.list_funnel_snapshots(
        session=session,
        principal=principal,
        strategy_name=strategy_name,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/funnel-snapshots",
    response_model=SignalFunnelSnapshot,
    status_code=status.HTTP_201_CREATED,
)
def create_funnel_snapshot(
    request: SignalFunnelSnapshotCreate,
    session: DbSession,
    principal: TraderPrincipal,
) -> SignalFunnelSnapshot:
    try:
        return ValidationService.create_funnel_snapshot(
            session=session,
            principal=principal,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
