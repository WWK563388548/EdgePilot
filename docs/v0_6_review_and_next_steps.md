# v0.6 PRD/TDD Review and Next Steps

## Source

Canonical product document for the next phase:

- `docs/edgepilot_prd_tdd_implementation_plan_v0_6_advanced_pa_engine.md`

This supersedes the v0.3 implementation roadmap as the product direction. The v0.3 roadmap remains useful as historical context for the database, frontend, and analytics foundation.

## Executive Conclusion

The existing implementation is still directionally correct. It has the right foundation for v0.6:

- FastAPI backend.
- PostgreSQL/TimescaleDB and Redis local stack.
- Alembic migrations.
- SQLAlchemy ORM.
- Auth0/OIDC authentication.
- Account-scoped business data.
- Polygon ingestion for daily US bars, option chains, and market context.
- Next.js workspace with protected dashboard and business tables.

The important v0.6 change is priority. EdgePilot should not jump directly to analytics, options, cashflow, or AI review while candidates are still empty. The next product milestone should be:

```text
Market data -> PA facts -> PA structure/location/volume -> setup detection -> PA score -> candidate generation
```

The app returning empty arrays is now expected behavior: authentication and business APIs work, but no scanner or PA engine has created product data yet.

## Current Implementation vs v0.6

| Area | Status | Notes |
| --- | --- | --- |
| Project skeleton | Done | Backend, frontend, Docker, CI, local compose are in place. |
| Auth and user isolation | Done | Auth is mandatory; business data is account-scoped. |
| ORM and migrations | Done | SQLAlchemy 2.0 and Alembic are active. |
| D1 market ingestion | Partial | Daily bars/options/market context exist; scheduled jobs and universe management are not done. |
| Business state APIs | Partial | CRUD exists, but workflow actions such as create planned position and close-to-journal are not done. |
| Frontend workspace | Partial | Core views exist; detail drawers, charts, PA Lab, validation, analytics, and cashflow pages are missing. |
| Scanner engine | Missing | No O'Neil, ETF rotation, or market-regime scanner yet. |
| PA facts layer | Missing | v0.6 tables and calculators are not implemented. |
| PA structure/location/volume layers | Missing | No derived PA layers yet. |
| PA setup library | Missing | Breakout/Pullback/etc. are only represented as free-text candidate fields. |
| PA quality score and entry/exit plans | Missing | Candidate has simple `score_total`, `entry_trigger`, and `initial_stop`, but not v0.6 score breakdown or JSON plans. |
| PA calibration and validation gate | Missing | v0.5/v0.6 testing tables and shadow/paper/live gating are not implemented. |
| AI PA reviewer | Missing | `ai_review_json` exists as a placeholder; no structured reviewer workflow exists. |
| Cashflow target engine | Missing | v0.4 remains a later risk-management layer. |
| J-Quants / Japan context | Missing | Should remain after US ETF PA foundation. |

## Correctness Review

No existing code needs to be rolled back for v0.6. The current stack is a solid foundation. The main correctness gap is scope alignment:

- README and historical roadmap needed v0.6 pointers; this branch updates those references.
- Candidate data model is too shallow for Advanced PA, but acceptable until the PA tables land.
- The product currently has no source of candidates; empty arrays are correct until a scanner/PA job exists.
- Ingestion is manually triggered; PA development needs a repeatable seed/universe ingestion path.
- Validation must be built before any advanced PA setup can influence live decisions.

## Recommended Next PR Sequence

### PR A: v0.6 Documentation Alignment

Status: this branch.

Tasks:

- Add the v0.6 PRD/TDD document into `docs/`.
- Add this short review and next-step document.
- Update README to reference v0.6 and explain why business APIs currently return empty arrays.

Acceptance:

- A new contributor can tell that v0.6 is the current product direction.
- The next implementation PR is unambiguous.

### PR B: PA Data Foundation

Goal: make v0.6 schema real before writing detector logic.

Tasks:

- Add Alembic migration `0003_pa_engine_foundation`.
- Add ORM models:
  - `pa_facts`
  - `pa_structures`
  - `pa_setups`
  - `pa_calibration_stats`
- Use JSON/JSONB columns for facts, metrics, entry plans, exit plans, and invalidation.
- Add Pydantic schemas for PA facts, structures, setups, and calibration stats.
- Add read APIs:
  - `GET /api/pa/facts/{symbol}?timeframe=1d`
  - `GET /api/pa/setups`
  - `GET /api/pa/setups/{setup_id}`
  - `GET /api/pa/calibration`
- Add tests for model creation, route serialization, and account/global scoping decisions.

Acceptance:

- Migrations apply cleanly.
- API can return empty PA datasets with correct response shape.
- The database can store all v0.6 PA artifacts without schema churn.

### PR C: ETF Market Data Seed and PA Facts Layer

Goal: produce the first real derived data from existing `bars`.

Suggested initial universe:

```text
SPY, QQQ, IWM, SMH, SOXX
```

Tasks:

- Add a configured ETF universe.
- Add a command/job to ingest recent daily bars for the universe.
- Add PA facts calculator for `1d` bars:
  - new highs/lows.
  - close near high/low.
  - moving-average facts.
  - distance from 20/50/200MA.
  - relative volume.
  - basic range facts.
- Store facts in `pa_facts`.
- Add an admin-triggered endpoint or CLI command for local testing.

Acceptance:

- Running one command can populate `bars` and `pa_facts` for the ETF universe.
- PA facts are deterministic and covered by unit tests.

### PR D: Basic PA Setup Detection and Candidate Generation

Goal: make the frontend stop being empty by generating first candidates.

Tasks:

- Implement structure/location/volume scoring for daily ETF bars.
- Implement first setup types:
  - `breakout`
  - `pullback_to_20ma`
  - `failed_breakdown_reclaim`
- Generate `pa_setups` with `validation_status="shadow_only"` by default.
- Map high-quality basic setups into `candidates`.
- Add candidate fields or join APIs so frontend can show PA score, grade, and entry/stop plans.

Acceptance:

- At least one test fixture can generate a PA setup and candidate.
- Frontend Candidates view can show real scanner output after local seed data is loaded.
- Advanced setup types remain shadow-only.

### PR E: PA Lab Frontend and Candidate Detail

Goal: expose the new PA artifacts without pretending they are trade recommendations.

Tasks:

- Add `PA Lab` navigation view.
- Add Setup Explorer table.
- Add PA quality breakdown panel.
- Add candidate detail drawer with:
  - PA setup.
  - PA grade.
  - score breakdown.
  - entry plan.
  - exit plan.
  - invalidation.
  - validation status.

Acceptance:

- User can inspect why a setup exists.
- UI clearly distinguishes `shadow_only`, `paper_allowed`, and `live_allowed`.

### PR F: Validation, Shadow Mode, and Calibration

Goal: enforce the v0.5/v0.6 safety rule: advanced PA can be recorded before it can be trusted.

Tasks:

- Add test/validation tables from v0.5 if not already present.
- Add signal funnel snapshots.
- Add PA calibration stat recalculation.
- Add paper/shadow status transitions.
- Add rules that prevent advanced setup live eligibility unless validation thresholds pass.

Acceptance:

- No advanced PA setup can become live-eligible without sample-size and expectancy checks.
- Calibration stats are visible through API.

## Next Step Recommendation

The next implementation PR should be **PR B: PA Data Foundation**.

Reason:

- It is the smallest useful step toward v0.6.
- It does not depend on OpenAI, J-Quants, broker APIs, or a finished frontend charting layer.
- It gives the project a stable schema for all later PA work.
- It avoids mixing detector logic with schema design.

After PR B, do PR C immediately so the system can generate real PA facts from Polygon ETF bars.

## Decisions to Keep Stable

- Advanced PA setups default to `shadow_only`.
- No automatic trading.
- No live decision path until validation gates exist.
- Options remain expression layer, not discovery layer.
- Cashflow Target Engine should reduce risk later, but should not block PA data foundation.
- J-Quants/Japan context comes after the US ETF PA foundation.
