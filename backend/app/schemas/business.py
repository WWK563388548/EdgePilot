from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.schemas.scanner import ScannerDecision

CandidateDecision = Literal["candidate", "watch", "avoid"]
PositionStatus = Literal[
    "planned",
    "open",
    "reduce",
    "exit_pending",
    "closed",
    "cancelled",
    "review_needed",
]
GuardrailLevel = Literal["block", "warning", "info"]
NotificationSeverity = Literal["info", "warning", "action_required"]
NotificationChannel = Literal["in_app", "email", "sms"]
AutomationJobType = Literal["market_refresh_scan"]
JobRunStatus = Literal["running", "succeeded", "failed"]
ExecutionImportStatus = Literal["completed", "partial", "failed"]
ExecutionFillSide = Literal["buy", "sell"]
ExecutionFillStatus = Literal["active", "ignored"]
ExecutionFillReconciliationStatus = Literal["matched", "review_needed", "bound", "confirmed", "ignored"]
ExecutionFillReconcileAction = Literal["bind_position", "confirm_position", "ignore_fill"]


class AccountRiskSettingsBase(BaseModel):
    account_equity: float = Field(default=10_000, gt=0)
    max_risk_per_trade_pct: float = Field(default=0.005, gt=0, le=0.1)
    max_total_risk_pct: float = Field(default=0.02, gt=0, le=0.5)
    max_open_positions: int = Field(default=3, ge=1, le=50)
    max_risk_distance_pct: float = Field(default=0.12, gt=0, le=0.5)
    shadow_only_requires_paper: bool = True


class AccountRiskSettingsUpdate(BaseModel):
    account_equity: float | None = Field(default=None, gt=0)
    max_risk_per_trade_pct: float | None = Field(default=None, gt=0, le=0.1)
    max_total_risk_pct: float | None = Field(default=None, gt=0, le=0.5)
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


class PortfolioRiskItem(BaseModel):
    position_id: str
    symbol_id: str
    status: str | None = None
    entry_price: float | None = None
    stop_price: float | None = None
    quantity: float | None = None
    risk_amount: float | None = None
    risk_pct: float | None = None
    source: Literal["position", "preview"] = "position"
    updated_at: datetime | None = None


class PortfolioRiskBucket(BaseModel):
    symbol_id: str
    risk_amount: float
    risk_pct: float
    position_count: int


class PortfolioRiskSummary(BaseModel):
    account_id: str
    account_equity: float
    max_total_risk_pct: float
    max_total_risk_amount: float
    max_open_positions: int
    active_position_count: int
    total_risk_amount: float
    total_risk_pct: float
    remaining_risk_amount: float
    remaining_risk_pct: float
    planned_risk_amount: float
    open_risk_amount: float
    reduced_risk_amount: float
    highest_symbol_risk: PortfolioRiskBucket | None = None
    by_symbol: list[PortfolioRiskBucket] = Field(default_factory=list)
    positions: list[PortfolioRiskItem] = Field(default_factory=list)
    notices: list[GuardrailNotice] = Field(default_factory=list)


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


class CandidateStratSignal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    signal_id: str
    symbol_id: str
    timeframe: str
    ts: datetime
    bar_type: str
    previous_bar_type: str | None = None
    pattern: str | None = None
    direction: str | None = None
    trigger_price: float | None = None
    trigger_stop: float | None = None
    invalidation: str | None = None
    timeframe_continuity: dict[str, Any] | None = None
    quality_score: float | None = None
    can_create_trade_alone: bool = False


class CandidateStratTriggerPlan(BaseModel):
    symbol_id: str
    timeframe: str
    latest_bar_ts: datetime | None = None
    latest_bar_type: str | None = None
    previous_bar_type: str | None = None
    status: str
    pattern: str | None = None
    direction: str | None = None
    trigger_price: float | None = None
    trigger_stop: float | None = None
    order_type: str | None = None
    stop_limit_price: float | None = None
    max_entry_price: float | None = None
    risk_per_share: float | None = None
    risk_distance_pct: float | None = None
    atr_14: float | None = None
    distance_to_sma_20_pct: float | None = None
    consecutive_2u_count: int = 0
    timeframe_continuity: dict[str, Any] | None = None
    no_chase_rules: list[dict[str, Any]] = Field(default_factory=list)
    can_create_trade_alone: bool = False


class CandidateDetail(BaseModel):
    candidate: Candidate
    pa_setup: CandidatePASetup | None = None
    strat_signal: CandidateStratSignal | None = None
    strat_plan: CandidateStratTriggerPlan | None = None
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
    portfolio_before: PortfolioRiskSummary | None = None
    portfolio_after_plan: PortfolioRiskSummary | None = None
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
    snoozed_until: datetime | None = None
    acknowledged: bool = False


class ExitAlertCreate(ExitAlertBase):
    alert_id: str | None = None


class ExitAlertUpdate(BaseModel):
    level: int | None = None
    action: str | None = None
    reason: str | None = None
    new_stop: float | None = None
    triggered_rules: str | None = None
    snoozed_until: datetime | None = None
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


class NotificationPreferencesBase(BaseModel):
    in_app_enabled: bool = True
    email_enabled: bool = False
    sms_enabled: bool = False
    min_severity: NotificationSeverity = "info"
    email_to: str | None = None
    phone_to: str | None = None
    event_preferences: dict[str, Any] = Field(default_factory=dict)


class NotificationPreferencesUpdate(BaseModel):
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    min_severity: NotificationSeverity | None = None
    email_to: str | None = None
    phone_to: str | None = None
    event_preferences: dict[str, Any] | None = None


class NotificationPreferences(NotificationPreferencesBase):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NotificationEventUpdate(BaseModel):
    read: bool | None = None
    acknowledged: bool | None = None
    snoozed_until: datetime | None = None


class NotificationEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: str
    account_id: str
    event_type: str
    severity: NotificationSeverity
    source_type: str | None = None
    source_id: str | None = None
    title: str | None = None
    body: str | None = None
    target_view: str | None = None
    target_id: str | None = None
    metadata_json: dict[str, Any] | None = None
    read_at: datetime | None = None
    acknowledged_at: datetime | None = None
    snoozed_until: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NotificationDeliveryLog(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    delivery_id: str
    notification_id: str
    account_id: str
    channel: NotificationChannel
    status: str
    target: str | None = None
    provider_message_id: str | None = None
    error_message: str | None = None
    attempted_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime | None = None


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


class ExecutionImport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    import_id: str
    account_id: str
    broker: str
    source_filename: str | None = None
    status: ExecutionImportStatus
    rows_total: int = 0
    rows_imported: int = 0
    rows_skipped: int = 0
    rows_failed: int = 0
    error_message: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExecutionFill(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fill_id: str
    import_id: str
    account_id: str
    position_id: str | None = None
    idempotency_key: str
    broker: str
    broker_account_id: str | None = None
    broker_order_id: str | None = None
    broker_execution_id: str | None = None
    symbol_id: str
    asset_type: str
    side: ExecutionFillSide
    quantity: float
    price: float
    gross_amount: float | None = None
    fees: float | None = None
    net_amount: float | None = None
    currency: str | None = None
    executed_at: datetime
    status: ExecutionFillStatus | None = "active"
    reconciliation_status: ExecutionFillReconciliationStatus | None = "matched"
    reconciliation_note: str | None = None
    reconciled_at: datetime | None = None
    raw_row_json: dict[str, Any] | None = None
    created_at: datetime | None = None


class ExecutionCSVImportRequest(BaseModel):
    broker: str = Field(default="edgepilot_generic_csv", min_length=1)
    source_filename: str | None = None
    csv_text: str = Field(..., min_length=1)


class ExecutionImportError(BaseModel):
    row_number: int
    message: str
    raw_row: dict[str, Any] = Field(default_factory=dict)


class ExecutionImportResult(BaseModel):
    import_record: ExecutionImport
    fills: list[ExecutionFill] = Field(default_factory=list)
    errors: list[ExecutionImportError] = Field(default_factory=list)


class ExecutionFillReconcileRequest(BaseModel):
    action: ExecutionFillReconcileAction
    target_position_id: str | None = None
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_action_payload(self) -> "ExecutionFillReconcileRequest":
        if self.action == "bind_position" and not (self.target_position_id or "").strip():
            raise ValueError("target_position_id is required when binding a fill")
        if self.target_position_id is not None:
            self.target_position_id = self.target_position_id.strip()
        if self.note is not None:
            self.note = self.note.strip() or None
        return self


class ExecutionFillReconciliationResult(BaseModel):
    fill: ExecutionFill
    source_position: Position | None = None
    target_position: Position | None = None
    message: str


class PositionCloseResponse(BaseModel):
    position: Position
    journal_trade: JournalTrade


class AutomationJobRunRequest(BaseModel):
    symbols: list[str] | None = None
    strategy_name: str = "oneil_core_us_etf"
    min_score: float = Field(default=60.0, ge=0, le=100)
    max_candidates: int = Field(default=25, ge=1, le=200)
    refresh_market_data: bool = True
    recalculate_outcomes: bool = True
    evaluate_alerts: bool = True
    outcome_limit: int | None = Field(default=None, ge=1, le=5000)
    alert_limit: int | None = Field(default=None, ge=1, le=500)

    @model_validator(mode="after")
    def normalize_symbols(self) -> "AutomationJobRunRequest":
        if self.symbols is not None:
            self.symbols = [symbol.strip().upper() for symbol in self.symbols if symbol.strip()]
        self.strategy_name = self.strategy_name.strip() or "oneil_core_us_etf"
        return self


class JobRun(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    account_id: str
    job_type: str
    status: str
    trigger: str | None = None
    records_written: int = 0
    error_message: str | None = None
    metadata_json: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None


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
