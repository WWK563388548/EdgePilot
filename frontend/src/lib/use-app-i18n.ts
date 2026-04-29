"use client";

import { useTranslations } from "next-intl";

import type { Candidate, PASetup } from "@/lib/api";
import { numberFromRecord } from "@/lib/format";

type LabelGroup = "setup" | "status" | "plan";

export function useAppI18n() {
  const t = useTranslations("ui");
  const setupLabels = useTranslations("labels.setup");
  const statusLabels = useTranslations("labels.status");
  const planLabels = useTranslations("labels.plan");
  const scoreLabels = useTranslations("score");
  const narratives = useTranslations("narratives");

  const labelFor = (group: LabelGroup, value: string | null | undefined) => {
    if (!value) {
      return "-";
    }
    const source = group === "setup" ? setupLabels : group === "status" ? statusLabels : planLabels;
    return source.has(value) ? source(value) : value;
  };

  const scoreMeta = (key: string) => {
    const labelKey = `${key}.label`;
    const descriptionKey = `${key}.description`;
    return {
      label: scoreLabels.has(labelKey) ? scoreLabels(labelKey) : key,
      description: scoreLabels.has(descriptionKey) ? scoreLabels(descriptionKey) : ""
    };
  };

  const setupNarrative = (setup: PASetup | null | undefined, candidate?: Candidate | null) => {
    if (!setup) {
      return narratives("noSetup");
    }

    const setupName = labelFor("setup", setup.setup_type);
    const validation = labelFor("status", setup.validation_status);
    const score = setup.pa_quality_score ?? candidate?.score_total ?? "-";
    const trigger = numberFromRecord(setup.entry_plan, "trigger_price") ?? candidate?.entry_trigger ?? "-";
    const stop = numberFromRecord(setup.exit_plan, "initial_stop") ?? candidate?.initial_stop ?? "-";
    const decision = labelFor("status", candidate?.decision ?? setup.status);

    return narratives("setup", {
      decision,
      score,
      setupName,
      stop,
      symbol: setup.symbol_id,
      trigger,
      validation
    });
  };

  return {
    labelFor,
    scoreMeta,
    setupNarrative,
    t
  };
}
