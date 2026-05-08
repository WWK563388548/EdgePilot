# EdgePilot Release Implementation Plan

This document is the implementation plan from the current main branch to the first private-beta release.

Authoritative strategy inputs:

- `docs/product_strategy_v1_5_1.md`
- `docs/prd_tdd_v1_5_1.md`
- `docs/reference/EdgePilot_PRD_TDD_Implementation_Plan_v1_5_1_Pragmatic_Rollout_Proxy_Robustness.md`

## 1. Release Definition

The first release is a private-beta manual trading operations cockpit.

It is not:

- A broker execution system.
- A commercial public SaaS.
- A signal-selling product.
- A copy-trading product.
- A portfolio management service.
- A multi-market all-at-once rollout.
- An options or live-short trading system.

The release is successful when a small number of users can:

1. Connect or provide their own market data credentials.
2. Run the US ETF / liquid large-cap workflow reliably.
3. Create and manage manual trade plans.
4. Import real executions from CSV.
5. Reconcile positions from actual fills.
6. Review real PnL, R-multiple, execution quality, and strategy outcomes.
7. Run backtest, shadow, and paper validation loops.
8. Understand why a candidate was accepted, downgraded, watched, or blocked.
9. Receive reliable in-app notifications and job status updates.
10. Use the system without confusing it for investment advice or automated trading.

## 2. Current Baseline

Already implemented or mostly implemented:

- Auth0/OIDC account-scoped auth.
- Tenant-lite foundation.
- BYOK-style Polygon credential storage path.
- Data capability and runtime health checks for Polygon US ETF daily data.
- PA facts, structures, setups, and PA Lab.
- Strat signal foundation and no-standalone-trade framing.
- US ETF O'Neil-core scanner.
- Candidate detail, chart evidence, explanation, scanner decision, and trade plan.
- Candidate plan preview and position creation.
- Position lifecycle: planned, open, reduce, closed, cancelled.
- Account risk settings and portfolio risk monitor.
- Exit Engine v0.2 and exit alerts.
- In-app notifications.
- Automation Job Runner.
- Trade journal creation on close.
- Next.js workspace with zh/en/ja i18n.

Known gaps before release:

- `BusinessService` is too large and should be split before more strategy modules are added.
- Planned/open positions are not yet driven by real execution fills.
- Analytics is not yet ledger-driven.
- Backtest, shadow, paper, and go-live gates are missing.
- Rejected Signal Shadow is missing, so guardrails cannot yet prove whether they are useful or overfit.
- ETF Rotation / Momentum Horizon is not yet the primary production line.
- Volatility Scaled Position Sizing is missing.
- MAX_20D is not yet available as an analytics/warning signal.
- Decision Policy Engine and decision traces are missing.
- Provider abstraction exists only implicitly through current Polygon code paths.
- Multi-market readiness is not yet implemented beyond early data capability concepts.

## 3. Non-Negotiable Rules Through Release

- Manual confirmation only.
- No automatic broker orders.
- No AI trade upgrades.
- No Strat-only trades.
- No options live workflow.
- No live short workflow.
- No risk increase from unvalidated research rules.
- No single proxy veto.
- Missing non-core proxy data must degrade the UI, not crash scanners.
- Core data failure can block production scans.
- All release-stage strategy rules need a traceable evidence path.

## 4. Strategy Conclusions From v1.5.1 Research

The research conclusions do not imply adding many more hard filters. They imply a stricter promotion process.

### 4.1 ETF Rotation Is The First Production Line

US ETF / liquid large-cap trend and rotation should become the first production strategy line because it is liquid, easier to validate, lower idiosyncratic risk, and a better small-account proving ground.

O'Neil / Growth Leader should become a satellite candidate source after ETF Rotation exists.

### 4.2 O'Neil Is Not The Final Buy Decision

O'Neil can identify strong leaders, but it should not decide final entry, position size, or exit.

Correct flow:

```text
O'Neil / Growth Leader says: worth watching.
PA / Strat says: objective trigger or no trigger.
Risk Engine says: can this account take it?
Exit Engine says: how to reduce, hold, or exit.
```

### 4.3 Strat Is A Trigger Layer

Strat remains useful as a precise trigger and timeframe-continuity label.

It cannot:

- Create a trade by itself.
- Increase risk.
- Override PA.
- Override risk.
- Override stop logic.

It can:

- Confirm a PA candidate.
- Delay entry until a trigger appears.
- Downgrade a stretched setup.
- Explain why a candidate is watch-only.

### 4.4 Volatility Scaling Comes Before More Aggressive Strategy Expansion

Volatility Scaled Position Sizing should reduce size in high-volatility conditions.

Initial MVP rule:

```text
ATR_pct = ATR(14) / close
vol_rank = ATR_pct percentile over 252 trading days

vol_rank > 80%      -> risk multiplier 0.50
vol_rank 60%-80%    -> risk multiplier 0.75
vol_rank 20%-60%    -> risk multiplier 1.00
vol_rank < 20%      -> risk multiplier 1.00
```

Low volatility must not automatically increase leverage or position size before validation.

### 4.5 Momentum Horizon Should Replace Simple Short-Term Chase Logic

ETF Rotation should distinguish medium-term momentum from short-term overextension.

Initial scoring direction:

- 3M momentum.
- 6M momentum.
- 12M momentum.
- Trend quality.
- Relative strength versus benchmark.
- 1M overextension penalty.

Output should include an entry mode:

- `breakout_allowed`
- `pullback_required`
- `retest_required`
- `watch_only`

### 4.6 VWAP Is Context-Specific

VWAP is useful for intraday entry and execution quality.

It should not become a universal hard veto for daily swing setups.

### 4.7 Exit Rules Need Profiles

The legacy universal +1R breakeven rule should not become the default production rule.

Exit Engine should move toward strategy-specific exit profiles:

- ETF / large-cap trend.
- Momentum leader.
- Short-term tactical.
- Future option-related, research-only.

### 4.8 MAX_20D Comes First Among Proxy/Anomaly Features

MAX_20D only needs single-symbol OHLCV, so it is the least fragile academic-anomaly feature.

It starts as analytics/warning only:

```text
Lottery Risk: Low / Medium / High
Suggested: Allow / Watch / Avoid
Production decision unchanged until validated
```

Promotion requires backtest, rejected-signal shadow, catalyst exceptions, parameter stability, and proof that it does not filter too many winners.

### 4.9 Breadth, Credit, Tail-Risk, And Calendar Proxies Stay Analytics-Only First

RSP/SPY, IWM/SPY, HYG/IEF, VIXY/SPY, turn-of-month tags, Monday effect, overnight drift, and FOMC tags start as analytics-only.

They must not directly veto production candidates in the first release.

## 5. Release Roadmap

### R0. Current PR Closeout

Goal: finish and merge the current data capability / proxy robustness work.

Exit criteria:

- Backend tests pass.
- Frontend build passes.
- Capability status reflects actual credential and runtime health.
- Transient provider failures do not permanently disable valid credentials.
- Current PR description and migration notes are accurate.

### R1. Service Split And Domain Foundation

Goal: split the large business service before adding more strategy and validation code.

Scope:

- Extract position lifecycle service.
- Extract portfolio risk service.
- Extract exit alert service.
- Extract notification/event helpers where appropriate.
- Extract scanner orchestration boundaries.
- Keep route contracts stable.
- Keep API responses unchanged.

Current PR foundation slice:

- Extract audit logging into `AuditService`.
- Extract account risk settings into `RiskSettingsService`.
- Extract portfolio risk summaries and preview risk items into `PortfolioRiskService`.
- Extract automation job run orchestration and job history queries into `JobRunService`.
- Extract notification preferences, event creation, delivery logs, and notification queries into `NotificationService`.
- Keep `BusinessService` as the compatibility facade for existing routes and tests while future slices move more domain logic out.

Out of scope:

- New strategy logic.
- New UI features.
- Database redesign.

Exit criteria:

- Existing backend tests pass.
- Existing frontend build passes.
- No response contract regressions.
- Future CSV, validation, strategy, and policy services have clear attachment points.

### R2. CSV Execution Import And Fill Ledger

Goal: make EdgePilot aware of real executions.

Scope:

- Add `execution_imports`.
- Add `execution_fills`.
- Add import status and error reporting.
- Support manual CSV upload/import for at least one broker export format.
- Normalize fills into a common internal schema.
- Match fills to existing planned positions when possible.
- Allow unmatched fills to create review-needed position records.
- Add idempotency keys so repeated CSV uploads do not duplicate fills.

Current branch foundation slice:

- Add execution import and execution fill ORM models, migration, schemas, and read APIs.
- Add generic CSV import request support without broker API sync.
- Normalize CSV rows into canonical execution fills.
- Match fills to account-scoped positions when a position ID or active symbol position exists.
- Create `review_needed` positions for unmatched fills.
- Apply basic long-position reconciliation for buy, partial sell, and close flows.
- Preserve idempotency so repeated imports skip existing fills.
- Mark `execution_import.csv` as available for tenant capability checks.

Out of scope:

- Direct broker API sync.
- Order placement.
- Multi-broker parser matrix.

Exit criteria:

- Same CSV can be imported twice without duplicate fills.
- Buy, sell, partial sell, and close flows are represented.
- Position quantity and average cost can be reconciled from fills.
- Import errors are visible and actionable.
- Tests cover malformed rows, duplicates, partial fills, and account scoping.

### R3. Real Analytics And Execution Quality

Goal: replace placeholder analytics with ledger-driven analytics.

Scope:

- Calculate realized PnL from fills.
- Calculate open unrealized PnL from latest available bars.
- Calculate R-multiple from actual entry, stop, and exit.
- Track planned versus actual entry.
- Track planned versus actual exit.
- Track execution drag in R.
- Add strategy, setup, and symbol breakdowns.
- Add basic equity curve from imported execution history.

Out of scope:

- Full tax accounting.
- Full broker reconciliation.
- Options analytics.

Exit criteria:

- Analytics no longer relies on placeholder numbers.
- Closed trades show real R and PnL.
- Execution quality can show whether manual delay hurt or helped.
- Strategy breakdown can identify which setup groups are worth more validation.

### R4. Dividend And Corporate Action Accounting

Goal: avoid false PnL and false chart/strategy conclusions from splits, dividends, and symbol events.

Scope:

- Add `dividend_events`.
- Add `corporate_action_events`.
- Record split adjustment mode.
- Make analytics distinguish trading PnL from dividends and other cash events.
- Store enough metadata to audit historical changes.

Out of scope:

- Complete tax reporting.
- Every global-market corporate-action edge case.

Exit criteria:

- Split-adjusted price data does not corrupt execution-derived PnL.
- Dividends are not treated as strategy alpha.
- Analytics can separate trading return and cash events.

### R5. Validation Engine Foundation

Goal: make strategy promotion measurable.

Scope:

- Add `test_runs`.
- Add `simulated_trades`.
- Add `signal_funnel_snapshots`.
- Add `go_live_gates`.
- Add `strategy_kill_switch_status`.
- Add stage labels: data_quality, backtest, shadow, paper, micro_live_allowed.
- Add minimum evidence checks before a strategy can be treated as production-ready.

Out of scope:

- Complex walk-forward optimization.
- Options backtesting.
- Live short validation.

Exit criteria:

- A strategy can be marked research, shadow, paper, or production-eligible.
- Go-live gate can explain why a strategy is blocked.
- Strategy kill switch can pause new live plans without deleting history.
- Tests cover blocked, shadow-only, paper-only, and production-eligible states.

### R6. Rejected Signal Shadow And Guardrail Evaluation

Goal: prevent anti-overfitting rules from becoming overfit filters.

Scope:

- Add `rejected_signal_logs`.
- Record rejected candidates with hypothetical entry, stop, and rejection reason.
- Later calculate future MFE, MAE, and hypothetical R.
- Track guards such as no-chase, overextension, data-quality, and MAX_20D warning.
- Expose rejected-signal summary in a validation or analytics view.

Out of scope:

- Automatically removing guards.
- Optimizing guard parameters.

Exit criteria:

- Every material candidate rejection has a traceable reason.
- Rejected signal performance can be compared against accepted candidates.
- Guardrails can be reviewed before becoming hard production rules.

### R7. ETF Rotation And Momentum Horizon

Goal: build the primary strategy line described in v1.5.1.

Scope:

- Add ETF rotation scoring.
- Calculate 3M, 6M, and 12M momentum.
- Add 1M overextension penalty.
- Add trend and relative-strength components.
- Output entry mode: breakout_allowed, pullback_required, retest_required, watch_only.
- Keep O'Neil scanner as a satellite source.

Out of scope:

- Full all-stock universe.
- Earnings drift.
- Japan strategy expansion.

Exit criteria:

- ETF Rotation candidates can be generated separately from O'Neil.
- Candidate detail explains momentum horizon and entry mode.
- Rotation output integrates with PA, Strat, Risk, and Exit plans.
- Backtest/shadow hooks exist for rotation results.

### R8. Volatility Scaled Position Sizing And Exit Profiles

Goal: make sizing and exits strategy-aware without increasing risk.

Scope:

- Add ATR_pct and vol_rank features.
- Apply volatility multiplier to plan sizing.
- Never increase position size from low volatility in the first release.
- Add exit profile field to positions.
- Support ETF / large-cap trend exit profile.
- Support momentum leader exit profile.
- Treat +1R as a review point, not universal automatic breakeven.

Out of scope:

- Options exit profile.
- Live short exit profile.

Exit criteria:

- Plan preview shows base size and volatility-adjusted size.
- High-volatility candidates have reduced allowed size.
- Exit alerts can explain which profile produced the recommendation.
- Existing hard stop behavior remains intact.

### R9. MAX_20D Analytics / Warning

Goal: add the first academic anomaly feature without turning it into an unvalidated veto.

Scope:

- Calculate MAX_20D from daily bars.
- Store or expose lottery risk level.
- Show warning in candidate detail.
- Include suggested allow/watch/avoid language.
- Record whether MAX_20D influenced a decision policy event.

Out of scope:

- Hard reject based solely on MAX_20D.
- Small-cap meme-stock full classifier.
- Catalyst data integration.

Exit criteria:

- MAX_20D appears in scanner evidence.
- It can warn or downgrade only through policy rules.
- It is included in rejected-signal shadow if it blocks or downgrades.

### R10. Decision Policy Engine Skeleton

Goal: move decision logic from scattered conditions into a traceable policy layer.

Scope:

- Add `decision_policy_events`.
- Define modifier input format.
- Define priority order:
  - hard safety
  - core data quality
  - validation eligibility
  - account risk / drawdown
  - strategy kill switch
  - liquidity / execution
  - market regime
  - proxy / anomaly warnings
  - PA / Strat
  - explanation-only layers
- Record final decision, risk multiplier, veto source, and explanation.
- Show decision trace in candidate detail.

Out of scope:

- Complex policy UI editor.
- User-defined arbitrary rules.

Exit criteria:

- Candidate decisions have a policy trace.
- Risk veto and watch-only downgrade are distinguishable.
- AI/explanation layers cannot upgrade decisions.
- Tests cover conflicting modifier combinations.

### R11. Proxy Data Quality And Analytics-Only Proxies

Goal: support market proxy research without fragile production dependencies.

Scope:

- Add `proxy_lifecycle_status`.
- Add `proxy_data_quality_events`.
- Add proxy freshness checks.
- Add RSP/SPY analytics-only dashboard.
- Add IWM/SPY analytics-only if data is stable.
- Keep HYG/IEF deferred until incremental value is proven.

Out of scope:

- Proxy hard veto.
- Proxy risk multiplier integration.
- Paid alternative data.

Exit criteria:

- Missing non-core proxy data is visible but does not crash.
- RSP/SPY can be observed historically and live.
- Proxy lifecycle shows analytics-only status.
- Single proxy cannot veto by design.

### R12. Provider Adapter Interface

Goal: stop hard-coding Polygon-specific assumptions before multi-market work begins.

Scope:

- Define provider adapter contracts:
  - daily bars
  - intraday bars, optional
  - symbol metadata
  - corporate actions, optional
  - capability resolution
  - freshness validation
  - rate limit hints
- Implement Polygon adapter behind the interface.
- Keep existing Polygon behavior stable.
- Make scanner and PA code call provider-neutral interfaces where practical.

Out of scope:

- JP/HK/A-share/crypto scanners.
- Multiple live providers at once.
- Full broker adapter.

Exit criteria:

- Existing Polygon workflows still pass.
- New providers can be added without rewriting scanner logic.
- Capability errors are provider-neutral.
- Tests cover provider success, missing capability, stale data, and transient failure.

## 6. When Provider Adapter And Multi-Market Readiness Happen

Provider Adapter should happen before the first private-beta release, but after the ledger and validation foundations are underway.

Reason:

- Doing it too early risks abstracting the wrong things.
- Doing it too late makes every scanner and strategy too Polygon-specific.

Recommended timing:

```text
Service split
  -> CSV import / ledger
  -> Validation foundation
  -> ETF Rotation / volatility sizing
  -> Provider Adapter Interface
  -> Multi-Market Readiness
```

Multi-Market Readiness is not the same as launching every market.

It means the system can represent:

- Provider identity.
- Market calendar.
- Trading timezone.
- Currency.
- Asset type.
- Exchange / venue.
- Tick size.
- Lot size.
- Adjusted price mode.
- Corporate-action mode.
- Session boundaries.
- Data freshness rules.

First market expansion after release should be JP daily, not JP + HK + A-share + crypto all at once.

## 7. Multi-Market Readiness Stage

Goal: prepare the domain model for JP daily expansion without expanding strategy scope too quickly.

Scope:

- Add market calendar abstraction.
- Add timezone-aware scan date handling.
- Add currency fields where missing.
- Add exchange / venue metadata.
- Add lot size and tick size metadata.
- Add adjusted-price mode metadata.
- Make provider capabilities market-aware.
- Document JP daily data requirements for J-Quants.

Out of scope:

- JP live trading.
- JP intraday/tick.
- HK, A-share, crypto, options, futures.
- Cross-market strategy optimization.

Exit criteria:

- US ETF workflows remain unchanged.
- JP daily symbols and bars can be represented without schema hacks.
- Strategy eligibility can say `data_available` without pretending production readiness.

## 8. Release Hardening

Goal: prepare the private beta release.

Scope:

- Migration dry-run on local and staging data.
- Seed/reset scripts documented.
- Error states in UI are understandable.
- Notification center and job status are reliable.
- Legal acknowledgement flow exists or is clearly gated.
- Data credential setup and capability status are documented.
- Railway deployment path is verified.
- Backup and restore notes exist.
- Release notes and known limitations are written.

Exit criteria:

- Backend full test suite passes.
- Frontend production build passes.
- `git diff --check` passes.
- Alembic upgrade from baseline to head succeeds.
- A fresh database can be initialized and scanned.
- Existing local data can be migrated or explicitly reset with documented steps.
- User can complete a representative manual workflow:
  - configure data source
  - refresh market data
  - run scanner
  - inspect candidate
  - create plan
  - mark entry manually
  - evaluate exit alerts
  - import execution CSV
  - review analytics

## 9. Release Gate Checklist

### Product Gate

- The UI states clearly that EdgePilot is a manual trading operations tool.
- No page implies guaranteed profit or auto trading.
- Candidate pages explain watch/candidate/blocked decisions.
- Risk blocks are understandable to a non-expert user.
- Strategy validation status is visible.

### Data Gate

- Polygon capability can be available, missing, stale, invalid, or fallback_used.
- Runtime failures do not silently become healthy.
- Non-core proxy failures degrade gracefully.
- Core market data failure blocks production scans.

### Trading Workflow Gate

- Candidate to plan works.
- Plan to open works.
- Planned position can be cancelled.
- Open position can be reduced and closed.
- Exit alerts can be acknowledged or snoozed.
- CSV import can reconcile real fills.

### Strategy Gate

- O'Neil remains satellite once ETF Rotation exists.
- ETF Rotation has validation hooks.
- Strat cannot create trades alone.
- MAX_20D starts as warning.
- Volatility scaling cannot increase risk.
- Decision policy traces candidate outcomes.

### Validation Gate

- Backtest, shadow, and paper states exist.
- Rejected signals are recorded.
- Strategy kill switch can pause new plans.
- Go-live gates can block unvalidated strategies.

### Engineering Gate

- Domain services are split enough to keep strategy additions isolated.
- Provider adapter interface exists.
- New market providers can be added without rewriting scanners.
- Tests cover capability, policy, CSV, validation, and core business flows.

## 10. Suggested PR Sequence

1. `feat/service-split-domain-foundation`
2. `feat/execution-csv-import-ledger`
3. `feat/ledger-analytics-execution-quality`
4. `feat/validation-engine-foundation`
5. `feat/rejected-signal-shadow`
6. `feat/etf-rotation-momentum-horizon`
7. `feat/volatility-sizing-exit-profiles`
8. `feat/max20d-warning`
9. `feat/decision-policy-trace`
10. `feat/proxy-data-quality-analytics`
11. `feat/provider-adapter-interface`
12. `feat/multi-market-readiness-jp-daily-foundation`
13. `feat/private-beta-release-hardening`

Small fixes and review comments should remain separate when they block merge safety.

## 11. Explicitly Deferred Until After First Release

- Live short.
- Short options.
- Options strategy scanner.
- 0DTE.
- Broker order placement.
- Semi-automated conditional order placement.
- Commercial SaaS billing.
- Full RBAC/team administration.
- HK/A-share/crypto production scanners.
- Paid alternative data integrations.
- GEX, true skew, borrow fee, insider/buyback, and advanced options analytics.

## 12. Final Principle

The first release should prove that EdgePilot can run a reliable manual trading loop and measure whether it works.

The correct order is:

```text
Real executions
  -> real analytics
  -> validation
  -> strategy promotion
  -> provider abstraction
  -> cautious multi-market expansion
```

This keeps the system aligned with the v1.5.1 principle:

> Robust before sophisticated.
