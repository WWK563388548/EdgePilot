"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ClipboardCheck, Loader2 } from "lucide-react";
import { useState } from "react";

import { Field } from "@/components/workspace/atoms/field";
import type { Candidate, PASetup, Position } from "@/lib/api";
import { api } from "@/lib/api";
import { formatNumber, numberFromRecord } from "@/lib/format";
import { localeTag, type Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function CandidateTradePlanCard({
  candidate,
  setup,
  entryPlan,
  exitPlan,
  locale
}: {
  candidate: Candidate;
  setup?: PASetup | null;
  entryPlan: Record<string, unknown> | null | undefined;
  exitPlan: Record<string, unknown> | null | undefined;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const [createdPlan, setCreatedPlan] = useState<Position | null>(null);
  const trigger = numberFromRecord(entryPlan, "trigger_price") ?? candidate.entry_trigger;
  const stop = numberFromRecord(exitPlan, "initial_stop") ?? candidate.initial_stop;
  const validationStatus = setup?.validation_status ?? candidate.validation_status;
  const riskDistance =
    trigger !== null && trigger !== undefined && stop !== null && stop !== undefined
      ? (trigger - stop) / trigger
      : null;
  const missingPlanLevels = trigger === null || trigger === undefined || stop === null || stop === undefined;
  const createPlan = useMutation({
    mutationFn: () => api.createCandidatePlan(candidate.candidate_id),
    onSuccess: async (position) => {
      setCreatedPlan(position);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      ]);
    }
  });

  return (
    <section className="border-t border-line pt-3">
      <div className="flex flex-col gap-3 rounded-md border border-teal/20 bg-teal-50/45 p-4 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-teal/20 bg-white text-teal">
              <ClipboardCheck size={17} />
            </span>
            <div>
              <h3 className="text-sm font-semibold text-ink">{t("tradePlan")}</h3>
              <p className="mt-0.5 text-xs text-slate-600">
                {validationStatus === "shadow_only" ? t("planShadowOnlyNote") : t("tradePlanHint")}
              </p>
            </div>
          </div>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Field label={t("plannedEntry")} value={formatNumber(trigger, 2, locale)} />
            <Field label={t("plannedStop")} value={formatNumber(stop, 2, locale)} />
            <Field
              label={t("riskDistance")}
              value={riskDistance === null ? "-" : formatPercent(riskDistance, locale)}
            />
            <Field label={t("planStatus")} value={labelFor("status", createdPlan?.status ?? "planned")} />
          </dl>
          {missingPlanLevels ? (
            <p className="mt-3 text-sm font-medium text-rose-700">{t("missingPlanLevels")}</p>
          ) : createPlan.isError ? (
            <p className="mt-3 text-sm font-medium text-rose-700">{t("planCreateFailed")}</p>
          ) : createdPlan ? (
            <p className="mt-3 text-sm font-medium text-teal-800">
              {t("planCreated", { position: createdPlan.position_id })}
            </p>
          ) : null}
        </div>
        <button
          className="focus-ring inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
          disabled={missingPlanLevels || createPlan.isPending}
          onClick={() => createPlan.mutate()}
          title={missingPlanLevels ? t("missingPlanLevels") : t("planButtonHelp")}
          type="button"
        >
          {createPlan.isPending ? <Loader2 className="animate-spin" size={16} /> : <ClipboardCheck size={16} />}
          {createPlan.isPending ? t("creatingPlan") : t("createPaperPlan")}
        </button>
      </div>
    </section>
  );
}

function formatPercent(value: number, locale: Locale) {
  return new Intl.NumberFormat(localeTag[locale], {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
    style: "percent"
  }).format(value);
}
