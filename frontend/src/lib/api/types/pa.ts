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
