import type { PASetup } from "./pa";
import type { StratSignal, StratTriggerPlan } from "./strat";

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
  strat_signal: StratSignal | null;
  strat_plan: StratTriggerPlan | null;
  score_breakdown: Record<string, unknown> | null;
  scanner_decision: ScannerDecision | null;
  entry_plan: Record<string, unknown> | null;
  exit_plan: Record<string, unknown> | null;
  invalidation: Record<string, unknown> | null;
};
