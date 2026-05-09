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
