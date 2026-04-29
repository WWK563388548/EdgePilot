from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.schemas.business import Candidate

Timeframe = Literal["1d"]


class PAFact(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fact_id: str
    symbol_id: str
    timeframe: str
    ts: datetime
    facts: dict[str, Any]
    created_at: datetime | None = None


class PAStructure(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    structure_id: str
    symbol_id: str
    timeframe: str
    ts: datetime
    structure_type: str
    confidence: float | None = None
    metrics: dict[str, Any] | None = None
    created_at: datetime | None = None


class PASetup(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    setup_id: str
    symbol_id: str
    timeframe: str
    detected_ts: datetime
    setup_type: str
    setup_grade: str | None = None
    pa_quality_score: float | None = None
    structure_score: float | None = None
    location_score: float | None = None
    volume_score: float | None = None
    trend_rs_score: float | None = None
    context_score: float | None = None
    risk_stop_score: float | None = None
    followthrough_score: float | None = None
    entry_plan: dict[str, Any] | None = None
    exit_plan: dict[str, Any] | None = None
    invalidation: dict[str, Any] | None = None
    status: str | None = None
    validation_status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PACalibrationStat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stat_id: str
    setup_type: str
    market_regime: str | None = None
    sector_context: str | None = None
    timeframe: str | None = None
    sample_size: int | None = None
    win_rate: float | None = None
    average_r: float | None = None
    median_r: float | None = None
    profit_factor: float | None = None
    false_breakout_rate: float | None = None
    avg_mfe_r: float | None = None
    avg_mae_r: float | None = None
    max_drawdown_pct: float | None = None
    confidence_level: str | None = None
    updated_at: datetime | None = None


class ETFUniverseFactsRequest(BaseModel):
    symbols: list[str] | None = None
    timeframe: Timeframe = "1d"

    @model_validator(mode="after")
    def normalize_symbols(self) -> "ETFUniverseFactsRequest":
        if self.symbols is not None:
            self.symbols = [symbol.strip().upper() for symbol in self.symbols if symbol.strip()]
        return self


class PAFactsCalculationResponse(BaseModel):
    timeframe: str
    symbols_processed: list[str]
    facts_written: int
    skipped_symbols: list[str] = Field(default_factory=list)


class ETFOneilScannerRequest(ETFUniverseFactsRequest):
    account_id: str = Field(default="acct_local", min_length=1)
    min_score: float = Field(default=60.0, ge=0, le=100)
    max_candidates: int = Field(default=25, ge=1, le=200)
    recalculate_facts: bool = True


class ETFOneilScannerResponse(BaseModel):
    account_id: str
    timeframe: str
    symbols_scanned: list[str]
    facts_written: int
    setups_written: int
    candidates_written: int
    skipped_symbols: list[str] = Field(default_factory=list)
    candidates: list[Candidate] = Field(default_factory=list)
