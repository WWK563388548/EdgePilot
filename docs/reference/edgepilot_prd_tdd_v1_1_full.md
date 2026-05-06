
# PRD + 技术设计文档 + 实现计划  
## 小资金交易辅助系统：美股/美股ETF + 日股候选 + Strat PA + 做空研究框架 + 期权最低优先级版

**版本**：v1.1  
**日期**：2026-05-04
**v0.2 更新重点**：追加前端实时 Dashboard、WebSocket/SSE 数据流、页面设计、组件设计、前端状态管理与实现计划。
**v0.3 更新重点**：明确正式前端技术栈、数据库选型、时序数据设计、统计分析面板、Analytics API 与实现计划。
**v0.4 更新重点**：追加 EdgePilot 动态现金流目标系统，包括 Cashflow Target Engine、目标阶梯、税后现金流、月度锁利、目标可行性、Profit Sweep、Rolling 12M Cashflow Analytics 与相关数据库/API/前端设计。
**v0.5 更新重点**：追加 Testing & Validation Engine，包括数据质量门禁、ETF-only 回测、Shadow Mode、Paper Trading、Micro Live、Go-Live Gate、Signal Funnel、Setup Quality Calibration、MFE/MAE、策略熔断、执行风险与相关数据库/API/前端页面。
**v0.6 更新重点**：将 PA 从基础 setup 升级为完整 Advanced PA Engine，一次性定义 PA Facts、Structure、Location、Volume、Context、Entry、Exit、Calibration、AI Review、数据库、API、前端与测试门禁。
**v0.7 更新重点**：追加 Anti-Overfitting Governance，将所有模块按 Production Decision、Risk-only、Research-only、Analytics-only 分类；限制实盘决策因子；引入 Decision Rights Registry、Parameter Budget、Walk-forward、Ablation Test、Baseline Comparison、Promotion Gate 与 Engine Influence Audit，防止系统复杂度导致过拟合。  
**v0.8 更新重点**：进行 Priority Reset，将所有期权相关功能降为最低优先级，默认从 MVP 和实盘链路中移除；期权、0DTE、covered call、iron condor、iron butterfly、tail hedge、beta-weighted delta 等仅保留为 Research-only / Paper-only backlog。新增 Engine Minimalism Rule，明确“写进研究文档 ≠ 要实现进产品”，避免 engine 膨胀导致过拟合。  
**v0.9 更新重点**：追加 Strat Trigger Layer，将 Strat 作为 PA Engine 的程序化触发层，而不是独立交易系统；将 Advanced PA 从后期 backlog 拆分为 Basic PA、PA/Strat Calibration、Advanced PA v1；追加 Short Capability Framework，默认系统仍为 long-biased，做空仅先支持 Bearish Context、Short Watchlist 和 Paper Short，live short 默认关闭；继续保持期权最低优先级，防止过拟合和 engine 膨胀。  
**v1.0 更新重点**：重构 Alpha Strategy 架构，将 ETF Trend/Rotation 设为第一生产线，Earnings Drift/Revision 设为第二生产线，O’Neil/Growth Leader 设为弹性层；新增 Short Capability Framework v2，支持 Bearish Context、Short Watchlist、Paper Short、Inverse ETF Alternative、Live Short Gate；明确 Options 仍最低优先级，Short Options 永久禁止，做空默认不实盘。
**v1.1 更新重点**：追加 Dynamic Milestone / First $100K Compounding Plan 与 Multi-User SaaS / Auth / Tenant Isolation。系统允许其他用户使用，但必须保持非投顾、非自动交易、数据授权合规、租户隔离、审计和权限控制；默认仍以独立交易账户复利、ETF/大票、PA/Strat、Exit Engine 为主线，Options 保持最低优先级。
**目标用户**：日本居住的个人投资者  
**核心原则**：不自动交易；系统只做筛选、计划、持仓管理、离场提醒和复盘；最终由用户手动确认与下单。

---

## 0. 一句话定义

本系统是一个**多资产交易辅助系统**：

> 用规则化策略先筛选美股、美股ETF、日股、日股ETF，再用 **PA Engine = Structure PA + Strat Trigger Layer** 生成可执行的入场、止损和失效条件；系统默认 long-biased，bearish/short 信号先用于避开多头、降低风险和 paper short 研究；持仓后由 Exit Engine 持续监控离场条件；期权相关功能保持最低优先级，默认不进入 MVP 和实盘链路；AI 只做结构化复核和解释，不直接决定交易。

---

## 1. 背景与约束

### 1.1 用户真实约束

用户当前情况：

- 人在日本。
- 初始交易资金约 **1000–2000 USD**。
- 每月追加约 **1万–2万日元**。
- 大头资产仍然放在 **NISA 和储蓄**。
- 不想做自动交易。
- 不想让 TradingView 进入项目数据链；TradingView 只用于个人最终复核。
- 已有 **Polygon/Massive API**，用于美股、美股ETF、美股期权数据。
- 日本 moomoo OpenAPI 禁用，不能作为系统数据源。
- 关注日股盈利，但也可以做美股。
- 期权感兴趣，但必须控制风险。
- 希望尽量减少自己看图，由系统给出最终候选、交易计划和离场提示。

### 1.2 系统设计原则

系统必须遵守以下原则：

1. **不自动下单**
   - 系统不连接交易执行接口。
   - 系统不发 broker order。
   - 所有买入、卖出、减仓、止损由用户手动执行。

2. **先保护本金，再追求收益**
   - 初始账户太小，不适合重仓期权或高频交易。
   - 每笔交易必须有最大可接受亏损。
   - 账户回撤超过阈值后自动降风险或停止实盘。

3. **离场优先**
   - 只有 Scanner 没有 Position Ledger 和 Exit Engine 的系统，只是选股器，不是交易系统。
   - 每笔交易必须记录入场理由、失效条件、初始止损、当前止损、离场规则。

4. **期权是表达层，不是筛选层**
   - 不从期权异动开始找交易。
   - 先筛 underlying，再判断是否适合用期权表达。
   - 小账户下，期权仓位必须极小。

5. **AI 不直接做交易决策**
   - AI 不预测涨跌。
   - AI 不直接输出“买/卖”作为唯一依据。
   - AI 只基于结构化数据做解释、反证、风险总结、计划格式化。

---

## 2. 产品需求文档（PRD）

## 2.1 产品目标

### 核心目标

构建一个可以长期迭代的交易辅助系统，帮助用户：

- 自动筛选高质量美股、美股ETF、日股、日股ETF候选。
- 自动生成 PA 入场计划。
- 自动记录持仓。
- 自动提示止损、止盈、减仓、移动止损、时间止损。
- 自动复盘每笔交易。
- 减少人工看图时间。
- 避免冲动交易和过度交易。
- 后期在系统已经通过验证后，才研究性判断期权是否适合表达某个 underlying 交易机会。期权不属于当前 MVP 核心目标。

### 非目标

系统第一版明确不做：

- 自动交易。
- 高频交易。
- 全市场订单簿扫描。
- 0DTE 期权策略。
- 裸卖期权。
- 小盘妖股追涨。
- 财报彩票。
- 通过 AI 预测特朗普、央行或突发新闻。
- 保证盈利。

---

## 2.2 用户故事

### Story 1：每日候选生成

作为用户，我希望系统每天自动输出美股/ETF候选，让我不用自己翻几百张图。

**输入**：

- 美股日线、60分钟、15分钟数据。
- ETF 数据。
- 市场环境数据。

**输出**：

- Top candidates。
- Setup 类型。
- 入场触发价。
- 止损价。
- 无效条件。
- 是否适合期权。
- 是否只观察。

---

### Story 2：日股候选生成

作为用户，我希望系统结合前一晚美股、美元日元、风险偏好，筛选今天值得关注的日股。

**输入**：

- J-Quants 日股日线/财务数据。
- 美股隔夜数据。
- 日股分足/Tick 数据，后续阶段。
- 可选 IBKR L1/L2 盘口数据，仅最终候选。

**输出**：

- 日股候选列表。
- 美股隔夜影响评分。
- 板块偏向。
- 开盘后是否允许交易。
- 是否需要等待 opening range / VWAP 确认。

---

### Story 3：期权适配

作为用户，我希望系统判断某个股票/ETF机会是否适合用期权表达，而不是让我盲目买 call/put。

**输入**：

- underlying 信号。
- 期权链。
- IV、Greeks、bid/ask spread、volume、open interest。
- 事件风险。

**输出**：

- 不适合期权。
- 适合现货/ETF。
- 可用小仓 call/put。
- 可用 debit spread。
- 避免短期期权。
- 期权止损/止盈/时间止损规则。

---

### Story 4：持仓管理和离场提醒

作为用户，我希望系统每天/盘中告诉我已有仓位应该继续持有、减仓、止损还是退出。

**输入**：

- 当前持仓记录。
- 当前价格数据。
- 市场环境变化。
- underlying 结构变化。
- 期权 DTE / IV / premium 变化。

**输出**：

- Hold。
- Watch。
- Tighten Stop。
- Reduce。
- Exit。
- 具体原因。
- 新止损价。
- 是否达到 +1R/+2R/+3R。
- 是否触发时间止损。
- 是否触发期权离场规则。

---

### Story 5：复盘

作为用户，我希望系统自动记录每笔交易表现，帮我判断到底哪些策略真的赚钱。

**输出指标**：

- 胜率。
- 平均盈利。
- 平均亏损。
- 平均 R。
- 最大回撤。
- 连续亏损次数。
- setup 类型表现。
- ETF vs 个股表现。
- 现货 vs 期权表现。
- 提前卖出/止损太晚/入场太晚等错误标签。

---

## 2.3 MVP 范围（v0.9 调整）

### MVP 资产范围

第一阶段优先级，v0.9 调整后：

1. 美股 ETF。
2. 美股大盘股/高流动性强势股。
3. Position Ledger + Exit Engine。
4. Paper Trading + Journal + Analytics。
5. **Basic PA + Strat bar labeling**，作为早期核心，不再放到后期。
6. **PA / Strat Calibration Lab**，用于验证哪些 setup 真正有 edge。
7. 日股 Prime 高流动性股票，作为第二阶段。
8. 日股 ETF，作为第二阶段。
9. **Short Watchlist / Paper Short**，只作为风控与研究能力，不进入 MVP live。
10. 期权相关功能，最低优先级，仅作为后期 Research-only / Paper-only backlog，不进入 MVP 实盘链路。

### MVP 周期

- 周线：趋势背景。
- 日线：主筛选。
- 60分钟：结构确认。
- 15分钟/30分钟：提醒触发，不做高频。

### MVP 策略

- O’Neil-core / CANSLIM-lite。
- ETF 动量轮动。
- Structure PA：突破、回踩、VWAP reclaim、Opening Range、failed breakdown reclaim。
- Strat Trigger Layer：1 / 2U / 2D / 3 bar state、inside breakout、2-1-2、3-1-2、多周期方向一致性。
- Headline Risk 降级。
- Exit Engine。
- Bearish Context：只用于 avoid long、tighten stop、reduce、exit，不直接生成 live short。
- Option Adapter 暂不进入 MVP；继续作为最低优先级 Research-only / Paper-only backlog。

### v0.9 明确不进入 MVP live 的内容

```text
1. Live short stock / ETF。
2. Short options。
3. 0DTE。
4. Covered call。
5. Iron condor / iron butterfly。
6. Tail hedge。
7. AI chart interpretation。
8. 全套 TheStrat pattern library。
9. Order flow / volume profile / 复杂 liquidity sweep 自动识别。
```

---

## 3. 数据源方案

## 3.1 美股 / 美股 ETF / 美股期权

### 主数据源：Polygon/Massive

用途：

- 美股全市场日线。
- 美股 ETF 日线。
- 60分钟 / 15分钟 aggregates。
- 美股期权链。
- Options Greeks / IV / volume / open interest / bid/ask。
- 美股指数/ETF代理市场环境。
- USDJPY / DXY / 利率 proxy，取决于订阅计划和可用 endpoint。

建议使用的数据：

- Stocks grouped daily。
- Stocks aggregates。
- Ticker details。
- Financials，Phase 2 使用。
- Options chain snapshot。
- Options quotes/trades。
- Indices/Forex 数据，如果订阅支持。

系统默认不使用 TradingView API，也不抓 TradingView 数据。

---

## 3.2 日股

### 主数据源：J-Quants

用途：

- 日股日线 OHLCV。
- 上市公司列表。
- 财务信息。
- 决算日。
- TOPIX / 指数数据。
- 信用交易。
- 空卖相关数据。
- 分足 / Tick add-on，后续用于减少人工看图。

推荐套餐：

- **MVP 日线版**：J-Quants Standard。
- **减少看图版**：J-Quants Standard + 分足/Tick add-on。
- **暂不建议**：Premium，除非需要更完整 BS/PL/CF、前场四本值、衍生品历史等。

### 辅助数据源：IBKR L1/L2

用途：

- 只对最终少数日股候选做盘口确认。
- 不做全市场订单簿扫描。
- 不做高频 order flow 策略。

使用方式：

- 先由 J-Quants 选出 20–100 只候选。
- 再由系统缩小到 3–10 只重点候选。
- 仅对重点候选打开 L1/L2。

---

## 3.3 TradingView

TradingView 不进入项目数据链。

允许使用：

- 人工看图确认。
- 用户自己设置 alert。
- 最终候选复核。

不允许使用：

- 抓取 TradingView 后台数据。
- 批量爬取 K 线。
- 依赖 TradingView 作为数据库。

---

## 4. 系统总体架构

```text
Data Sources
├── Polygon/Massive
│   ├── US stocks
│   ├── US ETFs
│   ├── US options
│   ├── market proxies
│   └── forex/index data if available
│
├── J-Quants
│   ├── JP stocks EOD
│   ├── JP financials
│   ├── JP listed info
│   ├── TOPIX / index data
│   ├── margin / short selling
│   └── minute/tick add-on
│
├── IBKR API, optional
│   ├── JP L1
│   └── JP L2 for top candidates only
│
└── Manual Inputs
    ├── actual positions
    ├── executions
    ├── watchlist overrides
    └── user notes

Data Ingestion
    ↓
Raw Data Store
    ↓
Normalized Market Data
    ↓
Feature Builder
    ↓
Strategy Scanners
    ├── O’Neil-core scanner
    ├── ETF rotation scanner
    ├── Market regime scanner
    ├── Japan overnight impact scanner
    └── Headline risk scanner
    ↓
PA Engine
    ├── Structure PA Layer
    ├── Strat Trigger Layer
    ├── Bearish Context Layer
    └── PA / Strat Calibration Layer
    ↓
Risk Engine
    ├── Long Risk Guard
    ├── Short Risk Guard, paper-first
    └── Direction Permission Gate
    ↓
Decision Layer
    ├── Long Candidate
    ├── Watch / Avoid
    ├── Short Watchlist, paper only by default
    └── No Trade
    ↓
AI Reviewer, explanation-only
    ↓
Position Ledger
    ↓
Exit Engine
    ↓
Alerts / Dashboard / Reports

Options Backlog, disabled by default
    └── Research-only / Paper-only, not in MVP live path
```

---

## 5. 技术栈建议

## 5.1 后端

建议：

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Polars 或 pandas
- DuckDB：本地快速分析。
- PostgreSQL：长期持久化。
- APScheduler / Prefect：任务调度。
- Redis：可选，用于缓存和任务队列。
- httpx：API 客户端。
- pytest：测试。
- ruff / mypy：质量控制。

MVP 可以先用：

```text
Python + DuckDB + FastAPI + Streamlit
```

成熟后升级为：

```text
Python + PostgreSQL + FastAPI + Next.js
```

---

## 5.2 前端

MVP：

- Streamlit。
- 或 FastAPI + simple HTML dashboard。

正式版：

- Next.js。
- React Table。
- Lightweight Charts / Plotly。
- Dashboard tabs：
  - Candidates。
  - Open Positions。
  - Exit Alerts。
  - Watchlist。
  - Backtest。
  - Journal。
  - Settings。

---

## 5.3 通知

MVP：

- Email。
- LINE Notify 替代方案。
- Telegram bot。
- Discord webhook。
- Local desktop notification。

通知分级：

- Info。
- Watch。
- Action required。
- Exit now。
- Risk halt。

---

## 6. 数据模型设计

## 6.1 symbols

```sql
CREATE TABLE symbols (
    symbol_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    market TEXT NOT NULL,         -- US, JP
    asset_type TEXT NOT NULL,     -- stock, etf, option, index, forex
    exchange TEXT,
    name TEXT,
    sector TEXT,
    industry TEXT,
    currency TEXT,
    active BOOLEAN DEFAULT TRUE,
    source TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 6.2 bars

```sql
CREATE TABLE bars (
    symbol_id TEXT NOT NULL,
    timeframe TEXT NOT NULL,      -- 1d, 1h, 30m, 15m, 1m
    ts TIMESTAMP NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    vwap DOUBLE,
    adjusted BOOLEAN DEFAULT FALSE,
    source TEXT,
    PRIMARY KEY (symbol_id, timeframe, ts)
);
```

---

## 6.3 fundamentals

```sql
CREATE TABLE fundamentals (
    symbol_id TEXT NOT NULL,
    period_end DATE NOT NULL,
    fiscal_period TEXT,           -- Q1, Q2, Q3, Q4, FY
    revenue DOUBLE,
    operating_income DOUBLE,
    net_income DOUBLE,
    eps DOUBLE,
    roe DOUBLE,
    gross_margin DOUBLE,
    operating_margin DOUBLE,
    debt_to_equity DOUBLE,
    source TEXT,
    updated_at TIMESTAMP,
    PRIMARY KEY (symbol_id, period_end, fiscal_period)
);
```

---

## 6.4 options_chain_snapshots

```sql
CREATE TABLE options_chain_snapshots (
    snapshot_ts TIMESTAMP NOT NULL,
    underlying_symbol TEXT NOT NULL,
    option_symbol TEXT NOT NULL,
    expiration DATE NOT NULL,
    strike DOUBLE NOT NULL,
    option_type TEXT NOT NULL,     -- call, put
    bid DOUBLE,
    ask DOUBLE,
    mid DOUBLE,
    last DOUBLE,
    volume DOUBLE,
    open_interest DOUBLE,
    iv DOUBLE,
    delta DOUBLE,
    gamma DOUBLE,
    theta DOUBLE,
    vega DOUBLE,
    dte INTEGER,
    spread_pct DOUBLE,
    source TEXT,
    PRIMARY KEY (snapshot_ts, option_symbol)
);
```

---

## 6.5 market_context

```sql
CREATE TABLE market_context (
    date DATE PRIMARY KEY,
    spy_return DOUBLE,
    qqq_return DOUBLE,
    iwm_return DOUBLE,
    smh_return DOUBLE,
    soxx_return DOUBLE,
    vix_change DOUBLE,
    usdjpy_change DOUBLE,
    dxy_change DOUBLE,
    us10y_change DOUBLE,
    nikkei_futures_change DOUBLE,
    topix_return DOUBLE,
    japan_bias TEXT,              -- bullish, neutral, bearish
    us_bias TEXT,
    risk_level TEXT,              -- normal, watch, shock
    notes TEXT
);
```

---

## 6.6 candidates

```sql
CREATE TABLE candidates (
    candidate_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    scan_date DATE NOT NULL,
    strategy_name TEXT NOT NULL,
    setup_type TEXT,
    score_total DOUBLE,
    score_strategy DOUBLE,
    score_pa DOUBLE,
    score_context DOUBLE,
    score_risk DOUBLE,
    entry_trigger DOUBLE,
    preferred_entry DOUBLE,
    initial_stop DOUBLE,
    invalidation TEXT,
    decision TEXT,                -- candidate, watch, avoid
    option_suitability TEXT,      -- none, low, medium, high
    ai_review_json TEXT,
    created_at TIMESTAMP
);
```

---

## 6.7 positions

```sql
CREATE TABLE positions (
    position_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    strategy_name TEXT,
    entry_date TIMESTAMP,
    entry_price DOUBLE,
    quantity DOUBLE,
    notional DOUBLE,
    initial_stop DOUBLE,
    current_stop DOUBLE,
    risk_per_unit DOUBLE,
    initial_risk_amount DOUBLE,
    entry_reason TEXT,
    invalidation TEXT,
    planned_holding_period TEXT,
    status TEXT,                  -- open, reduce, exit_pending, closed
    current_r DOUBLE,
    realized_pnl DOUBLE,
    unrealized_pnl DOUBLE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 6.8 option_positions

```sql
CREATE TABLE option_positions (
    position_id TEXT PRIMARY KEY,
    underlying_symbol TEXT NOT NULL,
    option_symbol TEXT NOT NULL,
    option_type TEXT,
    strike DOUBLE,
    expiration DATE,
    dte_at_entry INTEGER,
    premium_entry DOUBLE,
    delta_entry DOUBLE,
    iv_entry DOUBLE,
    spread_pct_entry DOUBLE,
    max_loss DOUBLE,
    underlying_entry DOUBLE,
    underlying_stop DOUBLE,
    option_exit_rule TEXT
);
```

---

## 6.9 exit_alerts

```sql
CREATE TABLE exit_alerts (
    alert_id TEXT PRIMARY KEY,
    position_id TEXT NOT NULL,
    alert_ts TIMESTAMP,
    level INTEGER,                -- 0 hold, 1 watch, 2 tighten, 3 reduce, 4 exit
    action TEXT,
    reason TEXT,
    new_stop DOUBLE,
    triggered_rules TEXT,
    acknowledged BOOLEAN DEFAULT FALSE
);
```

---

## 6.10 trades_journal

```sql
CREATE TABLE trades_journal (
    trade_id TEXT PRIMARY KEY,
    position_id TEXT,
    symbol_id TEXT,
    entry_ts TIMESTAMP,
    exit_ts TIMESTAMP,
    entry_price DOUBLE,
    exit_price DOUBLE,
    quantity DOUBLE,
    gross_pnl DOUBLE,
    net_pnl DOUBLE,
    r_multiple DOUBLE,
    setup_type TEXT,
    exit_reason TEXT,
    mistake_tags TEXT,
    notes TEXT
);
```

---

## 7. 核心模块设计

## 7.1 O’Neil-core Scanner

### 目标

找出强势、流动性好、有趋势、有量价支撑的股票或 ETF。

### 第一版不做完整 CAN SLIM 的原因

完整 CAN SLIM 需要：

- 当前季度 EPS 增长。
- 年度盈利增长。
- 新产品/新催化。
- 股本供需。
- 龙头强度。
- 机构持仓。
- 大盘方向。

这些可以逐步加入，但 MVP 先实现交易上最关键的部分：

- 相对强度。
- 趋势。
- 52周高点。
- 成交量。
- 平台整理。
- 市场环境。

### MVP 评分

总分 100：

```text
Trend Score: 25
Relative Strength Score: 25
Volume/Liquidity Score: 15
Base/Setup Score: 15
Market Context Score: 10
Fundamental Lite Score: 10
```

### 规则示例

```text
Trend:
- close > 50MA > 200MA
- 20MA upward slope
- close within 15% of 52w high

Relative Strength:
- 3M return rank vs universe
- 6M return rank vs universe
- relative return vs SPY/TOPIX

Volume:
- ADV threshold
- breakout day volume > 1.5x 20D volume
- pullback volume contraction

Base:
- base length 10–60 trading days
- base depth < 20%
- volatility contraction

Market:
- US market regime not bearish
- Japan overnight score not bearish for JP stocks

Fundamental Lite:
- revenue growth positive
- operating income growth positive
- no imminent earnings risk
```

---

## 7.2 ETF Rotation Scanner

### 目标

找出当前强势 ETF 和行业主线。

### Universe

美股 ETF：

```text
SPY, QQQ, IWM, DIA,
SMH, SOXX, XLK, XLF, XLE, XLI, XLY, XLP, XLU, XLV,
TLT, HYG, LQD, GLD, SLV, USO
```

日股 ETF：

```text
Nikkei 225 ETF
TOPIX ETF
JP sector ETFs, if data available
```

### 评分

```text
1M momentum: 20
3M momentum: 25
6M momentum: 20
trend score: 20
relative strength vs benchmark: 15
```

输出：

- Leading ETF。
- Improving ETF。
- Weakening ETF。
- Avoid ETF。

---

## 7.3 Japan Overnight Impact Scanner

### 目标

日本开盘前判断前一晚美股、汇率、风险资产对日股的影响。

### 输入

```text
SPY
QQQ
IWM
SMH / SOXX
VIX
USDJPY
DXY
US10Y proxy
Nikkei futures, if available
Japanese ADR proxies:
- TM
- SONY
- MUFG
```

### 输出

```text
Japan Market Bias:
- bullish
- neutral
- bearish

Sector Bias:
- semiconductor bullish
- exporters bullish
- banks bullish
- risk-off
- avoid growth

Risk Mode:
- normal
- watch
- shock
```

### 示例规则

```text
If QQQ > +1% and SMH > +1.5% and VIX down:
    Japan semiconductor bias = bullish

If USDJPY > +0.5%:
    exporters bias = positive

If VIX > +10% or QQQ < -2%:
    new long signals downgraded to watch-only

If headline risk high:
    opening breakout signals disabled
```

---

## 7.4 Headline Risk Engine

### 目标

识别市场是否处于突发新闻冲击环境，避免普通 PA 信号失效。

### 第一版输入

MVP 可以先用半自动方式：

- 用户手动标记 high headline risk。
- 系统通过 VIX、指数期货、ETF 急跌急涨、gap、异常波动 proxy 识别。
- 后续接新闻 API。

### Risk Mode

```text
0 Normal
1 Watch
2 Elevated
3 Shock
4 No New Trade
```

### 规则

```text
If VIX change > +10%:
    risk_mode = Elevated

If QQQ/SPY gap down > 1.5%:
    no chase

If major policy headline active:
    no first 30-minute trade

If shock mode:
    all new entry candidates become Watch Only
```

---

## 7.5 PA Engine

### 目标

根据价格行为生成入场计划和失效条件。

### PA 状态机

```text
1. Accumulation / Base
2. Breakout Setup
3. Breakout Confirmed
4. Retest / Pullback
5. Trend Continuation
6. Distribution / Breakdown
```

### Setup 类型

#### A. Breakout

条件：

```text
- price near base high
- base length 10–60 bars
- base depth within threshold
- volatility contraction
- breakout above resistance
- volume expansion
- close in upper 30% of range
```

输出：

```text
entry_trigger = resistance + buffer
initial_stop = breakout day low or base midpoint
invalidation = close back inside base
```

#### B. Pullback

条件：

```text
- trend up
- pullback to 20MA / 50MA / prior high
- volume contraction during pullback
- reclaim VWAP or 20MA
- higher low formation
```

输出：

```text
entry = reclaim level
stop = pullback low
invalidation = close below pullback low
```

#### C. Failed Breakdown Reclaim

条件：

```text
- price breaks support intraday
- then reclaims support
- volume confirms
- market context supportive
```

输出：

```text
entry = reclaim confirmation
stop = failed breakdown low
invalidation = loss of reclaimed level
```

#### D. Opening Range Breakout

用于日股开盘或美股开盘。

规则：

```text
- no trade first 15 minutes
- define opening range high/low
- allow long only if:
  - breaks OR high
  - holds above VWAP
  - market/sector confirms
```

---

## 7.6 Risk Engine

### 用户资金约束

初始资金：

```text
1000–2000 USD
```

每月追加：

```text
10,000–20,000 JPY
```

### 风控参数默认值

```text
single_trade_risk_pct = 0.5% to 1.0%
daily_loss_limit_pct = 1.0% to 2.0%
weekly_loss_limit_pct = 3.0%
max_open_positions = 1 to 3
max_option_positions = 1
max_option_premium_pct = 1% to 3%
absolute_option_premium_limit_pct = 5%
account_drawdown_stop = 10%
```

### 小账户规则

```text
If account_equity < 2000:
    no more than 2 open positions
    no option premium > 3% equity
    no averaging down
    no short options
    no 0DTE
```

### 交易暂停规则

```text
If 3 consecutive losses:
    block new live trades
    switch to paper mode until review

If drawdown > 5%:
    reduce risk by 50%

If drawdown > 10%:
    stop live trading
```

---

## 7.7 Position Ledger

### 目标

持仓生命周期管理。

每笔交易入场时必须记录：

- 为什么买。
- 哪个策略。
- 哪个 setup。
- 初始止损。
- 当前止损。
- 失效条件。
- 目标持仓周期。
- 离场规则。
- 是否允许加仓。
- 是否允许转期权。
- 市场环境。

### 状态

```text
planned
open
hold
watch
tighten_stop
reduce
exit_pending
closed
```

---

## 7.8 Exit Engine

### 重要性

Exit Engine 是系统核心，不是附属功能。

### Exit Alert Level

```text
0 Hold
1 Watch
2 Tighten Stop
3 Reduce
4 Exit
```

### 离场规则类型

#### A. Hard Stop

```text
If current_price <= current_stop:
    Level 4 Exit
```

#### B. Structure Invalidation

突破买入：

```text
If close back inside base:
    Level 4 Exit or Level 3 Reduce
```

回踩买入：

```text
If break pullback low:
    Level 4 Exit
```

趋势延续：

```text
If break previous higher low:
    Level 4 Exit
```

#### C. Profit Protection

```text
If position reaches +1R:
    move stop near breakeven

If reaches +2R:
    suggest reduce 30%–50%

If reaches +3R:
    trail with 10MA/20MA or structure low
```

#### D. Trailing Stop

```text
short-term:
    10MA close break = reduce

swing:
    20MA close break = reduce/exit

medium:
    50MA close break = exit
```

#### E. Time Stop

```text
If breakout has no follow-through after 5 bars:
    Level 2 or Level 3

If option underlying does not move after 3–5 days:
    Level 3 Reduce or Level 4 Exit
```

#### F. Market Regime Exit

```text
If market regime turns bearish:
    no add
    tighten stop

If shock mode:
    reduce optional positions
    no new trades
```

---

## 7.9 Option Adapter（v0.8：最低优先级 / 默认关闭）

### v0.8 结论

期权相关功能从 MVP 和早期实盘链路中移除，降为最低优先级。

```text
Current status:
    disabled_by_default

Priority:
    P8 / lowest

Decision right:
    research_only / paper_only

Live permission:
    false
```

### 原则

期权只在以下条件全部满足后，才允许进入研究或纸面交易：

```text
1. underlying 已通过 Scanner + PA + Risk Engine。
2. 当前系统已经完成 Position Ledger、Exit Engine、Journal、Paper Trading、Analytics。
3. 对应 underlying 策略已经有正期望证据。
4. 期权只用于表达 already-approved underlying plan。
5. 不允许因为期权指标反向提升 underlying 交易评级。
```

### 当前阶段不做

- 不扫全市场期权异动后追单。
- 不做 0DTE。
- 不做 iron condor / iron butterfly 实盘。
- 不做 covered call 实盘。
- 不做 tail hedge 实盘。
- 不做 beta-weighted delta 调整系统实盘。
- 不裸卖 call/put。
- 不买低流动性小票期权。
- 不财报前买短期期权彩票。
- 不用期权摊平亏损。
- 不因为高 POP、高 theta、高 IV 而升级交易。

### 后期最小可实现范围

如果未来重新启用期权模块，第一版只允许实现：

```text
1. 手动录入期权仓位。
2. 显示 max loss / premium risk / DTE / liquidity warning。
3. 若 underlying stop broken，则提示退出期权。
4. 若 DTE 进入 warning zone，则提示减仓或退出。
5. 若 settlement / assignment risk unknown，则标记 Blocked。
```

不允许第一版实现：

```text
0DTE strategy
short premium strategy
iron condor / iron butterfly
credit spread live
covered call live
AI option picker
option alpha ranking
```

### 期权研究输出，不进入实盘决策

```text
option_suitability:
- disabled
- research_only
- paper_only
- blocked

preferred_expression:
- stock/ETF only
- no option in MVP
- later: small defined-risk expression only after validation
```

### v0.8 权限

```text
Option Adapter can:
    explain risk
    block unsuitable option structures
    record paper trades
    support later research

Option Adapter cannot:
    generate live trade
    upgrade candidate
    increase position size
    override Risk Engine
    override Exit Engine
    override Anti-Overfitting Governance
```

---

## 7.10 AI Reviewer

### 目标

AI 只做复核，不做交易执行。

### 输入

AI 输入必须是结构化 JSON：

```json
{
  "symbol": "QQQ",
  "asset_type": "ETF",
  "strategy": "ETF_rotation",
  "market_regime": "bullish",
  "setup_type": "pullback_reclaim",
  "scores": {
    "strategy": 82,
    "pa": 76,
    "risk": 68
  },
  "entry": 455.2,
  "stop": 443.8,
  "risk_pct": 2.5,
  "context": {
    "spy": "strong",
    "qqq": "leading",
    "vix": "falling"
  }
}
```

### 输出 JSON Schema

```json
{
  "decision": "candidate | watch | avoid",
  "quality_score": 0,
  "setup_type": "breakout | pullback | reversal | trend_continuation",
  "bull_case": [],
  "bear_case": [],
  "key_context": [],
  "invalid_if": [],
  "risk_notes": [],
  "suggested_action": "hold | watch | reduce | exit | no_trade",
  "human_check_required": true
}
```

### AI 禁止事项

AI 不允许：

- 单独决定买入。
- 单独决定卖出。
- 修改风控阈值。
- 忽略 hard stop。
- 基于新闻幻想做预测。
- 输出无法解释的信号。

---

## 8. API 设计

## 8.1 Scanner APIs

```http
POST /scans/us/daily
POST /scans/us/intraday
POST /scans/jp/daily
POST /scans/jp/intraday
GET  /candidates?date=YYYY-MM-DD
GET  /candidates/{candidate_id}
```

---

## 8.2 Position APIs

```http
POST /positions
GET  /positions/open
GET  /positions/{position_id}
PATCH /positions/{position_id}
POST /positions/{position_id}/close
```

---

## 8.3 Exit APIs

```http
POST /exit/check-all
POST /exit/check/{position_id}
GET  /exit/alerts
POST /exit/alerts/{alert_id}/ack
```

---

## 8.4 Option APIs

```http
POST /options/analyze-underlying/{symbol}
GET  /options/chain/{underlying}
GET  /options/candidates/{underlying}
```

---

## 8.5 Backtest APIs

```http
POST /backtests/run
GET  /backtests/{backtest_id}
GET  /backtests/{backtest_id}/trades
GET  /backtests/{backtest_id}/metrics
```

---

## 9. Batch Jobs

## 9.1 美股收盘后

日本时间早晨运行：

```text
1. Ingest US daily bars
2. Update US ETF data
3. Update options snapshots for watchlist
4. Calculate US market regime
5. Run US scanners
6. Update open positions
7. Generate exit alerts
8. Generate daily report
```

---

## 9.2 日股开盘前

```text
1. Calculate US overnight impact
2. Load JP candidate universe
3. Apply Japan overnight bias
4. Downgrade risky signals
5. Generate JP pre-open watchlist
```

---

## 9.3 日股盘中，Phase 2

```text
1. Ingest J-Quants minute/tick data
2. Update opening range
3. Update VWAP
4. Check PA triggers
5. Check exit alerts
6. Optionally query IBKR L1/L2 for top candidates
```

---

## 9.4 收盘后

```text
1. Update realized/unrealized PnL
2. Update position status
3. Update stops
4. Create journal entries if positions closed
5. Generate next-day plan
```

---

## 10. Backtesting 设计

## 10.1 基本要求

回测必须避免：

- Look-ahead bias。
- Survivorship bias。
- 使用未来财报数据。
- 未调整拆股。
- 忽略手续费。
- 忽略滑点。
- 忽略无法成交。
- 期权回测中忽略 bid/ask。

### 最小回测粒度

美股：

- 日线信号。
- 60分钟/15分钟触发。
- 交易成本。
- 滑点。

日股：

- 日线信号。
- 分足/Tick add-on 后再做盘中触发回测。

期权：

- 先不要做复杂历史期权回测。
- Phase 1 只做 forward paper trading。
- Phase 2 再做期权链历史回测。

---

## 10.2 指标

```text
Total return
CAGR, if meaningful
Max drawdown
Win rate
Average win
Average loss
Profit factor
Expectancy per trade
Average R
Median R
Max consecutive losses
Exposure time
Strategy breakdown
Asset breakdown
Option vs underlying breakdown
```

### 期权额外指标

```text
Average premium risk
Average DTE at entry
Average DTE at exit
IV at entry vs exit
Theta loss estimate
Underlying move vs option PnL
```

---

## 11. UI 设计

## 11.1 Dashboard 首页

显示：

- 今日市场模式。
- 美股风险模式。
- 日本隔夜影响。
- 新候选数量。
- Open positions。
- Exit alerts。
- Risk limit status。

---

## 11.2 Candidates 页面

字段：

```text
Ticker
Market
Asset Type
Strategy
Setup
Score
Entry
Stop
Risk %
Decision
Option Suitability
Reason
AI Review
```

按钮：

- Add to watchlist。
- Create planned position。
- Ignore。
- View chart。
- AI explain。
- Export CSV。

---

## 11.3 Positions 页面

字段：

```text
Ticker
Entry
Current
P/L
R
Initial Stop
Current Stop
Status
Exit Level
Action
Reason
```

按钮：

- Mark reduced。
- Mark closed。
- Update quantity。
- Update stop。
- Add note。

---

## 11.4 Exit Alerts 页面

字段：

```text
Time
Ticker
Level
Action
Reason
Triggered Rules
New Stop
Acknowledged
```

颜色：

- Hold：灰。
- Watch：蓝。
- Tighten：黄。
- Reduce：橙。
- Exit：红。

---

## 11.5 Journal 页面

字段：

```text
Ticker
Strategy
Entry
Exit
PnL
R
Exit Reason
Mistake Tags
Notes
```

统计：

- 按策略。
- 按资产。
- 按月份。
- 按 setup。
- 按期权/非期权。

---

## 12. 实现计划（v0.9 调整）

v0.9 将 Advanced PA 前移并拆分，将 Strat 作为 PA 的可程序化触发层，同时保持做空 live 与期权 live 关闭。以下计划取代旧版 Phase 0–7 的优先级。

## Phase 0：项目骨架 + 数据质量门禁

目标：

- 建 repo。
- 建数据库。
- 建配置。
- 建数据模型。
- 建基础 CLI。
- 建 Data Quality Gate。

任务：

```text
- 初始化 Python 项目
- 配置 ruff/mypy/pytest
- 建 DuckDB/Postgres schema
- 实现 config loader
- 实现 logging
- 实现 symbol master
- 实现 job runner
- 实现 data freshness check
- 实现 missing bar / bad bar 检查
```

验收：

- 可以本地启动。
- 可以创建表。
- 可以加载配置。
- 可以跑一个 dummy scan。
- 数据缺失或延迟时，scanner 不生成 live candidate。

---

## Phase 1：美股/ETF 数据 + 基础 Scanner + Basic PA + Strat Bar Labeling

目标：

- 用 Polygon/Massive 做美股/ETF基础扫描。
- 同步实现 Basic PA 与 Strat 最小语法，不再把 PA 放到后期。

任务：

```text
- 实现 Massive client
- 拉取 US daily bars
- 拉取 ETF universe
- 计算 MA、RS、52w high、volume
- 实现 O’Neil-core scanner v1
- 实现 ETF rotation scanner v1
- 实现 Basic PA: breakout / pullback / reclaim / opening range
- 实现 Strat bar labeling: 1 / 2U / 2D / 3
- 实现 timeframe continuity: M / W / D / 60m
- 输出 candidates 表
```

验收：

- 每日能生成美股/ETF候选。
- 每个候选有 score、entry、stop、decision。
- 每个候选有 `trade_direction`，默认 long。
- 每个候选可显示当前 bar state：1 / 2U / 2D / 3。
- 能导出 CSV/Markdown 报告。

---

## Phase 2：Position Ledger + Exit Engine + Direction Support

目标：

- 从 scanner 升级为交易管理系统。
- Position Ledger 开始支持 long / short 字段，但 short live 默认关闭。

任务：

```text
- 实现 position CRUD
- positions 增加 position_side: long / short
- journal 增加 trade_direction
- 实现 hard stop
- 实现 structure invalidation
- 实现 +1R/+2R/+3R 规则
- 实现 trailing stop
- 实现 time stop
- 实现 exit alerts
- short position 只允许 paper/manual record，不允许 live permission
```

验收：

- 手动录入一笔 long 持仓后，系统能每天提示状态。
- 价格触发止损后，系统输出 Exit。
- 达到 +2R 后，系统输出 Reduce。
- 无 follow-through 后，系统输出 Time Stop。
- 系统字段支持 short，但默认前端不提供 live short 操作。

---

## Phase 3：前端 Dashboard + Candidates + Positions + Exit Alerts

目标：

- 前端实时显示候选、持仓、离场提醒、PA/Strat 状态。

任务：

```text
- Next.js 初始化
- Dashboard summary
- Candidates table
- DirectionBadge: Long / Short Watch / Neutral / No Trade
- StratTriggerBadge: 1 / 2U / 2D / 3 / 2-1-2 / 3-1-2
- Positions table
- Exit Alerts panel
- Mini chart with entry / stop / Strat trigger level
- SSE 或 WebSocket 事件流
```

验收：

- 后端跑完 scan 后，前端能显示候选。
- 候选可显示 PA state 与 Strat trigger。
- Level 4 Exit 自动弹出明显提醒。
- Short Watchlist 显示为 paper-only / disabled-live。

---

## Phase 4：Paper Trading + Journal + PA/Strat Calibration

目标：

- 验证系统是否有 edge。
- 验证 Strat 触发是否真的改善 PA 入场，而不是制造噪音。

任务：

```text
- Create paper position from candidate
- Auto update paper P/L
- Auto trigger paper exit alerts
- Manual journal entry
- R-multiple calculation
- Basic strategy breakdown
- Rule adherence tracking
- PA setup breakdown
- Strat pattern breakdown
- Ablation: PA only vs PA + Strat
```

验收：

- 用户可以从 candidate 创建 paper position。
- Paper position 能由 Exit Engine 管理。
- 平仓后自动进入 journal。
- 每笔交易能计算 R multiple。
- 能统计 win rate、average R、max drawdown。
- 能比较 `Structure PA only` 和 `Structure PA + Strat Trigger` 的差异。
- 期权不在本 phase 实现。

---

## Phase 5：Advanced PA v1，受控前移

目标：

- 加强 PA，但不一次性实现全部高级 PA，防止过拟合。

允许进入 v1 的内容：

```text
- Multi-timeframe PA alignment
- Breakout failure detection
- Overextension / no-chase warning
- Volume-price anomaly
- Trend day / range day basic classifier
- Structure quality score
```

禁止进入 v1 的内容：

```text
- AI visual chart interpretation
- 全套 liquidity sweep 自动识别
- 复杂 order flow
- volume profile
- 自动画高级 supply / demand zone
- 全套 TheStrat pattern library
```

验收：

- 每个新增 PA 规则都必须有 ablation test。
- 新增 PA 规则默认只能 downgrade / watch / avoid，不能单独生成 live trade。
- 参数数量不超过 Parameter Budget。

---

## Phase 6：Capital Accumulation Mode

目标：

- 把用户当前阶段定义为本金积累，而不是月度提款。

任务：

```text
- Monthly contribution tracking
- Profit retention tracking
- Account growth curve
- Risk-by-equity schedule
- Cashflow target locked until account threshold
- Drawdown-based risk reduction
```

验收：

- 系统显示当前模式为 Capital Accumulation。
- 未达到解锁条件时，Cashflow Mode 不会提高风险。
- 盈利默认留存复利。

---

## Phase 7：日股 J-Quants 日线版

目标：

- 加入日股日线和财务扫描。

任务：

```text
- 实现 J-Quants client
- 拉取 listed info
- 拉取 stock prices
- 拉取 financial summary
- 拉取 earnings schedule
- 计算 JP trend/RS/liquidity
- 实现 Japan scanner v1
- 实现 US overnight impact v1
- 将 Basic PA + Strat bar labeling 扩展到 JP daily
```

验收：

- 每日能生成日股候选。
- 能根据前一晚美股/美元日元/ETF风险降级候选。
- 能过滤低流动性票和财报临近票。
- 日股候选也有 PA/Strat 状态。

---

## Phase 8：Short Watchlist + Paper Short

目标：

- 支持做空研究能力，但不开放 live short。
- Bearish 信号优先用于 avoid long、tighten stop、reduce、exit。

任务：

```text
- 实现 bearish context scanner
- 实现 short candidate watchlist
- 实现 short paper position
- 实现 buy-to-cover journal action
- 实现 short gap-up stress test
- 实现 borrow availability / hard-to-borrow 字段，先手动或占位
- 实现 short squeeze risk tags
```

验收：

- 系统能输出 Short Watchlist。
- Short Watchlist 明确标记为 Paper-only。
- 熊市信号能用于降低 long 风险。
- 无 borrow/margin/event risk 信息时，不允许 live short。

---

## Phase 9：AI Reviewer，解释层

目标：

- 用结构化 AI 输出解释和反证。
- AI 不获得额外决策权。

任务：

```text
- 设计 JSON input schema
- 设计 JSON output schema
- 实现 prompt templates
- 实现 schema validation
- 将 AI 输出写入 candidates / exit_alerts
- AI 输出增加 Strat/Short 反证解释字段
```

验收：

- AI 只基于规则结果解释。
- AI 输出必须是合法 JSON。
- AI 不允许绕过 hard stop。
- AI 不允许把 short watch 升级为 live short。
- AI 能指出反证和风险。

---

## Phase 10：Options Backlog，最低优先级

目标：

- 保持期权为 Research-only / Paper-only backlog。

任务：

```text
- 暂不实现 live option adapter
- 暂不实现 0DTE
- 暂不实现 short premium
- 可保留手动 option note / risk note 字段
```

验收：

- Options live permission = false。
- Options 参数不会影响 MVP candidate 排名。
- Options 页面默认隐藏或 disabled。

---

## 13. 风险与限制

## 13.1 市场风险

系统无法避免：

- 特朗普/政策突发消息。
- 央行突发转向。
- 战争/地缘政治。
- 个股财报雷。
- 隔夜 gap。
- 流动性消失。
- 期权 IV crush。

系统只能：

- 降低风险。
- 暂停信号。
- 提醒减仓。
- 使止损更严格。
- 避免第一波追单。

---

## 13.2 数据风险

- Polygon/Massive 订阅计划不同，可用数据和实时性不同。
- J-Quants 不等于实时订单簿。
- IBKR L2 并发有限，不适合全市场盘口扫描。
- TradingView 不作为项目数据源。
- 新闻数据第一版可能不足。

---

## 13.3 小账户风险

1000–2000 USD 很容易因为几次错误受伤：

- 期权过大。
- 频繁交易。
- 亏损后加仓。
- 止损后马上报复交易。
- 忽略手续费和滑点。

系统必须强制记录：

- 每笔风险。
- 每日亏损。
- 连续亏损。
- 回撤。
- 期权权利金占比。

---

## 14. 默认参数建议

```yaml
account:
  starting_equity_usd: 1000-2000
  monthly_add_jpy: 10000-20000
  max_trade_risk_pct: 0.005
  aggressive_trade_risk_pct: 0.01
  daily_loss_limit_pct: 0.02
  weekly_loss_limit_pct: 0.03
  drawdown_reduce_risk_pct: 0.05
  drawdown_stop_live_pct: 0.10

positions:
  max_open_positions: 3
  max_option_positions: 1
  allow_averaging_down: false
  allow_short_options: false

options:
  preferred_dte_min: 30
  preferred_dte_max: 60
  aggressive_dte_min: 14
  min_delta: 0.35
  max_delta: 0.65
  max_premium_pct: 0.03
  absolute_max_premium_pct: 0.05
  profit_reduce_pct: 0.5
  loss_exit_pct: 0.4
  warning_dte: 21
  exit_dte: 14

pa:
  no_trade_first_minutes: 15
  breakout_volume_multiple: 1.5
  base_min_days: 10
  base_max_days: 60
  max_base_depth_pct: 0.2
  no_chase_gap_pct: 0.04

exit:
  move_stop_at_r: 1.0
  partial_take_profit_at_r: 2.0
  trail_after_r: 3.0
  breakout_time_stop_days: 5
```

---

## 15. 最终日常工作流

### 美股

```text
早上：
- 系统完成美股收盘扫描
- 用户查看候选和持仓离场提醒

白天：
- 系统生成今晚计划
- 用户决定是否关注

晚上：
- 系统按条件提醒
- 用户手动下单或不操作

次日：
- 系统更新 journal 和 exit alerts
```

### 日股

```text
8:00 前：
- 系统计算美股隔夜影响
- 生成日股候选

9:00-9:15：
- 系统不允许追单

9:15 以后：
- 系统判断 opening range / VWAP / PA confirmation

14:30-15:30：
- 系统判断是否日线收盘确认

收盘后：
- 更新持仓和复盘
```

---

## 16. 成功标准

### 技术成功

- 每天稳定生成候选。
- 每个候选都有 entry、stop、invalidation。
- 每个 open position 都有 exit state。
- 所有交易都有 journal。
- AI 输出可解释、可校验。
- 系统不依赖 TradingView 数据。

### 交易成功

先不追求赚大钱，而是：

- 50–100 笔后 expectancy > 0。
- 最大回撤可控。
- 单笔亏损受控。
- 用户没有因为期权快速爆仓。
- 系统能明确告诉用户什么时候不交易。
- 系统能在盈利时提示保护利润。
- 系统能减少人工看图时间。

---

## 17. 外部资料与数据源参考

- J-Quants API: https://www.jpx.co.jp/english/markets/other-data-services/j-quants-api/index.html
- J-Quants pricing/data website: https://jpx-jquants.com/en
- J-Quants data spec: https://jpx.gitbook.io/j-quants-ja/outline/data-spec
- J-Quants minute bar/tick add-on announcement: https://www.jpx.co.jp/english/corporate/news/news-releases/6020/20260119.html
- Massive / Polygon documentation: https://massive.com/docs
- Massive option chain snapshot: https://massive.com/docs/rest/options/snapshots/option-chain-snapshot
- IBKR Japan market data pricing: https://www.interactivebrokers.co.jp/en/pricing/market-data-pricing.php
- Options risk disclosure: https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document


---

# 19. 前端实时系统追加设计（v0.2）

## 19.1 为什么必须追加前端

原 v0.1 文档已经设计了后端 Scanner、Position Ledger、Exit Engine、Option Adapter 和通知模块。但如果系统只靠通知，会出现几个问题：

```text
1. 用户只能被动接收单点事件，看不到完整上下文。
2. 候选、持仓、风险模式、离场提醒分散在不同通知里，容易误判。
3. 盘中状态变化无法连续观察。
4. Exit Engine 的价值无法充分体现，因为用户看不到仓位生命周期。
5. 用户仍然可能回到 TradingView 手动翻图，违背“减少看图”的目标。
```

因此需要增加一个实时前端：

> 前端不是交易终端，而是实时决策面板。  
> 它显示系统已经计算好的候选、持仓、风险、PA 状态、期权适配和离场提醒，但不提供自动下单能力。

---

## 19.2 前端设计目标

### 核心目标

前端需要做到：

```text
1. 实时显示市场状态。
2. 实时显示候选池变化。
3. 实时显示持仓状态与 Exit Engine 结果。
4. 实时显示风险模式和是否允许新开仓。
5. 显示每个候选的入场计划、止损、无效条件。
6. 显示每个持仓的当前 R、P/L、止损、离场级别。
7. 显示期权适配结果。
8. 显示 AI Reviewer 的结构化解释和反证。
9. 支持用户手动录入持仓、标记减仓、标记平仓、写交易日志。
10. 支持从实时模式切换到复盘模式。
```

### 非目标

前端第一版不做：

```text
1. 不下单。
2. 不连接 broker trading API。
3. 不做自动交易按钮。
4. 不做一键买入/卖出。
5. 不显示 TradingView 内嵌数据作为系统数据源。
6. 不做高频 scalping 面板。
7. 不做全市场 tick tape。
```

---

## 19.3 前端总体信息架构

前端主导航建议如下：

```text
Dashboard
├── Market Overview
├── Live Candidates
├── Open Positions
├── Exit Alerts
├── Watchlist
├── Options
├── Charts
├── Journal
├── Backtest / Paper Trading
├── Settings
└── System Health
```

每个页面职责不同：

```text
Dashboard:
    总览，判断今天是否适合交易。

Live Candidates:
    实时候选池，显示哪些标的接近买点。

Open Positions:
    当前仓位管理，显示是否该持有、减仓、止损或退出。

Exit Alerts:
    离场提醒中心，所有 Exit Engine 输出集中显示。

Watchlist:
    用户关注列表和系统重点监控列表。

Options:
    对已通过 underlying 筛选的标的显示期权适配结果。

Charts:
    系统生成的简化图表，不依赖 TradingView。

Journal:
    交易记录、复盘、错误标签。

Backtest / Paper Trading:
    回测和纸面交易结果。

Settings:
    风控参数、通知参数、策略参数。

System Health:
    API 状态、数据更新时间、任务状态、WebSocket 状态。
```

---

## 19.4 前端技术栈建议

## 19.4.1 MVP 前端

如果想最快做出来：

```text
Streamlit + FastAPI
```

优点：

```text
1. 开发快。
2. 适合个人使用。
3. 能快速显示表格、图表、状态卡片。
4. 和 Python 后端集成简单。
```

缺点：

```text
1. 实时交互体验有限。
2. 页面结构复杂后会难维护。
3. 长期做成产品不如 Next.js。
```

适合 Phase 0–2。

---

## 19.4.2 正式前端

建议：

```text
Next.js 15+
React 19+
TypeScript
Tailwind CSS
shadcn/ui
TanStack Query
TanStack Table
Zustand
Lightweight Charts
Recharts
WebSocket / Server-Sent Events
```

模块职责：

```text
Next.js:
    路由、页面、SSR/CSR 混合。

TypeScript:
    类型安全，前后端 schema 对齐。

TanStack Query:
    REST API 数据获取、缓存、刷新。

TanStack Table:
    Candidates / Positions / Alerts 表格。

Zustand:
    全局 UI 状态，例如选中 ticker、筛选器、实时连接状态。

Lightweight Charts:
    K线、均线、VWAP、entry/stop 标记。

Recharts:
    统计图，例如 R 分布、策略表现、回撤曲线。

WebSocket/SSE:
    实时推送候选、持仓、离场提醒、市场状态。
```

---

## 19.5 实时数据流设计

前端实时显示不应该直接连接外部数据源。  
外部数据统一进入后端，后端计算后再推给前端。

```text
Polygon/Massive / J-Quants / IBKR
        ↓
Backend Ingestion
        ↓
Normalized Data Store
        ↓
Feature Builder / Scanner / Exit Engine
        ↓
Realtime Event Bus
        ↓
WebSocket / SSE Gateway
        ↓
Frontend Dashboard
```

### 原则

```text
1. 前端只显示后端计算后的结果。
2. 前端不直接调用 Polygon/Massive。
3. 前端不直接调用 J-Quants。
4. 前端不直接调用 IBKR。
5. 前端不承担交易逻辑。
6. 前端可以请求“刷新计算”，但最终计算仍由后端完成。
```

---

## 19.6 WebSocket / SSE 选择

### SSE 适合第一版

Server-Sent Events 适合：

```text
1. 后端向前端单向推送。
2. 候选状态更新。
3. Exit alerts。
4. Market regime 更新。
5. 系统任务状态。
```

优点：

```text
1. 简单。
2. 浏览器原生支持。
3. 自动重连。
4. 对个人项目足够。
```

缺点：

```text
1. 主要是单向。
2. 不适合复杂双向交互。
```

### WebSocket 适合正式版

WebSocket 适合：

```text
1. 更低延迟。
2. 双向交互。
3. 多频道订阅。
4. 用户实时修改 watchlist 后后端立刻调整推送。
```

建议路线：

```text
Phase 1:
    SSE

Phase 2:
    WebSocket

Phase 3:
    WebSocket + Redis Pub/Sub / Stream
```

---

## 19.7 实时事件模型

后端向前端推送的事件建议统一格式：

```json
{
  "event_id": "evt_20260425_000001",
  "event_type": "candidate.updated",
  "timestamp": "2026-04-25T09:15:00+09:00",
  "market": "US",
  "symbol": "QQQ",
  "severity": "info",
  "payload": {}
}
```

### event_type 枚举

```text
market_context.updated
candidate.created
candidate.updated
candidate.downgraded
candidate.removed

position.created
position.updated
position.stop_updated
position.pnl_updated
position.closed

exit_alert.created
exit_alert.updated
exit_alert.acknowledged

option_analysis.updated
watchlist.updated

scan.started
scan.completed
scan.failed

data_source.healthy
data_source.delayed
data_source.failed

risk_mode.changed
trading_halt.enabled
trading_halt.disabled
```

---

## 19.8 前端页面详细设计

## 19.8.1 Dashboard 首页

### 目标

一眼回答：

> 今天能不能交易？  
> 有哪些新机会？  
> 已有仓位有没有危险？  
> 风险模式是什么？

### 主要区域

```text
1. Market Regime Cards
2. Risk Mode Banner
3. Account Risk Snapshot
4. Top Candidates
5. Open Positions Summary
6. Exit Alerts
7. Option Risk Summary
8. Data Freshness / System Health
```

### Market Regime Cards

显示：

```text
US Market:
    Bullish / Neutral / Bearish / Shock

Japan Bias:
    Bullish / Neutral / Bearish

Sector Bias:
    Semiconductors / Banks / Exporters / Risk-off

Headline Risk:
    Normal / Watch / Elevated / Shock

VIX:
    Current / Change

USDJPY:
    Current / Change
```

### Risk Mode Banner

顶部常驻大横幅：

```text
NORMAL:
    Green - New candidates allowed.

WATCH:
    Yellow - New candidates require confirmation.

SHOCK:
    Red - No new trades. Manage existing positions only.

RISK HALT:
    Dark Red - Account risk limit hit. Live trading disabled.
```

---

## 19.8.2 Live Candidates 页面

### 目标

实时显示系统筛出的候选。

### 表格字段

```text
Ticker
Name
Market
Asset Type
Strategy
Setup
Score
Decision
Entry Trigger
Preferred Entry
Initial Stop
Risk %
Distance to Entry
PA State
Market Context
Option Suitability
Updated At
```

### 决策标签

```text
Candidate
Watch
Avoid
Downgraded
Triggered
Expired
```

### 行颜色

```text
Candidate: green
Watch: blue
Downgraded: yellow
Avoid: gray
Triggered: purple
High Risk: red outline
```

### 行点击后的详情 Drawer

详情展示：

```text
1. Strategy Score Breakdown
2. PA Facts
3. Entry Plan
4. Stop / Invalidation
5. Context
6. Option Suitability
7. AI Reviewer
8. Mini Chart
9. Create Planned Position
10. Add to Watchlist
```

### Mini Chart

显示：

```text
Candles
20MA / 50MA / 200MA
VWAP, if intraday
Entry line
Stop line
Resistance / support
Base range
Current price
```

不需要完全替代 TradingView，只需要辅助判断。

---

## 19.8.3 Open Positions 页面

### 目标

这是最重要的页面之一。

它回答：

> 我现在持有的每个仓位还成立吗？应该怎么处理？

### 表格字段

```text
Ticker
Asset Type
Strategy
Entry Price
Current Price
Quantity
Notional
P/L
P/L %
R Multiple
Initial Stop
Current Stop
Exit Level
Suggested Action
Reason
Updated At
```

### Exit Level 显示

```text
0 Hold: gray
1 Watch: blue
2 Tighten Stop: yellow
3 Reduce: orange
4 Exit: red
```

### Position Detail Drawer

显示：

```text
Entry thesis
Current thesis status
Invalidation conditions
Stop history
R progression
P/L chart
Exit alerts history
AI review
Manual notes
Action log
```

### 用户可执行操作

这些只是记录，不下单：

```text
Mark as reduced
Mark as closed
Update quantity
Update entry
Update current stop
Add note
Attach screenshot/link
Acknowledge alert
```

---

## 19.8.4 Exit Alerts 页面

### 目标

集中显示所有离场相关提醒，优先级高于新机会。

### 列表字段

```text
Time
Ticker
Position
Level
Action
Reason
Triggered Rules
New Stop
Acknowledged
```

### 筛选器

```text
Only Level 4 Exit
Only Reduce
Only Unacknowledged
By market
By strategy
By asset type
```

### Alert 详情

```text
Triggered rule:
    e.g. Close below current stop

Context:
    Market regime changed to bearish

Suggested action:
    Exit / Reduce / Tighten Stop

System note:
    This is not an execution order. Manual confirmation required.
```

---

## 19.8.5 Watchlist 页面

### 目标

管理系统重点监控标的。

### Watchlist 类型

```text
System Generated:
    Scanner 自动加入。

Manual:
    用户手动加入。

Position Related:
    当前持仓 underlying 自动加入。

Option Related:
    有期权仓位的 underlying 自动加入。

Japan Pre-open:
    日股开盘前候选。

US Night Plan:
    美股夜间计划。
```

### 字段

```text
Ticker
Reason
Source
Priority
Active
Current State
Next Trigger
Remove / Pause
```

---

## 19.8.6 Options 页面

### 目标

只展示 underlying 通过筛选后的期权适配，不展示全市场期权异动赌博。

### 页面结构

```text
1. Underlying Candidates
2. Option Suitability
3. Recommended Expiration Range
4. Candidate Contracts
5. Risk Summary
6. Existing Option Positions
```

### 合约表字段

```text
Option Symbol
Type
Strike
Expiration
DTE
Bid
Ask
Mid
Spread %
Volume
Open Interest
IV
Delta
Gamma
Theta
Vega
Score
Reject Reason
```

### 期权风险提示

每个可选合约旁边显示：

```text
Max premium risk
% of account
Underlying stop
Option exit rule
DTE warning
IV warning
```

如果权利金超过规则：

```text
Blocked:
    Premium exceeds max account risk.
```

---

## 19.8.7 Charts 页面

### 目标

提供系统内部图表，减少用户频繁打开 TradingView。

### 图表能力

```text
Candlestick
Volume
Moving averages
VWAP
Entry / Stop lines
Support / resistance
Opening range
Position entry marker
Exit marker
R multiple marker
```

### 不做

```text
不做复杂画线工具。
不做 TradingView 克隆。
不做社交指标。
不做手动图形交易。
```

### 推荐组件

```text
lightweight-charts
```

---

## 19.8.8 Journal 页面

### 目标

复盘和策略迭代。

### 功能

```text
Trade list
Position lifecycle
Entry reason
Exit reason
Mistake tags
R multiple
Setup type
Market context
Option vs non-option
Screenshot/link/note
```

### 错误标签

```text
chased_gap
ignored_stop
sold_too_early
held_loser
oversized_option
news_risk_ignored
entered_without_confirmation
exited_against_plan
```

---

## 19.8.9 Backtest / Paper Trading 页面

### 目标

显示系统是否真的有 edge。

### 显示

```text
Equity curve
Drawdown curve
Trade distribution
R distribution
Strategy breakdown
Asset breakdown
Monthly performance
Option contribution
Win/loss streaks
```

### Paper Mode

前端需要支持：

```text
Create paper position from candidate
Auto update paper P/L
Auto trigger paper exit
Compare paper vs actual
```

---

## 19.8.10 Settings 页面

### 可配置内容

```text
Account size
Max risk per trade
Max daily loss
Max weekly loss
Option premium limit
No trade first minutes
Breakout volume multiple
Base depth threshold
Exit R thresholds
Notification channel
Markets enabled
Data sources enabled
AI reviewer enabled
```

### 安全限制

某些参数需要二次确认：

```text
Increase max risk per trade
Enable options
Increase option premium limit
Disable hard stop alerts
Disable risk halt
```

---

## 19.8.11 System Health 页面

### 显示

```text
Data source status
Last successful ingestion
Last scan time
Last exit check time
WebSocket/SSE status
Queue length
API error count
Data delay
Disk/database status
```

### 状态颜色

```text
Healthy: green
Delayed: yellow
Failed: red
Disabled: gray
```

---

## 19.9 前端状态管理设计

### 服务端状态

使用 TanStack Query 管理：

```text
Candidates
Positions
Exit alerts
Options analysis
Market context
Journal
Backtest results
Settings
```

### 客户端 UI 状态

使用 Zustand 管理：

```text
selectedSymbol
selectedCandidateId
selectedPositionId
activeMarket
activeTimeframe
tableFilters
drawerOpen
sidebarCollapsed
realtimeConnected
```

### 实时事件处理

前端收到事件后：

```text
1. 根据 event_type 判断影响哪个 query cache。
2. 局部更新对应数据。
3. 高优先级 alert 弹出 toast/banner。
4. Level 4 Exit 事件固定显示在顶部。
5. 所有事件写入本地 event log。
```

---

## 19.10 前端 API 合约

## 19.10.1 Dashboard

```http
GET /api/dashboard/summary
```

返回：

```json
{
  "market_context": {},
  "risk_mode": "normal",
  "candidate_count": 12,
  "open_position_count": 3,
  "exit_alert_count": 2,
  "highest_exit_level": 3,
  "data_freshness": {}
}
```

---

## 19.10.2 Realtime Stream

SSE：

```http
GET /api/realtime/events
```

WebSocket：

```http
WS /ws/realtime
```

订阅参数：

```json
{
  "markets": ["US", "JP"],
  "symbols": ["QQQ", "NVDA", "7203.T"],
  "channels": [
    "market_context",
    "candidates",
    "positions",
    "exit_alerts",
    "options",
    "system"
  ]
}
```

---

## 19.10.3 Candidates

```http
GET /api/candidates
GET /api/candidates/{candidate_id}
PATCH /api/candidates/{candidate_id}
POST /api/candidates/{candidate_id}/watch
POST /api/candidates/{candidate_id}/create-planned-position
```

---

## 19.10.4 Positions

```http
GET /api/positions/open
GET /api/positions/{position_id}
POST /api/positions
PATCH /api/positions/{position_id}
POST /api/positions/{position_id}/reduce
POST /api/positions/{position_id}/close
POST /api/positions/{position_id}/notes
```

注意：

```text
reduce/close 只是记录用户手动执行结果，不向券商下单。
```

---

## 19.10.5 Exit Alerts

```http
GET /api/exit-alerts
GET /api/exit-alerts/{alert_id}
POST /api/exit-alerts/{alert_id}/ack
POST /api/exit-alerts/{alert_id}/snooze
```

---

## 19.10.6 Charts

```http
GET /api/charts/{symbol}?timeframe=1d&from=&to=
GET /api/charts/{symbol}/annotations
```

返回：

```json
{
  "bars": [],
  "indicators": {
    "ma20": [],
    "ma50": [],
    "ma200": [],
    "vwap": []
  },
  "annotations": [
    {
      "type": "entry",
      "price": 455.2,
      "timestamp": "..."
    },
    {
      "type": "stop",
      "price": 443.8
    }
  ]
}
```

---

## 19.11 前端组件设计

### 核心组件

```text
MarketRegimeCard
RiskModeBanner
CandidateTable
CandidateDetailDrawer
PositionTable
PositionDetailDrawer
ExitAlertPanel
OptionChainTable
OptionSuitabilityBadge
MiniCandlestickChart
RMultipleBadge
StopLineBadge
AIReviewPanel
SystemHealthIndicator
RealtimeConnectionBadge
```

### Badge 设计

```text
DecisionBadge:
    Candidate / Watch / Avoid / Downgraded

ExitLevelBadge:
    Hold / Watch / Tighten / Reduce / Exit

RiskBadge:
    Normal / Watch / Shock / Halt

OptionSuitabilityBadge:
    None / Low / Medium / High / Blocked
```

---

## 19.12 实时前端性能要求

### MVP

```text
Candidates table: <= 500 rows
Positions: <= 50 rows
Exit alerts: <= 500 recent alerts
Chart bars: <= 2000 bars per symbol/timeframe
Realtime event latency: under 2–5 seconds acceptable
```

### 正式版

```text
虚拟表格
分页
按市场/策略过滤
WebSocket channel subscription
事件去重
缓存过期策略
```

---

## 19.13 前端权限与安全

即使是个人系统，也建议设计基础权限。

### 登录

```text
Single-user password login
Optional OAuth later
Session cookie
CSRF protection
```

### 敏感操作二次确认

```text
Mark position closed
Increase risk limit
Enable options
Disable alerts
Delete journal
```

### 审计日志

记录：

```text
parameter_changed
position_updated
alert_acknowledged
trade_marked_closed
risk_limit_changed
```

---

## 19.14 前端与通知的关系

通知和前端不是二选一。

### 前端负责完整上下文

```text
完整候选列表
完整持仓状态
完整离场规则
图表和复盘
系统健康状态
```

### 通知负责高优先级事件

```text
Level 4 Exit
Risk Halt
Stop broken
Option DTE warning
High quality candidate triggered
Data source failure
```

### 通知不应该轰炸用户

规则：

```text
Level 0/1 不通知，只显示前端。
Level 2 可选通知。
Level 3 通知。
Level 4 强通知。
Risk Halt 强通知。
```

---

## 19.15 前端实现里程碑

## Frontend Phase F0：静态 Dashboard 原型

目标：

```text
不用实时数据，先把页面结构做出来。
```

任务：

```text
- Next.js 初始化
- Tailwind + shadcn/ui
- Layout / Sidebar / Header
- Dashboard mock data
- Candidates mock table
- Positions mock table
- Exit Alerts mock panel
```

验收：

```text
可以打开页面。
可以看到 dashboard。
可以切换主要 tabs。
mock 表格结构清楚。
```

---

## Frontend Phase F1：接 REST API

目标：

```text
从后端读取真实 candidates / positions / alerts。
```

任务：

```text
- TanStack Query setup
- GET /api/dashboard/summary
- GET /api/candidates
- GET /api/positions/open
- GET /api/exit-alerts
- Candidate detail drawer
- Position detail drawer
```

验收：

```text
后端跑完 scan 后，前端能显示候选。
手动录入持仓后，前端能显示。
Exit Engine 生成 alert 后，前端能显示。
```

---

## Frontend Phase F2：实时事件流

目标：

```text
前端不刷新页面，也能看到状态变化。
```

任务：

```text
- 实现 SSE 或 WebSocket client
- RealtimeConnectionBadge
- 事件流接入 candidates
- 事件流接入 positions
- 事件流接入 exit alerts
- Toast / banner for high severity alerts
```

验收：

```text
后端生成 exit alert 后，前端自动更新。
candidate 状态变化后，表格自动更新。
Level 4 Exit 自动弹出明显提醒。
```

---

## Frontend Phase F3：图表和交易计划展示

目标：

```text
减少打开 TradingView 的频率。
```

任务：

```text
- Lightweight Charts 集成
- 显示 candles
- 显示 MA / VWAP
- 显示 entry / stop / invalidation
- 显示 position markers
- 显示 R progression
```

验收：

```text
点击 candidate 能看到 mini chart。
图上有 entry/stop 线。
持仓图上能看到入场点和当前止损。
```

---

## Frontend Phase F4：手动持仓管理

目标：

```text
用户可以在前端记录真实交易执行，但不下单。
```

任务：

```text
- Create manual position form
- Mark reduced
- Mark closed
- Update stop
- Add note
- Journal entry auto generation
```

验收：

```text
用户可以把手动下单结果录入系统。
系统后续能对该持仓生成 exit alerts。
平仓后自动进入 journal。
```

---

## Frontend Phase F5：Options 页面

目标：

```text
显示期权适配结果和风险。
```

任务：

```text
- Underlying selector
- Option suitability summary
- Option chain table
- Spread/OI/IV/DTE filters
- Blocked reason
- Option position view
```

验收：

```text
QQQ/NVDA 等标的能显示期权候选。
不符合规则的合约显示 reject reason。
期权仓位能显示 DTE/IV/Premium 风险。
```

---

## Frontend Phase F6：Journal / Backtest / Analytics

目标：

```text
让系统成为可迭代的训练工具。
```

任务：

```text
- Journal table
- Mistake tags
- R distribution chart
- Equity curve
- Drawdown chart
- Strategy breakdown
- Option vs non-option breakdown
```

验收：

```text
用户能看出哪个策略赚钱。
能看出期权是否拖累收益。
能看出自己是否经常提前卖或止损太晚。
```

---

## 19.16 前端 MVP 推荐顺序

如果资源有限，建议顺序：

```text
1. Dashboard
2. Candidates
3. Positions
4. Exit Alerts
5. Realtime SSE
6. Manual Position Management
7. Mini Charts
8. Options
9. Journal
10. Backtest Analytics
```

理由：

```text
Positions + Exit Alerts 优先级高于 Options。
实时显示优先级高于复杂图表。
Journal 优先级高于美观。
```

---

## 19.17 前端验收标准

### 功能验收

```text
1. 用户无需查看后端日志即可知道系统状态。
2. 用户能实时看到 candidates 更新。
3. 用户能实时看到持仓 P/L 和 R。
4. 用户能实时看到离场提醒。
5. Level 4 Exit 必须明显展示。
6. 用户可以手动录入交易执行结果。
7. 用户可以查看每个信号的理由。
8. 用户可以查看每个仓位的生命周期。
```

### 可用性验收

```text
1. 一眼看出今天能不能交易。
2. 一眼看出当前最危险的仓位。
3. 一眼看出是否触发风险限制。
4. 不需要频繁打开 TradingView。
5. 不需要翻日志找错误。
```

### 安全验收

```text
1. 前端无自动下单入口。
2. 标记平仓/减仓必须说明这是记录，不是交易执行。
3. 修改风险参数需要确认。
4. 禁用 hard stop alert 需要确认。
```

---

## 19.18 前端最终定位

前端不是行情软件，也不是券商终端。

它的定位是：

> 一个实时交易驾驶舱。

它要回答四个问题：

```text
1. 当前市场是否允许交易？
2. 哪些标的值得关注？
3. 我已有仓位是否还成立？
4. 我现在最应该做的是等待、减仓、止损，还是复盘？
```

这会让系统从“后端扫描器 + 通知工具”升级为真正可日常使用的 trading assistant。


---

# 20. 数据库选型与统计分析面板追加设计（v0.3）

## 20.1 结论

正式版建议直接采用：

```text
Frontend:
    Next.js + TypeScript + TanStack Query + Zustand

Backend:
    FastAPI + SQLAlchemy/SQLModel + Pydantic

Primary DB:
    PostgreSQL + TimescaleDB extension

Analytics / Backtest Cache:
    DuckDB + Parquet

Cache / Realtime Event Bus:
    Redis

Object Storage, optional:
    Local filesystem / S3-compatible storage for exported reports, snapshots, backtest artifacts
```

不建议使用：

```text
SQLite as main DB:
    不适合长期承载行情、持仓、统计、实时事件和多任务写入。

Only DuckDB:
    很适合分析和回测，但不适合作为在线交易辅助系统的主业务库。

Only Redis:
    不适合作为持久化数据库。

Only PostgreSQL without TimescaleDB:
    可以做 MVP，但行情 bars、ticks、option snapshots 会越来越大，后续查询和保留策略会更麻烦。
```

---

## 20.2 为什么选 PostgreSQL + TimescaleDB

本系统有两类完全不同的数据：

### A. 业务状态数据

例如：

```text
symbols
candidates
positions
option_positions
exit_alerts
trades_journal
settings
user_notes
watchlists
audit_logs
```

这些数据需要：

```text
事务一致性
关系查询
外键约束
状态更新
审计记录
可靠持久化
```

PostgreSQL 很适合。

### B. 时间序列数据

例如：

```text
bars
ticks
quotes
option_chain_snapshots
market_context_snapshots
portfolio_value_snapshots
position_value_snapshots
realtime_events
```

这些数据特点是：

```text
按时间持续写入
按 symbol + timeframe + 时间范围查询
需要 retention
需要压缩
需要 rollup
需要快速聚合
```

TimescaleDB 是 PostgreSQL extension，可以保留 PostgreSQL 的 SQL、driver 和生态，同时增加 hypertable、time partition、compression、retention、continuous aggregates 等时间序列能力。

---

## 20.3 数据库存储分层

建议把数据分为四层。

```text
Layer 1: Raw Ingestion
    原始 API 返回数据，便于排查和重放。

Layer 2: Normalized Market Data
    标准化 bars、quotes、option snapshots。

Layer 3: Derived Features
    技术指标、PA facts、strategy scores、risk scores。

Layer 4: Product State
    candidates、positions、alerts、journal、analytics snapshots。
```

### Layer 1：Raw Ingestion

```text
raw_vendor_payloads
```

用于：

```text
debug
数据重放
API 返回结构变化排查
审计
```

不建议永久保存所有 raw payload。  
可以设置 7–30 天 retention。

---

### Layer 2：Normalized Market Data

核心表：

```text
bars
ticks
quotes
options_chain_snapshots
market_context_snapshots
```

这些建议建成 Timescale hypertables。

---

### Layer 3：Derived Features

核心表：

```text
technical_features
pa_facts
strategy_scores
risk_scores
option_features
```

这些可以是普通表，也可以是 hypertable，取决于是否按时间持续保存。

---

### Layer 4：Product State

核心表：

```text
candidates
positions
exit_alerts
trades_journal
watchlists
settings
audit_logs
```

这些用普通 PostgreSQL tables。

---

## 20.4 推荐数据库表设计追加

## 20.4.1 raw_vendor_payloads

```sql
CREATE TABLE raw_vendor_payloads (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,              -- massive, jquants, ibkr
    endpoint TEXT NOT NULL,
    symbol TEXT,
    request_params JSONB,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Retention：

```text
保留 7–30 天。
重要异常样本可手动归档。
```

---

## 20.4.2 bars 作为 hypertable

原文档已有 bars 表，v0.3 建议正式版使用 Timescale hypertable。

```sql
CREATE TABLE bars (
    ts TIMESTAMPTZ NOT NULL,
    symbol_id TEXT NOT NULL,
    market TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    timeframe TEXT NOT NULL,      -- 1d, 1h, 30m, 15m, 5m, 1m
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    vwap DOUBLE PRECISION,
    adjusted BOOLEAN DEFAULT FALSE,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (symbol_id, timeframe, ts)
);

SELECT create_hypertable('bars', 'ts', if_not_exists => TRUE);
```

索引：

```sql
CREATE INDEX idx_bars_symbol_tf_ts
ON bars (symbol_id, timeframe, ts DESC);

CREATE INDEX idx_bars_market_tf_ts
ON bars (market, timeframe, ts DESC);
```

---

## 20.4.3 options_chain_snapshots 作为 hypertable

```sql
CREATE TABLE options_chain_snapshots (
    snapshot_ts TIMESTAMPTZ NOT NULL,
    underlying_symbol TEXT NOT NULL,
    option_symbol TEXT NOT NULL,
    expiration DATE NOT NULL,
    strike DOUBLE PRECISION NOT NULL,
    option_type TEXT NOT NULL,     -- call, put
    bid DOUBLE PRECISION,
    ask DOUBLE PRECISION,
    mid DOUBLE PRECISION,
    last DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    open_interest DOUBLE PRECISION,
    iv DOUBLE PRECISION,
    delta DOUBLE PRECISION,
    gamma DOUBLE PRECISION,
    theta DOUBLE PRECISION,
    vega DOUBLE PRECISION,
    dte INTEGER,
    spread_pct DOUBLE PRECISION,
    liquidity_score DOUBLE PRECISION,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (snapshot_ts, option_symbol)
);

SELECT create_hypertable('options_chain_snapshots', 'snapshot_ts', if_not_exists => TRUE);
```

索引：

```sql
CREATE INDEX idx_options_underlying_snapshot
ON options_chain_snapshots (underlying_symbol, snapshot_ts DESC);

CREATE INDEX idx_options_contract_snapshot
ON options_chain_snapshots (option_symbol, snapshot_ts DESC);

CREATE INDEX idx_options_exp_delta
ON options_chain_snapshots (underlying_symbol, expiration, option_type, delta);
```

---

## 20.4.4 portfolio_snapshots

用于统计面板和权益曲线。

```sql
CREATE TABLE portfolio_snapshots (
    ts TIMESTAMPTZ NOT NULL,
    account_id TEXT NOT NULL,
    equity DOUBLE PRECISION NOT NULL,
    cash DOUBLE PRECISION,
    gross_exposure DOUBLE PRECISION,
    net_exposure DOUBLE PRECISION,
    open_risk_amount DOUBLE PRECISION,
    open_risk_pct DOUBLE PRECISION,
    daily_pnl DOUBLE PRECISION,
    realized_pnl DOUBLE PRECISION,
    unrealized_pnl DOUBLE PRECISION,
    drawdown_pct DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (account_id, ts)
);

SELECT create_hypertable('portfolio_snapshots', 'ts', if_not_exists => TRUE);
```

用途：

```text
Dashboard 当前权益
Equity curve
Drawdown curve
每日盈亏
风险占用
```

---

## 20.4.5 position_snapshots

用于前端实时显示持仓变化。

```sql
CREATE TABLE position_snapshots (
    ts TIMESTAMPTZ NOT NULL,
    position_id TEXT NOT NULL,
    symbol_id TEXT NOT NULL,
    current_price DOUBLE PRECISION,
    market_value DOUBLE PRECISION,
    unrealized_pnl DOUBLE PRECISION,
    unrealized_pnl_pct DOUBLE PRECISION,
    r_multiple DOUBLE PRECISION,
    distance_to_stop_pct DOUBLE PRECISION,
    exit_level INTEGER,
    suggested_action TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (position_id, ts)
);

SELECT create_hypertable('position_snapshots', 'ts', if_not_exists => TRUE);
```

---

## 20.4.6 analytics_daily

每日统计快照，避免前端每次重算。

```sql
CREATE TABLE analytics_daily (
    date DATE NOT NULL,
    account_id TEXT NOT NULL,
    equity DOUBLE PRECISION,
    daily_pnl DOUBLE PRECISION,
    daily_pnl_pct DOUBLE PRECISION,
    realized_pnl DOUBLE PRECISION,
    unrealized_pnl DOUBLE PRECISION,
    trades_count INTEGER,
    wins_count INTEGER,
    losses_count INTEGER,
    win_rate DOUBLE PRECISION,
    avg_win DOUBLE PRECISION,
    avg_loss DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    expectancy_r DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    open_positions_count INTEGER,
    option_exposure_pct DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (date, account_id)
);
```

---

## 20.4.7 analytics_strategy_daily

按策略统计。

```sql
CREATE TABLE analytics_strategy_daily (
    date DATE NOT NULL,
    account_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    asset_type TEXT,
    market TEXT,
    trades_count INTEGER,
    wins_count INTEGER,
    losses_count INTEGER,
    win_rate DOUBLE PRECISION,
    gross_profit DOUBLE PRECISION,
    gross_loss DOUBLE PRECISION,
    net_pnl DOUBLE PRECISION,
    avg_r DOUBLE PRECISION,
    median_r DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    expectancy_r DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (date, account_id, strategy_name, asset_type, market)
);
```

---

## 20.4.8 realtime_events

前端实时流事件存储。

```sql
CREATE TABLE realtime_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    market TEXT,
    symbol TEXT,
    entity_type TEXT,             -- candidate, position, alert, system
    entity_id TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

只需要保留近期事件：

```text
7–30 天即可。
```

---

## 20.5 Retention / Compression 建议

### bars

```text
1m / tick:
    保存 3–6 个月，或者只保存 watchlist。
15m / 30m:
    保存 2–3 年。
1h:
    保存 3–5 年。
1d:
    长期保存。
```

### option_chain_snapshots

```text
全链快照很大，不建议永久保存所有。
MVP：
    只保存 watchlist / candidates 的 options chain。
    保存 3–6 个月即可。

长期：
    对关键 underlying 保存更久。
    对非关键数据定期汇总后删除明细。
```

### portfolio / position snapshots

```text
portfolio_snapshots:
    长期保存。

position_snapshots:
    明细保存 1–2 年。
    日级汇总长期保存。
```

---

## 20.6 DuckDB 的角色

DuckDB 不作为在线主库，而作为：

```text
1. Backtest engine 的本地分析库。
2. Parquet 文件查询引擎。
3. 大批量历史数据研究。
4. 策略实验 sandbox。
5. 从 PostgreSQL 导出数据后的离线统计工具。
```

数据流：

```text
PostgreSQL / TimescaleDB
        ↓ export
Parquet
        ↓
DuckDB
        ↓
Backtest / Research / Report
```

适合的任务：

```text
多年度回测
参数扫描
策略分组统计
大表 join
生成报告
```

不适合的任务：

```text
实时持仓状态
实时 alert
用户交互状态
多任务写入
```

---

## 20.7 Redis 的角色

Redis 用于：

```text
1. Realtime event pub/sub。
2. 短期 cache。
3. Job status。
4. Rate limit。
5. WebSocket/SSE fanout。
```

不用于：

```text
长期存储交易记录
长期保存行情
替代 PostgreSQL
```

---

# 21. 标准前端技术设计（v0.3）

## 21.1 直接采用正式前端

既然已经决定使用：

```text
TanStack Query + Zustand
```

则不建议再做 Streamlit MVP。  
前端直接采用标准产品化方案：

```text
Next.js
React
TypeScript
Tailwind CSS
shadcn/ui
TanStack Query
TanStack Table
Zustand
Lightweight Charts
Recharts
SSE first, WebSocket later
```

保留原则：

```text
前端不下单。
前端不直接调用市场数据源。
前端只调用后端 API。
前端实时显示系统计算结果。
```

---

## 21.2 前端目录结构建议

```text
apps/web
├── app
│   ├── dashboard
│   ├── candidates
│   ├── positions
│   ├── exit-alerts
│   ├── options
│   ├── charts
│   ├── journal
│   ├── analytics
│   ├── backtests
│   ├── settings
│   └── system-health
│
├── components
│   ├── common
│   ├── dashboard
│   ├── candidates
│   ├── positions
│   ├── alerts
│   ├── options
│   ├── charts
│   ├── analytics
│   └── layout
│
├── features
│   ├── market-context
│   ├── candidates
│   ├── positions
│   ├── exit-alerts
│   ├── options
│   ├── journal
│   ├── analytics
│   └── realtime
│
├── lib
│   ├── api-client.ts
│   ├── query-client.ts
│   ├── realtime.ts
│   ├── formatters.ts
│   └── validators.ts
│
├── stores
│   ├── ui-store.ts
│   ├── realtime-store.ts
│   ├── filters-store.ts
│   └── preferences-store.ts
│
└── types
    ├── api.ts
    ├── market.ts
    ├── candidates.ts
    ├── positions.ts
    ├── analytics.ts
    └── options.ts
```

---

## 21.3 TanStack Query 使用原则

TanStack Query 管理所有 server state：

```text
market context
dashboard summary
candidates
positions
exit alerts
option analysis
journal
analytics
backtest results
system health
```

推荐 query keys：

```ts
['dashboard', 'summary']
['market-context', market]
['candidates', { market, strategy, decision }]
['candidate', candidateId]
['positions', 'open']
['position', positionId]
['exit-alerts', filters]
['options', underlyingSymbol]
['journal', filters]
['analytics', period, groupBy]
['system-health']
```

实时事件到来后：

```text
candidate.updated:
    queryClient.setQueryData(['candidate', id], ...)
    invalidate ['candidates']

position.updated:
    update ['position', id]
    invalidate ['positions', 'open']
    invalidate ['dashboard', 'summary']

exit_alert.created:
    prepend to ['exit-alerts']
    invalidate ['dashboard', 'summary']
```

原则：

```text
1. REST API 做初始加载。
2. SSE/WebSocket 做增量更新。
3. 高优先级事件触发局部 cache update。
4. 不把所有实时数据塞进 Zustand。
```

---

## 21.4 Zustand 使用原则

Zustand 只管理 client UI state：

```text
selectedSymbol
selectedCandidateId
selectedPositionId
activeMarket
activeTimeframe
sidebarCollapsed
drawerOpen
tableColumnVisibility
tableFilters
realtimeConnected
soundEnabled
theme
```

不要用 Zustand 存：

```text
完整 candidates
完整 positions
完整 bars
完整 option chains
完整 analytics
```

这些属于 server state，交给 TanStack Query。

---

## 21.5 实时显示策略

### 事件优先级

```text
P0:
    Level 4 Exit
    Risk Halt
    Data source failed
    Stop broken

P1:
    Level 3 Reduce
    Candidate triggered
    Option DTE warning

P2:
    Candidate updated
    Position P/L updated
    Market context updated

P3:
    Routine scan completed
    Low priority info
```

### 前端行为

```text
P0:
    顶部固定红色 banner + toast + 声音可选。

P1:
    toast + 页面 badge 更新。

P2:
    静默更新表格。

P3:
    写入 event log，不打扰用户。
```

---

# 22. 统计分析面板设计（v0.3）

## 22.1 为什么统计面板必须做

系统目标不是只找机会，而是验证自己是否真的有 edge。

统计面板要回答：

```text
1. 我整体赚钱吗？
2. 我的胜率是多少？
3. 平均盈利和平均亏损是多少？
4. 盈亏比是否健康？
5. 哪个策略赚钱？
6. 哪个市场赚钱？
7. 期权到底是增益还是拖累？
8. 我是不是经常提前卖？
9. 我是不是亏损拖太久？
10. 当前最大回撤是多少？
```

---

## 22.2 Analytics 页面结构

```text
Analytics
├── Overview
├── P/L
├── Win/Loss
├── R-Multiple
├── Drawdown
├── Strategy Breakdown
├── Asset Breakdown
├── Options Analysis
├── Behavior / Mistake Analysis
└── Calendar View
```

---

## 22.3 Overview 面板

顶部 KPI cards：

```text
Total Equity
Total P/L
Realized P/L
Unrealized P/L
Win Rate
Profit Factor
Expectancy / Trade
Average R
Max Drawdown
Current Drawdown
Number of Trades
Open Risk %
```

建议显示格式：

```text
Win Rate:
    48.2%

Profit Factor:
    1.42

Expectancy:
    +0.18R / trade

Average Win:
    +1.82R

Average Loss:
    -0.92R

Max Drawdown:
    -6.4%
```

---

## 22.4 P/L 面板

图表：

```text
Equity Curve
Daily P/L Bar Chart
Cumulative Realized P/L
Unrealized P/L
Monthly P/L Heatmap
```

表格：

```text
Date
Realized P/L
Unrealized P/L
Daily P/L
Equity
Drawdown
Trades Count
```

---

## 22.5 Win/Loss 面板

指标：

```text
Win Rate
Loss Rate
Average Win
Average Loss
Win/Loss Ratio
Largest Win
Largest Loss
Consecutive Wins
Consecutive Losses
```

图表：

```text
Win/Loss pie
Average win vs average loss bar
Rolling win rate
Rolling profit factor
```

---

## 22.6 R-Multiple 面板

这是最重要的交易统计之一。

图表：

```text
R distribution histogram
Cumulative R curve
Rolling average R
Boxplot by strategy
```

字段：

```text
trade_id
symbol
strategy
setup
entry
exit
r_multiple
holding_days
exit_reason
```

目标：

```text
判断是不是亏损被控制在 -1R 附近。
判断盈利交易是否能达到 +2R/+3R。
判断是否过早止盈。
```

---

## 22.7 Drawdown 面板

显示：

```text
Equity curve with drawdown
Drawdown percentage curve
Max drawdown period
Current drawdown
Days to recover
```

风险规则：

```text
If current_drawdown > 5%:
    show Risk Reduced

If current_drawdown > 10%:
    show Live Trading Halt
```

---

## 22.8 Strategy Breakdown

按策略拆分：

```text
O’Neil-core
ETF Rotation
Breakout
Pullback
Failed Breakdown Reclaim
Option Adapter
Japan Overnight Impact
Manual Override
```

指标：

```text
Trades
Win Rate
Net P/L
Average R
Profit Factor
Max Drawdown
Average Holding Days
Best Trade
Worst Trade
```

用途：

```text
保留赚钱策略。
减少或删除拖累策略。
判断 PA 哪类 setup 最有效。
```

---

## 22.9 Asset Breakdown

按资产类型：

```text
US Stock
US ETF
US Option
JP Stock
JP ETF
```

按市场：

```text
US
JP
```

按 symbol：

```text
QQQ
SPY
SMH
NVDA
7203.T
8035.T
```

目标：

```text
判断自己更适合 ETF、个股还是期权。
判断日股是否真的优于美股。
判断某些 ticker 是否经常亏钱。
```

---

## 22.10 Options Analysis

专门回答：

> 期权到底有没有帮你赚钱？

指标：

```text
Options Net P/L
Options Win Rate
Options Average R
Premium Risk Used
Average DTE Entry
Average DTE Exit
Average IV Entry
Average IV Exit
Theta Loss Estimate
Underlying Direction Correct Rate
Option P/L vs Underlying P/L
```

关键判断：

```text
如果 underlying 判断对但 option 亏：
    多半是 DTE / IV / spread / timing 问题。

如果 option 贡献为负：
    降低期权使用频率或暂停期权模块。

如果 option 只有少数大赚支撑：
    检查是否尾部风险过高。
```

---

## 22.11 Behavior / Mistake Analysis

错误标签统计：

```text
ignored_stop
chased_gap
sold_too_early
held_loser
oversized_option
news_risk_ignored
entered_without_confirmation
exited_against_plan
revenge_trade
overtraded
```

图表：

```text
Mistake frequency
Mistake cost
Mistake by strategy
Mistake by market
Mistake trend over time
```

目标：

```text
让系统不仅统计市场表现，也统计人的执行表现。
```

---

## 22.12 Calendar View

月历视图：

```text
每天显示：
    P/L
    Trades count
    Win/Loss
    Risk mode
    Notes
```

用途：

```text
发现某些日期/事件窗口容易亏钱。
例如 FOMC、CPI、财报季、特朗普 headline risk。
```

---

## 22.13 Analytics API

## Overview

```http
GET /api/analytics/overview?from=YYYY-MM-DD&to=YYYY-MM-DD
```

返回：

```json
{
  "equity": 2150.4,
  "total_pnl": 150.4,
  "realized_pnl": 120.1,
  "unrealized_pnl": 30.3,
  "win_rate": 0.482,
  "profit_factor": 1.42,
  "expectancy_r": 0.18,
  "average_r": 0.12,
  "max_drawdown_pct": -0.064,
  "current_drawdown_pct": -0.018,
  "trades_count": 83,
  "open_risk_pct": 0.012
}
```

---

## Equity Curve

```http
GET /api/analytics/equity-curve?from=&to=&interval=1d
```

---

## R Distribution

```http
GET /api/analytics/r-distribution?from=&to=&group_by=strategy
```

---

## Strategy Breakdown

```http
GET /api/analytics/strategy-breakdown?from=&to=
```

---

## Asset Breakdown

```http
GET /api/analytics/asset-breakdown?from=&to=
```

---

## Options Analytics

```http
GET /api/analytics/options?from=&to=
```

---

## Mistakes

```http
GET /api/analytics/mistakes?from=&to=
```

---

## Calendar

```http
GET /api/analytics/calendar?month=YYYY-MM
```

---

# 23. v0.3 实现计划追加

## Backend DB Phase D0：数据库基础

任务：

```text
- Docker Compose: PostgreSQL + TimescaleDB + Redis
- Alembic migrations
- SQLAlchemy models
- Hypertable migrations
- Seed symbols
- Basic health check
```

验收：

```text
PostgreSQL 正常启动。
TimescaleDB extension 正常启用。
bars/options snapshots 可写入。
Redis 可用于事件广播。
```

---

## Backend DB Phase D1：行情写入

任务：

```text
- bars ingestion 写入 TimescaleDB
- option chain snapshots 写入 TimescaleDB
- market context snapshots 写入
- 数据更新时间记录
```

验收：

```text
能写入 US ETF 日线。
能写入 selected underlying option chain。
能查询最近 N 根 bar。
能显示 data freshness。
```

---

## Backend DB Phase D2：业务状态

任务：

```text
- candidates table
- positions table
- exit_alerts table
- journal table
- watchlist table
- audit_logs table
```

验收：

```text
Scanner 结果能落库。
前端能读取 candidates。
用户能录入 position。
Exit Engine 能生成 alert。
```

---

## Backend DB Phase D3：统计快照

任务：

```text
- portfolio_snapshots
- position_snapshots
- analytics_daily
- analytics_strategy_daily
- daily analytics job
```

验收：

```text
Dashboard 能显示 equity/PnL。
Analytics 页面能显示 win rate/profit factor/expectancy。
```

---

## Frontend Phase F0：标准前端骨架

任务：

```text
- Next.js + TypeScript
- Tailwind + shadcn/ui
- TanStack Query
- Zustand
- Layout / Sidebar / Header
- Theme
```

验收：

```text
能打开标准 Web UI。
能访问 Dashboard / Candidates / Positions / Analytics。
```

---

## Frontend Phase F1：Dashboard + Candidates + Positions

任务：

```text
- Dashboard summary
- Candidate table
- Position table
- Exit alert panel
- Detail drawer
```

验收：

```text
后端数据落库后，前端能显示。
用户无需看日志即可知道系统状态。
```

---

## Frontend Phase F2：Realtime SSE

任务：

```text
- SSE endpoint
- frontend realtime client
- event cache update
- Risk banner
- Level 4 Exit toast/banner
```

验收：

```text
Exit alert 生成后，前端自动显示。
Candidate 状态变化自动更新。
```

---

## Frontend Phase F3：Analytics 面板

任务：

```text
- Overview KPI cards
- Equity curve
- Daily P/L chart
- Win/loss panel
- R distribution
- Strategy breakdown
- Options analytics
- Mistake analysis
```

验收：

```text
用户能看到胜率、盈利、损失、平均 R、最大回撤。
用户能判断期权是否拖累收益。
用户能判断哪个策略有效。
```

---

## Frontend Phase F4：Charts + Options + Journal

任务：

```text
- Lightweight Charts
- Entry/stop/invalidation lines
- Option chain table
- Option suitability panel
- Journal table
- Mistake tags
```

验收：

```text
点击候选能看到系统内部图表。
期权页面能显示 DTE/IV/spread/risk。
Journal 能记录每笔交易复盘。
```

---

# 24. v0.3 最终技术栈定稿

```text
Frontend:
    Next.js
    React
    TypeScript
    Tailwind CSS
    shadcn/ui
    TanStack Query
    TanStack Table
    Zustand
    Lightweight Charts
    Recharts

Backend:
    Python
    FastAPI
    Pydantic
    SQLAlchemy / SQLModel
    Alembic
    Polars / pandas

Database:
    PostgreSQL + TimescaleDB
    DuckDB for research/backtest
    Redis for realtime/cache

Data:
    Polygon/Massive
    J-Quants
    IBKR optional for limited L1/L2
    Manual inputs

Realtime:
    SSE first
    WebSocket later

Deployment:
    Docker Compose for local
    Later: VPS or home server
```

---

# 25. v0.3 核心产品判断

追加标准前端和统计面板后，系统定位进一步明确：

> 这不是一个提醒脚本，而是一个完整的交易驾驶舱。

它必须同时做到：

```text
1. 发现机会。
2. 展示机会。
3. 管理仓位。
4. 提醒离场。
5. 统计结果。
6. 纠正行为。
7. 验证策略。
```

其中统计面板非常关键。  
没有统计面板，用户无法知道自己到底是在赚钱、亏钱，还是被少数偶然盈利欺骗。

最终判断标准不是“今天有没有信号”，而是：

```text
50–100 笔后：
    expectancy 是否为正？
    max drawdown 是否可控？
    option contribution 是否为正？
    哪些 setup 应该保留？
    哪些行为错误最贵？
```


---

# 26. Cashflow Target Engine：动态现金流目标系统（v0.4）

## 26.1 为什么必须追加这个模块

v0.3 已经覆盖：

```text
1. 后端扫描器
2. 数据库
3. 标准前端
4. 实时面板
5. 持仓管理
6. 离场提醒
7. 统计分析
```

但用户的核心目标进一步明确为：

> EdgePilot 需要为用户产生交易现金流，起始目标是每月赚 1 万人民币等值，并且这个目标未来会提高。

因此系统不能只统计盈利，还必须管理：

```text
1. 当前现金流目标是多少。
2. 目标对应多少日元/美元。
3. 目标是税前还是税后。
4. 当前账户规模是否支持这个目标。
5. 达到目标还需要多少收益。
6. 本月是否应该继续交易。
7. 达到目标后是否应该降风险。
8. 未达到目标时是否禁止追风险。
9. 目标提高后需要多少本金。
10. 过去 12 个月滚动平均是否达标。
```

这部分是 EdgePilot 从“交易辅助系统”升级为“现金流交易系统”的关键。

---

## 26.2 核心原则

### 原则 1：目标可以增长，但风险不能失控

```text
现金流目标可以从 1 万 RMB/月提高到 2 万、3 万、5 万 RMB/月。
但仓位、期权、杠杆、交易频率不能因为目标提高而无纪律提高。
```

### 原则 2：目标由账户规模和系统表现解锁

系统不允许用户仅凭意愿把目标上调到不现实水平。

目标上调必须至少考虑：

```text
1. Account equity
2. 最近 50–100 笔 expectancy
3. 最大回撤
4. 规则执行率
5. 期权模块贡献
6. 连续亏损次数
7. 是否触发过 Risk Halt
```

### 原则 3：现金流只看已实现税后收益

系统必须区分：

```text
Gross P/L:
    税前收益

Tax Reserve:
    税金预留

Net Cashflow:
    税后可用现金流

Unrealized P/L:
    浮盈浮亏，不作为现金流目标完成依据
```

### 原则 4：目标未达成不是加风险理由

系统必须写死：

```text
Monthly target gap is not a valid trading signal.
```

也就是说：

```text
本月没赚够 ≠ 可以买低质量 setup
本月没赚够 ≠ 可以加仓
本月没赚够 ≠ 可以买更短期期权
本月没赚够 ≠ 可以报复交易
```

---

## 26.3 Cashflow Target Engine 的职责

Cashflow Target Engine 负责：

```text
1. 管理目标货币：RMB / JPY / USD。
2. 管理目标类型：税前 / 税后。
3. 计算目标等值金额。
4. 计算税前所需盈利。
5. 计算当前本月进度。
6. 计算剩余目标金额。
7. 计算所需月收益率。
8. 判断目标可行性。
9. 控制本月风险状态。
10. 达成目标后触发 Profit Lock。
11. 生成 Profit Sweep 提示。
12. 生成 Rolling 12M Cashflow 统计。
13. 为前端 Cashflow Dashboard 提供数据。
```

---

## 26.4 目标换算逻辑

目标可以由用户设置：

```yaml
cashflow_target:
  target_currency: RMB
  target_net_amount: 10000
  target_type: net_after_tax
  display_currencies:
    - JPY
    - USD
    - RMB
```

汇率来源：

```text
Phase 1:
    手动配置或每日 batch 更新。

Phase 2:
    使用 Polygon/Massive forex 数据或其他 FX 数据源。

Phase 3:
    保存每日 FX snapshot，用于税务和历史现金流回放。
```

注意：

```text
不要在系统里硬编码固定汇率。
目标金额必须通过 fx_rates 表按日期换算。
```

---

## 26.5 税后现金流计算

系统需要支持税率参数化。

默认配置：

```yaml
tax:
  taxable_account_capital_gains_rate: 0.20315
  apply_tax_reserve: true
  tax_reserve_currency: JPY
```

计算：

```text
tax_reserve = realized_profit * tax_rate
net_cashflow = realized_profit - tax_reserve
```

注意：

```text
1. 这只是交易现金流系统里的估算。
2. 实际税务应由用户根据日本税务规则和券商报表确认。
3. 系统不提供税务建议，只保留记录和估算。
```

---

## 26.6 Cashflow Target Ladder

目标不应只有一个固定数字，而应设计为阶梯。

```text
Level 0:
    Training Mode
    不追固定现金流，只验证正期望。

Level 1:
    Small Cashflow
    1000–3000 RMB/月等值。

Level 2:
    Early Cashflow
    5000 RMB/月等值。

Level 3:
    Primary Target
    10000 RMB/月等值。

Level 4:
    Advanced Target
    20000 RMB/月等值。

Level 5:
    Professional Target
    30000+ RMB/月等值。
```

每个 level 需要配置：

```text
target_net_amount
minimum_account_equity
max_required_monthly_return
minimum_trades_sample
minimum_expectancy_r
max_allowed_drawdown
minimum_discipline_score
option_module_requirement
```

示例：

```yaml
cashflow_ladder:
  level_3:
    label: "Primary Target"
    target_currency: RMB
    target_net_amount: 10000
    minimum_account_equity_usd: 50000
    recommended_account_equity_usd: 75000
    max_required_monthly_return_pct: 0.04
    preferred_required_monthly_return_pct: 0.02
    minimum_trade_sample: 100
    minimum_expectancy_r: 0.10
    max_drawdown_pct: 0.10
    minimum_discipline_score: 0.95
```

---

## 26.7 目标可行性状态

Cashflow Target Engine 每天输出目标可行性。

```text
Green:
    required monthly return <= 2%
    expectancy positive
    drawdown controlled
    risk status normal

Yellow:
    required monthly return > 2% and <= 4%
    only A/A+ setups allowed
    options limited

Orange:
    required monthly return > 4% and <= 8%
    target is aggressive
    system warns against overtrading

Red:
    required monthly return > 8%
    target is not feasible with current capital
    system blocks target-chasing behavior
```

示例：

```text
Current account: $2,000
Monthly net target: 10,000 RMB
Required return: extremely high
Feasibility: Red
Action: Training mode only. Do not increase risk.
```

---

## 26.8 Required Capital Calculator

系统应提供反向计算：

> 要达到目标，需要多少账户本金？

输入：

```text
target_net_cashflow
tax_rate
assumed_monthly_return
```

输出：

```text
required_pre_tax_profit
required_account_equity
```

公式：

```text
required_pre_tax_profit = target_net_cashflow / (1 - tax_rate)
required_equity = required_pre_tax_profit / assumed_monthly_return
```

前端显示不同收益率假设：

```text
1% / month
1.5% / month
2% / month
3% / month
5% / month
```

用途：

```text
让用户明确知道：
当前本金是否支持目标。
目标上涨后需要多少本金。
不允许用不现实月收益率倒逼交易风险。
```

---

## 26.9 Monthly Cashflow Dashboard

新增前端页面：

```text
Cashflow
├── Monthly Target
├── Progress
├── Feasibility
├── Required Capital
├── Profit Lock
├── Profit Sweep
├── Rolling 12M
└── Cashflow Breakdown
```

### 顶部 KPI

```text
Current Monthly Target
Target Currency
Target Type: Gross / Net
Target Equivalent: JPY / USD / RMB
Required Pre-tax Profit
Current Realized P/L
Current Tax Reserve
Current Net Cashflow
Unrealized P/L
Progress %
Remaining Target
Required Return This Month
Feasibility Status
Current Risk Mode
```

### 示例显示

```text
Target:
    10,000 RMB net

Equivalent:
    JPY / USD based on today's FX rate

Current Realized P/L:
    $420

Tax Reserve:
    $85

Net Cashflow:
    $335

Progress:
    23%

Status:
    Continue only A+ setups
```

---

## 26.10 Realized / Unrealized 分离

系统必须明确：

```text
Realized P/L:
    可以计入现金流。

Unrealized P/L:
    不计入现金流目标，只显示为潜在收益。

After-tax Net Cashflow:
    目标进度的核心指标。
```

Dashboard 上禁止把浮盈当作目标达成。

显示规则：

```text
If target progress uses unrealized_pnl:
    disallow

If realized net cashflow >= monthly target:
    target_reached = true
```

---

## 26.11 Monthly Profit Lock

当本月盈利达到目标，系统要自动降低风险。

建议规则：

```text
Progress < 50%:
    Normal risk rules.

Progress >= 50%:
    Only A/A+ setups.
    No B setups.

Progress >= 100%:
    New trade risk reduced by 50%.
    New options disabled or reduced to micro size.
    No ordinary breakout chase.

Progress >= 150%:
    No new option positions.
    Only manage existing positions.
    Consider profit sweep.

Monthly drawdown <= -30% of target:
    Reduce risk by 50%.

Monthly drawdown <= -50% of target:
    Stop live trading for the month or switch to paper mode.
```

这能防止：

```text
月初赚到目标，月底吐回去。
```

---

## 26.12 No Target-Chasing Rule

系统必须明确：

```text
目标缺口不是交易信号。
```

如果本月还差很多，但没有 A+ setup，系统应该输出：

```text
No valid setup.
Monthly target gap does not justify additional risk.
Stay flat.
```

规则：

```text
If candidate_quality < threshold:
    block trade
    even if monthly target not reached

If option risk exceeds limit:
    block option
    even if monthly target not reached

If account drawdown active:
    block risk increase
    even if monthly target not reached
```

---

## 26.13 Profit Sweep

当交易账户盈利后，系统提示把部分利润转入 FIRE Core / NISA / 储蓄 / 长期投资。

配置：

```yaml
profit_sweep:
  enabled: true
  trigger: account_new_high
  sweep_profit_pct: 0.3
  sweep_destination:
    - cash_reserve
    - long_term_investment
    - nisa
```

触发条件：

```text
1. Trading account reaches new high.
2. Monthly net cashflow exceeds target.
3. Rolling 3M net cashflow positive.
```

输出：

```text
Trading account reached new high.
Profit above previous high: $X.
Suggested sweep: 30%–50%.
Destination: FIRE Core / Cash Reserve.
```

目标：

```text
把交易 alpha 转化为长期资产，避免盈利一直留在交易账户里被吐回去。
```

---

## 26.14 Rolling 12M Cashflow Analytics

现金流目标不应要求每月都达标，因为交易收入不稳定。

核心 KPI：

```text
Rolling 12M Average Net Cashflow
Rolling 6M Average Net Cashflow
Rolling 3M Average Net Cashflow
```

系统显示：

```text
Monthly target:
    10,000 RMB net

Rolling 12M average:
    7,800 RMB net

Status:
    Below target but improving
```

或：

```text
Rolling 12M average:
    12,300 RMB net

Status:
    Target achieved on rolling basis
```

---

## 26.15 Cashflow Strategy Breakdown

系统需要显示现金流来自哪里：

```text
ETF Swing
O’Neil-core Stocks
JP Stocks
US Options
Manual Trades
Other
```

指标：

```text
Realized P/L
Tax reserve
Net cashflow
Win rate
Profit factor
Expectancy R
Max drawdown
Contribution %
```

目标：

```text
判断哪个策略真正贡献现金流。
判断期权是增益还是拖累。
判断日股和美股哪个更适合现金流目标。
```

---

## 26.16 Dynamic Target Increase Rules

目标提高必须满足条件。

### 允许提高目标的条件

```text
1. 当前 level 连续 3–6 个月 rolling net cashflow 达标。
2. 最近 100 笔 expectancy > 0。
3. 最大回撤在限制内。
4. 规则执行率 >= 95%。
5. 没有因为期权导致大额回撤。
6. 当前 required monthly return 不超过系统上限。
7. 账户本金达到下一目标 level 的 minimum equity。
```

### 禁止提高目标的条件

```text
1. 最近 50 笔 expectancy <= 0。
2. 最近 3 个月 cashflow 不稳定且最大回撤扩大。
3. 规则执行率 < 90%。
4. 期权模块净亏损且仍在使用。
5. 账户处于 drawdown。
6. required return > 8%/month。
```

---

# 27. Cashflow 数据库设计（v0.4）

## 27.1 cashflow_targets

```sql
CREATE TABLE cashflow_targets (
    target_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    label TEXT,
    target_currency TEXT NOT NULL,          -- RMB, JPY, USD
    target_net_amount DOUBLE PRECISION NOT NULL,
    target_type TEXT NOT NULL,              -- gross, net_after_tax
    active BOOLEAN DEFAULT TRUE,
    min_account_equity_usd DOUBLE PRECISION,
    recommended_account_equity_usd DOUBLE PRECISION,
    max_required_monthly_return_pct DOUBLE PRECISION,
    min_trade_sample INTEGER,
    min_expectancy_r DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    min_discipline_score DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 27.2 fx_rates

```sql
CREATE TABLE fx_rates (
    date DATE NOT NULL,
    base_currency TEXT NOT NULL,
    quote_currency TEXT NOT NULL,
    rate DOUBLE PRECISION NOT NULL,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (date, base_currency, quote_currency)
);
```

用途：

```text
RMB -> JPY
RMB -> USD
USD -> JPY
交易记录换算
现金流目标换算
税务记录辅助
```

---

## 27.3 monthly_cashflow_snapshots

```sql
CREATE TABLE monthly_cashflow_snapshots (
    month DATE NOT NULL,
    account_id TEXT NOT NULL,
    target_id TEXT,
    target_net_amount_base DOUBLE PRECISION,
    target_currency TEXT,
    target_equiv_jpy DOUBLE PRECISION,
    target_equiv_usd DOUBLE PRECISION,
    required_pre_tax_profit DOUBLE PRECISION,
    realized_pnl DOUBLE PRECISION,
    unrealized_pnl DOUBLE PRECISION,
    tax_reserve DOUBLE PRECISION,
    net_cashflow DOUBLE PRECISION,
    progress_pct DOUBLE PRECISION,
    remaining_target DOUBLE PRECISION,
    required_monthly_return_pct DOUBLE PRECISION,
    feasibility_status TEXT,        -- green, yellow, orange, red
    profit_lock_status TEXT,        -- normal, a_plus_only, reduce_risk, protect
    risk_mode TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (month, account_id)
);
```

---

## 27.4 profit_sweep_events

```sql
CREATE TABLE profit_sweep_events (
    sweep_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    trigger_type TEXT,              -- new_high, target_reached, rolling_positive
    trigger_ts TIMESTAMPTZ NOT NULL,
    profit_amount DOUBLE PRECISION,
    suggested_sweep_pct DOUBLE PRECISION,
    suggested_sweep_amount DOUBLE PRECISION,
    destination TEXT,               -- cash_reserve, nisa, long_term, manual
    status TEXT,                    -- suggested, accepted, ignored, completed
    user_note TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 27.5 cashflow_strategy_breakdown

```sql
CREATE TABLE cashflow_strategy_breakdown (
    month DATE NOT NULL,
    account_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    market TEXT,
    asset_type TEXT,
    realized_pnl DOUBLE PRECISION,
    tax_reserve DOUBLE PRECISION,
    net_cashflow DOUBLE PRECISION,
    trades_count INTEGER,
    wins_count INTEGER,
    losses_count INTEGER,
    win_rate DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    expectancy_r DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    contribution_pct DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (month, account_id, strategy_name, market, asset_type)
);
```

---

# 28. Cashflow API 设计（v0.4）

## 28.1 获取当前现金流目标状态

```http
GET /api/cashflow/current
```

返回：

```json
{
  "target": {
    "level": 3,
    "label": "Primary Target",
    "target_currency": "RMB",
    "target_net_amount": 10000,
    "target_type": "net_after_tax"
  },
  "equivalent": {
    "jpy": 0,
    "usd": 0
  },
  "current_month": {
    "realized_pnl": 0,
    "unrealized_pnl": 0,
    "tax_reserve": 0,
    "net_cashflow": 0,
    "progress_pct": 0,
    "remaining_target": 0,
    "required_monthly_return_pct": 0
  },
  "feasibility_status": "red",
  "profit_lock_status": "normal",
  "message": "Current account size does not support this target. Training mode recommended."
}
```

---

## 28.2 更新目标

```http
POST /api/cashflow/targets
PATCH /api/cashflow/targets/{target_id}
```

提高目标时必须返回 feasibility check：

```json
{
  "allowed": false,
  "reason": "Required monthly return exceeds max threshold.",
  "required_account_equity": 75000
}
```

---

## 28.3 Required Capital Calculator

```http
GET /api/cashflow/required-capital?target_currency=RMB&target_net_amount=10000
```

返回：

```json
{
  "target_net_amount": 10000,
  "target_currency": "RMB",
  "required_pre_tax_profit": {
    "usd": 0,
    "jpy": 0
  },
  "scenarios": [
    {
      "monthly_return_pct": 0.01,
      "required_equity_usd": 0
    },
    {
      "monthly_return_pct": 0.02,
      "required_equity_usd": 0
    },
    {
      "monthly_return_pct": 0.03,
      "required_equity_usd": 0
    },
    {
      "monthly_return_pct": 0.05,
      "required_equity_usd": 0
    }
  ]
}
```

---

## 28.4 Rolling Cashflow

```http
GET /api/cashflow/rolling?window=12m
```

返回：

```json
{
  "rolling_3m_avg": 0,
  "rolling_6m_avg": 0,
  "rolling_12m_avg": 0,
  "target": 10000,
  "target_currency": "RMB",
  "status": "below_target"
}
```

---

## 28.5 Profit Sweep

```http
GET /api/cashflow/profit-sweep/suggestions
POST /api/cashflow/profit-sweep/{sweep_id}/accept
POST /api/cashflow/profit-sweep/{sweep_id}/ignore
POST /api/cashflow/profit-sweep/{sweep_id}/complete
```

---

# 29. Cashflow 前端页面设计（v0.4）

## 29.1 新增主导航

在主导航新增：

```text
Cashflow
```

放在：

```text
Dashboard
Candidates
Positions
Exit Alerts
Cashflow
Analytics
Journal
Settings
```

---

## 29.2 Cashflow 页面结构

```text
Cashflow Dashboard
├── Target Summary Cards
├── Feasibility Banner
├── Monthly Progress Bar
├── Required Capital Scenarios
├── Realized vs Unrealized
├── Tax Reserve
├── Profit Lock Status
├── Profit Sweep Suggestions
├── Rolling 12M Cashflow
├── Strategy Cashflow Breakdown
└── Target Ladder
```

---

## 29.3 Target Summary Cards

显示：

```text
Current Target:
    10,000 RMB net / month

Equivalent:
    JPY / USD

Required Pre-tax Profit:
    JPY / USD

Current Net Cashflow:
    JPY / USD / RMB

Progress:
    0–100%+

Feasibility:
    Green / Yellow / Orange / Red
```

---

## 29.4 Feasibility Banner

状态：

```text
Green:
    Target feasible under current risk model.

Yellow:
    Target difficult. A/A+ setups only.

Orange:
    Target aggressive. Risk of overtrading.

Red:
    Target not feasible with current capital.
    Training mode recommended.
```

示例文案：

```text
Current target requires unrealistic monthly return.
Do not increase risk to chase target.
```

---

## 29.5 Required Capital Scenarios

表格：

```text
Assumed Monthly Return | Required Equity | Feasibility
1.0%                   | $X              | Conservative
1.5%                   | $X              | Moderate
2.0%                   | $X              | Strong
3.0%                   | $X              | Aggressive
5.0%                   | $X              | Very Aggressive
```

---

## 29.6 Monthly Profit Lock Panel

显示：

```text
Current Progress
Current Month Risk Mode
Allowed Setup Grade
Option Permission
New Trade Risk Multiplier
```

规则展示：

```text
Progress >= 100%:
    New trade risk reduced by 50%.
    Options disabled or micro-size only.
```

---

## 29.7 Profit Sweep Panel

显示：

```text
Sweep Trigger
Suggested Sweep Amount
Destination
Status
```

按钮：

```text
Mark Accepted
Mark Ignored
Mark Completed
```

注意：

```text
这只是记录和提醒，不自动转账。
```

---

## 29.8 Rolling 12M Cashflow Chart

显示：

```text
Monthly net cashflow bars
Target line
Rolling 3M average
Rolling 6M average
Rolling 12M average
```

目标：

```text
判断现金流是否稳定接近目标，而不是只看单月结果。
```

---

## 29.9 Target Ladder UI

显示每个 level：

```text
Level
Target
Required Equity
Unlocked / Locked
Reason
```

示例：

```text
Level 3: 10,000 RMB/month
Status: Locked
Reason:
    Account equity below recommended level.
    Required monthly return too high.
```

---

# 30. Cashflow 风控规则（v0.4）

## 30.1 现金流目标不得覆盖原始风控

以下规则优先级高于现金流目标：

```text
Hard stop
Daily loss limit
Weekly loss limit
Account drawdown stop
Option premium cap
No 0DTE
No naked short options
No revenge trade
No target chasing
```

## 30.2 新仓风险乘数

根据现金流状态调整：

```text
Normal:
    risk_multiplier = 1.0

Progress >= 50%:
    risk_multiplier = 0.75

Progress >= 100%:
    risk_multiplier = 0.5

Progress >= 150%:
    risk_multiplier = 0.0 for new option positions
```

## 30.3 目标缺口禁止影响 setup 分数

```text
Setup Quality Score 不允许因为 remaining_target 增加而提高。
```

换句话说：

```text
目标还差很多，不能让 B 级 setup 被升级成 A 级。
```

## 30.4 目标达成后不允许扩大风险

```text
If monthly target reached:
    block increasing max_trade_risk_pct
    block increasing option premium cap
    block enabling aggressive options
```

---

# 31. Cashflow 实现计划（v0.4）

## Backend Phase C0：现金流配置

任务：

```text
- cashflow_targets table
- fx_rates table
- tax config
- target config loader
```

验收：

```text
可以创建 1 万 RMB 税后月目标。
可以配置税率。
可以读取/写入 FX rates。
```

---

## Backend Phase C1：现金流计算

任务：

```text
- realized P/L aggregation
- tax reserve calculation
- net cashflow calculation
- monthly progress calculation
- required return calculation
- feasibility status calculation
```

验收：

```text
系统能计算本月税后现金流。
系统能判断目标可行性。
系统能输出 remaining target。
```

---

## Backend Phase C2：Required Capital Calculator

任务：

```text
- 实现目标反推本金 API
- 支持 1%、1.5%、2%、3%、5% 月收益率情景
- 支持 RMB/JPY/USD 显示
```

验收：

```text
用户输入目标后，系统能显示不同收益率下需要多少本金。
```

---

## Backend Phase C3：Profit Lock / No Target-Chasing

任务：

```text
- 根据 progress 调整 risk_multiplier
- 达标后降低新仓风险
- 未达标禁止提高风险
- 目标缺口不能提高 setup score
```

验收：

```text
本月达标后，系统自动降低风险。
本月未达标时，低质量信号不会被升级。
```

---

## Backend Phase C4：Profit Sweep

任务：

```text
- 检测 account new high
- 检测 monthly target reached
- 生成 sweep suggestion
- 支持 accepted / ignored / completed 状态
```

验收：

```text
账户创新高后，系统给出利润转出建议。
```

---

## Frontend Phase C5：Cashflow 页面

任务：

```text
- Cashflow route
- Target cards
- Progress bar
- Feasibility banner
- Required capital table
- Profit lock panel
- Profit sweep panel
- Rolling cashflow chart
- Target ladder
```

验收：

```text
用户能一眼看到：
    本月目标
    当前进度
    税后现金流
    可行性
    是否应该降风险
    目标提高是否解锁
```

---

## Analytics Phase C6：Rolling Cashflow

任务：

```text
- rolling 3M/6M/12M
- strategy cashflow breakdown
- option contribution to cashflow
- monthly target hit rate
```

验收：

```text
系统能显示过去 12 个月平均现金流是否达到目标。
系统能显示哪些策略贡献现金流。
```

---

# 32. v0.4 对系统定位的更新

v0.3 的定位是：

> 一个实时交易驾驶舱。

v0.4 之后定位升级为：

> 一个以动态现金流为目标的纪律交易驾驶舱。

它不仅回答：

```text
1. 今天能不能交易？
2. 哪些标的值得关注？
3. 仓位是否该离场？
4. 策略是否有 edge？
```

还要回答：

```text
5. 本月现金流目标完成了吗？
6. 当前目标是否现实？
7. 目标提高需要多少本金？
8. 达标后是否应该降风险？
9. 未达标时是否禁止追风险？
10. 交易盈利是否真的变成可用现金流？
```

最终核心：

> EdgePilot 可以追求每月 1 万 RMB 等值现金流，并支持目标逐步提高；但系统必须把目标增长绑定到账户规模、真实 edge 和最大回撤能力，而不是让目标倒逼风险。


---

# 33. Testing & Validation Engine：测试与验证系统（v0.5）

## 33.1 为什么必须追加这个模块

v0.4 已经把 EdgePilot 扩展为“以动态现金流为目标的纪律交易驾驶舱”。但是如果没有独立的 Testing & Validation Engine，系统仍然存在一个核心风险：

> 系统设计看起来完整，但没有证明它真的有 edge。

因此 v0.5 将 Backtest / Paper Trading 从“后期功能”提升为核心模块，并要求：

```text
1. 先验证数据质量。
2. 再验证 ETF 基础策略。
3. 再进入 Shadow Mode。
4. 再进入 Paper Trading。
5. 再进入 Micro Live。
6. 最后才允许小额正式 Live 和期权实盘。
```

核心原则：

```text
No validation, no live trading.
```

---

## 33.2 Testing & Validation Engine 的职责

该模块负责：

```text
1. 数据质量检查。
2. 历史回测。
3. Shadow Trading。
4. Paper Trading。
5. Micro Live 跟踪。
6. Go-Live Gate。
7. Signal Funnel 统计。
8. Setup Quality Calibration。
9. MFE / MAE 分析。
10. 策略熔断。
11. 执行风险评估。
12. Manual Override 审计。
13. 实盘扩容资格判断。
```

它的目标不是“证明系统一定赚钱”，而是：

```text
1. 证明系统不会因为数据错误产生错误信号。
2. 证明信号有可统计的正期望。
3. 证明 Exit Engine 能控制亏损并保护盈利。
4. 证明用户能按规则执行。
5. 证明期权模块不会拖累系统。
```

---

# 34. 分阶段测试协议

## 34.1 Stage 0：Data Quality Test

### 目标

确认系统数据可信，避免因为数据错误造成错误信号。

### 时间

```text
至少 10 个交易日，建议 2 周。
```

### 检查内容

```text
Polygon/Massive:
    US daily bars 是否完整。
    ETF bars 是否完整。
    15m/60m aggregates 是否完整。
    option chain 是否可用。
    quote/greeks/IV 是否更新时间正常。

J-Quants:
    日股日线是否更新。
    listed info 是否正常。
    财务数据是否可读取。
    分足/Tick add-on 是否按预期更新，若启用。

系统时间:
    美国时间 / 日本时间 / 夏令时 是否正确。
    bars timestamp 是否统一。
    scan schedule 是否正确。

Corporate actions:
    split 是否处理。
    adjusted price 是否一致。
    dividend adjustment 是否明确。

System jobs:
    ingestion 是否成功。
    scanner 是否运行。
    Exit Engine 是否运行。
    Dashboard 是否更新时间正确。
```

### 验收标准

```text
连续 10 个交易日无 P0 数据错误。
核心 batch jobs 成功率 > 95%。
核心行情数据缺失率 < 1%。
Exit Engine 每天正常运行。
System Health 页面显示正常。
```

### 不通过时

```text
禁止 Backtest 进入下一阶段。
禁止 Paper Trading。
禁止 Live Trading。
```

---

## 34.2 Stage 1：ETF-only Historical Backtest

### 目标

先用低噪音、高流动性 ETF 验证系统基础 edge。

### Universe

```text
SPY
QQQ
IWM
SMH
SOXX
TLT
GLD
XLK
XLF
XLE
```

### 策略范围

```text
ETF Rotation
Breakout
Pullback
Market Regime Filter
Exit Engine
```

### 不测试

```text
个股。
日股小票。
期权。
财报策略。
复杂 PA。
```

### 回测要求

```text
至少 2–3 年历史。
覆盖牛市、震荡、下跌和反弹环境。
必须扣除手续费。
必须模拟滑点。
必须记录 R multiple。
必须记录 MFE / MAE。
必须记录 market regime。
必须记录 signal funnel。
```

### 验收标准

```text
Average R > 0
Profit Factor > 1.15
Max Drawdown < 10%
单笔亏损基本控制在 -1R 附近
没有依赖 1–2 笔极端盈利
Strategy Kill Switch 未频繁触发
```

### 不通过时

```text
暂停个股和期权开发优先级。
优先修复 Market Regime / Exit Engine / PA Quality。
```

---

## 34.3 Stage 2：Shadow Mode

### 定义

Shadow Mode 是实时市场模拟，但用户不下单。  
系统每天照常生成候选、触发、离场，并记录“如果执行会发生什么”。

### 时间

```text
4–8 周。
```

### 记录字段

```text
candidate_time
trigger_time
simulated_entry
simulated_stop
simulated_position_size
simulated_exit
exit_reason
final_R
MFE
MAE
market_regime
setup_quality_score
context_score
option_suitability
whether_user_would_take
```

### 验收标准

```text
至少 30–50 个触发信号。
平均 R > 0。
Exit Engine 无明显逻辑错误。
没有大量误触发。
系统能正确说“不交易”。
Signal Funnel 数据完整。
```

### 重点观察

```text
候选是否太多。
触发是否太频繁。
触发后是否快速失败。
Exit 是否过早或过晚。
No Trade Engine 是否有效。
```

---

## 34.4 Stage 3：Paper Trading

### 类型 A：System Paper

系统按规则自动记录模拟成交。

优点：

```text
完全纪律化。
适合验证策略本身。
```

缺点：

```text
不能测试用户心理。
```

### 类型 B：Manual Paper

用户在前端点击：

```text
I would enter
I would reduce
I would exit
```

但不下真实单。

优点：

```text
测试用户是否能按系统执行。
测试用户是否会追单。
测试用户是否会忽略 Exit Alert。
```

缺点：

```text
没有真实亏钱压力。
```

### 时间

```text
1–3 个月。
```

### 验收标准

```text
至少 50 笔 paper trades。
Rule adherence > 95%。
Average R > 0。
Profit Factor > 1.20。
Max Drawdown < 8%。
Option paper trades 单独统计，不得拖累整体。
```

---

## 34.5 Stage 4：Micro Live，不做期权

### 目标

测试真实执行和真实心理，而不是赚钱。

### 允许范围

```text
ETF
高流动性美股大票
少数日股大票，若数据已稳定
```

### 禁止范围

```text
期权实盘。
小盘股。
财报前交易。
低流动性标的。
B 级 setup。
```

### 风险

```text
每笔风险 0.1%–0.25%。
最多 1–2 个仓位。
连续亏 3 笔停止。
月亏损 -3R 停止。
```

### 验收标准

```text
20–30 笔 micro live trades。
无重大规则违反。
真实成交与模拟成交差异可接受。
没有报复交易。
没有忽略 Level 4 Exit。
Manual Override 亏损不显著。
```

---

## 34.6 Stage 5：Small Live

### 目标

进入小额正式交易，但仍以验证 edge 为主。

### 风险

```text
每笔风险 0.25%–0.5%。
最多 1–3 个仓位。
期权仍然默认禁用或 micro-size。
只做 A/A+ setup。
```

### 验收标准

```text
50 笔 small live 后 Average R > 0。
Max Drawdown < 10%。
Rule adherence > 95%。
Manual Override Cost 可控。
```

---

## 34.7 Stage 6：Options Paper → Options Micro Live

### Options Paper 要求

```text
至少 20 笔 option paper trades。
只做通过 underlying 筛选的标的。
优先 30–60 DTE。
记录 IV entry / IV exit。
记录 spread cost。
记录 underlying 是否判断正确。
记录 option 是否因为 DTE / IV / spread 亏损。
```

### 允许 Options Micro Live 的条件

```text
Option paper expectancy > 0。
Option drawdown 可控。
没有因 spread/DTE/IV 系统性亏损。
Underlying 策略已经正期望。
```

### Options Micro Live 风险

```text
单笔权利金 1%。
最多 1 个 option position。
禁止 0DTE。
禁止裸卖。
禁止财报彩票。
亏损 30%–50% 退出。
盈利 50%–100% 保护。
```

---

## 34.8 Stage 7：Scaling & Cashflow Mode

只有在以下条件满足后，才允许把 EdgePilot 作为现金流系统逐步放大：

```text
Small Live 至少 100 笔。
Rolling expectancy > 0。
Max Drawdown 可控。
Option contribution 非负或期权模块禁用。
Rule adherence > 95%。
没有连续 Risk Halt。
Cashflow Target Feasibility 不为 Red。
```

---

# 35. Signal Funnel：信号漏斗

## 35.1 目的

信号漏斗用于回答：

> 系统到底在哪一层筛掉了标的？  
> 哪一层产生最多误判？  
> 哪一层最影响盈利？

## 35.2 漏斗层级

```text
Universe
↓
Strategy Passed
↓
PA Setup Found
↓
Context Passed
↓
Risk Passed
↓
Candidate
↓
Triggered
↓
Entered
↓
Reached +1R
↓
Reached +2R
↓
Reduced
↓
Exited
```

## 35.3 每层指标

```text
count
conversion_rate
average_score
average_R_after_entry
win_rate_after_entry
profit_factor_after_entry
avg_MFE
avg_MAE
false_positive_rate
```

## 35.4 诊断逻辑

```text
候选很多但触发少:
    筛选太宽或 entry 太远。

触发很多但 +1R 少:
    PA 质量不足或 context 过滤不够。

+2R 很多但最终收益小:
    Exit Engine 盈利保护不足。

亏损单超过 -1R:
    执行或滑点风险过高。

Watch 信号表现好于 Candidate:
    评分系统可能需要校准。
```

---

# 36. Setup Quality Calibration：Setup 质量校准

## 36.1 目标

将 PA 从主观判断转为可统计的概率判断。

## 36.2 每个 setup 保存上下文

```text
setup_type
market_regime
sector_confirmation
gap_pct
distance_from_20ma_pct
distance_from_50ma_pct
base_length
base_depth
volume_expansion
close_location_pct
stop_distance_pct
headline_risk
option_suitability
```

## 36.3 校准输出

```text
historical_win_rate
historical_average_R
historical_profit_factor
historical_max_drawdown
sample_size
confidence_level
```

## 36.4 使用方式

系统不再简单输出：

```text
Breakout detected.
```

而是输出：

```text
Breakout detected.
This context historically has positive expectancy.
Trade allowed.
```

或：

```text
Breakout detected.
This context historically underperforms.
Downgraded to Watch.
```

## 36.5 样本不足规则

```text
If sample_size < 30:
    confidence_level = low
    do not increase position size based on calibration
```

---

# 37. MFE / MAE Exit Analytics

## 37.1 定义

```text
MFE = Maximum Favorable Excursion
MAE = Maximum Adverse Excursion
Final R = 实际最终收益 R
```

## 37.2 需要回答的问题

```text
是否经常 +2R 后回到 0？
是否止损太紧？
是否盈利单卖太早？
是否亏损单拖太久？
是否 time stop 有效？
```

## 37.3 规则改进示例

如果：

```text
MFE >= +2R 但 Final R < +0.5R 的比例很高
```

则：

```text
增强 +2R partial profit。
更早移动止损。
增加 trailing stop 敏感度。
```

如果：

```text
MAE 经常接近 -1R 后转为 +2R
```

则：

```text
检查入场是否太早。
检查初始 stop 是否太紧。
优先等待二次确认。
```

---

# 38. 风险降低增强模块

## 38.1 Data Quality Gate

### 规则

```text
If core data missing:
    no new trades

If option chain stale:
    no option analysis

If FX rate stale:
    cashflow target shows warning

If scanner failed:
    dashboard shows system degraded

If Exit Engine failed:
    no new trades, existing positions require manual review
```

## 38.2 Execution Risk Score

每个候选生成执行风险：

```text
Low:
    SPY / QQQ / 高流动性 ETF

Medium:
    高流动性大票 / 流动性好期权

High:
    宽 spread option / 日股薄盘口 / 小票 / 高波动新闻环境
```

影响：

```text
High execution risk:
    降低 position size
    或直接 Watch Only
```

## 38.3 Correlation Guard

### 目标

避免表面多仓，实际同一风险。

风险簇示例：

```text
US Tech Growth
Semiconductors
High Beta Risk-on
Japan Exporters
Japan Banks
USDJPY-sensitive
AI/Data Center
```

规则：

```text
同一 cluster 最多 1–2 个仓位。
同一 cluster 总风险不超过账户 1%–2%。
期权按更高风险权重计入。
```

## 38.4 Manual Override Audit

记录：

```text
system_decision
user_action
override_reason
result_R
cost_of_override
```

统计：

```text
Manual Override P/L
Rule Violation Cost
Ignored Exit Cost
Unplanned Option Cost
```

目的：

> 判断用户介入是在提高系统收益，还是破坏系统收益。

## 38.5 Strategy Kill Switch

每个策略都有暂停条件：

```text
Breakout:
    最近 20 笔 expectancy < 0
    或连续亏损 5 笔
    → 暂停

Options:
    最近 10 笔净亏
    或 option drawdown > 5%
    → 暂停

Japan Strategy:
    连续跑输 US ETF strategy
    → 降权

Pullback:
    最近 20 笔 profit factor < 1
    → 降权
```

---

# 39. Testing 数据库设计（v0.5）

## 39.1 test_runs

```sql
CREATE TABLE test_runs (
    test_run_id TEXT PRIMARY KEY,
    test_type TEXT NOT NULL,       -- backtest, shadow, paper, micro_live
    strategy_name TEXT,
    market TEXT,
    universe TEXT,
    start_date DATE,
    end_date DATE,
    status TEXT,
    config JSONB,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);
```

---

## 39.2 simulated_trades

```sql
CREATE TABLE simulated_trades (
    simulated_trade_id TEXT PRIMARY KEY,
    test_run_id TEXT,
    symbol_id TEXT,
    market TEXT,
    asset_type TEXT,
    strategy_name TEXT,
    setup_type TEXT,
    signal_ts TIMESTAMPTZ,
    entry_ts TIMESTAMPTZ,
    exit_ts TIMESTAMPTZ,
    entry_price DOUBLE PRECISION,
    stop_price DOUBLE PRECISION,
    exit_price DOUBLE PRECISION,
    exit_reason TEXT,
    mfe_r DOUBLE PRECISION,
    mae_r DOUBLE PRECISION,
    final_r DOUBLE PRECISION,
    market_regime TEXT,
    setup_quality_score DOUBLE PRECISION,
    context_score DOUBLE PRECISION,
    execution_risk_score DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 39.3 signal_funnel_snapshots

```sql
CREATE TABLE signal_funnel_snapshots (
    date DATE NOT NULL,
    test_run_id TEXT,
    strategy_name TEXT,
    market TEXT,
    universe_count INTEGER,
    strategy_passed_count INTEGER,
    pa_setup_count INTEGER,
    context_passed_count INTEGER,
    risk_passed_count INTEGER,
    candidate_count INTEGER,
    triggered_count INTEGER,
    entered_count INTEGER,
    reached_1r_count INTEGER,
    reached_2r_count INTEGER,
    exited_count INTEGER,
    avg_final_r DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (date, test_run_id, strategy_name, market)
);
```

---

## 39.4 data_quality_checks

```sql
CREATE TABLE data_quality_checks (
    check_id TEXT PRIMARY KEY,
    check_ts TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL,          -- pass, warning, fail
    severity TEXT,                 -- p0, p1, p2
    affected_symbols TEXT[],
    message TEXT,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 39.5 go_live_gates

```sql
CREATE TABLE go_live_gates (
    gate_id TEXT PRIMARY KEY,
    gate_name TEXT NOT NULL,
    gate_type TEXT NOT NULL,       -- micro_live, small_live, options_live, scaling
    status TEXT NOT NULL,          -- locked, eligible, approved, blocked
    requirements JSONB,
    current_values JSONB,
    blocking_reasons JSONB,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 39.6 manual_overrides

```sql
CREATE TABLE manual_overrides (
    override_id TEXT PRIMARY KEY,
    entity_type TEXT,              -- candidate, position, alert
    entity_id TEXT,
    system_decision TEXT,
    user_action TEXT,
    override_reason TEXT,
    result_r DOUBLE PRECISION,
    cost_of_override DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 39.7 strategy_kill_switch_status

```sql
CREATE TABLE strategy_kill_switch_status (
    strategy_name TEXT PRIMARY KEY,
    status TEXT NOT NULL,          -- active, reduced, paused
    reason TEXT,
    recent_trade_count INTEGER,
    recent_expectancy_r DOUBLE PRECISION,
    recent_profit_factor DOUBLE PRECISION,
    recent_drawdown_pct DOUBLE PRECISION,
    triggered_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 40. Testing API 设计（v0.5）

## 40.1 Backtest

```http
POST /api/testing/backtests
GET  /api/testing/backtests/{test_run_id}
GET  /api/testing/backtests/{test_run_id}/trades
GET  /api/testing/backtests/{test_run_id}/metrics
```

## 40.2 Shadow Mode

```http
POST /api/testing/shadow/start
POST /api/testing/shadow/stop
GET  /api/testing/shadow/current
GET  /api/testing/shadow/trades
```

## 40.3 Paper Trading

```http
POST /api/testing/paper/positions
PATCH /api/testing/paper/positions/{position_id}
POST /api/testing/paper/positions/{position_id}/close
GET  /api/testing/paper/summary
GET  /api/testing/paper/trades
```

## 40.4 Signal Funnel

```http
GET /api/testing/signal-funnel?from=&to=&strategy=&market=
```

## 40.5 Data Quality

```http
GET /api/testing/data-quality
GET /api/testing/data-quality/latest
```

## 40.6 Go-Live Gate

```http
GET  /api/testing/go-live-gates
GET  /api/testing/go-live-gates/{gate_id}
POST /api/testing/go-live-gates/{gate_id}/request-approval
POST /api/testing/go-live-gates/{gate_id}/approve
```

## 40.7 Strategy Kill Switch

```http
GET  /api/testing/strategy-kill-switch
POST /api/testing/strategy-kill-switch/{strategy_name}/pause
POST /api/testing/strategy-kill-switch/{strategy_name}/resume
```

---

# 41. Testing 前端页面设计（v0.5）

## 41.1 新增主导航

```text
Validation
```

放在：

```text
Dashboard
Candidates
Positions
Exit Alerts
Cashflow
Analytics
Validation
Journal
Settings
```

---

## 41.2 Validation Dashboard

显示：

```text
Data Quality Status
Backtest Status
Shadow Mode Status
Paper Trading Status
Micro Live Eligibility
Options Live Eligibility
Go-Live Gate Status
Strategy Kill Switch Status
```

---

## 41.3 Signal Funnel 页面

显示漏斗图：

```text
Universe
Strategy Passed
PA Setup
Context Passed
Risk Passed
Candidate
Triggered
Entered
+1R
+2R
Exited
```

每层显示：

```text
count
conversion rate
avg R
win rate
profit factor
```

---

## 41.4 Paper Trading 页面

功能：

```text
System Paper trades
Manual Paper trades
Paper positions
Paper P/L
Paper R distribution
Paper vs Live comparison
```

---

## 41.5 Data Quality 页面

显示：

```text
Data source
Last update
Missing bars
Stale option chain
FX rate freshness
Job status
Severity
Blocking status
```

---

## 41.6 Go-Live Gate 页面

显示：

```text
Gate name
Status
Requirements
Current values
Blocking reasons
Approval history
```

示例：

```text
Options Live Gate:
    Locked

Blocking reasons:
    Option paper trades < 20
    Option expectancy not proven
    Underlying strategy still in testing
```

---

# 42. v0.5 实现计划调整

## 42.1 新优先级

原 Phase 7 Backtest + Paper Trading 不应放到最后。  
v0.5 调整为：

```text
Phase 0:
    项目骨架 + 数据库 + 前端骨架

Phase 1:
    美股 ETF 数据 + 基础 Scanner

Phase 2:
    Data Quality Gate + ETF-only Backtest

Phase 3:
    Position Ledger + Exit Engine

Phase 4:
    Shadow Mode + Signal Funnel

Phase 5:
    Paper Trading + MFE/MAE

Phase 6:
    Micro Live Tracker + Go-Live Gate

Phase 7:
    Option Adapter Paper-only

Phase 8:
    AI Reviewer

Phase 9:
    日股 J-Quants

Phase 10:
    日股分足/Tick + IBKR

Phase 11:
    Cashflow Target Engine

Phase 12:
    Options Micro Live Gate
```

理由：

```text
测试和验证必须前置。
期权必须在 paper 中独立验证。
日股复杂度高，应在 US ETF 流程跑通后再上。
Cashflow Target Engine 应基于真实统计数据工作。
```

---

## 42.2 最小可运行版本：EdgePilot MVP-Validation

MVP-Validation 只做：

```text
1. PostgreSQL + TimescaleDB + Redis
2. Next.js 标准前端
3. Polygon/Massive ETF daily bars
4. ETF Rotation Scanner
5. Basic PA Engine
6. Position Ledger
7. Exit Engine
8. Backtest
9. Shadow Mode
10. Paper Trading
11. Signal Funnel
12. Analytics
```

不做：

```text
期权实盘
日股实盘
AI Reviewer
Cashflow Mode 实盘目标
复杂订单簿
```

通过 MVP-Validation 后，再进入扩展阶段。

---

# 43. v0.5 最终判断

EdgePilot 要想真的提高盈利能力，不能只依靠更复杂的策略。  
它必须先证明：

```text
1. 数据是可信的。
2. 信号是可统计的。
3. PA 不是事后诸葛。
4. Exit Engine 能保护收益。
5. 用户能按规则执行。
6. 期权不会拖累系统。
7. 现金流目标不会倒逼风险。
```

v0.5 的核心变化是：

> 从“设计一个交易系统”升级为“设计一个能被验证、能被暂停、能被迭代、能逐步实盘的交易系统”。

最重要的规则：

```text
No validation, no live trading.
No paper edge, no option live.
No data quality, no new trade.
No target chasing, no risk increase.
```


---

# 44. Advanced PA Engine：完整价格行为系统（v0.6）

## 44.1 为什么 PA 必须一次性设计完整

EdgePilot 的核心交易判断不是单纯的 O’Neil 过滤，也不是简单指标信号，而是：

> 先筛出值得看的标的，再用 Price Action 判断怎么买、怎么卖、什么时候不做。

原先 PA Engine 已经包含基础状态机和基础 setup：

```text
1. Accumulation / Base
2. Breakout Setup
3. Breakout Confirmed
4. Retest / Pullback
5. Trend Continuation
6. Distribution / Breakdown
```

以及：

```text
Breakout
Pullback
Failed Breakdown Reclaim
Opening Range Breakout
```

但这还不够。PA 的真正难点不是识别图形，而是判断：

```text
这个 setup 在当前 context 下是否值得冒险？
这是有效突破，还是假突破？
这是健康回踩，还是趋势坏了？
这是洗盘，还是派发？
这是应该买，还是应该等，还是应该退出？
```

因此 v0.6 将 PA 设计为完整分层系统：

```text
PA Facts Layer
PA Structure Layer
PA Location Layer
PA Volume / Flow Layer
PA Context Layer
PA Entry Engine
PA Exit Engine
PA Quality Score
PA Calibration Layer
AI PA Reviewer
```

重要原则：

```text
完整 PA 一次性设计。
所有 PA 组件都可以落库和回测。
所有高级 PA setup 默认先进入 Shadow / Paper。
未通过 validation 的高级 PA 不允许进入 live decision。
```

---

## 44.2 Advanced PA Engine 总体架构

```text
Market Data
    ↓
PA Facts Layer
    ↓
Structure Detector
    ↓
Location Detector
    ↓
Volume / Flow Detector
    ↓
Context Adapter
    ↓
Setup Classifier
    ↓
PA Quality Score
    ↓
Entry Plan Generator
    ↓
Exit Plan Generator
    ↓
Calibration Engine
    ↓
Decision Layer
    ↓
AI PA Reviewer
    ↓
Candidate / Watch / Avoid / Exit
```

### 核心思想

```text
PA Facts:
    只记录事实，不判断好坏。

PA Quality:
    判断价格行为质量。

PA Context:
    判断这个 PA 是否适合当前环境。

PA Decision:
    将 PA、策略、风控、现金流、测试状态整合成最终状态。
```

---

# 45. PA Facts Layer

## 45.1 目标

将图表上的主观观察转成结构化事实。

事实层不做买卖决策，只回答：

```text
价格发生了什么？
成交量发生了什么？
位置在哪里？
结构是否变化？
```

## 45.2 基础事实

```text
new_20d_high
new_50d_high
new_52w_high
breaks_prior_high
breaks_prior_low
close_above_resistance
close_below_support
close_back_inside_base
close_near_high
close_near_low
gap_up
gap_down
wide_range_bar
inside_bar
outside_bar
narrow_range_bar
```

## 45.3 均线与趋势事实

```text
close_above_10ma
close_above_20ma
close_above_50ma
close_above_200ma
10ma_above_20ma
20ma_above_50ma
50ma_above_200ma
ma_slope_20_positive
ma_slope_50_positive
distance_from_20ma_pct
distance_from_50ma_pct
distance_from_200ma_pct
```

## 45.4 VWAP / 日内事实

```text
above_vwap
below_vwap
vwap_reclaim
vwap_loss
opening_range_high
opening_range_low
breaks_opening_range_high
breaks_opening_range_low
holds_above_opening_range_mid
fails_opening_range_breakout
```

## 45.5 成交量事实

```text
relative_volume
volume_above_20d_avg
volume_dryup
breakout_volume_expansion
pullback_volume_contraction
heavy_selling_volume
heavy_buying_volume
volume_climax
```

## 45.6 结构事实

```text
higher_high
higher_low
lower_high
lower_low
base_detected
base_length_bars
base_depth_pct
volatility_contraction
tight_close_cluster
support_retest
resistance_retest
undercut_prior_low
reclaim_prior_low
```

---

# 46. PA Structure Layer

## 46.1 目标

识别当前标的处于哪种价格结构中。

## 46.2 结构类型

```text
Uptrend
Downtrend
Range
Base
Volatility Contraction
Breakout Attempt
Breakout Confirmed
Breakout Failure
Pullback
Retest
Trend Continuation
Distribution
Climax
Reversal
```

## 46.3 Uptrend 判定

```text
20MA 上行
50MA 上行
价格在 50MA 上方
最近 N 个 swing low 抬高
相对强度不弱
```

## 46.4 Base 判定

```text
base_length: 10–60 bars
base_depth: <= 20%
high/low range 收敛
成交量逐步萎缩
价格接近 52w high 或中期高位
```

## 46.5 Volatility Contraction 判定

```text
连续 swing 回撤幅度递减
ATR percentile 下降
成交量萎缩
价格维持在较高位置
```

示例：

```text
pullback_1_depth > pullback_2_depth > pullback_3_depth
volume declining
price above 50MA
```

---

# 47. PA Location Layer

## 47.1 目标

判断信号出现的位置是否有利。

同样的 K 线，在不同位置意义完全不同。

## 47.2 位置指标

```text
distance_to_52w_high
distance_to_recent_resistance
distance_to_recent_support
distance_to_20ma
distance_to_50ma
distance_to_vwap
distance_to_entry_trigger
distance_to_initial_stop
distance_to_prior_supply_zone
```

## 47.3 位置评分

加分：

```text
接近前高但未过度延伸
回踩前高支撑
回踩 20MA / 50MA 后重新转强
突破前有足够整理
止损距离合理
```

扣分：

```text
离 20MA 太远
高开过大
前方压力很近
突破前整理不足
止损距离过宽
处于中间位置，没有明显支撑/压力
```

---

# 48. PA Volume / Flow Layer

## 48.1 目标

判断价格行为是否有成交量支持。

## 48.2 量能分类

```text
Dry-up
Normal
Expansion
Climax
Distribution
Absorption
```

## 48.3 Breakout 量能规则

加分：

```text
breakout volume >= 1.5x 20D average
突破前成交量萎缩
突破后回踩缩量
```

扣分：

```text
突破无量
放量但收盘弱
放量长上影
放量后跌回区间
```

## 48.4 Pullback 量能规则

加分：

```text
回踩期间缩量
支撑位附近出现承接
收复关键位时放量
```

扣分：

```text
回踩期间放量杀跌
反弹无量
跌破支撑后无法收回
```

## 48.5 Absorption 判定

用于识别大单是否真的有效。

```text
大买单后价格继续上行:
    买盘有效

大买单后价格不涨反跌:
    可能是派发或被动接盘

大卖单后价格不跌并收回:
    可能是空头被吸收
```

---

# 49. PA Context Layer

## 49.1 目标

将 PA 与市场环境结合。

PA 不直接决定交易。  
PA 必须经过 context gate。

## 49.2 Context 输入

```text
market_regime
sector_strength
relative_strength
overnight_us_lead
vix_change
usdjpy_change
headline_risk
earnings_risk
liquidity_score
execution_risk
cashflow_risk_mode
strategy_kill_switch_status
```

## 49.3 Context Gate

```text
Risk-on:
    允许 breakout / pullback / trend continuation

Neutral:
    breakout 降级
    pullback 优先

Distribution:
    禁止普通 breakout
    只允许管理已有仓位

Correction:
    新多仓默认禁止
    只保留极强 RS 标的 Watch

Shock:
    禁止新开仓
    只处理 Exit Engine
```

## 49.4 日股 Context

日股必须额外考虑：

```text
前一晚 QQQ / SPY / SMH / SOXX
USDJPY
VIX
Nikkei futures
TOPIX
相关 ADR
日本本土财报/新闻
```

规则：

```text
日股 PA 好，但美股隔夜冲击为 bearish:
    降级为 Watch

半导体日股 PA 好，SMH/SOXX 前一晚强:
    context 加分

出口股 PA 好，USDJPY 上行:
    context 加分

VIX 急升:
    所有突破信号降级
```

---

# 50. PA Setup Library：完整 Setup 库

## 50.1 Breakout

### 适用环境

```text
Risk-on
Sector leading
RS strong
Base quality high
```

### 条件

```text
base_length >= 10 bars
base_depth <= 20%
price near base high
volume expansion
close above resistance
close in upper 30% range
```

### 失效

```text
close back inside base
breakout day low broken
market regime turns bearish
sector fails to confirm
```

---

## 50.2 Breakout Retest

### 条件

```text
breakout occurred
price retests breakout level
retest volume contracts
price reclaims breakout level / VWAP
higher low forms
```

### 优点

```text
比直接追突破更适合小账户。
止损更清楚。
假突破过滤更好。
```

---

## 50.3 Pullback to 20MA / 50MA

### 条件

```text
trend up
price pulls back to 20MA or 50MA
pullback volume contraction
support holds
reclaim candle or VWAP reclaim
```

### 失效

```text
pullback low broken
close below 50MA
relative strength breaks down
```

---

## 50.4 Failed Breakdown Reclaim

### 条件

```text
price undercuts prior low or range low
quickly reclaims
close back above support
volume confirms
market not in shock mode
```

### 用途

```text
识别假跌破。
适合做反转或趋势延续中的洗盘收回。
```

---

## 50.5 VWAP Reclaim

### 条件

```text
price loses VWAP
then reclaims VWAP
holds above VWAP
higher low forms
market context supportive
```

### 用途

```text
日内确认。
避免开盘第一波追单。
```

---

## 50.6 Opening Range Breakout

### 条件

```text
no trade first 15 minutes
define OR high/low
break OR high
hold above VWAP
sector/index confirm
```

### 禁用条件

```text
shock mode
headline risk high
gap up too large
market breadth weak
```

---

## 50.7 VCP：Volatility Contraction Pattern

### 条件

```text
uptrend or high-level base
multiple pullbacks with decreasing depth
volume contracts through base
price tightens near resistance
breakout volume expands
```

### 评分重点

```text
contraction sequence quality
base depth
volume dry-up
RS strength
sector strength
stop distance
```

---

## 50.8 Pocket Pivot

### 条件

```text
price moves up from base or MA support
volume higher than recent down-volume
not too extended
near 10MA/20MA/50MA
market context supportive
```

### 用途

```text
比标准突破更早发现机构吸筹。
```

---

## 50.9 Undercut & Rally

### 条件

```text
price undercuts prior swing low
reclaims quickly
close strong
volume confirms absorption
```

### 用途

```text
适合强股回调后的洗盘收回。
```

---

## 50.10 Gap-and-Go

### 条件

```text
gap up on catalyst
opening range holds
VWAP holds
volume strong
sector/market confirms
```

### 风险

```text
只允许 A+ context。
gap 太大直接禁止。
```

---

## 50.11 Gap-up Failure

### 条件

```text
gap up
fails to hold OR high
loses VWAP
closes weak
high volume
```

### 用途

```text
避免追高。
已有仓位减仓/退出警告。
```

---

## 50.12 Distribution Warning

### 条件

```text
heavy volume down day
close near low
loss of 20MA/50MA
multiple failed rebounds
sector weakening
```

### 用途

```text
提高 Exit Engine 敏感度。
禁止新开同方向仓位。
```

---

## 50.13 Climax Run / Exhaustion

### 条件

```text
price extended far above 20MA/50MA
wide range up bars
huge volume
gap acceleration
then reversal / close weak
```

### 用途

```text
盈利仓位保护。
禁止追高。
```

---

## 50.14 Relative Strength New High

### 条件

```text
RS line makes new high before price
stock outperforms index
sector confirms
price close to breakout area
```

### 用途

```text
增强 O’Neil-style leader identification。
```

---

# 51. PA Quality Score

## 51.1 总分结构

```text
PA Quality Score = 100

Structure Quality: 20
Location Quality: 15
Volume Quality: 15
Trend / RS Quality: 15
Context Quality: 15
Risk / Stop Quality: 10
Follow-through Quality: 10
```

## 51.2 分级

```text
A+ : 85–100
A  : 75–84
B  : 65–74
C  : 50–64
D  : < 50
```

## 51.3 决策映射

```text
A+:
    Candidate
    normal risk allowed, unless cashflow lock reduces risk

A:
    Candidate / Watch
    depends on market context

B:
    Watch only
    no option

C:
    Avoid

D:
    Reject
```

## 51.4 硬性降级条件

```text
Shock mode:
    any entry setup -> No Trade

Data quality failed:
    No Trade

Stop distance too wide:
    Watch / Reject

Execution risk high:
    Watch / Reject

Strategy kill switch active:
    Reject

Cashflow target reached:
    risk reduced
    options disabled or micro-size only
```

---

# 52. PA Entry Plan Generator

每个 PA setup 必须输出：

```text
entry_trigger
preferred_entry
alternative_entry
initial_stop
stop_basis
risk_pct
invalidation
add_condition
no_trade_condition
```

## 示例：Breakout

```json
{
  "setup": "breakout",
  "entry_trigger": 105.20,
  "preferred_entry": "breakout close above 105.20 with volume expansion",
  "alternative_entry": "retest 105.20 and hold",
  "initial_stop": 99.80,
  "stop_basis": "base midpoint / breakout day low",
  "risk_pct": 5.1,
  "invalidation": [
    "close back inside base",
    "breakout day low broken",
    "sector fails"
  ],
  "no_trade_condition": [
    "gap up > 4%",
    "market regime shock",
    "stop distance > allowed"
  ]
}
```

---

# 53. PA Exit Engine

## 53.1 Exit PA 信号

```text
breakout_failure
loss_of_vwap
close_back_inside_base
break_higher_low
failed_retest
heavy_volume_down
gap_up_failure
distribution_warning
climax_reversal
no_follow_through_time_stop
```

## 53.2 Exit PA 分级

```text
Level 1 Watch:
    mild weakness

Level 2 Tighten:
    raise stop, no add

Level 3 Reduce:
    partial profit or risk reduction

Level 4 Exit:
    thesis invalidated
```

## 53.3 Exit PA 与 R 结合

```text
If +2R and distribution_warning:
    Level 3 Reduce

If +3R and climax_reversal:
    Level 3/4 depending on close

If -0.5R and breakout_failure:
    Level 4 Exit

If +1R and no_follow_through:
    tighten stop
```

---

# 54. PA Calibration Layer

## 54.1 目标

用历史和实时结果校准 PA，而不是凭感觉。

## 54.2 每个 setup 保存结果

```text
setup_type
pa_quality_score
market_regime
sector_confirmation
entry_type
exit_reason
MFE
MAE
final_R
holding_period
option_used
execution_risk_score
```

## 54.3 输出统计

```text
sample_size
win_rate
average_R
median_R
profit_factor
false_breakout_rate
avg_MFE
avg_MAE
max_drawdown
best_context
worst_context
```

## 54.4 样本不足规则

```text
sample_size < 30:
    low confidence
    no position size increase

sample_size >= 50:
    medium confidence

sample_size >= 100:
    high confidence
```

## 54.5 自动降级

```text
If setup expectancy < 0 over last 20 trades:
    setup downgraded

If false_breakout_rate high:
    require retest confirmation

If avg_MAE too high:
    entry timing too early
```

---

# 55. PA 数据库设计（v0.6）

## 55.1 pa_facts

```sql
CREATE TABLE pa_facts (
    fact_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    facts JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 55.2 pa_structures

```sql
CREATE TABLE pa_structures (
    structure_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    structure_type TEXT NOT NULL,
    confidence DOUBLE PRECISION,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 55.3 pa_setups

```sql
CREATE TABLE pa_setups (
    setup_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    detected_ts TIMESTAMPTZ NOT NULL,
    setup_type TEXT NOT NULL,
    setup_grade TEXT,
    pa_quality_score DOUBLE PRECISION,
    structure_score DOUBLE PRECISION,
    location_score DOUBLE PRECISION,
    volume_score DOUBLE PRECISION,
    trend_rs_score DOUBLE PRECISION,
    context_score DOUBLE PRECISION,
    risk_stop_score DOUBLE PRECISION,
    followthrough_score DOUBLE PRECISION,
    entry_plan JSONB,
    exit_plan JSONB,
    invalidation JSONB,
    status TEXT,                   -- detected, watch, candidate, triggered, failed, expired
    validation_status TEXT,        -- shadow_only, paper_allowed, live_allowed
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

## 55.4 pa_calibration_stats

```sql
CREATE TABLE pa_calibration_stats (
    stat_id TEXT PRIMARY KEY,
    setup_type TEXT NOT NULL,
    market_regime TEXT,
    sector_context TEXT,
    timeframe TEXT,
    sample_size INTEGER,
    win_rate DOUBLE PRECISION,
    average_r DOUBLE PRECISION,
    median_r DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    false_breakout_rate DOUBLE PRECISION,
    avg_mfe_r DOUBLE PRECISION,
    avg_mae_r DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    confidence_level TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 56. PA API 设计（v0.6）

## 56.1 PA Facts

```http
GET /api/pa/facts/{symbol}?timeframe=1d
```

## 56.2 PA Setups

```http
GET /api/pa/setups?symbol=&timeframe=&setup_type=&status=
GET /api/pa/setups/{setup_id}
```

## 56.3 PA Score

```http
POST /api/pa/score
```

## 56.4 PA Calibration

```http
GET /api/pa/calibration?setup_type=&market_regime=&timeframe=
POST /api/pa/calibration/recalculate
```

## 56.5 PA Explain

```http
GET /api/pa/setups/{setup_id}/explain
```

---

# 57. PA 前端页面设计（v0.6）

## 57.1 新增页面

```text
PA Lab
```

放在：

```text
Dashboard
Candidates
Positions
Exit Alerts
Cashflow
Analytics
Validation
PA Lab
Journal
Settings
```

## 57.2 PA Lab 页面结构

```text
PA Lab
├── Setup Explorer
├── PA Quality Breakdown
├── Structure View
├── Volume / Flow View
├── Context View
├── Entry / Exit Plan
├── Calibration Stats
├── MFE / MAE View
└── Shadow / Paper / Live Eligibility
```

## 57.3 Candidate Detail 增强

每个 candidate 展示：

```text
PA Event
PA Setup
PA Quality Score
PA Grade
Breakdown:
    Structure
    Location
    Volume
    Trend / RS
    Context
    Risk / Stop
    Follow-through

Entry Plan
Exit Plan
Invalidation
Calibration Stats
AI PA Review
```

## 57.4 图表增强

图上显示：

```text
base zone
resistance line
support line
entry trigger
initial stop
VWAP
opening range
failed breakout marker
distribution warning marker
climax warning marker
```

---

# 58. AI PA Reviewer（v0.6）

## 58.1 AI 角色

AI 不直接决定交易。  
AI 只复核 PA Engine 的结构化结果。

## 58.2 输入

```json
{
  "symbol": "NVDA",
  "timeframe": "1d",
  "setup_type": "VCP_breakout",
  "pa_quality_score": 84,
  "score_breakdown": {
    "structure": 18,
    "location": 13,
    "volume": 14,
    "trend_rs": 15,
    "context": 12,
    "risk_stop": 8,
    "followthrough": 6
  },
  "market_context": {
    "regime": "risk_on",
    "sector_strength": "strong",
    "headline_risk": "normal"
  },
  "entry_plan": {},
  "exit_plan": {},
  "calibration": {
    "sample_size": 42,
    "average_r": 0.21,
    "profit_factor": 1.31
  }
}
```

## 58.3 输出

```json
{
  "pa_review": "valid | questionable | weak",
  "decision_adjustment": "none | downgrade | reject",
  "main_bull_points": [],
  "main_bear_points": [],
  "context_risks": [],
  "execution_risks": [],
  "invalidation_summary": [],
  "human_review_notes": []
}
```

---

# 59. PA 测试门禁（v0.6）

## 59.1 每个高级 PA setup 默认 shadow_only

```text
VCP
Pocket Pivot
Gap-and-Go
Undercut & Rally
Distribution Warning
Climax Reversal
```

初始状态：

```text
validation_status = shadow_only
```

## 59.2 Paper Allowed 条件

```text
sample_size >= 30
average_R > 0
profit_factor > 1.10
false_signal_rate 可接受
Exit Engine 能正确处理
```

## 59.3 Live Allowed 条件

```text
sample_size >= 50
paper average_R > 0
paper profit_factor > 1.20
max_drawdown 可控
manual override cost 可控
market regime specific stats 不为负
```

## 59.4 禁止实盘条件

```text
sample_size < 30
expectancy <= 0
false_breakout_rate high
data quality failed
strategy kill switch active
```

---

# 60. v0.6 实现计划调整

## 60.1 新优先级

PA 不再作为“基础模块”，而作为核心模块一次性设计。

```text
Phase 0:
    项目骨架 + 数据库 + 前端骨架

Phase 1:
    Market data + PA Facts Layer

Phase 2:
    PA Structure / Location / Volume Layer

Phase 3:
    Basic + Advanced Setup Library

Phase 4:
    PA Quality Score + Entry / Exit Plan

Phase 5:
    ETF-only Backtest + PA Calibration

Phase 6:
    Shadow Mode for all PA setups

Phase 7:
    Paper Trading for validated setups

Phase 8:
    Micro Live for validated basic setups

Phase 9:
    Advanced PA live eligibility

Phase 10:
    Option Adapter integration

Phase 11:
    Japan PA Context integration

Phase 12:
    Cashflow Target Engine integration
```

## 60.2 重要约束

```text
完整 PA 可以一次性实现。
但未验证 setup 不允许 live。
高级 PA 可以显示和记录。
高级 PA 可以 shadow/paper。
高级 PA 不能绕过 Risk Engine。
高级 PA 不能绕过 Cashflow Target Engine。
```

---

# 61. v0.6 对系统定位的更新

EdgePilot 的 PA 不再是基础形态扫描，而是：

> 一个 context-aware、可校准、可回测、可解释的价格行为决策系统。

它不只是回答：

```text
有没有突破？
```

而是回答：

```text
这个突破质量如何？
这个位置值不值得追？
这个市场环境是否支持？
止损距离是否合理？
历史上类似 context 是否赚钱？
如果失败，什么时候走？
如果盈利，怎么保护？
```

最终目标：

```text
减少主观看图。
减少假突破。
减少冲动追高。
提高入场质量。
提高离场质量。
让 PA 能被统计验证和持续优化。
```

---

## 18. 最终建议

第一版不要贪大。

建议开发顺序：

```text
1. 美股/ETF Scanner
2. Position Ledger
3. Exit Engine
4. Option Adapter
5. AI Reviewer
6. J-Quants 日股日线
7. J-Quants 分足/Tick
8. IBKR 少数候选盘口确认
9. Backtest/Paper Trading
```

资金使用建议：

```text
NISA / 储蓄：继续作为主资产
交易账户：1000–2000 USD，仅作为训练和验证账户
每月追加：先进入现金池，不自动提高风险
期权：小仓、少做、只做高质量 setup
```

最终系统定位：

> 一个帮助用户减少看图、减少冲动、管理风险、提示离场、记录复盘的 trading assistant，而不是自动赚钱机器。


---

# 62. Anti-Overfitting Governance：反过拟合治理（v0.7）

## 62.1 为什么必须加入反过拟合治理

随着 EdgePilot 增加 PA、期权、0DTE、市场统计、现金流、Benchmark、Settlement、Greeks、IV、AI Reviewer 等模块，系统有一个重大风险：

> 模块越多，历史回测越容易看起来聪明；实盘越容易失效。

因此 v0.7 明确将系统从“多 engine 打分系统”改造成：

> **少数核心规则做实盘决策，大量 engine 做风控、研究、解释和复盘。**

系统必须避免：

```text
1. 过多因子共同加分。
2. 复杂总分掩盖风险。
3. 用历史噪声拟合规则。
4. 高级 PA setup 未验证就进入实盘。
5. 0DTE / 期权因高 POP 或高 theta 被误判为高胜率现金流。
6. Cashflow target 反向驱动仓位和风险。
7. AI Reviewer 变成事实上的交易决策者。
```

核心规则：

```text
Complexity must earn its place.
复杂度必须证明它带来真实改善，否则不得进入实盘决策。
```

---

## 62.2 v0.7 核心原则

### 原则 1：实盘决策极简

实盘决策最多只允许 5 个核心维度：

```text
1. Market Regime
2. Setup Quality
3. Relative Strength / Trend
4. Risk-Reward / Stop Distance
5. Liquidity / Execution
```

其他模块不能直接提高买入权限。

---

### 原则 2：新 engine 默认无交易权

任何新增 engine 默认状态：

```text
research_only
```

它可以：

```text
记录
展示
解释
回测
shadow
paper
```

但不能：

```text
提高实盘仓位
提高 setup 等级
放宽风险限制
让 Watch 变成 Candidate
让 Paper 变成 Live
```

---

### 原则 3：大多数 engine 只能降级，不能升级

例如：

```text
Cashflow Target Engine:
    可以在本月达标后降风险。
    不能因为本月没达标而提高风险。

Settlement Risk Guard:
    可以阻止 ETF options 持有到期。
    不能因为 SPX cash settlement 较好而自动升级交易。

Option Greeks Risk:
    可以因为 gamma / vega / theta 风险降级。
    不能因为 theta 高而自动建议卖期权。

Seasonality:
    只能作为提示或软过滤。
    不能作为交易触发器。
```

---

### 原则 4：Gate-based 优先于 Score-based

EdgePilot 不应依赖一个复杂总分：

```text
Final Score = 83 → Buy
```

而应采用 gate-based 结构：

```text
Data OK?
Market OK?
Setup OK?
Risk OK?
Liquidity OK?
Exit Plan OK?
Validation OK?
```

只要关键 gate 不通过：

```text
No Trade
```

---

### 原则 5：简单 baseline 优先

如果复杂模型没有显著优于简单模型，则使用简单模型。

例如：

```text
Basic PA + Exit Engine:
    Profit Factor = 1.22
    Max Drawdown = 8%

Advanced PA + Seasonality + Complex Context:
    Profit Factor = 1.24
    Max Drawdown = 8.5%
```

这种情况下：

```text
复杂模型不进入实盘。
```

---

# 63. Engine Decision Rights Registry

## 63.1 目标

为每个模块明确“决策权限”。

每个 engine 都必须注册为以下四类之一：

```text
1. Production Decision
2. Risk-only
3. Research-only
4. Analytics-only
```

---

## 63.2 Production Decision Engines

这些模块可以参与实盘候选和持仓决策：

```text
Data Quality Gate
Market Regime Gate
Basic PA / Setup Gate
Risk Engine
Liquidity Guard
Position Ledger
Exit Engine
Validated Option Adapter, non-0DTE only
```

限制：

```text
1. 必须经过 validation。
2. 必须保持参数简洁。
3. 必须有明确 no-trade 条件。
4. 必须可回测、可 shadow、可 paper。
```

---

## 63.3 Risk-only Engines

这些模块只能降级、阻止、减仓或提醒，不得升级交易：

```text
Headline Risk Engine
Settlement Risk Guard
Margin / Buying Power Guard
Cashflow Target Engine
Correlation Guard
Execution Risk Score
Option Greeks Risk
IV Regime Risk
Event Risk Calendar
Data Freshness Monitor
```

允许动作：

```text
Candidate → Watch
Watch → Avoid
Normal Risk → Reduced Risk
New Trade → No Trade
Hold → Tighten Stop
Hold → Reduce
Hold → Exit Warning
```

禁止动作：

```text
Watch → Candidate
B Setup → A Setup
Increase risk size
Enable options
Enable 0DTE live
```

---

## 63.4 Research-only Engines

这些模块只能用于研究、回测、Shadow 和 Paper：

```text
0DTE Research Lab
Iron Condor Research
Iron Butterfly Research
Short Premium Experiments
Advanced PA Setup Library before validation
Seasonality Engine
Kelly Sizing Engine
Complex Volatility Strategies
AI-generated strategy ideas
```

默认状态：

```text
no_live_permission = true
```

---

## 63.5 Analytics-only Engines

这些模块只用于复盘和解释：

```text
MFE / MAE Analytics
Benchmark Comparison
Edge Attribution
Profit Concentration Risk
Strategy Breakdown
Skill vs Luck Analyzer
Market Statistics
Stress Scenario Library
Manual Override Audit
Negative Selection Detector
```

它们回答：

```text
哪里赚钱？
哪里亏钱？
是否跑赢基准？
是否靠少数运气盈利？
执行是否吃掉 edge？
```

它们不直接回答：

```text
今天买什么？
```

---

# 64. Minimal Live Decision Path

## 64.1 实盘决策流程

```text
Universe
  ↓
Data Quality Gate
  ↓
Market Regime Gate
  ↓
Validated Strategy / Setup Gate
  ↓
PA Quality Check
  ↓
Risk / Stop / Liquidity Gate
  ↓
Position Plan
  ↓
Exit Plan
  ↓
Manual Confirmation
```

---

## 64.2 实盘候选生成条件

一个候选进入 live decision 必须同时满足：

```text
1. 数据质量通过。
2. 当前 market regime 支持该策略。
3. 策略 validation_status 至少为 micro_live_allowed。
4. setup 是已验证 setup。
5. stop distance 合理。
6. expected risk 在账户规则内。
7. liquidity / execution 风险合格。
8. 不处于 Cashflow target chasing 风险状态。
9. Exit plan 已明确。
```

---

## 64.3 实盘候选禁止条件

以下任一条件成立：

```text
Data Quality Failed
Market Shock
Strategy Kill Switch Active
Insufficient sample size
No clear stop
Stop distance too wide
Liquidity poor
Execution risk high
Cashflow target gap only reason
Naked option required
0DTE live not validated
```

则：

```text
No Trade
```

---

# 65. Parameter Budget：参数预算

## 65.1 目标

限制每个实盘策略的可调参数数量，降低过拟合。

## 65.2 规则

每个 live strategy 最多允许：

```text
3–5 个核心参数
```

例如 Breakout 策略：

```text
base_min_days
max_base_depth_pct
breakout_volume_multiple
max_stop_distance_pct
market_regime_required
```

禁止：

```text
20 个技术指标参数
多个任意阈值组合
针对某只股票调参
针对某一年调参
```

---

## 65.3 参数变更规则

每次参数变更必须记录：

```text
strategy_version
changed_parameter
old_value
new_value
change_reason
expected_improvement
approval_status
effective_date
```

参数变更后必须重新经过：

```text
Backtest
Shadow
Paper
Micro Live, if material change
```

---

# 66. Validation Protocol 防过拟合规则

## 66.1 Out-of-Sample

禁止只用同一段历史调参和验证。

推荐：

```text
Train: 2018–2021
Validate: 2022
Test: 2023–2024
Forward Paper: 2025+
```

或滚动：

```text
过去 24 个月训练
接下来 3 个月验证
持续 walk-forward
```

---

## 66.2 Walk-forward

每个策略必须至少做一次 walk-forward：

```text
train_window
validation_window
test_window
roll_forward
```

输出：

```text
in_sample_performance
out_of_sample_performance
walk_forward_decay
stability_score
```

如果：

```text
out_of_sample 显著低于 in_sample
```

则策略降级。

---

## 66.3 Ablation Test

每新增一个 engine，必须测试：

```text
without_engine_result
with_engine_result
difference_in_profit_factor
difference_in_max_drawdown
difference_in_average_R
difference_in_trade_count
difference_in_complexity
```

如果新增 engine 不能显著改善：

```text
不进入 Production Decision。
```

---

## 66.4 Baseline Comparison

每个复杂策略必须和简单 baseline 比较。

示例：

```text
Complex PA Strategy
vs
Basic PA + Exit Engine

ETF Rotation
vs
SPY / QQQ Buy & Hold

0DTE Premium Strategy
vs
No Trade / SPY Swing / Defined Risk Debit Spread
```

通过标准：

```text
1. 收益更高，或
2. 回撤更低，或
3. 风险调整后收益更好，或
4. 现金流更稳定，且
5. 执行复杂度可接受。
```

---

## 66.5 Sample Size Gate

样本不足不得进入实盘。

```text
sample_size < 30:
    research_only

30 <= sample_size < 50:
    shadow / paper

50 <= sample_size < 100:
    micro_live allowed only if metrics positive

100 <= sample_size < 200:
    small_live possible

sample_size >= 200:
    scaling review possible
```

如果按 market regime 拆分后样本不足，则该 regime 下不能 live。

---

# 67. Strategy Promotion Pipeline

## 67.1 Evidence Level

每个策略或 engine 有证据等级：

```text
E0: Idea only
E1: Backtest positive
E2: Shadow positive
E3: Paper positive
E4: Micro Live positive
E5: Small Live positive
E6: Scalable Live
```

---

## 67.2 权限映射

```text
E0:
    Research only

E1:
    Shadow only

E2:
    Paper allowed

E3:
    Micro Live eligible

E4:
    Small Live eligible

E5:
    Cashflow eligible

E6:
    Scaling eligible
```

---

## 67.3 降级规则

策略必须自动降级，如果：

```text
recent_expectancy <= 0
profit_factor < 1
max_drawdown exceeds limit
rule adherence < 95%
execution drag too high
manual override cost too high
strategy underperforms benchmark
```

---

# 68. Anti-Overfitting Database Design

## 68.1 engine_registry

```sql
CREATE TABLE engine_registry (
    engine_id TEXT PRIMARY KEY,
    engine_name TEXT NOT NULL,
    engine_category TEXT NOT NULL,  -- production_decision, risk_only, research_only, analytics_only
    default_permission TEXT NOT NULL,
    can_upgrade_trade BOOLEAN DEFAULT FALSE,
    can_downgrade_trade BOOLEAN DEFAULT TRUE,
    can_change_position_size BOOLEAN DEFAULT FALSE,
    can_enable_options BOOLEAN DEFAULT FALSE,
    can_enable_0dte BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 68.2 strategy_versions

```sql
CREATE TABLE strategy_versions (
    strategy_version_id TEXT PRIMARY KEY,
    strategy_name TEXT NOT NULL,
    version TEXT NOT NULL,
    parameters JSONB,
    parameter_count INTEGER,
    change_reason TEXT,
    validation_status TEXT,
    effective_from TIMESTAMPTZ,
    effective_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 68.3 validation_runs

```sql
CREATE TABLE validation_runs (
    validation_run_id TEXT PRIMARY KEY,
    strategy_version_id TEXT,
    validation_type TEXT NOT NULL, -- backtest, walk_forward, shadow, paper, micro_live
    train_start DATE,
    train_end DATE,
    validate_start DATE,
    validate_end DATE,
    test_start DATE,
    test_end DATE,
    metrics JSONB,
    pass BOOLEAN,
    failure_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 68.4 ablation_tests

```sql
CREATE TABLE ablation_tests (
    ablation_test_id TEXT PRIMARY KEY,
    strategy_version_id TEXT,
    engine_id TEXT,
    baseline_metrics JSONB,
    with_engine_metrics JSONB,
    improvement_summary JSONB,
    complexity_cost TEXT,
    approved_for_production BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 68.5 baseline_comparisons

```sql
CREATE TABLE baseline_comparisons (
    comparison_id TEXT PRIMARY KEY,
    strategy_version_id TEXT,
    benchmark TEXT, -- SPY, QQQ, Basic PA, No Trade, etc.
    strategy_metrics JSONB,
    benchmark_metrics JSONB,
    outperformance BOOLEAN,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 68.6 overfit_risk_assessments

```sql
CREATE TABLE overfit_risk_assessments (
    assessment_id TEXT PRIMARY KEY,
    strategy_version_id TEXT,
    parameter_count INTEGER,
    sample_size INTEGER,
    in_sample_pf DOUBLE PRECISION,
    out_of_sample_pf DOUBLE PRECISION,
    walk_forward_decay DOUBLE PRECISION,
    stability_score DOUBLE PRECISION,
    overfit_risk_level TEXT, -- low, medium, high, severe
    recommendation TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 69. Anti-Overfitting API Design

## 69.1 Engine Registry

```http
GET /api/governance/engines
PATCH /api/governance/engines/{engine_id}
```

---

## 69.2 Strategy Versions

```http
GET /api/governance/strategies/{strategy_name}/versions
POST /api/governance/strategies/{strategy_name}/versions
```

---

## 69.3 Validation Runs

```http
POST /api/governance/validation-runs
GET  /api/governance/validation-runs/{validation_run_id}
```

---

## 69.4 Ablation Tests

```http
POST /api/governance/ablation-tests
GET  /api/governance/ablation-tests/{ablation_test_id}
```

---

## 69.5 Baseline Comparison

```http
POST /api/governance/baseline-comparisons
GET  /api/governance/baseline-comparisons/{comparison_id}
```

---

## 69.6 Overfit Risk

```http
GET /api/governance/overfit-risk/{strategy_version_id}
```

---

# 70. Frontend：Governance Lab

## 70.1 新增导航

```text
Governance
```

放在：

```text
Dashboard
Candidates
Positions
Exit Alerts
Cashflow
Analytics
Validation
PA Lab
Options Risk Lab
Governance
Journal
Settings
```

---

## 70.2 页面结构

```text
Governance Lab
├── Engine Decision Rights
├── Strategy Version Control
├── Parameter Budget
├── Validation Runs
├── Walk-forward Results
├── Ablation Tests
├── Baseline Comparisons
├── Overfit Risk Assessment
├── Promotion Gate
└── Live Permission Matrix
```

---

## 70.3 Engine Decision Rights UI

显示每个 engine：

```text
Engine
Category
Can Upgrade?
Can Downgrade?
Can Change Position Size?
Can Enable Options?
Can Enable 0DTE?
Current Permission
```

对风险项高亮：

```text
任何 can_upgrade_trade = true 的 engine 必须显著标记。
```

---

## 70.4 Overfit Risk Panel

显示：

```text
Parameter count
Sample size
In-sample performance
Out-of-sample performance
Walk-forward decay
Ablation result
Baseline comparison
Overfit risk level
Recommendation
```

---

## 70.5 Promotion Gate UI

显示策略当前阶段：

```text
Research
Backtest
Shadow
Paper
Micro Live
Small Live
Cashflow Eligible
Scaling Eligible
```

并显示阻塞原因：

```text
Sample size too small
Out-of-sample weak
Benchmark underperformance
Execution drag high
Too many parameters
0DTE not validated
```

---

# 71. Implementation Plan v0.7

## Phase G0：Engine Registry

```text
建立 engine_registry。
将现有模块分类。
明确哪些模块可以参与 production decision。
```

验收：

```text
所有 engine 都有 category 和 permission。
没有未分类 engine。
```

---

## Phase G1：Parameter Budget

```text
建立 strategy_versions。
记录每个策略参数数量。
阻止超过参数预算的策略进入 live。
```

验收：

```text
实盘策略参数不超过 5 个核心参数。
```

---

## Phase G2：Validation + Walk-forward

```text
实现 validation_runs。
支持 train / validate / test 分割。
实现 walk-forward 结果记录。
```

验收：

```text
策略必须有 out-of-sample 结果才能进入 paper。
```

---

## Phase G3：Ablation + Baseline

```text
实现 ablation_tests。
实现 baseline_comparisons。
```

验收：

```text
新增 engine 必须证明改善。
复杂策略必须优于 baseline。
```

---

## Phase G4：Governance Frontend

```text
实现 Governance Lab。
显示 engine 权限、过拟合风险、验证状态、promotion gate。
```

验收：

```text
用户能一眼看到哪些模块有实盘决策权。
```

---

## Phase G5：Live Permission Enforcement

```text
在 decision layer 强制读取 engine_registry 和 strategy validation。
没有权限的 engine 不得影响 live decision。
```

验收：

```text
Research-only engine 无法让交易进入 live。
Risk-only engine 无法提高风险或升级信号。
```

---

# 72. v0.7 最终系统规则

```text
1. Core live decision must remain simple.
2. New engines cannot upgrade trades by default.
3. Risk-only engines can only reduce risk.
4. Research-only engines cannot affect live decisions.
5. Analytics-only engines cannot generate trades.
6. Live strategies have parameter budgets.
7. Every strategy needs out-of-sample validation.
8. Every added engine needs ablation testing.
9. Every strategy must beat a simple baseline or justify lower risk.
10. Sample size gates must be respected.
11. Cashflow target cannot increase risk.
12. AI cannot change trade decisions.
13. 0DTE cannot go live without paper validation.
14. Naked short options remain permanently rejected.
15. If complexity does not improve outcomes, use the simpler rule.
```

Final governance principle:

> EdgePilot should be a simple live trading system surrounded by powerful research, risk, and analytics tools — not a complex prediction machine.

---

# 73. Priority Reset：期权最低优先级与 Engine Minimalism（v0.8）

## 73.1 为什么需要 v0.8

v0.6 和 v0.7 已经把 EdgePilot 扩展成完整的交易驾驶舱，并且加入了 Advanced PA 和 Anti-Overfitting Governance。读完 0DTE 相关材料后，系统可以设计出很多期权研究模块：0DTE、covered call、iron condor、iron butterfly、tail hedge、beta-weighted delta、gamma threshold、theta budget、event calendar、settlement guard 等。

但是，系统复杂度本身会制造新的风险：

```text
1. engine 数量越多，越容易过拟合。
2. 参数越多，越容易用历史解释噪音。
3. 小账户越早碰期权，越容易被合约粒度和尾部风险伤害。
4. 0DTE 对执行速度、时区、心理和纪律要求过高。
5. 研究文档越完整，越容易误以为应该马上实现。
```

因此 v0.8 做一个明确的 Priority Reset：

> 期权相关功能全部降为最低优先级。当前系统主线只做股票/ETF候选、PA、风控、持仓、离场、Journal、Paper Trading、Analytics 和 Capital Accumulation。期权只保留为独立研究文档和未来 backlog。

---

## 73.2 v0.8 官方优先级（已由 v0.9 第 74 章覆盖）

> 本节保留作为 v0.8 历史记录。v0.9 的正式优先级以第 74 章为准：PA/Strat 前移，Short 仅 Watchlist/Paper，Options 继续最低优先级。

```text
P0 — Capital Protection / Trading Discipline
    Risk Engine
    Position Ledger
    Exit Engine
    Hard Stop
    Drawdown Halt
    Journal

P1 — Core Signal Generation
    US ETF Scanner
    US Large-cap Scanner
    Basic PA Engine
    Market Regime Filter

P2 — Frontend Trading Cockpit
    Dashboard
    Candidates
    Positions
    Exit Alerts
    Manual Position Management
    Mini Charts

P3 — Validation Before Expansion
    Paper Trading
    Journal Analytics
    Expectancy
    Profit Factor
    MFE / MAE
    Rule Adherence

P4 — Capital Accumulation Mode
    Monthly contribution tracking
    Profit retention
    Account growth ladder
    Cashflow target lock / unlock

P5 — Japan Expansion
    J-Quants daily scanner
    Japan overnight impact
    JP liquidity filter
    JP PA confirmation

P6 — AI Reviewer
    Explanation only
    Bear case
    Risk summary
    No decision rights

P7 — Advanced PA Research
    Advanced PA components only after ablation
    No production influence until validated

P8 — Options Backlog, Lowest Priority
    Option Adapter
    Option Risk Engine
    Covered Call Research
    0DTE Research Lab
    Tail Hedge Research
    Beta-weighted Delta
    Gamma / Theta / IV modules
```

v0.8 authoritative rule:

```text
P8 modules cannot be built before P0–P4 are working and validated.
```

---

## 73.3 MVP 范围重置

### MVP 必须完成

```text
1. US ETF / large-cap data ingestion.
2. Scanner v1.
3. Basic PA setup detection.
4. Risk Engine.
5. Position Ledger.
6. Exit Engine.
7. Frontend Candidates / Positions / Exit Alerts.
8. Manual trade recording.
9. Paper Trading Lite.
10. Journal Analytics.
11. Capital Accumulation Mode.
```

### MVP 不做

```text
1. Option chain UI.
2. Option signal ranking.
3. 0DTE.
4. Credit spreads.
5. Iron condors.
6. Iron butterflies.
7. Covered calls.
8. Tail hedges.
9. Beta-weighted delta hedging.
10. Gamma adjustment simulator.
11. AI option picker.
```

### 最小活系统路径

```text
Data → Scanner → Basic PA → Risk → Candidate → Manual/Paper Position → Exit Engine → Journal → Analytics
```

任何不在这条路径上的模块，默认不是 MVP。

---

## 73.4 Engine Minimalism Rule

v0.8 新增系统级规则：

> 写进研究文档的 engine，不等于要实现进产品；能命名一个 engine，不代表它应该存在。

每个新 engine 必须通过以下四问：

```text
1. 它解决的是当前 P0–P4 的真实瓶颈吗？
2. 没有它，系统是否无法验证正期望？
3. 它是否会增加 live decision 参数？
4. 它能否通过 ablation test 证明比简单规则更好？
```

如果答案不清楚：

```text
Do not build.
Keep as research note.
```

---

## 73.5 v0.8 Engine Decision Rights Registry

### Production Decision Engines

只有以下模块可以参与早期 live / paper decision：

```text
US ETF Scanner v1
US Large-cap Scanner v1
Basic PA Engine
Risk Engine
Position Ledger
Exit Engine
Drawdown Halt
Paper Trading Engine
Journal Analytics
Capital Accumulation Mode
```

### Risk-only Engines

这些模块只能降级、阻止、提醒，不能升级交易：

```text
Market Regime Filter
Headline Risk Filter
Event Calendar, simple version
Data Freshness Guard
Account Risk Guard
Cashflow Target Engine
```

### Research-only Engines

这些模块不能影响 live decision：

```text
Advanced PA sub-engines before validation
Seasonality
Kelly sizing
VIX expected move research
SPY/QQQ distribution research
Option Adapter
Option Risk Engine
Covered Call Research
0DTE Research Lab
Iron Condor Research
Iron Butterfly Research
Tail Hedge Research
Beta-weighted Delta
Gamma Threshold
Theta Budget
IV Regime
Settlement Risk, until options enabled
```

### Analytics-only Engines

这些模块只用于复盘和报告：

```text
Strategy attribution
Profit concentration
Benchmark comparison
Ablation reports
Walk-forward reports
MFE / MAE diagnostics
Rule violation cost
```

---

## 73.6 Option Backlog Lock

期权 backlog 默认锁定。

```yaml
options:
  enabled_in_mvp: false
  enabled_in_live: false
  priority: P8_lowest
  default_permission: research_only
  allow_0dte_live: false
  allow_short_premium_live: false
  allow_covered_call_live: false
  allow_credit_spread_live: false
  allow_iron_condor_live: false
  allow_iron_butterfly_live: false
  allow_tail_hedge_live: false
  allow_ai_option_picker: false
```

解锁条件：

```text
1. P0–P4 已完成。
2. 至少 100 笔股票/ETF paper 或 micro-live 交易完成。
3. 主要 setup expectancy > 0。
4. Rule adherence > 95%。
5. Max drawdown 可控。
6. 用户主动决定进入期权研究阶段。
7. 只允许 paper，不允许 live。
```

---

## 73.7 后期如果启用期权，第一步也必须极简

期权第一步不是做 0DTE，也不是做 Greeks 全套。

第一步只做：

```text
1. 手动录入 option position。
2. 显示 premium risk。
3. 显示 max loss。
4. 显示 DTE warning。
5. 如果 underlying stop broken，提示退出。
6. 如果 settlement unknown，标记 Blocked。
```

第一步不做：

```text
1. POP ranking。
2. EV optimizer。
3. 0DTE adjustment。
4. Gamma scalping。
5. VIX/Theta strategy。
6. Tail hedge optimizer。
7. Rolling automation。
```

---

## 73.8 v0.8 实现计划覆盖规则（已由 v0.9 第 80 章覆盖）

本节保留作为 v0.8 历史记录。v0.9 的正式实现计划以第 80 章为准。

```text
Phase 0: Project skeleton
Phase 1: US ETF / large-cap data + scanner
Phase 2: Position Ledger + Exit Engine
Phase 3: Paper Trading Lite + Journal Foundation
Phase 4: Frontend Dashboard / Candidates / Positions / Exit Alerts
Phase 5: Analytics + Validation Gate
Phase 6: Capital Accumulation Mode
Phase 7: Japan daily scanner
Phase 8: AI Reviewer, explanation-only
Phase 9: Advanced PA research, gated by ablation
Phase 10: Options read-only risk display, optional future backlog
Phase 11: Options paper research, optional future backlog
```

No option module may be promoted before Phase 0–6 are stable.

---

## 73.9 Parameter Budget v0.8

早期实盘或 micro-live 决策只允许使用极少参数。

```text
Core scanner parameters <= 5
Basic PA parameters <= 5
Risk parameters <= 5
Exit parameters <= 5
Options live parameters = 0, because options live is disabled
```

如果某个策略需要超过 5 个核心参数才能成立：

```text
Research-only.
```

---

## 73.10 最终规则 v0.8

```text
1. Options are lowest priority.
2. Options are not part of MVP live path.
3. 0DTE remains research/paper only.
4. More engines do not mean more edge.
5. No new engine can be implemented before it solves a current bottleneck.
6. Research documentation is not implementation permission.
7. Simple live path beats complex unvalidated architecture.
8. Risk-only modules can only reduce risk.
9. Research-only modules cannot upgrade trades.
10. AI cannot add decision rights to any engine.
11. Cashflow target cannot increase risk.
12. Capital accumulation comes before cashflow extraction.
13. If unsure, do less.
```

v0.8 final principle:

> EdgePilot should first become a small, disciplined, validated stock/ETF trading cockpit. Options can wait.



---

# 74. v0.9 Strat Trigger Layer 与做空研究框架

## 74.1 v0.9 设计动机

v0.8 将期权降为最低优先级是正确的，但 Advanced PA 被整体放得过后，容易导致系统早期仍然依赖用户手动看图。v0.9 的调整是：

```text
1. PA 不靠后。
2. Advanced PA 不一次性做大。
3. Strat 作为 PA 的程序化触发层。
4. 做空能力先做数据结构和 paper，不开放 live。
5. 期权继续最低优先级。
6. 所有新增能力都受 Anti-Overfitting Governance 约束。
```

---

## 74.2 PA 与 Strat 的定义

### PA Engine

PA 是系统对价格行为的整体结构分析，包括：

```text
Trend
Base
Support / resistance
Breakout
Pullback
VWAP reclaim
Opening range
Failed breakdown reclaim
Volume confirmation
Market / sector context
Entry / stop / invalidation
```

PA 回答：

```text
这张图有没有交易价值？
结构在哪里成立？
哪里失效？
风险是否可控？
```

### Strat Trigger Layer

Strat 指 1 / 2 / 3 bar scenarios、timeframe continuity、2-1-2 / 3-1-2 等规则化 K 线触发语法。

Strat 回答：

```text
当前 K 线是否给了一个客观触发？
触发价在哪里？
trigger bar stop 在哪里？
多周期方向是否一致？
```

### 关系

```text
PA = 结构 + 上下文 + 风险计划。
Strat = PA 中更客观、更容易写代码的触发语法。
```

原则：

```text
Strat is not an independent trading system.
Strat cannot create trades alone.
Strat can confirm, delay, downgrade, or invalidate a PA candidate.
```

---

## 74.3 Strat v1 范围

v1 只实现最小、可验证、低参数的 Strat 子集。

### Bar State

```text
1  = Inside bar: current high <= previous high and current low >= previous low
2U = Directional up bar: current high > previous high and current low >= previous low
2D = Directional down bar: current low < previous low and current high <= previous high
3  = Outside bar: current high > previous high and current low < previous low
```

### Timeframe Continuity

支持：

```text
Monthly
Weekly
Daily
60m
15m, alert only
```

计算字段：

```text
open_position = close - open
above_open = close > open
below_open = close < open
continuity_state = bullish / bearish / mixed / neutral
```

### Pattern v1

允许识别：

```text
Inside bar breakout
2-1-2 continuation
2-1-2 reversal
3-1-2 reversal
2U continuation
2D continuation
```

暂不识别：

```text
全套 Strat pattern library
复杂 broadening formation 自动画线
复杂 trigger stacking
AI 视觉识别 Strat
```

---

## 74.4 Strat 输出 Schema

```json
{
  "symbol": "QQQ",
  "timeframe": "1d",
  "bar_type": "2U",
  "previous_bar_type": "1",
  "pattern": "2-1-2_continuation",
  "direction": "long",
  "trigger_price": 455.20,
  "trigger_stop": 443.80,
  "invalidation": "close back below trigger bar low",
  "timeframe_continuity": {
    "monthly": "bullish",
    "weekly": "bullish",
    "daily": "bullish",
    "60m": "mixed"
  },
  "quality": "valid_trigger",
  "can_create_trade_alone": false
}
```

---

## 74.5 Strat 在交易流程中的位置

```text
Scanner
  ↓
Market Regime Gate
  ↓
Structure PA
  ↓
Strat Trigger Layer
  ↓
Risk Engine
  ↓
Position Plan
  ↓
Manual Confirmation
```

禁止流程：

```text
Strat Pattern → Buy
Strat Pattern → Short
Strat Pattern → Increase size
Strat Pattern → Override stop
```

允许流程：

```text
PA Candidate + Strat Trigger → Candidate confirmed
PA Candidate + no Strat Trigger → Watch
Weak context + Strat Trigger → Watch / Avoid
Bearish Strat Trigger → Avoid Long / Short Watchlist only
```

---

## 74.6 Strat 防过拟合规则

### Rule 1：Pattern Budget

```text
Strat v1 patterns <= 6
```

超出范围的 pattern：

```text
Research-only
```

### Rule 2：No standalone trades

```text
Strat cannot create a candidate without scanner + PA context.
```

### Rule 3：Ablation Required

每个 Strat 规则必须比较：

```text
PA only
PA + Strat trigger
PA + Strat no-chase filter
```

指标：

```text
Average R
Win rate
Profit factor
Max drawdown
Stop-out rate
False breakout rate
Missed winner rate
```

### Rule 4：Risk-first influence

Strat 早期只允许：

```text
Candidate → confirmed candidate
Candidate → watch
Watch → avoid
Entry → wait for trigger
Stop → tighten only if PA supports
```

不允许：

```text
Increase risk
Add leverage
Enable short live
Enable options
```

---

# 75. Short Capability Framework

## 75.1 当前状态

v0.9 明确：

```text
EdgePilot remains long-biased by default.
Live short is disabled.
Short options remain prohibited.
Short signals first serve risk management, not profit seeking.
```

当前系统支持的 bearish 作用：

```text
Avoid long
Downgrade candidate
Tighten stop
Reduce position
Exit existing long
Create paper short watchlist
```

---

## 75.2 Short Capability Levels

### Level 0：No Short，默认

```text
No live short stock.
No live short ETF.
No short options.
Bearish signals only reduce long risk.
```

### Level 1：Bearish Context Only

系统识别弱势，但只用于：

```text
avoid long
reduce exposure
tighten stop
exit weak holdings
```

### Level 2：Short Watchlist

系统输出潜在做空候选，但仅显示为观察：

```text
candidate_direction = short
decision = short_watch
live_permission = false
```

### Level 3：Paper Short

允许创建模拟空头：

```text
paper_position_side = short
entry = simulated short entry
stop = cover stop
exit_action = buy_to_cover
```

### Level 4：Micro Live Short，未来解锁

只有满足所有条件后才可研究解锁：

```text
100+ paper short trades
positive expectancy
max drawdown controlled
borrow data available
short squeeze filter available
event risk filter available
manual execution discipline proven
```

默认：

```text
live_short_enabled = false
```

---

## 75.3 Short 禁止清单

永久禁止或默认禁止：

```text
Short options
Naked options
All-in short
Martingale short
Short after huge down move chase
Short meme stocks
Short low liquidity stocks
Short hard-to-borrow names without borrow data
Short before earnings
Short during FOMC / CPI / major event window
Short without stop
Short when account cannot tolerate gap-up stress
```

---

## 75.4 Short Risk Guard

Short Risk Guard 是 Risk-only engine，只能阻止或降级。

输入：

```text
borrow_available
borrow_fee
hard_to_borrow_flag
short_interest_proxy
days_to_cover_proxy
liquidity
spread_pct
gap_up_history
earnings_date
event_risk
market_regime
sector_regime
beta
ATR
stop_distance
account_equity
```

输出：

```text
short_permission: blocked / paper_only / micro_live_allowed
short_risk_level: low / medium / high / extreme
reject_reasons: []
required_cover_stop
max_gap_up_loss_estimate
```

---

## 75.5 Short Setup v1

Short v1 只允许进入 watch / paper。

### A. Failed Breakout Short Watch

```text
price breaks above resistance
fails to hold
closes back inside range
volume heavy
market/sector weak
Strat trigger: 2D or 3-1-2 down confirmation
```

输出：

```text
entry = break of failed breakout low
cover_stop = failed breakout high
invalidation = reclaim above failed breakout high
```

### B. Bear Flag Breakdown Watch

```text
downtrend
weak bounce into declining 20MA / 50MA
volume contracts on bounce
breaks bear flag low
Strat trigger: 2D continuation
```

输出：

```text
entry = break of bear flag low
cover_stop = flag high
invalidation = reclaim above 20MA / structure high
```

### C. Relative Weakness Short Watch

```text
market flat/up
symbol underperforms
below 50MA / 200MA
failed reclaim
sector weak
```

输出：

```text
entry = breakdown trigger
cover_stop = reclaim level
invalidation = relative strength improves
```

---

## 75.6 做空与 Strat

Strat 支持双向，但 live 权限不同。

多头触发：

```text
2U continuation
inside bar breaks up
3-1-2 up
bullish timeframe continuity
```

空头触发：

```text
2D continuation
inside bar breaks down
3-1-2 down
bearish timeframe continuity
```

权限规则：

```text
Long Strat Trigger:
    may confirm a long candidate if scanner + PA + risk pass.

Short Strat Trigger:
    may create short_watch or paper_short only.
```

---

# 76. v0.9 数据库迁移

## 76.1 candidates 扩展

```sql
ALTER TABLE candidates ADD COLUMN trade_direction TEXT DEFAULT 'long';
ALTER TABLE candidates ADD COLUMN allowed_direction TEXT DEFAULT 'long_only';
ALTER TABLE candidates ADD COLUMN strat_bar_type TEXT;
ALTER TABLE candidates ADD COLUMN strat_pattern TEXT;
ALTER TABLE candidates ADD COLUMN strat_trigger_price DOUBLE;
ALTER TABLE candidates ADD COLUMN strat_trigger_stop DOUBLE;
ALTER TABLE candidates ADD COLUMN strat_invalidation TEXT;
ALTER TABLE candidates ADD COLUMN timeframe_continuity TEXT;
ALTER TABLE candidates ADD COLUMN short_permission TEXT DEFAULT 'disabled';
ALTER TABLE candidates ADD COLUMN short_reject_reasons TEXT;
```

---

## 76.2 positions 扩展

```sql
ALTER TABLE positions ADD COLUMN position_side TEXT DEFAULT 'long';
ALTER TABLE positions ADD COLUMN trade_direction TEXT DEFAULT 'long';
ALTER TABLE positions ADD COLUMN cover_stop DOUBLE;
ALTER TABLE positions ADD COLUMN borrow_fee DOUBLE;
ALTER TABLE positions ADD COLUMN borrow_status TEXT;
ALTER TABLE positions ADD COLUMN short_risk_level TEXT;
```

---

## 76.3 trades_journal 扩展

```sql
ALTER TABLE trades_journal ADD COLUMN trade_direction TEXT DEFAULT 'long';
ALTER TABLE trades_journal ADD COLUMN exit_action TEXT;
ALTER TABLE trades_journal ADD COLUMN borrow_cost DOUBLE;
ALTER TABLE trades_journal ADD COLUMN gap_risk_tag TEXT;
ALTER TABLE trades_journal ADD COLUMN strat_pattern TEXT;
ALTER TABLE trades_journal ADD COLUMN timeframe_continuity TEXT;
```

---

## 76.4 strat_signals

```sql
CREATE TABLE strat_signals (
    signal_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts TIMESTAMP NOT NULL,
    bar_type TEXT NOT NULL,              -- 1, 2U, 2D, 3
    previous_bar_type TEXT,
    pattern TEXT,
    direction TEXT,                      -- long, short, neutral
    trigger_price DOUBLE,
    trigger_stop DOUBLE,
    invalidation TEXT,
    timeframe_continuity TEXT,
    quality_score DOUBLE,
    can_create_trade_alone BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

---

## 76.5 short_risk_snapshots

```sql
CREATE TABLE short_risk_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    snapshot_ts TIMESTAMP NOT NULL,
    borrow_available BOOLEAN,
    borrow_fee DOUBLE,
    hard_to_borrow BOOLEAN,
    short_interest_proxy DOUBLE,
    days_to_cover_proxy DOUBLE,
    liquidity_score DOUBLE,
    spread_pct DOUBLE,
    gap_up_risk_score DOUBLE,
    event_risk_level TEXT,
    short_squeeze_risk TEXT,
    short_permission TEXT,               -- blocked, paper_only, micro_live_allowed
    reject_reasons TEXT,
    source TEXT,
    created_at TIMESTAMP
);
```

---

# 77. v0.9 API 追加

## 77.1 Strat APIs

```http
POST /pa/strat/scan
GET  /pa/strat/signals?symbol=&timeframe=&date=
GET  /pa/strat/continuity/{symbol}
GET  /pa/strat/patterns/{symbol}
```

---

## 77.2 Candidate Direction APIs

```http
GET /candidates?direction=long
GET /candidates?direction=short_watch
GET /candidates?direction=all
PATCH /candidates/{candidate_id}/direction
```

---

## 77.3 Short APIs

```http
POST /short/watchlist/run
GET  /short/watchlist
GET  /short/risk/{symbol}
POST /short/paper-position
POST /short/paper-position/{position_id}/cover
```

规则：

```text
No endpoint sends broker orders.
No endpoint enables live short without config + validation gate.
```

---

# 78. v0.9 前端追加

## 78.1 Candidates 页面新增字段

```text
Direction
Allowed Direction
Strat Bar
Strat Pattern
Timeframe Continuity
Trigger Price
Trigger Stop
Short Permission
Reject Reasons
```

新增 Badge：

```text
DirectionBadge:
    Long
    Short Watch
    Paper Short
    No Trade

StratBadge:
    1
    2U
    2D
    3
    2-1-2
    3-1-2

PermissionBadge:
    Live Allowed
    Paper Only
    Disabled
    Blocked
```

---

## 78.2 Charts 页面新增标记

```text
Previous bar high / low
Inside bar range
2U / 2D trigger level
3 bar high-low range
Entry trigger
Trigger bar stop
Cover stop for short paper
```

---

## 78.3 Short Watchlist 页面

Short Watchlist 不等于交易建议。

页面顶部必须显示：

```text
Short Watchlist is paper-only by default.
This system is long-biased unless explicitly unlocked by validation.
Shorting has asymmetric risk and may lose more than expected on gap-up events.
```

字段：

```text
Ticker
Setup
Strat Pattern
Entry Trigger
Cover Stop
Gap-up Stress Loss
Borrow Status
Event Risk
Short Permission
Reject Reason
Paper Trade Button
```

---

## 78.4 Positions 页面新增 short 支持

```text
Position Side: Long / Short
Exit Action:
    Sell to Close
    Buy to Cover
Current Stop:
    Stop for long
    Cover stop for short
```

---

# 79. v0.9 配置

```yaml
pa:
  enable_structure_pa: true
  enable_strat_trigger_layer: true
  strat_v1_enabled: true
  strat_can_create_trade_alone: false
  strat_patterns_enabled:
    - inside_breakout
    - 2-1-2_continuation
    - 2-1-2_reversal
    - 3-1-2_reversal
    - 2U_continuation
    - 2D_continuation
  max_strat_patterns_live: 6

shorts:
  system_default_bias: long_biased
  allow_bearish_context: true
  allow_short_watchlist: true
  allow_short_paper: true
  allow_short_stock_live: false
  allow_short_etf_live: false
  allow_short_options: false
  no_short_small_caps: true
  no_short_low_liquidity: true
  no_short_meme_stocks: true
  no_short_before_earnings: true
  no_short_during_major_events: true
  no_short_after_large_down_move: true
  require_borrow_data_for_live: true
  require_gap_stress_test_for_live: true

options:
  live_enabled: false
  research_only: true
  priority: lowest
```

---

# 80. v0.9 优先级总表

```text
P0: Risk Engine + Position Ledger + Exit Engine
P1: US ETF / Large-cap Scanner + Basic PA + Strat Bar Labeling
P2: Frontend Dashboard + Candidates + Positions + Exit Alerts
P3: Paper Trading + Journal
P4: PA / Strat Calibration Lab
P5: Advanced PA v1, limited and ablation-gated
P6: Capital Accumulation Mode
P7: Japan Daily Scanner + JP PA/Strat Extension
P8: Short Watchlist + Paper Short
P9: AI Reviewer, explanation-only
P10: Options Backlog, lowest priority
```

重要变化：

```text
Advanced PA is no longer late backlog.
Strat is early because it makes PA more objective.
Short live remains disabled.
Options remain lowest priority.
```

---

# 81. v0.9 最终规则

```text
1. PA is core.
2. Strat is a trigger layer inside PA, not a standalone strategy.
3. Basic PA and Strat bar labeling are early production features.
4. Advanced PA v1 is allowed only after Paper / Journal exists.
5. Every advanced PA / Strat rule requires ablation.
6. The system remains long-biased by default.
7. Bearish signals first reduce long risk.
8. Short Watchlist is paper-only by default.
9. Live short requires a future validation gate.
10. Short options remain prohibited.
11. Options remain lowest priority.
12. No engine can increase risk without validation.
13. No pattern can override stop/risk/market regime.
14. If a new rule cannot be measured, it is research-only.
15. If unsure, do less.
```

v0.9 final principle:

> EdgePilot should use Strat to make PA more objective, not to create another overfit signal factory. Bearish logic should protect capital first; shorting and options can wait until the core long-biased system proves positive expectancy.

---

# 73. Alpha Strategy Architecture v1.0：盈利策略架构重构

## 73.1 为什么需要重构

此前系统中 O’Neil-core / CANSLIM-lite 是较早出现的主筛选器之一，但这容易造成一个误解：

> EdgePilot 的核心盈利来源是寻找成长大牛股。

这不准确。

O’Neil / CANSLIM 的确适合寻找潜力股和成长股 leader，但它不适合作为 EdgePilot 的唯一盈利核心。系统要追求的是：

```text
1. 先用更稳定、更可回测的 ETF / 大票趋势策略建立基础 edge。
2. 再用财报后漂移和业绩修正捕捉催化型机会。
3. 再用 O’Neil / Growth Leader 捕捉少数大行情。
4. 最后由 PA / Strat Trigger / Exit Engine 提高入场和离场质量。
```

因此 v1.0 将 Alpha Engines 重构为：

```text
Alpha Engines
├── Primary: ETF Trend / Rotation Engine
├── Secondary: Earnings Drift / Revision Engine
├── Satellite: Growth Leader / O’Neil Engine
├── Context: Japan Overnight Impact Engine
├── Defensive: Bearish Context / Short Framework
└── Backlog: Options / 0DTE / Covered Call Research
```

---

## 73.2 三条主要盈利生产线

## A. ETF Trend / Rotation Engine：第一生产线

### 定位

这是 EdgePilot 的第一生产线，用于建立最基础、最可验证、最适合小账户的 edge。

### Universe

```text
SPY
QQQ
IWM
DIA
SMH / SOXX
XLK
XLF
XLE
XLV
TLT
GLD
SLV
```

### 信号类型

```text
1. ETF 相对强度排名。
2. 趋势向上。
3. 回踩 20MA / 50MA。
4. 突破后回踩。
5. Breakout Retest。
6. VWAP Reclaim。
7. Strat Trigger confirmation。
```

### 为什么优先

```text
1. 流动性好。
2. 个股雷少。
3. 数据稳定。
4. 回测容易。
5. 适合小账户验证。
6. 适合先测试 PA + Exit Engine。
```

### 默认权限

```text
Production candidate after validation.
Options expression disabled by default.
Short version disabled by default.
```

---

## B. Earnings Drift / Revision Engine：第二生产线

### 定位

利用财报后市场反应不足、业绩上修、财报后强势延续等可量化催化因素。

### 适用对象

```text
US large-cap growth
US liquid mid/large cap
Japan Prime stocks
Japan semiconductor / trading houses / banks / defense / exporters
```

### 输入

```text
earnings surprise
revenue surprise
guidance revision
post-earnings gap
post-earnings hold
volume expansion
relative strength continuation
Japan upward revision
自社株買い
増配
PBR improvement
```

### 交易方式

```text
不追财报当天第一波。
等待：
    gap hold
    3–10 day digestion
    PA / Strat trigger
    sector confirmation
```

### 默认权限

```text
Research → Shadow → Paper → Micro Live.
Live allowed only after validation.
```

---

## C. Growth Leader / O’Neil Engine：弹性层

### 定位

O’Neil / CANSLIM 不再是唯一核心，而是股票弹性层。

它负责寻找：

```text
强成长
强相对强度
强行业
接近 52w high
平台整理
机构资金迹象
财报增长支持
```

### 它不负责

```text
最终买点
仓位大小
离场
现金流目标
期权表达
```

### 正确流程

```text
O’Neil says:
    这只股票值得关注。

PA / Strat says:
    现在有没有可执行触发。

Risk Engine says:
    这笔能不能做。

Exit Engine says:
    什么时候减仓或退出。
```

### 默认权限

```text
Candidate source only.
No direct trade permission.
```

---

# 74. Short Capability Framework v2：做空能力框架

## 74.1 为什么必须考虑做空

当前系统默认 long-biased，这适合初始阶段，但如果完全不考虑做空，会有几个问题：

```text
1. 熊市只能空仓，不能研究防守和反向机会。
2. Bearish PA 只能用于退出，不能形成系统化观察。
3. 系统无法评估 inverse ETF、short watchlist、paper short 的表现。
4. EdgePilot 对市场下跌阶段的策略适应力不足。
```

但做空风险显著高于做多，尤其对小账户：

```text
1. 理论亏损无上限。
2. gap up 风险大。
3. short squeeze 风险大。
4. borrow availability 不稳定。
5. borrow fee / hard-to-borrow 风险。
6. margin requirement 更复杂。
7. 容易变成猜顶。
```

因此 v1.0 不是开放实盘做空，而是建立分阶段能力。

---

## 74.2 做空权限分级

## Level 0：No Short，当前默认

```text
不做空。
熊市只降风险、退出、空仓。
```

---

## Level 1：Bearish Context Only

允许：

```text
识别 bearish market regime
识别弱势板块
识别 bearish PA
识别 bearish Strat trigger
```

用途仅限：

```text
avoid long
reduce
tighten stop
exit
watch only
```

不允许：

```text
live short
short option
inverse ETF live
```

默认应尽早实现。

---

## Level 2：Short Watchlist

系统输出潜在 short candidates，但不允许实盘。

候选条件：

```text
downtrend
relative weakness
breakdown
failed bounce
lower high
below 20/50MA
sector weak
market regime bearish
```

输出：

```text
symbol
short setup
trigger
cover stop
reason
risk notes
paper eligible?
```

---

## Level 3：Paper Short

允许模拟空头交易。

必须记录：

```text
short_entry
cover_stop
borrow_assumption
gap_up_risk
max_adverse_excursion
final_R
market_regime
short_squeeze_signal
```

目标：

```text
验证 bearish setup 是否有 edge。
验证做空执行是否可行。
验证是否比简单空仓或 inverse ETF 更好。
```

---

## Level 4：Inverse ETF Alternative Research

在直接做空股票之前，先研究 inverse ETF 替代方案。

例如：

```text
SH
PSQ
SQQQ, leveraged, research only
SOXS, leveraged sector inverse, research only
```

注意：

```text
杠杆反向 ETF 有路径损耗，不适合长期持有。
只做短期研究，不做长期资产。
```

优点：

```text
无借券问题
无理论无限亏损
最大亏损为投入本金
更适合小账户 paper research
```

默认：

```text
Research / Paper only.
```

---

## Level 5：Micro Live Short，后期才允许

只在满足全部条件后才允许：

```text
Paper Short >= 50 trades
expectancy > 0
profit factor > 1.2
max drawdown controlled
short squeeze loss controlled
borrow data available
user rule adherence > 95%
```

允许范围：

```text
high liquidity ETF
high liquidity large-cap
no earnings window
no meme stock
no low float
no high short interest squeeze risk
```

---

## Level 6：Small Live Short，最终阶段

只在更大账户、稳定执行后考虑。

限制：

```text
max short exposure small
no overnight short high-vol stocks
no short before earnings
no short after extended downside move
no hard-to-borrow
strict buy-to-cover stop
```

---

# 75. Short Strategy Design

## 75.1 Bearish Strategy Types

```text
1. Breakdown
2. Failed Bounce
3. Lower High Rejection
4. Bearish 2D Strat Trigger
5. Inside Bar Breakdown
6. Gap-up Failure
7. Weak Stock in Weak Sector
8. ETF Breakdown
9. Inverse ETF Rotation, research only
```

---

## 75.2 Short Entry Rules

A short candidate must satisfy:

```text
market_regime bearish or neutral-risk-off
sector weak
symbol relative weakness
below key moving averages
clear trigger
clear cover stop
liquidity sufficient
no earnings event
no high squeeze risk
```

---

## 75.3 Short Exit Rules

```text
cover if stop hit
cover if reclaim VWAP / 20MA
cover if higher low forms
cover if market regime improves
cover if sector reverses
cover if short squeeze warning appears
cover before earnings
cover if gap risk rises
```

---

## 75.4 Short Risk Guard

Checks:

```text
borrow availability
borrow fee
hard-to-borrow
short interest
days to cover
low float
meme risk
earnings date
news catalyst
gap-up frequency
market rebound risk
margin requirement
```

Default actions:

```text
unknown borrow = paper only
hard-to-borrow = reject
earnings soon = reject
high squeeze risk = reject
low liquidity = reject
```

---

# 76. PA / Strat 对做空的支持

## 76.1 Strat 对做空的价值

The Strat 天然支持双向，因为：

```text
2U = directional up
2D = directional down
3 = outside bar
1 = inside bar
```

Long triggers:

```text
2U continuation
inside bar break up
3-1-2 up
timeframe continuity bullish
```

Short triggers:

```text
2D continuation
inside bar break down
3-1-2 down
timeframe continuity bearish
```

---

## 76.2 做空中的 PA / Strat 使用方式

不允许：

```text
2D = short
```

必须是：

```text
bearish context
+ weak symbol
+ weak sector
+ bearish PA structure
+ Strat trigger
+ short risk guard
```

---

## 76.3 Bearish Context 用途

在 Level 1 阶段，bearish signals 只用于：

```text
avoid long
tighten stop
reduce
exit
```

这是做空系统的第一阶段，也是最重要阶段。

---

# 77. 数据模型追加：Direction / Short

## 77.1 candidates 增加字段

```sql
ALTER TABLE candidates
ADD COLUMN trade_direction TEXT DEFAULT 'long'; -- long, short, neutral, no_trade

ALTER TABLE candidates
ADD COLUMN short_eligibility TEXT DEFAULT 'not_allowed'; -- not_allowed, watch, paper, micro_live, live

ALTER TABLE candidates
ADD COLUMN bearish_context_score DOUBLE PRECISION;

ALTER TABLE candidates
ADD COLUMN short_risk_notes JSONB;
```

---

## 77.2 positions 增加字段

```sql
ALTER TABLE positions
ADD COLUMN position_side TEXT DEFAULT 'long'; -- long, short

ALTER TABLE positions
ADD COLUMN cover_stop DOUBLE PRECISION;

ALTER TABLE positions
ADD COLUMN borrow_fee DOUBLE PRECISION;

ALTER TABLE positions
ADD COLUMN borrow_status TEXT;

ALTER TABLE positions
ADD COLUMN squeeze_risk_score DOUBLE PRECISION;
```

---

## 77.3 short_risk_assessments

```sql
CREATE TABLE short_risk_assessments (
    assessment_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    assessment_ts TIMESTAMPTZ NOT NULL,
    borrow_status TEXT,
    borrow_fee DOUBLE PRECISION,
    hard_to_borrow BOOLEAN,
    short_interest_pct DOUBLE PRECISION,
    days_to_cover DOUBLE PRECISION,
    low_float BOOLEAN,
    meme_risk BOOLEAN,
    earnings_risk BOOLEAN,
    gap_up_risk_score DOUBLE PRECISION,
    squeeze_risk_score DOUBLE PRECISION,
    margin_requirement DOUBLE PRECISION,
    allowed_action TEXT, -- reject, watch, paper, micro_live, live
    reasons JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 77.4 paper_short_trades

```sql
CREATE TABLE paper_short_trades (
    paper_short_trade_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    strategy_name TEXT,
    setup_type TEXT,
    entry_ts TIMESTAMPTZ,
    cover_ts TIMESTAMPTZ,
    entry_price DOUBLE PRECISION,
    cover_price DOUBLE PRECISION,
    cover_stop DOUBLE PRECISION,
    final_r DOUBLE PRECISION,
    mfe_r DOUBLE PRECISION,
    mae_r DOUBLE PRECISION,
    market_regime TEXT,
    bearish_context_score DOUBLE PRECISION,
    squeeze_risk_score DOUBLE PRECISION,
    exit_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 78. API 追加：Short Framework

## 78.1 Short Watchlist

```http
GET /api/shorts/watchlist
```

---

## 78.2 Short Risk Assessment

```http
GET /api/shorts/risk/{symbol}
POST /api/shorts/risk/check
```

---

## 78.3 Paper Short

```http
POST /api/shorts/paper
GET  /api/shorts/paper
GET  /api/shorts/paper/summary
```

---

## 78.4 Bearish Context

```http
GET /api/market/bearish-context
GET /api/symbols/{symbol}/bearish-context
```

---

# 79. 前端追加：Short Lab

## 79.1 新增页面

```text
Short Lab
```

放在：

```text
Dashboard
Candidates
Positions
Exit Alerts
Cashflow
Analytics
Validation
PA Lab
Short Lab
Options Risk Lab
Governance
Journal
Settings
```

---

## 79.2 页面结构

```text
Short Lab
├── Bearish Market Context
├── Weak Sector Map
├── Short Watchlist
├── Short Candidate Detail
├── Short Risk Guard
├── Paper Short Trades
├── Inverse ETF Research
└── Short Validation Gate
```

---

## 79.3 Candidate Detail

显示：

```text
symbol
bearish setup
short trigger
cover stop
relative weakness
sector weakness
borrow status
squeeze risk
earnings risk
gap-up risk
allowed action
```

---

## 79.4 Live warning

当用户试图将 short 从 paper 转 live：

```text
Live short is disabled by default.
Shorting has theoretically unlimited risk.
Enable only after validation gate and manual confirmation.
```

---

# 80. 默认配置追加

```yaml
shorts:
  allow_short_stock_live: false
  allow_short_etf_live: false
  allow_short_options: false
  allow_short_paper: true
  allow_inverse_etf_live: false
  allow_inverse_etf_paper: true

  max_short_risk_pct: 0.0025
  max_total_short_exposure_pct: 0.05
  max_short_positions: 1

  no_short_small_caps: true
  no_short_meme_stocks: true
  no_short_before_earnings: true
  no_short_low_float: true
  no_short_high_short_interest: true
  no_short_hard_to_borrow: true
  no_short_after_large_down_move: true
  no_overnight_short_high_vol: true

  paper_short_min_trades_before_micro_live: 50
  paper_short_min_profit_factor: 1.20
  paper_short_max_drawdown_pct: 0.08
```

---

# 81. 实现计划调整 v1.0

## 新优先级

```text
P0:
    Risk Engine + Position Ledger + Exit Engine

P1:
    US ETF / Large-cap Scanner + Basic PA + Strat labeling

P2:
    Frontend Dashboard + Charts + Alerts

P3:
    Paper Trading + Journal + Analytics

P4:
    ETF Trend / Rotation Engine

P5:
    Earnings Drift / Revision Engine

P6:
    PA / Strat Calibration Lab

P7:
    Growth Leader / O’Neil Engine

P8:
    Capital Accumulation Mode

P9:
    Bearish Context + Short Watchlist + Paper Short

P10:
    Japan Expansion

P11:
    AI Reviewer

P12:
    Options Backlog / Research only
```

---

## 81.1 为什么这样排

```text
1. ETF / 大票先于个股成长股。
2. Earnings Drift 先于完整 O’Neil。
3. O’Neil 是弹性层，不是唯一主线。
4. 做空先做 context / paper，不直接 live。
5. 期权继续最低优先级。
6. Advanced PA 不再过度靠后，而通过 PA / Strat Calibration 进入中期核心。
```

---

# 82. v1.0 最终策略定位

EdgePilot 不再是：

```text
O’Neil + PA + Options 的混合 scanner
```

而是：

```text
Capital Accumulation Trading System
├── ETF Trend / Rotation as first production line
├── Earnings Drift / Revision as second production line
├── Growth Leader / O’Neil as upside satellite
├── PA / Strat as execution layer
├── Exit Engine as profit protection layer
├── Bearish Context / Short Paper as defensive research
└── Options as lowest-priority research backlog
```

Final principle:

> O’Neil finds potential leaders.  
> ETF Rotation builds the base.  
> Earnings Drift finds catalysts.  
> PA / Strat handles execution.  
> Exit Engine protects profit.  
> Shorting starts as research.  
> Options stay last.

---

# 83. Dynamic Milestone System：从 First $100K 到动态目标阶梯（v1.1）

## 83.1 为什么需要从“现金流目标”改为“动态里程碑目标”

EdgePilot 当前阶段不应被定义为“每月提款系统”，而应定义为：

> 独立交易账户复利系统。

第一目标是将 EdgePilot 交易账户滚到第一个 $100,000。  
但 $100,000 不是终点，只是第一个关键里程碑。  
后续目标应根据账户规模、策略稳定性、回撤控制和执行纪律动态调整。

核心原则：

```text
1. 先活下来。
2. 再证明 edge。
3. 再小幅放大。
4. 再滚到第一个 $100k。
5. 再解锁下一阶段目标。
6. 任何目标升级都不得倒逼风险。
```

---

## 83.2 系统定位更新

EdgePilot v1.1 的主定位：

> EdgePilot 是一个支持多用户的独立交易账户复利系统。  
> 对每个用户而言，系统目标是在不依赖 NISA、家庭储蓄、自动交易和高风险杠杆的前提下，通过 ETF Trend/Rotation、Earnings Drift/Revision、Growth Leader/O’Neil、PA/Strat 和严格风控，将独立交易账户逐步滚大。

---

## 83.3 默认目标阶梯

```text
Level 1: $2k–$10k
    Mode: Survival / Validation
    Goal: 活下来，验证系统，不追提款。

Level 2: $10k–$25k
    Mode: Small Account Growth
    Goal: 建立正期望和稳定执行记录。

Level 3: $25k–$50k
    Mode: Controlled Scaling
    Goal: 小幅放大已验证 setup。

Level 4: $50k–$100k
    Mode: First $100K Push
    Goal: 稳定突破第一个 $100k，并守住。

Level 5: $100k–$250k
    Mode: Post-100K Growth
    Goal: 继续复利，但开始强调保护和 Profit Sweep。

Level 6: $250k–$500k
    Mode: Cashflow Pilot
    Goal: 小比例测试提款/利润扫入长期资产。

Level 7: $500k–$1M
    Mode: Cashflow + Preservation
    Goal: 现金流与回撤控制并重。

Level 8: $1M+
    Mode: FIRE Support / Preservation
    Goal: 税后现金流、低回撤、资产保护。
```

---

## 83.4 Milestone 解锁规则

账户到达某个 milestone 不等于自动提高风险。

```text
if equity >= next_milestone:
    freeze_risk_increase = true
    run_milestone_review = true
```

只有满足以下条件，才允许进入下一阶段：

```text
last_100_trades_expectancy > 0
profit_factor >= configured_threshold
max_drawdown <= allowed_threshold
rule_adherence >= 90% / 95%
no_recent_risk_halt = true
manual_override_cost acceptable
profit_concentration acceptable
strategy_not_overfit = true
```

如果账户增长主要来自入金而非交易盈利：

```text
milestone_reached = true
scaling_unlocked = false
```

---

## 83.5 Contribution-adjusted Performance

系统必须区分：

```text
Current Equity:
    当前账户总净值。

Net Deposits:
    累计入金 - 出金。

Trading P/L:
    交易产生的真实收益。

Contribution-adjusted Return:
    剔除入金影响后的回报。

TWR:
    Time-weighted return，用于评估策略本身。

MWR:
    Money-weighted return，用于评估实际资金体验。
```

没有 contribution-adjusted 统计，系统会误把“追加本金”当作“交易能力”。

---

## 83.6 No Withdrawal Until First $100K

默认：

```yaml
withdrawal_allowed: false
profit_reinvest: true
cashflow_mode: disabled
```

例外：

```text
1. 税金预留。
2. 券商费用。
3. 错误入金修正。
4. 明确紧急手动 override。
```

$100k 之前，盈利默认留在 EdgePilot 账户中复利。

---

## 83.7 Drawdown Recovery Mode

复利最怕大回撤。

默认规则：

```text
if drawdown >= 5%:
    risk_per_trade *= 0.5

if drawdown >= 10%:
    live_trading = disabled
    mode = paper_review

if consecutive_losses >= 3:
    block_new_live_trades = true
```

用户可以降低阈值，但不能在未通过 review 的情况下提高阈值。

---

## 83.8 Goal Ladder Engine 数据模型

```sql
CREATE TABLE goal_ladders (
    ladder_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    active_level INTEGER NOT NULL,
    current_mode TEXT NOT NULL,
    next_milestone_amount DOUBLE PRECISION,
    base_currency TEXT DEFAULT 'USD',
    withdrawal_allowed BOOLEAN DEFAULT FALSE,
    cashflow_mode_enabled BOOLEAN DEFAULT FALSE,
    profit_sweep_allowed BOOLEAN DEFAULT FALSE,
    scaling_allowed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

```sql
CREATE TABLE goal_milestones (
    milestone_id TEXT PRIMARY KEY,
    ladder_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    label TEXT,
    min_equity DOUBLE PRECISION,
    max_equity DOUBLE PRECISION,
    mode TEXT,
    default_max_risk_pct DOUBLE PRECISION,
    withdrawal_allowed BOOLEAN DEFAULT FALSE,
    cashflow_allowed BOOLEAN DEFAULT FALSE,
    options_allowed BOOLEAN DEFAULT FALSE,
    short_live_allowed BOOLEAN DEFAULT FALSE,
    unlock_requirements JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

```sql
CREATE TABLE milestone_reviews (
    review_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    milestone_id TEXT NOT NULL,
    review_ts TIMESTAMPTZ NOT NULL,
    equity DOUBLE PRECISION,
    net_deposits DOUBLE PRECISION,
    trading_pnl DOUBLE PRECISION,
    contribution_adjusted_return DOUBLE PRECISION,
    last_100_expectancy DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    rule_adherence DOUBLE PRECISION,
    profit_concentration JSONB,
    decision TEXT, -- approved, rejected, watch
    reasons JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 84. Multi-User SaaS / Auth / Tenant Isolation（v1.1）

## 84.1 为什么允许其他人使用

EdgePilot 已有 auth 和前端驾驶舱能力，因此可以从个人系统扩展为：

```text
single-user personal app
    ↓
private beta with invited users
    ↓
multi-user SaaS
```

但 SaaS 化后，系统性质发生变化：

```text
1. 必须有租户隔离。
2. 必须有权限控制。
3. 必须有审计日志。
4. 必须有用户数据保护。
5. 必须有市场数据授权边界。
6. 必须有法律/投顾边界。
7. 必须避免变成荐股服务、复制交易或自动交易平台。
```

---

## 84.2 SaaS 产品定位

EdgePilot SaaS 的定位：

> EdgePilot SaaS 是一个多用户交易研究、计划、日志、风控和复盘工具。  
> 它帮助用户记录交易计划、管理持仓、验证策略、查看风控提醒和复盘表现。  
> 它不是券商，不自动下单，不托管资金，不代客管理资产，不提供个性化投资建议。

---

## 84.3 SaaS 非目标

SaaS 版本明确不做：

```text
1. 自动下单。
2. 托管用户资金。
3. 替用户管理资产。
4. 复制交易 / 跟单。
5. 对外荐股信号群。
6. 对用户作出个性化买卖建议。
7. 未授权市场数据转售。
8. 将平台策略包装成收益承诺。
9. 展示“保证盈利”或“稳定收益”营销文案。
10. 允许 AI 直接决定交易。
```

---

## 84.4 法律与合规边界

### 84.4.1 日本金融监管边界

系统如面向日本用户提供服务，必须避免落入需要注册的金融商品交易业务、投资助言・代理業、投资管理、募集/销售等行为。

安全定位：

```text
tooling
journal
analytics
risk management
education
strategy testing
user-defined screening
```

高风险定位：

```text
specific buy/sell advice
portfolio management for users
copy trading
auto execution
paid signal service
solicitation of financial products
managed fund or pooled capital
```

产品文案必须避免：

```text
“买这个”
“保证收益”
“跟着系统交易”
“自动赚钱”
“AI 代你交易”
```

推荐文案：

```text
“辅助研究”
“交易计划与风险管理”
“策略验证”
“用户自主决策”
“非投资建议”
```

---

### 84.4.2 投资建议免责声明

用户首次使用必须确认：

```text
1. EdgePilot 不提供投资建议。
2. 系统输出不是买卖建议。
3. 所有交易由用户自行判断并手动执行。
4. 投资可能亏损本金。
5. 过去表现不代表未来结果。
6. Paper / backtest 不代表 live 结果。
7. 用户理解期权、做空、杠杆等高风险产品可能造成重大亏损。
```

---

### 84.4.3 市场数据授权边界

SaaS 化后，行情数据风险显著上升。

默认采用：

```text
Bring Your Own Data Key
```

也就是：

```text
用户自己配置 Polygon/Massive / J-Quants / broker data key。
平台只保存加密凭证。
平台不向未授权用户转售或再分发行情数据。
```

如果平台提供共享市场数据，必须确认：

```text
vendor license allows redistribution
plan supports commercial SaaS use
exchange fees and user entitlements handled
user display rights handled
```

未确认授权前：

```text
shared market data = disabled
```

---

### 84.4.4 个人信息保护

SaaS 版本会处理：

```text
email
login logs
IP address
portfolio names
trade journals
watchlists
broker/API credential metadata
billing information
```

因此必须遵守隐私保护和安全管理要求，至少包括：

```text
purpose of use
privacy policy
data retention
security controls
access logs
user deletion/export
breach response plan
vendor/subprocessor management
```

---

# 85. SaaS 用户与角色

## 85.1 角色

```text
Platform Owner:
    系统最高管理员，管理全局配置和部署。

Platform Admin:
    管理用户、租户、系统健康，但不能查看用户交易细节，除非有授权。

Tenant Owner:
    租户拥有者，管理成员、订阅、数据源、策略权限。

Tenant Admin:
    管理租户设置和成员权限。

Trader:
    普通用户，可创建 watchlist、position、journal、paper trades。

Read-only Reviewer:
    只读角色，用于复盘、教练或团队查看。

Support:
    支持人员，只能在用户授权下临时访问。
```

---

## 85.2 权限原则

```text
least privilege
tenant isolation
no default cross-tenant access
support access requires grant
platform admin access is audited
```

---

## 85.3 RBAC 权限示例

```text
tenant.manage_members
tenant.manage_billing
tenant.manage_data_sources
strategy.configure
candidate.view
position.create
position.update
position.close_record
journal.create
journal.view
analytics.view
settings.risk.update
settings.options.update
support.grant_access
audit.view
```

敏感权限：

```text
settings.risk.update
settings.options.update
data_source.credentials.update
support.impersonate
tenant.delete
```

必须二次确认和审计。

---

# 86. SaaS 数据隔离架构

## 86.1 多租户模型

推荐：

```text
shared database + tenant_id + row-level security
```

早期也可以选择：

```text
single database
tenant_id everywhere
application-layer enforcement
later add PostgreSQL RLS
```

更高安全级别：

```text
database-per-tenant
```

但运维成本更高。

---

## 86.2 所有业务表必须加入 tenant_id

以下表必须增加：

```text
symbols, if tenant-specific
watchlists
candidates
positions
exit_alerts
trades_journal
paper_trades
strategy_settings
risk_settings
goal_ladders
analytics_daily
audit_logs
api_credentials
```

原则：

```text
任何用户数据表没有 tenant_id = schema violation
```

---

## 86.3 Row-Level Security

PostgreSQL 建议启用 RLS：

```sql
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_positions
ON positions
USING (tenant_id = current_setting('app.tenant_id')::text);
```

后端请求中必须设置：

```text
app.tenant_id
app.user_id
app.role
```

---

# 87. Auth 设计

## 87.1 登录方式

MVP：

```text
email + password
email verification
password reset
session cookie
```

后续：

```text
TOTP 2FA
OAuth Google/GitHub
Passkeys/WebAuthn
magic link
SAML/SSO, team plan
```

---

## 87.2 会话安全

```text
HttpOnly secure cookies
CSRF protection
SameSite=Lax/Strict
short-lived access session
refresh token rotation
device/session list
logout all sessions
IP/device anomaly detection
```

---

## 87.3 密码安全

```text
Argon2id or bcrypt
minimum password length
breach password check, optional
rate limit login attempts
lockout / cooldown
password reset token expiry
```

---

## 87.4 邀请流程

```text
Tenant Owner invites user
↓
email invite
↓
user accepts
↓
user completes risk acknowledgement
↓
role assigned
↓
tenant dashboard access
```

---

# 88. SaaS 数据模型

## 88.1 users

```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    display_name TEXT,
    password_hash TEXT,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 88.2 tenants

```sql
CREATE TABLE tenants (
    tenant_id TEXT PRIMARY KEY,
    tenant_name TEXT NOT NULL,
    tenant_type TEXT DEFAULT 'personal', -- personal, team, org
    owner_user_id TEXT NOT NULL,
    plan TEXT DEFAULT 'personal',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 88.3 tenant_memberships

```sql
CREATE TABLE tenant_memberships (
    membership_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    invited_by TEXT,
    joined_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (tenant_id, user_id)
);
```

---

## 88.4 invitations

```sql
CREATE TABLE invitations (
    invitation_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 88.5 auth_sessions

```sql
CREATE TABLE auth_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    tenant_id TEXT,
    refresh_token_hash TEXT,
    user_agent TEXT,
    ip_address TEXT,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 88.6 api_credentials

```sql
CREATE TABLE api_credentials (
    credential_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL, -- polygon, jquants, ibkr, email, telegram
    credential_type TEXT NOT NULL,
    encrypted_secret BYTEA NOT NULL,
    key_last4 TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 88.7 legal_acknowledgements

```sql
CREATE TABLE legal_acknowledgements (
    acknowledgement_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    document_type TEXT NOT NULL, -- tos, privacy, risk_disclosure, no_advice
    document_version TEXT NOT NULL,
    accepted_at TIMESTAMPTZ NOT NULL,
    ip_address TEXT,
    user_agent TEXT
);
```

---

## 88.8 support_access_grants

```sql
CREATE TABLE support_access_grants (
    grant_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    granted_by_user_id TEXT NOT NULL,
    support_user_id TEXT NOT NULL,
    access_level TEXT NOT NULL, -- read_only, debug_metadata
    reason TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 88.9 audit_logs

```sql
CREATE TABLE audit_logs (
    audit_id TEXT PRIMARY KEY,
    tenant_id TEXT,
    user_id TEXT,
    actor_type TEXT, -- user, system, support, admin
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    before JSONB,
    after JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 88.10 subscriptions

```sql
CREATE TABLE subscriptions (
    subscription_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    plan TEXT NOT NULL,
    status TEXT NOT NULL,
    billing_provider TEXT,
    provider_customer_id TEXT,
    provider_subscription_id TEXT,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 88.11 usage_events

```sql
CREATE TABLE usage_events (
    usage_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    user_id TEXT,
    event_type TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 89. SaaS API 设计

## 89.1 Auth

```http
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
POST /api/auth/password-reset/request
POST /api/auth/password-reset/confirm
POST /api/auth/mfa/setup
POST /api/auth/mfa/verify
GET  /api/auth/sessions
DELETE /api/auth/sessions/{session_id}
```

---

## 89.2 Tenants

```http
POST /api/tenants
GET  /api/tenants
GET  /api/tenants/{tenant_id}
PATCH /api/tenants/{tenant_id}
```

---

## 89.3 Members

```http
GET  /api/tenants/{tenant_id}/members
POST /api/tenants/{tenant_id}/invitations
PATCH /api/tenants/{tenant_id}/members/{user_id}
DELETE /api/tenants/{tenant_id}/members/{user_id}
```

---

## 89.4 Data Credentials

```http
GET  /api/tenants/{tenant_id}/credentials
POST /api/tenants/{tenant_id}/credentials
PATCH /api/tenants/{tenant_id}/credentials/{credential_id}
DELETE /api/tenants/{tenant_id}/credentials/{credential_id}
```

---

## 89.5 Legal

```http
GET  /api/legal/documents
POST /api/legal/acknowledgements
GET  /api/legal/acknowledgements/me
```

---

## 89.6 Audit

```http
GET /api/audit/logs
```

---

## 89.7 Billing

```http
GET  /api/billing/subscription
POST /api/billing/checkout
POST /api/billing/portal
POST /api/billing/webhook
```

---

# 90. SaaS 前端页面

新增页面：

```text
Login
Register
Forgot Password
MFA Setup
Tenant Switcher
Onboarding
Legal Acknowledgement
Team Members
Invitations
Data Source Settings
Billing
Audit Logs
Support Access
Admin Console
```

---

## 90.1 Onboarding Flow

```text
1. Create account
2. Verify email
3. Create tenant/workspace
4. Accept Terms / Privacy / Risk Disclosure / No Advice
5. Choose mode:
    - Personal
    - Team
6. Configure data source:
    - Bring Your Own Data Key
7. Set account goal:
    - First $100K default
    - custom milestone ladder
8. Set risk limits
9. Start paper mode
```

---

## 90.2 Data Source Settings

显示：

```text
Provider
Status
Last successful sync
Entitlement mode
Credential owner
Data sharing allowed?
```

默认：

```text
data_sharing_allowed = false
```

---

# 91. SaaS Plan / Billing

## 91.1 Plan 草案

```text
Personal:
    1 user
    BYO data keys
    journal
    dashboard
    paper trading
    limited scanners

Pro:
    1 user
    advanced analytics
    PA / Strat calibration
    more symbols
    more history

Team:
    multiple users
    shared workspaces
    read-only reviewers
    audit logs
    shared playbooks

Research:
    paper-only advanced modules
    no live flags
    options research lab, if enabled
```

---

## 91.2 Feature Flags

```text
feature_options_lab
feature_short_paper
feature_ai_reviewer
feature_japan_market
feature_team_members
feature_audit_logs
feature_advanced_pa
feature_data_export
```

Features can be enabled per plan and per tenant.

---

# 92. SaaS 合规产品边界

## 92.1 禁止类功能

除非完成法律审查和相关注册，否则 SaaS 版本禁止：

```text
1. 平台统一给所有用户发“买入/卖出”信号。
2. 针对具体用户资产情况给出个性化投资建议。
3. 自动下单。
4. 替用户管理仓位。
5. 代客交易。
6. 收取收益分成。
7. 跟单/复制交易。
8. 资金托管。
9. 推荐未授权金融产品。
```

---

## 92.2 允许类功能

```text
1. 用户自定义 watchlist。
2. 用户自定义策略参数。
3. 系统生成研究候选。
4. 系统显示风险、止损、失效条件。
5. Paper trading。
6. Journal。
7. Analytics。
8. 教育性解释。
9. 通用市场统计。
```

---

## 92.3 输出文案要求

候选输出不应写：

```text
Buy NVDA now.
Sell QQQ now.
This trade will profit.
```

应写：

```text
Candidate detected.
Setup conditions met.
Risk plan generated.
Manual decision required.
Not investment advice.
```

---

# 93. Security / Privacy / Operations

## 93.1 安全要求

```text
TLS everywhere
encrypted credentials
KMS or equivalent secret management
tenant_id isolation
audit logs
rate limiting
2FA for sensitive actions
backup and restore
least privilege admin access
support access grants
CSRF protection
secure cookies
```

---

## 93.2 隐私要求

```text
privacy policy
purpose of use
data retention policy
user data export
user data deletion
subprocessor disclosure
breach response process
access logs
```

---

## 93.3 运维要求

```text
system health
data source health
tenant usage metrics
job monitoring
error alerting
security alerting
daily backups
restore drill
audit export
```

---

# 94. Multi-User Implementation Plan

## Phase S0：Auth MVP

```text
email/password login
email verification
password reset
session cookies
basic user table
single personal tenant per user
```

验收：

```text
用户可注册、登录、退出。
每个用户自动创建 personal tenant。
```

---

## Phase S1：Tenant Isolation

```text
tenant_id added to all user-owned tables
membership table
query scoping
middleware sets tenant context
basic audit logs
```

验收：

```text
用户 A 无法访问用户 B 的 candidates / positions / journal。
```

---

## Phase S2：RBAC + Team

```text
roles
permissions
invitations
member management
read-only reviewer
tenant admin
```

验收：

```text
Tenant Owner 可邀请成员并分配只读/编辑权限。
```

---

## Phase S3：BYO Data Credentials

```text
encrypted credential storage
provider test connection
per-tenant data source settings
data entitlement status
```

验收：

```text
用户可配置自己的 Polygon/Massive key。
平台不会把一个用户的 market data 分发给另一个用户。
```

---

## Phase S4：Legal / Risk Acknowledgement

```text
terms of service
privacy policy
risk disclosure
no investment advice acknowledgement
versioned acknowledgement table
```

验收：

```text
未接受最新版本风险声明的用户不能进入 Dashboard。
```

---

## Phase S5：Billing / Plan / Feature Flags

```text
subscription table
plan management
feature flags
billing provider integration
usage events
```

验收：

```text
不同 plan 可控制功能。
Options Lab 可按 plan/tenant 禁用。
```

---

## Phase S6：Admin / Support / Audit

```text
admin console
support access grant
audit logs
security event logs
tenant deletion/export
```

验收：

```text
任何 support 访问都有授权和审计。
```

---

# 95. v1.1 实现优先级

更新后优先级：

```text
P0:
    Risk Engine + Position Ledger + Exit Engine

P1:
    Auth MVP + Personal Tenant

P1:
    Journal / Analytics + Paper Trading

P1:
    Trading Account Milestone Dashboard

P2:
    ETF Trend / Rotation Engine

P3:
    Basic PA + Strat Trigger

P4:
    Tenant Isolation + BYO Data Credentials

P5:
    Earnings Drift / Revision

P6:
    PA / Strat Calibration

P7:
    Growth Leader / O’Neil

P8:
    Team / RBAC / Audit

P9:
    Bearish Context + Paper Short

P10:
    Japan Expansion

P11:
    AI Reviewer

P12:
    Options Backlog / Research only
```

重要变化：

```text
Auth 和 tenant isolation 提前。
Options 继续最低。
AI 继续靠后。
做空继续 paper。
```

---

# 96. v1.1 最终系统定位

EdgePilot 不再只是个人交易系统，而是：

> 一个支持多用户的交易账户复利与风控研究平台。

但产品边界必须保持：

```text
No auto trading.
No investment advice.
No copy trading.
No managed accounts.
No broker execution.
No data redistribution without license.
```

Final principle:

> EdgePilot may become SaaS, but it must remain a decision-support and risk-management platform — not an investment adviser, broker, signal seller, or automated trading agent.
