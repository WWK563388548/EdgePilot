"use client";

import { formatDetailValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function PlanFields({
  title,
  data,
  locale,
  omitKeys = []
}: {
  title: string;
  data: Record<string, unknown> | null | undefined;
  locale: Locale;
  omitKeys?: string[];
}) {
  const { labelFor } = useAppI18n();
  const entries = Object.entries(data ?? {}).filter(([key]) => !omitKeys.includes(key));

  return (
    <section className="border-t border-line pt-3">
      <h3 className="mb-2 text-sm font-semibold text-ink">{title}</h3>
      {entries.length ? (
        <dl className="grid gap-2">
          {entries.map(([key, value]) => (
            <div
              key={key}
              className="grid gap-1 rounded-md border border-line bg-panel/70 px-3 py-2 text-sm sm:grid-cols-[8rem_minmax(0,1fr)] sm:gap-3"
            >
              <dt className="min-w-0 break-words text-slate-500">{labelFor("plan", key)}</dt>
              <dd className="min-w-0 break-words font-semibold leading-6 text-ink">
                {formatDetailValue(value, locale, labelFor)}
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-sm text-slate-500">-</p>
      )}
    </section>
  );
}
