import type { Candidate, PASetup } from "@/lib/api";
import {
  defaultLocale,
  isLocale,
  localeOptions,
  locales,
  localeTag,
  type Locale
} from "@/lib/i18n-config";

export { defaultLocale, isLocale, localeOptions, locales, localeTag, type Locale };

const text = {
  zh: {
    overview: "总览",
    candidates: "候选",
    paLab: "PA 实验室",
    positions: "持仓",
    alerts: "离场提醒",
    journal: "交易日志",
    settings: "设置",
    subtitle: "交易运营工作台",
    refresh: "30 秒刷新",
    loading: "加载中...",
    apiUnavailable: "API 不可用",
    unknown: "未知",
    symbol: "标的",
    setup: "形态",
    grade: "评级",
    validation: "验证状态",
    score: "评分",
    decision: "决策",
    entry: "入场",
    stop: "止损",
    scanDate: "扫描日期",
    detected: "识别时间",
    status: "状态",
    quality: "质量分",
    timeframe: "周期",
    openDetail: "查看详情",
    closeDetail: "关闭详情",
    candidateDetail: "候选详情",
    setupDetail: "形态详情",
    noCandidate: "没有候选数据。",
    noSetup: "没有 PA setup 数据。",
    plainExplanation: "人话解释",
    keyLevels: "关键价位",
    scoreBreakdown: "评分拆解",
    entryPlan: "入场计划",
    exitPlan: "离场计划",
    invalidation: "失效条件",
    rawPlan: "计划参数",
    allSetups: "全部形态",
    allValidation: "全部验证状态",
    marketContext: "市场环境",
    dataFreshness: "数据新鲜度",
    openPositions: "开放持仓",
    openAlerts: "未处理提醒",
    highestLevel: "最高级别",
    runtime: "运行环境",
    connections: "连接",
    app: "应用",
    apiBaseUrl: "API 地址",
    sseUrl: "SSE 地址",
    auth: "认证",
    user: "用户",
    email: "邮箱",
    authRequired: "必需",
    emailVerified: "已验证",
    emailPending: "待验证",
    backendApi: "后端 API",
    realtimeStream: "实时流",
    configured: "已配置",
    missing: "缺失",
    authNotConfigured: "认证未配置",
    checkingSession: "正在检查会话...",
    signInRequired: "需要登录",
    verifyEmail: "请先验证邮箱",
    resendVerificationEmail: "重新发送验证邮件",
    signIn: "登录",
    verifiedEmail: "我已验证邮箱",
    risk: "风险",
    usBias: "美国偏向",
    japanBias: "日本偏向",
    updated: "更新时间",
    noMarketNotes: "暂无市场备注。",
    noFreshnessRecords: "暂无数据新鲜度记录。",
    setupExplorer: "PA 形态浏览器",
    noSelection: "请选择一条记录。",
    structure: "结构",
    location: "位置",
    volume: "成交量",
    trendRs: "趋势/相对强度",
    context: "环境",
    riskStop: "风控/止损",
    type: "类型",
    qty: "数量",
    level: "级别",
    action: "动作",
    reason: "原因",
    newStop: "新止损",
    time: "时间",
    exit: "离场",
    netPnl: "净盈亏",
    rMultiple: "R 倍数",
    exitReason: "离场原因",
    source: "来源",
    candidatePool: "候选池",
    paUniverse: "PA 形态池",
    topScore: "最高分",
    activeFilters: "筛选条件",
    selected: "当前选择",
    setupCount: "形态数量"
  },
  en: {
    overview: "Overview",
    candidates: "Candidates",
    paLab: "PA Lab",
    positions: "Positions",
    alerts: "Exit Alerts",
    journal: "Journal",
    settings: "Settings",
    subtitle: "Trading operations workspace",
    refresh: "30s refresh",
    loading: "Loading data...",
    apiUnavailable: "API unavailable",
    unknown: "Unknown",
    symbol: "Symbol",
    setup: "Setup",
    grade: "Grade",
    validation: "Validation",
    score: "Score",
    decision: "Decision",
    entry: "Entry",
    stop: "Stop",
    scanDate: "Scan Date",
    detected: "Detected",
    status: "Status",
    quality: "Quality",
    timeframe: "Timeframe",
    openDetail: "Open detail",
    closeDetail: "Close detail",
    candidateDetail: "Candidate Detail",
    setupDetail: "Setup Detail",
    noCandidate: "No candidates found.",
    noSetup: "No PA setups found.",
    plainExplanation: "Plain-English Explanation",
    keyLevels: "Key Levels",
    scoreBreakdown: "Score Breakdown",
    entryPlan: "Entry Plan",
    exitPlan: "Exit Plan",
    invalidation: "Invalidation",
    rawPlan: "Plan Fields",
    allSetups: "All setups",
    allValidation: "All validation",
    marketContext: "Market Context",
    dataFreshness: "Data Freshness",
    openPositions: "Open Positions",
    openAlerts: "Open Alerts",
    highestLevel: "Highest Level",
    runtime: "Runtime",
    connections: "Connections",
    app: "App",
    apiBaseUrl: "API Base URL",
    sseUrl: "SSE URL",
    auth: "Auth",
    user: "User",
    email: "Email",
    authRequired: "required",
    emailVerified: "verified",
    emailPending: "pending",
    backendApi: "Backend API",
    realtimeStream: "Realtime Stream",
    configured: "configured",
    missing: "missing",
    authNotConfigured: "Auth is not configured",
    checkingSession: "Checking session...",
    signInRequired: "Sign in required",
    verifyEmail: "Verify your email to continue",
    resendVerificationEmail: "Resend verification email",
    signIn: "Sign in",
    verifiedEmail: "I verified my email",
    risk: "Risk",
    usBias: "US Bias",
    japanBias: "Japan Bias",
    updated: "Updated",
    noMarketNotes: "No market notes yet.",
    noFreshnessRecords: "No freshness records yet.",
    setupExplorer: "PA Setup Explorer",
    noSelection: "Select a record.",
    structure: "Structure",
    location: "Location",
    volume: "Volume",
    trendRs: "Trend/RS",
    context: "Context",
    riskStop: "Risk Stop",
    type: "Type",
    qty: "Qty",
    level: "Level",
    action: "Action",
    reason: "Reason",
    newStop: "New Stop",
    time: "Time",
    exit: "Exit",
    netPnl: "Net PnL",
    rMultiple: "R",
    exitReason: "Exit Reason",
    source: "Source",
    candidatePool: "Candidate Pool",
    paUniverse: "PA Universe",
    topScore: "Top score",
    activeFilters: "Active filters",
    selected: "Selected",
    setupCount: "Setups"
  },
  ja: {
    overview: "概要",
    candidates: "候補",
    paLab: "PA ラボ",
    positions: "ポジション",
    alerts: "決済アラート",
    journal: "売買日誌",
    settings: "設定",
    subtitle: "トレード運用ワークスペース",
    refresh: "30 秒更新",
    loading: "読み込み中...",
    apiUnavailable: "API に接続できません",
    unknown: "不明",
    symbol: "銘柄",
    setup: "セットアップ",
    grade: "評価",
    validation: "検証状態",
    score: "スコア",
    decision: "判定",
    entry: "エントリー",
    stop: "損切り",
    scanDate: "スキャン日",
    detected: "検出時刻",
    status: "状態",
    quality: "品質スコア",
    timeframe: "時間軸",
    openDetail: "詳細を開く",
    closeDetail: "詳細を閉じる",
    candidateDetail: "候補詳細",
    setupDetail: "セットアップ詳細",
    noCandidate: "候補データがありません。",
    noSetup: "PA setup データがありません。",
    plainExplanation: "わかりやすい説明",
    keyLevels: "重要価格",
    scoreBreakdown: "スコア内訳",
    entryPlan: "エントリー計画",
    exitPlan: "出口計画",
    invalidation: "無効条件",
    rawPlan: "計画パラメータ",
    allSetups: "すべての形態",
    allValidation: "すべての検証状態",
    marketContext: "市場環境",
    dataFreshness: "データ鮮度",
    openPositions: "保有中",
    openAlerts: "未対応アラート",
    highestLevel: "最高レベル",
    runtime: "実行環境",
    connections: "接続",
    app: "アプリ",
    apiBaseUrl: "API URL",
    sseUrl: "SSE URL",
    auth: "認証",
    user: "ユーザー",
    email: "メール",
    authRequired: "必須",
    emailVerified: "認証済み",
    emailPending: "未認証",
    backendApi: "バックエンド API",
    realtimeStream: "リアルタイム配信",
    configured: "設定済み",
    missing: "未設定",
    authNotConfigured: "認証が未設定です",
    checkingSession: "セッション確認中...",
    signInRequired: "ログインが必要です",
    verifyEmail: "メール認証を完了してください",
    resendVerificationEmail: "認証メールを再送",
    signIn: "ログイン",
    verifiedEmail: "メール認証済み",
    risk: "リスク",
    usBias: "米国バイアス",
    japanBias: "日本バイアス",
    updated: "更新時刻",
    noMarketNotes: "市場メモはまだありません。",
    noFreshnessRecords: "データ鮮度の記録はまだありません。",
    setupExplorer: "PA セットアップ一覧",
    noSelection: "レコードを選択してください。",
    structure: "構造",
    location: "位置",
    volume: "出来高",
    trendRs: "トレンド/RS",
    context: "環境",
    riskStop: "リスク/損切り",
    type: "種類",
    qty: "数量",
    level: "レベル",
    action: "アクション",
    reason: "理由",
    newStop: "新しい損切り",
    time: "時刻",
    exit: "決済",
    netPnl: "純損益",
    rMultiple: "R",
    exitReason: "決済理由",
    source: "ソース",
    candidatePool: "候補プール",
    paUniverse: "PA ユニバース",
    topScore: "最高スコア",
    activeFilters: "フィルター",
    selected: "選択中",
    setupCount: "セットアップ数"
  }
} as const;

export type TextKey = keyof typeof text.en;

export function t(locale: Locale, key: TextKey) {
  return text[locale][key] ?? text.en[key];
}

const labels = {
  setup: {
    breakout: { zh: "突破", en: "Breakout", ja: "ブレイクアウト" },
    pullback_to_20ma: { zh: "回踩 20 日均线", en: "Pullback to 20MA", ja: "20日線への押し目" },
    failed_breakdown_reclaim: {
      zh: "跌破后收复",
      en: "Failed breakdown reclaim",
      ja: "下抜け失敗からの回復"
    },
    oneil_leader_watch: {
      zh: "欧奈尔强势观察",
      en: "O'Neil leader watch",
      ja: "オニール型リーダー監視"
    }
  },
  status: {
    unknown: { zh: "未知", en: "Unknown", ja: "不明" },
    unlinked: { zh: "未关联", en: "Unlinked", ja: "未連携" },
    candidate: { zh: "候选", en: "Candidate", ja: "候補" },
    watch: { zh: "观察", en: "Watch", ja: "監視" },
    avoid: { zh: "回避", en: "Avoid", ja: "見送り" },
    shadow_only: { zh: "影子观察", en: "Shadow only", ja: "シャドー観察" },
    paper_allowed: { zh: "允许模拟", en: "Paper allowed", ja: "ペーパー可" },
    live_allowed: { zh: "允许实盘", en: "Live allowed", ja: "実運用可" }
  },
  plan: {
    side: { zh: "方向", en: "Side", ja: "方向" },
    timeframe: { zh: "周期", en: "Timeframe", ja: "時間軸" },
    trigger_type: { zh: "触发方式", en: "Trigger type", ja: "トリガー種別" },
    trigger_price: { zh: "触发价", en: "Trigger price", ja: "トリガー価格" },
    initial_stop: { zh: "初始止损", en: "Initial stop", ja: "初期損切り" },
    trail_reference: { zh: "跟踪参考", en: "Trail reference", ja: "トレール基準" },
    first_trim_r: { zh: "首次减仓 R", en: "First trim R", ja: "初回利確 R" },
    price_below: { zh: "跌破价格", en: "Price below", ja: "下回る価格" },
    reason: { zh: "原因", en: "Reason", ja: "理由" },
    long: { zh: "做多", en: "Long", ja: "ロング" },
    break_above_high: { zh: "突破当日高点", en: "Break above high", ja: "高値上抜け" },
    reclaim_momentum: { zh: "重新转强", en: "Reclaim momentum", ja: "勢い回復" }
  }
} as const;

export function labelFor(locale: Locale, group: "setup" | "status" | "plan", value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  const item = labels[group][value as keyof (typeof labels)[typeof group]];
  return item?.[locale] ?? value;
}

const scoreText = {
  total: {
    zh: ["总分", "综合质量分。越高表示趋势、强度、成交量和形态越一致。"],
    en: ["Total", "Overall quality. Higher means trend, strength, volume, and setup agree."],
    ja: ["総合", "総合品質。高いほどトレンド、強さ、出来高、形がそろっています。"]
  },
  trend: {
    zh: ["趋势", "价格相对 20/50/200 日均线和 52 周高点的位置。"],
    en: ["Trend", "Price location versus the 20/50/200-day averages and the 52-week high."],
    ja: ["トレンド", "20/50/200日線と52週高値に対する価格位置。"]
  },
  relative_strength: {
    zh: ["相对强度", "近 3/6 个月在当前 ETF 池中的相对表现。"],
    en: ["Relative strength", "3/6-month performance rank inside the current ETF universe."],
    ja: ["相対強度", "現在のETFユニバース内での3/6か月リターン順位。"]
  },
  volume_liquidity: {
    zh: ["成交量/流动性", "成交量是否足够、当天是否有放量支持。"],
    en: ["Volume/liquidity", "Whether liquidity is sufficient and volume supports the move."],
    ja: ["出来高/流動性", "流動性が十分で、出来高が値動きを支えているか。"]
  },
  base_setup: {
    zh: ["形态位置", "是否处在突破、回踩或强势观察等可跟踪位置。"],
    en: ["Setup location", "Whether price is in a breakout, pullback, or leader-watch area."],
    ja: ["形の位置", "ブレイクアウト、押し目、リーダー監視など追跡しやすい位置か。"]
  },
  market_context: {
    zh: ["市场环境", "当前大盘风险是否支持做多观察。"],
    en: ["Market context", "Whether the broader market regime supports long-side observation."],
    ja: ["市場環境", "市場全体の地合いがロング監視を支えているか。"]
  },
  fundamental_lite: {
    zh: ["基本面占位", "ETF 版本先给轻量默认分，后续会接入更完整基本面。"],
    en: ["Fundamental lite", "A light placeholder for ETF v1; richer fundamentals come later."],
    ja: ["簡易ファンダ", "ETF v1 の軽量プレースホルダー。詳細ファンダは後続で追加。"]
  }
} as const;

export function scoreMeta(locale: Locale, key: string) {
  const item = scoreText[key as keyof typeof scoreText];
  if (!item) {
    return { label: key, description: "" };
  }
  return { label: item[locale][0], description: item[locale][1] };
}

function numberFromRecord(data: Record<string, unknown> | null | undefined, key: string) {
  const value = data?.[key];
  return typeof value === "number" ? value : null;
}

export function setupNarrative(locale: Locale, setup: PASetup | null | undefined, candidate?: Candidate | null) {
  if (!setup) {
    return locale === "zh"
      ? "请选择一个 setup 查看解释。"
      : locale === "ja"
        ? "セットアップを選択すると説明が表示されます。"
        : "Select a setup to see the explanation.";
  }

  const symbol = setup.symbol_id;
  const setupName = labelFor(locale, "setup", setup.setup_type);
  const validation = labelFor(locale, "status", setup.validation_status);
  const score = setup.pa_quality_score ?? candidate?.score_total ?? null;
  const trigger = numberFromRecord(setup.entry_plan, "trigger_price") ?? candidate?.entry_trigger ?? null;
  const stop = numberFromRecord(setup.exit_plan, "initial_stop") ?? candidate?.initial_stop ?? null;
  const decision = labelFor(locale, "status", candidate?.decision ?? setup.status);

  if (locale === "zh") {
    return `${symbol} 当前被识别为「${setupName}」。综合分${score ?? "-"}，系统判定为「${decision}」。入场关注价约为 ${trigger ?? "-"}，初始止损约为 ${stop ?? "-"}。验证状态是「${validation}」，表示这条信号目前只适合观察和复盘，不应直接当作实盘交易指令。`;
  }
  if (locale === "ja") {
    return `${symbol} は「${setupName}」として検出されています。総合スコアは ${score ?? "-"}、判定は「${decision}」です。注目するエントリー価格は約 ${trigger ?? "-"}、初期損切りは約 ${stop ?? "-"}。検証状態は「${validation}」なので、現時点では観察・検証用であり、実運用シグナルではありません。`;
  }
  return `${symbol} is currently classified as "${setupName}". The overall score is ${score ?? "-"} and the decision is "${decision}". Watch the entry area around ${trigger ?? "-"} with an initial stop near ${stop ?? "-"}. Validation is "${validation}", so this is for observation and review, not a live trading instruction.`;
}
