"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  CheckCircle2,
  CircleSlash,
  HelpCircle,
  ListFilter,
  RefreshCw,
  TrendingUp
} from "lucide-react";
import { useState } from "react";

import { CompactStat } from "@/components/workspace/atoms/stat-card";
import { DataState } from "@/components/workspace/atoms/data-state";
import { ScannerOutcomeGuide } from "@/components/workspace/molecules/scanner-outcome-guide";
import { ScannerOutcomeTable } from "@/components/workspace/organisms/scanner-outcome-table";
import { api, type ScannerOutcomeFilters } from "@/lib/api";
import { localeTag, type Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

const OUTCOME_PAGE_SIZE = 10;
type OutcomeStatusFilter = "all" | "matured_60d" | "matured_20d" | "pending" | "missing_reference";

export function OutcomesView({ locale }: { locale: Locale }) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<OutcomeStatusFilter>("all");
  const [page, setPage] = useState(0);
  const [recalculateResult, setRecalculateResult] = useState<string | null>(null);
  const evaluationStatus = statusFilter === "all" ? undefined : statusFilter;
  const baseFilters: ScannerOutcomeFilters = {
    evaluationStatus
  };
  const pageFilters: ScannerOutcomeFilters = {
    ...baseFilters,
    limit: OUTCOME_PAGE_SIZE + 1,
    offset: page * OUTCOME_PAGE_SIZE
  };

  const outcomes = useQuery({
    queryKey: ["scanner-outcomes", evaluationStatus, page],
    queryFn: () => api.scannerOutcomes(pageFilters)
  });
  const outcomesCount = useQuery({
    queryKey: ["scanner-outcomes-count", evaluationStatus],
    queryFn: () => api.scannerOutcomesCount(baseFilters)
  });
  const summary = useQuery({
    queryKey: ["scanner-outcomes-summary", evaluationStatus],
    queryFn: () => api.scannerOutcomeSummary(baseFilters)
  });
  const recalculate = useMutation({
    mutationFn: () => api.recalculateScannerOutcomes(),
    onSuccess: async (response) => {
      setPage(0);
      setRecalculateResult(
        t("recalculateOutcomesResult", {
          outcomes: response.outcomes_written,
          skipped: response.skipped_candidates
        })
      );
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["scanner-outcomes"] }),
        queryClient.invalidateQueries({ queryKey: ["scanner-outcomes-count"] }),
        queryClient.invalidateQueries({ queryKey: ["scanner-outcomes-summary"] })
      ]);
    },
    onError: () => {
      setRecalculateResult(null);
    }
  });
  const rawRows = outcomes.data ?? [];
  const rows = rawRows.slice(0, OUTCOME_PAGE_SIZE);
  const hasNextPage =
    outcomesCount.data?.total !== undefined
      ? (page + 1) * OUTCOME_PAGE_SIZE < outcomesCount.data.total
      : rawRows.length > OUTCOME_PAGE_SIZE;
  const total = summary.data?.total ?? outcomesCount.data?.total ?? rows.length;

  return (
    <section className="flex flex-col gap-4">
      <div className="grid gap-3 md:grid-cols-4">
        <CompactStat icon={<Activity size={18} />} label={t("outcomePool")} value={total} />
        <CompactStat
          icon={<CheckCircle2 size={18} />}
          label={t("triggerRate")}
          value={formatPercent(summary.data?.trigger_rate, locale)}
        />
        <CompactStat
          icon={<TrendingUp size={18} />}
          label={t("hitRate20d")}
          value={formatPercent(summary.data?.positive_20d_rate, locale)}
        />
        <CompactStat
          icon={<CircleSlash size={18} />}
          label={t("falseBreakoutRate")}
          value={formatPercent(summary.data?.false_breakout_rate, locale)}
        />
      </div>

      <ScannerOutcomeGuide />

      <section className="overflow-hidden rounded-md border border-line bg-white shadow-[0_1px_0_rgba(22,32,42,0.04)]">
        <div className="flex flex-col gap-3 border-b border-line bg-white px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-center gap-2">
            <Activity size={18} className="shrink-0 text-teal" />
            <div className="min-w-0">
              <h2 className="truncate text-base font-semibold text-ink">{t("scannerReview")}</h2>
              <p className="text-xs text-slate-500">{t("outcomeDataBoundary")}</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              className="focus-ring inline-flex h-9 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60"
              disabled={recalculate.isPending}
              onClick={() => recalculate.mutate()}
              title={t("recalculateOutcomesHelp")}
              type="button"
            >
              <RefreshCw size={16} className={recalculate.isPending ? "animate-spin" : ""} />
              {recalculate.isPending ? t("recalculatingOutcomes") : t("recalculateOutcomes")}
            </button>
            <span
              className="inline-flex h-9 items-center rounded-md border border-line bg-panel px-2 text-slate-500"
              title={t("recalculateOutcomesHelp")}
            >
              <HelpCircle size={15} />
            </span>
            <OutcomeStatusControl
              active={statusFilter}
              labelFor={(value) => (value === "all" ? t("allOutcomes") : labelFor("status", value))}
              onChange={(nextStatus) => {
                setStatusFilter(nextStatus);
                setPage(0);
              }}
            />
            <DataState
              isLoading={outcomes.isLoading || summary.isLoading || recalculate.isPending}
              isError={outcomes.isError || summary.isError || recalculate.isError}
              locale={locale}
            />
          </div>
        </div>

        {recalculateResult || recalculate.isError ? (
          <div
            className={`border-b border-line px-4 py-3 text-sm ${
              recalculate.isError ? "bg-rose-50 text-rose-700" : "bg-teal-50 text-teal-800"
            }`}
          >
            {recalculate.isError ? t("recalculateOutcomesFailed") : recalculateResult}
          </div>
        ) : null}

        <div className="grid gap-3 border-b border-line bg-panel/45 px-4 py-3 text-sm text-slate-600 lg:grid-cols-3">
          <SummaryMetric label={t("maturedOutcomes")} value={summary.data?.matured_count ?? 0} />
          <SummaryMetric label={t("pendingOutcomes")} value={summary.data?.pending_count ?? 0} />
          <SummaryMetric
            label={t("avgReturn60d")}
            value={formatPercent(summary.data?.avg_forward_return_60d, locale)}
          />
        </div>

        <ScannerOutcomeTable
          error={outcomes.isError}
          hasNextPage={hasNextPage}
          loading={outcomes.isLoading}
          locale={locale}
          onPageChange={setPage}
          page={page}
          pageSize={OUTCOME_PAGE_SIZE}
          rows={rows}
          totalCount={outcomesCount.data?.total}
        />
      </section>
    </section>
  );
}

function OutcomeStatusControl({
  active,
  onChange,
  labelFor
}: {
  active: OutcomeStatusFilter;
  onChange: (filter: OutcomeStatusFilter) => void;
  labelFor: (value: OutcomeStatusFilter) => string;
}) {
  const options: OutcomeStatusFilter[] = [
    "all",
    "matured_60d",
    "matured_20d",
    "pending",
    "missing_reference"
  ];

  return (
    <div className="inline-flex max-w-full items-center gap-1 overflow-x-auto rounded-md border border-line bg-panel p-1">
      <ListFilter size={15} className="mx-2 shrink-0 text-slate-500" />
      {options.map((option) => (
        <button
          className={`focus-ring whitespace-nowrap rounded px-2.5 py-1.5 text-xs font-semibold transition-colors ${
            active === option ? "bg-ink text-white" : "text-slate-600 hover:bg-white hover:text-ink"
          }`}
          key={option}
          onClick={() => onChange(option)}
          type="button"
        >
          {labelFor(option)}
        </button>
      ))}
    </div>
  );
}

function SummaryMetric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="min-w-0">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 truncate text-base font-semibold text-ink">{value}</div>
    </div>
  );
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
