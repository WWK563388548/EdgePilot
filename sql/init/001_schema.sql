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

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id TEXT PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS positions (
    position_id TEXT PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS exit_alerts (
    alert_id TEXT PRIMARY KEY,
    position_id TEXT NOT NULL,
    alert_ts TIMESTAMPTZ DEFAULT now(),
    level INTEGER,
    action TEXT,
    reason TEXT,
    new_stop DOUBLE PRECISION,
    triggered_rules TEXT,
    acknowledged BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS trades_journal (
    trade_id TEXT PRIMARY KEY,
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
