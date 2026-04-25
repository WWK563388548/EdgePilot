
# PRD + 技术设计文档 + 实现计划  
## 小资金交易辅助系统：美股/美股ETF/美股期权 + 日股候选扩展版

**版本**：v0.3  
**日期**：2026-04-25
**v0.2 更新重点**：追加前端实时 Dashboard、WebSocket/SSE 数据流、页面设计、组件设计、前端状态管理与实现计划。
**v0.3 更新重点**：明确正式前端技术栈、数据库选型、时序数据设计、统计分析面板、Analytics API 与实现计划。  
**目标用户**：日本居住的个人投资者  
**核心原则**：不自动交易；系统只做筛选、计划、持仓管理、离场提醒和复盘；最终由用户手动确认与下单。

---

## 0. 一句话定义

本系统是一个**多资产交易辅助系统**：

> 用规则化策略先筛选美股、美股ETF、日股、日股ETF，再用 PA（Price Action）生成买入/卖出计划；持仓后由 Exit Engine 持续监控离场条件；期权只作为 underlying 交易计划的表达工具；AI 只做结构化复核和解释，不直接决定交易。

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
- 自动判断期权是否适合表达某个 underlying 交易机会。
- 自动复盘每笔交易。
- 减少人工看图时间。
- 避免冲动交易和过度交易。

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

## 2.3 MVP 范围

### MVP 资产范围

第一阶段优先级：

1. 美股 ETF。
2. 美股大盘股/高流动性强势股。
3. 美股期权，仅作为 underlying 表达层。
4. 日股 Prime 高流动性股票，作为第二阶段。
5. 日股 ETF，作为第二阶段。

### MVP 周期

- 周线：趋势背景。
- 日线：主筛选。
- 60分钟：结构确认。
- 15分钟/30分钟：提醒触发，不做高频。

### MVP 策略

- O’Neil-core / CANSLIM-lite。
- ETF 动量轮动。
- PA 突破、回踩、VWAP reclaim、Opening Range。
- Headline Risk 降级。
- Exit Engine。
- Option Adapter。

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
    ↓
Risk Engine
    ↓
Option Adapter
    ↓
AI Reviewer
    ↓
Decision Layer
    ↓
Position Ledger
    ↓
Exit Engine
    ↓
Alerts / Dashboard / Reports
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

## 7.9 Option Adapter

### 原则

期权只在 underlying 信号通过后使用。

### 不做

- 不扫全市场期权异动后追单。
- 不做 0DTE。
- 不裸卖 call/put。
- 不买低流动性小票期权。
- 不财报前买短期期权彩票。
- 不用期权摊平亏损。

### Option Suitability Score

```text
Underlying Score: 30
PA Quality: 20
Liquidity: 20
IV Condition: 10
DTE Quality: 10
Event Risk: 10
```

### 默认过滤条件

```text
DTE preferred: 30–60
DTE aggressive: 14–30, only for small size
Delta preferred: 0.35–0.65
Bid/ask spread: reject if too wide
Volume: must be sufficient
Open interest: must be sufficient
IV: avoid long option if extreme
No earnings within high-risk window
```

### 输出

```text
option_suitability:
- none
- low
- medium
- high

preferred_expression:
- stock/ETF only
- small call/put
- debit spread
- avoid option, watch underlying
```

### 期权离场

```text
If underlying stop broken:
    exit option

If option premium loss > 30%–50%:
    exit

If option profit > 50%–100%:
    reduce

If DTE < 21:
    warning

If DTE < 14:
    reduce/exit unless explicit plan

If IV crush and underlying not moving:
    exit/reduce
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

## 12. 实现计划

## Phase 0：项目骨架

目标：

- 建 repo。
- 建数据库。
- 建配置。
- 建数据模型。
- 建基础 CLI。

任务：

```text
- 初始化 Python 项目
- 配置 ruff/mypy/pytest
- 建 DuckDB/Postgres schema
- 实现 config loader
- 实现 logging
- 实现 symbol master
- 实现 job runner
```

交付：

- 可以本地启动。
- 可以创建表。
- 可以加载配置。
- 可以跑一个 dummy scan。

---

## Phase 1：美股/ETF 数据与基础扫描器

目标：

- 用 Polygon/Massive 做美股/ETF基础扫描。

任务：

```text
- 实现 Massive client
- 拉取 US daily bars
- 拉取 ETF universe
- 计算 MA、RS、52w high、volume
- 实现 O’Neil-core scanner v1
- 实现 ETF rotation scanner v1
- 输出 candidates 表
```

验收：

- 每日能生成美股/ETF候选。
- 每个候选有 score、entry、stop、decision。
- 能导出 CSV/Markdown 报告。

---

## Phase 2：Position Ledger + Exit Engine

目标：

- 从 scanner 升级为交易管理系统。

任务：

```text
- 实现 position CRUD
- 实现 hard stop
- 实现 structure invalidation
- 实现 +1R/+2R/+3R 规则
- 实现 trailing stop
- 实现 time stop
- 实现 exit alerts
```

验收：

- 手动录入一笔持仓后，系统能每天提示状态。
- 价格触发止损后，系统输出 Exit。
- 达到 +2R 后，系统输出 Reduce。
- 无 follow-through 后，系统输出 Time Stop。

---

## Phase 3：期权适配器

目标：

- 只对通过筛选的 underlying 判断期权适配。

任务：

```text
- 实现 option chain client
- 拉取 selected underlying option chain
- 计算 spread_pct, DTE, liquidity
- 过滤 delta/DTE/spread/OI/volume
- 输出 option_suitability
- 实现 option exit rules
```

验收：

- 输入 QQQ/NVDA 等 underlying，系统能输出是否适合期权。
- 能识别 spread 太宽、DTE 太短、IV 太高、财报风险。
- 能对 option position 生成离场提醒。

---

## Phase 4：AI Reviewer

目标：

- 用结构化 AI 输出解释和反证。

任务：

```text
- 设计 JSON input schema
- 设计 JSON output schema
- 实现 prompt templates
- 实现 schema validation
- 将 AI 输出写入 candidates / exit_alerts
```

验收：

- AI 只基于规则结果解释。
- AI 输出必须是合法 JSON。
- AI 不允许绕过 hard stop。
- AI 能指出反证和风险。

---

## Phase 5：日股 J-Quants 日线版

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
```

验收：

- 每日能生成日股候选。
- 能根据前一晚美股/美元日元/ETF风险降级候选。
- 能过滤低流动性票和财报临近票。

---

## Phase 6：日股分足/Tick + IBKR L1/L2

目标：

- 减少用户看图，实现盘中 PA 判断。

任务：

```text
- 接入 J-Quants minute/tick add-on
- 计算 opening range
- 计算 VWAP
- 计算 intraday structure
- 实现 intraday alert
- 可选接 IBKR L1/L2
- 只对 top candidates 拉 L2
```

验收：

- 9:00-9:15 不生成追单信号。
- 9:15 后可以判断 opening range breakout。
- 能判断高开低走、VWAP reclaim、突破失败。
- IBKR 仅用于少数候选盘口确认。

---

## Phase 7：Backtest + Paper Trading

目标：

- 验证系统是否有正期望。

任务：

```text
- 实现 historical backtest engine
- 实现 R-multiple statistics
- 实现 strategy breakdown
- 实现 paper trading mode
- 实现 journal analytics
```

验收：

- 至少完成 2–3 年历史回测。
- 能输出 win rate、avg R、max drawdown。
- 能区分策略表现。
- Paper trading 能跑 1–2 个月。

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
