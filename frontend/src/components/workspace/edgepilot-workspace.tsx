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
import { useEffect } from "react";

import { AuthScreen } from "@/components/workspace/auth-screen";
import { CandidatesView } from "@/components/workspace/candidates-view";
import { DataState } from "@/components/workspace/common";
import { OverviewView } from "@/components/workspace/overview-view";
import { PALabView } from "@/components/workspace/pa-lab-view";
import { AlertsTable, JournalTable, PositionsTable, SettingsPanel } from "@/components/workspace/secondary-views";
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

export function EdgePilotWorkspace({ locale }: { locale: Locale }) {
  const { t } = useAppI18n();
  const auth = useAuth();
  const { view, setView } = useWorkspaceStore();
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
    queryKey: ["candidates", "candidate"],
    queryFn: () => api.candidates({ decision: "candidate", limit: 100 }),
    enabled: queriesEnabled
  });
  const positions = useQuery({
    queryKey: ["positions"],
    queryFn: api.positions,
    enabled: queriesEnabled
  });
  const alerts = useQuery({
    queryKey: ["alerts"],
    queryFn: api.alerts,
    enabled: queriesEnabled
  });
  const journal = useQuery({
    queryKey: ["journal"],
    queryFn: api.journal,
    enabled: queriesEnabled
  });

  const summary = dashboard.data;
  const riskTone = summary?.risk_mode === "normal" ? "good" : summary?.risk_mode === "shock" ? "bad" : "warn";

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
            data={candidates.data ?? []}
            error={candidates.isError}
            loading={candidates.isLoading}
            locale={locale}
          />
        )}
        {view === "pa_lab" && <PALabView locale={locale} />}
        {view === "positions" && (
          <PositionsTable
            data={positions.data ?? []}
            error={positions.isError}
            loading={positions.isLoading}
            locale={locale}
          />
        )}
        {view === "alerts" && (
          <AlertsTable
            data={alerts.data ?? []}
            error={alerts.isError}
            loading={alerts.isLoading}
            locale={locale}
          />
        )}
        {view === "journal" && (
          <JournalTable
            data={journal.data ?? []}
            error={journal.isError}
            loading={journal.isLoading}
            locale={locale}
          />
        )}
        {view === "settings" && <SettingsPanel locale={locale} />}
      </div>
    </WorkspaceFrame>
  );
}
