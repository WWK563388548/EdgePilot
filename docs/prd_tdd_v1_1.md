# EdgePilot PRD/TDD v1.1

This is the repo-maintained v1.1 PRD/TDD summary. The full research and design archive is stored at `docs/reference/edgepilot_prd_tdd_v1_1_full.md`.

Superseded v0.9 documents are kept under `docs/reference/` only for historical context.

## 1. Product Definition

EdgePilot is a manual trading operations cockpit for multi-asset, multi-user use.

It screens candidates, explains price-action and strategy context, creates trade plans, tracks positions, enforces portfolio risk, raises exit alerts, records journals, and helps users compound a trading account through dynamic milestones.

It does not place broker orders. Every entry, trim, stop, close, and cancel remains manually confirmed by the user.

## 2. Non-Goals

EdgePilot must not become:

- Automatic broker execution.
- Investment advice.
- Managed accounts.
- Copy trading.
- Signal selling.
- Data redistribution without proper licensing.
- High-frequency trading.
- Short-options or naked-options tooling.
- AI-driven trade authorization.

## 3. Core Data Boundary

v1.1 introduces a SaaS-ready boundary:

```text
User
  -> Tenant
  -> Account / Workspace
  -> Candidates / Plans / Positions / Journal / Alerts
```

Current implementation mostly uses `account_id` as the isolation boundary. v1.1 requires introducing `tenant_id` above `account_id` instead of blindly renaming account fields.

Market data can remain shared only when licensing permits. Otherwise, tenant/user-provided credentials and entitlement checks are required.

## 4. Production Decision Path

The live/paper decision path should stay minimal:

```text
Data Quality Gate
  -> ETF Trend / Rotation
  -> Basic PA
  -> Strat Trigger Layer
  -> Risk Engine
  -> Candidate / Plan
  -> Manual Position
  -> Exit Engine
  -> Journal
  -> Analytics / Calibration
```

O'Neil/Growth Leader remains an upside satellite after the ETF rotation foundation.

## 5. Current Implementation Mapping

Implemented or partially implemented:

- Auth0/OIDC account-scoped access.
- PostgreSQL/Timescale-ready schema and Alembic migrations.
- Market data ingestion foundation.
- PA facts, PA structures, PA setups, and PA Lab.
- Strat signal layer foundation.
- US ETF O'Neil-core scanner.
- Candidate detail, plan preview, and plan creation.
- Position lifecycle.
- Portfolio risk monitor.
- Exit Engine v0.2.
- Exit alerts and in-app notifications.
- Automation Job Runner.
- Scanner outcome review.
- Journal generation on close.
- Next.js workspace with zh/en/ja i18n.

Not yet implemented:

- Tenant model.
- Legal acknowledgement.
- BYO data credentials.
- Support access grants.
- Billing and usage events.
- Real analytics from position/journal ledger.
- Milestone dashboard and contribution-adjusted performance.
- ETF Trend / Rotation engine.
- Data Quality Gate.
- Strategy Kill Switch.
- Correlation Guard.
- Paper trading validation gates.
- Earnings Drift / Revision.
- Japan market expansion.
- AI reviewer.
- Options adapter beyond raw option-chain ingestion.

## 6. Near-Term Technical Plan

### PR 1: v1.1 Foundation Alignment

- Add `tenants`.
- Add `tenant_memberships`.
- Add `accounts.tenant_id`.
- Add `tenant_id` to auth principal.
- Preserve current Auth0 account flow as compatibility mode.
- Add legal acknowledgement schema.
- Add BYO data credential schema shell.
- Keep existing account-scoped business tables stable for this step.

### PR 2: Domain Service Split

- Split notification, job, risk, position, and journal logic out of the large business service.
- Keep route contracts stable.
- Add focused tests around each domain service.

### PR 3: Milestone + Real Analytics Foundation

- Add goal ladder and milestone tables.
- Add contribution/deposit tracking.
- Compute equity, trading P/L, contribution-adjusted return, TWR, MWR, drawdown, and recovery state.
- Add milestone dashboard UI.

### PR 4: ETF Trend / Rotation Engine

- Add ETF rotation scoring.
- Add market breadth and trend diagnostics.
- Make ETF Rotation the first production alpha engine.
- Keep O'Neil as satellite scoring.

### PR 5: Realtime and Background Jobs

- Move automation jobs toward background execution.
- Expand SSE from heartbeat to job, notification, candidate, and alert events.

## 7. Validation Plan

Before live use or public beta:

- Data Quality Gate v1.
- Signal funnel snapshots.
- Scanner outcome tracking.
- Paper trading validation.
- MFE/MAE analytics.
- Drawdown recovery rules.
- Manual override audit.
- Strategy kill switch.

## 8. Documentation Rules

- `docs/product_strategy_v1_1.md` is the current strategy summary.
- `docs/prd_tdd_v1_1.md` is the current maintained PRD/TDD summary.
- `docs/reference/edgepilot_prd_tdd_v1_1_full.md` is the full v1.1 source archive.
- v0.9 files under `docs/reference/` are superseded and should not drive new implementation.
