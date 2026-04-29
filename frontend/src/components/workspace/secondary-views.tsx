"use client";

import { PlugZap, Settings } from "lucide-react";

import { Field, StatusPill, TableShell } from "@/components/workspace/common";
import type { ExitAlert, JournalTrade, Position } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDate, formatValue } from "@/lib/format";
import { t, type Locale } from "@/lib/i18n";

export function SettingsPanel({ locale }: { locale: Locale }) {
  const auth = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const sseUrl =
    process.env.NEXT_PUBLIC_SSE_URL ?? "http://localhost:8000/api/realtime/events/stream";
  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "EdgePilot";

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
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

      <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
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

export function PositionsTable({
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

export function AlertsTable({
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

export function JournalTable({
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
