"use client";

import { BarChart3 } from "lucide-react";

import type { PAEvidenceLevel } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function WatchLevelsPanel({
  levels,
  locale
}: {
  levels: PAEvidenceLevel[];
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();

  return (
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
  );
}
