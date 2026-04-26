from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

CandidateDecision = Literal["candidate", "watch", "avoid"]
PositionStatus = Literal["open", "reduce", "exit_pending", "closed"]


class CandidateBase(BaseModel):
    symbol_id: str = Field(..., min_length=1)
    scan_date: date
    strategy_name: str = Field(..., min_length=1)
    setup_type: str | None = None
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
    score_total: float | None = None
    entry_trigger: float | None = None
    initial_stop: float | None = None
    decision: CandidateDecision | None = None
    option_suitability: str | None = None
    ai_review_json: str | None = None


class Candidate(CandidateBase):
    candidate_id: str
    created_at: datetime | None = None


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


class PositionUpdate(BaseModel):
    strategy_name: str | None = None
    current_stop: float | None = None
    status: PositionStatus | None = None
    current_r: float | None = None
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None


class Position(PositionBase):
    position_id: str
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
    alert_id: str
    alert_ts: datetime | None = None


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
    trade_id: str


class DataFreshnessSummary(BaseModel):
    dataset_key: str
    last_updated_at: datetime
    source: str | None = None


class MarketContextSummary(BaseModel):
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
