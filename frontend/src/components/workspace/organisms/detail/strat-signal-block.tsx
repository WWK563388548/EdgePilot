"use client";

import { GitBranch } from "lucide-react";

import { Field } from "@/components/workspace/atoms/field";
import { StatusPill } from "@/components/workspace/atoms/status-pill";
import { DetailFieldPanel } from "@/components/workspace/organisms/detail/detail-field-panel";
import type { StratSignal } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function StratSignalBlock({
  locale,
  signal
}: {
  locale: Locale;
  signal: StratSignal | null | undefined;
}) {
  const { labelFor, t } = useAppI18n();

  if (!signal) {
    return (
      <section className="rounded-md border border-line bg-panel/45 px-3 py-3">
        <div className="flex items-center gap-2">
          <GitBranch className="text-teal" size={18} />
          <h3 className="text-sm font-semibold text-ink">{t("stratTrigger")}</h3>
        </div>
        <p className="mt-2 text-sm text-slate-600">{t("stratNoSignal")}</p>
      </section>
    );
  }

  const continuity = signal.timeframe_continuity
    ? Object.entries(signal.timeframe_continuity)
        .map(([timeframe, state]) => `${labelFor("plan", timeframe)}: ${labelFor("plan", state)}`)
        .join(" / ")
    : "-";

  return (
    <section className="rounded-md border border-teal/20 bg-teal-50/30 px-3 py-3">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <GitBranch className="text-teal" size={18} />
        <h3 className="text-sm font-semibold text-ink">{t("stratTrigger")}</h3>
        <StatusPill label={signal.bar_type} tone="neutral" />
        {signal.pattern ? (
          <StatusPill label={labelFor("plan", signal.pattern)} tone="good" />
        ) : null}
      </div>

      <p className="mb-3 text-sm leading-6 text-slate-700">{t("stratNoStandalone")}</p>

      <DetailFieldPanel title={t("stratTrigger")}>
        <Field label={t("stratBar")} value={labelFor("plan", signal.bar_type)} />
        <Field label={t("stratPattern")} value={labelFor("plan", signal.pattern)} />
        <Field label={t("stratDirection")} value={labelFor("plan", signal.direction)} />
        <Field
          label={t("stratTriggerPrice")}
          value={formatNumber(signal.trigger_price, 2, locale)}
        />
        <Field
          label={t("stratTriggerStop")}
          value={formatNumber(signal.trigger_stop, 2, locale)}
        />
        <Field label={t("detected")} value={formatDate(signal.ts, locale)} />
        <Field label={t("stratContinuity")} value={continuity} />
        <Field label={t("invalidation")} value={labelFor("plan", signal.invalidation)} />
      </DetailFieldPanel>
    </section>
  );
}
