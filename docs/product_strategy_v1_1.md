# EdgePilot Product Strategy v1.1

This is the current authoritative product direction for EdgePilot.

Full source archive: `docs/reference/edgepilot_prd_tdd_v1_1_full.md`.

Superseded v0.9 documents are retained under `docs/reference/` only for traceability.

## One-Line Definition

EdgePilot is a multi-asset, multi-user manual trading operations cockpit. It helps users screen candidates, create trade plans, manage position risk, monitor exits, review outcomes, and compound a small trading account toward milestone goals. It does not place broker orders and must not operate as investment advice, copy trading, managed accounts, or signal selling.

## Current Strategic Direction

EdgePilot is moving from a single-account trading cockpit into a SaaS-ready trading account operating system.

Core principles:

- Manual confirmation only. No broker order execution.
- Protect capital before seeking return.
- Risk Engine, Position Ledger, and Exit Engine are the core production foundation.
- ETF Trend / Rotation is the first production alpha line.
- Earnings Drift / Revision is the second production alpha line.
- Growth Leader / O'Neil is an upside satellite, not the core engine.
- PA and Strat are execution and structure layers, not standalone trading systems.
- Bearish / short logic starts as defensive context and paper research.
- Options remain the lowest-priority research backlog.
- AI can explain, challenge, and review. It cannot upgrade a trade, override risk, or increase size.
- Multi-user support requires tenant isolation, auditability, data authorization, legal acknowledgements, and role-based permissions.

## v1.1 Priority Order

### P0: Risk, Position, Exit

Production foundation.

- Account risk settings.
- Position lifecycle.
- Portfolio risk monitor.
- Exit alert engine.
- Drawdown recovery rules.
- Strategy kill switch.
- Correlation guard.
- Data quality gate.

Current status: partially implemented.

### P1: Auth, Personal Tenant, Journal, Analytics, Paper, Milestones

User and account operating layer.

- Auth MVP.
- Personal tenant and tenant membership.
- Legal acknowledgement.
- Journal and real performance analytics.
- Paper trading validation.
- Trading account milestone dashboard.
- Contribution-adjusted return, TWR, MWR, drawdown, and recovery state.

Current status: Auth0/account-scoped MVP exists. Tenant model, milestones, and real analytics are not implemented.

### P2: ETF Trend / Rotation Engine

First production alpha line.

- ETF universe and market breadth.
- Trend and rotation scoring.
- Risk-adjusted ETF candidate generation.
- Rotation diagnostics and signal funnel.

Current status: not yet implemented as a distinct engine. Existing US ETF O'Neil-core scanner can be reused as data/scanner foundation.

### P3: Basic PA + Strat Trigger

Execution layer.

- Basic PA structure.
- Strat bar labels and small trigger set.
- No standalone Strat trades.
- No-chase and invalidation guards.
- Multi-timeframe support later.

Current status: partially implemented.

### P4: Tenant Isolation + BYO Data Credentials

SaaS compliance and platform safety layer.

- Tenants and tenant memberships.
- Role-based access.
- BYO market data credentials unless redistribution rights are licensed.
- Audit logs.
- Support access grants.

Current status: not implemented beyond account-scoped Auth0 access.

### P5 and Later

- Earnings Drift / Revision.
- PA / Strat calibration and ablation.
- Growth Leader / O'Neil expansion.
- Team RBAC and audit console.
- Bearish context and paper short.
- Japan expansion.
- AI reviewer.
- Options research backlog.

## Implementation Stance

Current implementation should not be rewritten from scratch.

Keep and extend:

- PA facts, structures, setups, and scanner outcomes.
- Candidate, plan, position, risk, exit alert, notification, and job run foundations.
- Auth0 MVP and account scoping while tenant support is introduced.
- Next.js workspace, i18n, and component split.

Refactor before adding larger v1.1 modules:

- Introduce tenant model above account/workspace.
- Split the large business service by domain.
- Replace placeholder analytics with ledger-driven metrics.
- Expand realtime SSE beyond heartbeat.
- Move current O'Neil ETF scanner into satellite status after ETF Rotation exists.

## Deployment Position

Railway remains the recommended first staging/internal beta path. AWS should wait until multi-user tenant boundaries, backup policy, monitoring, and data credential handling are stable enough to justify the operational overhead.
