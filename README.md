# EdgePilot

基于 `docs/edgepilot_prd_tdd_implementation_plan_v0_6_advanced_pa_engine.md` 的交易辅助系统。v0.6 的当前产品重点是 Advanced PA Engine：从市场数据生成 PA facts、结构/位置/量能判断、setup、评分、入场/离场计划，并通过 shadow/paper/live validation gate 控制风险。

## 当前已落地（平台与数据底座）

- Backend FastAPI 基础服务（health、analytics API、realtime SSE 事件流占位、D1 ingestion API、D2 business state API）。
- PostgreSQL + TimescaleDB + Redis 的 `docker-compose` 本地开发环境。
- 时序表和核心业务表 SQL 初始化脚本（D0/D2/D3 核心子集）。
- Alembic baseline migration，供已有数据库升级使用。
- SQLAlchemy 2.0 ORM models/session layer，覆盖 auth、business、ingestion、analytics core tables。
- Auth foundation：JWT/OIDC bearer token verification、users/accounts/memberships、account-scoped business data、role checks、audit logs。
- PA Data Foundation：`pa_facts`、`pa_structures`、`pa_setups`、`pa_calibration_stats` migration/ORM/schemas/read APIs。
- US ETF PA facts calculator 与第一版 O'Neil-core scanner，可从已有 ETF 日线 `bars` 生成 shadow-only PA setups 和第一批 candidates。
- US ETF universe seed 流程：可批量拉 Polygon 日线、计算 PA facts、运行 scanner 并写入 candidates。
- Candidate + PA setup bridge：`candidates.pa_setup_id` 直接关联 `pa_setups`，候选详情 API 可返回 score breakdown、entry/exit/invalidation。
- Next.js + Tailwind + shadcn-compatible UI scaffold + TanStack Query + Zustand 前端工作台。
- 环境变量模板：
  - 根目录 `.env.example`
  - `backend/.env.example`
  - `frontend/.env.example`
- 面向 v0.6 的 PRD/TDD 与下一步实施路线图文档。

## 当前还没有落地

- Polygon ETF universe seed/scheduled job 尚未完成；当前 scanner 从数据库中已有 `bars` 计算 PA facts。
- PA Lab、candidate detail drawer、图表标注、validation/cashflow/analytics 扩展页面尚未实现。
- J-Quants、日本市场 context、Option Adapter、AI PA Reviewer 仍是后续阶段。

## 快速启动

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up -d
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn backend.app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev -- --port 3000
```

## API

- `GET /health`
- `GET /api/analytics/overview?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /api/realtime/events/stream` (SSE mock stream)
- `POST /api/ingestion/bars`
- `POST /api/ingestion/options-chain`
- `POST /api/ingestion/market-context`
- `POST /api/ingestion/us-etf-universe/seed`
- `GET /api/ingestion/bars/{ticker}?timeframe=1d&limit=200`
- `GET /api/ingestion/options-chain/{underlying_symbol}?limit=250`
- `GET /api/ingestion/freshness`
- `GET /api/pa/facts/{symbol}?timeframe=1d&limit=200`
- `GET /api/pa/structures/{symbol}?timeframe=1d&limit=200`
- `GET /api/pa/setups?symbol=&timeframe=1d&setup_type=&status=`
- `GET /api/pa/setups/{setup_id}`
- `GET /api/pa/calibration?setup_type=&market_regime=&timeframe=`
- `POST /api/pa/facts/etf-universe`
- `POST /api/pa/scanners/us-etf/oneil-core`
- `GET /api/dashboard/summary`
- `GET /api/candidates`
- `GET /api/candidates/{candidate_id}`
- `POST /api/candidates`
- `PATCH /api/candidates/{candidate_id}`
- `GET /api/positions`
- `POST /api/positions`
- `PATCH /api/positions/{position_id}`
- `GET /api/exit-alerts`
- `POST /api/exit-alerts`
- `PATCH /api/exit-alerts/{alert_id}`
- `GET /api/journal/trades`
- `POST /api/journal/trades`

Ingestion write endpoints and PA/scanner trigger endpoints require the admin header:

```text
X-Ingestion-Admin-Token: <INGESTION_ADMIN_TOKEN>
```

Business/dashboard endpoints require:

```text
Authorization: Bearer <OIDC access token>
```

Business write endpoints additionally require a role that passes the backend role gate.

## US ETF PA 本地一键 seed

在完成 `alembic upgrade head`、配置 `POLYGON_API_KEY` 且本地存在 `acct_local` 后，可以跑：

```bash
.venv/bin/python scripts/seed_us_etf_pa.py --account-id acct_local --symbols SPY QQQ IWM SMH SOXX
```

也可以通过 API 触发完整流程：

```bash
curl -X POST http://localhost:8000/api/ingestion/us-etf-universe/seed \
  -H "Content-Type: application/json" \
  -H "X-Ingestion-Admin-Token: $INGESTION_ADMIN_TOKEN" \
  -d '{"symbols":["SPY","QQQ","IWM","SMH","SOXX"],"account_id":"acct_local"}'
```

这个流程会依次写入 `bars`、`pa_facts`、`pa_setups`，并将高分 shadow-only setups 映射到 `candidates`。

## 规划阶段

当前产品方向：

- v0.6 PRD/TDD：`docs/edgepilot_prd_tdd_implementation_plan_v0_6_advanced_pa_engine.md`
- v0.6 review and next steps：`docs/v0_6_review_and_next_steps.md`
- v0.3 historical roadmap：`docs/v0_3_execution_roadmap.md`

当前实现已覆盖 `PR B: PA Data Foundation`，并启动 `PR C/PR D` 的第一版本地流程：批量 seed US ETF daily bars，计算 PA facts，运行 O'Neil-core scanner，写入 shadow-only setups 和 account-scoped candidates。

## D1 Ingestion 环境变量

- `POLYGON_API_KEY`（必填）
- `POLYGON_BASE_URL`（默认 `https://api.polygon.io`）
- `INGESTION_ADMIN_TOKEN`（写入接口必填 header：`X-Ingestion-Admin-Token`）
- `CORS_ALLOWED_ORIGINS`（默认 `http://localhost:3000`；部署前端后加入正式域名）
- `AUTH_ISSUER`
- `AUTH_AUDIENCE`
- `AUTH_JWKS_URL`（可选；默认从 issuer 推导 `/.well-known/jwks.json`）
- `AUTH_ACCOUNT_CLAIM`（默认 `https://edgepilot/account_id`）
- `AUTH_ROLE_CLAIM`（默认 `https://edgepilot/role`）
- `AUTH_EMAIL_CLAIM`（默认 `https://edgepilot/email`）
- `AUTH_DISPLAY_NAME_CLAIM`（默认 `https://edgepilot/name`）
- `AUTH_EMAIL_VERIFIED_CLAIM`（默认 `https://edgepilot/email_verified`）
- `AUTH0_MANAGEMENT_CLIENT_ID`（用于重发验证邮件）
- `AUTH0_MANAGEMENT_CLIENT_SECRET`
- `AUTH0_MANAGEMENT_AUDIENCE`

## Frontend Auth 环境变量

- `NEXT_PUBLIC_AUTH0_DOMAIN`
- `NEXT_PUBLIC_AUTH0_CLIENT_ID`
- `NEXT_PUBLIC_AUTH0_AUDIENCE`
- `NEXT_PUBLIC_AUTH0_REDIRECT_URI`
- `NEXT_PUBLIC_AUTH0_CONNECTION`（默认留空，使用 Auth0 Database 邮箱 + 密码登录）

## 部署

- Railway 部署说明：`docs/railway_deployment.md`
- Auth0 设置说明：`docs/auth0_setup.md`
- 后端镜像：根目录 `Dockerfile`
- Railway 配置：根目录 `railway.toml`
- CI：`.github/workflows/ci.yml`
