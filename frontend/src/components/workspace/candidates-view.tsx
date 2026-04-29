"use client";

import { useQuery } from "@tanstack/react-query";
import { Eye, Target, TrendingUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { CompactStat, DataState, StatusPill, TableShell } from "@/components/workspace/common";
import { CandidateDetailPanel } from "@/components/workspace/detail-panels";
import type { Candidate } from "@/lib/api";
import { api } from "@/lib/api";
import { formatNumber, formatValue } from "@/lib/format";
import { labelFor, t, type Locale } from "@/lib/i18n";
import { decisionTone } from "@/lib/presentation";

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
        <CompactStat icon={<Target size={18} />} label={t(locale, "candidatePool")} value={data.length} />
        <CompactStat icon={<TrendingUp size={18} />} label={t(locale, "topScore")} value={formatNumber(topScore, 1, locale)} />
        <CompactStat icon={<Eye size={18} />} label={t(locale, "selected")} value={activeCandidate?.symbol_id ?? "-"} />
      </div>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(360px,440px)]">
        <TableShell title={t(locale, "candidates")} loading={loading} error={error} locale={locale}>
          <table className="min-w-full table-fixed text-left text-sm">
            <thead className="bg-panel text-xs uppercase text-slate-500">
              <tr>
                <th className="w-24 px-4 py-3">{t(locale, "symbol")}</th>
                <th className="w-44 px-4 py-3">{t(locale, "setup")}</th>
                <th className="w-20 px-4 py-3">{t(locale, "grade")}</th>
                <th className="w-32 px-4 py-3">{t(locale, "validation")}</th>
                <th className="w-24 px-4 py-3">{t(locale, "score")}</th>
                <th className="w-28 px-4 py-3">{t(locale, "decision")}</th>
                <th className="w-32 px-4 py-3">{t(locale, "entry")}</th>
                <th className="w-32 px-4 py-3">{t(locale, "stop")}</th>
                <th className="w-32 px-4 py-3">{t(locale, "scanDate")}</th>
                <th className="w-20 px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {!data.length ? (
                <tr>
                  <td className="px-4 py-6 text-sm text-slate-600" colSpan={10}>
                    {loading || error ? <DataState isLoading={loading} isError={error} locale={locale} /> : t(locale, "noCandidate")}
                  </td>
                </tr>
              ) : null}
              {data.map((row) => (
                <tr
                  key={row.candidate_id}
                  className={`border-t border-line transition-colors hover:bg-panel/70 ${
                    activeCandidateId === row.candidate_id ? "bg-teal-50/60" : ""
                  }`}
                >
                  <td className="px-4 py-3 font-semibold text-ink">{row.symbol_id}</td>
                  <td className="truncate px-4 py-3" title={row.setup_type ?? row.strategy_name}>
                    {row.setup_type ? labelFor(locale, "setup", row.setup_type) : row.strategy_name}
                  </td>
                  <td className="px-4 py-3">{formatValue(row.pa_setup_grade)}</td>
                  <td className="px-4 py-3">
                    <StatusPill
                      label={labelFor(locale, "status", row.validation_status ?? "unlinked")}
                      tone={decisionTone(row.validation_status)}
                    />
                  </td>
                  <td className="px-4 py-3 font-medium text-ink">{formatNumber(row.score_total, 1, locale)}</td>
                  <td className="px-4 py-3">
                    <StatusPill label={labelFor(locale, "status", row.decision ?? "unknown")} tone={decisionTone(row.decision)} />
                  </td>
                  <td className="px-4 py-3">{formatNumber(row.entry_trigger, 2, locale)}</td>
                  <td className="px-4 py-3">{formatNumber(row.initial_stop, 2, locale)}</td>
                  <td className="px-4 py-3">{row.scan_date}</td>
                  <td className="px-4 py-3">
                    <button
                      className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-slate-700 hover:border-slate-400"
                      onClick={() => setSelectedCandidateId(row.candidate_id)}
                      title={t(locale, "openDetail")}
                      type="button"
                    >
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>

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
