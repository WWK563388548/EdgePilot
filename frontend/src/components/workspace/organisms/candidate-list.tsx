"use client";

import { CalendarDays, Eye } from "lucide-react";
import type { ReactNode } from "react";

import { StatusPill } from "@/components/workspace/atoms/status-pill";
import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import type { CandidateDecisionFilter } from "@/components/workspace/molecules/candidate-decision-filter";
import { DataState } from "@/components/workspace/atoms/data-state";
import type { Candidate } from "@/lib/api";
import { formatDateOnly, formatNumber, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { decisionTone } from "@/lib/presentation";
import { useAppI18n } from "@/lib/use-app-i18n";

export function CandidateList({
  data,
  activeCandidateId,
  decisionFilter,
  loading,
  error,
  locale,
  page,
  pageSize,
  totalCount,
  hasNextPage,
  onPageChange,
  onSelect
}: {
  data: Candidate[];
  activeCandidateId: string | null;
  decisionFilter: CandidateDecisionFilter;
  loading: boolean;
  error: boolean;
  locale: Locale;
  page: number;
  pageSize: number;
  totalCount?: number;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
  onSelect: (candidateId: string) => void;
}) {
  return (
    <>
      <div className="divide-y divide-line">
        {!data.length ? (
          <div className="px-4 py-6 text-sm text-slate-600">
            {loading || error ? (
              <DataState isLoading={loading} isError={error} locale={locale} />
            ) : (
              <EmptyCandidateState decisionFilter={decisionFilter} />
            )}
          </div>
        ) : null}
        {data.map((row) => (
          <CandidateListItem
            active={activeCandidateId === row.candidate_id}
            key={row.candidate_id}
            locale={locale}
            onSelect={() => onSelect(row.candidate_id)}
            row={row}
          />
        ))}
      </div>
      <PaginationControls
        hasNext={hasNextPage}
        itemCount={data.length}
        onPageChange={onPageChange}
        page={page}
        pageSize={pageSize}
        totalCount={totalCount}
      />
    </>
  );
}

function EmptyCandidateState({ decisionFilter }: { decisionFilter: CandidateDecisionFilter }) {
  const { t } = useAppI18n();
  const message =
    decisionFilter === "candidate"
      ? t("emptyCandidatesHint")
      : decisionFilter === "watch"
        ? t("emptyWatchHint")
        : t("emptyAllCandidatesHint");

  return (
    <div>
      <p className="font-medium text-ink">{t("noCandidate")}</p>
      <p className="mt-1 text-slate-600">{message}</p>
    </div>
  );
}

function CandidateListItem({
  row,
  active,
  locale,
  onSelect
}: {
  row: Candidate;
  active: boolean;
  locale: Locale;
  onSelect: () => void;
}) {
  const { labelFor, t } = useAppI18n();
  const score = row.score_total ?? 0;
  const scoreWidth = Math.max(0, Math.min(100, score));
  const setupLabel = row.setup_type ? labelFor("setup", row.setup_type) : row.strategy_name;
  const strategyLabel =
    row.strategy_name === "etf_rotation_us_etf"
      ? t("usEtfRotation")
      : row.strategy_name === "oneil_core_us_etf"
        ? "O'Neil Core"
        : row.strategy_name;

  return (
    <button
      aria-pressed={active}
      className={`focus-ring group block w-full px-4 py-4 text-left transition-colors ${
        active ? "bg-teal-50/70" : "bg-white hover:bg-panel/80"
      }`}
      onClick={onSelect}
      type="button"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-lg font-semibold tracking-normal text-ink">{row.symbol_id}</span>
            <span className="inline-flex h-6 items-center whitespace-nowrap rounded-md border border-line bg-panel px-2 text-xs font-semibold text-slate-700">
              {formatValue(row.pa_setup_grade)}
            </span>
            <StatusPill
              label={labelFor("status", row.validation_status ?? "unlinked")}
              tone={decisionTone(row.validation_status)}
            />
            <StatusPill label={labelFor("status", row.decision ?? "unknown")} tone={decisionTone(row.decision)} />
            <span className="inline-flex h-6 items-center whitespace-nowrap rounded-md border border-teal/20 bg-teal-50 px-2 text-xs font-semibold text-teal">
              {strategyLabel}
            </span>
          </div>
          <div className="mt-1 truncate text-sm font-medium text-ink" title={setupLabel ?? undefined}>
            {setupLabel}
          </div>
        </div>

        <div className="w-24 shrink-0 text-right">
          <div className="text-2xl font-semibold text-ink">{formatNumber(row.score_total, 1, locale)}</div>
          <div className="mt-2 h-1.5 overflow-hidden rounded bg-slate-100">
            <div className="h-full rounded bg-teal" style={{ width: `${scoreWidth}%` }} />
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-2 text-sm sm:grid-cols-3">
        <MiniField label={t("entry")} value={formatNumber(row.entry_trigger, 2, locale)} />
        <MiniField label={t("stop")} value={formatNumber(row.initial_stop, 2, locale)} />
        <MiniField icon={<CalendarDays size={14} />} label={t("scan")} value={formatDateOnly(row.scan_date, locale)} />
      </div>

      <div className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-teal opacity-0 transition-opacity group-hover:opacity-100">
        <Eye size={14} />
        {t("openDetail")}
      </div>
    </button>
  );
}

function MiniField({
  label,
  value,
  icon
}: {
  label: string;
  value: string | number;
  icon?: ReactNode;
}) {
  return (
    <div className="min-w-0 rounded-md border border-line bg-white/80 px-3 py-2">
      <div className="flex items-center gap-1 text-xs text-slate-500">
        {icon}
        <span className="truncate">{label}</span>
      </div>
      <div className="mt-0.5 truncate font-semibold text-ink">{value}</div>
    </div>
  );
}
