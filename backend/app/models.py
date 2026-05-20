from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    PrimaryKeyConstraint,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base

PA_JSON = JSON().with_variant(JSONB, "postgresql")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    external_subject: Mapped[str] = mapped_column(Text, unique=True, index=True)
    email: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    slug: Mapped[str | None] = mapped_column(Text, unique=True)
    owner_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"))
    status: Mapped[str | None] = mapped_column(Text, server_default=text("'active'"))
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class TenantMembership(Base):
    __tablename__ = "tenant_memberships"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    role: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(Text, primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(ForeignKey("tenants.tenant_id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class AccountMembership(Base):
    __tablename__ = "account_memberships"

    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    role: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class AccountRiskSettings(Base):
    __tablename__ = "account_risk_settings"

    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), primary_key=True)
    account_equity: Mapped[float | None] = mapped_column(Float)
    max_risk_per_trade_pct: Mapped[float | None] = mapped_column(Float)
    max_total_risk_pct: Mapped[float | None] = mapped_column(Float)
    max_open_positions: Mapped[int | None] = mapped_column(Integer)
    max_risk_distance_pct: Mapped[float | None] = mapped_column(Float)
    shadow_only_requires_paper: Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("true")
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    tenant_id: Mapped[str | None] = mapped_column(ForeignKey("tenants.tenant_id"), index=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"))
    action: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class LegalAcknowledgement(Base):
    __tablename__ = "legal_acknowledgements"
    __table_args__ = (
        Index(
            "idx_legal_ack_tenant_user_doc",
            "tenant_id",
            "user_id",
            "document_key",
            "document_version",
        ),
    )

    acknowledgement_id: Mapped[str] = mapped_column(Text, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    document_key: Mapped[str] = mapped_column(Text)
    document_version: Mapped[str] = mapped_column(Text)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    ip_address: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)


class TenantApiKey(Base):
    __tablename__ = "tenant_api_keys"
    __table_args__ = (Index("idx_tenant_api_keys_tenant_provider", "tenant_id", "provider"),)

    credential_id: Mapped[str] = mapped_column(Text, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id"))
    provider: Mapped[str] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text, server_default=text("'configured'"))
    encrypted_payload: Mapped[str | None] = mapped_column(Text)
    key_fingerprint: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class TenantDataCapability(Base):
    __tablename__ = "tenant_data_capabilities"
    __table_args__ = (
        Index(
            "idx_tenant_data_capabilities_unique",
            "tenant_id",
            "capability_key",
            unique=True,
        ),
        Index("idx_tenant_data_capabilities_status", "tenant_id", "status"),
    )

    capability_id: Mapped[str] = mapped_column(Text, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id"))
    capability_key: Mapped[str] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(Text)
    market: Mapped[str | None] = mapped_column(Text)
    asset_type: Mapped[str | None] = mapped_column(Text)
    timeframe: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class TenantJobState(Base):
    __tablename__ = "tenant_job_states"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "job_type"),
        Index("idx_tenant_job_states_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id"))
    job_type: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool | None] = mapped_column(Boolean, server_default=text("true"))
    status: Mapped[str | None] = mapped_column(Text, server_default=text("'idle'"))
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer)
    next_allowed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_id: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class Symbol(Base):
    __tablename__ = "symbols"

    symbol_id: Mapped[str] = mapped_column(Text, primary_key=True)
    ticker: Mapped[str] = mapped_column(Text)
    market: Mapped[str] = mapped_column(Text)
    asset_type: Mapped[str] = mapped_column(Text)
    exchange: Mapped[str | None] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool | None] = mapped_column(Boolean, server_default=text("true"))
    source: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class Bar(Base):
    __tablename__ = "bars"
    __table_args__ = (
        PrimaryKeyConstraint("symbol_id", "timeframe", "ts"),
        Index("idx_bars_symbol_tf_ts", "symbol_id", "timeframe", "ts"),
    )

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    symbol_id: Mapped[str] = mapped_column(Text)
    timeframe: Mapped[str] = mapped_column(Text)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)
    vwap: Mapped[float | None] = mapped_column(Float)
    adjusted: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    source: Mapped[str | None] = mapped_column(Text)


class OptionChainSnapshot(Base):
    __tablename__ = "options_chain_snapshots"
    __table_args__ = (
        PrimaryKeyConstraint("snapshot_ts", "option_symbol"),
        Index("idx_options_underlying_snapshot", "underlying_symbol", "snapshot_ts"),
        Index("idx_options_contract_snapshot", "option_symbol", "snapshot_ts"),
        Index("idx_options_exp_delta", "underlying_symbol", "expiration", "option_type", "delta"),
    )

    snapshot_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    underlying_symbol: Mapped[str] = mapped_column(Text)
    option_symbol: Mapped[str] = mapped_column(Text)
    expiration: Mapped[date] = mapped_column(Date)
    strike: Mapped[float] = mapped_column(Float)
    option_type: Mapped[str] = mapped_column(Text)
    bid: Mapped[float | None] = mapped_column(Float)
    ask: Mapped[float | None] = mapped_column(Float)
    mid: Mapped[float | None] = mapped_column(Float)
    last: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)
    open_interest: Mapped[float | None] = mapped_column(Float)
    iv: Mapped[float | None] = mapped_column(Float)
    delta: Mapped[float | None] = mapped_column(Float)
    gamma: Mapped[float | None] = mapped_column(Float)
    theta: Mapped[float | None] = mapped_column(Float)
    vega: Mapped[float | None] = mapped_column(Float)
    dte: Mapped[int | None] = mapped_column(Integer)
    spread_pct: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(Text)


class MarketContextSnapshot(Base):
    __tablename__ = "market_context_snapshots"
    __table_args__ = (PrimaryKeyConstraint("market", "snapshot_ts"),)

    snapshot_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    market: Mapped[str] = mapped_column(Text, server_default=text("'global'"))
    spy_return: Mapped[float | None] = mapped_column(Float)
    qqq_return: Mapped[float | None] = mapped_column(Float)
    iwm_return: Mapped[float | None] = mapped_column(Float)
    smh_return: Mapped[float | None] = mapped_column(Float)
    soxx_return: Mapped[float | None] = mapped_column(Float)
    vix_change: Mapped[float | None] = mapped_column(Float)
    usdjpy_change: Mapped[float | None] = mapped_column(Float)
    dxy_change: Mapped[float | None] = mapped_column(Float)
    us10y_change: Mapped[float | None] = mapped_column(Float)
    nikkei_futures_change: Mapped[float | None] = mapped_column(Float)
    topix_return: Mapped[float | None] = mapped_column(Float)
    japan_bias: Mapped[str | None] = mapped_column(Text)
    us_bias: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (
        Index("idx_candidates_account_scan_date", "account_id", "scan_date", "created_at"),
        Index("idx_candidates_account_decision", "account_id", "decision"),
    )

    candidate_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    symbol_id: Mapped[str] = mapped_column(Text)
    scan_date: Mapped[date] = mapped_column(Date)
    strategy_name: Mapped[str] = mapped_column(Text)
    setup_type: Mapped[str | None] = mapped_column(Text)
    pa_setup_id: Mapped[str | None] = mapped_column(ForeignKey("pa_setups.setup_id"))
    score_total: Mapped[float | None] = mapped_column(Float)
    entry_trigger: Mapped[float | None] = mapped_column(Float)
    initial_stop: Mapped[float | None] = mapped_column(Float)
    decision: Mapped[str | None] = mapped_column(Text)
    option_suitability: Mapped[str | None] = mapped_column(Text)
    ai_review_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class PAFact(Base):
    __tablename__ = "pa_facts"
    __table_args__ = (Index("idx_pa_facts_symbol_tf_ts", "symbol_id", "timeframe", "ts"),)

    fact_id: Mapped[str] = mapped_column(Text, primary_key=True)
    symbol_id: Mapped[str] = mapped_column(Text)
    timeframe: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    facts: Mapped[dict[str, Any]] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class PAStructure(Base):
    __tablename__ = "pa_structures"
    __table_args__ = (
        Index("idx_pa_structures_symbol_tf_ts", "symbol_id", "timeframe", "ts"),
        Index("idx_pa_structures_type", "structure_type"),
    )

    structure_id: Mapped[str] = mapped_column(Text, primary_key=True)
    symbol_id: Mapped[str] = mapped_column(Text)
    timeframe: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    structure_type: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class PASetup(Base):
    __tablename__ = "pa_setups"
    __table_args__ = (
        Index("idx_pa_setups_symbol_tf_detected", "symbol_id", "timeframe", "detected_ts"),
        Index("idx_pa_setups_filters", "setup_type", "status", "validation_status"),
    )

    setup_id: Mapped[str] = mapped_column(Text, primary_key=True)
    symbol_id: Mapped[str] = mapped_column(Text)
    timeframe: Mapped[str] = mapped_column(Text)
    detected_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    setup_type: Mapped[str] = mapped_column(Text)
    setup_grade: Mapped[str | None] = mapped_column(Text)
    pa_quality_score: Mapped[float | None] = mapped_column(Float)
    structure_score: Mapped[float | None] = mapped_column(Float)
    location_score: Mapped[float | None] = mapped_column(Float)
    volume_score: Mapped[float | None] = mapped_column(Float)
    trend_rs_score: Mapped[float | None] = mapped_column(Float)
    context_score: Mapped[float | None] = mapped_column(Float)
    risk_stop_score: Mapped[float | None] = mapped_column(Float)
    followthrough_score: Mapped[float | None] = mapped_column(Float)
    entry_plan: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    exit_plan: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    invalidation: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    status: Mapped[str | None] = mapped_column(Text)
    validation_status: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class StratSignal(Base):
    __tablename__ = "strat_signals"
    __table_args__ = (
        Index("idx_strat_signals_symbol_tf_ts", "symbol_id", "timeframe", "ts"),
        Index("idx_strat_signals_pattern_direction", "pattern", "direction"),
    )

    signal_id: Mapped[str] = mapped_column(Text, primary_key=True)
    symbol_id: Mapped[str] = mapped_column(Text)
    timeframe: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    bar_type: Mapped[str] = mapped_column(Text)
    previous_bar_type: Mapped[str | None] = mapped_column(Text)
    pattern: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[str | None] = mapped_column(Text)
    trigger_price: Mapped[float | None] = mapped_column(Float)
    trigger_stop: Mapped[float | None] = mapped_column(Float)
    invalidation: Mapped[str | None] = mapped_column(Text)
    timeframe_continuity: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    quality_score: Mapped[float | None] = mapped_column(Float)
    can_create_trade_alone: Mapped[bool | None] = mapped_column(
        Boolean,
        server_default=text("false"),
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class ScannerOutcome(Base):
    __tablename__ = "scanner_outcomes"
    __table_args__ = (
        Index("idx_scanner_outcomes_candidate", "candidate_id"),
        Index("idx_scanner_outcomes_setup", "pa_setup_id"),
        Index("idx_scanner_outcomes_account_status", "account_id", "evaluation_status"),
        Index("idx_scanner_outcomes_symbol_detected", "symbol_id", "timeframe", "detected_ts"),
    )

    outcome_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), unique=True)
    pa_setup_id: Mapped[str | None] = mapped_column(ForeignKey("pa_setups.setup_id"))
    symbol_id: Mapped[str] = mapped_column(Text)
    timeframe: Mapped[str] = mapped_column(Text)
    detected_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    setup_type: Mapped[str | None] = mapped_column(Text)
    setup_grade: Mapped[str | None] = mapped_column(Text)
    score_total: Mapped[float | None] = mapped_column(Float)
    reference_close: Mapped[float | None] = mapped_column(Float)
    entry_trigger: Mapped[float | None] = mapped_column(Float)
    initial_stop: Mapped[float | None] = mapped_column(Float)
    bars_available: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    evaluation_status: Mapped[str] = mapped_column(Text)
    latest_evaluated_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    triggered_entry: Mapped[bool | None] = mapped_column(Boolean)
    trigger_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_out: Mapped[bool | None] = mapped_column(Boolean)
    stop_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stop_hit_before_trigger: Mapped[bool | None] = mapped_column(Boolean)
    false_breakout: Mapped[bool | None] = mapped_column(Boolean)
    forward_return_5d: Mapped[float | None] = mapped_column(Float)
    forward_return_10d: Mapped[float | None] = mapped_column(Float)
    forward_return_20d: Mapped[float | None] = mapped_column(Float)
    forward_return_60d: Mapped[float | None] = mapped_column(Float)
    mfe_5d: Mapped[float | None] = mapped_column(Float)
    mfe_10d: Mapped[float | None] = mapped_column(Float)
    mfe_20d: Mapped[float | None] = mapped_column(Float)
    mfe_60d: Mapped[float | None] = mapped_column(Float)
    mae_5d: Mapped[float | None] = mapped_column(Float)
    mae_10d: Mapped[float | None] = mapped_column(Float)
    mae_20d: Mapped[float | None] = mapped_column(Float)
    mae_60d: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class PACalibrationStat(Base):
    __tablename__ = "pa_calibration_stats"
    __table_args__ = (
        Index(
            "idx_pa_calibration_filters",
            "setup_type",
            "market_regime",
            "sector_context",
            "timeframe",
        ),
    )

    stat_id: Mapped[str] = mapped_column(Text, primary_key=True)
    setup_type: Mapped[str] = mapped_column(Text)
    market_regime: Mapped[str | None] = mapped_column(Text)
    sector_context: Mapped[str | None] = mapped_column(Text)
    timeframe: Mapped[str | None] = mapped_column(Text)
    sample_size: Mapped[int | None] = mapped_column(Integer)
    win_rate: Mapped[float | None] = mapped_column(Float)
    average_r: Mapped[float | None] = mapped_column(Float)
    median_r: Mapped[float | None] = mapped_column(Float)
    profit_factor: Mapped[float | None] = mapped_column(Float)
    false_breakout_rate: Mapped[float | None] = mapped_column(Float)
    avg_mfe_r: Mapped[float | None] = mapped_column(Float)
    avg_mae_r: Mapped[float | None] = mapped_column(Float)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float)
    confidence_level: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class TestRun(Base):
    __tablename__ = "test_runs"
    __table_args__ = (
        Index(
            "idx_test_runs_account_strategy_completed",
            "account_id",
            "strategy_name",
            "completed_at",
        ),
        Index("idx_test_runs_account_status", "account_id", "status"),
    )

    test_run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    strategy_name: Mapped[str] = mapped_column(Text)
    stage: Mapped[str] = mapped_column(Text)
    run_type: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    sample_count: Mapped[int | None] = mapped_column(Integer)
    trades_count: Mapped[int | None] = mapped_column(Integer)
    win_rate: Mapped[float | None] = mapped_column(Float)
    profit_factor: Mapped[float | None] = mapped_column(Float)
    expectancy_r: Mapped[float | None] = mapped_column(Float)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float)
    execution_drag_r: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class SimulatedTrade(Base):
    __tablename__ = "simulated_trades"
    __table_args__ = (
        Index(
            "idx_simulated_trades_account_strategy_exit", "account_id", "strategy_name", "exit_ts"
        ),
        Index("idx_simulated_trades_test_run", "test_run_id"),
    )

    simulated_trade_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    test_run_id: Mapped[str | None] = mapped_column(ForeignKey("test_runs.test_run_id"))
    strategy_name: Mapped[str] = mapped_column(Text)
    symbol_id: Mapped[str] = mapped_column(Text)
    side: Mapped[str | None] = mapped_column(Text)
    entry_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exit_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entry_price: Mapped[float | None] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float)
    quantity: Mapped[float | None] = mapped_column(Float)
    pnl: Mapped[float | None] = mapped_column(Float)
    r_multiple: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class SignalFunnelSnapshot(Base):
    __tablename__ = "signal_funnel_snapshots"
    __table_args__ = (
        Index(
            "idx_signal_funnel_account_strategy_date", "account_id", "strategy_name", "scan_date"
        ),
    )

    snapshot_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    strategy_name: Mapped[str] = mapped_column(Text)
    stage: Mapped[str | None] = mapped_column(Text)
    scan_date: Mapped[date] = mapped_column(Date)
    scanned_count: Mapped[int | None] = mapped_column(Integer)
    rejected_count: Mapped[int | None] = mapped_column(Integer)
    watch_count: Mapped[int | None] = mapped_column(Integer)
    candidate_count: Mapped[int | None] = mapped_column(Integer)
    planned_count: Mapped[int | None] = mapped_column(Integer)
    accepted_count: Mapped[int | None] = mapped_column(Integer)
    rejection_breakdown: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class GoLiveGate(Base):
    __tablename__ = "go_live_gates"
    __table_args__ = (
        Index("idx_go_live_gates_unique", "account_id", "strategy_name", unique=True),
        Index("idx_go_live_gates_account_status", "account_id", "status"),
    )

    gate_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    strategy_name: Mapped[str] = mapped_column(Text)
    stage: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    required_trades: Mapped[int | None] = mapped_column(Integer)
    min_profit_factor: Mapped[float | None] = mapped_column(Float)
    min_expectancy_r: Mapped[float | None] = mapped_column(Float)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float)
    max_execution_drag_r: Mapped[float | None] = mapped_column(Float)
    current_trades: Mapped[int | None] = mapped_column(Integer)
    current_profit_factor: Mapped[float | None] = mapped_column(Float)
    current_expectancy_r: Mapped[float | None] = mapped_column(Float)
    current_max_drawdown_pct: Mapped[float | None] = mapped_column(Float)
    current_execution_drag_r: Mapped[float | None] = mapped_column(Float)
    reasons: Mapped[list[str] | None] = mapped_column(PA_JSON)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class StrategyKillSwitchStatus(Base):
    __tablename__ = "strategy_kill_switch_status"
    __table_args__ = (
        PrimaryKeyConstraint("account_id", "strategy_name"),
        Index("idx_strategy_kill_switch_account_status", "account_id", "status"),
    )

    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    strategy_name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    paused_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"))
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index("idx_positions_account_status", "account_id", "status", "updated_at"),
        Index("idx_positions_account_symbol_status", "account_id", "symbol_id", "status"),
    )

    position_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    symbol_id: Mapped[str] = mapped_column(Text)
    asset_type: Mapped[str] = mapped_column(Text)
    strategy_name: Mapped[str | None] = mapped_column(Text)
    exit_profile: Mapped[str | None] = mapped_column(Text)
    entry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entry_price: Mapped[float | None] = mapped_column(Float)
    quantity: Mapped[float | None] = mapped_column(Float)
    initial_stop: Mapped[float | None] = mapped_column(Float)
    current_stop: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str | None] = mapped_column(Text)
    current_r: Mapped[float | None] = mapped_column(Float)
    realized_pnl: Mapped[float | None] = mapped_column(Float)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class ExitAlert(Base):
    __tablename__ = "exit_alerts"
    __table_args__ = (
        Index(
            "idx_exit_alerts_account_ack_level", "account_id", "acknowledged", "level", "alert_ts"
        ),
        Index("idx_exit_alerts_account_position", "account_id", "position_id", "alert_ts"),
    )

    alert_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    position_id: Mapped[str] = mapped_column(Text)
    alert_ts: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    level: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    new_stop: Mapped[float | None] = mapped_column(Float)
    triggered_rules: Mapped[str | None] = mapped_column(Text)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), primary_key=True)
    in_app_enabled: Mapped[bool | None] = mapped_column(Boolean, server_default=text("true"))
    email_enabled: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    sms_enabled: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    min_severity: Mapped[str | None] = mapped_column(Text, server_default=text("'info'"))
    email_to: Mapped[str | None] = mapped_column(Text)
    phone_to: Mapped[str | None] = mapped_column(Text)
    event_preferences: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class NotificationEvent(Base):
    __tablename__ = "notification_events"
    __table_args__ = (
        Index("idx_notification_events_account_created", "account_id", "created_at"),
        Index("idx_notification_events_account_read", "account_id", "read_at", "created_at"),
        Index("idx_notification_events_source", "account_id", "source_type", "source_id"),
    )

    notification_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    event_type: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    target_view: Mapped[str | None] = mapped_column(Text)
    target_id: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class NotificationDeliveryLog(Base):
    __tablename__ = "notification_delivery_logs"
    __table_args__ = (
        Index("idx_notification_delivery_notification", "notification_id", "channel"),
        Index("idx_notification_delivery_account_created", "account_id", "created_at"),
    )

    delivery_id: Mapped[str] = mapped_column(Text, primary_key=True)
    notification_id: Mapped[str] = mapped_column(ForeignKey("notification_events.notification_id"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    channel: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    target: Mapped[str | None] = mapped_column(Text)
    provider_message_id: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class TradeJournal(Base):
    __tablename__ = "trades_journal"
    __table_args__ = (
        Index("idx_trades_journal_account_entry_ts", "account_id", "entry_ts"),
        Index("idx_trades_journal_account_symbol", "account_id", "symbol_id"),
    )

    trade_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    position_id: Mapped[str | None] = mapped_column(Text)
    symbol_id: Mapped[str | None] = mapped_column(Text)
    entry_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exit_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entry_price: Mapped[float | None] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float)
    quantity: Mapped[float | None] = mapped_column(Float)
    gross_pnl: Mapped[float | None] = mapped_column(Float)
    net_pnl: Mapped[float | None] = mapped_column(Float)
    r_multiple: Mapped[float | None] = mapped_column(Float)
    setup_type: Mapped[str | None] = mapped_column(Text)
    exit_reason: Mapped[str | None] = mapped_column(Text)
    mistake_tags: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class ExecutionImport(Base):
    __tablename__ = "execution_imports"
    __table_args__ = (
        Index("idx_execution_imports_account_created", "account_id", "created_at"),
        Index("idx_execution_imports_account_status", "account_id", "status", "created_at"),
    )

    import_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    broker: Mapped[str] = mapped_column(Text)
    source_filename: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    rows_total: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    rows_imported: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    rows_skipped: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    rows_failed: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class ExecutionFill(Base):
    __tablename__ = "execution_fills"
    __table_args__ = (
        Index("idx_execution_fills_account_executed", "account_id", "executed_at"),
        Index("idx_execution_fills_account_symbol", "account_id", "symbol_id", "executed_at"),
        Index("idx_execution_fills_position", "position_id", "executed_at"),
        Index("idx_execution_fills_idempotency", "idempotency_key", unique=True),
    )

    fill_id: Mapped[str] = mapped_column(Text, primary_key=True)
    import_id: Mapped[str] = mapped_column(ForeignKey("execution_imports.import_id"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    position_id: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(Text)
    broker: Mapped[str] = mapped_column(Text)
    broker_account_id: Mapped[str | None] = mapped_column(Text)
    broker_order_id: Mapped[str | None] = mapped_column(Text)
    broker_execution_id: Mapped[str | None] = mapped_column(Text)
    symbol_id: Mapped[str] = mapped_column(Text)
    asset_type: Mapped[str] = mapped_column(Text)
    side: Mapped[str] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    gross_amount: Mapped[float | None] = mapped_column(Float)
    fees: Mapped[float | None] = mapped_column(Float)
    net_amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(Text)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(Text, server_default=text("'active'"))
    reconciliation_status: Mapped[str | None] = mapped_column(
        Text,
        server_default=text("'matched'"),
    )
    reconciliation_note: Mapped[str | None] = mapped_column(Text)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_row_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (PrimaryKeyConstraint("account_id", "ts"),)

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    account_id: Mapped[str] = mapped_column(Text)
    equity: Mapped[float] = mapped_column(Float)
    cash: Mapped[float | None] = mapped_column(Float)
    gross_exposure: Mapped[float | None] = mapped_column(Float)
    net_exposure: Mapped[float | None] = mapped_column(Float)
    open_risk_amount: Mapped[float | None] = mapped_column(Float)
    open_risk_pct: Mapped[float | None] = mapped_column(Float)
    daily_pnl: Mapped[float | None] = mapped_column(Float)
    realized_pnl: Mapped[float | None] = mapped_column(Float)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float)
    drawdown_pct: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class AnalyticsDaily(Base):
    __tablename__ = "analytics_daily"
    __table_args__ = (PrimaryKeyConstraint("date", "account_id"),)

    date: Mapped[date] = mapped_column(Date)
    account_id: Mapped[str] = mapped_column(Text)
    equity: Mapped[float | None] = mapped_column(Float)
    daily_pnl: Mapped[float | None] = mapped_column(Float)
    daily_pnl_pct: Mapped[float | None] = mapped_column(Float)
    realized_pnl: Mapped[float | None] = mapped_column(Float)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float)
    trades_count: Mapped[int | None] = mapped_column(Integer)
    wins_count: Mapped[int | None] = mapped_column(Integer)
    losses_count: Mapped[int | None] = mapped_column(Integer)
    win_rate: Mapped[float | None] = mapped_column(Float)
    avg_win: Mapped[float | None] = mapped_column(Float)
    avg_loss: Mapped[float | None] = mapped_column(Float)
    profit_factor: Mapped[float | None] = mapped_column(Float)
    expectancy_r: Mapped[float | None] = mapped_column(Float)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float)
    open_positions_count: Mapped[int | None] = mapped_column(Integer)
    option_exposure_pct: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class DataFreshness(Base):
    __tablename__ = "data_freshness"

    dataset_key: Mapped[str] = mapped_column(Text, primary_key=True)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (Index("idx_ingestion_runs_dataset_started", "dataset_key", "started_at"),)

    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    dataset_key: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    records_written: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    source: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)


class JobRun(Base):
    __tablename__ = "job_runs"
    __table_args__ = (
        Index("idx_job_runs_account_started", "account_id", "started_at"),
        Index("idx_job_runs_account_status", "account_id", "status", "started_at"),
    )

    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"))
    job_type: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    trigger: Mapped[str | None] = mapped_column(Text)
    records_written: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(PA_JSON)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
