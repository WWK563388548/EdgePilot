"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  ClipboardCheck,
  FileUp,
  ListChecks,
  Settings,
  ShieldCheck,
  Workflow
} from "lucide-react";
import { useEffect, useState } from "react";

import { AuthScreen } from "@/components/workspace/auth-screen";
import { AutomationView } from "@/components/workspace/automation-view";
import {
  CandidatesView,
  type CandidateDecisionFilter,
  type CandidateStrategyFilter
} from "@/components/workspace/candidates-view";
import { DataState } from "@/components/workspace/atoms/data-state";
import { ExecutionImportView } from "@/components/workspace/organisms/execution-import-view";
import { OverviewView } from "@/components/workspace/overview-view";
import { OutcomesView } from "@/components/workspace/outcomes-view";
import { PALabView } from "@/components/workspace/pa-lab-view";
import { PaperReviewView } from "@/components/workspace/paper-review-view";
import { AlertsTable, JournalTable, PositionsTable } from "@/components/workspace/organisms/account-tables";
import { NotificationBell, NotificationModal } from "@/components/workspace/organisms/notification-center";
import { SettingsPanel } from "@/components/workspace/secondary-views";
import { WorkspaceFrame, WorkspaceHeader, WorkspaceNav, type WorkspaceNavItem } from "@/components/workspace/shell";
import { api, type PositionStatus } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { localeTag, type Locale } from "@/lib/i18n-config";
import { useWorkspaceStore } from "@/lib/store";
import { useAppI18n } from "@/lib/use-app-i18n";

const views: WorkspaceNavItem[] = [
  { id: "overview", labelKey: "overview", icon: BarChart3 },
  { id: "candidates", labelKey: "candidates", icon: ListChecks },
  { id: "pa_lab", labelKey: "paLab", icon: ShieldCheck },
  { id: "outcomes", labelKey: "outcomes", icon: Activity },
  { id: "paper_review", labelKey: "paperReview", icon: ClipboardCheck },
  { id: "positions", labelKey: "positions", icon: BriefcaseBusiness },
  { id: "alerts", labelKey: "alerts", icon: AlertTriangle },
  { id: "automation", labelKey: "automation", icon: Workflow },
  { id: "execution", labelKey: "executionImport", icon: FileUp },
  { id: "journal", labelKey: "journal", icon: BookOpen },
  { id: "settings", labelKey: "settings", icon: Settings }
];

const LIST_PAGE_SIZE = 10;

export function EdgePilotWorkspace({ locale }: { locale: Locale }) {
  const { t } = useAppI18n();
  const auth = useAuth();
  const { view, setView } = useWorkspaceStore();
  const [candidateDecision, setCandidateDecision] = useState<CandidateDecisionFilter>("candidate");
  const [candidateStrategy, setCandidateStrategy] = useState<CandidateStrategyFilter>("all");
  const [candidatePage, setCandidatePage] = useState(0);
  const [positionPage, setPositionPage] = useState(0);
  const [positionStatus, setPositionStatus] = useState<PositionStatus | "all">("all");
  const [alertPage, setAlertPage] = useState(0);
  const [notificationPage, setNotificationPage] = useState(0);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [journalPage, setJournalPage] = useState(0);
  const queriesEnabled = auth.ready && auth.isAuthenticated && auth.emailVerified;

  useEffect(() => {
    document.documentElement.lang = localeTag[locale];
  }, [locale]);

  useEffect(() => {
    if (view === "notifications") {
      setNotificationPage(0);
      setNotificationsOpen(true);
      setView("overview");
    }
  }, [setView, view]);

  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
    enabled: queriesEnabled
  });
  const portfolioRisk = useQuery({
    queryKey: ["portfolio-risk"],
    queryFn: api.portfolioRisk,
    enabled: queriesEnabled
  });
  const paperReview = useQuery({
    queryKey: ["paper-review"],
    queryFn: api.paperReview,
    enabled: queriesEnabled
  });
  const candidates = useQuery({
    queryKey: ["candidates", candidateDecision, candidateStrategy, candidatePage],
    queryFn: () =>
      api.candidates({
        decision: candidateDecision === "all" ? undefined : candidateDecision,
        strategy_name: candidateStrategy === "all" ? undefined : candidateStrategy,
        limit: LIST_PAGE_SIZE + 1,
        offset: candidatePage * LIST_PAGE_SIZE
      }),
    enabled: queriesEnabled
  });
  const candidatesCount = useQuery({
    queryKey: ["candidates-count", candidateDecision, candidateStrategy],
    queryFn: () =>
      api.candidateCount({
        decision: candidateDecision === "all" ? undefined : candidateDecision,
        strategy_name: candidateStrategy === "all" ? undefined : candidateStrategy
      }),
    enabled: queriesEnabled
  });
  const positions = useQuery({
    queryKey: ["positions", positionStatus, positionPage],
    queryFn: () =>
      api.positions({
        limit: LIST_PAGE_SIZE + 1,
        offset: positionPage * LIST_PAGE_SIZE,
        status: positionStatus === "all" ? undefined : positionStatus
      }),
    enabled: queriesEnabled
  });
  const positionsCount = useQuery({
    queryKey: ["positions-count", positionStatus],
    queryFn: () =>
      api.positionsCount({
        status: positionStatus === "all" ? undefined : positionStatus
      }),
    enabled: queriesEnabled
  });
  const alerts = useQuery({
    queryKey: ["alerts", alertPage],
    queryFn: () =>
      api.alerts({
        limit: LIST_PAGE_SIZE + 1,
        offset: alertPage * LIST_PAGE_SIZE
      }),
    enabled: queriesEnabled
  });
  const alertsCount = useQuery({
    queryKey: ["alerts-count"],
    queryFn: api.alertsCount,
    enabled: queriesEnabled
  });
  const notifications = useQuery({
    queryKey: ["notifications", notificationPage],
    queryFn: () =>
      api.notifications({
        acknowledged: false,
        limit: LIST_PAGE_SIZE + 1,
        offset: notificationPage * LIST_PAGE_SIZE,
        read: false
    }),
    enabled: queriesEnabled,
    refetchInterval: notificationsOpen ? 15_000 : false
  });
  const notificationsCount = useQuery({
    queryKey: ["notifications-count"],
    queryFn: () =>
      api.notificationsCount({
        acknowledged: false,
        read: false
      }),
    enabled: queriesEnabled,
    refetchInterval: 15_000
  });
  const journal = useQuery({
    queryKey: ["journal", journalPage],
    queryFn: () =>
      api.journal({
        limit: LIST_PAGE_SIZE + 1,
        offset: journalPage * LIST_PAGE_SIZE
      }),
    enabled: queriesEnabled
  });
  const journalCount = useQuery({
    queryKey: ["journal-count"],
    queryFn: api.journalCount,
    enabled: queriesEnabled
  });

  const summary = dashboard.data;
  const riskTone = summary?.risk_mode === "normal" ? "good" : summary?.risk_mode === "shock" ? "bad" : "warn";
  const candidateRows = (candidates.data ?? []).slice(0, LIST_PAGE_SIZE);
  const positionRows = (positions.data ?? []).slice(0, LIST_PAGE_SIZE);
  const alertRows = (alerts.data ?? []).slice(0, LIST_PAGE_SIZE);
  const notificationRows = (notifications.data ?? []).slice(0, LIST_PAGE_SIZE);
  const journalRows = (journal.data ?? []).slice(0, LIST_PAGE_SIZE);
  const hasCandidateNextPage =
    candidatesCount.data?.total !== undefined
      ? (candidatePage + 1) * LIST_PAGE_SIZE < candidatesCount.data.total
      : (candidates.data ?? []).length > LIST_PAGE_SIZE;
  const hasPositionNextPage =
    positionsCount.data?.total !== undefined
      ? (positionPage + 1) * LIST_PAGE_SIZE < positionsCount.data.total
      : (positions.data ?? []).length > LIST_PAGE_SIZE;
  const hasAlertNextPage =
    alertsCount.data?.total !== undefined
      ? (alertPage + 1) * LIST_PAGE_SIZE < alertsCount.data.total
      : (alerts.data ?? []).length > LIST_PAGE_SIZE;
  const hasNotificationNextPage =
    notificationsCount.data?.total !== undefined
      ? (notificationPage + 1) * LIST_PAGE_SIZE < notificationsCount.data.total
      : (notifications.data ?? []).length > LIST_PAGE_SIZE;
  const hasJournalNextPage =
    journalCount.data?.total !== undefined
      ? (journalPage + 1) * LIST_PAGE_SIZE < journalCount.data.total
      : (journal.data ?? []).length > LIST_PAGE_SIZE;

  if (!auth.configured) {
    return <AuthScreen locale={locale} status={t("authNotConfigured")} />;
  }

  if (!auth.ready) {
    return <AuthScreen locale={locale} status={t("checkingSession")} />;
  }

  if (!auth.isAuthenticated) {
    return <AuthScreen action={auth.login} locale={locale} status={t("signInRequired")} />;
  }

  if (!auth.emailVerified) {
    return (
      <AuthScreen
        action={auth.resendVerificationEmail}
        locale={locale}
        secondaryAction={auth.refreshSession}
        secondaryLabel={t("verifiedEmail")}
        status={t("verifyEmail")}
      />
    );
  }

  return (
    <WorkspaceFrame>
      <WorkspaceHeader
        actions={
          <NotificationBell
            count={notificationsCount.data?.total ?? 0}
            locale={locale}
            onOpen={() => {
              setNotificationPage(0);
              setNotificationsOpen(true);
              void notifications.refetch();
              void notificationsCount.refetch();
            }}
          />
        }
        locale={locale}
        riskMode={summary?.risk_mode ?? t("unknown")}
        riskTone={riskTone}
      />
      <WorkspaceNav activeView={view} items={views} locale={locale} onChange={setView} />

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <DataState isLoading={dashboard.isLoading} isError={dashboard.isError} locale={locale} />

        {view === "overview" && (
          <OverviewView
            locale={locale}
            portfolioRisk={portfolioRisk.data}
            summary={summary}
          />
        )}
        {view === "candidates" && (
          <CandidatesView
            data={candidateRows}
            decisionFilter={candidateDecision}
            error={candidates.isError}
            hasNextPage={hasCandidateNextPage}
            loading={candidates.isLoading}
            locale={locale}
            onDecisionFilterChange={(filter) => {
              setCandidateDecision(filter);
              setCandidatePage(0);
            }}
            onStrategyFilterChange={(filter) => {
              setCandidateStrategy(filter);
              setCandidatePage(0);
            }}
            onPageChange={setCandidatePage}
            page={candidatePage}
            pageSize={LIST_PAGE_SIZE}
            strategyFilter={candidateStrategy}
            totalCount={candidatesCount.data?.total}
          />
        )}
        {view === "pa_lab" && <PALabView locale={locale} />}
        {view === "outcomes" && <OutcomesView locale={locale} />}
        {view === "paper_review" && (
          <PaperReviewView
            data={paperReview.data}
            error={paperReview.isError}
            loading={paperReview.isLoading}
            locale={locale}
          />
        )}
        {view === "positions" && (
          <PositionsTable
            data={positionRows}
            error={positions.isError}
            hasNextPage={hasPositionNextPage}
            loading={positions.isLoading}
            locale={locale}
            onPageChange={setPositionPage}
            onStatusFilterChange={(filter) => {
              setPositionStatus(filter);
              setPositionPage(0);
            }}
            page={positionPage}
            pageSize={LIST_PAGE_SIZE}
            statusFilter={positionStatus}
            totalCount={positionsCount.data?.total}
          />
        )}
        {view === "alerts" && (
          <AlertsTable
            data={alertRows}
            error={alerts.isError}
            hasNextPage={hasAlertNextPage}
            loading={alerts.isLoading}
            locale={locale}
            onPageChange={setAlertPage}
            page={alertPage}
            pageSize={LIST_PAGE_SIZE}
            totalCount={alertsCount.data?.total}
          />
        )}
        {view === "automation" && <AutomationView locale={locale} />}
        {view === "execution" && <ExecutionImportView locale={locale} />}
        {view === "journal" && (
          <JournalTable
            data={journalRows}
            error={journal.isError}
            hasNextPage={hasJournalNextPage}
            loading={journal.isLoading}
            locale={locale}
            onPageChange={setJournalPage}
            page={journalPage}
            pageSize={LIST_PAGE_SIZE}
            totalCount={journalCount.data?.total}
          />
        )}
        {view === "settings" && <SettingsPanel locale={locale} />}
      </div>
      <NotificationModal
        data={notificationRows}
        error={notifications.isError}
        hasNextPage={hasNotificationNextPage}
        loading={notifications.isLoading}
        locale={locale}
        onClose={() => setNotificationsOpen(false)}
        onNavigate={(targetView) => {
          setNotificationsOpen(false);
          setView(targetView);
        }}
        onPageChange={setNotificationPage}
        open={notificationsOpen}
        page={notificationPage}
        pageSize={LIST_PAGE_SIZE}
        totalCount={notificationsCount.data?.total}
      />
    </WorkspaceFrame>
  );
}
