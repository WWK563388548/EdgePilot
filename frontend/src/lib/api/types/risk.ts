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
  base_suggested_quantity: number | null;
  volatility_adjusted_quantity: number | null;
  volatility_multiplier: number | null;
  atr_pct: number | null;
  vol_rank: number | null;
  exit_profile: string | null;
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
