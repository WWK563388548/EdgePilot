# EdgePilot Review, Next Steps, Deployment, and CI/CD Plan

## Scope

This review covers the current `main` state after D1 market-data ingestion was merged. It focuses on implementation correctness, the next backend/frontend milestones, and a pragmatic deployment plus CI/CD path.

## Implementation Status

- [x] GitHub Actions CI for lint, tests, compile, and Docker build.
- [x] Backend Dockerfile.
- [x] Railway deployment config.
- [x] Alembic baseline migration.
- [x] Missing market-data indexes.
- [x] `ingestion_runs` table.
- [x] Admin token protection for ingestion write endpoints.
- [x] Polygon option-chain pagination.
- [x] `timeframe` restricted to `1d` until intraday mapping is implemented.
- [x] Empty provider responses no longer update `data_freshness`.
- [x] Backend D2 API for candidates, positions, exit alerts, trades journal, and dashboard summary.
- [x] Next.js frontend foundation with Tailwind, shadcn-compatible scaffold, TanStack Query, Zustand, API client, and SSE client wrapper.
- [x] Frontend CI build job.

## Correctness Review

### P0 / release blockers

1. Ingestion write APIs are unauthenticated.
   - Status: resolved in this branch with `INGESTION_ADMIN_TOKEN` and `X-Ingestion-Admin-Token`.
   - Files: `backend/app/api/routes/ingestion.py`
   - Risk: once the backend is reachable outside local development, anyone can trigger Polygon requests, burn quota, and write arbitrary market context snapshots.
   - Recommendation: add an internal admin token or signed job trigger before exposing these endpoints. Keep read endpoints separate from write endpoints.

2. No migration system exists for already-created databases.
   - Status: resolved in this branch with Alembic baseline migration.
   - Files: `sql/init/001_schema.sql`
   - Risk: `docker-entrypoint-initdb.d` only runs on a fresh Postgres volume. Existing dev/staging/prod databases will not receive D1 tables or future D2/D3 schema changes.
   - Recommendation: add Alembic as the next infrastructure PR, keep `sql/init` for bootstrap only, and make CI run migration checks.

### P1 / high priority

1. Polygon option chain ingestion only stores the first page.
   - Status: resolved in this branch with `next_url` pagination and a max-page guard.
   - Files: `backend/app/services/polygon_client.py`, `backend/app/services/ingestion_service.py`
   - Risk: `limit=250` is not enough for liquid underlyings such as SPY/QQQ. The API can return paginated responses; current freshness can report success while the chain is partial.
   - Recommendation: follow `next_url` until complete, with max-page and rate-limit guards.

2. Failed or empty provider responses can still mark data as fresh.
   - Status: resolved in this branch for empty provider responses; broader provider status mapping remains future work.
   - Files: `backend/app/services/ingestion_service.py`
   - Risk: empty `results`, API errors, entitlement errors, and malformed payloads currently collapse into `records_written=0` but still update `data_freshness`.
   - Recommendation: introduce ingestion run status (`success`, `partial`, `failed`), provider error capture, and only update dataset freshness for successful writes.

3. Bar timeframe is accepted as arbitrary input but always fetches daily bars.
   - Status: resolved in this branch by restricting ingestion requests to `1d`.
   - Files: `backend/app/schemas/ingestion.py`, `backend/app/services/ingestion_service.py`
   - Risk: a caller can request `timeframe="1h"` and the service writes daily Polygon bars labeled as hourly.
   - Recommendation: either restrict D1 to `1d` with validation or implement multiplier/timespan mapping.

4. Tests only cover route delegation.
   - Status: improved in this branch with auth and request validation coverage; DB integration tests remain future work.
   - Files: `backend/tests/test_ingestion_routes.py`
   - Risk: SQL statements, provider parsing, pagination, empty/error payload handling, and freshness semantics are untested.
   - Recommendation: add unit tests for Polygon parsing and service tests with fake DB cursors, then add an integration test profile with Postgres/Timescale.

### P2 / medium priority

1. Query performance indexes from the PRD are missing.
   - Status: resolved in this branch for D1 query paths.
   - Files: `sql/init/001_schema.sql`
   - Risk: options lookup by underlying and snapshot time will degrade as snapshots accumulate.
   - Recommendation: add indexes for bars by `(symbol_id, timeframe, ts DESC)`, options by `(underlying_symbol, snapshot_ts DESC)`, `(option_symbol, snapshot_ts DESC)`, and `(underlying_symbol, expiration, option_type, delta)`.

2. Provider client lacks retry/backoff and structured error handling.
   - Files: `backend/app/services/polygon_client.py`
   - Risk: transient HTTP errors and rate limits become generic 500s and are hard to observe.
   - Recommendation: switch to a small HTTP client wrapper with timeouts, retries for transient failures, and normalized provider exceptions.

3. Backend is not containerized yet.
   - Status: resolved in this branch with `Dockerfile`, `railway.toml`, and `scripts/start_backend.sh`.
   - Files: repository root
   - Risk: deployment cannot be reproduced consistently.
   - Recommendation: add a backend Dockerfile and a production compose or platform-specific deployment manifest.

## Next Implementation Plan

### PR 1: Backend reliability foundation

- Add Alembic migrations and baseline the current schema.
- Add missing Timescale indexes and migration smoke tests.
- Add ingestion write authentication.
- Add provider error types and FastAPI exception mapping.
- Add unit tests for request validation, provider response parsing, and freshness behavior.

### PR 2: D1 ingestion hardening

- Implement Polygon pagination for options snapshots.
- Restrict or correctly map `timeframe`.
- Add `ingestion_runs` table for success/partial/failure status, record counts, provider status, and error messages.
- Add freshness semantics based on last successful ingestion.
- Add a scheduled ingestion entry point that can be called by cron/GitHub Actions/platform scheduler.

### PR 3: Backend D2 business state

- Status: implemented in this branch.
- Implemented CRUD/API for `candidates`, `positions`, `exit_alerts`, and `trades_journal`.
- Added request validation for PRD state enums such as candidate decision and position status.
- Added route-level tests for create/update/read delegation and dashboard summary.
- Added dashboard summary API that combines market context, counts, alerts, and freshness.

### PR 4: Frontend foundation

- Status: implemented in this branch.
- Scaffolded Next.js app with Tailwind, shadcn-compatible config/components, TanStack Query, and Zustand.
- Added API client and SSE client wrappers.
- Implemented Dashboard, Candidates, Positions, Exit Alerts, Journal, and Settings views.
- Uses dashboard summary and freshness data for visible operational status.

## Deployment Plan

### Target architecture

- Backend: FastAPI container.
- Database: managed Postgres with TimescaleDB support where possible; local dev remains `timescale/timescaledb`.
- Cache/realtime: Redis, optional for first production deploy if SSE remains heartbeat-only.
- Frontend: Vercel or static/container deployment once Next.js exists.
- Secrets: platform secrets for `DATABASE_URL`, `REDIS_URL`, `POLYGON_API_KEY`, `OPENAI_API_KEY`, and ingestion admin token.

### Environments

1. Local
   - Docker Compose for Postgres/Timescale and Redis.
   - Backend runs via `uvicorn` or backend container.

2. Staging
   - Same container image as production.
   - Separate database and secrets.
   - Auto-deploy from `main` after CI passes.

3. Production
   - Manual approval or protected environment deploy.
   - Migrations run before app rollout.
   - Ingestion schedule enabled only after secrets and rate limits are validated.

### Release gates

- CI green.
- Alembic migration check green.
- Docker image builds successfully.
- Staging health endpoint passes.
- Smoke test covers `/health`, freshness read, and a read-only market-data query.

## CI/CD Plan

### GitHub Actions CI

Run on pull requests and pushes to `main`:

- Set up Python 3.12.
- Install `.[dev]`.
- Run `ruff check .`.
- Run `pytest -q`.
- Run `python -m compileall backend`.
- Optional next step: spin up TimescaleDB service and run migration/integration tests.

### Build pipeline

- Build backend Docker image on `main`.
- Tag images with commit SHA and optionally `latest` for staging.
- Push to GHCR or the selected deployment platform registry.

### Deploy pipeline

- Staging deploy on every merge to `main`.
- Production deploy by manual approval.
- Deployment steps:
  1. Pull image.
  2. Run migrations.
  3. Start or roll backend service.
  4. Run smoke tests.
  5. Enable scheduled ingestion job.

## Suggested Immediate Order

1. Create the reliability foundation PR before D2 feature work.
2. Add CI first, even before deployment, so every next PR has a safety rail.
3. Add Alembic before more schema changes.
4. Harden ingestion semantics before scheduling real Polygon jobs.
5. Start D2 APIs once the database migration path is stable.
