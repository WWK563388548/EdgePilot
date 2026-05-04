const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type AccessTokenProvider = () => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | null = null;

export function setAccessTokenProvider(provider: AccessTokenProvider | null) {
  accessTokenProvider = provider;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number) {
    super(`Request failed: ${status}`);
    this.status = status;
  }
}

export type DashboardSummary = {
  market_context: {
    snapshot_ts: string | null;
    risk_level: string | null;
    us_bias: string | null;
    japan_bias: string | null;
    notes: string | null;
  };
  risk_mode: string;
  candidate_count: number;
  open_position_count: number;
  exit_alert_count: number;
  highest_exit_level: number | null;
  data_freshness: Array<{
    dataset_key: string;
    last_updated_at: string;
    source: string | null;
  }>;
};

export type Candidate = {
  candidate_id: string;
  symbol_id: string;
  scan_date: string;
  strategy_name: string;
  setup_type: string | null;
  pa_setup_id: string | null;
  score_total: number | null;
  entry_trigger: number | null;
  initial_stop: number | null;
  decision: string | null;
  option_suitability: string | null;
  ai_review_json: string | null;
  created_at: string | null;
  pa_setup_grade: string | null;
  validation_status: string | null;
};

export type ScannerDecisionRule = {
  key: string;
  score?: number | null;
  max_score?: number | null;
  threshold?: number | null;
  passed?: boolean | null;
};

export type ScannerDecision = {
  version: string;
  strategy: string;
  decision: string;
  score?: number | null;
  total_score?: number | null;
  setup_type?: string | null;
  setup_grade?: string | null;
  validation_status?: string | null;
  trigger_price?: number | null;
  initial_stop?: number | null;
  passed_rules: ScannerDecisionRule[];
  failed_rules: ScannerDecisionRule[];
  watch_reasons: string[];
  upgrade_conditions: string[];
  risk_notes: string[];
  metrics: Record<string, unknown>;
};

export type PASetup = {
  setup_id: string;
  symbol_id: string;
  timeframe: string;
  detected_ts: string;
  setup_type: string;
  setup_grade: string | null;
  pa_quality_score: number | null;
  structure_score: number | null;
  location_score: number | null;
  volume_score: number | null;
  trend_rs_score: number | null;
  context_score: number | null;
  risk_stop_score: number | null;
  followthrough_score: number | null;
  entry_plan: Record<string, unknown> | null;
  exit_plan: Record<string, unknown> | null;
  invalidation: Record<string, unknown> | null;
  status: string | null;
  validation_status: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type PAEvidenceBar = {
  ts: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
};

export type PAEvidenceLevel = {
  key: string;
  value: number;
  source: string | null;
};

export type PASetupExplain = {
  setup_id: string;
  symbol_id: string;
  timeframe: string;
  detected_ts: string;
  setup_type: string;
  validation_status: string | null;
  summary: string;
  strengths: string[];
  watchouts: string[];
  score_breakdown: Record<string, unknown> | null;
  evidence: {
    bars: PAEvidenceBar[];
    levels: PAEvidenceLevel[];
    latest_facts: Record<string, unknown> | null;
  };
};

export type PASetupFilters = {
  symbol?: string;
  timeframe?: string;
  setupType?: string;
  validationStatus?: string;
  status?: string;
  limit?: number;
  offset?: number;
};

export type CandidateFilters = {
  decision?: string;
  limit?: number;
  offset?: number;
};

export type CountResponse = {
  total: number;
};

export type AccountScannerRequest = {
  symbols?: string[];
  min_score?: number;
  max_candidates?: number;
  recalculate_facts?: boolean;
};

export type AccountRefreshRequest = {
  symbols?: string[];
  lookback_days?: number;
  min_score?: number;
  max_candidates?: number;
};

export type ETFOneilScannerResponse = {
  account_id: string;
  timeframe: string;
  symbols_scanned: string[];
  facts_written: number;
  setups_written: number;
  candidates_written: number;
  decision_counts: Record<string, number>;
  latest_scan_date: string | null;
  latest_bar_date: string | null;
  skipped_symbols: string[];
  candidates: Candidate[];
};

export type ETFUniverseSeedSymbolResult = {
  symbol: string;
  status: "success" | "failed";
  bars_written: number;
  error_message: string | null;
};

export type ETFUniverseSeedResponse = {
  account_id: string;
  timeframe: string;
  from_date: string;
  to_date: string;
  symbols_requested: string[];
  bars_written: number;
  facts_written: number;
  setups_written: number;
  candidates_written: number;
  decision_counts: Record<string, number>;
  latest_scan_date: string | null;
  latest_bar_date: string | null;
  skipped_symbols: string[];
  symbol_results: ETFUniverseSeedSymbolResult[];
  candidates: Candidate[];
};

export type CandidateDetail = {
  candidate: Candidate;
  pa_setup: PASetup | null;
  score_breakdown: Record<string, unknown> | null;
  scanner_decision: ScannerDecision | null;
  entry_plan: Record<string, unknown> | null;
  exit_plan: Record<string, unknown> | null;
  invalidation: Record<string, unknown> | null;
};

export type ScannerOutcome = {
  outcome_id: string;
  account_id: string;
  candidate_id: string;
  pa_setup_id: string | null;
  symbol_id: string;
  timeframe: string;
  detected_ts: string;
  setup_type: string | null;
  setup_grade: string | null;
  score_total: number | null;
  reference_close: number | null;
  entry_trigger: number | null;
  initial_stop: number | null;
  bars_available: number;
  evaluation_status: string;
  latest_evaluated_ts: string | null;
  triggered_entry: boolean | null;
  trigger_ts: string | null;
  stopped_out: boolean | null;
  stop_ts: string | null;
  stop_hit_before_trigger: boolean | null;
  false_breakout: boolean | null;
  forward_return_5d: number | null;
  forward_return_10d: number | null;
  forward_return_20d: number | null;
  forward_return_60d: number | null;
  mfe_5d: number | null;
  mfe_10d: number | null;
  mfe_20d: number | null;
  mfe_60d: number | null;
  mae_5d: number | null;
  mae_10d: number | null;
  mae_20d: number | null;
  mae_60d: number | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ScannerOutcomeSummary = {
  total: number;
  pending_count: number;
  matured_count: number;
  triggered_count: number;
  stopped_count: number;
  false_breakout_count: number;
  positive_20d_count: number;
  positive_60d_count: number;
  trigger_rate: number | null;
  stop_rate: number | null;
  false_breakout_rate: number | null;
  positive_20d_rate: number | null;
  positive_60d_rate: number | null;
  avg_forward_return_20d: number | null;
  avg_forward_return_60d: number | null;
  avg_mfe_20d: number | null;
  avg_mfe_60d: number | null;
  avg_mae_20d: number | null;
  avg_mae_60d: number | null;
};

export type ScannerOutcomeFilters = {
  evaluationStatus?: string;
  symbol?: string;
  limit?: number;
  offset?: number;
};

export type Position = {
  position_id: string;
  symbol_id: string;
  asset_type: string;
  strategy_name: string | null;
  entry_price: number | null;
  quantity: number | null;
  current_stop: number | null;
  status: string | null;
  current_r: number | null;
  unrealized_pnl: number | null;
  updated_at: string | null;
};

export type ExitAlert = {
  alert_id: string;
  position_id: string;
  level: number | null;
  action: string | null;
  reason: string | null;
  new_stop: number | null;
  acknowledged: boolean;
  alert_ts: string | null;
};

export type JournalTrade = {
  trade_id: string;
  symbol_id: string | null;
  entry_ts: string | null;
  exit_ts: string | null;
  net_pnl: number | null;
  r_multiple: number | null;
  exit_reason: string | null;
  notes: string | null;
};

export type AuthMe = {
  user_id: string;
  account_id: string;
  role: string;
  email: string | null;
  display_name: string | null;
  email_verified: boolean;
};

export type VerificationEmailResponse = {
  status: string;
  job_id: string | null;
};

function queryString(params: Record<string, string | number | undefined>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function getJson<T>(path: string): Promise<T> {
  const token = accessTokenProvider ? await accessTokenProvider() : null;
  const headers: Record<string, string> = {
    Accept: "application/json"
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status);
  }

  return response.json() as Promise<T>;
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const token = accessTokenProvider ? await accessTokenProvider() : null;
  const headers: Record<string, string> = {
    Accept: "application/json"
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status);
  }

  return response.json() as Promise<T>;
}

export const api = {
  me: () => getJson<AuthMe>("/api/auth/me"),
  resendVerificationEmail: () =>
    postJson<VerificationEmailResponse>("/api/auth/resend-verification"),
  dashboard: () => getJson<DashboardSummary>("/api/dashboard/summary"),
  candidates: (filters: CandidateFilters = {}) =>
    getJson<Candidate[]>(
      `/api/candidates${queryString({
        decision: filters.decision,
        limit: filters.limit ?? 100,
        offset: filters.offset
      })}`
    ),
  candidateCount: (filters: CandidateFilters = {}) =>
    getJson<CountResponse>(
      `/api/candidates/count${queryString({
        decision: filters.decision
      })}`
    ),
  scanAccountOneilCandidates: (request: AccountScannerRequest = {}) =>
    postJson<ETFOneilScannerResponse>("/api/candidates/scanners/us-etf/oneil-core", request),
  refreshAccountOneilCandidates: (request: AccountRefreshRequest = {}) =>
    postJson<ETFUniverseSeedResponse>(
      "/api/candidates/scanners/us-etf/oneil-core/refresh",
      request
    ),
  candidateDetail: (candidateId: string) =>
    getJson<CandidateDetail>(`/api/candidates/${encodeURIComponent(candidateId)}`),
  scannerOutcomes: (filters: ScannerOutcomeFilters = {}) =>
    getJson<ScannerOutcome[]>(
      `/api/candidates/outcomes${queryString({
        evaluation_status: filters.evaluationStatus,
        symbol: filters.symbol,
        limit: filters.limit ?? 100,
        offset: filters.offset
      })}`
    ),
  scannerOutcomesCount: (filters: ScannerOutcomeFilters = {}) =>
    getJson<CountResponse>(
      `/api/candidates/outcomes/count${queryString({
        evaluation_status: filters.evaluationStatus,
        symbol: filters.symbol
      })}`
    ),
  scannerOutcomeSummary: (filters: ScannerOutcomeFilters = {}) =>
    getJson<ScannerOutcomeSummary>(
      `/api/candidates/outcomes/summary${queryString({
        evaluation_status: filters.evaluationStatus,
        symbol: filters.symbol
      })}`
    ),
  candidateOutcome: (candidateId: string) =>
    getJson<ScannerOutcome>(`/api/candidates/${encodeURIComponent(candidateId)}/outcome`),
  paSetups: (filters: PASetupFilters = {}) =>
    getJson<PASetup[]>(
      `/api/pa/setups${queryString({
        symbol: filters.symbol,
        setup_type: filters.setupType,
        validation_status: filters.validationStatus,
        status: filters.status,
        timeframe: filters.timeframe ?? "1d",
        limit: filters.limit ?? 100,
        offset: filters.offset
      })}`
    ),
  paSetupsCount: (filters: PASetupFilters = {}) =>
    getJson<CountResponse>(
      `/api/pa/setups/count${queryString({
        symbol: filters.symbol,
        setup_type: filters.setupType,
        validation_status: filters.validationStatus,
        status: filters.status,
        timeframe: filters.timeframe ?? "1d"
      })}`
    ),
  paSetupExplain: (setupId: string, barLimit = 90) =>
    getJson<PASetupExplain>(
      `/api/pa/setups/${encodeURIComponent(setupId)}/explain${queryString({
        bar_limit: barLimit
      })}`
    ),
  positions: (pagination: { limit?: number; offset?: number } = {}) =>
    getJson<Position[]>(
      `/api/positions${queryString({
        limit: pagination.limit ?? 100,
        offset: pagination.offset
      })}`
    ),
  positionsCount: () => getJson<CountResponse>("/api/positions/count"),
  alerts: (pagination: { limit?: number; offset?: number } = {}) =>
    getJson<ExitAlert[]>(
      `/api/exit-alerts${queryString({
        acknowledged: "false",
        limit: pagination.limit ?? 100,
        offset: pagination.offset
      })}`
    ),
  alertsCount: () =>
    getJson<CountResponse>(
      `/api/exit-alerts/count${queryString({
        acknowledged: "false"
      })}`
    ),
  journal: (pagination: { limit?: number; offset?: number } = {}) =>
    getJson<JournalTrade[]>(
      `/api/journal/trades${queryString({
        limit: pagination.limit ?? 100,
        offset: pagination.offset
      })}`
    ),
  journalCount: () => getJson<CountResponse>("/api/journal/trades/count")
};
