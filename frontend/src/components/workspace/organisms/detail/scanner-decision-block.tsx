"use client";

import { BadgeCheck, CircleAlert, CircleCheck, CircleX, Target, TrendingUp } from "lucide-react";
import type { ReactNode } from "react";

import type { ScannerDecision } from "@/lib/api";
import { formatNumber, numberFromRecord, stringFromRecord } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function ScannerDecisionBlock({
  data,
  locale
}: {
  data: ScannerDecision | Record<string, unknown> | null | undefined;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  if (!data) {
    return null;
  }

  const record = data as Record<string, unknown>;
  const decision = stringFromRecord(record, "decision");
  const totalScore = numberFromRecord(record, "score") ?? numberFromRecord(record, "total_score");
  const triggerPrice = numberFromRecord(record, "trigger_price");
  const initialStop = numberFromRecord(record, "initial_stop");
  const validationStatus = stringFromRecord(record, "validation_status");
  const passedRules = recordListFromRecord(record, "passed_rules");
  const failedRules = recordListFromRecord(record, "failed_rules");
  const watchReasons = stringListFromRecord(record, "watch_reasons");
  const upgradeConditions = stringListFromRecord(record, "upgrade_conditions");
  const riskNotes = stringListFromRecord(record, "risk_notes");
  const decisionTone =
    decision === "candidate"
      ? "border-teal-200 bg-teal-50 text-teal"
      : "border-amber-200 bg-amber-50 text-amber-700";

  return (
    <section className="border-t border-line pt-3">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-ink">{t("scannerDecision")}</h3>
        <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${decisionTone}`}>
          {labelFor("status", decision)} · {formatNumber(totalScore, 1, locale)}
        </span>
      </div>
      <p className="mb-3 rounded-md border border-line bg-panel/70 px-3 py-2 text-sm leading-6 text-slate-700">
        {decision === "candidate"
          ? t("scannerDecisionCandidate", { score: formatNumber(totalScore, 1, locale) })
          : t("scannerDecisionWatch", { score: formatNumber(totalScore, 1, locale) })}
      </p>

      <div className="mb-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <DecisionMetric
          icon={<BadgeCheck size={16} />}
          label={t("decision")}
          value={labelFor("status", decision)}
        />
        <DecisionMetric
          icon={<TrendingUp size={16} />}
          label={t("score")}
          value={formatNumber(totalScore, 1, locale)}
        />
        <DecisionMetric
          icon={<Target size={16} />}
          label={t("entry")}
          value={formatNumber(triggerPrice, 2, locale)}
        />
        <DecisionMetric
          icon={<CircleAlert size={16} />}
          label={t("stop")}
          value={`${formatNumber(initialStop, 2, locale)} · ${labelFor("status", validationStatus)}`}
        />
      </div>

      <div className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="grid gap-3 lg:grid-cols-2">
          <RuleList title={t("passedRules")} items={passedRules} locale={locale} tone="pass" />
          <RuleList
            emptyMessage={t("allCoreRulesPassed")}
            title={t("failedRules")}
            items={failedRules}
            locale={locale}
            tone="fail"
          />
        </div>
        <div className="grid gap-3">
          <KeyList title={t("watchReasons")} items={watchReasons} tone="watch" />
          <KeyList title={t("upgradeConditions")} items={upgradeConditions} tone="upgrade" />
        </div>
      </div>
      {riskNotes.length ? (
        <div className="mt-3 rounded-md border border-amber-200 bg-amber-50/70 px-3 py-2">
          <div className="mb-1 text-sm font-semibold text-ink">{t("riskNotes")}</div>
          <ul className="grid gap-1.5 text-sm leading-6 text-slate-700">
            {riskNotes.map((item) => (
              <li key={item}>{scannerDecisionText(t, item)}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function DecisionMetric({
  icon,
  label,
  value
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border border-line bg-white px-3 py-2">
      <div className="mb-1 flex items-center gap-1.5 text-xs font-medium uppercase text-slate-500">
        {icon}
        <span>{label}</span>
      </div>
      <div className="truncate text-sm font-semibold text-ink" title={value}>
        {value}
      </div>
    </div>
  );
}

function RuleList({
  title,
  items,
  locale,
  tone,
  emptyMessage = "-"
}: {
  title: string;
  items: Record<string, unknown>[];
  locale: Locale;
  tone: "pass" | "fail";
  emptyMessage?: string;
}) {
  const { t } = useAppI18n();
  return (
    <div className="rounded-md border border-line bg-white px-3 py-2">
      <div className="mb-2 text-sm font-semibold text-ink">{title}</div>
      {items.length ? (
        <ul className="grid gap-2">
          {items.map((item, index) => {
            const key = stringFromRecord(item, "key") ?? String(index);
            const score = numberFromRecord(item, "score");
            const maxScore = numberFromRecord(item, "max_score");
            return (
              <li className="grid grid-cols-[0.9rem_minmax(0,1fr)_auto] items-start gap-2 text-sm" key={`${key}-${index}`}>
                {tone === "pass" ? (
                  <CircleCheck size={14} className="mt-1 shrink-0 text-teal" />
                ) : (
                  <CircleX size={14} className="mt-1 shrink-0 text-amber-600" />
                )}
                <span className="min-w-0 leading-6 text-slate-700">{scannerDecisionText(t, key)}</span>
                {score !== null ? (
                  <span className="whitespace-nowrap text-xs font-semibold text-slate-500">
                    {formatNumber(score, 1, locale)}
                    {maxScore !== null ? `/${formatNumber(maxScore, 0, locale)}` : ""}
                  </span>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="text-sm text-slate-500">{emptyMessage}</p>
      )}
    </div>
  );
}

function KeyList({
  title,
  items,
  tone
}: {
  title: string;
  items: string[];
  tone: "watch" | "upgrade";
}) {
  const { t } = useAppI18n();
  return (
    <div className="rounded-md border border-line bg-white px-3 py-2">
      <div className="mb-2 text-sm font-semibold text-ink">{title}</div>
      {items.length ? (
        <ul className="grid gap-1.5 text-sm leading-6 text-slate-700">
          {items.map((item) => (
            <li className="flex gap-2" key={item}>
              <span className={`mt-2 h-2 w-2 shrink-0 rounded-full ${tone === "upgrade" ? "bg-teal" : "bg-slate-400"}`} />
              <span>{scannerDecisionText(t, item)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-500">-</p>
      )}
    </div>
  );
}

const SCANNER_DECISION_TEXT_KEYS: Record<string, string> = {
  break_above_trigger: "conditionBreakAboveTrigger",
  extended_from_20ma: "riskExtendedFrom20ma",
  hold_above_20_50ma: "conditionHoldAboveMas",
  initial_stop_required: "riskInitialStopRequired",
  invalidates_below_stop: "riskInvalidatesBelowStop",
  market_context_caution: "ruleMarketContextCaution",
  market_context_green: "conditionMarketContextGreen",
  market_support: "ruleMarketSupport",
  needs_trigger_confirmation: "reasonNeedsTriggerConfirmation",
  relative_strength_lagging: "ruleRelativeStrengthLagging",
  relative_strength_leader: "ruleRelativeStrengthLeader",
  risk_contained: "ruleRiskContained",
  risk_too_wide: "ruleRiskTooWide",
  score_below_candidate: "reasonScoreBelowCandidate",
  setup_location: "ruleSetupLocation",
  setup_location_unclear: "ruleSetupLocationUnclear",
  shadow_only: "reasonShadowOnly",
  trend_aligned: "ruleTrendAligned",
  trend_needs_alignment: "ruleTrendNeedsAlignment",
  volume_confirmation_missing: "ruleVolumeConfirmationMissing",
  volume_expansion: "conditionVolumeExpansion",
  volume_liquidity: "ruleVolumeLiquidity",
  volume_needs_confirmation: "reasonVolumeNeedsConfirmation"
};

function scannerDecisionText(t: ReturnType<typeof useAppI18n>["t"], key: string) {
  const messageKey = SCANNER_DECISION_TEXT_KEYS[key];
  return messageKey ? t(messageKey) : humanizeKey(key);
}

function recordListFromRecord(data: Record<string, unknown>, key: string) {
  const value = data[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object" && !Array.isArray(item));
}

function stringListFromRecord(data: Record<string, unknown>, key: string) {
  const value = data[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function humanizeKey(value: string) {
  return value.replace(/_/g, " ");
}
