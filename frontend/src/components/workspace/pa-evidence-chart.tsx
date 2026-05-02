"use client";

import { useMemo, useState, type ReactNode } from "react";
import { AlertTriangle, BarChart3, ChevronLeft, ChevronRight, LineChart, ZoomIn, ZoomOut } from "lucide-react";

import { DataState, Field } from "@/components/workspace/common";
import type { PAEvidenceBar, PAEvidenceLevel, PASetupExplain } from "@/lib/api";
import { formatDateOnly, formatNumber, formatValue, numberFromRecord } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

const CHART_WIDTH = 980;
const CHART_HEIGHT = 430;
const PLOT_LEFT = 54;
const PLOT_RIGHT = CHART_WIDTH - 74;
const PRICE_TOP = 34;
const PRICE_BOTTOM = 326;
const VOLUME_TOP = 346;
const VOLUME_BOTTOM = 408;
const WINDOW_OPTIONS = [30, 60, 90];

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
              t={t}
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

          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <Field label={t("latestClose")} value={formatNumber(numberFromRecord(facts, "close"), 2, locale)} />
            <Field label={t("relativeVolume")} value={formatMultiple(numberFromRecord(facts, "relative_volume"), locale)} />
            <Field label={t("sma20")} value={formatNumber(numberFromRecord(facts, "sma_20"), 2, locale)} />
            <Field label={t("sma50")} value={formatNumber(numberFromRecord(facts, "sma_50"), 2, locale)} />
            <Field label={t("sma200")} value={formatNumber(numberFromRecord(facts, "sma_200"), 2, locale)} />
            <Field label={t("closeVs20")} value={formatPercent(numberFromRecord(facts, "distance_to_sma_20_pct"), locale)} />
            <Field label={t("closeVs50")} value={formatPercent(numberFromRecord(facts, "distance_to_sma_50_pct"), locale)} />
            <Field label={t("from52wHigh")} value={formatPercent(numberFromRecord(facts, "pct_from_52w_high"), locale)} />
            <Field label={t("baseDepth")} value={formatPercent(numberFromRecord(facts, "base_depth_60d"), locale)} />
            <Field label={t("rangePosition")} value={formatPercent(numberFromRecord(facts, "close_position_in_range"), locale)} />
            <Field label={t("return3m")} value={formatPercent(numberFromRecord(facts, "return_3m"), locale)} />
            <Field label={t("return6m")} value={formatPercent(numberFromRecord(facts, "return_6m"), locale)} />
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

function ChartControls({
  canMoveNewer,
  canMoveOlder,
  canZoomIn,
  canZoomOut,
  onMoveNewer,
  onMoveOlder,
  onZoomIn,
  onZoomOut,
  t,
  visibleCount
}: {
  canMoveNewer: boolean;
  canMoveOlder: boolean;
  canZoomIn: boolean;
  canZoomOut: boolean;
  onMoveNewer: () => void;
  onMoveOlder: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  t: ReturnType<typeof useAppI18n>["t"];
  visibleCount: number;
}) {
  return (
    <div className="flex items-center gap-1">
      <IconButton disabled={!canMoveOlder} label={t("olderBars")} onClick={onMoveOlder}>
        <ChevronLeft size={15} />
      </IconButton>
      <IconButton disabled={!canMoveNewer} label={t("newerBars")} onClick={onMoveNewer}>
        <ChevronRight size={15} />
      </IconButton>
      <IconButton disabled={!canZoomIn} label={t("zoomIn")} onClick={onZoomIn}>
        <ZoomIn size={15} />
      </IconButton>
      <IconButton disabled={!canZoomOut} label={t("zoomOut")} onClick={onZoomOut}>
        <ZoomOut size={15} />
      </IconButton>
      <span className="ml-1 min-w-12 text-right text-xs font-semibold text-slate-500">{visibleCount}D</span>
    </div>
  );
}

function IconButton({
  children,
  disabled,
  label,
  onClick
}: {
  children: ReactNode;
  disabled: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-slate-700 hover:border-slate-400 disabled:cursor-not-allowed disabled:opacity-40"
      disabled={disabled}
      onClick={onClick}
      title={label}
      type="button"
    >
      {children}
    </button>
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

function PriceEvidenceSvg({
  bars,
  explain,
  locale
}: {
  bars: PAEvidenceBar[];
  explain: PASetupExplain;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
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
  const xFor = (index: number) => PLOT_LEFT + (index / Math.max(1, bars.length - 1)) * (PLOT_RIGHT - PLOT_LEFT);
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
        {[0, 1, 2, 3, 4].map((tick) => {
          const value = domainMax - (tick / 4) * (domainMax - domainMin);
          const y = yFor(value) ?? PRICE_TOP;
          return (
            <g key={tick}>
              <line x1={PLOT_LEFT} x2={PLOT_RIGHT} y1={y} y2={y} stroke="#edf1f4" strokeWidth="1" />
              <text x={CHART_WIDTH - 16} y={y + 4} textAnchor="end" fill="#687383" fontSize="11">
                {formatNumber(value, 2, locale)}
              </text>
            </g>
          );
        })}

        {bars.map((bar, index) => {
          const x = xFor(index);
          const highY = yFor(bar.high);
          const lowY = yFor(bar.low);
          const openY = yFor(bar.open);
          const closeY = yFor(bar.close);
          const isUp = (bar.close ?? 0) >= (bar.open ?? 0);
          const bodyTop = Math.min(openY ?? 0, closeY ?? 0);
          const bodyHeight = Math.max(3, Math.abs((closeY ?? 0) - (openY ?? 0)));
          const volumeHeight = ((bar.volume ?? 0) / volumeMax) * (VOLUME_BOTTOM - VOLUME_TOP);
          const candleWidth = Math.max(4, Math.min(11, (PLOT_RIGHT - PLOT_LEFT) / bars.length * 0.52));
          return (
            <g key={bar.ts}>
              <rect
                x={x - candleWidth / 2}
                y={VOLUME_BOTTOM - volumeHeight}
                width={candleWidth}
                height={volumeHeight}
                fill={isUp ? "#cfe8e3" : "#ead6d2"}
              />
              {highY !== null && lowY !== null ? (
                <line x1={x} x2={x} y1={highY} y2={lowY} stroke={isUp ? "#24756b" : "#a44a3f"} strokeWidth="1.2" />
              ) : null}
              {openY !== null && closeY !== null ? (
                <rect
                  x={x - candleWidth / 2}
                  y={bodyTop}
                  width={candleWidth}
                  height={bodyHeight}
                  rx="1"
                  fill={isUp ? "#2f7f75" : "#b85c50"}
                />
              ) : null}
            </g>
          );
        })}

        <MovingAveragePath bars={bars} color="#0f766e" valueKey="sma_20" xFor={xFor} yFor={yFor} />
        <MovingAveragePath bars={bars} color="#7c6cbb" valueKey="sma_50" xFor={xFor} yFor={yFor} />
        <MovingAveragePath bars={bars} color="#8b97a5" valueKey="sma_200" xFor={xFor} yFor={yFor} />

        {levels.map((level) => {
          const y = yFor(level.value);
          if (y === null) {
            return null;
          }
          const tone = level.key === "trigger_price" ? "#1d766c" : level.key === "initial_stop" ? "#a44a3f" : "#8b6f2a";
          const title = `${labelFor("plan", level.key)}: ${formatNumber(level.value, 2, locale)}`;
          return (
            <g className="cursor-help" key={`${level.source}-${level.key}`}>
              <title>{title}</title>
              <rect x={PLOT_LEFT} y={y - 6} width={PLOT_RIGHT - PLOT_LEFT + 10} height="12" fill="transparent" pointerEvents="all" />
              <line x1={PLOT_LEFT} x2={PLOT_RIGHT} y1={y} y2={y} stroke={tone} strokeDasharray="5 5" strokeWidth="1.4" />
              <circle cx={PLOT_RIGHT} cy={y} r="4.5" fill="#ffffff" stroke={tone} strokeWidth="1.6" />
            </g>
          );
        })}

        <text x={PLOT_LEFT} y="22" fill="#687383" fontSize="12">
          {bars[0] ? formatDateOnly(bars[0].ts, locale) : ""} - {bars[bars.length - 1] ? formatDateOnly(bars[bars.length - 1].ts, locale) : ""}
        </text>
        <text x={PLOT_LEFT} y={VOLUME_TOP + 12} fill="#687383" fontSize="12">
          {t("volume")}
        </text>
        <Legend />
      </svg>
    </div>
  );
}

function Legend() {
  return (
    <g transform={`translate(${PLOT_LEFT}, ${CHART_HEIGHT - 14})`}>
      <LegendItem color="#0f766e" label="20MA" x={0} />
      <LegendItem color="#7c6cbb" label="50MA" x={74} />
      <LegendItem color="#8b97a5" label="200MA" x={148} />
    </g>
  );
}

function LegendItem({ color, label, x }: { color: string; label: string; x: number }) {
  return (
    <g transform={`translate(${x}, 0)`}>
      <line x1="0" x2="20" y1="0" y2="0" stroke={color} strokeWidth="2" />
      <text x="26" y="4" fill="#687383" fontSize="11">
        {label}
      </text>
    </g>
  );
}

function OHLCStrip({ bars, locale }: { bars: PAEvidenceBar[]; locale: Locale }) {
  const { t } = useAppI18n();
  const latest = bars.at(-1);
  if (!latest) {
    return null;
  }

  return (
    <div className="grid gap-2 rounded-md border border-line bg-panel/70 px-3 py-2 text-sm sm:grid-cols-5">
      <MiniMetric label={t("open")} value={formatNumber(latest.open, 2, locale)} />
      <MiniMetric label={t("high")} value={formatNumber(latest.high, 2, locale)} />
      <MiniMetric label={t("low")} value={formatNumber(latest.low, 2, locale)} />
      <MiniMetric label={t("close")} value={formatNumber(latest.close, 2, locale)} />
      <MiniMetric label={t("date")} value={formatDateOnly(latest.ts, locale)} />
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="min-w-0">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="truncate font-semibold text-ink">{formatValue(value)}</div>
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
