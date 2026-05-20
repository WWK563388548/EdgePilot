export type ValidationStage =
  | "data_quality"
  | "backtest"
  | "shadow"
  | "paper"
  | "micro_live_allowed";

export type ValidationGateStatus =
  | "blocked"
  | "shadow_only"
  | "paper_only"
  | "micro_live_allowed";

export type ValidationKillSwitchStatus = "active" | "paused" | "blocked";

export type ValidationTestRunStatus = "running" | "succeeded" | "failed";

export type ValidationTestRun = {
  test_run_id: string;
  account_id: string;
  strategy_name: string;
  stage: ValidationStage;
  run_type: string;
  status: ValidationTestRunStatus;
  sample_count: number | null;
  trades_count: number | null;
  win_rate: number | null;
  profit_factor: number | null;
  expectancy_r: number | null;
  max_drawdown_pct: number | null;
  execution_drag_r: number | null;
  started_at: string | null;
  completed_at: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ValidationGate = {
  gate_id: string;
  account_id: string;
  strategy_name: string;
  stage: ValidationStage;
  status: ValidationGateStatus;
  required_trades: number | null;
  min_profit_factor: number | null;
  min_expectancy_r: number | null;
  max_drawdown_pct: number | null;
  max_execution_drag_r: number | null;
  current_trades: number | null;
  current_profit_factor: number | null;
  current_expectancy_r: number | null;
  current_max_drawdown_pct: number | null;
  current_execution_drag_r: number | null;
  reasons: string[];
  evaluated_at: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ValidationKillSwitch = {
  account_id: string;
  strategy_name: string;
  status: ValidationKillSwitchStatus;
  reason: string | null;
  paused_by_user_id: string | null;
  paused_at: string | null;
  expires_at: string | null;
  metadata_json: Record<string, unknown> | null;
  updated_at: string | null;
};

export type StrategyReadiness = {
  strategy_name: string;
  gate: ValidationGate;
  latest_test_run: ValidationTestRun | null;
  kill_switch: ValidationKillSwitch | null;
};

export type ValidationGateEvaluateRequest = {
  required_trades?: number;
  min_profit_factor?: number;
  min_expectancy_r?: number;
  max_drawdown_pct?: number;
  max_execution_drag_r?: number;
  metadata_json?: Record<string, unknown> | null;
};

export type StrategyKillSwitchUpdate = {
  status: ValidationKillSwitchStatus;
  reason?: string | null;
  expires_at?: string | null;
  metadata_json?: Record<string, unknown> | null;
};
