CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS symbols (
    symbol_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    market TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    exchange TEXT,
    name TEXT,
    sector TEXT,
    industry TEXT,
    currency TEXT,
    active BOOLEAN DEFAULT TRUE,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bars (
    ts TIMESTAMPTZ NOT NULL,
    symbol_id TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    vwap DOUBLE PRECISION,
    adjusted BOOLEAN DEFAULT FALSE,
    source TEXT,
    PRIMARY KEY (symbol_id, timeframe, ts)
);
SELECT create_hypertable('bars', 'ts', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_bars_symbol_tf_ts
ON bars (symbol_id, timeframe, ts DESC);

CREATE TABLE IF NOT EXISTS options_chain_snapshots (
    snapshot_ts TIMESTAMPTZ NOT NULL,
    underlying_symbol TEXT NOT NULL,
    option_symbol TEXT NOT NULL,
    expiration DATE NOT NULL,
    strike DOUBLE PRECISION NOT NULL,
    option_type TEXT NOT NULL,
    bid DOUBLE PRECISION,
    ask DOUBLE PRECISION,
    mid DOUBLE PRECISION,
    last DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    open_interest DOUBLE PRECISION,
    iv DOUBLE PRECISION,
    delta DOUBLE PRECISION,
    gamma DOUBLE PRECISION,
    theta DOUBLE PRECISION,
    vega DOUBLE PRECISION,
    dte INTEGER,
    spread_pct DOUBLE PRECISION,
    source TEXT,
    PRIMARY KEY (snapshot_ts, option_symbol)
);
SELECT create_hypertable('options_chain_snapshots', 'snapshot_ts', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_options_underlying_snapshot
ON options_chain_snapshots (underlying_symbol, snapshot_ts DESC);
CREATE INDEX IF NOT EXISTS idx_options_contract_snapshot
ON options_chain_snapshots (option_symbol, snapshot_ts DESC);
CREATE INDEX IF NOT EXISTS idx_options_exp_delta
ON options_chain_snapshots (underlying_symbol, expiration, option_type, delta);

CREATE TABLE IF NOT EXISTS market_context_snapshots (
    snapshot_ts TIMESTAMPTZ NOT NULL,
    market TEXT NOT NULL DEFAULT 'global',
    spy_return DOUBLE PRECISION,
    qqq_return DOUBLE PRECISION,
    iwm_return DOUBLE PRECISION,
    smh_return DOUBLE PRECISION,
    soxx_return DOUBLE PRECISION,
    vix_change DOUBLE PRECISION,
    usdjpy_change DOUBLE PRECISION,
    dxy_change DOUBLE PRECISION,
    us10y_change DOUBLE PRECISION,
    nikkei_futures_change DOUBLE PRECISION,
    topix_return DOUBLE PRECISION,
    japan_bias TEXT,
    us_bias TEXT,
    risk_level TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (market, snapshot_ts)
);
SELECT create_hypertable('market_context_snapshots', 'snapshot_ts', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    external_subject TEXT NOT NULL UNIQUE,
    email TEXT,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_login_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_users_external_subject
ON users (external_subject);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS account_memberships (
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (account_id, user_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    actor_user_id TEXT REFERENCES users(user_id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    metadata_json TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_account_id
ON audit_logs (account_id);

INSERT INTO accounts (account_id, name)
VALUES ('acct_local', 'Local Dev')
ON CONFLICT (account_id) DO NOTHING;
INSERT INTO users (user_id, external_subject, email, display_name)
VALUES ('user_local', 'local-dev', 'local@edgepilot.dev', 'Local Dev')
ON CONFLICT (user_id) DO NOTHING;
INSERT INTO account_memberships (account_id, user_id, role)
VALUES ('acct_local', 'user_local', 'owner')
ON CONFLICT (account_id, user_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    symbol_id TEXT NOT NULL,
    scan_date DATE NOT NULL,
    strategy_name TEXT NOT NULL,
    setup_type TEXT,
    score_total DOUBLE PRECISION,
    entry_trigger DOUBLE PRECISION,
    initial_stop DOUBLE PRECISION,
    decision TEXT,
    option_suitability TEXT,
    ai_review_json TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_candidates_account_scan_date
ON candidates (account_id, scan_date DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_candidates_account_decision
ON candidates (account_id, decision);

CREATE TABLE IF NOT EXISTS positions (
    position_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    symbol_id TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    strategy_name TEXT,
    entry_date TIMESTAMPTZ,
    entry_price DOUBLE PRECISION,
    quantity DOUBLE PRECISION,
    initial_stop DOUBLE PRECISION,
    current_stop DOUBLE PRECISION,
    status TEXT,
    current_r DOUBLE PRECISION,
    realized_pnl DOUBLE PRECISION,
    unrealized_pnl DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_positions_account_status
ON positions (account_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_positions_account_symbol_status
ON positions (account_id, symbol_id, status);

CREATE TABLE IF NOT EXISTS exit_alerts (
    alert_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    position_id TEXT NOT NULL,
    alert_ts TIMESTAMPTZ DEFAULT now(),
    level INTEGER,
    action TEXT,
    reason TEXT,
    new_stop DOUBLE PRECISION,
    triggered_rules TEXT,
    acknowledged BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_exit_alerts_account_ack_level
ON exit_alerts (account_id, acknowledged, level DESC, alert_ts DESC);
CREATE INDEX IF NOT EXISTS idx_exit_alerts_account_position
ON exit_alerts (account_id, position_id, alert_ts DESC);

CREATE TABLE IF NOT EXISTS trades_journal (
    trade_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    position_id TEXT,
    symbol_id TEXT,
    entry_ts TIMESTAMPTZ,
    exit_ts TIMESTAMPTZ,
    entry_price DOUBLE PRECISION,
    exit_price DOUBLE PRECISION,
    quantity DOUBLE PRECISION,
    gross_pnl DOUBLE PRECISION,
    net_pnl DOUBLE PRECISION,
    r_multiple DOUBLE PRECISION,
    setup_type TEXT,
    exit_reason TEXT,
    mistake_tags TEXT,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_trades_journal_account_entry_ts
ON trades_journal (account_id, entry_ts DESC);
CREATE INDEX IF NOT EXISTS idx_trades_journal_account_symbol
ON trades_journal (account_id, symbol_id);

CREATE TABLE IF NOT EXISTS execution_imports (
    import_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    broker TEXT NOT NULL,
    source_filename TEXT,
    status TEXT NOT NULL,
    rows_total INTEGER DEFAULT 0,
    rows_imported INTEGER DEFAULT 0,
    rows_skipped INTEGER DEFAULT 0,
    rows_failed INTEGER DEFAULT 0,
    error_message TEXT,
    metadata_json JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_execution_imports_account_created
ON execution_imports (account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_imports_account_status
ON execution_imports (account_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS execution_fills (
    fill_id TEXT PRIMARY KEY,
    import_id TEXT NOT NULL REFERENCES execution_imports(import_id),
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    position_id TEXT,
    idempotency_key TEXT NOT NULL,
    broker TEXT NOT NULL,
    broker_account_id TEXT,
    broker_order_id TEXT,
    broker_execution_id TEXT,
    symbol_id TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    gross_amount DOUBLE PRECISION,
    fees DOUBLE PRECISION,
    net_amount DOUBLE PRECISION,
    currency TEXT,
    executed_at TIMESTAMPTZ NOT NULL,
    raw_row_json JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_execution_fills_account_executed
ON execution_fills (account_id, executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_fills_account_symbol
ON execution_fills (account_id, symbol_id, executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_fills_position
ON execution_fills (position_id, executed_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_execution_fills_idempotency
ON execution_fills (idempotency_key);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    ts TIMESTAMPTZ NOT NULL,
    account_id TEXT NOT NULL,
    equity DOUBLE PRECISION NOT NULL,
    cash DOUBLE PRECISION,
    gross_exposure DOUBLE PRECISION,
    net_exposure DOUBLE PRECISION,
    open_risk_amount DOUBLE PRECISION,
    open_risk_pct DOUBLE PRECISION,
    daily_pnl DOUBLE PRECISION,
    realized_pnl DOUBLE PRECISION,
    unrealized_pnl DOUBLE PRECISION,
    drawdown_pct DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (account_id, ts)
);
SELECT create_hypertable('portfolio_snapshots', 'ts', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS analytics_daily (
    date DATE NOT NULL,
    account_id TEXT NOT NULL,
    equity DOUBLE PRECISION,
    daily_pnl DOUBLE PRECISION,
    daily_pnl_pct DOUBLE PRECISION,
    realized_pnl DOUBLE PRECISION,
    unrealized_pnl DOUBLE PRECISION,
    trades_count INTEGER,
    wins_count INTEGER,
    losses_count INTEGER,
    win_rate DOUBLE PRECISION,
    avg_win DOUBLE PRECISION,
    avg_loss DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    expectancy_r DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    open_positions_count INTEGER,
    option_exposure_pct DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (date, account_id)
);

CREATE TABLE IF NOT EXISTS data_freshness (
    dataset_key TEXT PRIMARY KEY,
    last_updated_at TIMESTAMPTZ NOT NULL,
    source TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,
    dataset_key TEXT NOT NULL,
    status TEXT NOT NULL,
    records_written INTEGER NOT NULL DEFAULT 0,
    source TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_dataset_started
ON ingestion_runs (dataset_key, started_at DESC);
