# EdgePilot

基于 `docs/trading_assistant_prd_tdd_implementation_plan_v0_3_db_frontend_analytics (1).md` 的首版落地骨架。

## 当前已落地（D0 + F0 启动）

- Backend FastAPI 基础服务（health、analytics API、realtime SSE 事件流占位）。
- PostgreSQL + TimescaleDB + Redis 的 `docker-compose` 本地开发环境。
- 时序表和核心业务表 SQL 初始化脚本（D0/D2/D3 核心子集）。
- 环境变量模板：
  - 根目录 `.env.example`
  - `backend/.env.example`
  - `frontend/.env.example`
- 面向 v0.3 的分阶段实施路线图文档。

## 快速启动

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up -d
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn backend.app.main:app --reload --port 8000
```

## API

- `GET /health`
- `GET /api/analytics/overview?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /api/realtime/events/stream` (SSE mock stream)

## 规划阶段

详见：`docs/v0_3_execution_roadmap.md`

