# Railway Deployment Guide

## What This Deploys

This deployment publishes the FastAPI backend and can be paired with the Next.js frontend in `frontend/`.

After backend deployment you can show technical users:

- `/health`
- `/docs`
- read-only ingestion query endpoints
- the Next.js dashboard once the frontend is deployed and pointed at the backend URL

Keep all write endpoints protected with `INGESTION_ADMIN_TOKEN`.

## Services

Create these Railway services:

1. Backend from this GitHub repository.
2. TimescaleDB using a Railway TimescaleDB template or compatible Postgres service with TimescaleDB enabled.
3. Redis, optional for the current heartbeat-only SSE stream but recommended before realtime features expand.

## Console Walkthrough

### 1. Create the backend service

On the Railway `New Project` page:

1. Click `GitHub Repository`.
2. Select `WWK563388548/EdgePilot`.
3. Railway should detect the root `Dockerfile`.
4. Name the service `edgepilot-backend`.

Do not choose `Function`. EdgePilot backend is a long-running FastAPI web service, not a serverless function.

### 2. Create TimescaleDB

From the project canvas:

1. Click `+ New`.
2. Click `Template`.
3. Search for `TimescaleDB`.
4. Choose a TimescaleDB/PostgreSQL 16 template.
5. Rename the service to `TimescaleDB` if Railway lets you rename it.

Do not use plain PostgreSQL for the MVP unless TimescaleDB is enabled. The schema uses `CREATE EXTENSION IF NOT EXISTS timescaledb` and hypertables.

### 3. Create Redis

From the project canvas:

1. Click `+ New`.
2. Click `Database`.
3. Choose `Redis`.
4. Rename the service to `Redis` if Railway lets you rename it.

Redis is optional for the current heartbeat-only SSE stream, but adding it now keeps the environment close to the planned production shape.

## Backend Configuration

Railway will use:

- `Dockerfile` for the image build.
- `railway.toml` for the start command and health check.
- `scripts/start_backend.sh` to run `alembic upgrade head` and then start Uvicorn.

Set these environment variables on the backend service:

```text
APP_ENV=staging
APP_NAME=EdgePilot Backend
POLYGON_API_KEY=<Polygon/Massive API key>
POLYGON_BASE_URL=https://api.polygon.io
INGESTION_ADMIN_TOKEN=<long random token>
SSE_HEARTBEAT_SECONDS=15
CORS_ALLOWED_ORIGINS=http://localhost:3000
AUTH_ISSUER=https://<auth0-domain>/
AUTH_AUDIENCE=<auth0-api-audience>
AUTH_ALGORITHMS=RS256
AUTH_ACCOUNT_CLAIM=https://edgepilot/account_id
AUTH_ROLE_CLAIM=https://edgepilot/role
AUTH_DEFAULT_ROLE=owner
AUTH0_MANAGEMENT_CLIENT_ID=<auth0-m2m-client-id>
AUTH0_MANAGEMENT_CLIENT_SECRET=<auth0-m2m-client-secret>
AUTH0_MANAGEMENT_AUDIENCE=https://<auth0-domain>/api/v2/
DATABASE_URL=${{ TimescaleDB.DATABASE_URL }}
REDIS_URL=${{ Redis.REDIS_URL }}
```

Do not expose `INGESTION_ADMIN_TOKEN` to frontend users.

### Auth0 backend values

For Auth0:

- `AUTH_ISSUER` is usually `https://<tenant-domain>/`.
- `AUTH_AUDIENCE` must match the API identifier configured in Auth0.
- `AUTH_JWKS_URL` can be omitted unless the issuer cannot be used to derive `/.well-known/jwks.json`.
- Custom claims can set account and role:
  - `https://edgepilot/account_id`
  - `https://edgepilot/role`

If no account claim is present, the backend creates a personal account from the JWT subject. That is safer for beta usage because users do not share data accidentally.

Token lifetime requirements live in Auth0, not Railway:

- Set the API access token lifetime to `1800` seconds.
- Enable Refresh Token Rotation for the SPA.
- Set refresh token absolute lifetime to `86400` seconds.
- Enable an Auth0 Database connection for the SPA for the first email/password login flow.

See `docs/auth0_setup.md` for the full Auth0 checklist.

### Where DATABASE_URL and REDIS_URL come from

Railway database services expose connection variables automatically.

- The TimescaleDB/Postgres service exposes `DATABASE_URL`.
- The Redis service exposes `REDIS_URL`.

On the backend service, set reference variables instead of copy-pasting long connection strings:

```text
DATABASE_URL=${{ TimescaleDB.DATABASE_URL }}
REDIS_URL=${{ Redis.REDIS_URL }}
```

If your service names differ, use the actual Railway service names. For example:

```text
DATABASE_URL=${{ Postgres.DATABASE_URL }}
REDIS_URL=${{ edgepilot-redis.REDIS_URL }}
```

When typing `${{` in Railway's variable editor, Railway usually opens an autocomplete dropdown with available service variables.

### How to create INGESTION_ADMIN_TOKEN

`INGESTION_ADMIN_TOKEN` is a private admin key for write endpoints. It prevents public users from triggering Polygon API calls or writing data.

Generate it locally:

```bash
openssl rand -hex 32
```

Example shape:

```text
INGESTION_ADMIN_TOKEN=9f4a7e4c0b7a0f7c3f1e6d...
```

Use the full generated value in Railway. Do not commit it, paste it into frontend code, or show it to users.

Protected write requests must include:

```text
X-Ingestion-Admin-Token: <INGESTION_ADMIN_TOKEN>
```

## Deployment Steps

1. Create a Railway project.
2. Add the backend service from `GitHub Repository`.
3. Add the TimescaleDB service from `Template`.
4. Add Redis from `Database`.
5. Open the backend service's `Variables` tab.
6. Add the variables listed above.
7. Review and deploy the staged variable changes.
8. Generate a public domain for the backend service.
9. Visit `https://<domain>/health`.
10. Visit `https://<domain>/docs` for Swagger.

## Frontend Deployment

The frontend is a separate Next.js app in `frontend/`.

For the quickest user-facing demo:

1. Deploy the backend on Railway first.
2. Copy the backend public domain, for example `https://edgepilot-backend.up.railway.app`.
3. Deploy the frontend to Vercel, or create a second Railway service from the same GitHub repo with root directory `frontend`.
4. Set these frontend variables:

```text
NEXT_PUBLIC_API_BASE_URL=https://<backend-domain>
NEXT_PUBLIC_SSE_URL=https://<backend-domain>/api/realtime/events/stream
NEXT_PUBLIC_APP_NAME=EdgePilot
NEXT_PUBLIC_AUTH0_DOMAIN=<auth0-domain>
NEXT_PUBLIC_AUTH0_CLIENT_ID=<auth0-spa-client-id>
NEXT_PUBLIC_AUTH0_AUDIENCE=<auth0-api-audience>
NEXT_PUBLIC_AUTH0_REDIRECT_URI=https://<frontend-domain>
NEXT_PUBLIC_AUTH0_CONNECTION=
```

5. Add the frontend domain to the backend service variable:

```text
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://<frontend-domain>
```

6. Redeploy the backend after changing `CORS_ALLOWED_ORIGINS`.

Do not put `INGESTION_ADMIN_TOKEN` in frontend variables. The current frontend only reads data.

## Smoke Test

Read-only:

```bash
curl https://<domain>/health
curl https://<domain>/api/ingestion/freshness
```

Protected write endpoint:

```bash
curl -X POST https://<domain>/api/ingestion/market-context \
  -H "Content-Type: application/json" \
  -H "X-Ingestion-Admin-Token: <INGESTION_ADMIN_TOKEN>" \
  -d '{"spy_return": 0.01, "risk_level": "normal"}'
```

## Can This Be Shown To Users?

For internal or technical users: yes, after `/health` and `/docs` work and the write token is configured.

For normal end users: yes for a small beta demo after the frontend is deployed and the backend has real or seed data. Treat it as an internal beta, not public production, because auth is still a single admin token and the app does not yet have per-user accounts.

Recommended demo order:

1. Show `/health` as deployment proof.
2. Show `/docs` as API proof.
3. Trigger a protected market-context write.
4. Show freshness/read endpoints.
5. Open the Next.js dashboard and check Overview, Candidates, Positions, Exit Alerts, Journal, and Settings.

## Railway vs Tiger Data

You can stay on Railway for the MVP. Railway is the right default for the current stage because it keeps backend, database, Redis, environment variables, and deploys in one small operational surface.

Tiger Data/Tiger Cloud is a future option, not a mandatory next step. Revisit it when the workload becomes database-heavy enough that managed time-series features matter more than platform simplicity:

- large bars/options history and heavier analytics queries;
- compression, retention, hypertable tuning, continuous aggregates, and time-series observability become daily concerns;
- stronger database operations are needed, such as high availability, point-in-time recovery, cross-region posture, and specialist support;
- you want the app platform and database lifecycle separated.

Railway also has volume backups, so this is not an urgent migration. The practical plan is: ship the MVP on Railway, measure data volume/cost/query latency, and only move the database to Tiger if those numbers justify it.
