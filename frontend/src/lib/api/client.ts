import { getJson, patchJson, postJson, queryString } from "./http";
import type {
  DashboardSummary,
  Candidate,
  ScannerDecisionRule,
  ScannerDecision,
  PASetup,
  StratSignal,
  StratTriggerPlan,
  PAEvidenceBar,
  PAEvidenceLevel,
  PASetupExplain,
  PASetupFilters,
  CandidateFilters,
  CountResponse,
  JobRunStatus,
  AutomationJobRunRequest,
  JobRun,
  AccountScannerRequest,
  AccountRefreshRequest,
  ETFOneilScannerResponse,
  ETFUniverseSeedSymbolResult,
  ETFUniverseSeedResponse,
  CandidateDetail,
  ScannerOutcome,
  ScannerOutcomeSummary,
  ScannerOutcomeFilters,
  ScannerOutcomeRecalculateRequest,
  ScannerOutcomeRecalculateResponse,
  CandidatePlanCreate,
  AccountRiskSettings,
  AccountRiskSettingsUpdate,
  NotificationSeverity,
  NotificationPreferences,
  NotificationPreferencesUpdate,
  GuardrailNotice,
  PortfolioRiskItem,
  PortfolioRiskBucket,
  PortfolioRiskSummary,
  CandidatePlanPreview,
  PositionActivate,
  PositionStopUpdate,
  PositionReduce,
  PositionClose,
  PositionStatus,
  Position,
  ExitAlert,
  ExitAlertEvaluationRequest,
  ExitAlertEvaluationResponse,
  NotificationEvent,
  NotificationEventUpdate,
  JournalTrade,
  PositionCloseResponse,
  ExecutionImportStatus,
  ExecutionFillStatus,
  ExecutionFillReconciliationStatus,
  ExecutionFillReconcileRequest,
  ExecutionCSVImportRequest,
  ExecutionImport,
  ExecutionFill,
  ExecutionImportError,
  ExecutionImportResult,
  ExecutionFillReconciliationResult,
  AuthMe,
  Tenant,
  TenantMember,
  TenantApiKey,
  TenantApiKeyCreate,
  TenantDataCapability,
  DataSourceCheckResponse,
  VerificationEmailResponse
} from "./types";

export const api = {
  me: () => getJson<AuthMe>("/api/auth/me"),
  resendVerificationEmail: () =>
    postJson<VerificationEmailResponse>("/api/auth/resend-verification"),
  currentTenant: () => getJson<Tenant>("/api/tenants/current"),
  tenantMembers: () => getJson<TenantMember[]>("/api/tenants/current/members"),
  dataCredentials: () => getJson<TenantApiKey[]>("/api/data-credentials"),
  createDataCredential: (request: TenantApiKeyCreate) =>
    postJson<TenantApiKey>("/api/data-credentials", request),
  checkDataCredential: (credentialId: string) =>
    postJson<DataSourceCheckResponse>(
      `/api/data-credentials/${encodeURIComponent(credentialId)}/check`
    ),
  dataCapabilities: () => getJson<TenantDataCapability[]>("/api/data-capabilities"),
  checkDataCapability: (capabilityKey: string) =>
    postJson<DataSourceCheckResponse>(
      `/api/data-capabilities/${encodeURIComponent(capabilityKey)}/check`
    ),
  dashboard: () => getJson<DashboardSummary>("/api/dashboard/summary"),
  riskSettings: () => getJson<AccountRiskSettings>("/api/settings/risk"),
  updateRiskSettings: (request: AccountRiskSettingsUpdate) =>
    patchJson<AccountRiskSettings>("/api/settings/risk", request),
  notificationPreferences: () =>
    getJson<NotificationPreferences>("/api/settings/notifications"),
  updateNotificationPreferences: (request: NotificationPreferencesUpdate) =>
    patchJson<NotificationPreferences>("/api/settings/notifications", request),
  portfolioRisk: () => getJson<PortfolioRiskSummary>("/api/risk/portfolio"),
  runAutomationJob: (request: AutomationJobRunRequest = {}) =>
    postJson<JobRun>("/api/jobs/automation/run", request),
  jobRuns: (pagination: { limit?: number; offset?: number; status?: JobRunStatus } = {}) =>
    getJson<JobRun[]>(
      `/api/jobs/runs${queryString({
        limit: pagination.limit ?? 100,
        offset: pagination.offset,
        status: pagination.status
      })}`
    ),
  jobRunsCount: (filters: { status?: JobRunStatus } = {}) =>
    getJson<CountResponse>(
      `/api/jobs/runs/count${queryString({
        status: filters.status
      })}`
    ),
  candidates: (filters: CandidateFilters = {}) =>
    getJson<Candidate[]>(
      `/api/candidates${queryString({
        decision: filters.decision,
        strategy_name: filters.strategy_name,
        limit: filters.limit ?? 100,
        offset: filters.offset
      })}`
    ),
  candidateCount: (filters: CandidateFilters = {}) =>
    getJson<CountResponse>(
      `/api/candidates/count${queryString({
        decision: filters.decision,
        strategy_name: filters.strategy_name
      })}`
    ),
  scanAccountOneilCandidates: (request: AccountScannerRequest = {}) =>
    postJson<ETFOneilScannerResponse>("/api/candidates/scanners/us-etf/oneil-core", request),
  refreshAccountOneilCandidates: (request: AccountRefreshRequest = {}) =>
    postJson<ETFUniverseSeedResponse>(
      "/api/candidates/scanners/us-etf/oneil-core/refresh",
      request
    ),
  scanAccountRotationCandidates: (request: AccountScannerRequest = {}) =>
    postJson<ETFOneilScannerResponse>("/api/candidates/scanners/us-etf/rotation", request),
  refreshAccountRotationCandidates: (request: AccountRefreshRequest = {}) =>
    postJson<ETFUniverseSeedResponse>(
      "/api/candidates/scanners/us-etf/rotation/refresh",
      request
    ),
  candidateDetail: (candidateId: string) =>
    getJson<CandidateDetail>(`/api/candidates/${encodeURIComponent(candidateId)}`),
  createCandidatePlan: (candidateId: string, request: CandidatePlanCreate = {}) =>
    postJson<Position>(`/api/candidates/${encodeURIComponent(candidateId)}/plan`, request),
  candidatePlan: (candidateId: string) =>
    getJson<Position | null>(`/api/candidates/${encodeURIComponent(candidateId)}/plan`),
  candidatePlanPreview: (candidateId: string) =>
    getJson<CandidatePlanPreview>(
      `/api/candidates/${encodeURIComponent(candidateId)}/plan-preview`
    ),
  scannerOutcomes: (filters: ScannerOutcomeFilters = {}) =>
    getJson<ScannerOutcome[]>(
      `/api/candidates/outcomes${queryString({
        evaluation_status: filters.evaluationStatus,
        symbol: filters.symbol,
        limit: filters.limit ?? 100,
        offset: filters.offset
      })}`
    ),
  scannerOutcomesCount: (filters: ScannerOutcomeFilters = {}) =>
    getJson<CountResponse>(
      `/api/candidates/outcomes/count${queryString({
        evaluation_status: filters.evaluationStatus,
        symbol: filters.symbol
      })}`
    ),
  scannerOutcomeSummary: (filters: ScannerOutcomeFilters = {}) =>
    getJson<ScannerOutcomeSummary>(
      `/api/candidates/outcomes/summary${queryString({
        evaluation_status: filters.evaluationStatus,
        symbol: filters.symbol
      })}`
    ),
  recalculateScannerOutcomes: (request: ScannerOutcomeRecalculateRequest = {}) =>
    postJson<ScannerOutcomeRecalculateResponse>(
      "/api/candidates/outcomes/recalculate",
      request
    ),
  candidateOutcome: (candidateId: string) =>
    getJson<ScannerOutcome>(`/api/candidates/${encodeURIComponent(candidateId)}/outcome`),
  paSetups: (filters: PASetupFilters = {}) =>
    getJson<PASetup[]>(
      `/api/pa/setups${queryString({
        symbol: filters.symbol,
        setup_type: filters.setupType,
        validation_status: filters.validationStatus,
        status: filters.status,
        timeframe: filters.timeframe ?? "1d",
        limit: filters.limit ?? 100,
        offset: filters.offset
      })}`
    ),
  paSetupsCount: (filters: PASetupFilters = {}) =>
    getJson<CountResponse>(
      `/api/pa/setups/count${queryString({
        symbol: filters.symbol,
        setup_type: filters.setupType,
        validation_status: filters.validationStatus,
        status: filters.status,
        timeframe: filters.timeframe ?? "1d"
      })}`
    ),
  paSetupExplain: (setupId: string, barLimit = 90) =>
    getJson<PASetupExplain>(
      `/api/pa/setups/${encodeURIComponent(setupId)}/explain${queryString({
        bar_limit: barLimit
      })}`
    ),
  positions: (pagination: { limit?: number; offset?: number; status?: PositionStatus } = {}) =>
    getJson<Position[]>(
      `/api/positions${queryString({
        limit: pagination.limit ?? 100,
        offset: pagination.offset,
        status: pagination.status
      })}`
    ),
  positionsCount: (filters: { status?: PositionStatus } = {}) =>
    getJson<CountResponse>(
      `/api/positions/count${queryString({
        status: filters.status
      })}`
    ),
  activatePosition: (positionId: string, request: PositionActivate) =>
    postJson<Position>(`/api/positions/${encodeURIComponent(positionId)}/activate`, request),
  updatePositionStop: (positionId: string, request: PositionStopUpdate) =>
    postJson<Position>(`/api/positions/${encodeURIComponent(positionId)}/stop`, request),
  cancelPosition: (positionId: string) =>
    postJson<Position>(`/api/positions/${encodeURIComponent(positionId)}/cancel`),
  reducePosition: (positionId: string, request: PositionReduce) =>
    postJson<Position>(`/api/positions/${encodeURIComponent(positionId)}/reduce`, request),
  closePosition: (positionId: string, request: PositionClose) =>
    postJson<PositionCloseResponse>(
      `/api/positions/${encodeURIComponent(positionId)}/close`,
      request
    ),
  importExecutionCsv: (request: ExecutionCSVImportRequest) =>
    postJson<ExecutionImportResult>("/api/execution/imports/csv", request),
  executionImports: (
    pagination: { limit?: number; offset?: number; status?: ExecutionImportStatus } = {}
  ) =>
    getJson<ExecutionImport[]>(
      `/api/execution/imports${queryString({
        limit: pagination.limit ?? 100,
        offset: pagination.offset,
        status: pagination.status
      })}`
    ),
  executionImportsCount: (filters: { status?: ExecutionImportStatus } = {}) =>
    getJson<CountResponse>(
      `/api/execution/imports/count${queryString({
        status: filters.status
      })}`
    ),
  executionFills: (
    filters: {
      limit?: number;
      offset?: number;
      positionId?: string;
      reconciliationStatus?: ExecutionFillReconciliationStatus;
      status?: ExecutionFillStatus;
      symbolId?: string;
    } = {}
  ) =>
    getJson<ExecutionFill[]>(
      `/api/execution/fills${queryString({
        limit: filters.limit ?? 100,
        offset: filters.offset,
        position_id: filters.positionId,
        reconciliation_status: filters.reconciliationStatus,
        status: filters.status,
        symbol_id: filters.symbolId
      })}`
    ),
  executionFillsCount: (
    filters: {
      positionId?: string;
      reconciliationStatus?: ExecutionFillReconciliationStatus;
      status?: ExecutionFillStatus;
      symbolId?: string;
    } = {}
  ) =>
    getJson<CountResponse>(
      `/api/execution/fills/count${queryString({
        position_id: filters.positionId,
        reconciliation_status: filters.reconciliationStatus,
        status: filters.status,
        symbol_id: filters.symbolId
      })}`
    ),
  reconcileExecutionFill: (fillId: string, request: ExecutionFillReconcileRequest) =>
    postJson<ExecutionFillReconciliationResult>(
      `/api/execution/fills/${encodeURIComponent(fillId)}/reconcile`,
      request
    ),
  alerts: (pagination: { limit?: number; offset?: number } = {}) =>
    getJson<ExitAlert[]>(
      `/api/exit-alerts${queryString({
        acknowledged: "false",
        include_snoozed: "false",
        limit: pagination.limit ?? 100,
        offset: pagination.offset
      })}`
    ),
  alertsCount: () =>
    getJson<CountResponse>(
      `/api/exit-alerts/count${queryString({
        acknowledged: "false",
        include_snoozed: "false"
      })}`
    ),
  evaluateExitAlerts: (request: ExitAlertEvaluationRequest = {}) =>
    postJson<ExitAlertEvaluationResponse>("/api/exit-alerts/evaluate", request),
  updateAlert: (alertId: string, request: Partial<ExitAlert>) =>
    patchJson<ExitAlert>(`/api/exit-alerts/${encodeURIComponent(alertId)}`, request),
  notifications: (
    pagination: {
      acknowledged?: boolean;
      includeSnoozed?: boolean;
      limit?: number;
      offset?: number;
      read?: boolean;
    } = {}
  ) =>
    getJson<NotificationEvent[]>(
      `/api/notifications${queryString({
        acknowledged: pagination.acknowledged,
        include_snoozed: pagination.includeSnoozed,
        limit: pagination.limit ?? 100,
        offset: pagination.offset,
        read: pagination.read
      })}`
    ),
  notificationsCount: (
    filters: {
      acknowledged?: boolean;
      includeSnoozed?: boolean;
      read?: boolean;
    } = {}
  ) =>
    getJson<CountResponse>(
      `/api/notifications/count${queryString({
        acknowledged: filters.acknowledged,
        include_snoozed: filters.includeSnoozed,
        read: filters.read
      })}`
    ),
  updateNotification: (notificationId: string, request: NotificationEventUpdate) =>
    patchJson<NotificationEvent>(
      `/api/notifications/${encodeURIComponent(notificationId)}`,
      request
    ),
  journal: (pagination: { limit?: number; offset?: number } = {}) =>
    getJson<JournalTrade[]>(
      `/api/journal/trades${queryString({
        limit: pagination.limit ?? 100,
        offset: pagination.offset
      })}`
    ),
  journalCount: () => getJson<CountResponse>("/api/journal/trades/count")
};
