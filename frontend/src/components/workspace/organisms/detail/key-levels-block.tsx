"use client";

import { Field } from "@/components/workspace/atoms/field";
import type { Candidate, PASetup } from "@/lib/api";
import { formatNumber, numberFromRecord, stringFromRecord } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function KeyLevelsBlock({
  candidate,
  setup,
  entryPlan,
  exitPlan,
  locale
}: {
  candidate?: Candidate | null;
  setup?: PASetup | null;
  entryPlan: Record<string, unknown> | null | undefined;
  exitPlan: Record<string, unknown> | null | undefined;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const trigger = numberFromRecord(entryPlan, "trigger_price") ?? candidate?.entry_trigger ?? null;
  const stop = numberFromRecord(exitPlan, "initial_stop") ?? candidate?.initial_stop ?? null;
  const triggerType = stringFromRecord(entryPlan, "trigger_type");

  return (
    <section className="border-t border-line pt-3">
      <h3 className="mb-2 text-sm font-semibold text-ink">{t("keyLevels")}</h3>
      <dl className="grid grid-cols-2 gap-3">
        <Field label={t("entry")} value={formatNumber(trigger, 2, locale)} />
        <Field label={t("stop")} value={formatNumber(stop, 2, locale)} />
        <Field label={labelFor("plan", "trigger_type")} value={labelFor("plan", triggerType)} />
        <Field label={t("validation")} value={labelFor("status", setup?.validation_status)} />
      </dl>
    </section>
  );
}
