# Auth, ORM, and Next Implementation Plan

## Current Context

The project now has a deployable FastAPI backend, D1 ingestion hardening, D2 business-state APIs, and a Next.js frontend workspace. The remaining blocker before sharing the system with non-technical users is not UI polish; it is user identity and data isolation.

The current `INGESTION_ADMIN_TOKEN` is only suitable for internal jobs and admin-only write endpoints. It should not become the user authentication model.

## Implementation Status

- [x] SQLAlchemy 2.0 dependency, `Base`, engine, and session dependency.
- [x] ORM models for auth, market data, business state, ingestion runs, freshness, and analytics core tables.
- [x] Account ownership tables: `users`, `accounts`, `account_memberships`, `audit_logs`.
- [x] Account scoping for `candidates`, `positions`, `exit_alerts`, and `trades_journal`.
- [x] Alembic migration `0002_auth_orm_account_scope`.
- [x] Business service migrated from raw psycopg SQL to SQLAlchemy ORM.
- [x] Ingestion service migrated from raw psycopg SQL to SQLAlchemy Core/ORM session usage.
- [x] JWT/OIDC bearer verification foundation for FastAPI.
- [x] Auth is mandatory in every environment; there is no env-var bypass.
- [x] Email verification is required before business/dashboard access.
- [x] Backend endpoint for resending Auth0 verification emails.
- [x] Frontend Auth0 refresh-token rotation support.
- [x] Frontend email-verification gate.
- [x] Role dependencies for viewer/trader/admin/owner.
- [x] Business/dashboard API protection with authenticated account context.
- [x] Auth0 React provider and frontend bearer token injection.
- [x] Account isolation test for business service.

## Auth Decision

### Recommendation

Use external OIDC/JWT authentication for the first multi-user beta, and store only application authorization data in EdgePilot.

Recommended first provider: Auth0.

Rationale:

- The app already has a separate FastAPI backend and Next.js frontend.
- Auth0 has a direct FastAPI API integration path.
- Email/password, OAuth, MFA, password reset, email verification, and session/device security are easy to get wrong if hand-rolled.
- We can keep trading data in our own Railway/Timescale database.

Acceptable alternatives:

- Clerk: very strong Next.js developer experience; backend verification needs a JWT/JWKS integration.
- Supabase Auth: good if we later move auth plus database/RLS into Supabase, but less compelling while the primary DB is Railway/TimescaleDB.
- Better Auth/Auth.js: good self-hosted path for Next.js, but more integration work because our source-of-truth API is FastAPI.

### Target Auth Model

Add app-owned authorization tables:

- `users`
  - `user_id`
  - `external_subject`
  - `email`
  - `display_name`
  - `created_at`
  - `last_login_at`
- `accounts`
  - `account_id`
  - `name`
  - `created_at`
- `account_memberships`
  - `account_id`
  - `user_id`
  - `role`: `owner`, `admin`, `trader`, `viewer`
  - `created_at`
- `audit_logs`
  - `audit_id`
  - `account_id`
  - `actor_user_id`
  - `action`
  - `entity_type`
  - `entity_id`
  - `metadata_json`
  - `created_at`

Add `account_id` to user-owned tables:

- `candidates`
- `positions`
- `exit_alerts`
- `trades_journal`
- future user-facing analytics/portfolio tables

Keep provider/global market-data tables shared unless later user-specific data policy requires otherwise:

- `bars`
- `options_chain_snapshots`
- `market_context_snapshots`
- `data_freshness`
- `ingestion_runs`

### Backend Authorization Rules

- Public or semi-public:
  - `GET /health`
  - optionally API docs in non-production only
- Authenticated user required:
  - dashboard summary
  - candidates
  - positions
  - exit alerts
  - journal
  - user-specific analytics
- Admin/system token required:
  - ingestion writes
  - scheduled jobs
  - provider-triggering operations
- Role-gated operations:
  - `viewer`: read only
  - `trader`: create/update trading state
  - `admin`: manage account members/settings
  - `owner`: billing/destructive/account ownership actions

## ORM Decision

### Recommendation

Use SQLAlchemy 2.0 as the standard database layer across the backend.

Use SQLAlchemy ORM for:

- users/accounts/memberships/audit logs;
- candidates/positions/exit alerts/journal;
- future business workflows that need relationships, transactions, and account scoping.

Keep SQLAlchemy Core acceptable only where the database operation itself is clearer as SQL expression work:

- high-volume ingestion upserts;
- Timescale hypertable operations;
- provider data writes where explicit SQL is clearer and faster.

### Why ORM Now

The earlier raw `psycopg` services were fine for D1/D2 velocity, but multi-user auth changes the complexity:

- every user-owned query must be scoped by `account_id`;
- relationships between users, accounts, roles, positions, alerts, and journal entries matter;
- tests need a cleaner session boundary;
- Alembic autogenerate becomes more valuable once models are the schema source of truth.

### Why SQLAlchemy Instead of SQLModel

SQLModel remains a reasonable option, but SQLAlchemy 2.0 is the safer choice for this codebase now:

- the project already uses separate Pydantic schemas;
- Alembic is already in place;
- SQLAlchemy 2.0 typed ORM is mature and explicit;
- Timescale/Postgres-specific behavior is easier to model without coupling API schemas to DB models.

## Immediate PR Sequence

### PR 5: ORM and Ownership Foundation

Status: implemented in this branch.

Goal: create the data model required for safe multi-user auth before exposing user data.

Tasks:

- Add SQLAlchemy 2.0 dependency and session dependency.
- Add ORM models for existing D2 business tables.
- Add ORM models for `users`, `accounts`, `account_memberships`, and `audit_logs`.
- Add Alembic migration for new auth/ownership tables.
- Add `account_id` to user-owned business tables.
- Backfill a default account for existing local/staging data.
- Refactor D2 business service to use SQLAlchemy sessions and account-scoped queries.
- Add tests for account scoping, role checks, and no cross-account leakage.

Acceptance:

- Business reads/writes always require an account context.
- A user from account A cannot see account B's candidates, positions, alerts, or journal entries.
- Existing tests remain green.

### PR 6: Auth Integration

Status: implemented as foundation in this branch. Still needs real Auth0 tenant values and an end-to-end deployed login test.

Goal: replace the current frontend-open dashboard with authenticated sessions.

Tasks:

- Add Auth0 environment variables and backend JWT verification.
- Configure Auth0 access token lifetime to 1800 seconds and refresh-token lifetime to 86400 seconds.
- Configure Auth0 email passwordless OTP and verification-email templates.
- Add `current_user`, `current_account`, and role dependencies.
- Protect business read/write endpoints.
- Keep ingestion writes behind `INGESTION_ADMIN_TOKEN`.
- Add frontend login/logout flow.
- Add protected frontend workspace route.
- Add API client token injection.
- Add 401/403 states in the frontend.
- Add audit logs for sensitive mutations.

Acceptance:

- Anonymous users cannot access dashboard data.
- Authenticated users see only their account data.
- Role restrictions work for read-only vs mutation routes.
- Ingestion admin token is never exposed to the frontend.

### PR 7: Product Workflow Completion

Goal: make the app useful, not just readable.

Tasks:

- Create planned position from candidate.
- Acknowledge or resolve exit alerts.
- Close position and write journal entry.
- Add confirm dialogs for sensitive operations.
- Add seed/demo data for internal beta.

### PR 8: Scheduled Ingestion and Job Status

Goal: make data refresh automatic.

Tasks:

- Add scheduled ingestion command/entrypoint.
- Add Railway cron or GitHub Actions trigger.
- Add job status endpoint.
- Add frontend job/freshness status view.

### PR 9: D3 Analytics

Goal: implement PRD analytics surfaces.

Tasks:

- Aggregate portfolio snapshots.
- Generate daily analytics tables.
- Add equity curve, win rate, PF, expectancy, drawdown, strategy breakdown.
- Add frontend charts.

## Deployment Implication

Do not invite normal users until PR 5 and PR 6 are complete. Railway is still fine for the app and database during this phase; auth does not force a move away from Railway.
