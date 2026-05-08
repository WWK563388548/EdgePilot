# EdgePilot Product Strategy v1.5.1

This is the current authoritative product strategy for EdgePilot.

Full source archive: `docs/reference/EdgePilot_PRD_TDD_Implementation_Plan_v1_5_1_Pragmatic_Rollout_Proxy_Robustness.md`.

Release implementation plan: `docs/release_implementation_plan.md`.

The v1.5.1 update supersedes the v1.1 maintained docs. It does not ask the project to become more complex immediately. Its main message is the opposite: EdgePilot should become robust before it becomes sophisticated.

## 1. Product Positioning

EdgePilot is a multi-asset, manual trading operations cockpit.

It helps a user:

- Screen trade candidates.
- Understand price-action, strategy, and market-context evidence.
- Create manual trade plans.
- Size risk before entry.
- Track planned and open positions.
- Monitor exit conditions.
- Record journal outcomes.
- Review whether the system is working.
- Compound a small trading account through milestones.
- Prepare for private-beta multi-user use without turning into a full commercial SaaS too early.

EdgePilot does not place broker orders. Every entry, trim, stop, close, and cancel remains manually confirmed by the user outside the system.

## 2. v1.5.1 Priority Reset

v1.5.1 keeps the platform ambition from v1.1, but changes the rollout posture.

The system should not jump directly into full SaaS, advanced proxy scoring, or expensive data. It should first make the core loop reliable:

```text
Risk / Position / Exit
  -> CSV execution import and real analytics
  -> Shadow / Paper validation
  -> Tenant-lite + BYOK + Data Capability
  -> ETF / large-cap scanner
  -> Basic PA + Strat trigger
  -> MAX_20D analytics / warning
  -> Proxy Data Quality
  -> Decision Policy skeleton
  -> RSP/SPY analytics-only
  -> broader proxy research later
```

This preserves the v1.1 tenant direction, but narrows it to a pragmatic private-beta path.

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
- Proxy data starts analytics-only.
- Single proxy cannot veto a trade.
- Missing proxy data cannot crash the scanner.
- Decision logic must be policy-driven, not scattered if/else rules.

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

## 5. Current Implementation Status

Implemented or partially implemented:

- FastAPI backend.
- Auth0/OIDC account-scoped auth.
- PostgreSQL/Timescale-ready schema and Alembic migrations.
- Polygon/Massive ingestion foundation.
- PA facts, structures, setups, and PA Lab.
- Strat signal layer foundation.
- US ETF O'Neil-core scanner.
- Candidate detail with explanation, scanner decision, chart evidence, entry plan, and exit plan.
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

Not yet implemented:

- Tenant-lite data boundary.
- BYOK encrypted credential storage.
- Per-tenant rate limit and job state.
- Data Capability Matrix.
- CSV execution import.
- Dividend and corporate-action accounting.
- Real ledger-driven analytics.
- Dynamic milestone dashboard.
- Backtest / Shadow / Paper validation gates.
- ETF Trend / Rotation engine.
- MAX_20D analytics/warning.
- Proxy lifecycle and data quality state.
- Decision Policy Engine.
- RSP/SPY analytics-only dashboard.
- State combination test matrix.

## 6. What Should Not Be Rewritten

The current implementation should not be thrown away.

Keep and extend:

- Auth0 MVP while tenant-lite is introduced.
- `account_id` scoped business data.
- PA facts, structures, setups, and scanner outcomes.
- Candidate and candidate detail APIs.
- Plan preview and plan creation workflow.
- Position lifecycle workflow.
- Risk settings and portfolio risk summary.
- Exit alert engine.
- Notification event model.
- Job run model.
- Frontend workspace, component split, and i18n.

The code needs targeted refactoring, not a rewrite.

## 7. What Needs Refactoring

Refactor in controlled steps:

- Add tenant-lite above accounts without renaming every `account_id`.
- Split the large business service into domain services.
- Replace placeholder analytics with real ledger queries.
- Add CSV execution import before broker sync.
- Add data capability and BYOK boundaries before inviting external users.
- Expand SSE from heartbeat to job/notification/candidate/alert events only after background jobs mature.
- Move O'Neil-core scanner into satellite status once ETF Rotation exists.

## 8. Tenant-Lite Private Beta Strategy

v1.5.1 confirms that early multi-user support should be tenant-lite, not full commercial SaaS.

Now required:

- `tenant_id / user_id` basic isolation.
- BYOK encrypted credential storage.
- Per-tenant API rate limit.
- Data Capability Matrix.
- CSV execution import.
- Dividend / Corporate Actions accounting.
- Public market data vs private user data separation.
- Redis channel namespace, when realtime expands.
- Basic audit log.

Later, after beta:

- Read-only broker integration.
- Tenant-level worker queue.
- API key tier detection.
- Feature degradation UI.
- Broker reconciliation.
- Usage-based job scheduling.

Commercial SaaS later:

- Full PostgreSQL RLS.
- Multi-region infrastructure.
- Enterprise observability.
- Billing/subscription.
- Advanced RBAC.
- Formal legal/compliance review.

## 9. Data-Aware Proxy Strategy

v1.5.1 says proxy modules must be introduced gradually.

Production v1.5-MVP:

- ETF / large-cap scanner.
- Basic PA / Strat trigger.
- Position Ledger.
- Exit Engine.
- CSV execution import.
- Backtest.
- Shadow Mode.
- Paper Trading.
- MAX_20D lottery warning.
- Basic analytics dashboard.

Analytics-only in v1.5-MVP:

- RSP/SPY.
- IWM/SPY.
- HYG/IEF.
- VIXY/SPY.
- Turn-of-the-month tags.
- Monday effect.
- Overnight drift.
- FOMC manual calendar.
- Smart Money Flow, only if intraday data is stable.

Research-only:

- True options skew.
- Dealer GEX.
- Insider buying.
- Buyback execution.
- Borrow fee.
- Real-time short data.
- EPS surprise / guidance until paid data is added.

## 10. Proxy Robustness Rules

Each proxy must have a lifecycle stage:

```text
Idea
Data Available
Analytics-only
Shadow Modifier
Paper Modifier
Risk Modifier
Production Decision Contributor
```

Each proxy must have a daily data state:

```text
available
stale
missing
invalid
fallback_used
disabled
```

Rules:

- Missing proxy data does not imply risk-off.
- Missing proxy data does not imply risk-on.
- Missing non-core proxy data disables that proxy for the day.
- Core price data failure can block production scanning.
- `risk_multiplier` cannot be NaN.
- `decision` cannot be undefined.
- Single proxy warning cannot reject an A+ setup.

## 11. Decision Policy Strategy

Modules should output standardized modifiers. A Decision Policy Engine should combine them.

Priority order:

1. Hard Safety Rules.
2. Data Quality.
3. Validation / Live Eligibility.
4. Account Risk / Drawdown.
5. Strategy Kill Switch.
6. Liquidity / Execution Risk.
7. Market Regime.
8. Breadth / Credit / Proxy Modifiers.
9. PA / Strat Quality.
10. Calendar / Timing Modifiers.
11. Cashflow Target Modifier.
12. AI Reviewer, explanation only.

Only these layers can veto:

- Hard Safety Rules.
- Data Quality, core failure only.
- Validation / Live Eligibility.
- Account Risk / Drawdown.
- Strategy Kill Switch.
- Liquidity / Execution hard failure.

Default non-veto layers:

- Breadth proxy.
- Credit proxy.
- Calendar tags.
- FOMC window.
- Turn-of-the-month.
- Overnight drift.
- AI review.

## 12. Near-Term PR Sequence

Expanded release roadmap: `docs/release_implementation_plan.md`.

### PR A: v1.5.1 Documentation Alignment

Current PR.

Scope:

- Preserve full v1.5.1 source archive.
- Replace v1.1 maintained docs with v1.5.1 maintained docs.
- Update README roadmap references.

### PR B: Tenant-Lite + Data Capability Foundation

Scope:

- `tenants`.
- `tenant_memberships`.
- `accounts.tenant_id`.
- `AuthPrincipal.tenant_id`.
- BYOK credential table shell.
- Data Capability Matrix shell.
- Per-tenant job/rate-limit state shell.
- Basic legal acknowledgement.
- Keep current account-scoped business tables stable.

### PR C: Service Split

Scope:

- Position service.
- Risk service.
- Notification service.
- Job service.
- Journal service.
- Keep route contracts stable.

### PR D: CSV Import + Real Analytics

Scope:

- CSV execution import.
- Ledger-driven analytics.
- P/L by realized/unrealized.
- R multiple distribution.
- Execution quality basics.

### PR E: Backtest / Shadow / Paper Validation

Scope:

- Backtest run model.
- Shadow candidates.
- Paper validation gates.
- Rejected Signal Shadow.

### PR F: ETF Rotation + MAX_20D Analytics

Scope:

- ETF rotation foundation.
- MAX_20D analytics/warning.
- No direct hard reject until validated.

### PR G: Proxy Data Quality + Decision Policy Skeleton

Scope:

- Proxy lifecycle status.
- Proxy data quality events.
- Decision policy events.
- State combination test cases.
- Analytics-only RSP/SPY dashboard.
