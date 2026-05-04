"use client";

import { Activity, CalendarDays } from "lucide-react";
import type { ReactNode } from "react";

import { DataState } from "@/components/workspace/atoms/data-state";
import { StatusPill } from "@/components/workspace/atoms/status-pill";
import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import type { ScannerOutcome } from "@/lib/api";
import { formatDateOnly, formatNumber } from "@/lib/format";
import { localeTag, type Locale } from "@/lib/i18n-config";
import { decisionTone } from "@/lib/presentation";
import { useAppI18n } from "@/lib/use-app-i18n";

export function ScannerOutcomeTable({
  rows,
  loading,
  error,
  locale,
  page,
  pageSize,
  totalCount,
  hasNextPage,
  onPageChange
}: {
  rows: ScannerOutcome[];
  loading: boolean;
  error: boolean;
  locale: Locale;
  page: number;
  pageSize: number;
  totalCount?: number;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
}) {
  const { t } = useAppI18n();

  return (
    <>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-line text-left text-sm">
          <thead className="bg-panel/70 text-xs font-semibold uppercase tracking-normal text-slate-500">
            <tr>
              <HeaderCell>{t("symbol")}</HeaderCell>
              <HeaderCell>{t("evaluationStatus")}</HeaderCell>
              <HeaderCell>{t("score")}</HeaderCell>
              <HeaderCell>{t("triggerAndStop")}</HeaderCell>
              <HeaderCell>{t("return20d")}</HeaderCell>
              <HeaderCell>{t("return60d")}</HeaderCell>
              <HeaderCell>{t("maxFavorableExcursion")}</HeaderCell>
              <HeaderCell>{t("maxAdverseExcursion")}</HeaderCell>
              <HeaderCell>{t("barsAvailable")}</HeaderCell>
              <HeaderCell>{t("detected")}</HeaderCell>
            </tr>
          </thead>
          <tbody className="divide-y divide-line bg-white">
            {!rows.length ? (
              <tr>
                <td className="px-4 py-6 text-sm text-slate-600" colSpan={10}>
                  {loading || error ? (
                    <DataState isLoading={loading} isError={error} locale={locale} />
                  ) : (
                    <div>
                      <p className="font-medium text-ink">{t("noOutcomes")}</p>
                      <p className="mt-1 text-slate-600">{t("emptyOutcomesHint")}</p>
                    </div>
                  )}
                </td>
              </tr>
            ) : null}
            {rows.map((row) => (
              <OutcomeRow key={row.outcome_id} locale={locale} row={row} />
            ))}
          </tbody>
        </table>
      </div>
      <PaginationControls
        hasNext={hasNextPage}
        itemCount={rows.length}
        onPageChange={onPageChange}
        page={page}
        pageSize={pageSize}
        totalCount={totalCount}
      />
    </>
  );
}

function OutcomeRow({ row, locale }: { row: ScannerOutcome; locale: Locale }) {
  const { labelFor, t } = useAppI18n();
  const setupLabel = row.setup_type ? labelFor("setup", row.setup_type) : "-";

  return (
    <tr className="hover:bg-panel/60">
      <td className="whitespace-nowrap px-4 py-4">
        <div className="flex min-w-48 items-start gap-3">
          <div className="mt-0.5 rounded-md border border-teal/25 bg-teal-50 p-2 text-teal">
            <Activity size={16} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-base font-semibold text-ink">{row.symbol_id}</span>
              <span className="rounded-md border border-line bg-panel px-2 py-0.5 text-xs font-semibold text-slate-700">
                {row.setup_grade ?? "-"}
              </span>
            </div>
            <div className="mt-1 max-w-48 truncate text-xs text-slate-500" title={setupLabel}>
              {setupLabel}
            </div>
          </div>
        </div>
      </td>
      <td className="whitespace-nowrap px-4 py-4">
        <StatusPill
          label={labelFor("status", row.evaluation_status)}
          tone={decisionTone(row.evaluation_status)}
        />
      </td>
      <td className="whitespace-nowrap px-4 py-4 font-semibold text-ink">
        {formatNumber(row.score_total, 1, locale)}
      </td>
      <td className="px-4 py-4">
        <div className="flex flex-col gap-1.5">
          <BooleanLine label={t("triggered")} value={row.triggered_entry} />
          <BooleanLine label={t("stopped")} value={row.stopped_out} />
          <BooleanLine label={t("falseBreakout")} value={row.false_breakout} />
        </div>
      </td>
      <td className="whitespace-nowrap px-4 py-4">
        <PercentValue locale={locale} value={row.forward_return_20d} />
      </td>
      <td className="whitespace-nowrap px-4 py-4">
        <PercentValue locale={locale} value={row.forward_return_60d} />
      </td>
      <td className="whitespace-nowrap px-4 py-4">
        <div className="text-xs text-slate-500">20D</div>
        <PercentValue locale={locale} value={row.mfe_20d} />
        <div className="mt-1 text-xs text-slate-500">60D</div>
        <PercentValue locale={locale} value={row.mfe_60d} />
      </td>
      <td className="whitespace-nowrap px-4 py-4">
        <div className="text-xs text-slate-500">20D</div>
        <PercentValue locale={locale} value={row.mae_20d} />
        <div className="mt-1 text-xs text-slate-500">60D</div>
        <PercentValue locale={locale} value={row.mae_60d} />
      </td>
      <td className="whitespace-nowrap px-4 py-4 font-medium text-ink">
        {formatNumber(row.bars_available, 0, locale)}
      </td>
      <td className="whitespace-nowrap px-4 py-4 text-slate-600">
        <div className="inline-flex items-center gap-1.5">
          <CalendarDays size={14} />
          {formatDateOnly(row.detected_ts, locale)}
        </div>
      </td>
    </tr>
  );
}

function HeaderCell({ children }: { children: ReactNode }) {
  return <th className="whitespace-nowrap px-4 py-3">{children}</th>;
}

function BooleanLine({
  label,
  value
}: {
  label: string;
  value: boolean | null;
}) {
  const { labelFor } = useAppI18n();

  return (
    <div className="flex min-w-36 items-center justify-between gap-3 text-xs">
      <span className="text-slate-500">{label}</span>
      <span className={`font-semibold ${value ? "text-ink" : "text-slate-400"}`}>
        {value === null ? "-" : labelFor("plan", value ? "true" : "false")}
      </span>
    </div>
  );
}

function PercentValue({ value, locale }: { value: number | null; locale: Locale }) {
  if (value === null || value === undefined) {
    return <span className="text-slate-400">-</span>;
  }

  const tone = value > 0 ? "text-teal" : value < 0 ? "text-rose-700" : "text-slate-700";
  return (
    <span className={`font-semibold ${tone}`}>
      {new Intl.NumberFormat(localeTag[locale], {
        maximumFractionDigits: 1,
        minimumFractionDigits: 0,
        style: "percent"
      }).format(value)}
    </span>
  );
}
