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

## Backend Configuration

Railway will use:

- `Dockerfile` for the image build.
- `railway.toml` for the start command and health check.
- `scripts/start_backend.sh` to run `alembic upgrade head` and then start Uvicorn.

Set these environment variables on the backend service:

```text
APP_ENV=staging
APP_NAME=EdgePilot Backend
DATABASE_URL=<Railway TimescaleDB connection URL>
REDIS_URL=<Railway Redis connection URL>
POLYGON_API_KEY=<Polygon/Massive API key>
POLYGON_BASE_URL=https://api.polygon.io
INGESTION_ADMIN_TOKEN=<long random token>
SSE_HEARTBEAT_SECONDS=15
```

Do not expose `INGESTION_ADMIN_TOKEN` to frontend users.

## Deployment Steps

1. Create a Railway project.
2. Add the TimescaleDB service first.
3. Add the backend service from GitHub.
4. Confirm Railway detects and uses the root `Dockerfile`.
5. Add the backend environment variables.
6. Deploy the backend.
7. Generate a public domain for the backend service.
8. Visit `https://<domain>/health`.
9. Visit `https://<domain>/docs` for Swagger.

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
