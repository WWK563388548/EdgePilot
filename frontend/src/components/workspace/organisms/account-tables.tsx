"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Clock3, RefreshCw } from "lucide-react";
import { useState } from "react";

import { DataState } from "@/components/workspace/atoms/data-state";
import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import { PositionLifecycleRow } from "@/components/workspace/organisms/position-lifecycle-row";
import { TableShell } from "@/components/workspace/molecules/table-shell";
import type { ExitAlert, JournalTrade, Position, PositionStatus } from "@/lib/api";
import { api } from "@/lib/api";
import { formatDate, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

type PaginatedTableProps<T> = {
  data: T[];
  loading: boolean;
  error: boolean;
  page: number;
  pageSize: number;
  totalCount?: number;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
  locale: Locale;
};

export function PositionsTable({
  data,
  loading,
  error,
  page,
  pageSize,
  totalCount,
  hasNextPage,
  onPageChange,
  onStatusFilterChange,
  statusFilter,
  locale
}: PaginatedTableProps<Position> & {
  onStatusFilterChange: (filter: PositionStatus | "all") => void;
  statusFilter: PositionStatus | "all";
}) {
  const { labelFor, t } = useAppI18n();
  const filters: Array<PositionStatus | "all"> = [
    "all",
    "planned",
    "open",
    "reduce",
    "exit_pending",
    "review_needed",
    "closed",
    "cancelled"
  ];

  return (
    <TableShell title={t("positions")} loading={loading} error={error} locale={locale}>
      <div className="border-b border-line bg-white px-4 py-4">
        <div className="mb-3 text-sm font-semibold text-ink">{t("positionLifecycleTitle")}</div>
        <div className="grid gap-2 md:grid-cols-4">
          <LifecycleStep label={t("positionLifecyclePlanned")} value={labelFor("status", "planned")} />
          <LifecycleStep label={t("positionLifecycleOpen")} value={labelFor("status", "open")} />
          <LifecycleStep label={t("positionLifecycleReduced")} value={labelFor("status", "reduce")} />
          <LifecycleStep label={t("positionLifecycleClosed")} value={labelFor("status", "closed")} />
        </div>
      </div>
      <div className="flex flex-wrap gap-2 border-b border-line bg-white px-4 py-3">
        {filters.map((filter) => {
          const selected = statusFilter === filter;
          return (
            <button
              className={`focus-ring h-8 rounded-md px-3 text-xs font-semibold transition-colors ${
                selected
                  ? "bg-ink text-white"
                  : "border border-line bg-panel text-slate-700 hover:border-teal hover:text-teal"
              }`}
              key={filter}
              onClick={() => onStatusFilterChange(filter)}
              type="button"
            >
              {filter === "all" ? t("allPositions") : labelFor("status", filter)}
            </button>
          );
        })}
      </div>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("symbol")}</th>
            <th className="px-4 py-3">{t("type")}</th>
            <th className="px-4 py-3">{t("qty")}</th>
            <th className="px-4 py-3">{t("entry")}</th>
            <th className="px-4 py-3">{t("stop")}</th>
            <th className="px-4 py-3">{t("riskAmount")}</th>
            <th className="px-4 py-3">{t("riskPercent")}</th>
            <th className="px-4 py-3">{t("status")}</th>
            <th className="px-4 py-3">{t("action")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <EmptyTableRow
              colSpan={9}
              error={error}
              loading={loading}
              locale={locale}
              message={t("noPositions")}
            />
          ) : null}
          {data.map((row) => (
            <PositionLifecycleRow key={row.position_id} locale={locale} position={row} />
          ))}
        </tbody>
      </table>
      <PaginationControls
        hasNext={hasNextPage}
        itemCount={data.length}
        onPageChange={onPageChange}
        page={page}
        pageSize={pageSize}
        totalCount={totalCount}
      />
    </TableShell>
  );
}

export function AlertsTable({
  data,
  loading,
  error,
  page,
  pageSize,
  totalCount,
  hasNextPage,
  onPageChange,
  locale
}: PaginatedTableProps<ExitAlert>) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const [evaluationResult, setEvaluationResult] = useState<string | null>(null);
  const highPriorityAlert = data.find((row) => (row.level ?? 0) >= 3);
  const updateAlert = useMutation({
    mutationFn: ({ alertId, snoozedUntil }: { alertId: string; snoozedUntil?: string }) =>
      api.updateAlert(
        alertId,
        snoozedUntil
          ? {
              snoozed_until: snoozedUntil
            }
          : {
              acknowledged: true
            }
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["alerts"] }),
        queryClient.invalidateQueries({ queryKey: ["alerts-count"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      ]);
    }
  });
  const evaluateAlerts = useMutation({
    mutationFn: () => api.evaluateExitAlerts(),
    onSuccess: async (response) => {
      setEvaluationResult(
        response.alerts_created === 0 && response.duplicate_alerts === 0
          ? t("exitAlertEvaluationNoTriggers", {
              positions: response.positions_evaluated,
              skipped: response.skipped_positions
            })
          : t("exitAlertEvaluationResult", {
              alerts: response.alerts_created,
              duplicates: response.duplicate_alerts,
              positions: response.positions_evaluated,
              skipped: response.skipped_positions
            })
      );
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["alerts"] }),
        queryClient.invalidateQueries({ queryKey: ["alerts-count"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["portfolio-risk"] }),
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] })
      ]);
    },
    onError: () => {
      setEvaluationResult(null);
    }
  });

  return (
    <TableShell
      title={t("alerts")}
      loading={loading || evaluateAlerts.isPending}
      error={error || evaluateAlerts.isError}
      locale={locale}
      actions={
        <button
          className="focus-ring inline-flex h-9 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60"
          disabled={evaluateAlerts.isPending}
          onClick={() => evaluateAlerts.mutate()}
          title={t("exitAlertEvaluationHelp")}
          type="button"
        >
          <RefreshCw size={16} className={evaluateAlerts.isPending ? "animate-spin" : ""} />
          {evaluateAlerts.isPending ? t("evaluatingExitAlerts") : t("evaluateExitAlerts")}
        </button>
      }
    >
      {highPriorityAlert ? (
        <div className="border-b border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          <span className="font-semibold">{t("highPriorityExitAlert")}</span>{" "}
          {labelFor("plan", highPriorityAlert.reason)}
        </div>
      ) : null}
      {evaluationResult || evaluateAlerts.isError ? (
        <div
          className={`border-b border-line px-4 py-3 text-sm ${
            evaluateAlerts.isError ? "bg-rose-50 text-rose-700" : "bg-teal-50 text-teal-800"
          }`}
        >
          {evaluateAlerts.isError ? t("exitAlertEvaluationFailed") : evaluationResult}
        </div>
      ) : null}
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("level")}</th>
            <th className="px-4 py-3">{t("manage")}</th>
            <th className="px-4 py-3">{t("reason")}</th>
            <th className="px-4 py-3">{t("rule")}</th>
            <th className="px-4 py-3">{t("newStop")}</th>
            <th className="px-4 py-3">{t("time")}</th>
            <th className="px-4 py-3">{t("action")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <EmptyTableRow
              colSpan={7}
              error={error}
              loading={loading}
              locale={locale}
              message={t("noAlerts")}
            />
          ) : null}
          {data.map((row) => (
            <tr key={row.alert_id} className="border-t border-line">
              <td className="px-4 py-3">{formatValue(row.level)}</td>
              <td className="px-4 py-3">{labelFor("plan", row.action)}</td>
              <td className="px-4 py-3">{labelFor("plan", row.reason)}</td>
              <td className="px-4 py-3">{labelFor("plan", row.triggered_rules)}</td>
              <td className="px-4 py-3">{formatValue(row.new_stop)}</td>
              <td className="px-4 py-3">{formatDate(row.alert_ts, locale)}</td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-2">
                  <button
                    className="focus-ring inline-flex h-8 items-center gap-1 rounded-md border border-line bg-white px-2 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:opacity-60"
                    disabled={updateAlert.isPending}
                    onClick={() => updateAlert.mutate({ alertId: row.alert_id })}
                    title={t("ackExitAlertHelp")}
                    type="button"
                  >
                    <Check size={14} />
                    {t("ackExitAlert")}
                  </button>
                  <button
                    className="focus-ring inline-flex h-8 items-center gap-1 rounded-md border border-line bg-white px-2 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:opacity-60"
                    disabled={updateAlert.isPending}
                    onClick={() =>
                      updateAlert.mutate({
                        alertId: row.alert_id,
                        snoozedUntil: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
                      })
                    }
                    title={t("snoozeExitAlertHelp")}
                    type="button"
                  >
                    <Clock3 size={14} />
                    {t("snoozeExitAlert")}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <PaginationControls
        hasNext={hasNextPage}
        itemCount={data.length}
        onPageChange={onPageChange}
        page={page}
        pageSize={pageSize}
        totalCount={totalCount}
      />
    </TableShell>
  );
}

export function JournalTable({
  data,
  loading,
  error,
  page,
  pageSize,
  totalCount,
  hasNextPage,
  onPageChange,
  locale
}: PaginatedTableProps<JournalTrade>) {
  const { t } = useAppI18n();

  return (
    <TableShell title={t("journal")} loading={loading} error={error} locale={locale}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("symbol")}</th>
            <th className="px-4 py-3">{t("journalAction")}</th>
            <th className="px-4 py-3">{t("qty")}</th>
            <th className="px-4 py-3">{t("entry")}</th>
            <th className="px-4 py-3">{t("exit")}</th>
            <th className="px-4 py-3">{t("netPnl")}</th>
            <th className="px-4 py-3">{t("rMultiple")}</th>
            <th className="px-4 py-3">{t("notes")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <EmptyTableRow
              colSpan={8}
              error={error}
              loading={loading}
              locale={locale}
              message={t("noJournal")}
            />
          ) : null}
          {data.map((row) => (
            <tr key={row.trade_id} className="border-t border-line">
              <td className="px-4 py-3 font-medium text-ink">{formatValue(row.symbol_id)}</td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex rounded-md px-2 py-1 text-xs font-semibold ${
                    row.exit_reason === "trim"
                      ? "bg-teal-50 text-teal-800 ring-1 ring-teal-200"
                      : "bg-slate-100 text-slate-700 ring-1 ring-slate-200"
                  }`}
                >
                  {journalActionLabel(row.exit_reason, t)}
                </span>
              </td>
              <td className="px-4 py-3">{formatValue(row.quantity)}</td>
              <td className="px-4 py-3">{formatDate(row.entry_ts, locale)}</td>
              <td className="px-4 py-3">{formatDate(row.exit_ts, locale)}</td>
              <td className="px-4 py-3">{formatValue(row.net_pnl)}</td>
              <td className="px-4 py-3">{formatValue(row.r_multiple)}</td>
              <td className="px-4 py-3">
                <div className="font-medium text-ink">{formatValue(row.exit_reason)}</div>
                <div className="mt-1 max-w-72 text-xs leading-5 text-slate-500">{formatValue(row.notes)}</div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <PaginationControls
        hasNext={hasNextPage}
        itemCount={data.length}
        onPageChange={onPageChange}
        page={page}
        pageSize={pageSize}
        totalCount={totalCount}
      />
    </TableShell>
  );
}

function LifecycleStep({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-panel px-3 py-2">
      <div className="text-xs font-semibold uppercase text-slate-500">{value}</div>
      <div className="mt-1 text-sm font-medium text-ink">{label}</div>
    </div>
  );
}

function journalActionLabel(
  reason: string | null | undefined,
  t: ReturnType<typeof useAppI18n>["t"]
) {
  if (reason === "trim") {
    return t("journalActionTrim");
  }
  if (reason) {
    return t("journalActionClose");
  }
  return t("journalActionOther");
}

function EmptyTableRow({
  colSpan,
  error,
  loading,
  locale,
  message
}: {
  colSpan: number;
  error: boolean;
  loading: boolean;
  locale: Locale;
  message: string;
}) {
  return (
    <tr>
      <td className="border-t border-line px-4 py-6 text-sm text-slate-600" colSpan={colSpan}>
        {loading || error ? <DataState isLoading={loading} isError={error} locale={locale} /> : message}
      </td>
    </tr>
  );
}
