from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    risk_level: str | None = None
    notes: str | None = None


class IngestionResponse(BaseModel):
    records_written: int
    last_updated_at: datetime
    source: str = "polygon"


class BarRecord(BaseModel):
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
    dataset_key: str
    last_updated_at: datetime
    source: str | None
    updated_at: datetime | None


class DataFreshnessResponse(BaseModel):
    data: list[DataFreshnessRecord]
