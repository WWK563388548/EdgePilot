# EdgePilot PRD/TDD v0.9

This is the repo-maintained PRD/TDD for EdgePilot v0.9. It captures the current product requirements, technical design, data contracts, risk rules, and implementation plan. It intentionally replaces the older stacked v0.3/v0.6 planning docs and avoids carrying superseded historical sections forward.

Source basis: `EdgePilot_PRD_TDD_Implementation_Plan_v0_9_Strat_PA_Short_Framework.md`, dated 2026-05-04.

## 1. Product Definition

EdgePilot is a manual trading operations cockpit for a small account.

It screens US ETF and stock candidates, explains price-action evidence, creates paper/manual plans, tracks positions, enforces risk guardrails, raises exit alerts, and records journals.

It does not place broker orders. Every entry, trim, stop, and close is manually confirmed by the user.

## 2. User Context And Constraints

- User is based in Japan.
- Initial active trading capital is small, roughly 1,000-2,000 USD.
- Monthly additions are modest, roughly 10,000-20,000 JPY.
- Larger wealth remains in NISA and savings.
- Polygon/Massive is available for US market data.
- Japan moomoo OpenAPI is not available as a system data source.
- TradingView remains a personal final-review tool, not an application data source.
- The system should reduce chart-scanning time and produce explainable candidates, plans, risk checks, and exit prompts.

## 3. Product Principles

- No automatic trading.
- Protect capital before seeking return.
- Exit management is as important as candidate generation.
- PA is core.
- Strat is a trigger layer inside PA, not a standalone strategy.
- The default system remains long-biased.
- Bearish logic first reduces long risk.
- Short watchlist and paper short are research/paper capabilities first.
- Live short remains disabled until a future validation gate.
- Options are lowest-priority research/paper backlog.
- AI can explain, challenge, and summarize. AI cannot upgrade a trade, override stops, or increase risk.
- If a rule cannot be measured, it is research-only.
- If unsure, do less.

## 4. Non-Goals

The system does not target:

- Broker order execution.
- High-frequency trading.
- Full order book scanning.
- 0DTE strategies.
- Naked options.
- Short options.
- All-in or martingale trading.
- Meme-stock chasing.
- Earnings lottery trades.
- AI prediction of macro/news events.
- Guaranteed profitability.

## 5. MVP Scope

### Assets

- US ETFs first.
- US liquid large-cap stocks after the ETF workflow proves stable.
- Japan daily candidates later through J-Quants.
- Options remain research-only and disabled from live workflows.

### Strategy Scope

- O'Neil-core US ETF scanner as the first scanner.
- Basic PA: breakout, pullback, failed breakdown reclaim, VWAP reclaim, opening range where data allows.
- Strat Trigger Layer v1: objective bar labeling and small pattern set.
- Portfolio Risk Monitor.
- Position Ledger.
- Exit Engine.
- Journal and scanner outcome review.
- PA / Strat Calibration Lite before expanding rule complexity.

### Live/Paper Decision Path

```text
Data
  -> Scanner
  -> Market / data quality gate
  -> Basic PA
  -> Strat Trigger Layer
  -> Risk Engine
  -> Candidate
  -> Paper/Manual Position
  -> Exit Engine
  -> Journal
  -> Analytics / Calibration
```

## 6. PA And Strat Definitions

### PA Engine

PA is the system's structure analysis layer. It answers:

- Does this chart have tradeable structure?
- Where is the setup valid?
- Where is it invalidated?
- Is the risk controllable?

PA inputs include:

- Trend.
- Base.
- Support/resistance.
- Breakout.
- Pullback.
- VWAP reclaim.
- Opening range.
- Failed breakdown reclaim.
- Volume confirmation.
- Market/sector context.
- Entry, stop, and invalidation.

### Strat Trigger Layer

Strat is the objective trigger grammar inside PA. It answers:

- Did the current bar produce an objective trigger?
- Where is the trigger price?
- Where is the trigger-bar stop?
- Are higher timeframes aligned?

Strat cannot create trades alone. It can confirm, delay, downgrade, or invalidate a PA candidate.

## 7. Strat v1 Scope

### Bar State

```text
1  = inside bar: current high <= previous high and current low >= previous low
2U = directional up bar: current high > previous high and current low >= previous low
2D = directional down bar: current low < previous low and current high <= previous high
3  = outside bar: current high > previous high and current low < previous low
```

### Timeframe Continuity

Supported timeframes:

- Monthly.
- Weekly.
- Daily.
- 60m.
- 15m as alert-only later.

Computed fields:

- `open_position`.
- `above_open`.
- `below_open`.
- `continuity_state`: bullish, bearish, mixed, neutral.

### Pattern Budget

Strat v1 allows at most six live/paper decision patterns:

- inside breakout.
- 2-1-2 continuation.
- 2-1-2 reversal.
- 3-1-2 reversal.
- 2U continuation.
- 2D continuation.

Out of scope for v1:

- Full Strat pattern library.
- Complex broadening-formation drawing.
- Complex trigger stacking.
- AI visual Strat recognition.

## 8. Strat Signal Contract

```json
{
  "symbol": "QQQ",
  "timeframe": "1d",
  "bar_type": "2U",
  "previous_bar_type": "1",
  "pattern": "2-1-2_continuation",
  "direction": "long",
  "trigger_price": 455.2,
  "trigger_stop": 443.8,
  "invalidation": "close back below trigger bar low",
  "timeframe_continuity": {
    "monthly": "bullish",
    "weekly": "bullish",
    "daily": "bullish",
    "60m": "mixed"
  },
  "quality": "valid_trigger",
  "can_create_trade_alone": false
}
```

## 9. Short Capability Framework

EdgePilot remains long-biased by default.

Bearish signals first serve:

- Avoid long.
- Downgrade candidate.
- Tighten stop.
- Reduce position.
- Exit existing long.
- Create paper-only short watchlist.

### Capability Levels

- Level 0: no short, default.
- Level 1: bearish context only.
- Level 2: short watchlist.
- Level 3: paper short.
- Level 4: micro live short, future research only.

Live short requires future evidence:

- 100+ paper short trades.
- Positive expectancy.
- Controlled drawdown.
- Borrow data available.
- Short-squeeze and event-risk filters available.
- Manual execution discipline proven.

### Permanent Or Default Short Blocks

- Short options.
- Naked options.
- All-in short.
- Martingale short.
- Short after large down-move chase.
- Short meme stocks.
- Short low-liquidity stocks.
- Short hard-to-borrow names without borrow data.
- Short before earnings.
- Short during major macro/event windows.
- Short without stop.
- Short when the account cannot tolerate gap-up stress.

## 10. Short Watch / Paper Short v1

Short v1 can only produce watch or paper outputs.

### Failed Breakout Short Watch

Inputs:

- Price breaks above resistance.
- Price fails to hold and closes back inside range.
- Heavy volume.
- Market or sector weak.
- Strat down trigger, such as 2D or 3-1-2 down confirmation.

Output:

- Entry: break of failed breakout low.
- Cover stop: failed breakout high.
- Invalidation: reclaim above failed breakout high.

### Bear Flag Breakdown Watch

Inputs:

- Downtrend.
- Weak bounce into declining 20MA / 50MA.
- Volume contracts on bounce.
- Breaks bear flag low.
- Strat 2D continuation.

Output:

- Entry: break of bear flag low.
- Cover stop: flag high.
- Invalidation: reclaim above 20MA or structure high.

### Relative Weakness Short Watch

Inputs:

- Market flat or up.
- Symbol underperforms.
- Below 50MA / 200MA.
- Failed reclaim.
- Sector weak.

Output:

- Entry: breakdown trigger.
- Cover stop: reclaim level.
- Invalidation: relative strength improves.

## 11. Database Design For v0.9 Roadmap

### Candidate Direction Extensions

Planned candidate fields:

- `trade_direction`: long, short, neutral.
- `allowed_direction`: long_only, long_or_short_watch, no_trade.
- `strat_bar_type`.
- `strat_pattern`.
- `strat_trigger_price`.
- `strat_trigger_stop`.
- `strat_invalidation`.
- `timeframe_continuity`.
- `short_permission`: disabled, blocked, paper_only, micro_live_allowed.
- `short_reject_reasons`.

### Position Direction Extensions

Planned position fields:

- `position_side`: long, short.
- `trade_direction`.
- `cover_stop`.
- `borrow_fee`.
- `borrow_status`.
- `short_risk_level`.

### Journal Extensions

Planned journal fields:

- `trade_direction`.
- `exit_action`: sell_to_close, buy_to_cover.
- `borrow_cost`.
- `gap_risk_tag`.
- `strat_pattern`.
- `timeframe_continuity`.

### `strat_signals`

```sql
CREATE TABLE strat_signals (
    signal_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts TIMESTAMP NOT NULL,
    bar_type TEXT NOT NULL,
    previous_bar_type TEXT,
    pattern TEXT,
    direction TEXT,
    trigger_price DOUBLE PRECISION,
    trigger_stop DOUBLE PRECISION,
    invalidation TEXT,
    timeframe_continuity JSONB,
    quality_score DOUBLE PRECISION,
    can_create_trade_alone BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

### `short_risk_snapshots`

```sql
CREATE TABLE short_risk_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    snapshot_ts TIMESTAMP NOT NULL,
    borrow_available BOOLEAN,
    borrow_fee DOUBLE PRECISION,
    hard_to_borrow BOOLEAN,
    short_interest_proxy DOUBLE PRECISION,
    days_to_cover_proxy DOUBLE PRECISION,
    liquidity_score DOUBLE PRECISION,
    spread_pct DOUBLE PRECISION,
    gap_up_risk_score DOUBLE PRECISION,
    event_risk_level TEXT,
    short_squeeze_risk TEXT,
    short_permission TEXT,
    reject_reasons JSONB,
    source TEXT,
    created_at TIMESTAMP
);
```

## 12. API Design For v0.9 Roadmap

### Strat APIs

```http
POST /api/pa/strat/scan
GET  /api/pa/strat/signals?symbol=&timeframe=&date=
GET  /api/pa/strat/continuity/{symbol}
GET  /api/pa/strat/patterns/{symbol}
```

### Candidate Direction APIs

```http
GET   /api/candidates?direction=long
GET   /api/candidates?direction=short_watch
GET   /api/candidates?direction=all
PATCH /api/candidates/{candidate_id}/direction
```

### Short APIs

```http
POST /api/short/watchlist/run
GET  /api/short/watchlist
GET  /api/short/risk/{symbol}
POST /api/short/paper-position
POST /api/short/paper-position/{position_id}/cover
```

Rules:

- No endpoint sends broker orders.
- No endpoint enables live short without config plus validation gate.

## 13. Frontend Design For v0.9 Roadmap

### Candidate Fields

- Direction.
- Allowed Direction.
- Strat Bar.
- Strat Pattern.
- Timeframe Continuity.
- Trigger Price.
- Trigger Stop.
- Short Permission.
- Reject Reasons.

### Badges

- `DirectionBadge`: Long, Short Watch, Paper Short, No Trade.
- `StratBadge`: 1, 2U, 2D, 3, 2-1-2, 3-1-2.
- `PermissionBadge`: Live Allowed, Paper Only, Disabled, Blocked.

### Chart Marks

- Previous bar high / low.
- Inside bar range.
- 2U / 2D trigger level.
- Outside bar range.
- Entry trigger.
- Trigger-bar stop.
- Paper short cover stop.

### Short Watchlist Page

The page must clearly state:

- Short Watchlist is paper-only by default.
- EdgePilot is long-biased unless explicitly unlocked by validation.
- Shorting has asymmetric risk and may lose more than expected on gap-up events.

Fields:

- Ticker.
- Setup.
- Strat Pattern.
- Entry Trigger.
- Cover Stop.
- Gap-up stress loss.
- Borrow status.
- Event risk.
- Short permission.
- Reject reason.
- Paper trade button.

## 14. Configuration

```yaml
pa:
  enable_structure_pa: true
  enable_strat_trigger_layer: true
  strat_v1_enabled: true
  strat_can_create_trade_alone: false
  strat_patterns_enabled:
    - inside_breakout
    - 2-1-2_continuation
    - 2-1-2_reversal
    - 3-1-2_reversal
    - 2U_continuation
    - 2D_continuation
  max_strat_patterns_live: 6

shorts:
  system_default_bias: long_biased
  allow_bearish_context: true
  allow_short_watchlist: true
  allow_short_paper: true
  allow_short_stock_live: false
  allow_short_etf_live: false
  allow_short_options: false
  no_short_small_caps: true
  no_short_low_liquidity: true
  no_short_meme_stocks: true
  no_short_before_earnings: true
  no_short_during_major_events: true
  no_short_after_large_down_move: true
  require_borrow_data_for_live: true
  require_gap_stress_test_for_live: true

options:
  live_enabled: false
  research_only: true
  priority: lowest
```

## 15. Anti-Overfitting Governance

### Decision Rights

Production/paper engines:

- US ETF Scanner v1.
- Basic PA Engine.
- Strat Trigger Layer v1, only as PA confirmation/downgrade.
- Risk Engine.
- Position Ledger.
- Exit Engine.
- Journal / Paper Trading.

Risk-only engines:

- Portfolio Risk Monitor.
- Market Regime Filter.
- Data Freshness Guard.
- Headline/Event Risk Filter, future.
- Short Risk Guard, future.

Research-only engines:

- Advanced PA rules before validation.
- Short Watchlist before paper validation.
- Options Adapter.
- AI Reviewer before explicit permissioning.

### Validation Rules

- Strat v1 live/paper pattern budget <= 6.
- Strat cannot create a candidate without scanner + PA context.
- Every Strat or Advanced PA rule must compare PA-only vs PA-plus-rule.
- New rules start research-only or shadow-only.
- Rules can graduate only through enough out-of-sample evidence.
- Added complexity must beat a simpler baseline.

Required metrics:

- Average R.
- Win rate.
- Profit factor.
- Max drawdown.
- Stop-out rate.
- False breakout rate.
- Missed winner rate.

## 16. Implementation Plan

### P0: Risk + Position + Exit Foundation

Status: mostly implemented.

Acceptance:

- Positions can move through planned, open, reduced, and closed.
- Plans have entry, stop, quantity, and risk.
- Portfolio risk budget can block oversized new plans.
- Exit alerts can be evaluated, acknowledged, and snoozed.
- Journal entries are created on close.

Remaining:

- Drawdown halt.
- Consecutive-loss rule.
- Data repair/diagnostic endpoint for incomplete planned positions.

### P1: US ETF / Large-Cap Scanner + Basic PA + Strat Bar Labeling

Next feature area.

Acceptance:

- `strat_signals` exists.
- Daily bar state `1 / 2U / 2D / 3` is computed.
- Minimal patterns are detected.
- Strat summary appears in candidate detail.
- Strat cannot create standalone trades.
- Candidate scanner can mark confirmed/watch/avoid based on PA + Strat.

### P2: Frontend Trading Cockpit

Status: implemented for current modules.

Remaining:

- Position detail drawer.
- Stronger level-4 alert visualization.
- Data quality/system health panel.
- Richer chart marks for Strat trigger and trigger stop.

### P3: Paper Trading + Journal Analytics

Acceptance:

- Paper/manual plans can be tracked through lifecycle.
- Journal can compare setup performance.
- Review pages show scanner outcome, forward returns, false breakouts, and R results.

### P4: PA / Strat Calibration Lite

Acceptance:

- Compare PA-only and PA + Strat.
- Store enough samples before promotion.
- Show false breakout, MFE/MAE, average R, and stop-out rate.
- Downgrade noisy rules instead of adding more complexity.

### P5: Advanced PA v1

Acceptance:

- Add only limited advanced PA rules after Paper + Journal exists.
- Every advanced PA rule must have ablation.
- Advanced PA can downgrade/watch/avoid before it can upgrade anything.

### P6: Capital Accumulation Mode

Acceptance:

- Account growth targets are based on realized results and risk budget.
- Goals cannot increase risk automatically.

### P7: Japan Daily Scanner

Acceptance:

- J-Quants daily data is ingested.
- JP symbols can be scored with Basic PA and Strat.
- US overnight/sector context is reflected.

### P8: Short Watchlist + Paper Short

Acceptance:

- System outputs short watchlist only.
- Paper short positions can be created and closed.
- Live short remains disabled.
- Short risk guard blocks or downgrades risky cases.

### P9: AI Reviewer

Acceptance:

- AI explains structured PA/Strat/risk outputs.
- AI highlights contradictions and missing evidence.
- AI cannot upgrade trade status or override risk.

### P10: Options Backlog

Acceptance:

- Options remain research-only.
- No live options workflow is enabled by default.

## 17. Deployment Readiness

Required before Railway staging:

- Reviewed `main` branch.
- Migrations pass on staging database.
- Auth0 SPA/API configured.
- Backend CORS configured for deployed frontend domain.
- Required secrets configured: `DATABASE_URL`, `POLYGON_API_KEY`, `INGESTION_ADMIN_TOKEN`, Auth0 values.
- Smoke test: `/health`, authenticated dashboard, candidates, positions, and exit alerts.

Required before public beta:

- Data Quality Gate v1.
- Basic application logs and error monitoring.
- Database backup policy.
- Staging/production environment split.
- Validation Lite dashboard.
- Clear in-app disclaimers.

Not required before staging:

- AWS migration.
- Options module.
- Short live support.
- Full Advanced PA.
- AI Reviewer.

## 18. Final v0.9 Rules

1. PA is core.
2. Strat is a trigger layer inside PA, not a standalone strategy.
3. Basic PA and Strat bar labeling are early production features.
4. Advanced PA v1 is allowed only after Paper / Journal exists.
5. Every advanced PA / Strat rule requires ablation.
6. The system remains long-biased by default.
7. Bearish signals first reduce long risk.
8. Short Watchlist is paper-only by default.
9. Live short requires a future validation gate.
10. Short options remain prohibited.
11. Options remain lowest priority.
12. No engine can increase risk without validation.
13. No pattern can override stop/risk/market regime.
14. If a new rule cannot be measured, it is research-only.
15. If unsure, do less.
