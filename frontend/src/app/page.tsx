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
  ListChecks,
  LogIn,
  LogOut,
  PlugZap,
  RefreshCcw,
  Settings,
  ShieldCheck,
  UserCircle
} from "lucide-react";
import type { ReactNode } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Candidate, ExitAlert, JournalTrade, Position } from "@/lib/api";
import { useWorkspaceStore } from "@/lib/store";
import type { WorkspaceView } from "@/lib/store";

const views: Array<{ id: WorkspaceView; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "candidates", label: "Candidates" },
  { id: "positions", label: "Positions" },
  { id: "alerts", label: "Exit Alerts" },
  { id: "journal", label: "Journal" },
  { id: "settings", label: "Settings" }
];

function formatValue(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("en", {
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

function DataState({ isLoading, isError }: { isLoading: boolean; isError: boolean }) {
  if (isLoading) {
    return <span className="text-sm text-slate-500">Loading data...</span>;
  }
  if (isError) {
    return <span className="text-sm text-rose-700">API unavailable</span>;
  }
  return null;
}

export default function Home() {
  const auth = useAuth();
  const { view, setView } = useWorkspaceStore();
  const queriesEnabled = auth.ready && auth.isAuthenticated;
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

  if (auth.enabled && !auth.ready) {
    return <AuthScreen status="Checking session..." />;
  }

  if (auth.enabled && !auth.isAuthenticated) {
    return <AuthScreen action={auth.login} status="Sign in required" />;
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
                <p className="text-sm text-slate-600">Trading operations workspace</p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill label={summary?.risk_mode ?? "unknown"} tone={riskTone} />
            <AuthButton />
            <div className="inline-flex items-center gap-2 rounded-md border border-line bg-panel px-3 py-2 text-sm text-slate-700">
              <RefreshCcw size={16} />
              30s refresh
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
              {item.label}
            </button>
          ))}
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <DataState isLoading={dashboard.isLoading} isError={dashboard.isError} />

        {view === "overview" && (
          <div className="space-y-6">
            <section className="grid gap-3 md:grid-cols-4">
              <Metric icon={<ListChecks size={18} />} label="Candidates" value={summary?.candidate_count ?? 0} />
              <Metric icon={<BriefcaseBusiness size={18} />} label="Open Positions" value={summary?.open_position_count ?? 0} />
              <Metric icon={<AlertTriangle size={18} />} label="Open Alerts" value={summary?.exit_alert_count ?? 0} />
              <Metric icon={<ShieldCheck size={18} />} label="Highest Level" value={summary?.highest_exit_level ?? "-"} />
            </section>

            <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-md border border-line bg-white p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-base font-semibold text-ink">Market Context</h2>
                  <Activity size={18} className="text-teal" />
                </div>
                <dl className="grid gap-3 sm:grid-cols-2">
                  <Field label="Risk" value={summary?.market_context.risk_level} />
                  <Field label="US Bias" value={summary?.market_context.us_bias} />
                  <Field label="Japan Bias" value={summary?.market_context.japan_bias} />
                  <Field label="Updated" value={formatDate(summary?.market_context.snapshot_ts)} />
                </dl>
                <p className="mt-4 text-sm text-slate-600">{summary?.market_context.notes ?? "No market notes yet."}</p>
              </div>

              <div className="rounded-md border border-line bg-white p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-base font-semibold text-ink">Data Freshness</h2>
                  <Database size={18} className="text-teal" />
                </div>
                <div className="space-y-3">
                  {summary?.data_freshness.length ? (
                    summary.data_freshness.map((item) => (
                      <div key={item.dataset_key} className="flex items-center justify-between gap-3 border-b border-line pb-2 last:border-0 last:pb-0">
                        <div>
                          <div className="text-sm font-medium text-ink">{item.dataset_key}</div>
                          <div className="text-xs text-slate-500">{item.source ?? "unknown"}</div>
                        </div>
                        <div className="text-right text-xs text-slate-600">{formatDate(item.last_updated_at)}</div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-600">No freshness records yet.</p>
                  )}
                </div>
              </div>
            </section>
          </div>
        )}

        {view === "candidates" && <CandidatesTable data={candidates.data ?? []} loading={candidates.isLoading} error={candidates.isError} />}
        {view === "positions" && <PositionsTable data={positions.data ?? []} loading={positions.isLoading} error={positions.isError} />}
        {view === "alerts" && <AlertsTable data={alerts.data ?? []} loading={alerts.isLoading} error={alerts.isError} />}
        {view === "journal" && <JournalTable data={journal.data ?? []} loading={journal.isLoading} error={journal.isError} />}
        {view === "settings" && <SettingsPanel />}
      </div>
    </main>
  );
}

function AuthScreen({ status, action }: { status: string; action?: () => Promise<void> }) {
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
          <button
            className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
            onClick={() => void action()}
            type="button"
          >
            <LogIn size={16} />
            Sign in
          </button>
        ) : (
          <div className="h-2 rounded-md bg-panel" />
        )}
      </section>
    </main>
  );
}

function AuthButton() {
  const auth = useAuth();
  if (!auth.enabled) {
    return (
      <div className="inline-flex items-center gap-2 rounded-md border border-line bg-panel px-3 py-2 text-sm text-slate-700">
        <UserCircle size={16} />
        Local Dev
      </div>
    );
  }
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
    <div>
      <dt className="text-xs uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-ink">{formatValue(value)}</dd>
    </div>
  );
}

function TableShell({
  title,
  loading,
  error,
  children
}: {
  title: string;
  loading: boolean;
  error: boolean;
  children: ReactNode;
}) {
  return (
    <section className="rounded-md border border-line bg-white">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div className="flex items-center gap-2">
          <BookOpen size={18} className="text-teal" />
          <h2 className="text-base font-semibold text-ink">{title}</h2>
        </div>
        <DataState isLoading={loading} isError={error} />
      </div>
      <div className="overflow-x-auto">{children}</div>
    </section>
  );
}

function SettingsPanel() {
  const auth = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const sseUrl =
    process.env.NEXT_PUBLIC_SSE_URL ?? "http://localhost:8000/api/realtime/events/stream";
  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "EdgePilot";

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-md border border-line bg-white p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">Runtime</h2>
          <Settings size={18} className="text-teal" />
        </div>
        <dl className="grid gap-3">
          <Field label="App" value={appName} />
          <Field label="API Base URL" value={apiBaseUrl} />
          <Field label="SSE URL" value={sseUrl} />
          <Field label="Auth" value={auth.enabled ? "enabled" : "local dev"} />
          <Field label="User" value={auth.userLabel} />
        </dl>
      </div>

      <div className="rounded-md border border-line bg-white p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">Connections</h2>
          <PlugZap size={18} className="text-teal" />
        </div>
        <div className="grid gap-3">
          <div className="flex items-center justify-between border-b border-line pb-3">
            <span className="text-sm font-medium text-ink">Backend API</span>
            <StatusPill label={apiBaseUrl ? "configured" : "missing"} tone={apiBaseUrl ? "good" : "bad"} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-ink">Realtime Stream</span>
            <StatusPill label={sseUrl ? "configured" : "missing"} tone={sseUrl ? "good" : "bad"} />
          </div>
        </div>
      </div>
    </section>
  );
}

function CandidatesTable({ data, loading, error }: { data: Candidate[]; loading: boolean; error: boolean }) {
  return (
    <TableShell title="Candidates" loading={loading} error={error}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Symbol</th>
            <th className="px-4 py-3">Strategy</th>
            <th className="px-4 py-3">Score</th>
            <th className="px-4 py-3">Decision</th>
            <th className="px-4 py-3">Scan Date</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.candidate_id} className="border-t border-line">
              <td className="px-4 py-3 font-medium text-ink">{row.symbol_id}</td>
              <td className="px-4 py-3">{row.strategy_name}</td>
              <td className="px-4 py-3">{formatValue(row.score_total)}</td>
              <td className="px-4 py-3">{formatValue(row.decision)}</td>
              <td className="px-4 py-3">{row.scan_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableShell>
  );
}

function PositionsTable({ data, loading, error }: { data: Position[]; loading: boolean; error: boolean }) {
  return (
    <TableShell title="Positions" loading={loading} error={error}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Symbol</th>
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Qty</th>
            <th className="px-4 py-3">Entry</th>
            <th className="px-4 py-3">Stop</th>
            <th className="px-4 py-3">Status</th>
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

function AlertsTable({ data, loading, error }: { data: ExitAlert[]; loading: boolean; error: boolean }) {
  return (
    <TableShell title="Exit Alerts" loading={loading} error={error}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Level</th>
            <th className="px-4 py-3">Action</th>
            <th className="px-4 py-3">Reason</th>
            <th className="px-4 py-3">New Stop</th>
            <th className="px-4 py-3">Time</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.alert_id} className="border-t border-line">
              <td className="px-4 py-3">{formatValue(row.level)}</td>
              <td className="px-4 py-3">{formatValue(row.action)}</td>
              <td className="px-4 py-3">{formatValue(row.reason)}</td>
              <td className="px-4 py-3">{formatValue(row.new_stop)}</td>
              <td className="px-4 py-3">{formatDate(row.alert_ts)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableShell>
  );
}

function JournalTable({ data, loading, error }: { data: JournalTrade[]; loading: boolean; error: boolean }) {
  return (
    <TableShell title="Journal" loading={loading} error={error}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Symbol</th>
            <th className="px-4 py-3">Entry</th>
            <th className="px-4 py-3">Exit</th>
            <th className="px-4 py-3">Net PnL</th>
            <th className="px-4 py-3">R</th>
            <th className="px-4 py-3">Exit Reason</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.trade_id} className="border-t border-line">
              <td className="px-4 py-3 font-medium text-ink">{formatValue(row.symbol_id)}</td>
              <td className="px-4 py-3">{formatDate(row.entry_ts)}</td>
              <td className="px-4 py-3">{formatDate(row.exit_ts)}</td>
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
