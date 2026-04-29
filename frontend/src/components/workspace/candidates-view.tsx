"use client";

import { useQuery } from "@tanstack/react-query";
import { CalendarDays, Eye, Target, TrendingUp } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { CompactStat, DataState, StatusPill } from "@/components/workspace/common";
import { CandidateDetailPanel } from "@/components/workspace/detail-panels";
import type { Candidate } from "@/lib/api";
import { api } from "@/lib/api";
import { formatDateOnly, formatNumber, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { decisionTone } from "@/lib/presentation";
import { useAppI18n } from "@/lib/use-app-i18n";

export function CandidatesView({
  data,
  loading,
  error,
  locale
}: {
  data: Candidate[];
  loading: boolean;
  error: boolean;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const activeCandidateId = selectedCandidateId ?? data[0]?.candidate_id ?? null;
  const detail = useQuery({
    queryKey: ["candidate-detail", activeCandidateId],
    queryFn: () => api.candidateDetail(activeCandidateId as string),
    enabled: Boolean(activeCandidateId)
  });
  const topScore = useMemo(
    () => data.reduce<number | null>((best, row) => Math.max(best ?? 0, row.score_total ?? 0), null),
    [data]
  );
  const activeCandidate = data.find((row) => row.candidate_id === activeCandidateId);

  useEffect(() => {
    if (selectedCandidateId && !data.some((row) => row.candidate_id === selectedCandidateId)) {
      setSelectedCandidateId(null);
    }
  }, [data, selectedCandidateId]);

  return (
    <section className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        <CompactStat icon={<Target size={18} />} label={t("candidatePool")} value={data.length} />
        <CompactStat icon={<TrendingUp size={18} />} label={t("topScore")} value={formatNumber(topScore, 1, locale)} />
        <CompactStat icon={<Eye size={18} />} label={t("selected")} value={activeCandidate?.symbol_id ?? "-"} />
      </div>

      <section className="grid gap-4 xl:grid-cols-[minmax(420px,0.95fr)_minmax(420px,0.75fr)]">
        <section className="min-w-0 overflow-hidden rounded-md border border-line bg-white shadow-[0_1px_0_rgba(22,32,42,0.04)]">
          <div className="flex items-center justify-between gap-3 border-b border-line bg-white px-4 py-3">
            <div className="flex min-w-0 items-center gap-2">
              <Target size={18} className="shrink-0 text-teal" />
              <div className="min-w-0">
                <h2 className="truncate text-base font-semibold text-ink">{t("candidates")}</h2>
                <p className="text-xs text-slate-500">{t("reviewOnly")}</p>
              </div>
            </div>
            <DataState isLoading={loading} isError={error} locale={locale} />
          </div>

          <div className="divide-y divide-line">
            {!data.length ? (
              <div className="px-4 py-6 text-sm text-slate-600">
                {loading || error ? <DataState isLoading={loading} isError={error} locale={locale} /> : t("noCandidate")}
              </div>
            ) : null}
            {data.map((row) => (
              <CandidateListItem
                active={activeCandidateId === row.candidate_id}
                key={row.candidate_id}
                locale={locale}
                onSelect={() => setSelectedCandidateId(row.candidate_id)}
                row={row}
              />
            ))}
          </div>
        </section>

        <CandidateDetailPanel
          detail={detail.data}
          error={detail.isError}
          locale={locale}
          loading={detail.isLoading}
          onClose={() => setSelectedCandidateId(null)}
          selected={Boolean(activeCandidateId)}
        />
      </section>
    </section>
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
