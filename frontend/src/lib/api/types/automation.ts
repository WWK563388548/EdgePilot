export type JobRunStatus = "running" | "succeeded" | "failed";

export type AutomationJobRunRequest = {
  symbols?: string[];
  strategy_name?: string;
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
