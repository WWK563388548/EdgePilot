const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type AccessTokenProvider = () => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | null = null;

export function setAccessTokenProvider(provider: AccessTokenProvider | null) {
  accessTokenProvider = provider;
}

export class ApiError extends Error {
  detail?: string;
  status: number;

  constructor(status: number, detail?: string) {
    super(detail ? `Request failed: ${status}: ${detail}` : `Request failed: ${status}`);
    this.detail = detail;
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
  strat_confirmation?: {
    status: string;
    base_decision: string;
    final_decision: string;
    bar_type?: string | null;
    pattern?: string | null;
    direction?: string | null;
    trigger_price?: number | null;
    trigger_stop?: number | null;
    order_type?: string | null;
    stop_limit_price?: number | null;
    max_entry_price?: number | null;
    no_chase_rules?: Array<Record<string, unknown>>;
    reason?: string | null;
    can_create_trade_alone?: boolean;
  } | null;
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

export type StratSignal = {
  signal_id: string;
  symbol_id: string;
  timeframe: string;
  ts: string;
  bar_type: string;
  previous_bar_type: string | null;
  pattern: string | null;
  direction: string | null;
  trigger_price: number | null;
  trigger_stop: number | null;
  invalidation: string | null;
  timeframe_continuity: Record<string, string> | null;
  quality_score: number | null;
  can_create_trade_alone: boolean;
  created_at?: string | null;
};

export type StratTriggerPlan = {
  symbol_id: string;
  timeframe: string;
  latest_bar_ts: string | null;
  latest_bar_type: string | null;
  previous_bar_type: string | null;
  status: string;
  pattern: string | null;
  direction: string | null;
  trigger_price: number | null;
  trigger_stop: number | null;
  order_type: string | null;
  stop_limit_price: number | null;
  max_entry_price: number | null;
  risk_per_share: number | null;
  risk_distance_pct: number | null;
  atr_14: number | null;
  distance_to_sma_20_pct: number | null;
  consecutive_2u_count: number;
  timeframe_continuity: Record<string, string> | null;
  no_chase_rules: Array<Record<string, unknown>>;
  can_create_trade_alone: boolean;
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

export type JobRunStatus = "running" | "succeeded" | "failed";

export type AutomationJobRunRequest = {
  symbols?: string[];
  min_score?: number;
  max_candidates?: number;
  refresh_market_data?: boolean;
  recalculate_outcomes?: boolean;
  evaluate_alerts?: boolean;
  outcome_limit?: number | null;
  alert_limit?: number | null;
};

export type JobRun = {
  run_id: string;
  account_id: string;
  job_type: string;
  status: JobRunStatus;
  trigger: string | null;
  records_written: number;
  error_message: string | null;
  metadata_json: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
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
  strat_signal: StratSignal | null;
  strat_plan: StratTriggerPlan | null;
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

export type ScannerOutcomeRecalculateRequest = {
  candidate_id?: string;
  symbol?: string;
  strategy_name?: string | null;
  limit?: number;
};

export type ScannerOutcomeRecalculateResponse = {
  account_id: string;
  candidates_scanned: number;
  outcomes_written: number;
  skipped_candidates: number;
  status_counts: Record<string, number>;
  symbols_processed: string[];
};

export type CandidatePlanCreate = {
  asset_type?: string;
  entry_price?: number;
  initial_stop?: number;
  quantity?: number;
};

export type AccountRiskSettings = {
  account_id: string;
  account_equity: number;
  max_risk_per_trade_pct: number;
  max_total_risk_pct: number;
  max_open_positions: number;
  max_risk_distance_pct: number;
  shadow_only_requires_paper: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type AccountRiskSettingsUpdate = Partial<
  Pick<
    AccountRiskSettings,
    | "account_equity"
    | "max_risk_per_trade_pct"
    | "max_total_risk_pct"
    | "max_open_positions"
    | "max_risk_distance_pct"
    | "shadow_only_requires_paper"
  >
>;

export type NotificationSeverity = "info" | "warning" | "action_required";

export type NotificationPreferences = {
  account_id: string;
  in_app_enabled: boolean;
  email_enabled: boolean;
  sms_enabled: boolean;
  min_severity: NotificationSeverity;
  email_to: string | null;
  phone_to: string | null;
  event_preferences: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
};

export type NotificationPreferencesUpdate = Partial<
  Pick<
    NotificationPreferences,
    | "in_app_enabled"
    | "email_enabled"
    | "sms_enabled"
    | "min_severity"
    | "email_to"
    | "phone_to"
    | "event_preferences"
  >
>;

export type GuardrailNotice = {
  level: "block" | "warning" | "info";
  code: string;
};

export type PortfolioRiskItem = {
  position_id: string;
  symbol_id: string;
  status: string | null;
  entry_price: number | null;
  stop_price: number | null;
  quantity: number | null;
  risk_amount: number | null;
  risk_pct: number | null;
  source: "position" | "preview";
  updated_at: string | null;
};

export type PortfolioRiskBucket = {
  symbol_id: string;
  risk_amount: number;
  risk_pct: number;
  position_count: number;
};

export type PortfolioRiskSummary = {
  account_id: string;
  account_equity: number;
  max_total_risk_pct: number;
  max_total_risk_amount: number;
  max_open_positions: number;
  active_position_count: number;
  total_risk_amount: number;
  total_risk_pct: number;
  remaining_risk_amount: number;
  remaining_risk_pct: number;
  planned_risk_amount: number;
  open_risk_amount: number;
  reduced_risk_amount: number;
  highest_symbol_risk: PortfolioRiskBucket | null;
  by_symbol: PortfolioRiskBucket[];
  positions: PortfolioRiskItem[];
  notices: GuardrailNotice[];
};

export type CandidatePlanPreview = {
  account_id: string;
  candidate_id: string;
  entry_price: number | null;
  initial_stop: number | null;
  risk_per_unit: number | null;
  risk_distance_pct: number | null;
  account_equity: number;
  max_risk_per_trade_pct: number;
  max_risk_amount: number;
  suggested_quantity: number | null;
  planned_quantity: number | null;
  planned_risk_amount: number | null;
  planned_risk_pct: number | null;
  max_open_positions: number;
  active_position_count: number;
  portfolio_before: PortfolioRiskSummary | null;
  portfolio_after_plan: PortfolioRiskSummary | null;
  validation_status: string | null;
  guardrails: GuardrailNotice[];
};

export type PositionActivate = {
  entry_price: number;
  quantity?: number;
  entry_date?: string;
};

export type PositionStopUpdate = {
  new_stop: number;
};

export type PositionReduce = {
  exit_price: number;
  quantity?: number;
  current_stop?: number;
  exit_date?: string;
  notes?: string;
};

export type PositionClose = {
  exit_price: number;
  quantity?: number;
  exit_date?: string;
  exit_reason?: string;
  notes?: string;
};

export type PositionStatus =
  | "planned"
  | "open"
  | "reduce"
  | "exit_pending"
  | "review_needed"
  | "closed"
  | "cancelled";

export type Position = {
  position_id: string;
  symbol_id: string;
  asset_type: string;
  strategy_name: string | null;
  entry_date: string | null;
  entry_price: number | null;
  quantity: number | null;
  initial_stop: number | null;
  current_stop: number | null;
  status: string | null;
  current_r: number | null;
  realized_pnl: number | null;
  unrealized_pnl: number | null;
  risk_per_unit: number | null;
  risk_amount: number | null;
  risk_pct: number | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ExitAlert = {
  alert_id: string;
  position_id: string;
  level: number | null;
  action: string | null;
  reason: string | null;
  new_stop: number | null;
  triggered_rules: string | null;
  snoozed_until: string | null;
  acknowledged: boolean;
  alert_ts: string | null;
};

export type ExitAlertEvaluationRequest = {
  position_id?: string;
  limit?: number;
};

export type ExitAlertEvaluationResponse = {
  account_id: string;
  positions_evaluated: number;
  alerts_created: number;
  skipped_positions: number;
  duplicate_alerts: number;
  symbols_processed: string[];
  alerts: ExitAlert[];
};

export type NotificationEvent = {
  notification_id: string;
  account_id: string;
  event_type: string;
  severity: NotificationSeverity;
  source_type: string | null;
  source_id: string | null;
  title: string | null;
  body: string | null;
  target_view: string | null;
  target_id: string | null;
  metadata_json: Record<string, unknown> | null;
  read_at: string | null;
  acknowledged_at: string | null;
  snoozed_until: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type NotificationEventUpdate = {
  read?: boolean;
  acknowledged?: boolean;
  snoozed_until?: string | null;
};

export type JournalTrade = {
  trade_id: string;
  position_id: string | null;
  symbol_id: string | null;
  entry_price: number | null;
  exit_price: number | null;
  quantity: number | null;
  gross_pnl: number | null;
  entry_ts: string | null;
  exit_ts: string | null;
  net_pnl: number | null;
  r_multiple: number | null;
  exit_reason: string | null;
  notes: string | null;
};

export type PositionCloseResponse = {
  position: Position;
  journal_trade: JournalTrade;
};

export type ExecutionImportStatus = "completed" | "partial" | "failed";

export type ExecutionCSVImportRequest = {
  broker?: string;
  source_filename?: string | null;
  csv_text: string;
};

export type ExecutionImport = {
  import_id: string;
  account_id: string;
  broker: string;
  source_filename: string | null;
  status: ExecutionImportStatus;
  rows_total: number;
  rows_imported: number;
  rows_skipped: number;
  rows_failed: number;
  error_message: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ExecutionFill = {
  fill_id: string;
  import_id: string;
  account_id: string;
  position_id: string | null;
  idempotency_key: string;
  broker: string;
  broker_account_id: string | null;
  broker_order_id: string | null;
  broker_execution_id: string | null;
  symbol_id: string;
  asset_type: string;
  side: "buy" | "sell";
  quantity: number;
  price: number;
  gross_amount: number | null;
  fees: number | null;
  net_amount: number | null;
  currency: string | null;
  executed_at: string;
  raw_row_json: Record<string, unknown> | null;
  created_at: string | null;
};

export type ExecutionImportError = {
  row_number: number;
  message: string;
  raw_row: Record<string, unknown>;
};

export type ExecutionImportResult = {
  import_record: ExecutionImport;
  fills: ExecutionFill[];
  errors: ExecutionImportError[];
};

export type AuthMe = {
  user_id: string;
  account_id: string;
  tenant_id: string;
  role: string;
  email: string | null;
  display_name: string | null;
  email_verified: boolean;
};

export type Tenant = {
  tenant_id: string;
  name: string;
  slug: string | null;
  owner_user_id: string | null;
  status: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type TenantMember = {
  tenant_id: string;
  user_id: string;
  role: string;
  email: string | null;
  display_name: string | null;
  created_at: string | null;
};

export type TenantApiKey = {
  credential_id: string;
  tenant_id: string;
  provider: string;
  label: string | null;
  status: string | null;
  key_fingerprint: string | null;
  has_encrypted_payload: boolean;
  last_verified_at: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
};

export type TenantApiKeyCreate = {
  provider: string;
  label?: string | null;
  encrypted_payload?: string | null;
  key_fingerprint?: string | null;
  metadata_json?: Record<string, unknown> | null;
};

export type TenantDataCapability = {
  capability_id: string;
  tenant_id: string;
  capability_key: string;
  provider: string | null;
  market: string | null;
  asset_type: string | null;
  timeframe: string | null;
  status: string;
  source: string | null;
  reason: string | null;
  last_checked_at: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
};

export type DataSourceCheckResponse = {
  provider: string;
  capability_key: string;
  status: string;
  source: string | null;
  message: string | null;
  checked_at: string;
  credential_id: string | null;
};

export type VerificationEmailResponse = {
  status: string;
  job_id: string | null;
};

function queryString(params: Record<string, string | number | boolean | undefined>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function responseErrorDetail(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";
  try {
    if (contentType.includes("application/json")) {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        return payload.detail;
      }
      if (Array.isArray(payload.detail)) {
        return payload.detail
          .map((item) =>
            typeof item === "object" && item !== null && "msg" in item
              ? String((item as { msg: unknown }).msg)
              : String(item)
          )
          .join("; ");
      }
    }

    const text = await response.text();
    return text || undefined;
  } catch {
    return undefined;
  }
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
    throw new ApiError(response.status, await responseErrorDetail(response));
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
    throw new ApiError(response.status, await responseErrorDetail(response));
  }

  return response.json() as Promise<T>;
}

async function patchJson<T>(path: string, body?: unknown): Promise<T> {
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
    method: "PATCH",
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status, await responseErrorDetail(response));
  }

  return response.json() as Promise<T>;
}

export const api = {
  me: () => getJson<AuthMe>("/api/auth/me"),
  resendVerificationEmail: () =>
    postJson<VerificationEmailResponse>("/api/auth/resend-verification"),
  currentTenant: () => getJson<Tenant>("/api/tenants/current"),
  tenantMembers: () => getJson<TenantMember[]>("/api/tenants/current/members"),
  dataCredentials: () => getJson<TenantApiKey[]>("/api/data-credentials"),
  createDataCredential: (request: TenantApiKeyCreate) =>
    postJson<TenantApiKey>("/api/data-credentials", request),
  checkDataCredential: (credentialId: string) =>
    postJson<DataSourceCheckResponse>(
      `/api/data-credentials/${encodeURIComponent(credentialId)}/check`
    ),
  dataCapabilities: () => getJson<TenantDataCapability[]>("/api/data-capabilities"),
  checkDataCapability: (capabilityKey: string) =>
    postJson<DataSourceCheckResponse>(
      `/api/data-capabilities/${encodeURIComponent(capabilityKey)}/check`
    ),
  dashboard: () => getJson<DashboardSummary>("/api/dashboard/summary"),
  riskSettings: () => getJson<AccountRiskSettings>("/api/settings/risk"),
  updateRiskSettings: (request: AccountRiskSettingsUpdate) =>
    patchJson<AccountRiskSettings>("/api/settings/risk", request),
  notificationPreferences: () =>
    getJson<NotificationPreferences>("/api/settings/notifications"),
  updateNotificationPreferences: (request: NotificationPreferencesUpdate) =>
    patchJson<NotificationPreferences>("/api/settings/notifications", request),
  portfolioRisk: () => getJson<PortfolioRiskSummary>("/api/risk/portfolio"),
  runAutomationJob: (request: AutomationJobRunRequest = {}) =>
    postJson<JobRun>("/api/jobs/automation/run", request),
  jobRuns: (pagination: { limit?: number; offset?: number; status?: JobRunStatus } = {}) =>
    getJson<JobRun[]>(
      `/api/jobs/runs${queryString({
        limit: pagination.limit ?? 100,
        offset: pagination.offset,
        status: pagination.status
      })}`
    ),
  jobRunsCount: (filters: { status?: JobRunStatus } = {}) =>
    getJson<CountResponse>(
      `/api/jobs/runs/count${queryString({
        status: filters.status
      })}`
    ),
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
  createCandidatePlan: (candidateId: string, request: CandidatePlanCreate = {}) =>
    postJson<Position>(`/api/candidates/${encodeURIComponent(candidateId)}/plan`, request),
  candidatePlan: (candidateId: string) =>
    getJson<Position | null>(`/api/candidates/${encodeURIComponent(candidateId)}/plan`),
  candidatePlanPreview: (candidateId: string) =>
    getJson<CandidatePlanPreview>(
      `/api/candidates/${encodeURIComponent(candidateId)}/plan-preview`
    ),
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
  recalculateScannerOutcomes: (request: ScannerOutcomeRecalculateRequest = {}) =>
    postJson<ScannerOutcomeRecalculateResponse>(
      "/api/candidates/outcomes/recalculate",
      request
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
  positions: (pagination: { limit?: number; offset?: number; status?: PositionStatus } = {}) =>
    getJson<Position[]>(
      `/api/positions${queryString({
        limit: pagination.limit ?? 100,
        offset: pagination.offset,
        status: pagination.status
      })}`
    ),
  positionsCount: (filters: { status?: PositionStatus } = {}) =>
    getJson<CountResponse>(
      `/api/positions/count${queryString({
        status: filters.status
      })}`
    ),
  activatePosition: (positionId: string, request: PositionActivate) =>
    postJson<Position>(`/api/positions/${encodeURIComponent(positionId)}/activate`, request),
  updatePositionStop: (positionId: string, request: PositionStopUpdate) =>
    postJson<Position>(`/api/positions/${encodeURIComponent(positionId)}/stop`, request),
  cancelPosition: (positionId: string) =>
    postJson<Position>(`/api/positions/${encodeURIComponent(positionId)}/cancel`),
  reducePosition: (positionId: string, request: PositionReduce) =>
    postJson<Position>(`/api/positions/${encodeURIComponent(positionId)}/reduce`, request),
  closePosition: (positionId: string, request: PositionClose) =>
    postJson<PositionCloseResponse>(
      `/api/positions/${encodeURIComponent(positionId)}/close`,
      request
    ),
  importExecutionCsv: (request: ExecutionCSVImportRequest) =>
    postJson<ExecutionImportResult>("/api/execution/imports/csv", request),
  executionImports: (
    pagination: { limit?: number; offset?: number; status?: ExecutionImportStatus } = {}
  ) =>
    getJson<ExecutionImport[]>(
      `/api/execution/imports${queryString({
        limit: pagination.limit ?? 100,
        offset: pagination.offset,
        status: pagination.status
      })}`
    ),
  executionImportsCount: (filters: { status?: ExecutionImportStatus } = {}) =>
    getJson<CountResponse>(
      `/api/execution/imports/count${queryString({
        status: filters.status
      })}`
    ),
  executionFills: (
    filters: {
      limit?: number;
      offset?: number;
      positionId?: string;
      symbolId?: string;
    } = {}
  ) =>
    getJson<ExecutionFill[]>(
      `/api/execution/fills${queryString({
        limit: filters.limit ?? 100,
        offset: filters.offset,
        position_id: filters.positionId,
        symbol_id: filters.symbolId
      })}`
    ),
  executionFillsCount: (filters: { positionId?: string; symbolId?: string } = {}) =>
    getJson<CountResponse>(
      `/api/execution/fills/count${queryString({
        position_id: filters.positionId,
        symbol_id: filters.symbolId
      })}`
    ),
  alerts: (pagination: { limit?: number; offset?: number } = {}) =>
    getJson<ExitAlert[]>(
      `/api/exit-alerts${queryString({
        acknowledged: "false",
        include_snoozed: "false",
        limit: pagination.limit ?? 100,
        offset: pagination.offset
      })}`
    ),
  alertsCount: () =>
    getJson<CountResponse>(
      `/api/exit-alerts/count${queryString({
        acknowledged: "false",
        include_snoozed: "false"
      })}`
    ),
  evaluateExitAlerts: (request: ExitAlertEvaluationRequest = {}) =>
    postJson<ExitAlertEvaluationResponse>("/api/exit-alerts/evaluate", request),
  updateAlert: (alertId: string, request: Partial<ExitAlert>) =>
    patchJson<ExitAlert>(`/api/exit-alerts/${encodeURIComponent(alertId)}`, request),
  notifications: (
    pagination: {
      acknowledged?: boolean;
      includeSnoozed?: boolean;
      limit?: number;
      offset?: number;
      read?: boolean;
    } = {}
  ) =>
    getJson<NotificationEvent[]>(
      `/api/notifications${queryString({
        acknowledged: pagination.acknowledged,
        include_snoozed: pagination.includeSnoozed,
        limit: pagination.limit ?? 100,
        offset: pagination.offset,
        read: pagination.read
      })}`
    ),
  notificationsCount: (
    filters: {
      acknowledged?: boolean;
      includeSnoozed?: boolean;
      read?: boolean;
    } = {}
  ) =>
    getJson<CountResponse>(
      `/api/notifications/count${queryString({
        acknowledged: filters.acknowledged,
        include_snoozed: filters.includeSnoozed,
        read: filters.read
      })}`
    ),
  updateNotification: (notificationId: string, request: NotificationEventUpdate) =>
    patchJson<NotificationEvent>(
      `/api/notifications/${encodeURIComponent(notificationId)}`,
      request
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
