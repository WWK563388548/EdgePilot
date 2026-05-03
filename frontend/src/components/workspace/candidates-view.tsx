"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, CircleHelp, Eye, RefreshCw, Target, TrendingUp } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { CompactStat, DataState, PaginationControls, StatusPill } from "@/components/workspace/common";
import { CandidateDetailPanel } from "@/components/workspace/detail-panels";
import type { Candidate, ETFOneilScannerResponse, ETFUniverseSeedResponse } from "@/lib/api";
import { api } from "@/lib/api";
import { formatDateOnly, formatNumber, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { decisionTone } from "@/lib/presentation";
import { useAppI18n } from "@/lib/use-app-i18n";

export type CandidateDecisionFilter = "candidate" | "watch" | "all";
type AccountScanResult = ETFOneilScannerResponse | ETFUniverseSeedResponse;

export function CandidatesView({
  data,
  decisionFilter,
  onDecisionFilterChange,
  page,
  pageSize,
  hasNextPage,
  onPageChange,
  loading,
  error,
  locale
}: {
  data: Candidate[];
  decisionFilter: CandidateDecisionFilter;
  onDecisionFilterChange: (filter: CandidateDecisionFilter) => void;
  page: number;
  pageSize: number;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
  loading: boolean;
  error: boolean;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [scanResult, setScanResult] = useState<AccountScanResult | null>(null);
  const activeCandidateId = detailOpen ? selectedCandidateId ?? data[0]?.candidate_id ?? null : null;
  const detail = useQuery({
    queryKey: ["candidate-detail", activeCandidateId],
    queryFn: () => api.candidateDetail(activeCandidateId as string),
    enabled: Boolean(activeCandidateId)
  });
  const quickScan = useMutation({
    mutationFn: () => api.scanAccountOneilCandidates({ recalculate_facts: true }),
    onSuccess: async (response) => {
      setScanResult(response);
      setDetailOpen(false);
      setSelectedCandidateId(null);
      onPageChange(0);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["candidates"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["pa-setups"] })
      ]);
    }
  });
  const marketRefreshScan = useMutation({
    mutationFn: () => api.refreshAccountOneilCandidates(),
    onSuccess: async (response) => {
      setScanResult(response);
      setDetailOpen(false);
      setSelectedCandidateId(null);
      onPageChange(0);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["candidates"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["pa-setups"] })
      ]);
    }
  });
  const scanPending = quickScan.isPending || marketRefreshScan.isPending;
  const scanError = quickScan.isError || marketRefreshScan.isError;
  const topScore = useMemo(
    () => data.reduce<number | null>((best, row) => Math.max(best ?? 0, row.score_total ?? 0), null),
    [data]
  );
  const activeCandidate = data.find((row) => row.candidate_id === activeCandidateId);
  const candidateCount = hasNextPage ? `${page * pageSize + data.length}+` : page * pageSize + data.length;

  useEffect(() => {
    if (selectedCandidateId && !data.some((row) => row.candidate_id === selectedCandidateId)) {
      setSelectedCandidateId(null);
      setDetailOpen(false);
    }
  }, [data, selectedCandidateId]);

  return (
    <section className="flex flex-col gap-4">
      <div className="grid gap-3 md:grid-cols-3">
        <CompactStat icon={<Target size={18} />} label={t("candidatePool")} value={candidateCount} />
        <CompactStat icon={<TrendingUp size={18} />} label={t("topScore")} value={formatNumber(topScore, 1, locale)} />
        <CompactStat icon={<Eye size={18} />} label={t("selected")} value={activeCandidate?.symbol_id ?? "-"} />
      </div>

      <section>
        <section className="min-w-0 overflow-hidden rounded-md border border-line bg-white shadow-[0_1px_0_rgba(22,32,42,0.04)]">
          <div className="flex flex-col gap-3 border-b border-line bg-white px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 items-center gap-2">
              <Target size={18} className="shrink-0 text-teal" />
              <div className="min-w-0">
                <h2 className="truncate text-base font-semibold text-ink">{t("candidates")}</h2>
                <p className="text-xs text-slate-500">{t("accountScopedCandidates")}</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <DecisionFilterControl
                active={decisionFilter}
                onChange={onDecisionFilterChange}
              />
              <DataState isLoading={loading || scanPending} isError={error || scanError} locale={locale} />
              <button
                className="focus-ring inline-flex h-9 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60"
                disabled={scanPending}
                onClick={() => quickScan.mutate()}
                type="button"
              >
                <RefreshCw size={16} className={quickScan.isPending ? "animate-spin" : ""} />
                {quickScan.isPending ? t("scanning") : t("quickRescan")}
              </button>
              <button
                className="focus-ring inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
                disabled={scanPending}
                onClick={() => marketRefreshScan.mutate()}
                type="button"
              >
                <RefreshCw size={16} className={marketRefreshScan.isPending ? "animate-spin" : ""} />
                {marketRefreshScan.isPending ? t("refreshingMarketData") : t("refreshBarsAndRescan")}
              </button>
              <ScanActionsHelp />
            </div>
          </div>

          <div className="border-b border-line bg-panel/50 px-4 py-3 text-sm leading-6 text-slate-600">
            <p>{t("candidateDataBoundary")}</p>
            <p className="mt-1 text-xs text-slate-500">
              {t("scanParameterSummary", {
                maxCandidates: 25,
                minScore: 60,
                universe: "US ETF"
              })}
            </p>
          </div>

          {scanResult || scanError ? (
            <div
              className={`border-b border-line px-4 py-3 ${
                scanError ? "bg-rose-50 text-rose-700" : "bg-teal-50 text-teal-800"
              }`}
            >
              {scanError ? (
                <p className="text-sm">{t("scanFailed")}</p>
              ) : scanResult ? (
                <ScanResultPanel locale={locale} result={scanResult} />
              ) : null}
            </div>
          ) : null}

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
                onSelect={() => {
                  setSelectedCandidateId(row.candidate_id);
                  setDetailOpen(true);
                }}
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
          />
        </section>

      </section>
      {detailOpen && activeCandidateId ? (
        <CandidateDetailPanel
          detail={detail.data}
          error={detail.isError}
          locale={locale}
          loading={detail.isLoading}
          onClose={() => {
            setDetailOpen(false);
            setSelectedCandidateId(null);
          }}
          selected={Boolean(activeCandidateId)}
        />
      ) : null}
    </section>
  );
}

function ScanActionsHelp() {
  const { t } = useAppI18n();

  return (
    <div className="group relative inline-flex">
      <button
        aria-label={t("scanActionsHelp")}
        className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md border border-line bg-white text-slate-600 transition-colors hover:border-teal hover:text-teal"
        type="button"
      >
        <CircleHelp size={17} />
      </button>
      <div
        className="pointer-events-none absolute right-0 top-full z-30 mt-2 w-80 rounded-md border border-line bg-white p-3 text-left text-xs leading-5 text-slate-600 opacity-0 shadow-lg transition-opacity duration-150 group-focus-within:opacity-100 group-hover:opacity-100"
        role="tooltip"
      >
        <p>
          <span className="font-semibold text-ink">{t("quickRescan")}:</span> {t("quickRescanHelp")}
        </p>
        <p className="mt-2">
          <span className="font-semibold text-ink">{t("refreshBarsAndRescan")}:</span>{" "}
          {t("marketRefreshRescanHelp")}
        </p>
      </div>
    </div>
  );
}

function ScanResultPanel({
  result,
  locale
}: {
  result: AccountScanResult;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const candidateCount = result.decision_counts?.candidate ?? 0;
  const watchCount = result.decision_counts?.watch ?? 0;
  const isMarketRefresh = "bars_written" in result;
  const scannedSymbols = "symbols_scanned" in result ? result.symbols_scanned : result.symbols_requested;
  const symbols = scannedSymbols.join(", ");
  const skippedSymbols = result.skipped_symbols.length ? result.skipped_symbols.join(", ") : t("none");
  const metrics = [
    { label: t("scanMode"), value: isMarketRefresh ? t("marketRefreshMode") : t("quickRescanMode") },
    ...(isMarketRefresh
      ? [{ label: t("barsWritten"), value: formatNumber(result.bars_written, 0, locale) }]
      : []),
    { label: t("symbolsScanned"), value: formatNumber(scannedSymbols.length, 0, locale) },
    { label: t("factsWritten"), value: formatNumber(result.facts_written, 0, locale) },
    { label: t("setupsWritten"), value: formatNumber(result.setups_written, 0, locale) },
    { label: t("candidatesWritten"), value: formatNumber(result.candidates_written, 0, locale) },
    { label: t("latestScanDate"), value: formatDateOnly(result.latest_scan_date, locale) },
    { label: t("latestBarDate"), value: formatDateOnly(result.latest_bar_date, locale) }
  ];

  return (
    <div className="flex flex-col gap-3 text-sm">
      <div>
        <p className="font-semibold text-teal-900">
          {t("scanResultSummary", {
            candidates: candidateCount,
            watch: watchCount,
            total: result.candidates_written
          })}
        </p>
        <p className="mt-1 text-xs text-teal-700">
          {labelFor("status", "candidate")}: {formatNumber(candidateCount, 0, locale)}
          {" · "}
          {labelFor("status", "watch")}: {formatNumber(watchCount, 0, locale)}
        </p>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => (
          <div className="rounded-md border border-teal-100 bg-white/70 px-3 py-2" key={metric.label}>
            <div className="text-xs text-slate-500">{metric.label}</div>
            <div className="mt-0.5 font-semibold text-ink">{metric.value}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-2 text-xs leading-5 text-slate-700 lg:grid-cols-2">
        <div>
          <span className="font-semibold text-ink">{t("symbolsScanned")}:</span>{" "}
          <span>{symbols || "-"}</span>
        </div>
        <div>
          <span className="font-semibold text-ink">{t("skippedSymbols")}:</span>{" "}
          <span>{skippedSymbols}</span>
        </div>
      </div>
    </div>
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

function DecisionFilterControl({
  active,
  onChange
}: {
  active: CandidateDecisionFilter;
  onChange: (filter: CandidateDecisionFilter) => void;
}) {
  const { labelFor, t } = useAppI18n();
  const options: Array<{ value: CandidateDecisionFilter; label: string }> = [
    { value: "candidate", label: labelFor("status", "candidate") },
    { value: "watch", label: labelFor("status", "watch") },
    { value: "all", label: t("allCandidateResults") }
  ];

  return (
    <div
      aria-label={t("candidateDecisionFilter")}
      className="inline-flex h-9 rounded-md border border-line bg-panel p-1"
      role="group"
    >
      {options.map((option) => (
        <button
          aria-pressed={active === option.value}
          className={`focus-ring min-w-16 rounded px-3 text-sm font-semibold transition-colors ${
            active === option.value ? "bg-ink text-white shadow-sm" : "text-slate-600 hover:text-ink"
          }`}
          key={option.value}
          onClick={() => onChange(option.value)}
          type="button"
        >
          {option.label}
        </button>
      ))}
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
