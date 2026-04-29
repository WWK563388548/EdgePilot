"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  CircleDot,
  Database,
  Eye,
  Filter,
  ListChecks,
  LogIn,
  LogOut,
  PlugZap,
  RefreshCcw,
  Settings,
  ShieldCheck,
  X
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Candidate, CandidateDetail, ExitAlert, JournalTrade, PASetup, Position } from "@/lib/api";
import { labelFor, localeOptions, scoreMeta, setupNarrative, t } from "@/lib/i18n";
import type { Locale, TextKey } from "@/lib/i18n";
import { useWorkspaceStore } from "@/lib/store";
import type { WorkspaceView } from "@/lib/store";

const views: Array<{ id: WorkspaceView; labelKey: TextKey }> = [
  { id: "overview", labelKey: "overview" },
  { id: "candidates", labelKey: "candidates" },
  { id: "pa_lab", labelKey: "paLab" },
  { id: "positions", labelKey: "positions" },
  { id: "alerts", labelKey: "alerts" },
  { id: "journal", labelKey: "journal" },
  { id: "settings", labelKey: "settings" }
];

const localeTag: Record<Locale, string> = {
  zh: "zh-CN",
  en: "en-US",
  ja: "ja-JP"
};

function formatValue(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

function formatNumber(value: number | null | undefined, digits = 1, locale: Locale = "en") {
  if (value === null || value === undefined) {
    return "-";
  }
  return new Intl.NumberFormat(localeTag[locale], {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0
  }).format(value);
}

function formatDate(value: string | null | undefined, locale: Locale = "en") {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat(localeTag[locale], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function StatusPill({ label, tone = "neutral" }: { label: string; tone?: "good" | "warn" | "bad" | "neutral" }) {
  const tones = {
    good: "bg-teal-50 text-teal-700 ring-teal-200",
    warn: "bg-amber-50 text-amber-700 ring-amber-200",
    bad: "bg-rose-50 text-rose-700 ring-rose-200",
    neutral: "bg-slate-50 text-slate-700 ring-slate-200"
  };

  return (
    <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ${tones[tone]}`}>
      {label}
    </span>
  );
}

function DataState({ isLoading, isError, locale = "en" }: { isLoading: boolean; isError: boolean; locale?: Locale }) {
  if (isLoading) {
    return <span className="text-sm text-slate-500">{t(locale, "loading")}</span>;
  }
  if (isError) {
    return <span className="text-sm text-rose-700">{t(locale, "apiUnavailable")}</span>;
  }
  return null;
}

function decisionTone(value: string | null | undefined): "good" | "warn" | "bad" | "neutral" {
  if (value === "candidate" || value === "live_allowed") {
    return "good";
  }
  if (value === "watch" || value === "paper_allowed" || value === "shadow_only") {
    return "warn";
  }
  if (value === "avoid" || value === "failed") {
    return "bad";
  }
  return "neutral";
}

export default function Home() {
  const auth = useAuth();
  const { view, setView, locale, setLocale } = useWorkspaceStore();
  const queriesEnabled = auth.ready && auth.isAuthenticated && auth.emailVerified;
  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
    enabled: queriesEnabled
  });
  const candidates = useQuery({
    queryKey: ["candidates"],
    queryFn: api.candidates,
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
    return <AuthScreen locale={locale} status={t(locale, "authNotConfigured")} />;
  }

  if (!auth.ready) {
    return <AuthScreen locale={locale} status={t(locale, "checkingSession")} />;
  }

  if (!auth.isAuthenticated) {
    return <AuthScreen action={auth.login} locale={locale} status={t(locale, "signInRequired")} />;
  }

  if (!auth.emailVerified) {
    return (
      <AuthScreen
        action={auth.resendVerificationEmail}
        locale={locale}
        secondaryAction={auth.refreshSession}
        secondaryLabel={t(locale, "verifiedEmail")}
        status={t(locale, "verifyEmail")}
      />
    );
  }

  return (
    <main className="min-h-screen bg-[#eef2f5]">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-ink text-white">
                <BarChart3 size={22} />
              </div>
              <div>
                <h1 className="text-xl font-semibold tracking-normal text-ink">EdgePilot</h1>
                <p className="text-sm text-slate-600">{t(locale, "subtitle")}</p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill label={summary?.risk_mode ?? t(locale, "unknown")} tone={riskTone} />
            <LanguageSwitcher locale={locale} setLocale={setLocale} />
            <AuthButton />
            <div className="inline-flex items-center gap-2 rounded-md border border-line bg-panel px-3 py-2 text-sm text-slate-700">
              <RefreshCcw size={16} />
              {t(locale, "refresh")}
            </div>
          </div>
        </div>
      </header>

      <section className="border-b border-line bg-panel">
        <div className="mx-auto flex max-w-7xl gap-2 overflow-x-auto px-4 py-3 sm:px-6 lg:px-8">
          {views.map((item) => (
            <button
              key={item.id}
              className={`focus-ring rounded-md px-3 py-2 text-sm font-medium ${
                view === item.id
                  ? "bg-ink text-white"
                  : "border border-line bg-white text-slate-700 hover:border-slate-400"
              }`}
              onClick={() => setView(item.id)}
              type="button"
            >
              {t(locale, item.labelKey)}
            </button>
          ))}
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <DataState isLoading={dashboard.isLoading} isError={dashboard.isError} locale={locale} />

        {view === "overview" && (
          <div className="space-y-6">
            <section className="grid gap-3 md:grid-cols-4">
              <Metric icon={<ListChecks size={18} />} label={t(locale, "candidates")} value={summary?.candidate_count ?? 0} />
              <Metric icon={<BriefcaseBusiness size={18} />} label={t(locale, "openPositions")} value={summary?.open_position_count ?? 0} />
              <Metric icon={<AlertTriangle size={18} />} label={t(locale, "openAlerts")} value={summary?.exit_alert_count ?? 0} />
              <Metric icon={<ShieldCheck size={18} />} label={t(locale, "highestLevel")} value={summary?.highest_exit_level ?? "-"} />
            </section>

            <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-md border border-line bg-white p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-base font-semibold text-ink">{t(locale, "marketContext")}</h2>
                  <Activity size={18} className="text-teal" />
                </div>
                <dl className="grid gap-3 sm:grid-cols-2">
                  <Field label={t(locale, "risk")} value={summary?.market_context.risk_level} />
                  <Field label={t(locale, "usBias")} value={summary?.market_context.us_bias} />
                  <Field label={t(locale, "japanBias")} value={summary?.market_context.japan_bias} />
                  <Field label={t(locale, "updated")} value={formatDate(summary?.market_context.snapshot_ts, locale)} />
                </dl>
                <p className="mt-4 text-sm text-slate-600">{summary?.market_context.notes ?? t(locale, "noMarketNotes")}</p>
              </div>

              <div className="rounded-md border border-line bg-white p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-base font-semibold text-ink">{t(locale, "dataFreshness")}</h2>
                  <Database size={18} className="text-teal" />
                </div>
                <div className="space-y-3">
                  {summary?.data_freshness.length ? (
                    summary.data_freshness.map((item) => (
                      <div key={item.dataset_key} className="flex items-center justify-between gap-3 border-b border-line pb-2 last:border-0 last:pb-0">
                        <div>
                          <div className="text-sm font-medium text-ink">{item.dataset_key}</div>
                          <div className="text-xs text-slate-500">{item.source ?? t(locale, "unknown")}</div>
                        </div>
                        <div className="text-right text-xs text-slate-600">{formatDate(item.last_updated_at, locale)}</div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-600">{t(locale, "noFreshnessRecords")}</p>
                  )}
                </div>
              </div>
            </section>
          </div>
        )}

        {view === "candidates" && <CandidatesTable data={candidates.data ?? []} loading={candidates.isLoading} error={candidates.isError} locale={locale} />}
        {view === "pa_lab" && <PALab locale={locale} />}
        {view === "positions" && <PositionsTable data={positions.data ?? []} loading={positions.isLoading} error={positions.isError} locale={locale} />}
        {view === "alerts" && <AlertsTable data={alerts.data ?? []} loading={alerts.isLoading} error={alerts.isError} locale={locale} />}
        {view === "journal" && <JournalTable data={journal.data ?? []} loading={journal.isLoading} error={journal.isError} locale={locale} />}
        {view === "settings" && <SettingsPanel locale={locale} />}
      </div>
    </main>
  );
}

function AuthScreen({
  status,
  locale,
  action,
  secondaryAction,
  secondaryLabel
}: {
  status: string;
  locale: Locale;
  action?: () => Promise<void>;
  secondaryAction?: () => Promise<void>;
  secondaryLabel?: string;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#eef2f5] px-4">
      <section className="w-full max-w-sm rounded-md border border-line bg-white p-5">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-ink text-white">
            <BarChart3 size={22} />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-ink">EdgePilot</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
        </div>
        {action ? (
          <div className="grid gap-2">
            <button
              className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
              onClick={() => void action()}
              type="button"
            >
              <LogIn size={16} />
              {secondaryAction ? t(locale, "resendVerificationEmail") : t(locale, "signIn")}
            </button>
            {secondaryAction ? (
              <button
                className="focus-ring inline-flex w-full items-center justify-center rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:border-slate-400"
                onClick={() => void secondaryAction()}
                type="button"
              >
                {secondaryLabel}
              </button>
            ) : null}
          </div>
        ) : (
          <div className="h-2 rounded-md bg-panel" />
        )}
      </section>
    </main>
  );
}

function LanguageSwitcher({
  locale,
  setLocale
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}) {
  return (
    <div className="inline-flex rounded-md border border-line bg-panel p-1">
      {localeOptions.map((option) => (
        <button
          className={`focus-ring min-w-16 rounded px-2.5 py-1.5 text-xs font-medium ${
            locale === option.id ? "bg-ink text-white" : "text-slate-700 hover:bg-white"
          }`}
          key={option.id}
          onClick={() => setLocale(option.id)}
          type="button"
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function AuthButton() {
  const auth = useAuth();
  return (
    <button
      className="focus-ring inline-flex items-center gap-2 rounded-md border border-line bg-panel px-3 py-2 text-sm text-slate-700 hover:border-slate-400"
      onClick={() => auth.logout()}
      type="button"
    >
      <LogOut size={16} />
      {auth.userLabel}
    </button>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <div className="mb-3 flex items-center justify-between text-slate-500">
        {icon}
        <CircleDot size={14} />
      </div>
      <div className="text-2xl font-semibold text-ink">{value}</div>
      <div className="mt-1 text-sm text-slate-600">{label}</div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium text-ink">{formatValue(value)}</dd>
    </div>
  );
}

function TableShell({
  title,
  loading,
  error,
  locale = "en",
  children
}: {
  title: string;
  loading: boolean;
  error: boolean;
  locale?: Locale;
  children: ReactNode;
}) {
  return (
    <section className="rounded-md border border-line bg-white">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div className="flex items-center gap-2">
          <BookOpen size={18} className="text-teal" />
          <h2 className="text-base font-semibold text-ink">{title}</h2>
        </div>
        <DataState isLoading={loading} isError={error} locale={locale} />
      </div>
      <div className="overflow-x-auto">{children}</div>
    </section>
  );
}

function SettingsPanel({ locale }: { locale: Locale }) {
  const auth = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const sseUrl =
    process.env.NEXT_PUBLIC_SSE_URL ?? "http://localhost:8000/api/realtime/events/stream";
  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "EdgePilot";

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-md border border-line bg-white p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">{t(locale, "runtime")}</h2>
          <Settings size={18} className="text-teal" />
        </div>
        <dl className="grid gap-3">
          <Field label={t(locale, "app")} value={appName} />
          <Field label={t(locale, "apiBaseUrl")} value={apiBaseUrl} />
          <Field label={t(locale, "sseUrl")} value={sseUrl} />
          <Field label={t(locale, "auth")} value={t(locale, "authRequired")} />
          <Field label={t(locale, "user")} value={auth.userLabel} />
          <Field label={t(locale, "email")} value={auth.emailVerified ? t(locale, "emailVerified") : t(locale, "emailPending")} />
        </dl>
      </div>

      <div className="rounded-md border border-line bg-white p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">{t(locale, "connections")}</h2>
          <PlugZap size={18} className="text-teal" />
        </div>
        <div className="grid gap-3">
          <div className="flex items-center justify-between border-b border-line pb-3">
            <span className="text-sm font-medium text-ink">{t(locale, "backendApi")}</span>
            <StatusPill label={apiBaseUrl ? t(locale, "configured") : t(locale, "missing")} tone={apiBaseUrl ? "good" : "bad"} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-ink">{t(locale, "realtimeStream")}</span>
            <StatusPill label={sseUrl ? t(locale, "configured") : t(locale, "missing")} tone={sseUrl ? "good" : "bad"} />
          </div>
        </div>
      </div>
    </section>
  );
}

function CandidatesTable({
  data,
  loading,
  error,
  locale
}: {
  data: Candidate[];
  loading: boolean;
  error: boolean;
  locale: Locale;
}) {
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const activeCandidateId = selectedCandidateId ?? data[0]?.candidate_id ?? null;
  const detail = useQuery({
    queryKey: ["candidate-detail", activeCandidateId],
    queryFn: () => api.candidateDetail(activeCandidateId as string),
    enabled: Boolean(activeCandidateId)
  });

  useEffect(() => {
    if (selectedCandidateId && !data.some((row) => row.candidate_id === selectedCandidateId)) {
      setSelectedCandidateId(null);
    }
  }, [data, selectedCandidateId]);

  return (
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_440px]">
      <TableShell title={t(locale, "candidates")} loading={loading} error={error} locale={locale}>
        <table className="min-w-full table-fixed text-left text-sm">
          <thead className="bg-panel text-xs uppercase text-slate-500">
            <tr>
              <th className="w-24 px-4 py-3">{t(locale, "symbol")}</th>
              <th className="w-44 px-4 py-3">{t(locale, "setup")}</th>
              <th className="w-20 px-4 py-3">{t(locale, "grade")}</th>
              <th className="w-32 px-4 py-3">{t(locale, "validation")}</th>
              <th className="w-24 px-4 py-3">{t(locale, "score")}</th>
              <th className="w-28 px-4 py-3">{t(locale, "decision")}</th>
              <th className="w-32 px-4 py-3">{t(locale, "entry")}</th>
              <th className="w-32 px-4 py-3">{t(locale, "stop")}</th>
              <th className="w-32 px-4 py-3">{t(locale, "scanDate")}</th>
              <th className="w-20 px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {!data.length ? (
              <tr>
                <td className="px-4 py-6 text-sm text-slate-600" colSpan={10}>
                  {t(locale, "noCandidate")}
                </td>
              </tr>
            ) : null}
            {data.map((row) => (
              <tr
                key={row.candidate_id}
                className={`border-t border-line ${activeCandidateId === row.candidate_id ? "bg-teal-50/50" : ""}`}
              >
                <td className="px-4 py-3 font-medium text-ink">{row.symbol_id}</td>
                <td className="truncate px-4 py-3" title={row.setup_type ?? row.strategy_name}>
                  {row.setup_type ? labelFor(locale, "setup", row.setup_type) : row.strategy_name}
                </td>
                <td className="px-4 py-3">{formatValue(row.pa_setup_grade)}</td>
                <td className="px-4 py-3">
                  <StatusPill
                    label={labelFor(locale, "status", row.validation_status ?? "unlinked")}
                    tone={decisionTone(row.validation_status)}
                  />
                </td>
                <td className="px-4 py-3">{formatNumber(row.score_total, 1, locale)}</td>
                <td className="px-4 py-3">
                  <StatusPill label={labelFor(locale, "status", row.decision ?? "unknown")} tone={decisionTone(row.decision)} />
                </td>
                <td className="px-4 py-3">{formatNumber(row.entry_trigger, 2, locale)}</td>
                <td className="px-4 py-3">{formatNumber(row.initial_stop, 2, locale)}</td>
                <td className="px-4 py-3">{row.scan_date}</td>
                <td className="px-4 py-3">
                  <button
                    className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-slate-700 hover:border-slate-400"
                    onClick={() => setSelectedCandidateId(row.candidate_id)}
                    title={t(locale, "openDetail")}
                    type="button"
                  >
                    <Eye size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>

      <CandidateDetailPanel
        detail={detail.data}
        error={detail.isError}
        locale={locale}
        loading={detail.isLoading}
        onClose={() => setSelectedCandidateId(null)}
        selected={Boolean(activeCandidateId)}
      />
    </section>
  );
}

function CandidateDetailPanel({
  detail,
  loading,
  error,
  locale,
  selected,
  onClose
}: {
  detail: CandidateDetail | undefined;
  loading: boolean;
  error: boolean;
  locale: Locale;
  selected: boolean;
  onClose: () => void;
}) {
  const candidate = detail?.candidate;
  const setup = detail?.pa_setup;
  const entryPlan = detail?.entry_plan ?? setup?.entry_plan;
  const exitPlan = detail?.exit_plan ?? setup?.exit_plan;
  const scoreBreakdown = detail?.score_breakdown ?? nestedRecord(entryPlan, "score_breakdown");

  return (
    <aside className="min-w-0 rounded-md border border-line bg-white">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-ink">
            {candidate ? `${candidate.symbol_id} ${t(locale, "candidateDetail")}` : t(locale, "candidateDetail")}
          </h2>
          <p className="truncate text-xs text-slate-500">{setup?.setup_id ?? candidate?.candidate_id ?? t(locale, "noSelection")}</p>
        </div>
        <button
          className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-slate-700 hover:border-slate-400"
          disabled={!selected}
          onClick={onClose}
          title={t(locale, "closeDetail")}
          type="button"
        >
          <X size={16} />
        </button>
      </div>

      <div className="space-y-4 p-4">
        <DataState isLoading={loading} isError={error} locale={locale} />
        {!selected && <p className="text-sm text-slate-600">{t(locale, "noSelection")}</p>}
        {candidate ? (
          <>
            <ExplanationBlock locale={locale} setup={setup} candidate={candidate} />

            <div className="grid grid-cols-2 gap-3">
              <Field label={t(locale, "setup")} value={candidate.setup_type ? labelFor(locale, "setup", candidate.setup_type) : "-"} />
              <Field label={t(locale, "grade")} value={setup?.setup_grade} />
              <Field label={t(locale, "validation")} value={labelFor(locale, "status", setup?.validation_status)} />
              <Field label={t(locale, "status")} value={labelFor(locale, "status", setup?.status ?? candidate.decision)} />
              <Field label={t(locale, "quality")} value={formatNumber(setup?.pa_quality_score ?? candidate.score_total, 1, locale)} />
              <Field label={t(locale, "timeframe")} value={setup?.timeframe} />
            </div>

            <KeyLevelsBlock
              candidate={candidate}
              entryPlan={entryPlan}
              exitPlan={exitPlan}
              locale={locale}
              setup={setup}
            />
            <ScoreBreakdownBlock data={scoreBreakdown} locale={locale} />
            <PlanFields title={t(locale, "entryPlan")} data={entryPlan} locale={locale} omitKeys={["score_breakdown"]} />
            <PlanFields title={t(locale, "exitPlan")} data={exitPlan} locale={locale} />
            <PlanFields title={t(locale, "invalidation")} data={detail?.invalidation ?? setup?.invalidation} locale={locale} />
          </>
        ) : null}
      </div>
    </aside>
  );
}

function ExplanationBlock({
  locale,
  setup,
  candidate
}: {
  locale: Locale;
  setup: PASetup | null | undefined;
  candidate?: Candidate | null;
}) {
  return (
    <section className="rounded-md border border-teal-200 bg-teal-50/60 p-3">
      <h3 className="mb-2 text-sm font-semibold text-ink">{t(locale, "plainExplanation")}</h3>
      <p className="text-sm leading-6 text-slate-700">{setupNarrative(locale, setup, candidate)}</p>
    </section>
  );
}

function KeyLevelsBlock({
  candidate,
  setup,
  entryPlan,
  exitPlan,
  locale
}: {
  candidate?: Candidate | null;
  setup?: PASetup | null;
  entryPlan: Record<string, unknown> | null | undefined;
  exitPlan: Record<string, unknown> | null | undefined;
  locale: Locale;
}) {
  const trigger = numberFromRecord(entryPlan, "trigger_price") ?? candidate?.entry_trigger ?? null;
  const stop = numberFromRecord(exitPlan, "initial_stop") ?? candidate?.initial_stop ?? null;
  const triggerType = stringFromRecord(entryPlan, "trigger_type");

  return (
    <section className="border-t border-line pt-3">
      <h3 className="mb-2 text-sm font-semibold text-ink">{t(locale, "keyLevels")}</h3>
      <dl className="grid grid-cols-2 gap-3">
        <Field label={t(locale, "entry")} value={formatNumber(trigger, 2, locale)} />
        <Field label={t(locale, "stop")} value={formatNumber(stop, 2, locale)} />
        <Field label={labelFor(locale, "plan", "trigger_type")} value={labelFor(locale, "plan", triggerType)} />
        <Field label={t(locale, "validation")} value={labelFor(locale, "status", setup?.validation_status)} />
      </dl>
    </section>
  );
}

function ScoreBreakdownBlock({
  data,
  locale
}: {
  data: Record<string, unknown> | null | undefined;
  locale: Locale;
}) {
  const order = ["total", "trend", "relative_strength", "volume_liquidity", "base_setup", "market_context", "fundamental_lite"];
  const entries = Object.entries(data ?? {})
    .filter(([, value]) => typeof value === "number")
    .sort(([left], [right]) => {
      const leftIndex = order.indexOf(left);
      const rightIndex = order.indexOf(right);
      return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
    });

  return (
    <section className="border-t border-line pt-3">
      <h3 className="mb-3 text-sm font-semibold text-ink">{t(locale, "scoreBreakdown")}</h3>
      {entries.length ? (
        <div className="grid gap-3">
          {entries.map(([key, value]) => {
            const meta = scoreMeta(locale, key);
            const score = typeof value === "number" ? value : null;
            return (
              <div key={key} className="grid grid-cols-[minmax(0,1fr)_3.5rem] gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-medium text-ink">{meta.label}</div>
                  {meta.description ? <div className="mt-0.5 text-xs leading-5 text-slate-500">{meta.description}</div> : null}
                  <div className="mt-2 h-1.5 overflow-hidden rounded bg-slate-100">
                    <div
                      className="h-full rounded bg-teal"
                      style={{ width: `${Math.max(0, Math.min(100, score ?? 0))}%` }}
                    />
                  </div>
                </div>
                <div className="text-right text-sm font-semibold text-ink">{formatNumber(score, 1, locale)}</div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-slate-500">-</p>
      )}
    </section>
  );
}

function PlanFields({
  title,
  data,
  locale,
  omitKeys = []
}: {
  title: string;
  data: Record<string, unknown> | null | undefined;
  locale: Locale;
  omitKeys?: string[];
}) {
  const entries = Object.entries(data ?? {});
  return (
    <section className="border-t border-line pt-3">
      <h3 className="mb-2 text-sm font-semibold text-ink">{title}</h3>
      {entries.filter(([key]) => !omitKeys.includes(key)).length ? (
        <dl className="grid gap-2">
          {entries.filter(([key]) => !omitKeys.includes(key)).map(([key, value]) => (
            <div key={key} className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] gap-3 text-sm">
              <dt className="min-w-0 break-words text-slate-500">{labelFor(locale, "plan", key)}</dt>
              <dd className="min-w-0 break-words font-medium text-ink">{formatDetailValue(value, locale)}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-sm text-slate-500">-</p>
      )}
    </section>
  );
}

function PALab({ locale }: { locale: Locale }) {
  const [symbol, setSymbol] = useState("");
  const [setupType, setSetupType] = useState("");
  const [validationStatus, setValidationStatus] = useState("");
  const [selectedSetupId, setSelectedSetupId] = useState<string | null>(null);
  const filters = {
    symbol: symbol.trim().toUpperCase() || undefined,
    setupType: setupType || undefined,
    validationStatus: validationStatus || undefined,
    limit: 200
  };
  const setups = useQuery({
    queryKey: ["pa-setups", filters],
    queryFn: () => api.paSetups(filters)
  });
  const selectedSetup =
    setups.data?.find((setup) => setup.setup_id === selectedSetupId) ?? setups.data?.[0] ?? null;

  return (
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_440px]">
      <section className="rounded-md border border-line bg-white">
        <div className="border-b border-line px-4 py-3">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-teal" />
              <h2 className="text-base font-semibold text-ink">{t(locale, "setupExplorer")}</h2>
            </div>
            <DataState isLoading={setups.isLoading} isError={setups.isError} locale={locale} />
          </div>
          <div className="grid gap-2 md:grid-cols-[minmax(120px,180px)_minmax(160px,220px)_minmax(160px,220px)]">
            <input
              className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
              onChange={(event) => setSymbol(event.target.value)}
              placeholder={t(locale, "symbol")}
              value={symbol}
            />
            <select
              className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
              onChange={(event) => setSetupType(event.target.value)}
              value={setupType}
            >
              <option value="">{t(locale, "allSetups")}</option>
              <option value="breakout">{labelFor(locale, "setup", "breakout")}</option>
              <option value="pullback_to_20ma">{labelFor(locale, "setup", "pullback_to_20ma")}</option>
              <option value="failed_breakdown_reclaim">{labelFor(locale, "setup", "failed_breakdown_reclaim")}</option>
              <option value="oneil_leader_watch">{labelFor(locale, "setup", "oneil_leader_watch")}</option>
            </select>
            <select
              className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
              onChange={(event) => setValidationStatus(event.target.value)}
              value={validationStatus}
            >
              <option value="">{t(locale, "allValidation")}</option>
              <option value="shadow_only">{labelFor(locale, "status", "shadow_only")}</option>
              <option value="paper_allowed">{labelFor(locale, "status", "paper_allowed")}</option>
              <option value="live_allowed">{labelFor(locale, "status", "live_allowed")}</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full table-fixed text-left text-sm">
            <thead className="bg-panel text-xs uppercase text-slate-500">
              <tr>
                <th className="w-24 px-4 py-3">{t(locale, "symbol")}</th>
                <th className="w-48 px-4 py-3">{t(locale, "setup")}</th>
                <th className="w-20 px-4 py-3">{t(locale, "grade")}</th>
                <th className="w-24 px-4 py-3">{t(locale, "score")}</th>
                <th className="w-32 px-4 py-3">{t(locale, "validation")}</th>
                <th className="w-28 px-4 py-3">{t(locale, "status")}</th>
                <th className="w-40 px-4 py-3">{t(locale, "detected")}</th>
                <th className="w-20 px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {!(setups.data ?? []).length ? (
                <tr>
                  <td className="px-4 py-6 text-sm text-slate-600" colSpan={8}>
                    {t(locale, "noSetup")}
                  </td>
                </tr>
              ) : null}
              {(setups.data ?? []).map((setup) => (
                <tr
                  key={setup.setup_id}
                  className={`border-t border-line ${selectedSetup?.setup_id === setup.setup_id ? "bg-teal-50/50" : ""}`}
                >
                  <td className="px-4 py-3 font-medium text-ink">{setup.symbol_id}</td>
                  <td className="truncate px-4 py-3" title={setup.setup_type}>
                    {labelFor(locale, "setup", setup.setup_type)}
                  </td>
                  <td className="px-4 py-3">{formatValue(setup.setup_grade)}</td>
                  <td className="px-4 py-3">{formatNumber(setup.pa_quality_score, 1, locale)}</td>
                  <td className="px-4 py-3">
                    <StatusPill
                      label={labelFor(locale, "status", setup.validation_status ?? "unknown")}
                      tone={decisionTone(setup.validation_status)}
                    />
                  </td>
                  <td className="px-4 py-3">{labelFor(locale, "status", setup.status)}</td>
                  <td className="px-4 py-3">{formatDate(setup.detected_ts, locale)}</td>
                  <td className="px-4 py-3">
                    <button
                      className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-slate-700 hover:border-slate-400"
                      onClick={() => setSelectedSetupId(setup.setup_id)}
                      title={t(locale, "openDetail")}
                      type="button"
                    >
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <PASetupDetailPanel locale={locale} setup={selectedSetup} />
    </section>
  );
}

function PASetupDetailPanel({ setup, locale }: { setup: PASetup | null; locale: Locale }) {
  const scoreBreakdown = nestedRecord(setup?.entry_plan, "score_breakdown");
  return (
    <aside className="min-w-0 rounded-md border border-line bg-white">
      <div className="border-b border-line px-4 py-3">
        <h2 className="text-base font-semibold text-ink">
          {setup ? `${setup.symbol_id} ${t(locale, "setupDetail")}` : t(locale, "setupDetail")}
        </h2>
        <p className="truncate text-xs text-slate-500">{setup?.setup_id ?? t(locale, "noSelection")}</p>
      </div>
      <div className="space-y-4 p-4">
        {setup ? (
          <>
            <ExplanationBlock locale={locale} setup={setup} />
            <div className="grid grid-cols-2 gap-3">
              <Field label={t(locale, "setup")} value={labelFor(locale, "setup", setup.setup_type)} />
              <Field label={t(locale, "grade")} value={setup.setup_grade} />
              <Field label={t(locale, "quality")} value={formatNumber(setup.pa_quality_score, 1, locale)} />
              <Field label={t(locale, "timeframe")} value={setup.timeframe} />
              <Field label={t(locale, "validation")} value={labelFor(locale, "status", setup.validation_status)} />
              <Field label={t(locale, "status")} value={labelFor(locale, "status", setup.status)} />
            </div>
            <div className="grid grid-cols-2 gap-3 border-t border-line pt-3">
              <Field label={t(locale, "structure")} value={formatNumber(setup.structure_score, 1, locale)} />
              <Field label={t(locale, "location")} value={formatNumber(setup.location_score, 1, locale)} />
              <Field label={t(locale, "volume")} value={formatNumber(setup.volume_score, 1, locale)} />
              <Field label={t(locale, "trendRs")} value={formatNumber(setup.trend_rs_score, 1, locale)} />
              <Field label={t(locale, "context")} value={formatNumber(setup.context_score, 1, locale)} />
              <Field label={t(locale, "riskStop")} value={formatNumber(setup.risk_stop_score, 1, locale)} />
            </div>
            <KeyLevelsBlock entryPlan={setup.entry_plan} exitPlan={setup.exit_plan} locale={locale} setup={setup} />
            <ScoreBreakdownBlock data={scoreBreakdown} locale={locale} />
            <PlanFields title={t(locale, "entryPlan")} data={setup.entry_plan} locale={locale} omitKeys={["score_breakdown"]} />
            <PlanFields title={t(locale, "exitPlan")} data={setup.exit_plan} locale={locale} />
            <PlanFields title={t(locale, "invalidation")} data={setup.invalidation} locale={locale} />
          </>
        ) : (
          <p className="text-sm text-slate-600">{t(locale, "noSetup")}</p>
        )}
      </div>
    </aside>
  );
}

function nestedRecord(
  data: Record<string, unknown> | null | undefined,
  key: string
): Record<string, unknown> | null {
  const value = data?.[key];
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

function numberFromRecord(data: Record<string, unknown> | null | undefined, key: string) {
  const value = data?.[key];
  return typeof value === "number" ? value : null;
}

function stringFromRecord(data: Record<string, unknown> | null | undefined, key: string) {
  const value = data?.[key];
  return typeof value === "string" ? value : null;
}

function formatDetailValue(value: unknown, locale: Locale): string {
  if (typeof value === "number") {
    return formatNumber(value, 3, locale);
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (Array.isArray(value)) {
    return value.map((item) => formatDetailValue(item, locale)).join(", ");
  }
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .filter(([, nestedValue]) => nestedValue !== null && nestedValue !== undefined && nestedValue !== "")
      .map(([nestedKey, nestedValue]) => `${labelFor(locale, "plan", nestedKey)}: ${formatDetailValue(nestedValue, locale)}`)
      .join(" / ");
  }
  const raw = String(value);
  const planLabel = labelFor(locale, "plan", raw);
  if (planLabel !== raw) {
    return planLabel;
  }
  return labelFor(locale, "status", raw);
}

function PositionsTable({
  data,
  loading,
  error,
  locale
}: {
  data: Position[];
  loading: boolean;
  error: boolean;
  locale: Locale;
}) {
  return (
    <TableShell title={t(locale, "positions")} loading={loading} error={error} locale={locale}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t(locale, "symbol")}</th>
            <th className="px-4 py-3">{t(locale, "type")}</th>
            <th className="px-4 py-3">{t(locale, "qty")}</th>
            <th className="px-4 py-3">{t(locale, "entry")}</th>
            <th className="px-4 py-3">{t(locale, "stop")}</th>
            <th className="px-4 py-3">{t(locale, "status")}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.position_id} className="border-t border-line">
              <td className="px-4 py-3 font-medium text-ink">{row.symbol_id}</td>
              <td className="px-4 py-3">{row.asset_type}</td>
              <td className="px-4 py-3">{formatValue(row.quantity)}</td>
              <td className="px-4 py-3">{formatValue(row.entry_price)}</td>
              <td className="px-4 py-3">{formatValue(row.current_stop)}</td>
              <td className="px-4 py-3">{formatValue(row.status)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableShell>
  );
}

function AlertsTable({
  data,
  loading,
  error,
  locale
}: {
  data: ExitAlert[];
  loading: boolean;
  error: boolean;
  locale: Locale;
}) {
  return (
    <TableShell title={t(locale, "alerts")} loading={loading} error={error} locale={locale}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t(locale, "level")}</th>
            <th className="px-4 py-3">{t(locale, "action")}</th>
            <th className="px-4 py-3">{t(locale, "reason")}</th>
            <th className="px-4 py-3">{t(locale, "newStop")}</th>
            <th className="px-4 py-3">{t(locale, "time")}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.alert_id} className="border-t border-line">
              <td className="px-4 py-3">{formatValue(row.level)}</td>
              <td className="px-4 py-3">{formatValue(row.action)}</td>
              <td className="px-4 py-3">{formatValue(row.reason)}</td>
              <td className="px-4 py-3">{formatValue(row.new_stop)}</td>
              <td className="px-4 py-3">{formatDate(row.alert_ts, locale)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableShell>
  );
}

function JournalTable({
  data,
  loading,
  error,
  locale
}: {
  data: JournalTrade[];
  loading: boolean;
  error: boolean;
  locale: Locale;
}) {
  return (
    <TableShell title={t(locale, "journal")} loading={loading} error={error} locale={locale}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t(locale, "symbol")}</th>
            <th className="px-4 py-3">{t(locale, "entry")}</th>
            <th className="px-4 py-3">{t(locale, "exit")}</th>
            <th className="px-4 py-3">{t(locale, "netPnl")}</th>
            <th className="px-4 py-3">{t(locale, "rMultiple")}</th>
            <th className="px-4 py-3">{t(locale, "exitReason")}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.trade_id} className="border-t border-line">
              <td className="px-4 py-3 font-medium text-ink">{formatValue(row.symbol_id)}</td>
              <td className="px-4 py-3">{formatDate(row.entry_ts, locale)}</td>
              <td className="px-4 py-3">{formatDate(row.exit_ts, locale)}</td>
              <td className="px-4 py-3">{formatValue(row.net_pnl)}</td>
              <td className="px-4 py-3">{formatValue(row.r_multiple)}</td>
              <td className="px-4 py-3">{formatValue(row.exit_reason)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableShell>
  );
}
