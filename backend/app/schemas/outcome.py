from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScannerOutcome(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    outcome_id: str
    account_id: str
    candidate_id: str
    pa_setup_id: str | None = None
    symbol_id: str
    timeframe: str
    detected_ts: datetime
    setup_type: str | None = None
    setup_grade: str | None = None
    score_total: float | None = None
    reference_close: float | None = None
    entry_trigger: float | None = None
    initial_stop: float | None = None
    bars_available: int
    evaluation_status: str
    latest_evaluated_ts: datetime | None = None
    triggered_entry: bool | None = None
    trigger_ts: datetime | None = None
    stopped_out: bool | None = None
    stop_ts: datetime | None = None
    stop_hit_before_trigger: bool | None = None
    false_breakout: bool | None = None
    forward_return_5d: float | None = None
    forward_return_10d: float | None = None
    forward_return_20d: float | None = None
    forward_return_60d: float | None = None
    mfe_5d: float | None = None
    mfe_10d: float | None = None
    mfe_20d: float | None = None
    mfe_60d: float | None = None
    mae_5d: float | None = None
    mae_10d: float | None = None
    mae_20d: float | None = None
    mae_60d: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ScannerOutcomeSummary(BaseModel):
    total: int
    pending_count: int
    matured_count: int
    triggered_count: int
    stopped_count: int
    false_breakout_count: int
    positive_20d_count: int
    positive_60d_count: int
    trigger_rate: float | None = None
    stop_rate: float | None = None
    false_breakout_rate: float | None = None
    positive_20d_rate: float | None = None
    positive_60d_rate: float | None = None
    avg_forward_return_20d: float | None = None
    avg_forward_return_60d: float | None = None
    avg_mfe_20d: float | None = None
    avg_mfe_60d: float | None = None
    avg_mae_20d: float | None = None
    avg_mae_60d: float | None = None


class ScannerOutcomeRecalculateRequest(BaseModel):
    candidate_id: str | None = None
    symbol: str | None = None
    strategy_name: str | None = "oneil_core_us_etf"
    limit: int | None = Field(default=None, ge=1, le=5000)


class ScannerOutcomeRecalculateResponse(BaseModel):
    account_id: str
    candidates_scanned: int
    outcomes_written: int
    skipped_candidates: int = 0
    status_counts: dict[str, int] = Field(default_factory=dict)
    symbols_processed: list[str] = Field(default_factory=list)
