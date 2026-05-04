from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.scanner import ScannerDecision

CandidateDecision = Literal["candidate", "watch", "avoid"]
PositionStatus = Literal["planned", "open", "reduce", "exit_pending", "closed"]
GuardrailLevel = Literal["block", "warning", "info"]


class AccountRiskSettingsBase(BaseModel):
    account_equity: float = Field(default=10_000, gt=0)
    max_risk_per_trade_pct: float = Field(default=0.005, gt=0, le=0.1)
    max_open_positions: int = Field(default=3, ge=1, le=50)
    max_risk_distance_pct: float = Field(default=0.12, gt=0, le=0.5)
    shadow_only_requires_paper: bool = True


class AccountRiskSettingsUpdate(BaseModel):
    account_equity: float | None = Field(default=None, gt=0)
    max_risk_per_trade_pct: float | None = Field(default=None, gt=0, le=0.1)
    max_open_positions: int | None = Field(default=None, ge=1, le=50)
    max_risk_distance_pct: float | None = Field(default=None, gt=0, le=0.5)
    shadow_only_requires_paper: bool | None = None


class AccountRiskSettings(AccountRiskSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GuardrailNotice(BaseModel):
    level: GuardrailLevel
    code: str


class CandidateBase(BaseModel):
    symbol_id: str = Field(..., min_length=1)
    scan_date: date
    strategy_name: str = Field(..., min_length=1)
    setup_type: str | None = None
    pa_setup_id: str | None = None
    score_total: float | None = None
    entry_trigger: float | None = None
    initial_stop: float | None = None
    decision: CandidateDecision | None = None
    option_suitability: str | None = None
    ai_review_json: str | None = None


class CandidateCreate(CandidateBase):
    candidate_id: str | None = None


class CandidateUpdate(BaseModel):
    setup_type: str | None = None
    pa_setup_id: str | None = None
    score_total: float | None = None
    entry_trigger: float | None = None
    initial_stop: float | None = None
    decision: CandidateDecision | None = None
    option_suitability: str | None = None
    ai_review_json: str | None = None


class Candidate(CandidateBase):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    created_at: datetime | None = None
    pa_setup_grade: str | None = None
    validation_status: str | None = None


class CandidatePASetup(BaseModel):
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


class CandidateDetail(BaseModel):
    candidate: Candidate
    pa_setup: CandidatePASetup | None = None
    score_breakdown: dict[str, Any] | None = None
    scanner_decision: ScannerDecision | None = None
    entry_plan: dict[str, Any] | None = None
    exit_plan: dict[str, Any] | None = None
    invalidation: dict[str, Any] | None = None


class CandidatePlanPreview(BaseModel):
    account_id: str
    candidate_id: str
    entry_price: float | None = None
    initial_stop: float | None = None
    risk_per_unit: float | None = None
    risk_distance_pct: float | None = None
    account_equity: float
    max_risk_per_trade_pct: float
    max_risk_amount: float
    suggested_quantity: int | None = None
    planned_quantity: float | None = None
    planned_risk_amount: float | None = None
    planned_risk_pct: float | None = None
    max_open_positions: int
    active_position_count: int
    validation_status: str | None = None
    guardrails: list[GuardrailNotice] = Field(default_factory=list)


class PositionBase(BaseModel):
    symbol_id: str = Field(..., min_length=1)
    asset_type: str = Field(..., min_length=1)
    strategy_name: str | None = None
    entry_date: datetime | None = None
    entry_price: float | None = None
    quantity: float | None = None
    initial_stop: float | None = None
    current_stop: float | None = None
    status: PositionStatus | None = "open"
    current_r: float | None = None
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None


class PositionCreate(PositionBase):
    position_id: str | None = None


class CandidatePlanCreate(BaseModel):
    asset_type: str = Field(default="etf", min_length=1)
    entry_price: float | None = Field(default=None, gt=0)
    initial_stop: float | None = Field(default=None, gt=0)
    quantity: float | None = Field(default=None, gt=0)


class PositionUpdate(BaseModel):
    strategy_name: str | None = None
    current_stop: float | None = None
    status: PositionStatus | None = None
    current_r: float | None = None
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None


class PositionActivate(BaseModel):
    entry_price: float = Field(..., gt=0)
    quantity: float | None = Field(default=None, gt=0)
    entry_date: datetime | None = None


class PositionStopUpdate(BaseModel):
    new_stop: float = Field(..., gt=0)


class PositionReduce(BaseModel):
    exit_price: float = Field(..., gt=0)
    quantity: float | None = Field(default=None, gt=0)
    current_stop: float | None = Field(default=None, gt=0)
    exit_date: datetime | None = None
    notes: str | None = None


class PositionClose(BaseModel):
    exit_price: float = Field(..., gt=0)
    quantity: float | None = Field(default=None, gt=0)
    exit_date: datetime | None = None
    exit_reason: str | None = None
    notes: str | None = None


class Position(PositionBase):
    model_config = ConfigDict(from_attributes=True)

    position_id: str
    risk_per_unit: float | None = None
    risk_amount: float | None = None
    risk_pct: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExitAlertBase(BaseModel):
    position_id: str = Field(..., min_length=1)
    level: int | None = None
    action: str | None = None
    reason: str | None = None
    new_stop: float | None = None
    triggered_rules: str | None = None
    acknowledged: bool = False


class ExitAlertCreate(ExitAlertBase):
    alert_id: str | None = None


class ExitAlertUpdate(BaseModel):
    level: int | None = None
    action: str | None = None
    reason: str | None = None
    new_stop: float | None = None
    triggered_rules: str | None = None
    acknowledged: bool | None = None


class ExitAlert(ExitAlertBase):
    model_config = ConfigDict(from_attributes=True)

    alert_id: str
    alert_ts: datetime | None = None


class ExitAlertEvaluationRequest(BaseModel):
    position_id: str | None = None
    limit: int | None = Field(default=None, ge=1, le=500)


class ExitAlertEvaluationResponse(BaseModel):
    account_id: str
    positions_evaluated: int
    alerts_created: int
    skipped_positions: int = 0
    duplicate_alerts: int = 0
    symbols_processed: list[str] = Field(default_factory=list)
    alerts: list[ExitAlert] = Field(default_factory=list)


class JournalTradeBase(BaseModel):
    position_id: str | None = None
    symbol_id: str | None = None
    entry_ts: datetime | None = None
    exit_ts: datetime | None = None
    entry_price: float | None = None
    exit_price: float | None = None
    quantity: float | None = None
    gross_pnl: float | None = None
    net_pnl: float | None = None
    r_multiple: float | None = None
    setup_type: str | None = None
    exit_reason: str | None = None
    mistake_tags: str | None = None
    notes: str | None = None


class JournalTradeCreate(JournalTradeBase):
    trade_id: str | None = None


class JournalTrade(JournalTradeBase):
    model_config = ConfigDict(from_attributes=True)

    trade_id: str


class PositionCloseResponse(BaseModel):
    position: Position
    journal_trade: JournalTrade


class DataFreshnessSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_key: str
    last_updated_at: datetime
    source: str | None = None


class MarketContextSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshot_ts: datetime | None = None
    risk_level: str | None = None
    us_bias: str | None = None
    japan_bias: str | None = None
    notes: str | None = None


class DashboardSummary(BaseModel):
    market_context: MarketContextSummary
    risk_mode: str
    candidate_count: int
    open_position_count: int
    exit_alert_count: int
    highest_exit_level: int | None
    data_freshness: list[DataFreshnessSummary]
