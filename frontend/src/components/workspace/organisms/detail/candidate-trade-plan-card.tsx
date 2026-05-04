"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardCheck, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Field } from "@/components/workspace/atoms/field";
import type { Candidate, PASetup, Position } from "@/lib/api";
import { ApiError, api } from "@/lib/api";
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
  const candidatePlan = useQuery({
    queryKey: ["candidate-plan", candidate.candidate_id],
    queryFn: () => api.candidatePlan(candidate.candidate_id),
    enabled: !missingPlanLevels
  });
  const planPreview = useQuery({
    queryKey: ["candidate-plan-preview", candidate.candidate_id],
    queryFn: () => api.candidatePlanPreview(candidate.candidate_id)
  });
  const createPlan = useMutation({
    mutationFn: () =>
      api.createCandidatePlan(candidate.candidate_id, {
        quantity: planPreview.data?.suggested_quantity ?? undefined
      }),
    onSuccess: async (position) => {
      setCreatedPlan(position);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["candidate-plan", candidate.candidate_id] }),
        queryClient.invalidateQueries({ queryKey: ["candidate-plan-preview", candidate.candidate_id] }),
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      ]);
    }
  });
  const { reset: resetCreatePlan } = createPlan;
  useEffect(() => {
    setCreatedPlan(null);
    resetCreatePlan();
  }, [candidate.candidate_id, resetCreatePlan]);
  const trackedPlan = createdPlan ?? candidatePlan.data ?? null;
  const planAlreadyTracked = trackedPlan !== null;
  const guardrails = planPreview.data?.guardrails ?? [];
  const blocked = guardrails.some((notice) => notice.level === "block");
  const planErrorMessage = createPlan.error
    ? planCreateErrorMessage(createPlan.error, t)
    : null;

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
            <Field label={t("planStatus")} value={labelFor("status", trackedPlan?.status ?? "planned")} />
            <Field
              label={t("suggestedQuantity")}
              value={formatNumber(planPreview.data?.suggested_quantity, 0, locale)}
            />
            <Field
              label={t("maxRiskAmount")}
              value={formatMoney(planPreview.data?.max_risk_amount, locale)}
            />
            <Field
              label={t("plannedRisk")}
              value={
                planPreview.data?.planned_risk_amount === null ||
                planPreview.data?.planned_risk_amount === undefined
                  ? "-"
                  : `${formatMoney(planPreview.data.planned_risk_amount, locale)} / ${formatPercent(
                      planPreview.data.planned_risk_pct ?? 0,
                      locale
                    )}`
              }
            />
            <Field
              label={t("riskSettingsShort")}
              value={`${formatMoney(planPreview.data?.account_equity, locale)} · ${formatPercent(
                planPreview.data?.max_risk_per_trade_pct ?? 0,
                locale
              )}`}
            />
          </dl>
          {guardrails.length ? (
            <div className="mt-3 grid gap-2">
              {guardrails.map((notice) => (
                <div
                  className={`rounded-md border px-3 py-2 text-xs font-medium ${
                    notice.level === "block"
                      ? "border-rose-200 bg-rose-50 text-rose-800"
                      : notice.level === "warning"
                        ? "border-amber-200 bg-amber-50 text-amber-900"
                        : "border-slate-200 bg-white text-slate-700"
                  }`}
                  key={`${notice.level}-${notice.code}`}
                >
                  {labelFor("plan", notice.code)}
                </div>
              ))}
            </div>
          ) : null}
          {missingPlanLevels ? (
            <p className="mt-3 text-sm font-medium text-rose-700">{t("missingPlanLevels")}</p>
          ) : createPlan.isError ? (
            <p className="mt-3 text-sm font-medium text-rose-700">{planErrorMessage}</p>
          ) : planAlreadyTracked ? (
            <div className="mt-3 flex flex-col gap-1 text-sm">
              <p className="font-medium text-teal-800">
                {t("planAlreadyTracked", { position: trackedPlan.position_id })}
              </p>
              <p className="text-slate-600">{t("planNextStep")}</p>
            </div>
          ) : null}
        </div>
        <button
          className="focus-ring inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
          disabled={
            missingPlanLevels ||
            blocked ||
            candidatePlan.isLoading ||
            planPreview.isLoading ||
            planAlreadyTracked ||
            createPlan.isPending
          }
          onClick={() => createPlan.mutate()}
          title={
            missingPlanLevels
              ? t("missingPlanLevels")
              : blocked
                ? t("planBlockedHelp")
              : planAlreadyTracked
                ? t("planAlreadyTrackedHelp")
                : t("planButtonHelp")
          }
          type="button"
        >
          {createPlan.isPending ? <Loader2 className="animate-spin" size={16} /> : <ClipboardCheck size={16} />}
          {createPlan.isPending
            ? t("creatingPlan")
            : planAlreadyTracked
              ? t("planAlreadyTrackedButton")
              : t("createPaperPlan")}
        </button>
      </div>
    </section>
  );
}

function planCreateErrorMessage(error: Error, t: (key: string, params?: Record<string, string | number>) => string) {
  if (error instanceof ApiError) {
    if (error.status === 404 && error.detail === "Not Found") {
      return t("planCreateRouteUnavailable");
    }
    if (error.detail) {
      return t("planCreateFailedWithDetail", { detail: error.detail });
    }
  }
  return t("planCreateFailed");
}

function formatPercent(value: number, locale: Locale) {
  return new Intl.NumberFormat(localeTag[locale], {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
    style: "percent"
  }).format(value);
}

function formatMoney(value: number | null | undefined, locale: Locale) {
  if (value === null || value === undefined) {
    return "-";
  }
  return new Intl.NumberFormat(localeTag[locale], {
    currency: "USD",
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
    style: "currency"
  }).format(value);
}
