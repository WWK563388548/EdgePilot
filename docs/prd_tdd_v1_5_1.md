# EdgePilot PRD/TDD v1.5.1

This is the repo-maintained v1.5.1 PRD/TDD. It is the implementation-facing version of the latest full design document.

Full source archive: `docs/reference/EdgePilot_PRD_TDD_Implementation_Plan_v1_5_1_Pragmatic_Rollout_Proxy_Robustness.md`.

Release implementation plan: `docs/release_implementation_plan.md`.

## 1. Product Definition

EdgePilot is a manual trading operations cockpit for small-account trading, multi-asset expansion, and private-beta multi-user use.

It supports:

- Candidate generation.
- PA and strategy evidence explanation.
- Manual trade planning.
- Portfolio risk checks.
- Position lifecycle management.
- Exit alert monitoring.
- Journal recording.
- Scanner and trade outcome review.
- Automation job records.
- Future tenant-lite BYOK usage.
- Future proxy analytics and validation.

It does not place broker orders.

## 2. Current Implementation Mapping

Implemented:

- Auth0 account-scoped auth.
- Account risk settings.
- Candidates.
- PA facts / structures / setups.
- Strat signal foundation.
- Scanner outcomes.
- Candidate plan preview and creation.
- Position lifecycle.
- Portfolio risk monitor.
- Exit alerts.
- Notifications.
- Automation Job Runner.
- Trade journal creation.
- v1.5.1 source documentation archive.

Partial:

- Analytics, currently placeholder.
- Market context, currently basic.
- Realtime SSE, currently heartbeat-only.
- O'Neil-core ETF scanner, useful but should become satellite after ETF Rotation exists.

Not implemented:

- Tenant-lite.
- BYOK credential storage.
- Data Capability Matrix.
- Per-tenant rate limits.
- CSV execution import.
- Corporate action accounting.
- Backtest.
- Shadow Mode.
- Paper validation gates.
- MAX_20D warning.
- Proxy lifecycle.
- Proxy data quality.
- Decision Policy Engine.
- State combination test matrix.

## 3. Data Boundary

Target hierarchy:

```text
User
  -> Tenant
  -> Account / Workspace
  -> Candidates / Plans / Positions / Journal / Alerts
```

Current system mostly uses `account_id`.

v1.5.1 migration rule:

- Do not blindly rename `account_id` to `tenant_id`.
- Add `tenant_id` above `accounts`.
- Keep account-scoped business tables stable in the first tenant-lite PR.
- Add direct `tenant_id` to future private-user tables where required.

## 4. Required New Tables

### Tenant-Lite

```text
tenants
tenant_memberships
legal_acknowledgements
tenant_api_keys
tenant_job_states
tenant_data_capabilities
```

### Execution Import And Accounting

```text
execution_imports
execution_fills
dividend_events
corporate_action_events
```

### Validation

```text
test_runs
simulated_trades
rejected_signal_logs
signal_funnel_snapshots
go_live_gates
strategy_kill_switch_status
```

### Proxy Robustness

```text
proxy_lifecycle_status
proxy_data_quality_events
decision_policy_events
state_combination_test_cases
proxy_market_context_snapshots
```

## 5. Required API Areas

### Tenant-Lite

```http
GET  /api/tenants
POST /api/tenants
GET  /api/tenants/current
GET  /api/tenants/current/members
GET  /api/legal/acknowledgements
POST /api/legal/acknowledgements
GET  /api/data-credentials
POST /api/data-credentials
GET  /api/data-capabilities
```

### Execution Import

```http
POST /api/executions/imports
GET  /api/executions/imports
GET  /api/executions/fills
```

### Analytics

```http
GET /api/analytics/overview
GET /api/analytics/equity-curve
GET /api/analytics/r-distribution
GET /api/analytics/strategy-breakdown
GET /api/analytics/execution-quality
```

### Proxy Rollout

```http
GET   /api/proxies/lifecycle
PATCH /api/proxies/lifecycle/{proxy_id}
GET   /api/proxies/data-quality
GET   /api/decision-policy/events
POST  /api/decision-policy/evaluate
GET   /api/testing/state-combinations
POST  /api/testing/state-combinations/run
```

## 6. Frontend Areas

Existing workspace views stay:

- Overview.
- Candidates.
- PA Lab.
- Review.
- Positions.
- Exit Alerts.
- Automation.
- Notifications.
- Journal.
- Settings.

New views later:

- Workspace / Tenant settings.
- Data Credentials.
- Data Capability Matrix.
- Legal acknowledgement.
- Execution Import.
- Analytics.
- Backtest / Shadow / Paper.
- Proxy Rollout Lab.
- Decision Policy Trace.

## 7. Risk Rules

Keep current rules:

- Max risk per trade.
- Max total portfolio risk.
- Max active positions.
- Risk distance guard.
- Shadow-only paper limitation.
- Portfolio-after-plan guardrail.

Add next:

- Drawdown recovery mode.
- Consecutive-loss pause.
- Strategy kill switch.
- Data quality gate.
- Liquidity/execution risk gate.
- Decision policy trace for every candidate/position decision.

## 8. Position And Execution Workflow

Current:

```text
candidate
  -> plan preview
  -> planned position
  -> manual activation
  -> open / reduce / close
  -> journal
```

Next:

```text
broker or CSV execution file
  -> execution import
  -> fill normalization
  -> position reconciliation
  -> journal / analytics
```

Broker sync remains read-only and later. Automatic order placement remains out of scope.

## 9. Proxy Lifecycle

Each proxy must progress through stages:

```text
idea
data_available
analytics
shadow
paper
risk_modifier
production
```

No proxy may jump straight into production decisions.

## 10. Proxy Data Quality Rules

Each proxy input must record:

- Provider.
- Affected date.
- Latest input date.
- Status.
- Message.
- Details.

Statuses:

- `available`.
- `stale`.
- `missing`.
- `invalid`.
- `fallback_used`.
- `disabled`.

Rules:

- Missing non-core proxy does not crash scanner.
- Missing proxy data does not imply risk-on or risk-off.
- Proxy weight becomes zero when unavailable.
- Core price data failure can block production scanning.
- No NaN risk multipliers.
- No undefined decisions.

## 11. Decision Policy Engine

Modules should emit standardized modifiers:

```json
{
  "module": "breadth_proxy",
  "modifier_type": "risk",
  "severity": "warning",
  "risk_multiplier_delta": -0.25,
  "permission_delta": "disable_B_setup",
  "confidence": 0.65,
  "reason": "RSP/SPY weak and IWM/SPY weak"
}
```

The Decision Policy Engine combines modifiers in a stable priority order.

Only hard safety, core data quality failure, validation/live eligibility, account risk/drawdown, strategy kill switch, and hard liquidity/execution failure can veto.

## 12. State Combination Test Matrix

Required dimensions:

- Market regime.
- Data quality.
- Validation/live eligibility.
- PA grade.
- Breadth proxy.
- Credit proxy.
- Cashflow/drawdown state.
- Strategy kill switch.
- Liquidity.

Required tests:

- Hard safety veto always wins.
- Missing non-core proxy does not crash decision.
- Single proxy warning cannot reject A+ setup.
- B setup disabled only with enough confirmed warnings.
- Cashflow target reached reduces risk but does not upgrade setup.
- AI reviewer cannot override decision.
- Data failed blocks production trade.

## 13. Implementation Sequence

Expanded release roadmap: `docs/release_implementation_plan.md`.

### PR A: v1.5.1 Docs Alignment

Current docs PR.

### PR B: Tenant-Lite + Data Capability Foundation

- `tenants`.
- `tenant_memberships`.
- `accounts.tenant_id`.
- `AuthPrincipal.tenant_id`.
- BYOK credential table shell.
- Data Capability Matrix shell.
- Per-tenant job state shell.
- Basic legal acknowledgement.

### PR C: Service Split

- `PositionService`.
- `RiskService`.
- `NotificationService`.
- `JobRunService`.
- `JournalService`.

### PR D: CSV Execution Import + Analytics

- CSV import.
- Execution fills.
- Ledger-driven analytics.
- Execution quality basics.

### PR E: Backtest / Shadow / Paper

- Backtest run model.
- Shadow result storage.
- Paper validation gates.
- Rejected Signal Shadow.

### PR F: ETF Rotation + MAX_20D

- ETF Rotation foundation.
- MAX_20D analytics/warning.
- No hard reject until validation.

### PR G: Proxy Rollout Lab

- Proxy lifecycle status.
- Proxy data quality.
- Decision policy events.
- State combination tests.
- RSP/SPY analytics-only.

## 14. Rewrite Guidance

Do not rewrite current codebase.

Refactor gradually:

- Keep current account-scoped APIs stable.
- Add tenant-lite above account.
- Split services before adding more strategy modules.
- Replace analytics placeholder before milestone or proxy dashboards.
- Validate proxy modules before allowing them to affect decisions.

## 15. Verification Requirements

Every PR must keep:

```bash
.venv/bin/pytest backend/tests
.venv/bin/ruff check backend/app backend/tests migrations
cd frontend && npm run build
git diff --check
```

For docs archive updates, compare source and reference with:

```bash
cmp -s <downloaded-source.md> docs/reference/<same-file-name.md>
```
