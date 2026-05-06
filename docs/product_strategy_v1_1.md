# EdgePilot Product Strategy v1.1

This is the current authoritative product strategy for EdgePilot.

Full source archive: `docs/reference/EdgePilot_PRD_TDD_Implementation_Plan_v1_1_Multi_User_SaaS_Auth_Dynamic_Milestones.md`.

The full archive is intentionally retained because it includes the original v1.1 PRD/TDD text and historical context from earlier drafts. Separate v0.9 documents have been removed to avoid conflicting product direction.

## 1. Product Positioning

EdgePilot is a multi-asset, multi-user manual trading operations cockpit.

It helps a user:

- Screen trade candidates.
- Understand price-action and strategy evidence.
- Create a manual trade plan.
- Size risk before entry.
- Track planned and open positions.
- Monitor exit conditions.
- Record journal outcomes.
- Review whether the system is actually working.
- Compound a small trading account through dynamic milestones.

EdgePilot does not place broker orders. Every entry, trim, stop, close, and cancel is manually confirmed by the user outside the system.

## 2. Strategic Repositioning In v1.1

v1.1 moves EdgePilot from a single-user trading cockpit toward a SaaS-ready trading account operating system.

The important priority reset is:

```text
Risk / Position / Exit foundation
  -> Auth / Tenant / Legal / Data authorization
  -> Journal / Analytics / Paper validation
  -> Milestone dashboard
  -> ETF Trend / Rotation
  -> Basic PA + Strat trigger
  -> Earnings Drift / Revision
  -> Growth Leader / O'Neil satellite
  -> Bearish context / paper short
  -> Japan expansion
  -> AI reviewer
  -> Options research backlog
```

This means current O'Neil-core ETF work should be preserved, but it is not the final core alpha engine. The first production alpha line should become ETF Trend / Rotation. O'Neil/Growth Leader becomes an upside satellite after the core workflow is stable.

## 3. Non-Negotiable Product Rules

- Manual confirmation only.
- No automatic broker execution.
- No managed accounts.
- No copy trading.
- No signal-selling product.
- No personalized investment advice.
- No redistribution of licensed market data without proper rights.
- Risk Engine can block a plan.
- AI cannot upgrade a trade or increase size.
- PA and Strat cannot override portfolio risk.
- Strat cannot create a trade by itself.
- Short logic starts as defensive context and paper research.
- Options remain research-only until the rest of the system is validated.

## 4. Current User Context

The product is still designed first around a small independent trading account.

Known constraints:

- User is based in Japan.
- Initial active trading capital is small, roughly 1,000-2,000 USD.
- Monthly additions are modest.
- Larger wealth remains outside the active trading account.
- US market data is available through Polygon/Massive.
- Japan moomoo OpenAPI is not available as a system data source.
- TradingView can remain a personal final-review tool, but should not become a required data dependency.
- The system should reduce manual chart-scanning time without becoming an auto-trader.

## 5. Target System Shape

```text
User
  -> Tenant
  -> Trading Account / Workspace
  -> Market Data Entitlements
  -> Strategy Engines
  -> Candidates
  -> Plans
  -> Positions
  -> Exit Alerts
  -> Journal
  -> Analytics
  -> Milestones
```

Tenant isolation is a platform boundary. Trading accounts are product/workflow boundaries. They should not be collapsed into the same concept.

## 6. Engine Decision Rights

### Production Decision Engines

These engines can create, rank, block, or update live/paper workflow objects.

- Data Quality Gate.
- ETF Trend / Rotation Engine.
- Basic PA Engine.
- Strat Trigger Layer, only inside PA.
- Risk Engine.
- Position Ledger.
- Exit Engine.
- Journal and Paper Trading workflow.

### Risk-Only Engines

Risk-only engines can downgrade, block, tighten, reduce, or exit. They cannot upgrade signals or increase size.

- Portfolio Risk Monitor.
- Market Regime Filter.
- Correlation Guard.
- Drawdown Recovery Engine.
- Data Freshness Guard.
- Strategy Kill Switch.
- Bearish Context Engine.

### Research-Only Engines

Research-only engines cannot affect live decisions until promoted through validation.

- Advanced PA rules.
- Short Watchlist.
- Paper Short.
- Options Adapter.
- 0DTE research.
- Covered call, spread, hedge, and options portfolio research.
- AI Reviewer before explicit permissioning.

### Analytics-Only Engines

Analytics-only engines measure the system. They do not generate trades.

- Signal funnel reports.
- MFE/MAE diagnostics.
- Setup calibration.
- Strategy attribution.
- Baseline comparisons.
- Walk-forward reports.
- Rule violation cost reports.

## 7. Current Implementation Status

### Implemented Or Partially Implemented

- FastAPI backend.
- Auth0/OIDC account-scoped auth.
- PostgreSQL/Timescale-ready schema and Alembic migrations.
- Polygon/Massive ingestion foundation.
- PA facts, structures, setups, and PA Lab.
- Strat signal layer foundation.
- US ETF O'Neil-core scanner.
- Account-scoped candidates linked to PA setups.
- Candidate detail with human explanation, scanner decision, chart evidence, entry plan, and exit plan.
- Scanner outcome review and recalculation.
- Candidate plan preview and plan creation.
- Position lifecycle: planned, open, reduce, closed, cancelled.
- Account risk settings and position sizing.
- Portfolio risk monitor.
- Exit Engine v0.2.
- Exit alerts and in-app notifications.
- Automation Job Runner.
- Trade journal generation on close.
- Next.js workspace with zh/en/ja i18n.
- Frontend views for overview, candidates, PA Lab, review, positions, exit alerts, automation, notifications, journal, and settings.

### Not Yet Implemented

- Tenant model above account/workspace.
- Tenant memberships and invitations.
- Legal acknowledgement gate.
- BYO data credentials.
- Data entitlement checks.
- Support access grants.
- Billing and usage events.
- True ledger-driven analytics.
- Dynamic milestone dashboard.
- Contribution-adjusted return, TWR, and MWR.
- Drawdown recovery state.
- Data Quality Gate.
- Strategy Kill Switch.
- Correlation Guard.
- ETF Trend / Rotation Engine.
- Earnings Drift / Revision.
- Japan expansion.
- Paper Short workflow.
- AI Reviewer.
- Options product layer.

## 8. What Should Not Be Rewritten

The current system should not be thrown away.

Keep and extend:

- PA tables and PA calculator.
- Scanner outcome tables.
- Candidate and candidate detail APIs.
- Plan preview and plan creation workflow.
- Position lifecycle workflow.
- Risk settings and portfolio risk summary.
- Exit alert engine.
- Notification event model.
- Job run model.
- Frontend workspace and component split.
- i18n foundation.
- Auth0 MVP while tenant support is added.

## 9. What Needs Refactoring

Refactor before adding the next large product layer:

- Introduce `tenant_id` above account/workspace.
- Split the large business service into domain services.
- Replace placeholder analytics with real ledger queries.
- Expand SSE from heartbeat to job/notification/candidate/alert events.
- Move O'Neil-core scanner into satellite status once ETF Rotation exists.
- Add data authorization boundaries before external users are invited.

## 10. Dynamic Milestone Strategy

The milestone system exists to answer:

- What stage is this trading account in?
- Should the user preserve, validate, scale, or pause?
- Is current performance from deposits or trading P/L?
- Has drawdown forced a lower-risk mode?
- Is the account allowed to withdraw profit, or should it keep compounding?

Default ladder:

| Level | Equity Range | Primary Objective |
| --- | --- | --- |
| 1 | $2k-$10k | Survival and validation |
| 2 | $10k-$25k | Small account growth |
| 3 | $25k-$50k | Controlled scaling |
| 4 | $50k-$100k | First $100K push |
| 5 | $100k-$250k | Post-100K growth |
| 6 | $250k-$500k | Cashflow pilot |
| 7 | $500k-$1M | Cashflow and preservation |
| 8 | $1M+ | FIRE support and preservation |

Before the first $100K, default behavior is compounding rather than monthly withdrawal, except for taxes, fees, emergency withdrawal, or explicit manual override.

Required metrics:

- Current equity.
- Net deposits.
- Trading P/L.
- Contribution-adjusted return.
- Time-weighted return.
- Money-weighted return.
- Current drawdown.
- Max drawdown.
- Consecutive losses.
- Current milestone.
- Recovery mode.

## 11. Multi-User SaaS Strategy

SaaS support is allowed only if the product keeps strict boundaries:

- Tenant isolation.
- Account/workspace isolation.
- Role-based access.
- Audit logs.
- Legal acknowledgement.
- Data credential ownership.
- Support access grants.
- No brokerage execution.
- No personalized buy/sell instruction.

Recommended roles:

- Platform owner/admin.
- Tenant owner/admin.
- Trader.
- Read-only reviewer.
- Support, only with explicit grant.

The initial implementation can keep shared database plus application-level tenant enforcement. PostgreSQL RLS can be added later, after the schema boundary is stable.

## 12. Deployment Strategy

Railway remains the recommended first staging/internal beta path.

AWS should wait until:

- Tenant model exists.
- Auth and legal gates are stable.
- Data credentials are handled safely.
- Backups and monitoring are configured.
- Background job and realtime event paths are clearer.
- The system has enough beta usage to justify operational overhead.

## 13. Near-Term PR Sequence

### PR A: Current Position Lifecycle PR

Merge after tests pass.

Scope:

- Position lifecycle operations.
- Automation Job Runner.
- v1.1 documentation alignment.

### PR B: Tenant Foundation

Scope:

- `tenants`.
- `tenant_memberships`.
- `accounts.tenant_id`.
- `AuthPrincipal.tenant_id`.
- Legal acknowledgement schema.
- BYO data credential schema shell.
- Compatibility with the current Auth0 account flow.

### PR C: Service Split

Scope:

- Position service.
- Risk service.
- Notification service.
- Job service.
- Journal service.
- Keep route contracts stable.

### PR D: Milestone + Real Analytics

Scope:

- Goal ladders.
- Milestones.
- Contribution/deposit tracking.
- Real analytics from positions and journals.
- Drawdown recovery mode.

### PR E: ETF Trend / Rotation

Scope:

- ETF universe and rotation scoring.
- Trend, breadth, and regime diagnostics.
- Candidate generation using ETF Rotation as first production alpha line.

### PR F: Realtime Job And Notification Events

Scope:

- Background job runner.
- SSE event fanout.
- Frontend live updates for jobs, notifications, candidates, and alerts.
