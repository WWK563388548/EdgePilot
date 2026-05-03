"use client";

import type { Candidate, PASetup } from "@/lib/api";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function ExplanationBlock({
  locale,
  setup,
  candidate
}: {
  locale: Locale;
  setup: PASetup | null | undefined;
  candidate?: Candidate | null;
}) {
  const { setupNarrative, t } = useAppI18n();

  return (
    <section className="rounded-md border border-teal-200 bg-teal-50/70 p-3">
      <h3 className="mb-2 text-sm font-semibold text-ink">{t("plainExplanation")}</h3>
      <p className="text-sm leading-6 text-slate-700">{setupNarrative(setup, candidate)}</p>
    </section>
  );
}
