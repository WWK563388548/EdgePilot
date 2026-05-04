"use client";

import type { PASetupExplain } from "@/lib/api";
import { formatNumber, numberFromRecord } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";
import { formatMultiple } from "@/components/workspace/organisms/evidence/chart-format";

export function EvidenceNarrative({ explain, locale }: { explain: PASetupExplain; locale: Locale }) {
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
