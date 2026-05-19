"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ClipboardCheck, RefreshCw, TimerReset } from "lucide-react";
import type { ReactNode } from "react";

import { TableShell } from "@/components/workspace/molecules/table-shell";
import { api, type PaperReviewSummary } from "@/lib/api";
import { formatDate, formatNumber, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function PaperReviewView({
  data,
  error,
  loading,
  locale
}: {
  data: PaperReviewSummary | undefined;
  error: boolean;
  loading: boolean;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const evaluateAlerts = useMutation({
    mutationFn: () => api.evaluateExitAlerts(),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["paper-review"] }),
        queryClient.invalidateQueries({ queryKey: ["alerts"] }),
        queryClient.invalidateQueries({ queryKey: ["alerts-count"] }),
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] }),
        queryClient.invalidateQueries({ queryKey: ["portfolio-risk"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      ]);
    }
  });

  const rows = data?.positions ?? [];

  return (
    <TableShell
      title={t("paperReview")}
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
          {evaluateAlerts.isPending ? t("evaluatingExitAlerts") : t("paperReviewEvaluateAlerts")}
        </button>
      }
    >
      <div className="border-b border-line bg-white px-4 py-4">
        <p className="max-w-3xl text-sm text-slate-600">{t("paperReviewHelp")}</p>
        <div className="mt-3 text-xs text-slate-500">
          {t("paperReviewGenerated", {
            time: data?.generated_at ? formatDate(data.generated_at, locale) : "-"
          })}
        </div>
      </div>

      <div className="grid gap-3 border-b border-line bg-panel px-4 py-4 md:grid-cols-4">
        <ReviewStat
          icon={<ClipboardCheck size={18} />}
          label={t("paperReviewActivePositions")}
          value={data?.total_positions ?? 0}
        />
        <ReviewStat
          icon={<TimerReset size={18} />}
          label={t("paperReviewPlanned")}
          value={data?.planned_count ?? 0}
        />
        <ReviewStat
          icon={<CheckCircle2 size={18} />}
          label={t("paperReviewOpenReduced")}
          value={(data?.open_count ?? 0) + (data?.reduced_count ?? 0)}
        />
        <ReviewStat
          icon={<AlertTriangle size={18} />}
          label={t("paperReviewOpenAlerts")}
          value={data?.open_alert_count ?? 0}
        />
      </div>

      <div className="grid gap-3 bg-white px-4 py-4">
        {!rows.length ? (
          <div className="rounded-md border border-line bg-panel px-4 py-6 text-sm text-slate-600">
            {t("paperReviewNoPositions")}
          </div>
        ) : null}
        {rows.map((row) => {
          const position = row.position;
          return (
            <article
              className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]"
              key={position.position_id}
            >
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-lg font-semibold text-ink">{position.symbol_id}</h3>
                    <span className="rounded-md border border-line bg-panel px-2 py-1 text-xs font-semibold text-slate-700">
                      {labelFor("status", position.status)}
                    </span>
                    {row.candidate_role ? (
                      <span className="rounded-md border border-teal/30 bg-teal-50 px-2 py-1 text-xs font-semibold text-teal">
                        {labelFor("plan", row.candidate_role)}
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-1 text-sm text-slate-600">
                    {labelFor("plan", row.next_action_reason)}
                  </p>
                </div>
                <div className="rounded-md border border-line bg-panel px-3 py-2 text-sm">
                  <div className="text-xs font-semibold uppercase text-slate-500">
                    {t("paperReviewNextAction")}
                  </div>
                  <div className="mt-1 font-semibold text-ink">{labelFor("plan", row.next_action)}</div>
                </div>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-4">
                <MiniField label={t("entry")} value={formatNumber(position.entry_price, 2, locale)} />
                <MiniField label={t("stop")} value={formatNumber(position.current_stop, 2, locale)} />
                <MiniField label={t("qty")} value={formatValue(position.quantity)} />
                <MiniField
                  label={t("riskAmount")}
                  value={position.risk_amount === null ? "-" : `US$${formatNumber(position.risk_amount, 0, locale)}`}
                />
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <MiniField label={t("entryMode")} value={labelFor("plan", row.entry_mode)} />
                <MiniField
                  label={t("paperReviewMax20d")}
                  value={
                    row.max_20d_return === null
                      ? "-"
                      : `${formatNumber(row.max_20d_return, 1, locale)}% · ${labelFor(
                          "plan",
                          row.max_20d_lottery_risk ? `max20d_${row.max_20d_lottery_risk}` : null
                        )}`
                  }
                />
                <MiniField
                  label={t("paperReviewLatestAlert")}
                  value={
                    row.latest_alert
                      ? `${labelFor("plan", row.latest_alert.reason)} · L${formatValue(row.latest_alert.level)}`
                      : "-"
                  }
                />
              </div>
            </article>
          );
        })}
      </div>
    </TableShell>
  );
}

function ReviewStat({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-white px-4 py-3">
      <div className="mb-2 flex items-center justify-between text-slate-500">
        {icon}
        <span className="text-xs font-semibold uppercase">{label}</span>
      </div>
      <div className="text-2xl font-semibold text-ink">{value}</div>
    </div>
  );
}

function MiniField({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-line bg-panel px-3 py-2">
      <div className="text-xs font-semibold uppercase text-slate-500">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}
