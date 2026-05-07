# EdgePilot

EdgePilot is a manual trading operations cockpit for a small account. It screens US ETF candidates, explains price-action evidence, creates paper/manual trade plans, tracks positions, enforces risk guardrails, raises exit alerts, and records journals.

It does **not** place broker orders. Every entry, trim, stop, and close remains manually confirmed by the user.

## Current Strategy

The current product strategy is v1.5.1:

- Risk Engine, Position Ledger, and Exit Engine are the production foundation.
- Tenant-lite, BYOK, and Data Capability are the private-beta platform foundation.
- CSV execution import, real analytics, shadow mode, and paper validation come before more alpha complexity.
- ETF Trend / Rotation remains the next production alpha line, but should land after the platform and validation base.
- Growth Leader / O'Neil is an upside satellite, not the core engine.
- PA and Strat are execution and structure layers, not standalone trading systems.
- The system remains manual-confirmation only and does not place broker orders.
- Proxy data starts analytics-only; single proxy warnings cannot veto trades.
- Missing proxy data must degrade safely and never crash the scanner.
- Options remain lowest-priority research backlog.
- AI can explain and challenge, but cannot upgrade a trade or override risk.

Authoritative docs:

- `docs/product_strategy_v1_5_1.md`
- `docs/prd_tdd_v1_5_1.md`
- `docs/reference/EdgePilot_PRD_TDD_Implementation_Plan_v1_5_1_Pragmatic_Rollout_Proxy_Robustness.md`

Older standalone roadmap documents were removed after v1.5.1 alignment to avoid conflicting implementation guidance. Historical context is preserved inside the full v1.5.1 archive.

## Current Implementation

Implemented:

- FastAPI backend with account-scoped Auth0/OIDC auth.
- PostgreSQL/Timescale-ready schema with Alembic migrations.
- Polygon/Massive market data ingestion foundation.
- PA facts, PA structures, PA setups, and calibration stats foundation.
- US ETF daily PA facts calculator.
- O'Neil-core US ETF scanner v1.
- Account-scoped candidates linked to PA setups.
- Candidate detail API with scanner decision, score breakdown, entry/exit plan, invalidation, and chart evidence.
- PA Lab setup explorer.
- Scanner outcome review and recalculation.
- Candidate paper/manual plan creation.
- Position lifecycle: planned, open, reduce, closed.
- Journal generation on close.
- Account risk settings and single-trade risk sizing.
- Portfolio risk monitoring.
- Exit alert engine.
- In-app notifications.
- Automation Job Runner.
- Next.js frontend with zh/en/ja i18n.
- Frontend views: Overview, Candidates, PA Lab, Review, Positions, Exit Alerts, Automation, Notifications, Journal, Settings.
- Railway deployment guide and Auth0 setup guide.

## Local Setup

Copy environment files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Start dependencies:

```bash
docker compose up -d
```

Install backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn backend.app.main:app --reload --port 8000
```

Start frontend:

```bash
cd frontend
npm install
npm run dev -- --port 3000
```

Open:

```text
http://localhost:3000/zh
```

## Verification

Backend:

```bash
.venv/bin/pytest backend/tests
.venv/bin/ruff check backend/app backend/tests migrations
.venv/bin/alembic upgrade head
```

Frontend:

```bash
cd frontend
npm run build
```

Diff hygiene:

```bash
git diff --check
```

## Important APIs

Health and dashboard:

- `GET /health`
- `GET /api/dashboard/summary`
- `GET /api/risk/portfolio`

Risk settings:

- `GET /api/settings/risk`
- `PATCH /api/settings/risk`

Candidates:

- `GET /api/candidates`
- `GET /api/candidates/count`
- `GET /api/candidates/{candidate_id}`
- `GET /api/candidates/{candidate_id}/plan`
- `GET /api/candidates/{candidate_id}/plan-preview`
- `POST /api/candidates/{candidate_id}/plan`
- `POST /api/candidates/scanners/us-etf/oneil-core`
- `POST /api/candidates/scanners/us-etf/oneil-core/refresh`

Review:

- `GET /api/candidates/outcomes`
- `GET /api/candidates/outcomes/summary`
- `POST /api/candidates/outcomes/recalculate`

PA:

- `GET /api/pa/facts/{symbol}`
- `GET /api/pa/structures/{symbol}`
- `GET /api/pa/setups`
- `GET /api/pa/setups/{setup_id}`
- `GET /api/pa/setups/{setup_id}/explain`
- `GET /api/pa/calibration`

Positions and exits:

- `GET /api/positions`
- `POST /api/positions`
- `POST /api/positions/{position_id}/activate`
- `POST /api/positions/{position_id}/stop`
- `POST /api/positions/{position_id}/reduce`
- `POST /api/positions/{position_id}/close`
- `GET /api/exit-alerts`
- `POST /api/exit-alerts/evaluate`
- `PATCH /api/exit-alerts/{alert_id}`

Journal:

- `GET /api/journal/trades`
- `POST /api/journal/trades`

## Data Seeding

With `POLYGON_API_KEY` configured, seed the US ETF universe:

```bash
.venv/bin/python scripts/seed_us_etf_pa.py --account-id acct_local --symbols SPY QQQ IWM SMH SOXX
```

Or trigger the account scanner through the authenticated frontend.

Protected ingestion write endpoints require:

```text
X-Ingestion-Admin-Token: <INGESTION_ADMIN_TOKEN>
```

Do not expose this token to the frontend.

## Deployment

Recommended path:

1. Railway staging/internal beta first.
2. Keep AWS migration for later, after MVP usage and operational needs justify it.

Deployment docs:

- `docs/railway_deployment.md`
- `docs/auth0_setup.md`

Before staging:

- Deploy from a reviewed `main` branch.
- Run `alembic upgrade head` on the staging database.
- Configure Auth0 SPA/API.
- Configure backend CORS for the frontend domain.
- Set `DATABASE_URL`, `POLYGON_API_KEY`, `INGESTION_ADMIN_TOKEN`, and Auth0 secrets.
- Smoke test `/health`, authenticated dashboard, candidates, positions, and exit alerts.

## Roadmap

The product roadmap and implementation spec are tracked in:

- `docs/product_strategy_v1_5_1.md`
- `docs/prd_tdd_v1_5_1.md`
- `docs/reference/EdgePilot_PRD_TDD_Implementation_Plan_v1_5_1_Pragmatic_Rollout_Proxy_Robustness.md`
