"use client";

import {
  Activity,
  AlertTriangle,
  BriefcaseBusiness,
  Database,
  ListChecks,
  ShieldCheck
} from "lucide-react";

import { Field } from "@/components/workspace/atoms/field";
import { Metric } from "@/components/workspace/atoms/stat-card";
import type { DashboardSummary } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function OverviewView({
  locale,
  summary
}: {
  locale: Locale;
  summary: DashboardSummary | undefined;
}) {
  const { t } = useAppI18n();

  return (
    <div className="flex flex-col gap-6">
      <section className="grid gap-3 md:grid-cols-4">
        <Metric icon={<ListChecks size={18} />} label={t("candidates")} value={summary?.candidate_count ?? 0} />
        <Metric icon={<BriefcaseBusiness size={18} />} label={t("openPositions")} value={summary?.open_position_count ?? 0} />
        <Metric icon={<AlertTriangle size={18} />} label={t("openAlerts")} value={summary?.exit_alert_count ?? 0} />
        <Metric icon={<ShieldCheck size={18} />} label={t("highestLevel")} value={summary?.highest_exit_level ?? "-"} />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold text-ink">{t("marketContext")}</h2>
            <Activity size={18} className="text-teal" />
          </div>
          <dl className="grid gap-3 sm:grid-cols-2">
            <Field label={t("risk")} value={summary?.market_context.risk_level} />
            <Field label={t("usBias")} value={summary?.market_context.us_bias} />
            <Field label={t("japanBias")} value={summary?.market_context.japan_bias} />
            <Field label={t("updated")} value={formatDate(summary?.market_context.snapshot_ts, locale)} />
          </dl>
          <p className="mt-4 text-sm text-slate-600">{summary?.market_context.notes ?? t("noMarketNotes")}</p>
        </div>

        <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold text-ink">{t("dataFreshness")}</h2>
            <Database size={18} className="text-teal" />
          </div>
          <div className="flex flex-col gap-3">
            {summary?.data_freshness.length ? (
              summary.data_freshness.map((item) => (
                <div key={item.dataset_key} className="flex items-center justify-between gap-3 border-b border-line pb-2 last:border-0 last:pb-0">
                  <div>
                    <div className="text-sm font-medium text-ink">{item.dataset_key}</div>
                    <div className="text-xs text-slate-500">{item.source ?? t("unknown")}</div>
                  </div>
                  <div className="text-right text-xs text-slate-600">{formatDate(item.last_updated_at, locale)}</div>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-600">{t("noFreshnessRecords")}</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
