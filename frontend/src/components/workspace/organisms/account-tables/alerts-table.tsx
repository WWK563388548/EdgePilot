"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Clock3, RefreshCw } from "lucide-react";
import { useState } from "react";

import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import { TableShell } from "@/components/workspace/molecules/table-shell";
import { EmptyTableRow } from "@/components/workspace/organisms/account-tables/empty-table-row";
import type { PaginatedTableProps } from "@/components/workspace/organisms/account-tables/types";
import { api, type ExitAlert } from "@/lib/api";
import { formatDate, formatValue } from "@/lib/format";
import { useAppI18n } from "@/lib/use-app-i18n";

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
        queryClient.invalidateQueries({ queryKey: ["positions-count"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] })
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
