"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  ListChecks,
  Settings,
  ShieldCheck
} from "lucide-react";
import { useEffect, useState } from "react";

import { AuthScreen } from "@/components/workspace/auth-screen";
import { CandidatesView, type CandidateDecisionFilter } from "@/components/workspace/candidates-view";
import { DataState } from "@/components/workspace/atoms/data-state";
import { OverviewView } from "@/components/workspace/overview-view";
import { PALabView } from "@/components/workspace/pa-lab-view";
import { AlertsTable, JournalTable, PositionsTable } from "@/components/workspace/organisms/account-tables";
import { SettingsPanel } from "@/components/workspace/secondary-views";
import { WorkspaceFrame, WorkspaceHeader, WorkspaceNav, type WorkspaceNavItem } from "@/components/workspace/shell";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { localeTag, type Locale } from "@/lib/i18n-config";
import { useWorkspaceStore } from "@/lib/store";
import { useAppI18n } from "@/lib/use-app-i18n";

const views: WorkspaceNavItem[] = [
  { id: "overview", labelKey: "overview", icon: BarChart3 },
  { id: "candidates", labelKey: "candidates", icon: ListChecks },
  { id: "pa_lab", labelKey: "paLab", icon: ShieldCheck },
  { id: "positions", labelKey: "positions", icon: BriefcaseBusiness },
  { id: "alerts", labelKey: "alerts", icon: AlertTriangle },
  { id: "journal", labelKey: "journal", icon: BookOpen },
  { id: "settings", labelKey: "settings", icon: Settings }
];

const LIST_PAGE_SIZE = 10;

export function EdgePilotWorkspace({ locale }: { locale: Locale }) {
  const { t } = useAppI18n();
  const auth = useAuth();
  const { view, setView } = useWorkspaceStore();
  const [candidateDecision, setCandidateDecision] = useState<CandidateDecisionFilter>("candidate");
  const [candidatePage, setCandidatePage] = useState(0);
  const [positionPage, setPositionPage] = useState(0);
  const [alertPage, setAlertPage] = useState(0);
  const [journalPage, setJournalPage] = useState(0);
  const queriesEnabled = auth.ready && auth.isAuthenticated && auth.emailVerified;

  useEffect(() => {
    document.documentElement.lang = localeTag[locale];
  }, [locale]);

  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
    enabled: queriesEnabled
  });
  const candidates = useQuery({
    queryKey: ["candidates", candidateDecision, candidatePage],
    queryFn: () =>
      api.candidates({
        decision: candidateDecision === "all" ? undefined : candidateDecision,
        limit: LIST_PAGE_SIZE + 1,
        offset: candidatePage * LIST_PAGE_SIZE
      }),
    enabled: queriesEnabled
  });
  const positions = useQuery({
    queryKey: ["positions", positionPage],
    queryFn: () =>
      api.positions({
        limit: LIST_PAGE_SIZE + 1,
        offset: positionPage * LIST_PAGE_SIZE
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
  const journal = useQuery({
    queryKey: ["journal", journalPage],
    queryFn: () =>
      api.journal({
        limit: LIST_PAGE_SIZE + 1,
        offset: journalPage * LIST_PAGE_SIZE
      }),
    enabled: queriesEnabled
  });

  const summary = dashboard.data;
  const riskTone = summary?.risk_mode === "normal" ? "good" : summary?.risk_mode === "shock" ? "bad" : "warn";
  const candidateRows = (candidates.data ?? []).slice(0, LIST_PAGE_SIZE);
  const positionRows = (positions.data ?? []).slice(0, LIST_PAGE_SIZE);
  const alertRows = (alerts.data ?? []).slice(0, LIST_PAGE_SIZE);
  const journalRows = (journal.data ?? []).slice(0, LIST_PAGE_SIZE);

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
        locale={locale}
        riskMode={summary?.risk_mode ?? t("unknown")}
        riskTone={riskTone}
      />
      <WorkspaceNav activeView={view} items={views} locale={locale} onChange={setView} />

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <DataState isLoading={dashboard.isLoading} isError={dashboard.isError} locale={locale} />

        {view === "overview" && <OverviewView locale={locale} summary={summary} />}
        {view === "candidates" && (
          <CandidatesView
            data={candidateRows}
            decisionFilter={candidateDecision}
            error={candidates.isError}
            hasNextPage={(candidates.data ?? []).length > LIST_PAGE_SIZE}
            loading={candidates.isLoading}
            locale={locale}
            onDecisionFilterChange={(filter) => {
              setCandidateDecision(filter);
              setCandidatePage(0);
            }}
            onPageChange={setCandidatePage}
            page={candidatePage}
            pageSize={LIST_PAGE_SIZE}
          />
        )}
        {view === "pa_lab" && <PALabView locale={locale} />}
        {view === "positions" && (
          <PositionsTable
            data={positionRows}
            error={positions.isError}
            hasNextPage={(positions.data ?? []).length > LIST_PAGE_SIZE}
            loading={positions.isLoading}
            locale={locale}
            onPageChange={setPositionPage}
            page={positionPage}
            pageSize={LIST_PAGE_SIZE}
          />
        )}
        {view === "alerts" && (
          <AlertsTable
            data={alertRows}
            error={alerts.isError}
            hasNextPage={(alerts.data ?? []).length > LIST_PAGE_SIZE}
            loading={alerts.isLoading}
            locale={locale}
            onPageChange={setAlertPage}
            page={alertPage}
            pageSize={LIST_PAGE_SIZE}
          />
        )}
        {view === "journal" && (
          <JournalTable
            data={journalRows}
            error={journal.isError}
            hasNextPage={(journal.data ?? []).length > LIST_PAGE_SIZE}
            loading={journal.isLoading}
            locale={locale}
            onPageChange={setJournalPage}
            page={journalPage}
            pageSize={LIST_PAGE_SIZE}
          />
        )}
        {view === "settings" && <SettingsPanel locale={locale} />}
      </div>
    </WorkspaceFrame>
  );
}
