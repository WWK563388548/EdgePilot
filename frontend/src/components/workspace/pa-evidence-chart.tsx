"use client";

import { useMemo, useState } from "react";
import { LineChart } from "lucide-react";

import { DataState } from "@/components/workspace/atoms/data-state";
import type { PASetupExplain } from "@/lib/api";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";
import { WINDOW_OPTIONS } from "@/components/workspace/organisms/evidence/chart-constants";
import {
  ChartControls,
  EvidenceMetricsGrid,
  EvidenceNarrative,
  OHLCStrip,
  PriceEvidenceSvg,
  WatchLevelsPanel
} from "@/components/workspace/organisms/evidence";

export function PAEvidencePanel({
  explain,
  loading,
  error,
  locale
}: {
  explain: PASetupExplain | undefined;
  loading: boolean;
  error: boolean;
  locale: Locale;
}) {
  const { t } = useAppI18n();
  const facts = explain?.evidence.latest_facts;
  const levels = explain?.evidence.levels ?? [];
  const bars = explain?.evidence.bars ?? [];
  const [visibleCount, setVisibleCount] = useState(60);
  const [offsetFromEnd, setOffsetFromEnd] = useState(0);
  const normalizedVisibleCount = Math.min(Math.max(20, visibleCount), Math.max(20, bars.length || visibleCount));
  const maxOffset = Math.max(0, bars.length - normalizedVisibleCount);
  const normalizedOffset = Math.min(offsetFromEnd, maxOffset);
  const visibleBars = useMemo(() => {
    if (!bars.length) {
      return [];
    }
    const end = bars.length - normalizedOffset;
    const start = Math.max(0, end - normalizedVisibleCount);
    return bars.slice(start, end);
  }, [bars, normalizedOffset, normalizedVisibleCount]);

  const setWindow = (nextCount: number) => {
    setVisibleCount(nextCount);
    setOffsetFromEnd(0);
  };

  return (
    <section className="border-t border-line pt-3">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <LineChart size={16} className="shrink-0 text-teal" />
          <h3 className="text-sm font-semibold text-ink">{t("chartEvidence")}</h3>
        </div>
        <div className="flex items-center gap-2">
          <DataState isLoading={loading} isError={error} locale={locale} />
          {explain ? (
            <ChartControls
              canMoveNewer={normalizedOffset > 0}
              canMoveOlder={normalizedOffset < maxOffset}
              canZoomIn={normalizedVisibleCount > 20}
              canZoomOut={normalizedVisibleCount < bars.length}
              onMoveNewer={() => setOffsetFromEnd(Math.max(0, normalizedOffset - Math.max(10, Math.round(normalizedVisibleCount / 2))))}
              onMoveOlder={() => setOffsetFromEnd(Math.min(maxOffset, normalizedOffset + Math.max(10, Math.round(normalizedVisibleCount / 2))))}
              onZoomIn={() => setWindow(Math.max(20, Math.round(normalizedVisibleCount * 0.65)))}
              onZoomOut={() => setWindow(Math.min(bars.length, Math.round(normalizedVisibleCount * 1.5)))}
              visibleCount={normalizedVisibleCount}
            />
          ) : null}
        </div>
      </div>

      {explain ? (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {WINDOW_OPTIONS.filter((option) => option <= Math.max(option, bars.length)).map((option) => (
              <button
                className={`focus-ring h-8 rounded-md border px-3 text-xs font-semibold ${
                  normalizedVisibleCount === Math.min(option, bars.length)
                    ? "border-teal bg-teal text-white"
                    : "border-line bg-white text-slate-700 hover:border-slate-400"
                }`}
                key={option}
                onClick={() => setWindow(Math.min(option, bars.length || option))}
                type="button"
              >
                {option}D
              </button>
            ))}
            <button
              className={`focus-ring h-8 rounded-md border px-3 text-xs font-semibold ${
                normalizedVisibleCount === bars.length
                  ? "border-teal bg-teal text-white"
                  : "border-line bg-white text-slate-700 hover:border-slate-400"
              }`}
              onClick={() => setWindow(bars.length || 90)}
              type="button"
            >
              {t("allBars")}
            </button>
          </div>

          <PriceEvidenceSvg bars={visibleBars} explain={explain} locale={locale} />
          <OHLCStrip bars={visibleBars} locale={locale} />
          <EvidenceMetricsGrid facts={facts} locale={locale} />
          <EvidenceNarrative explain={explain} locale={locale} />
          <WatchLevelsPanel levels={levels} locale={locale} />
        </div>
      ) : (
        <div className="rounded-md border border-line bg-panel/70 p-3 text-sm text-slate-600">
          {loading || error ? <DataState isLoading={loading} isError={error} locale={locale} /> : t("noEvidence")}
        </div>
      )}
    </section>
  );
}
