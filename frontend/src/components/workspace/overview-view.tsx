"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  BriefcaseBusiness,
  Database,
  Gauge,
  ListChecks,
  ShieldCheck
} from "lucide-react";

import { Field } from "@/components/workspace/atoms/field";
import { Metric } from "@/components/workspace/atoms/stat-card";
import type { AnalyticsOverview, DashboardSummary, PortfolioRiskSummary } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { localeTag } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function OverviewView({
  analytics,
  locale,
  portfolioRisk,
  summary
}: {
  analytics: AnalyticsOverview | undefined;
  locale: Locale;
  portfolioRisk: PortfolioRiskSummary | undefined;
  summary: DashboardSummary | undefined;
}) {
  const { labelFor, t } = useAppI18n();
  const riskUsedPct = portfolioRisk?.total_risk_pct ?? 0;
  const riskBudgetPct = portfolioRisk?.max_total_risk_pct ?? 0;
  const riskUsage =
    riskBudgetPct > 0 ? Math.min(100, Math.max(0, (riskUsedPct / riskBudgetPct) * 100)) : 0;

  return (
    <div className="flex flex-col gap-6">
      <section className="grid gap-3 md:grid-cols-4">
        <Metric icon={<BarChart3 size={18} />} label={t("totalPnl")} value={formatMoney(analytics?.total_pnl, locale)} />
        <Metric icon={<Gauge size={18} />} label={t("averageR")} value={formatR(analytics?.average_r, locale)} />
        <Metric icon={<ListChecks size={18} />} label={t("trades")} value={analytics?.trades_count ?? 0} />
        <Metric icon={<BriefcaseBusiness size={18} />} label={t("openPositions")} value={analytics?.open_positions_count ?? summary?.open_position_count ?? 0} />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">{t("realPerformance")}</h2>
              <p className="mt-1 text-xs text-slate-600">{t("realPerformanceHelp")}</p>
            </div>
            <BarChart3 size={18} className="text-teal" />
          </div>
          <dl className="grid gap-3 sm:grid-cols-3">
            <Field label={t("realizedPnl")} value={formatMoney(analytics?.realized_pnl, locale)} />
            <Field label={t("unrealizedPnl")} value={formatMoney(analytics?.unrealized_pnl, locale)} />
            <Field label={t("winRate")} value={formatPercent(analytics?.win_rate, locale)} />
            <Field label={t("profitFactor")} value={formatNumber(analytics?.profit_factor, 2, locale)} />
            <Field label={t("expectancyR")} value={formatR(analytics?.expectancy_r, locale)} />
            <Field label={t("maxDrawdown")} value={formatPercent(analytics?.max_drawdown_pct, locale)} />
          </dl>
        </div>

        <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-ink">{t("executionQuality")}</h2>
              <p className="mt-1 text-xs text-slate-600">{t("executionQualityHelp")}</p>
            </div>
            <Gauge size={18} className="text-teal" />
          </div>
          <dl className="grid gap-3 sm:grid-cols-2">
            <Field label={t("fills")} value={analytics?.execution_quality.fills_count ?? 0} />
            <Field label={t("needsReview")} value={analytics?.execution_quality.review_needed_fills_count ?? 0} />
            <Field label={t("entryDragR")} value={formatR(analytics?.execution_quality.average_entry_drag_r, locale)} />
            <Field label={t("entrySlippage")} value={formatPercent(analytics?.execution_quality.average_entry_slippage_pct, locale)} />
            <Field label={t("exitDragR")} value={formatR(analytics?.execution_quality.average_exit_drag_r, locale)} />
            <Field label={t("plannedEntries")} value={analytics?.execution_quality.planned_entry_count ?? 0} />
          </dl>
        </div>
      </section>

      <section className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink">{t("strategyBreakdown")}</h2>
            <p className="mt-1 text-xs text-slate-600">{t("strategyBreakdownHelp")}</p>
          </div>
          <Activity size={18} className="text-teal" />
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="border-b border-line text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-2 py-2">{t("strategy")}</th>
                <th className="px-2 py-2">{t("trades")}</th>
                <th className="px-2 py-2">{t("realizedPnl")}</th>
                <th className="px-2 py-2">{t("winRate")}</th>
                <th className="px-2 py-2">{t("averageR")}</th>
              </tr>
            </thead>
            <tbody>
              {analytics?.strategy_breakdown.length ? (
                analytics.strategy_breakdown.map((row) => (
                  <tr className="border-b border-line last:border-0" key={row.strategy_name}>
                    <td className="px-2 py-2 font-medium text-ink">{labelFor("plan", row.strategy_name)}</td>
                    <td className="px-2 py-2 text-slate-700">{row.trades_count}</td>
                    <td className="px-2 py-2 text-slate-700">{formatMoney(row.realized_pnl, locale)}</td>
                    <td className="px-2 py-2 text-slate-700">{formatPercent(row.win_rate, locale)}</td>
                    <td className="px-2 py-2 text-slate-700">{formatR(row.average_r, locale)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-2 py-4 text-sm text-slate-600" colSpan={5}>
                    {t("noRealAnalytics")}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
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

function formatR(value: number | null | undefined, locale: Locale) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${formatNumber(value, 2, locale)}R`;
}
