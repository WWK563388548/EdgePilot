# EdgePilot PRD/TDD v1.1

This is the repo-maintained v1.1 PRD/TDD. It should be detailed enough to guide implementation without requiring every developer to read the full research archive.

Full source archive: `docs/reference/edgepilot_prd_tdd_v1_1_full.md`.

The full archive is the source of record for research context. This maintained document is the implementation-facing version.

## 1. Product Definition

EdgePilot is a manual trading operations cockpit for multi-asset, multi-user use.

It supports:

- Candidate generation.
- PA and strategy evidence explanation.
- Manual trade planning.
- Portfolio risk checks.
- Position lifecycle management.
- Exit alert monitoring.
- Journal recording.
- Scanner and trade outcome review.
- Dynamic milestone tracking.
- SaaS-ready tenant isolation.

It does not place broker orders.

## 2. Core User Stories

### Story 1: Daily Candidate Generation

As a trader, I want the system to generate a short list of actionable candidates so that I do not manually inspect hundreds of charts.

Output should include:

- Symbol.
- Market and asset type.
- Strategy source.
- Setup type.
- Entry trigger.
- Initial stop.
- Invalidated-if condition.
- Risk distance.
- Decision: candidate, watch, avoid, or research-only.
- Human-readable explanation.

### Story 2: Trade Plan Creation

As a trader, I want to turn a candidate into a plan only after the system checks risk and explains what I am allowed to do.

Output should include:

- Planned entry.
- Planned stop.
- Suggested quantity.
- Maximum allowed quantity.
- Single-trade risk.
- Portfolio-after-plan risk.
- Whether shadow-only validation blocks live treatment.
- Why the plan is allowed or blocked.

### Story 3: Position Lifecycle

As a trader, I want the system to track what happens after I manually enter a trade.

Supported states:

- `planned`.
- `open`.
- `reduce`.
- `closed`.
- `cancelled`.

Supported operations:

- Create plan.
- Cancel plan.
- Activate plan after manual entry.
- Adjust stop.
- Reduce quantity.
- Close position.
- Generate journal entry.

### Story 4: Exit Monitoring

As a trader, I want the system to notify me when a position needs action.

Exit alerts include:

- Hard stop.
- Breakeven after 1R.
- 2R trim.
- 20MA trailing after profit.
- Time stop.
- Failed breakout on heavy volume.
- Risk-off regime exit.

### Story 5: Scanner Review

As a system builder, I want to evaluate whether scanner results worked after future bars arrived.

Review metrics include:

- Triggered entry.
- Hit initial stop.
- False breakout.
- 5D, 20D, 60D forward returns.
- MFE.
- MAE.
- Missing reference bars.
- Insufficient future bars.

### Story 6: Dynamic Milestones

As a small-account trader, I want the system to tell me what stage the account is in and whether I should scale, pause, or recover.

The system should track:

- Equity.
- Deposits.
- Trading P/L.
- Contribution-adjusted return.
- TWR.
- MWR.
- Drawdown.
- Consecutive losses.
- Current milestone.
- Next milestone.
- Recovery mode.

### Story 7: Multi-User SaaS

As a SaaS user, I need my account, market data credentials, plans, positions, journals, and alerts isolated from other tenants.

The system must support:

- Tenant.
- Membership.
- Role.
- Legal acknowledgement.
- Audit log.
- BYO data credentials.
- Support access grant.

## 3. Non-Goals

The system does not target:

- Automatic trading.
- Broker order placement.
- Managed accounts.
- Copy trading.
- Signal selling.
- Personalized investment advice.
- Licensed market data redistribution without entitlement.
- High-frequency trading.
- Naked options.
- Short options.
- 0DTE production trading.
- AI macro/news prediction.
- Guaranteed profitability.

## 4. Architecture

### 4.1 Logical Layers

```text
Frontend Workspace
  -> API Routes
  -> Domain Services
  -> Database Models
  -> Market Data / Auth / Notification Adapters
```

### 4.2 Trading Workflow

```text
Market Data
  -> Data Quality Gate
  -> ETF Trend / Rotation
  -> Basic PA
  -> Strat Trigger Layer
  -> Risk Engine
  -> Candidate
  -> Plan Preview
  -> Manual Plan
  -> Manual Position
  -> Exit Engine
  -> Journal
  -> Analytics / Calibration
```

### 4.3 SaaS Boundary

```text
User
  -> Tenant
  -> Account / Workspace
  -> Candidates
  -> Positions
  -> Alerts
  -> Journal
  -> Analytics
```

Current implementation mostly uses `account_id`. v1.1 should introduce `tenant_id` above `account_id` and migrate gradually.

## 5. Data Model

### 5.1 Existing Important Tables

Already present or partially present:

- `users`.
- `accounts`.
- `account_memberships`.
- `account_risk_settings`.
- `audit_logs`.
- `symbols`.
- `bars`.
- `options_chain_snapshots`.
- `market_context_snapshots`.
- `candidates`.
- `pa_facts`.
- `pa_structures`.
- `pa_setups`.
- `strat_signals`.
- `scanner_outcomes`.
- `pa_calibration_stats`.
- `positions`.
- `exit_alerts`.
- `notification_preferences`.
- `notification_events`.
- `notification_delivery_logs`.
- `trades_journal`.
- `portfolio_snapshots`.
- `analytics_daily`.
- `data_freshness`.
- `ingestion_runs`.
- `job_runs`.

### 5.2 Required v1.1 Tables

Tenant and SaaS:

- `tenants`.
- `tenant_memberships`.
- `invitations`.
- `legal_acknowledgements`.
- `api_credentials`.
- `support_access_grants`.
- `subscriptions`.
- `usage_events`.

Milestones and analytics:

- `goal_ladders`.
- `goal_milestones`.
- `milestone_reviews`.
- `account_cashflows`.
- `equity_snapshots`.

Validation and safety:

- `data_quality_checks`.
- `signal_funnel_snapshots`.
- `test_runs`.
- `simulated_trades`.
- `go_live_gates`.
- `manual_overrides`.
- `strategy_kill_switch_status`.

Future strategy modules:

- `etf_rotation_scores`.
- `market_breadth_snapshots`.
- `earnings_revision_events`.
- `earnings_drift_scores`.
- `bearish_context_scores`.
- `paper_short_plans`.

### 5.3 Tenant Migration Rule

Do not blindly rename `account_id` to `tenant_id`.

Target relationship:

```text
tenants.tenant_id
  -> accounts.tenant_id
  -> candidates.account_id
  -> positions.account_id
  -> journal.account_id
```

Phase 1 can keep user-owned tables account-scoped while adding tenant ownership to accounts. Later phases can add direct `tenant_id` columns to hot or compliance-sensitive tables if needed.

## 6. Backend Services

### 6.1 Current Services To Keep

- Auth service.
- Scanner service.
- PA service.
- Strat service.
- Scanner outcome service.
- Business route contracts.

### 6.2 Services To Split

The large business service should be split into:

- `RiskService`.
- `PositionService`.
- `ExitAlertService`.
- `NotificationService`.
- `JobRunService`.
- `JournalService`.
- `MilestoneService`.
- `TenantService`.

The split should preserve API behavior and focus tests around each service.

## 7. API Design

### 7.1 Existing API Areas

Keep:

- `/api/auth/me`.
- `/api/dashboard/summary`.
- `/api/settings/risk`.
- `/api/settings/notifications`.
- `/api/candidates`.
- `/api/candidates/{candidate_id}`.
- `/api/candidates/{candidate_id}/plan-preview`.
- `/api/candidates/{candidate_id}/plan`.
- `/api/candidates/outcomes`.
- `/api/pa/*`.
- `/api/positions`.
- `/api/positions/{position_id}/activate`.
- `/api/positions/{position_id}/stop`.
- `/api/positions/{position_id}/reduce`.
- `/api/positions/{position_id}/close`.
- `/api/positions/{position_id}/cancel`.
- `/api/exit-alerts`.
- `/api/notifications`.
- `/api/jobs/automation/run`.
- `/api/jobs/runs`.
- `/api/journal/trades`.
- `/api/realtime/events/stream`.

### 7.2 Required v1.1 API Areas

Auth and tenant:

- `GET /api/tenants`.
- `POST /api/tenants`.
- `GET /api/tenants/{tenant_id}`.
- `PATCH /api/tenants/{tenant_id}`.
- `GET /api/tenants/{tenant_id}/members`.
- `POST /api/tenants/{tenant_id}/invitations`.
- `PATCH /api/tenant-memberships/{membership_id}`.

Legal and credentials:

- `GET /api/legal/acknowledgements`.
- `POST /api/legal/acknowledgements`.
- `GET /api/data-credentials`.
- `POST /api/data-credentials`.
- `PATCH /api/data-credentials/{credential_id}`.
- `DELETE /api/data-credentials/{credential_id}`.

Milestones:

- `GET /api/milestones/ladder`.
- `GET /api/milestones/current`.
- `POST /api/milestones/review`.

Analytics:

- `GET /api/analytics/overview`.
- `GET /api/analytics/equity-curve`.
- `GET /api/analytics/r-distribution`.
- `GET /api/analytics/strategy-breakdown`.
- `GET /api/analytics/signal-funnel`.
- `GET /api/analytics/mfe-mae`.

Safety:

- `GET /api/data-quality`.
- `POST /api/data-quality/run`.
- `GET /api/strategy-kill-switches`.
- `PATCH /api/strategy-kill-switches/{strategy_name}`.

## 8. Frontend Design

### 8.1 Existing Views To Keep

- Overview.
- Candidates.
- PA Lab.
- Review.
- Positions.
- Exit Alerts.
- Automation.
- Notifications modal.
- Journal.
- Settings.

### 8.2 Required v1.1 Views

- Tenant switcher.
- Onboarding.
- Legal acknowledgement screen.
- Team members.
- Invitations.
- Data source settings.
- Audit log.
- Support access grant.
- Milestone dashboard.
- Analytics dashboard.
- Data Quality dashboard.
- Strategy kill switch panel.
- ETF Rotation dashboard.

### 8.3 UX Rules

- The app should feel like a trading operations cockpit, not a marketing page.
- Keep dashboards dense but readable.
- Every risky action must explain why it is allowed or blocked.
- Human-readable explanations must sit beside raw metrics.
- Candidate pages should distinguish `candidate`, `watch`, `avoid`, and `research-only`.
- Strat UI must make clear that Strat is a trigger/reference layer, not a standalone order instruction.
- Notifications should be visible but not mixed into primary navigation.

## 9. Risk Rules

### 9.1 Existing Risk Rules

- Max account risk.
- Max risk per trade.
- Max open positions.
- Risk distance check.
- Shadow-only plan limitation.
- Portfolio-after-plan guardrail.

### 9.2 Required v1.1 Risk Rules

- If drawdown >= 5%, reduce risk per trade by half.
- If drawdown >= 10%, disable live trading and enter paper/review mode.
- If consecutive losses >= 3, block new live trades.
- Correlation guard blocks excessive same-theme exposure.
- Data Quality Gate blocks stale or suspicious data.
- Strategy Kill Switch disables engines that fail validation.

## 10. Exit Engine

Existing v0.2 rules:

- Hard stop.
- Breakeven after 1R.
- 2R trim.
- 20MA trailing after profit.
- Time stop.
- Failed breakout on heavy volume.
- Risk-off regime exit.

Required next rules:

- Action checklist for each alert.
- Alert-to-journal linkage.
- Post-alert outcome measurement.
- User override audit.

## 11. ETF Trend / Rotation Engine

ETF Rotation is the first production alpha line in v1.1.

Inputs:

- ETF daily bars.
- Relative strength.
- Moving average trend.
- Market breadth.
- Volume/liquidity.
- Sector/theme grouping.
- Risk regime.

Outputs:

- Rotation rank.
- Trend state.
- Risk-adjusted score.
- Candidate/watch/avoid decision.
- Human explanation.
- Signal funnel snapshot.

O'Neil-core can remain as a satellite score but should not be the core production engine after ETF Rotation lands.

## 12. PA And Strat

### 12.1 PA Role

PA answers:

- Is there structure?
- Where is the valid entry zone?
- Where is invalidation?
- Is risk controllable?
- Is the setup extended, early, or mature?

### 12.2 Strat Role

Strat answers:

- What is the objective bar state?
- Is there a possible trigger?
- Does the trigger align with PA?
- Is the trigger blocked by no-chase rules?

Strat must not:

- Create a standalone trade.
- Override PA.
- Override stops.
- Override risk.

### 12.3 Anti-Overfitting Constraints

- Keep the first pattern set small.
- Compare against simpler baselines.
- Use ablation before promotion.
- Track false breakouts and missing follow-through.
- Do not add rules just because one recent chart looks convincing.

## 13. Dynamic Milestone System

### 13.1 Default Milestones

| Level | Equity Range | Objective |
| --- | --- | --- |
| 1 | $2k-$10k | Survival and validation |
| 2 | $10k-$25k | Small account growth |
| 3 | $25k-$50k | Controlled scaling |
| 4 | $50k-$100k | First $100K push |
| 5 | $100k-$250k | Post-100K growth |
| 6 | $250k-$500k | Cashflow pilot |
| 7 | $500k-$1M | Cashflow and preservation |
| 8 | $1M+ | FIRE support and preservation |

### 13.2 Required Calculations

- Current equity.
- Net deposits.
- Trading P/L.
- Contribution-adjusted return.
- TWR.
- MWR.
- Current drawdown.
- Max drawdown.
- Consecutive losses.
- Risk mode.
- Next milestone gap.

### 13.3 Withdrawal Rule

Before first $100K, default behavior is no regular withdrawal. Exceptions:

- Taxes.
- Fees.
- Emergency.
- Explicit manual override.

## 14. Validation Plan

### Stage 0: Data Quality

Before backtest, paper, or live workflow:

- Check missing bars.
- Check duplicate bars.
- Check timestamp order.
- Check stale symbols.
- Check corporate-action adjustment assumptions.
- Check split/dividend anomalies where available.

### Stage 1: Historical ETF Backtest

Run ETF-only historical backtests over multiple regimes.

Track:

- Signal count.
- Trigger rate.
- Stop rate.
- False breakout rate.
- Average R.
- Profit factor.
- MFE.
- MAE.
- Max drawdown.

### Stage 2: Shadow Mode

Run without live trades.

Requirements:

- 4-8 weeks.
- 30-50 triggers if market permits.
- Record simulated entry, stop, exit, final R, MFE, MAE, and rule violations.

### Stage 3: Paper Trading

Requirements:

- 1-3 months.
- 50 paper trades if market permits.
- Rule adherence > 95%.
- Profit factor > 1.20 before micro live consideration.

### Stage 4: Micro Live

Requirements:

- ETF/large-cap only.
- Tiny fixed risk.
- No live options.
- No live short.
- Manual confirmation only.

## 15. Notification And Realtime

Current notifications are in-app. Email/SMS preference fields can exist before delivery providers are connected, but the UI must not imply external delivery is active until it is.

SSE should be used before WebSocket unless two-way realtime control becomes necessary.

Target SSE events:

- Job started.
- Job succeeded.
- Job failed.
- Scanner candidates updated.
- Exit alert created.
- Notification created.
- Data quality failed.
- Strategy disabled.

## 16. Deployment

Railway staging remains the near-term target.

Required before staging:

- Reviewed `main`.
- Migrations pass.
- Auth0 configured.
- CORS configured.
- Required secrets configured.
- `/health` smoke test.
- Authenticated dashboard smoke test.
- Candidates smoke test.
- Positions smoke test.
- Exit alerts smoke test.

Required before external beta:

- Tenant isolation.
- Legal acknowledgement.
- Data credential boundary.
- Backups.
- Error monitoring.
- Audit log.
- Data Quality Gate.
- Clear non-advice disclaimers.

AWS can wait until the product has enough operational load or compliance need to justify it.

## 17. Implementation Sequence

### Current PR

- Position lifecycle UX and operations.
- Automation Job Runner.
- v1.1 docs alignment.

### Next PR

- Tenant foundation.
- Legal acknowledgement schema.
- BYO data credential shell.
- Auth principal tenant awareness.

### Follow-Up PR

- Service split.
- Real analytics foundation.
- Milestone dashboard.

### Then

- ETF Trend / Rotation Engine.
- Data Quality Gate.
- Strategy Kill Switch.
- SSE event fanout.

## 18. Documentation Rules

- Current strategy: `docs/product_strategy_v1_1.md`.
- Current implementation PRD/TDD: `docs/prd_tdd_v1_1.md`.
- Full source archive: `docs/reference/edgepilot_prd_tdd_v1_1_full.md`.
- Do not reintroduce standalone older-version docs unless there is an explicit migration reason.
