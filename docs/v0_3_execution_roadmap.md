# v0.3 开发规划（TDD 对齐版）

> Status: historical roadmap. The current product direction is v0.6 Advanced PA Engine.
> Use `docs/v0_6_review_and_next_steps.md` for the next implementation sequence.

## 目标

基于 `trading_assistant_prd_tdd_implementation_plan_v0_3_db_frontend_analytics (1).md`，把项目拆解为可执行里程碑，优先完成：

1. 数据底座（PostgreSQL + TimescaleDB + Redis）
2. 后端 API 基础与可观测健康状态
3. 前端正式技术栈预留（环境变量、API/SSE 接口契约）
4. 统计分析 API 的最小闭环

## 已完成（本次）

- [x] D0: Compose 基础服务（Postgres/Timescale/Redis）
- [x] D0: SQL 初始化脚本（核心业务表 + 时序表）
- [x] Backend 基础 API：`/health`
- [x] Analytics API 占位：`/api/analytics/overview`
- [x] SSE 占位：`/api/realtime/events/stream`
- [x] 环境变量模板（root/backend/frontend）

## 已完成（D1 PR）

- [x] Polygon US ETF 日线抓取并写入 `bars`
- [x] selected underlying options chain 抓取并写入 `options_chain_snapshots`
- [x] market context snapshot 写入 `market_context_snapshots`
- [x] 数据新鲜度写入与查询：`data_freshness`
- [x] 最近 N 根 bar 与最新 options snapshot 查询 API

## 已完成（D2 + F0/F1 PR）

- [x] CRUD/API for `candidates`
- [x] CRUD/API for `positions`
- [x] CRUD/API for `exit_alerts`
- [x] CRUD/API for `trades_journal`
- [x] Dashboard summary API：market context、counts、open alerts、freshness
- [x] Next.js + Tailwind + shadcn-compatible UI scaffold + TanStack Query + Zustand
- [x] Dashboard/Candidates/Positions/Exit Alerts/Journal/Settings 基础页面
- [x] 前端 API client 与 SSE client wrapper

## 下一步开发计划

## Phase D2 后续加强

- 候选/持仓/警报的真实业务流转动作，例如 create planned position、acknowledge alert。
- DB integration tests with Postgres/Timescale.
- 更细的权限模型，替代当前单一 admin token。

## Phase D3（统计）

- 定时聚合 `portfolio_snapshots`
- 生成 `analytics_daily` / `analytics_strategy_daily`
- 扩展 Analytics API：
  - equity curve
  - strategy breakdown
  - asset breakdown
  - options analytics
  - mistakes
- 验收：
  - 前端可展示 win rate / PF / expectancy / drawdown

## Frontend F0-F2（正式栈）

- F0: Next.js + Tailwind + shadcn + TanStack Query + Zustand
- F1: Dashboard/Candidates/Positions/Exit Alerts 页面
- F2: SSE 接入 + cache 局部更新 + 风险 banner

## 环境变量约定

后续所有第三方 key 统一放入环境变量，不写死在代码：

- `POLYGON_API_KEY`
- `JQUANTS_EMAIL`
- `JQUANTS_PASSWORD`
- `OPENAI_API_KEY`
- `REDIS_URL`
- `DATABASE_URL`

并通过 CI/CD secret 或部署平台 secret 注入。
