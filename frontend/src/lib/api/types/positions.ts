import type { NotificationSeverity } from "./risk";

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
  exit_profile: string | null;
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
