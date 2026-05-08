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
