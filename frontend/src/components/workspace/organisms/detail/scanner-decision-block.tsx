"use client";

import {
  BadgeCheck,
  CircleAlert,
  CircleCheck,
  CircleX,
  GitBranch,
  Target,
  TrendingUp
} from "lucide-react";
import type { ReactNode } from "react";

import { formatPercent } from "@/components/workspace/organisms/evidence/chart-format";
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
  const metrics = recordFromRecord(record, "metrics");
  const max20dWarning = metrics ? recordFromRecord(metrics, "max20d_warning") : null;
  const entryMode = metrics ? stringFromRecord(metrics, "entry_mode") : null;
  const passedRules = recordListFromRecord(record, "passed_rules");
  const failedRules = recordListFromRecord(record, "failed_rules");
  const watchReasons = stringListFromRecord(record, "watch_reasons");
  const upgradeConditions = stringListFromRecord(record, "upgrade_conditions");
  const riskNotes = stringListFromRecord(record, "risk_notes");
  const stratConfirmation = recordFromRecord(record, "strat_confirmation");
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

      <div className="mb-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
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
        {entryMode ? (
          <DecisionMetric
            icon={<GitBranch size={16} />}
            label={t("entryMode")}
            value={labelFor("plan", entryMode)}
          />
        ) : null}
      </div>

      {stratConfirmation ? (
        <StratDecisionCard data={stratConfirmation} locale={locale} />
      ) : null}
      {max20dWarning ? (
        <Max20dWarningCard data={max20dWarning} locale={locale} />
      ) : null}

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

function StratDecisionCard({
  data,
  locale
}: {
  data: Record<string, unknown>;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const status = stringFromRecord(data, "status");
  const reason = stringFromRecord(data, "reason");
  const barType = stringFromRecord(data, "bar_type");
  const pattern = stringFromRecord(data, "pattern");
  const direction = stringFromRecord(data, "direction");
  const triggerPrice = numberFromRecord(data, "trigger_price");
  const triggerStop = numberFromRecord(data, "trigger_stop");
  const baseDecision = stringFromRecord(data, "base_decision");
  const finalDecision = stringFromRecord(data, "final_decision");
  const tone =
    status === "confirm"
      ? "border-teal-200 bg-teal-50"
      : status === "downgrade"
        ? "border-amber-200 bg-amber-50"
        : "border-line bg-panel/70";

  return (
    <div className={`mb-3 rounded-md border px-3 py-2 ${tone}`}>
      <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
        <GitBranch size={16} className="text-teal" />
        {t("stratDecision")}
      </div>
      <p className="text-sm leading-6 text-slate-700">
        {reason ? scannerDecisionText(t, reason) : "-"}
      </p>
      <div className="mt-2 grid gap-2 text-xs text-slate-600 sm:grid-cols-2 xl:grid-cols-4">
        <span>{labelFor("plan", status)}</span>
        <span>
          {labelFor("plan", barType)}
          {pattern ? ` · ${labelFor("plan", pattern)}` : ""}
        </span>
        <span>{labelFor("plan", direction)}</span>
        <span>
          {formatNumber(triggerPrice, 2, locale)} / {formatNumber(triggerStop, 2, locale)}
        </span>
        {baseDecision && finalDecision && baseDecision !== finalDecision ? (
          <span className="font-semibold text-amber-700">
            {labelFor("status", baseDecision)} → {labelFor("status", finalDecision)}
          </span>
        ) : null}
      </div>
    </div>
  );
}

function Max20dWarningCard({
  data,
  locale
}: {
  data: Record<string, unknown>;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const maxReturn = numberFromRecord(data, "max_20d_return");
  const lotteryRisk = stringFromRecord(data, "lottery_risk") ?? "unknown";
  const suggestedAction = stringFromRecord(data, "suggested_action") ?? "unknown";
  const tone =
    lotteryRisk === "high"
      ? "border-rose-200 bg-rose-50"
      : lotteryRisk === "medium"
        ? "border-amber-200 bg-amber-50"
        : "border-line bg-panel/70";

  return (
    <div className={`mb-3 rounded-md border px-3 py-2 ${tone}`}>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-sm font-semibold text-ink">
        <CircleAlert size={16} className={lotteryRisk === "high" ? "text-rose-700" : "text-amber-700"} />
        {t("max20dWarning")}
        <span className="rounded-md border border-white/70 bg-white px-2 py-0.5 text-xs text-slate-700">
          {labelFor("plan", `max20d_${lotteryRisk}`)}
        </span>
      </div>
      <p className="text-sm leading-6 text-slate-700">
        {t("max20dWarningCopy", {
          max20d: formatPercent(maxReturn, locale),
          action: labelFor("plan", `max20d_action_${suggestedAction}`)
        })}
      </p>
    </div>
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
  base_depth_healthy: "ruleBaseDepthHealthy",
  base_too_deep: "ruleBaseTooDeep",
  break_above_trigger: "conditionBreakAboveTrigger",
  breakout_close_near_high: "ruleBreakoutCloseNearHigh",
  breakout_near_pivot: "ruleBreakoutNearPivot",
  breakout_volume_confirmed: "ruleBreakoutVolumeConfirmed",
  breakout_volume_missing: "ruleBreakoutVolumeMissing",
  extended_from_20ma: "riskExtendedFrom20ma",
  hold_above_20_50ma: "conditionHoldAboveMas",
  hold_above_20ma: "ruleHoldAbove20ma",
  initial_stop_required: "riskInitialStopRequired",
  invalidates_below_stop: "riskInvalidatesBelowStop",
  leader_near_high: "ruleLeaderNearHigh",
  market_context_caution: "ruleMarketContextCaution",
  market_context_green: "conditionMarketContextGreen",
  market_support: "ruleMarketSupport",
  max20d_lottery_risk_high: "riskMax20dLotteryRiskHigh",
  max20d_lottery_risk_medium: "riskMax20dLotteryRiskMedium",
  needs_trigger_confirmation: "reasonNeedsTriggerConfirmation",
  pullback_near_20ma: "rulePullbackNear20ma",
  pullback_volume_heavy: "rulePullbackVolumeHeavy",
  pullback_volume_quiet: "rulePullbackVolumeQuiet",
  reclaim_50ma: "ruleReclaim50ma",
  reclaim_volume_confirmed: "ruleReclaimVolumeConfirmed",
  reclaim_after_pullback: "conditionReclaimAfterPullback",
  relative_strength_lagging: "ruleRelativeStrengthLagging",
  relative_strength_leader: "ruleRelativeStrengthLeader",
  risk_contained: "ruleRiskContained",
  risk_too_wide: "ruleRiskTooWide",
  rs_not_leading: "ruleRsNotLeading",
  rs_top_quartile: "ruleRsTopQuartile",
  score_below_candidate: "reasonScoreBelowCandidate",
  do_not_chase_overextended_rotation: "riskDoNotChaseOverextendedRotation",
  medium_momentum_reasserts: "conditionMediumMomentumReasserts",
  one_month_overextension: "riskOneMonthOverextension",
  pullback_to_20ma_or_reclaim: "conditionPullbackTo20maOrReclaim",
  respect_strategy_entry_mode: "conditionRespectStrategyEntryMode",
  rotation_12m_lagging: "ruleRotation12mLagging",
  rotation_12m_support: "ruleRotation12mSupport",
  rotation_benchmark_rs_lagging: "ruleRotationBenchmarkRsLagging",
  rotation_benchmark_rs_leader: "ruleRotationBenchmarkRsLeader",
  rotation_breakout_allowed: "ruleRotationBreakoutAllowed",
  rotation_healthy_pullback: "ruleRotationHealthyPullback",
  rotation_medium_momentum_leader: "ruleRotationMediumMomentumLeader",
  rotation_medium_momentum_weak: "ruleRotationMediumMomentumWeak",
  rotation_one_month_overextended: "ruleRotationOneMonthOverextended",
  rotation_pullback_required: "reasonRotationPullbackRequired",
  rotation_retest_required: "reasonRotationRetestRequired",
  rotation_watch_only: "reasonRotationWatchOnly",
  setup_location: "ruleSetupLocation",
  setup_location_unclear: "ruleSetupLocationUnclear",
  shadow_only: "reasonShadowOnly",
  supportive_close_position: "ruleSupportiveClosePosition",
  trend_aligned: "ruleTrendAligned",
  trend_needs_alignment: "ruleTrendNeedsAlignment",
  volatility_contraction: "ruleVolatilityContraction",
  volume_confirmation_missing: "ruleVolumeConfirmationMissing",
  volume_expansion: "conditionVolumeExpansion",
  volume_liquidity: "ruleVolumeLiquidity",
  volume_needs_confirmation: "reasonVolumeNeedsConfirmation",
  weak_close_position: "ruleWeakClosePosition",
  strat_bearish_context: "riskStratBearishContext",
  strat_bearish_downgrade: "reasonStratBearishDowngrade",
  strat_bearish_trigger: "ruleStratBearishTrigger",
  strat_bullish_trigger: "ruleStratBullishTrigger",
  strat_bullish_trigger_needed: "conditionStratBullishTriggerNeeded",
  strat_atr_extension: "ruleStratAtrExtension",
  strat_consecutive_2u_no_chase: "ruleStratConsecutive2UNoChase",
  strat_gap_no_chase_limit: "ruleStratGapNoChaseLimit",
  strat_mother_bar_exceeds_atr: "ruleStratMotherBarExceedsAtr",
  strat_no_chase_blocked: "reasonStratNoChaseBlocked",
  strat_overextended_from_20ma: "ruleStratOverextendedFrom20ma",
  strat_pending_trigger_armed: "reasonStratPendingTriggerArmed",
  strat_risk_too_wide: "ruleStratRiskTooWide",
  strat_signal_missing: "reasonStratSignalMissing",
  strat_trigger_price_reached: "conditionStratTriggerPriceReached",
  strat_waiting_for_trigger: "reasonStratWaitingForTrigger",
  strat_wide_mother_bar: "ruleStratWideMotherBar"
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

function recordFromRecord(data: Record<string, unknown>, key: string) {
  const value = data[key];
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function humanizeKey(value: string) {
  return value.replace(/_/g, " ");
}
