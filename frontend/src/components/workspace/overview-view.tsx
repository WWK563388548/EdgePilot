import {
  Activity,
  AlertTriangle,
  BriefcaseBusiness,
  Database,
  ListChecks,
  ShieldCheck
} from "lucide-react";

import { Field, Metric } from "@/components/workspace/common";
import type { DashboardSummary } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { t, type Locale } from "@/lib/i18n";

export function OverviewView({
  locale,
  summary
}: {
  locale: Locale;
  summary: DashboardSummary | undefined;
}) {
  return (
    <div className="space-y-6">
      <section className="grid gap-3 md:grid-cols-4">
        <Metric icon={<ListChecks size={18} />} label={t(locale, "candidates")} value={summary?.candidate_count ?? 0} />
        <Metric icon={<BriefcaseBusiness size={18} />} label={t(locale, "openPositions")} value={summary?.open_position_count ?? 0} />
        <Metric icon={<AlertTriangle size={18} />} label={t(locale, "openAlerts")} value={summary?.exit_alert_count ?? 0} />
        <Metric icon={<ShieldCheck size={18} />} label={t(locale, "highestLevel")} value={summary?.highest_exit_level ?? "-"} />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
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

        <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
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
  );
}
