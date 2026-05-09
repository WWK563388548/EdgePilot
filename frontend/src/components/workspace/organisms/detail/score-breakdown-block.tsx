"use client";

import { formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function ScoreBreakdownBlock({
  data,
  locale
}: {
  data: Record<string, unknown> | null | undefined;
  locale: Locale;
}) {
  const { scoreMeta, t } = useAppI18n();
  const order = [
    "total",
    "momentum_6m",
    "momentum_3m",
    "momentum_12m",
    "trend",
    "benchmark_relative_strength",
    "overextension_penalty",
    "relative_strength",
    "volume_liquidity",
    "base_setup",
    "market_context",
    "fundamental_lite"
  ];
  const maxScoreByKey: Record<string, number> = {
    total: 100,
    trend: 25,
    momentum_6m: 30,
    momentum_3m: 30,
    momentum_12m: 15,
    benchmark_relative_strength: 10,
    overextension_penalty: 20,
    relative_strength: 25,
    volume_liquidity: 15,
    base_setup: 15,
    market_context: 10,
    fundamental_lite: 10
  };
  const entries = Object.entries(data ?? {})
    .filter(([, value]) => typeof value === "number")
    .sort(([left], [right]) => {
      const leftIndex = order.indexOf(left);
      const rightIndex = order.indexOf(right);
      return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
    });

  return (
    <section className="border-t border-line pt-3">
      <h3 className="mb-3 text-sm font-semibold text-ink">{t("scoreBreakdown")}</h3>
      {entries.length ? (
        <div className="grid gap-3">
          {entries.map(([key, value]) => {
            const meta = scoreMeta(key);
            const score = typeof value === "number" ? value : null;
            const maxScore = maxScoreByKey[key] ?? 100;
            const barWidth = Math.max(0, Math.min(100, (Math.abs(score ?? 0) / maxScore) * 100));
            const barColor = score !== null && score < 0 ? "bg-rose-500" : "bg-teal";
            return (
              <div key={key} className="grid grid-cols-[minmax(0,1fr)_3.5rem] gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-medium text-ink">{meta.label}</div>
                  {meta.description ? <div className="mt-0.5 text-xs leading-5 text-slate-500">{meta.description}</div> : null}
                  <div className="mt-2 h-1.5 overflow-hidden rounded bg-slate-100">
                    <div
                      className={`h-full rounded ${barColor}`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
                <div className="text-right text-sm font-semibold text-ink">{formatNumber(score, 1, locale)}</div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-slate-500">-</p>
      )}
    </section>
  );
}
