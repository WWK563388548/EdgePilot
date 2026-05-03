"use client";

import { AlertTriangle } from "lucide-react";
import { useState } from "react";

import type { PAEvidenceBar, PASetupExplain } from "@/lib/api";
import { formatDateOnly, formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";
import {
  CHART_HEIGHT,
  CHART_WIDTH,
  DATE_AXIS_Y,
  PLOT_LEFT,
  PLOT_RIGHT,
  PRICE_BOTTOM,
  PRICE_TOP,
  VOLUME_BOTTOM,
  VOLUME_TOP
} from "@/components/workspace/organisms/evidence/chart-constants";
import { buildDateTicks } from "@/components/workspace/organisms/evidence/chart-utils";

export function PriceEvidenceSvg({
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
  const [hoveredLevelId, setHoveredLevelId] = useState<string | null>(null);
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
  const levelMarkers = levels
    .map((level) => {
      const y = yFor(level.value);
      if (y === null) {
        return null;
      }
      const tone = level.key === "trigger_price" ? "#1d766c" : level.key === "initial_stop" ? "#8a5d13" : "#6b5ca5";
      const label = labelFor("plan", level.key);
      const shortLabel = level.key === "trigger_price" ? t("entry") : level.key === "initial_stop" ? t("stop") : label;
      const valueLabel = formatNumber(level.value, 2, locale);
      return {
        id: `${level.source}-${level.key}`,
        label,
        labelY: Math.max(PRICE_TOP + 2, Math.min(PRICE_BOTTOM - 24, y - 12)),
        shortLabel,
        tone,
        valueLabel,
        y
      };
    })
    .filter((marker): marker is NonNullable<typeof marker> => Boolean(marker));
  const hoveredLevel = levelMarkers.find((marker) => marker.id === hoveredLevelId) ?? null;
  const dateTicks = buildDateTicks(bars);

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

        {levelMarkers.map((marker) => {
          const isHovered = hoveredLevelId === marker.id;
          return (
            <g
              aria-label={`${marker.label}: ${marker.valueLabel}`}
              className="cursor-help"
              key={marker.id}
              onBlur={() => setHoveredLevelId(null)}
              onFocus={() => setHoveredLevelId(marker.id)}
              onMouseEnter={() => setHoveredLevelId(marker.id)}
              onMouseLeave={() => setHoveredLevelId(null)}
              role="button"
              tabIndex={0}
            >
              <rect
                x={PLOT_LEFT}
                y={marker.y - 8}
                width={PLOT_RIGHT - PLOT_LEFT + 68}
                height="16"
                fill="transparent"
                pointerEvents="all"
              />
              <line
                x1={PLOT_LEFT}
                x2={PLOT_RIGHT}
                y1={marker.y}
                y2={marker.y}
                stroke={marker.tone}
                strokeDasharray="5 5"
                strokeOpacity={isHovered ? "1" : "0.88"}
                strokeWidth={isHovered ? "2.2" : "1.6"}
              />
              <line x1={PLOT_RIGHT} x2={PLOT_RIGHT + 8} y1={marker.y} y2={marker.labelY + 12} stroke={marker.tone} strokeWidth="1.4" />
              <circle cx={PLOT_RIGHT} cy={marker.y} r={isHovered ? "7" : "5.5"} fill={marker.tone} stroke="#ffffff" strokeWidth="2" />
              <rect
                x={PLOT_RIGHT + 10}
                y={marker.labelY}
                width="58"
                height="24"
                rx="6"
                fill="#ffffff"
                stroke={marker.tone}
                strokeWidth={isHovered ? "2" : "1.5"}
              />
              <text
                x={PLOT_RIGHT + 39}
                y={marker.labelY + 16}
                textAnchor="middle"
                fill={marker.tone}
                fontSize="11"
                fontWeight="800"
              >
                {marker.shortLabel}
              </text>
            </g>
          );
        })}
        {hoveredLevel ? <LevelTooltip marker={hoveredLevel} /> : null}

        <text x={PLOT_LEFT} y="22" fill="#687383" fontSize="12">
          {bars[0] ? formatDateOnly(bars[0].ts, locale) : ""} - {bars[bars.length - 1] ? formatDateOnly(bars[bars.length - 1].ts, locale) : ""}
        </text>
        <text x={PLOT_LEFT} y={VOLUME_TOP + 12} fill="#687383" fontSize="12">
          {t("volume")}
        </text>
        <DateAxis ticks={dateTicks} xFor={xFor} locale={locale} />
        <Legend />
      </svg>
    </div>
  );
}

function LevelTooltip({
  marker
}: {
  marker: {
    label: string;
    tone: string;
    valueLabel: string;
    y: number;
  };
}) {
  const tooltipWidth = 170;
  const tooltipHeight = 46;
  const x = PLOT_RIGHT - tooltipWidth - 12;
  const y = Math.max(PRICE_TOP + 4, Math.min(PRICE_BOTTOM - tooltipHeight - 4, marker.y - tooltipHeight - 10));

  return (
    <g pointerEvents="none">
      <rect x={x} y={y} width={tooltipWidth} height={tooltipHeight} rx="7" fill="#16202a" opacity="0.96" />
      <rect x={x} y={y} width="4" height={tooltipHeight} rx="2" fill={marker.tone} />
      <text x={x + 14} y={y + 18} fill="#ffffff" fontSize="12" fontWeight="800">
        {marker.label}
      </text>
      <text x={x + 14} y={y + 35} fill="#d8e0e7" fontSize="12" fontWeight="700">
        {marker.valueLabel}
      </text>
    </g>
  );
}

function DateAxis({
  ticks,
  xFor,
  locale
}: {
  ticks: Array<{ index: number; ts: string }>;
  xFor: (index: number) => number;
  locale: Locale;
}) {
  if (!ticks.length) {
    return null;
  }

  return (
    <g>
      <line x1={PLOT_LEFT} x2={PLOT_RIGHT} y1={DATE_AXIS_Y - 14} y2={DATE_AXIS_Y - 14} stroke="#edf1f4" strokeWidth="1" />
      {ticks.map((tick, tickIndex) => {
        const x = xFor(tick.index);
        const anchor = tickIndex === 0 ? "start" : tickIndex === ticks.length - 1 ? "end" : "middle";
        return (
          <g key={`${tick.index}-${tick.ts}`}>
            <line x1={x} x2={x} y1={DATE_AXIS_Y - 18} y2={DATE_AXIS_Y - 12} stroke="#cfd8e3" strokeWidth="1" />
            <text x={x} y={DATE_AXIS_Y + 2} textAnchor={anchor} fill="#687383" fontSize="11" fontWeight="600">
              {formatDateOnly(tick.ts, locale)}
            </text>
          </g>
        );
      })}
    </g>
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
