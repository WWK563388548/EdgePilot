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
import type { DashboardSummary, PortfolioRiskSummary } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { localeTag } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function OverviewView({
  locale,
  portfolioRisk,
  summary
}: {
  locale: Locale;
  portfolioRisk: PortfolioRiskSummary | undefined;
  summary: DashboardSummary | undefined;
}) {
  const { t } = useAppI18n();
  const riskUsedPct = portfolioRisk?.total_risk_pct ?? 0;
  const riskBudgetPct = portfolioRisk?.max_total_risk_pct ?? 0;
  const riskUsage =
    riskBudgetPct > 0 ? Math.min(100, Math.max(0, (riskUsedPct / riskBudgetPct) * 100)) : 0;

  return (
    <div className="flex flex-col gap-6">
      <section className="grid gap-3 md:grid-cols-4">
        <Metric icon={<ListChecks size={18} />} label={t("candidates")} value={summary?.candidate_count ?? 0} />
        <Metric icon={<BriefcaseBusiness size={18} />} label={t("openPositions")} value={summary?.open_position_count ?? 0} />
        <Metric icon={<AlertTriangle size={18} />} label={t("openAlerts")} value={summary?.exit_alert_count ?? 0} />
        <Metric icon={<ShieldCheck size={18} />} label={t("highestLevel")} value={summary?.highest_exit_level ?? "-"} />
      </section>

      <section className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink">{t("portfolioRiskMonitor")}</h2>
            <p className="mt-1 text-xs text-slate-600">{t("portfolioRiskMonitorHelp")}</p>
          </div>
          <ShieldCheck size={18} className="text-teal" />
        </div>
        <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-md border border-line bg-panel/50 p-4">
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm font-semibold text-slate-600">{t("riskBudgetUsed")}</span>
              <span className="text-2xl font-semibold text-ink">
                {formatPercent(riskUsedPct, locale)}
              </span>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
              <div
                className={`h-full rounded-full ${
                  riskUsage >= 100 ? "bg-rose-600" : riskUsage >= 75 ? "bg-amber-500" : "bg-teal"
                }`}
                style={{ width: `${riskUsage}%` }}
              />
            </div>
            <dl className="mt-4 grid gap-3 sm:grid-cols-2">
              <Field label={t("totalRisk")} value={formatMoney(portfolioRisk?.total_risk_amount, locale)} />
              <Field label={t("remainingRisk")} value={formatMoney(portfolioRisk?.remaining_risk_amount, locale)} />
              <Field label={t("riskBudget")} value={formatMoney(portfolioRisk?.max_total_risk_amount, locale)} />
              <Field
                label={t("activePositions")}
                value={`${portfolioRisk?.active_position_count ?? 0}/${portfolioRisk?.max_open_positions ?? 0}`}
              />
            </dl>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <RiskSlice label={t("plannedRisk")} locale={locale} value={portfolioRisk?.planned_risk_amount} />
            <RiskSlice label={t("openRisk")} locale={locale} value={portfolioRisk?.open_risk_amount} />
            <RiskSlice label={t("reducedRisk")} locale={locale} value={portfolioRisk?.reduced_risk_amount} />
            <div className="rounded-md border border-line p-3 sm:col-span-3">
              <div className="mb-2 text-xs font-semibold uppercase text-slate-500">
                {t("highestSymbolRisk")}
              </div>
              {portfolioRisk?.highest_symbol_risk ? (
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-lg font-semibold text-ink">
                    {portfolioRisk.highest_symbol_risk.symbol_id}
                  </div>
                  <div className="text-sm font-medium text-slate-700">
                    {formatMoney(portfolioRisk.highest_symbol_risk.risk_amount, locale)} ·{" "}
                    {formatPercent(portfolioRisk.highest_symbol_risk.risk_pct, locale)}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-600">{t("noPortfolioRisk")}</p>
              )}
            </div>
          </div>
        </div>
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

function RiskSlice({ label, locale, value }: { label: string; locale: Locale; value: number | undefined }) {
  return (
    <div className="rounded-md border border-line p-3">
      <div className="text-xs font-semibold uppercase text-slate-500">{label}</div>
      <div className="mt-2 text-lg font-semibold text-ink">{formatMoney(value, locale)}</div>
    </div>
  );
}

function formatMoney(value: number | null | undefined, locale: Locale) {
  if (value === null || value === undefined) {
    return "-";
  }
  return new Intl.NumberFormat(localeTag[locale], {
    currency: "USD",
    maximumFractionDigits: 0,
    minimumFractionDigits: 0,
    style: "currency"
  }).format(value);
}

function formatPercent(value: number | null | undefined, locale: Locale) {
  if (value === null || value === undefined) {
    return "-";
  }
  return new Intl.NumberFormat(localeTag[locale], {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
    style: "percent"
  }).format(value);
}
