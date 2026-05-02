"use client";

import { AlertTriangle, BarChart3, LineChart } from "lucide-react";

import { DataState, Field } from "@/components/workspace/common";
import type { PAEvidenceBar, PAEvidenceLevel, PASetupExplain } from "@/lib/api";
import { formatDateOnly, formatNumber, numberFromRecord } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

const CHART_WIDTH = 760;
const CHART_HEIGHT = 260;
const PRICE_TOP = 16;
const PRICE_BOTTOM = 210;
const VOLUME_TOP = 218;
const VOLUME_BOTTOM = 252;

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
  const { labelFor, t } = useAppI18n();
  const facts = explain?.evidence.latest_facts;
  const levels = explain?.evidence.levels ?? [];

  return (
    <section className="border-t border-line pt-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <LineChart size={16} className="shrink-0 text-teal" />
          <h3 className="text-sm font-semibold text-ink">{t("chartEvidence")}</h3>
        </div>
        <DataState isLoading={loading} isError={error} locale={locale} />
      </div>

      {explain ? (
        <div className="space-y-3">
          <PriceEvidenceSvg explain={explain} locale={locale} />

          <div className="grid grid-cols-2 gap-3">
            <Field label={t("latestClose")} value={formatNumber(numberFromRecord(facts, "close"), 2, locale)} />
            <Field label={t("relativeVolume")} value={formatMultiple(numberFromRecord(facts, "relative_volume"), locale)} />
            <Field label={t("sma20")} value={formatNumber(numberFromRecord(facts, "sma_20"), 2, locale)} />
            <Field label={t("sma50")} value={formatNumber(numberFromRecord(facts, "sma_50"), 2, locale)} />
            <Field label={t("closeVs20")} value={formatPercent(numberFromRecord(facts, "distance_to_sma_20_pct"), locale)} />
            <Field label={t("from52wHigh")} value={formatPercent(numberFromRecord(facts, "pct_from_52w_high"), locale)} />
          </div>

          <EvidenceNarrative explain={explain} locale={locale} />

          <section className="rounded-md border border-line bg-panel/70 px-3 py-2">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
              <BarChart3 size={15} className="text-teal" />
              {t("watchLevels")}
            </div>
            <dl className="grid gap-2">
              {levels.length ? (
                levels.map((level) => (
                  <div key={`${level.source}-${level.key}`} className="grid grid-cols-[minmax(0,1fr)_5rem] gap-3 text-sm">
                    <dt className="min-w-0 truncate text-slate-500">{labelFor("plan", level.key)}</dt>
                    <dd className="text-right font-semibold text-ink">{formatNumber(level.value, 2, locale)}</dd>
                  </div>
                ))
              ) : (
                <div className="text-sm text-slate-500">-</div>
              )}
            </dl>
          </section>
        </div>
      ) : (
        <div className="rounded-md border border-line bg-panel/70 p-3 text-sm text-slate-600">
          {loading || error ? <DataState isLoading={loading} isError={error} locale={locale} /> : t("noEvidence")}
        </div>
      )}
    </section>
  );
}

function EvidenceNarrative({ explain, locale }: { explain: PASetupExplain; locale: Locale }) {
  const { t } = useAppI18n();
  const facts = explain.evidence.latest_facts;
  const score = numberFromRecord(explain.score_breakdown, "total");
  const relativeVolume = numberFromRecord(facts, "relative_volume");
  const trigger = explain.evidence.levels.find((level) => level.key === "trigger_price")?.value ?? null;
  const stop = explain.evidence.levels.find((level) => level.key === "initial_stop")?.value ?? null;
  const bullets = [
    score !== null && score >= 75 ? t("evidenceScoreStrong", { score: formatNumber(score, 1, locale) }) : null,
    facts?.above_sma_20 && facts?.above_sma_50 ? t("evidenceTrendAbove") : null,
    relativeVolume !== null && relativeVolume >= 1
      ? t("evidenceVolumeSupport", { volume: formatMultiple(relativeVolume, locale) })
      : relativeVolume !== null
        ? t("evidenceVolumeWeak", { volume: formatMultiple(relativeVolume, locale) })
        : null,
    trigger !== null && stop !== null
      ? t("evidencePlan", {
          stop: formatNumber(stop, 2, locale),
          trigger: formatNumber(trigger, 2, locale)
        })
      : null,
    explain.validation_status === "shadow_only" ? t("evidenceShadowOnly") : null
  ].filter((item): item is string => Boolean(item));

  return (
    <section className="rounded-md border border-teal-200 bg-teal-50/60 px-3 py-2">
      <h4 className="mb-2 text-sm font-semibold text-ink">{t("evidenceWhy")}</h4>
      <ul className="grid gap-1.5 text-sm leading-6 text-slate-700">
        {bullets.map((bullet) => (
          <li key={bullet}>{bullet}</li>
        ))}
      </ul>
    </section>
  );
}

function PriceEvidenceSvg({ explain, locale }: { explain: PASetupExplain; locale: Locale }) {
  const { labelFor, t } = useAppI18n();
  const bars = explain.evidence.bars.slice(-70);
  const levels = explain.evidence.levels;
  const priceValues = bars.flatMap((bar) => [bar.open, bar.high, bar.low, bar.close, bar.sma_20, bar.sma_50, bar.sma_200]);
  const levelValues = levels.map((level) => level.value);
  const finiteValues = [...priceValues, ...levelValues].filter((value): value is number => typeof value === "number" && Number.isFinite(value));

  if (bars.length < 2 || !finiteValues.length) {
    return (
      <div className="rounded-md border border-line bg-panel/70 p-3 text-sm text-slate-600">
        <AlertTriangle size={15} className="mr-1 inline text-amber-600" />
        {t("notEnoughEvidence")}
      </div>
    );
  }

  const minPrice = Math.min(...finiteValues);
  const maxPrice = Math.max(...finiteValues);
  const padding = Math.max((maxPrice - minPrice) * 0.08, maxPrice * 0.004, 1);
  const domainMin = minPrice - padding;
  const domainMax = maxPrice + padding;
  const volumeMax = Math.max(...bars.map((bar) => bar.volume ?? 0), 1);
  const xFor = (index: number) => 18 + (index / Math.max(1, bars.length - 1)) * (CHART_WIDTH - 36);
  const yFor = (value: number | null | undefined) => {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      return null;
    }
    return PRICE_BOTTOM - ((value - domainMin) / (domainMax - domainMin || 1)) * (PRICE_BOTTOM - PRICE_TOP);
  };

  return (
    <div className="overflow-hidden rounded-md border border-line bg-white">
      <svg className="block h-auto w-full" viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} role="img" aria-label={t("chartEvidence")}>
        <rect x="0" y="0" width={CHART_WIDTH} height={CHART_HEIGHT} fill="#ffffff" />
        {[0, 1, 2, 3].map((tick) => {
          const y = PRICE_TOP + (tick / 3) * (PRICE_BOTTOM - PRICE_TOP);
          return <line key={tick} x1="12" x2={CHART_WIDTH - 12} y1={y} y2={y} stroke="#edf1f4" strokeWidth="1" />;
        })}

        {bars.map((bar, index) => {
          const x = xFor(index);
          const highY = yFor(bar.high);
          const lowY = yFor(bar.low);
          const openY = yFor(bar.open);
          const closeY = yFor(bar.close);
          const isUp = (bar.close ?? 0) >= (bar.open ?? 0);
          const bodyTop = Math.min(openY ?? 0, closeY ?? 0);
          const bodyHeight = Math.max(2, Math.abs((closeY ?? 0) - (openY ?? 0)));
          const volumeHeight = ((bar.volume ?? 0) / volumeMax) * (VOLUME_BOTTOM - VOLUME_TOP);
          return (
            <g key={bar.ts}>
              <rect
                x={x - 2}
                y={VOLUME_BOTTOM - volumeHeight}
                width="4"
                height={volumeHeight}
                fill={isUp ? "#cfe8e3" : "#ead6d2"}
              />
              {highY !== null && lowY !== null ? (
                <line x1={x} x2={x} y1={highY} y2={lowY} stroke={isUp ? "#24756b" : "#a44a3f"} strokeWidth="1.2" />
              ) : null}
              {openY !== null && closeY !== null ? (
                <rect
                  x={x - 3}
                  y={bodyTop}
                  width="6"
                  height={bodyHeight}
                  rx="1"
                  fill={isUp ? "#2f7f75" : "#b85c50"}
                />
              ) : null}
            </g>
          );
        })}

        <MovingAveragePath bars={bars} color="#2f7f75" valueKey="sma_20" xFor={xFor} yFor={yFor} />
        <MovingAveragePath bars={bars} color="#7c6cbb" valueKey="sma_50" xFor={xFor} yFor={yFor} />
        <MovingAveragePath bars={bars} color="#8b97a5" valueKey="sma_200" xFor={xFor} yFor={yFor} />

        {levels.map((level) => {
          const y = yFor(level.value);
          if (y === null) {
            return null;
          }
          const tone = level.key === "trigger_price" ? "#1d766c" : level.key === "initial_stop" ? "#a44a3f" : "#8b6f2a";
          return (
            <g key={`${level.source}-${level.key}`}>
              <line x1="12" x2={CHART_WIDTH - 12} y1={y} y2={y} stroke={tone} strokeDasharray="5 5" strokeWidth="1.2" />
              <text x={CHART_WIDTH - 14} y={Math.max(12, y - 4)} textAnchor="end" fill={tone} fontSize="11" fontWeight="600">
                {labelFor("plan", level.key)} {formatNumber(level.value, 2, locale)}
              </text>
            </g>
          );
        })}

        <text x="16" y="20" fill="#687383" fontSize="11">
          {bars[0] ? formatDateOnly(bars[0].ts, locale) : ""} - {bars[bars.length - 1] ? formatDateOnly(bars[bars.length - 1].ts, locale) : ""}
        </text>
        <text x="16" y="248" fill="#687383" fontSize="11">
          {t("volume")}
        </text>
      </svg>
    </div>
  );
}

function MovingAveragePath({
  bars,
  valueKey,
  color,
  xFor,
  yFor
}: {
  bars: PAEvidenceBar[];
  valueKey: "sma_20" | "sma_50" | "sma_200";
  color: string;
  xFor: (index: number) => number;
  yFor: (value: number | null | undefined) => number | null;
}) {
  const points = bars
    .map((bar, index) => {
      const y = yFor(bar[valueKey]);
      return y === null ? null : `${xFor(index)},${y}`;
    })
    .filter((point): point is string => Boolean(point));

  if (points.length < 2) {
    return null;
  }

  return <polyline points={points.join(" ")} fill="none" stroke={color} strokeWidth="1.5" />;
}

function formatPercent(value: number | null, locale: Locale) {
  if (value === null) {
    return "-";
  }
  return `${formatNumber(value * 100, 1, locale)}%`;
}

function formatMultiple(value: number | null, locale: Locale) {
  if (value === null) {
    return "-";
  }
  return `${formatNumber(value, 2, locale)}x`;
}
