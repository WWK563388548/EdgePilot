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
  setupType?: string;
  validationStatus?: string;
  status?: string;
  limit?: number;
};

export type CandidateFilters = {
  decision?: string;
  limit?: number;
};

export type CandidateDetail = {
  candidate: Candidate;
  pa_setup: PASetup | null;
  score_breakdown: Record<string, unknown> | null;
  entry_plan: Record<string, unknown> | null;
  exit_plan: Record<string, unknown> | null;
  invalidation: Record<string, unknown> | null;
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

async function postJson<T>(path: string): Promise<T> {
  const token = accessTokenProvider ? await accessTokenProvider() : null;
  const headers: Record<string, string> = {
    Accept: "application/json"
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
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
        limit: filters.limit ?? 100
      })}`
    ),
  candidateDetail: (candidateId: string) =>
    getJson<CandidateDetail>(`/api/candidates/${encodeURIComponent(candidateId)}`),
  paSetups: (filters: PASetupFilters = {}) =>
    getJson<PASetup[]>(
      `/api/pa/setups${queryString({
        symbol: filters.symbol,
        setup_type: filters.setupType,
        validation_status: filters.validationStatus,
        status: filters.status,
        timeframe: "1d",
        limit: filters.limit ?? 100
      })}`
    ),
  paSetupExplain: (setupId: string, barLimit = 90) =>
    getJson<PASetupExplain>(
      `/api/pa/setups/${encodeURIComponent(setupId)}/explain${queryString({
        bar_limit: barLimit
      })}`
    ),
  positions: () => getJson<Position[]>("/api/positions?limit=100"),
  alerts: () => getJson<ExitAlert[]>("/api/exit-alerts?acknowledged=false&limit=100"),
  journal: () => getJson<JournalTrade[]>("/api/journal/trades?limit=100")
};
