# EdgePilot Product Strategy v0.9

This is the current authoritative product direction for EdgePilot. Older v0.3/v0.6 planning docs were removed because they were superseded by this strategy.

Detailed PRD/TDD and implementation contracts are tracked in `docs/prd_tdd_v0_9.md`.
The full original v0.9 research document is archived at `docs/reference/edgepilot_prd_tdd_v0_9_full.md` for traceability.

## One-Line Definition

EdgePilot is a manual trading operations cockpit for a small account. It screens US ETF and stock candidates, explains price-action evidence, creates paper/manual trade plans, tracks positions, enforces risk guardrails, raises exit alerts, and records journals. It does not place broker orders.

## Current Product Principles

- Manual confirmation only. No broker order execution.
- Protect capital before seeking return.
- Keep the live decision path simple.
- Treat PA as core structure analysis.
- Treat Strat as an objective trigger layer inside PA, not a standalone strategy.
- Keep the system long-biased by default.
- Use bearish logic first to reduce long risk.
- Keep short live trading disabled.
- Keep options as lowest-priority research/paper backlog.
- AI can explain and challenge, but cannot upgrade a trade or override risk.
- Every new rule that can affect decisions needs validation, ablation, and a simpler baseline comparison.

## Minimal Live/Paper Path

```text
Data
  -> Scanner
  -> Basic PA
  -> Strat Trigger Layer
  -> Risk Engine
  -> Candidate
  -> Paper/Manual Position
  -> Exit Engine
  -> Journal
  -> Analytics / Calibration
```

Anything outside this path is not MVP unless it removes a current blocker.

## Engine Decision Rights

### Production/Paper Decision Engines

- US ETF Scanner v1
- US liquid large-cap scanner v1, future
- Basic PA Engine
- Strat Trigger Layer v1, only as PA confirmation/downgrade
- Risk Engine
- Position Ledger
- Exit Engine
- Journal / Paper Trading

### Risk-Only Engines

Risk-only engines can downgrade, block, tighten risk, reduce, or exit. They cannot upgrade a signal or increase size.

- Portfolio Risk Monitor
- Market Regime Filter
- Data Freshness Guard
- Headline/Event Risk Filter, future
- Cashflow Target Engine, future
- Short Risk Guard, future

### Research-Only Engines

Research-only engines cannot affect live decisions.

- Advanced PA rules before validation
- Short Watchlist before paper validation
- Options Adapter
- 0DTE research
- Covered call / spread / hedge research
- AI Reviewer before explicit permissioning

### Analytics-Only Engines

- Strategy attribution
- MFE/MAE diagnostics
- Walk-forward reports
- Ablation reports
- Baseline comparisons
- Rule violation cost

## Current Implementation Status

Implemented:

- FastAPI backend with account-scoped Auth0/OIDC auth.
- PostgreSQL/Timescale-ready schema and Alembic migrations.
- Market data ingestion endpoints and Polygon/Massive client.
- PA facts, PA structures, PA setups, calibration stats foundation.
- US ETF daily PA facts calculator.
- O'Neil-core US ETF scanner v1.
- Account-scoped candidates with PA setup bridge.
- Candidate detail with scanner decision, human explanation, chart evidence, entry/exit plan.
- PA Lab setup explorer.
- Scanner outcome review and recalculation.
- Candidate paper/manual plan creation.
- Position lifecycle: planned, open, reduce, closed.
- Journal generation on close.
- Account risk settings and single-trade sizing.
- Portfolio Risk Monitor v1, including account-level risk budget checks.
- Exit Engine v0.2, including hard stop, breakeven, trim, trailing, time-stop, failed-breakout, and risk-off regime alerts.
- Next.js frontend with zh/en/ja i18n, dashboard, candidates, PA Lab, review, positions, alerts, journal, settings.
- Railway deployment guide and Auth0 setup guide.

## Gaps Before Staging Deployment

Required before Railway staging:

- Deploy from a reviewed `main` branch.
- Migrations pass on staging database.
- Auth0 SPA/API configured.
- Backend CORS updated for deployed frontend domain.
- Required secrets configured: `DATABASE_URL`, `POLYGON_API_KEY`, `INGESTION_ADMIN_TOKEN`, Auth0 values.
- Basic smoke test: `/health`, authenticated dashboard, candidates, positions, exit alerts.

Required before public beta:

- Data Quality Gate v1.
- Basic application logs and error monitoring.
- Database backup policy.
- Staging/production environment split.
- Validation Lite dashboard.
- Clear in-app disclaimers that the system is paper/manual and not investment advice.

Not required before staging:

- AWS migration.
- Options module.
- Short live support.
- Full Advanced PA.
- AI Reviewer.

## Roadmap

### P0: Risk + Position + Exit Foundation

Mostly implemented.

Remaining:

- Add data repair/diagnostic endpoint for incomplete planned positions.
- Add drawdown halt and consecutive-loss rule.

### P1: US ETF / Large-Cap Scanner + Basic PA + Strat Bar Labeling

Next feature PR:

- Add `strat_signals`.
- Compute daily bar state: `1`, `2U`, `2D`, `3`.
- Add minimal patterns: inside breakout, 2U continuation, 2D continuation.
- Attach Strat summary to PA setup/candidate detail.
- Strat can confirm, delay, downgrade, or invalidate. It cannot create a trade alone.

### P2: Frontend Trading Cockpit

Mostly implemented for current modules.

Remaining:

- Make alert level 4 visually stronger.
- Add position detail drawer.
- Add data quality/system health panel.
- Add richer chart marks for Strat trigger and trigger stop.

### P3: Paper Trading + Journal Analytics

Next after Strat foundation:

- Auto paper P/L snapshots.
- R distribution.
- Win/loss, average R, profit factor.
- Setup breakdown.
- PA-only vs PA+Strat comparison.

### P4: PA / Strat Calibration

- Signal funnel.
- Sample size gates.
- Ablation tests.
- Baseline comparison.
- Promotion gate: research -> shadow -> paper -> micro live.

### P5: Advanced PA v1

Only after calibration exists.

Allowed first:

- Breakout failure detection.
- No-chase/overextension warning.
- Multi-timeframe PA alignment.
- Volume-price anomaly.
- Structure quality score.

### P6: Capital Accumulation Mode

- Monthly contribution tracking.
- Account growth ladder.
- Risk-by-equity schedule.
- Cashflow target remains locked until account threshold and validation gates are met.

### P7: Japan Daily Scanner

- J-Quants listed info, daily prices, financial summary, earnings schedule.
- Japan liquidity and event filters.
- JP daily PA/Strat.
- US overnight impact context.

### P8: Short Watchlist + Paper Short

- Bearish context for long risk reduction.
- Paper-only short watchlist.
- Short gap-up stress test.
- Borrow/hard-to-borrow fields as manual or placeholder first.
- Live short remains disabled.

### P9: AI Reviewer

- Structured JSON input/output.
- Explanation, bear case, risk summary.
- No decision rights.

### P10: Options Backlog

- Disabled by default.
- First future step is manual option note/risk display, not option picking.
- No 0DTE, no short premium, no live options until later validation.

## Deployment Direction

Use Railway for staging/internal beta first. It is simple and already documented. Move to AWS only after the MVP has real usage, stable ingestion, basic monitoring, and a clearer cost/ops profile.

Preferred AWS path later:

- App Runner for backend container, or Lightsail Containers for a simpler AWS entry.
- Managed database separately, ideally Timescale/Tiger Data or RDS-compatible Postgres if Timescale requirements are relaxed.
- S3/CloudWatch/Secrets Manager as the operational surface grows.
