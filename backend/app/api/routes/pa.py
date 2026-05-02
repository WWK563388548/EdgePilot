from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.api.dependencies import DbSession, require_ingestion_admin
from backend.app.schemas.pa import (
    ETFOneilScannerRequest,
    ETFOneilScannerResponse,
    ETFUniverseFactsRequest,
    PACalibrationStat,
    PAFact,
    PAFactsCalculationResponse,
    PAStructure,
    PASetup,
)
from backend.app.services.pa_service import PAService
from backend.app.services.scanner_service import ETFScannerService

router = APIRouter(prefix="/api/pa", tags=["pa"])
IngestionAdmin = Annotated[None, Depends(require_ingestion_admin)]


@router.get("/facts/{symbol}", response_model=list[PAFact])
def list_pa_facts(
    symbol: str,
    session: DbSession,
    timeframe: str = "1d",
    limit: int = Query(default=200, ge=1, le=2000),
) -> list[PAFact]:
    return PAService.list_facts(
        session=session,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )


@router.get("/structures/{symbol}", response_model=list[PAStructure])
def list_pa_structures(
    symbol: str,
    session: DbSession,
    timeframe: str = "1d",
    structure_type: str | None = None,
    limit: int = Query(default=200, ge=1, le=2000),
) -> list[PAStructure]:
    return PAService.list_structures(
        session=session,
        symbol=symbol,
        timeframe=timeframe,
        structure_type=structure_type,
        limit=limit,
    )


@router.get("/setups", response_model=list[PASetup])
def list_pa_setups(
    session: DbSession,
    symbol: str | None = None,
    timeframe: str | None = "1d",
    setup_type: str | None = None,
    status: str | None = None,
    validation_status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[PASetup]:
    return PAService.list_setups(
        session=session,
        symbol=symbol,
        timeframe=timeframe,
        setup_type=setup_type,
        status=status,
        validation_status=validation_status,
        limit=limit,
    )


@router.get("/setups/{setup_id}", response_model=PASetup)
def get_pa_setup(setup_id: str, session: DbSession) -> PASetup:
    setup = PAService.get_setup(session=session, setup_id=setup_id)
    if setup is None:
        raise HTTPException(status_code=404, detail=f"PA setup not found: {setup_id}")
    return setup


@router.get("/calibration", response_model=list[PACalibrationStat])
def list_pa_calibration(
    session: DbSession,
    setup_type: str | None = None,
    market_regime: str | None = None,
    timeframe: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[PACalibrationStat]:
    return PAService.list_calibration_stats(
        session=session,
        setup_type=setup_type,
        market_regime=market_regime,
        timeframe=timeframe,
        limit=limit,
    )


@router.post("/facts/etf-universe", response_model=PAFactsCalculationResponse)
def calculate_etf_daily_facts(
    request: ETFUniverseFactsRequest | None = None,
    _admin: IngestionAdmin = None,
) -> PAFactsCalculationResponse:
    return PAService.calculate_etf_daily_facts(request or ETFUniverseFactsRequest())


@router.post("/scanners/us-etf/oneil-core", response_model=ETFOneilScannerResponse)
def run_us_etf_oneil_core_scanner(
    request: ETFOneilScannerRequest | None = None,
    _admin: IngestionAdmin = None,
) -> ETFOneilScannerResponse:
    try:
        return ETFScannerService.run_us_etf_oneil_core(request or ETFOneilScannerRequest())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
