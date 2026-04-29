from datetime import UTC, date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.schemas.business import Candidate


class BarsIngestionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ticker: str = Field(..., min_length=1)
    from_date: date = Field(..., alias="from")
    to_date: date = Field(..., alias="to")
    timeframe: Literal["1d"] = "1d"

    @model_validator(mode="after")
    def validate_date_range(self) -> "BarsIngestionRequest":
        if self.to_date < self.from_date:
            raise ValueError("to must be greater than or equal to from")
        return self


class OptionChainIngestionRequest(BaseModel):
    underlying_symbol: str = Field(..., min_length=1)


class MarketContextIngestionRequest(BaseModel):
    snapshot_ts: datetime | None = None
    market: str = "global"
    spy_return: float | None = None
    qqq_return: float | None = None
    iwm_return: float | None = None
    smh_return: float | None = None
    soxx_return: float | None = None
    vix_change: float | None = None
    usdjpy_change: float | None = None
    dxy_change: float | None = None
    us10y_change: float | None = None
    nikkei_futures_change: float | None = None
    topix_return: float | None = None
    japan_bias: str | None = None
    us_bias: str | None = None
    risk_level: Literal["normal", "watch", "shock"] | None = None
    notes: str | None = None


class IngestionResponse(BaseModel):
    records_written: int
    last_updated_at: datetime
    source: str = "polygon"


class ETFUniverseSeedRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symbols: list[str] | None = None
    from_date: date | None = Field(default=None, alias="from")
    to_date: date | None = Field(default=None, alias="to")
    timeframe: Literal["1d"] = "1d"
    lookback_days: int = Field(default=550, ge=30, le=3000)
    account_id: str = Field(default="acct_local", min_length=1)
    run_pa_facts: bool = True
    run_scanner: bool = True
    min_score: float = Field(default=60.0, ge=0, le=100)
    max_candidates: int = Field(default=25, ge=1, le=200)

    @model_validator(mode="after")
    def normalize_seed_request(self) -> "ETFUniverseSeedRequest":
        if self.symbols is not None:
            self.symbols = [symbol.strip().upper() for symbol in self.symbols if symbol.strip()]
        if self.to_date is None:
            self.to_date = datetime.now(UTC).date()
        if self.from_date is None:
            self.from_date = self.to_date - timedelta(days=self.lookback_days)
        if self.to_date < self.from_date:
            raise ValueError("to must be greater than or equal to from")
        return self


class ETFUniverseSeedSymbolResult(BaseModel):
    symbol: str
    status: Literal["success", "failed"]
    bars_written: int = 0
    error_message: str | None = None


class ETFUniverseSeedResponse(BaseModel):
    account_id: str
    timeframe: str
    from_date: date
    to_date: date
    symbols_requested: list[str]
    bars_written: int
    facts_written: int = 0
    setups_written: int = 0
    candidates_written: int = 0
    skipped_symbols: list[str] = Field(default_factory=list)
    symbol_results: list[ETFUniverseSeedSymbolResult] = Field(default_factory=list)
    candidates: list[Candidate] = Field(default_factory=list)


class BarRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ts: datetime
    symbol_id: str
    timeframe: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None
    vwap: float | None
    adjusted: bool
    source: str | None


class BarsQueryResponse(BaseModel):
    ticker: str
    timeframe: str
    bars: list[BarRecord]


class OptionChainSnapshotRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshot_ts: datetime
    underlying_symbol: str
    option_symbol: str
    expiration: date
    strike: float
    option_type: str
    bid: float | None
    ask: float | None
    mid: float | None
    last: float | None
    volume: float | None
    open_interest: float | None
    iv: float | None
    delta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    dte: int | None
    spread_pct: float | None
    source: str | None


class OptionChainSnapshotResponse(BaseModel):
    underlying_symbol: str
    snapshot_ts: datetime | None
    options: list[OptionChainSnapshotRecord]


class DataFreshnessRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_key: str
    last_updated_at: datetime
    source: str | None
    updated_at: datetime | None


class DataFreshnessResponse(BaseModel):
    data: list[DataFreshnessRecord]
