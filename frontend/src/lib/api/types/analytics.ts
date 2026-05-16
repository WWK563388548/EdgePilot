export type AnalyticsStrategyBreakdown = {
  strategy_name: string;
  trades_count: number;
  realized_pnl: number;
  win_rate: number | null;
  profit_factor: number | null;
  average_r: number | null;
};

export type AnalyticsExecutionQuality = {
  fills_count: number;
  matched_fills_count: number;
  review_needed_fills_count: number;
  planned_entry_count: number;
  average_entry_drag_r: number | null;
  average_entry_slippage_pct: number | null;
  planned_exit_count: number;
  average_exit_drag_r: number | null;
};

export type AnalyticsOverview = {
  from_date: string;
  to_date: string;
  equity: number;
  total_pnl: number;
  realized_pnl: number;
  unrealized_pnl: number;
  win_rate: number;
  profit_factor: number;
  expectancy_r: number;
  average_r: number;
  max_drawdown_pct: number;
  current_drawdown_pct: number;
  trades_count: number;
  open_risk_pct: number;
  open_positions_count: number;
  closed_positions_count: number;
  strategy_breakdown: AnalyticsStrategyBreakdown[];
  execution_quality: AnalyticsExecutionQuality;
};
