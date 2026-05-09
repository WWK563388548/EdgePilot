export type ExecutionImportStatus = "completed" | "partial" | "failed";
export type ExecutionFillStatus = "active" | "ignored";
export type ExecutionFillReconciliationStatus =
  | "matched"
  | "review_needed"
  | "bound"
  | "confirmed"
  | "ignored";
export type ExecutionFillReconcileAction = "bind_position" | "confirm_position" | "ignore_fill";

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
  status: ExecutionFillStatus | null;
  reconciliation_status: ExecutionFillReconciliationStatus | null;
  reconciliation_note: string | null;
  reconciled_at: string | null;
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

export type ExecutionFillReconcileRequest = {
  action: ExecutionFillReconcileAction;
  target_position_id?: string | null;
  note?: string | null;
};

export type ExecutionFillReconciliationResult = {
  fill: ExecutionFill;
  source_position: import("./positions").Position | null;
  target_position: import("./positions").Position | null;
  message: string;
};
