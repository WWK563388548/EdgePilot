from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ValidationStage = Literal["data_quality", "backtest", "shadow", "paper", "micro_live_allowed"]
ValidationGateStatus = Literal["blocked", "shadow_only", "paper_only", "micro_live_allowed"]
ValidationTestRunStatus = Literal["running", "succeeded", "failed"]
ValidationKillSwitchStatus = Literal["active", "paused", "blocked"]


class TestRunCreate(BaseModel):
    test_run_id: str | None = None
    strategy_name: str = Field(..., min_length=1)
    stage: ValidationStage = "backtest"
    run_type: str = Field(default="manual", min_length=1)
    status: ValidationTestRunStatus = "succeeded"
    sample_count: int | None = Field(default=None, ge=0)
    trades_count: int | None = Field(default=None, ge=0)
    win_rate: float | None = Field(default=None, ge=0, le=1)
    profit_factor: float | None = Field(default=None, ge=0)
    expectancy_r: float | None = None
    max_drawdown_pct: float | None = None
    execution_drag_r: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata_json: dict[str, Any] | None = None


class TestRun(TestRunCreate):
    model_config = ConfigDict(from_attributes=True)

    test_run_id: str
    account_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SimulatedTradeCreate(BaseModel):
    simulated_trade_id: str | None = None
    test_run_id: str | None = None
    strategy_name: str = Field(..., min_length=1)
    symbol_id: str = Field(..., min_length=1)
    side: Literal["long", "short"] | None = "long"
    entry_ts: datetime | None = None
    exit_ts: datetime | None = None
    entry_price: float | None = Field(default=None, gt=0)
    exit_price: float | None = Field(default=None, gt=0)
    quantity: float | None = Field(default=None, gt=0)
    pnl: float | None = None
    r_multiple: float | None = None
    status: str | None = None
    metadata_json: dict[str, Any] | None = None


class SimulatedTrade(SimulatedTradeCreate):
    model_config = ConfigDict(from_attributes=True)

    simulated_trade_id: str
    account_id: str
    created_at: datetime | None = None


class SignalFunnelSnapshotCreate(BaseModel):
    snapshot_id: str | None = None
    strategy_name: str = Field(..., min_length=1)
    stage: ValidationStage | None = None
    scan_date: date
    scanned_count: int | None = Field(default=None, ge=0)
    rejected_count: int | None = Field(default=None, ge=0)
    watch_count: int | None = Field(default=None, ge=0)
    candidate_count: int | None = Field(default=None, ge=0)
    planned_count: int | None = Field(default=None, ge=0)
    accepted_count: int | None = Field(default=None, ge=0)
    rejection_breakdown: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None


class SignalFunnelSnapshot(SignalFunnelSnapshotCreate):
    model_config = ConfigDict(from_attributes=True)

    snapshot_id: str
    account_id: str
    created_at: datetime | None = None


class GoLiveGateEvaluateRequest(BaseModel):
    required_trades: int = Field(default=30, ge=1)
    min_profit_factor: float = Field(default=1.1, ge=0)
    min_expectancy_r: float = Field(default=0.05)
    max_drawdown_pct: float = Field(default=0.15, ge=0, le=1)
    max_execution_drag_r: float = Field(default=0.2, ge=0)
    metadata_json: dict[str, Any] | None = None


class GoLiveGate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    gate_id: str
    account_id: str
    strategy_name: str
    stage: ValidationStage
    status: ValidationGateStatus
    required_trades: int | None = None
    min_profit_factor: float | None = None
    min_expectancy_r: float | None = None
    max_drawdown_pct: float | None = None
    max_execution_drag_r: float | None = None
    current_trades: int | None = None
    current_profit_factor: float | None = None
    current_expectancy_r: float | None = None
    current_max_drawdown_pct: float | None = None
    current_execution_drag_r: float | None = None
    reasons: list[str] = Field(default_factory=list)
    evaluated_at: datetime | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StrategyKillSwitchUpdate(BaseModel):
    status: ValidationKillSwitchStatus
    reason: str | None = None
    expires_at: datetime | None = None
    metadata_json: dict[str, Any] | None = None


class StrategyKillSwitch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    strategy_name: str
    status: ValidationKillSwitchStatus
    reason: str | None = None
    paused_by_user_id: str | None = None
    paused_at: datetime | None = None
    expires_at: datetime | None = None
    metadata_json: dict[str, Any] | None = None
    updated_at: datetime | None = None


class StrategyReadiness(BaseModel):
    strategy_name: str
    gate: GoLiveGate
    latest_test_run: TestRun | None = None
    kill_switch: StrategyKillSwitch | None = None
