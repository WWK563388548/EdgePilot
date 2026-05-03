"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, RefreshCw, Target, TrendingUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { CompactStat } from "@/components/workspace/atoms/stat-card";
import { CandidateDetailPanel } from "@/components/workspace/detail-panels";
import { DataState } from "@/components/workspace/atoms/data-state";
import {
  DecisionFilterControl,
  type CandidateDecisionFilter
} from "@/components/workspace/molecules/candidate-decision-filter";
import {
  ScanResultPanel,
  type AccountScanResult
} from "@/components/workspace/molecules/scan-result-panel";
import { ScanActionsHelp } from "@/components/workspace/molecules/scan-actions-help";
import { CandidateList } from "@/components/workspace/organisms/candidate-list";
import type { Candidate } from "@/lib/api";
import { api } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export type { CandidateDecisionFilter } from "@/components/workspace/molecules/candidate-decision-filter";

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
  const { t } = useAppI18n();
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

          <CandidateList
            activeCandidateId={activeCandidateId}
            data={data}
            decisionFilter={decisionFilter}
            error={error}
            hasNextPage={hasNextPage}
            loading={loading}
            locale={locale}
            onPageChange={onPageChange}
            onSelect={(candidateId) => {
              setSelectedCandidateId(candidateId);
              setDetailOpen(true);
            }}
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
