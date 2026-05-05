"use client";

import { GitBranch } from "lucide-react";

import { Field } from "@/components/workspace/atoms/field";
import { StatusPill } from "@/components/workspace/atoms/status-pill";
import { DetailFieldPanel } from "@/components/workspace/organisms/detail/detail-field-panel";
import type { StratSignal, StratTriggerPlan } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function StratSignalBlock({
  locale,
  plan,
  signal
}: {
  locale: Locale;
  plan: StratTriggerPlan | null | undefined;
  signal: StratSignal | null | undefined;
}) {
  const { labelFor, t } = useAppI18n();

  if (!signal && !plan) {
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

  const continuity = signal?.timeframe_continuity
    ? Object.entries(signal.timeframe_continuity)
        .map(([timeframe, state]) => `${labelFor("plan", timeframe)}: ${labelFor("plan", state)}`)
        .join(" / ")
    : "-";
  const hasActionablePattern = Boolean(signal?.pattern && signal.direction);
  const showPendingPlan = plan?.status === "armed" || plan?.status === "blocked";

  return (
    <section className="rounded-md border border-teal/20 bg-teal-50/30 px-3 py-3">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <GitBranch className="text-teal" size={18} />
        <h3 className="text-sm font-semibold text-ink">{t("stratTrigger")}</h3>
        {signal ? <StatusPill label={signal.bar_type} tone="neutral" /> : null}
        {hasActionablePattern ? <StatusPill label={labelFor("plan", signal?.pattern)} tone="good" /> : null}
        {!hasActionablePattern && signal ? <StatusPill label={t("stratBarOnlyBadge")} tone="neutral" /> : null}
        {showPendingPlan ? (
          <StatusPill
            label={labelFor("plan", plan?.status)}
            tone={plan?.status === "armed" ? "good" : "warn"}
          />
        ) : null}
      </div>

      <p className="mb-3 text-sm leading-6 text-slate-700">
        {hasActionablePattern ? t("stratNoStandalone") : signal ? t("stratBarOnly") : t("stratNoSignal")}
      </p>

      {signal ? (
        <DetailFieldPanel title={hasActionablePattern ? t("stratTrigger") : t("stratBarState")}>
          <Field label={t("stratBar")} value={labelFor("plan", signal.bar_type)} />
          {hasActionablePattern ? (
            <>
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
              <Field label={t("invalidation")} value={labelFor("plan", signal.invalidation)} />
            </>
          ) : null}
          <Field label={t("stratContinuity")} value={continuity} />
          <Field label={t("detected")} value={formatDate(signal.ts, locale)} />
        </DetailFieldPanel>
      ) : null}

      {showPendingPlan ? <StratPendingPlan locale={locale} plan={plan} /> : null}
    </section>
  );
}

function StratPendingPlan({
  locale,
  plan
}: {
  locale: Locale;
  plan: StratTriggerPlan;
}) {
  const { labelFor, t } = useAppI18n();
  const continuity = plan.timeframe_continuity
    ? Object.entries(plan.timeframe_continuity)
        .map(([timeframe, state]) => `${labelFor("plan", timeframe)}: ${labelFor("plan", state)}`)
        .join(" / ")
    : "-";

  return (
    <div className="mt-3 rounded-md border border-line bg-white px-3 py-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h4 className="text-sm font-semibold text-ink">{t("stratPendingPlan")}</h4>
        <StatusPill label={labelFor("plan", plan.status)} tone={plan.status === "armed" ? "good" : "warn"} />
      </div>
      <p className="mb-3 text-sm leading-6 text-slate-700">
        {plan.status === "armed" ? t("stratPendingPlanArmed") : t("stratPendingPlanBlocked")}
      </p>
      <DetailFieldPanel title={t("stratPendingPlan")}>
        <Field label={t("stratPattern")} value={labelFor("plan", plan.pattern)} />
        <Field label={t("stratDirection")} value={labelFor("plan", plan.direction)} />
        <Field label={t("stratTriggerPrice")} value={formatNumber(plan.trigger_price, 2, locale)} />
        <Field label={t("stratTriggerStop")} value={formatNumber(plan.trigger_stop, 2, locale)} />
        <Field label={t("orderType")} value={labelFor("plan", plan.order_type)} />
        <Field label={t("maxEntryPrice")} value={formatNumber(plan.max_entry_price, 2, locale)} />
        <Field label={t("riskDistance")} value={formatPercent(plan.risk_distance_pct)} />
        <Field label={t("stratContinuity")} value={continuity} />
      </DetailFieldPanel>
      {plan.no_chase_rules.length ? (
        <div className="mt-3 rounded-md border border-line bg-panel/60 px-3 py-2">
          <div className="mb-1 text-xs font-semibold uppercase text-slate-500">{t("noChaseRules")}</div>
          <ul className="grid gap-1.5 text-sm leading-6 text-slate-700">
            {plan.no_chase_rules.map((rule, index) => {
              const code = typeof rule.code === "string" ? rule.code : "";
              const level = typeof rule.level === "string" ? rule.level : "info";
              return (
                <li className="flex gap-2" key={`${code}-${index}`}>
                  <span
                    className={`mt-2 h-2 w-2 shrink-0 rounded-full ${level === "block" ? "bg-rose-700" : level === "warning" ? "bg-amber-500" : "bg-teal"}`}
                  />
                  <span>{noChaseRuleText(t, code)}</span>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${(value * 100).toFixed(1)}%`;
}

const NO_CHASE_TEXT_KEYS: Record<string, string> = {
  strat_atr_extension: "ruleStratAtrExtension",
  strat_consecutive_2u_no_chase: "ruleStratConsecutive2UNoChase",
  strat_gap_no_chase_limit: "ruleStratGapNoChaseLimit",
  strat_mother_bar_exceeds_atr: "ruleStratMotherBarExceedsAtr",
  strat_overextended_from_20ma: "ruleStratOverextendedFrom20ma",
  strat_risk_too_wide: "ruleStratRiskTooWide",
  strat_wide_mother_bar: "ruleStratWideMotherBar"
};

function noChaseRuleText(t: ReturnType<typeof useAppI18n>["t"], code: string) {
  const key = NO_CHASE_TEXT_KEYS[code];
  return key ? t(key) : code || "-";
}
