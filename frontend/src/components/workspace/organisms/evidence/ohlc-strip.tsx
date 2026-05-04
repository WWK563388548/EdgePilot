"use client";

import type { PAEvidenceBar } from "@/lib/api";
import { formatDateOnly, formatNumber, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function OHLCStrip({ bars, locale }: { bars: PAEvidenceBar[]; locale: Locale }) {
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
