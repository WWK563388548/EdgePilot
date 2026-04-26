from fastapi import APIRouter, Query

from backend.app.schemas.ingestion import (
    BarsIngestionRequest,
    BarsQueryResponse,
    DataFreshnessResponse,
    IngestionResponse,
    MarketContextIngestionRequest,
    OptionChainSnapshotResponse,
    OptionChainIngestionRequest,
)
from backend.app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])


@router.post("/bars", response_model=IngestionResponse)
def ingest_bars(request: BarsIngestionRequest) -> IngestionResponse:
    return IngestionService.ingest_bars(request=request)


@router.post("/options-chain", response_model=IngestionResponse)
def ingest_options_chain(request: OptionChainIngestionRequest) -> IngestionResponse:
    return IngestionService.ingest_option_chain(request=request)


@router.post("/market-context", response_model=IngestionResponse)
def ingest_market_context(request: MarketContextIngestionRequest) -> IngestionResponse:
    return IngestionService.ingest_market_context(request=request)


@router.get("/bars/{ticker}", response_model=BarsQueryResponse)
def get_recent_bars(
    ticker: str,
    timeframe: str = "1d",
    limit: int = Query(default=200, ge=1, le=2000),
) -> BarsQueryResponse:
    return IngestionService.recent_bars(ticker=ticker, timeframe=timeframe, limit=limit)


@router.get("/options-chain/{underlying_symbol}", response_model=OptionChainSnapshotResponse)
def get_latest_options_chain(
    underlying_symbol: str,
    limit: int = Query(default=250, ge=1, le=2000),
) -> OptionChainSnapshotResponse:
    return IngestionService.latest_option_chain(underlying_symbol=underlying_symbol, limit=limit)


@router.get("/freshness", response_model=DataFreshnessResponse)
def get_data_freshness() -> DataFreshnessResponse:
    return IngestionService.data_freshness()
