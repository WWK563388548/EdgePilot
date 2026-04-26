# Railway Deployment Guide

## What This Deploys

This deployment publishes the FastAPI backend. It can show API health and Swagger docs, but it is not yet an end-user product UI. General users should wait for the frontend milestone.

After deployment you can show technical users:

- `/health`
- `/docs`
- read-only ingestion query endpoints

Keep write endpoints protected with `INGESTION_ADMIN_TOKEN`.

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
DATABASE_URL=${{ TimescaleDB.DATABASE_URL }}
REDIS_URL=${{ Redis.REDIS_URL }}
```

Do not expose `INGESTION_ADMIN_TOKEN` to frontend users.

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

For normal end users: not yet. The current app is an API backend. A user-facing demo still needs the frontend milestone: dashboard, candidates, positions, exit alerts, and freshness/status UI.

Recommended demo order:

1. Show `/health` as deployment proof.
2. Show `/docs` as API proof.
3. Trigger a protected market-context write.
4. Show freshness/read endpoints.
5. Build the Next.js frontend before sharing with non-technical users.
