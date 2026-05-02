import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import { DataState, Field } from "@/components/workspace/common";
import { PAEvidencePanel } from "@/components/workspace/pa-evidence-chart";
import type { Candidate, CandidateDetail, PASetup } from "@/lib/api";
import { api } from "@/lib/api";
import {
  formatDetailValue,
  formatNumber,
  nestedRecord,
  numberFromRecord,
  stringFromRecord
} from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function CandidateDetailPanel({
  detail,
  loading,
  error,
  locale,
  selected,
  onClose
}: {
  detail: CandidateDetail | undefined;
  loading: boolean;
  error: boolean;
  locale: Locale;
  selected: boolean;
  onClose: () => void;
}) {
  const { labelFor, t } = useAppI18n();
  const candidate = detail?.candidate;
  const setup = detail?.pa_setup;
  const entryPlan = detail?.entry_plan ?? setup?.entry_plan;
  const exitPlan = detail?.exit_plan ?? setup?.exit_plan;
  const scoreBreakdown = detail?.score_breakdown ?? nestedRecord(entryPlan, "score_breakdown");
  const scannerDecision = detail?.scanner_decision ?? nestedRecord(entryPlan, "scanner_decision");
  const explain = useQuery({
    queryKey: ["pa-setup-explain", setup?.setup_id],
    queryFn: () => api.paSetupExplain(setup?.setup_id as string),
    enabled: Boolean(setup?.setup_id)
  });
  const title = candidate ? `${candidate.symbol_id} ${t("candidateDetail")}` : t("candidateDetail");
  const subtitle = setup?.setup_id ?? candidate?.candidate_id ?? t("noSelection");

  return (
    <DetailModalShell
      closeLabel={t("closeDetail")}
      onClose={onClose}
      subtitle={subtitle}
      title={title}
    >
        <DataState isLoading={loading} isError={error} locale={locale} />
        {!selected && <p className="text-sm text-slate-600">{t("noSelection")}</p>}
        {candidate ? (
          <>
            <ExplanationBlock locale={locale} setup={setup} candidate={candidate} />

            <div className="grid grid-cols-2 gap-3">
              <Field label={t("setup")} value={candidate.setup_type ? labelFor("setup", candidate.setup_type) : "-"} />
              <Field label={t("grade")} value={setup?.setup_grade} />
              <Field label={t("validation")} value={labelFor("status", setup?.validation_status)} />
              <Field label={t("status")} value={labelFor("status", setup?.status ?? candidate.decision)} />
              <Field label={t("quality")} value={formatNumber(setup?.pa_quality_score ?? candidate.score_total, 1, locale)} />
              <Field label={t("timeframe")} value={labelFor("plan", setup?.timeframe)} />
            </div>

            <KeyLevelsBlock
              candidate={candidate}
              entryPlan={entryPlan}
              exitPlan={exitPlan}
              locale={locale}
              setup={setup}
            />
            <ScannerDecisionBlock data={scannerDecision} locale={locale} />
            <PAEvidencePanel
              error={explain.isError}
              explain={explain.data}
              loading={Boolean(setup?.setup_id) && explain.isLoading}
              locale={locale}
            />
            <ScoreBreakdownBlock data={scoreBreakdown} locale={locale} />
            <PlanFields title={t("entryPlan")} data={entryPlan} locale={locale} omitKeys={["score_breakdown", "scanner_decision"]} />
            <PlanFields title={t("exitPlan")} data={exitPlan} locale={locale} />
            <PlanFields title={t("invalidation")} data={detail?.invalidation ?? setup?.invalidation} locale={locale} />
          </>
        ) : null}
    </DetailModalShell>
  );
}

export function PASetupDetailPanel({
  setup,
  locale,
  onClose
}: {
  setup: PASetup | null;
  locale: Locale;
  onClose?: () => void;
}) {
  const { labelFor, t } = useAppI18n();
  const scoreBreakdown = nestedRecord(setup?.entry_plan, "score_breakdown");
  const scannerDecision = nestedRecord(setup?.entry_plan, "scanner_decision");
  const explain = useQuery({
    queryKey: ["pa-setup-explain", setup?.setup_id],
    queryFn: () => api.paSetupExplain(setup?.setup_id as string),
    enabled: Boolean(setup?.setup_id)
  });
  const title = setup ? `${setup.symbol_id} ${t("setupDetail")}` : t("setupDetail");
  const subtitle = setup?.setup_id ?? t("noSelection");

  return (
    <DetailModalShell
      closeLabel={t("closeDetail")}
      onClose={onClose}
      subtitle={subtitle}
      title={title}
    >
        {setup ? (
          <>
            <ExplanationBlock locale={locale} setup={setup} />
            <div className="grid grid-cols-2 gap-3">
              <Field label={t("setup")} value={labelFor("setup", setup.setup_type)} />
              <Field label={t("grade")} value={setup.setup_grade} />
              <Field label={t("quality")} value={formatNumber(setup.pa_quality_score, 1, locale)} />
              <Field label={t("timeframe")} value={labelFor("plan", setup.timeframe)} />
              <Field label={t("validation")} value={labelFor("status", setup.validation_status)} />
              <Field label={t("status")} value={labelFor("status", setup.status)} />
            </div>
            <div className="grid grid-cols-2 gap-3 border-t border-line pt-3">
              <Field label={t("structure")} value={formatNumber(setup.structure_score, 1, locale)} />
              <Field label={t("location")} value={formatNumber(setup.location_score, 1, locale)} />
              <Field label={t("volume")} value={formatNumber(setup.volume_score, 1, locale)} />
              <Field label={t("trendRs")} value={formatNumber(setup.trend_rs_score, 1, locale)} />
              <Field label={t("context")} value={formatNumber(setup.context_score, 1, locale)} />
              <Field label={t("riskStop")} value={formatNumber(setup.risk_stop_score, 1, locale)} />
            </div>
            <KeyLevelsBlock entryPlan={setup.entry_plan} exitPlan={setup.exit_plan} locale={locale} setup={setup} />
            <ScannerDecisionBlock data={scannerDecision} locale={locale} />
            <PAEvidencePanel
              error={explain.isError}
              explain={explain.data}
              loading={Boolean(setup?.setup_id) && explain.isLoading}
              locale={locale}
            />
            <ScoreBreakdownBlock data={scoreBreakdown} locale={locale} />
            <PlanFields title={t("entryPlan")} data={setup.entry_plan} locale={locale} omitKeys={["score_breakdown", "scanner_decision"]} />
            <PlanFields title={t("exitPlan")} data={setup.exit_plan} locale={locale} />
            <PlanFields title={t("invalidation")} data={setup.invalidation} locale={locale} />
          </>
        ) : (
          <p className="text-sm text-slate-600">{t("noSetup")}</p>
        )}
    </DetailModalShell>
  );
}

function DetailModalShell({
  children,
  closeLabel,
  onClose,
  subtitle,
  title
}: {
  children: ReactNode;
  closeLabel: string;
  onClose?: () => void;
  subtitle: string;
  title: string;
}) {
  const [closing, setClosing] = useState(false);

  const requestClose = useCallback(() => {
    if (!onClose || closing) {
      return;
    }
    setClosing(true);
    window.setTimeout(onClose, 180);
  }, [closing, onClose]);

  useEffect(() => {
    setClosing(false);
  }, [title, subtitle]);

  useEffect(() => {
    if (!onClose) {
      return undefined;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        requestClose();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, requestClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-6">
      {onClose ? (
        <div
          aria-hidden="true"
          className={`absolute inset-0 cursor-default bg-transparent ${
            closing ? "detail-backdrop-out" : "detail-backdrop-in"
          }`}
          onClick={requestClose}
        />
      ) : null}
      <section
        aria-label={title}
        aria-modal="true"
        className={`relative z-10 flex h-[92vh] w-[calc(100vw-1rem)] max-w-[1480px] flex-col overflow-hidden rounded-lg border border-line bg-white shadow-2xl sm:h-[85vh] sm:w-[85vw] ${
          closing ? "detail-modal-out" : "detail-modal-in"
        }`}
        role="dialog"
      >
        <div className="flex min-h-20 shrink-0 items-center justify-between gap-3 border-b border-line bg-white px-5 py-4 sm:px-6">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-ink">{title}</h2>
            <p className="truncate text-sm text-slate-500">{subtitle}</p>
          </div>
          {onClose ? (
            <button
              className="focus-ring inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-line bg-white text-slate-700 transition-colors hover:border-slate-400 hover:bg-panel"
              onClick={requestClose}
              title={closeLabel}
              type="button"
            >
              <X size={18} />
            </button>
          ) : null}
        </div>
        <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-5 py-5 sm:px-6">{children}</div>
      </section>
    </div>
  );
}

function ExplanationBlock({
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

function KeyLevelsBlock({
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

function ScannerDecisionBlock({
  data,
  locale
}: {
  data: Record<string, unknown> | null | undefined;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  if (!data) {
    return null;
  }

  const decision = stringFromRecord(data, "decision");
  const totalScore = numberFromRecord(data, "total_score");
  const passedRules = recordListFromRecord(data, "passed_rules");
  const failedRules = recordListFromRecord(data, "failed_rules");
  const watchReasons = stringListFromRecord(data, "watch_reasons");
  const upgradeConditions = stringListFromRecord(data, "upgrade_conditions");
  const riskNotes = stringListFromRecord(data, "risk_notes");

  return (
    <section className="border-t border-line pt-3">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-ink">{t("scannerDecision")}</h3>
        <span className="rounded-md border border-teal-200 bg-teal-50 px-2 py-1 text-xs font-semibold text-teal">
          {labelFor("status", decision)} · {formatNumber(totalScore, 1, locale)}
        </span>
      </div>
      <p className="mb-3 rounded-md border border-line bg-panel/70 px-3 py-2 text-sm leading-6 text-slate-700">
        {decision === "candidate"
          ? t("scannerDecisionCandidate", { score: formatNumber(totalScore, 1, locale) })
          : t("scannerDecisionWatch", { score: formatNumber(totalScore, 1, locale) })}
      </p>
      <div className="grid gap-3 lg:grid-cols-2">
        <RuleList title={t("passedRules")} items={passedRules} locale={locale} tone="pass" />
        <RuleList title={t("failedRules")} items={failedRules} locale={locale} tone="fail" />
        <KeyList title={t("watchReasons")} items={watchReasons} tone="watch" />
        <KeyList title={t("upgradeConditions")} items={upgradeConditions} tone="upgrade" />
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

function RuleList({
  title,
  items,
  locale,
  tone
}: {
  title: string;
  items: Record<string, unknown>[];
  locale: Locale;
  tone: "pass" | "fail";
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
              <li className="grid grid-cols-[0.55rem_minmax(0,1fr)_auto] items-start gap-2 text-sm" key={`${key}-${index}`}>
                <span className={`mt-2 h-2 w-2 rounded-full ${tone === "pass" ? "bg-teal" : "bg-amber-500"}`} />
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
        <p className="text-sm text-slate-500">-</p>
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

function ScoreBreakdownBlock({
  data,
  locale
}: {
  data: Record<string, unknown> | null | undefined;
  locale: Locale;
}) {
  const { scoreMeta, t } = useAppI18n();
  const order = ["total", "trend", "relative_strength", "volume_liquidity", "base_setup", "market_context", "fundamental_lite"];
  const maxScoreByKey: Record<string, number> = {
    total: 100,
    trend: 25,
    relative_strength: 25,
    volume_liquidity: 15,
    base_setup: 15,
    market_context: 10,
    fundamental_lite: 10
  };
  const entries = Object.entries(data ?? {})
    .filter(([, value]) => typeof value === "number")
    .sort(([left], [right]) => {
      const leftIndex = order.indexOf(left);
      const rightIndex = order.indexOf(right);
      return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
    });

  return (
    <section className="border-t border-line pt-3">
      <h3 className="mb-3 text-sm font-semibold text-ink">{t("scoreBreakdown")}</h3>
      {entries.length ? (
        <div className="grid gap-3">
          {entries.map(([key, value]) => {
            const meta = scoreMeta(key);
            const score = typeof value === "number" ? value : null;
            const maxScore = maxScoreByKey[key] ?? 100;
            const barWidth = Math.max(0, Math.min(100, ((score ?? 0) / maxScore) * 100));
            return (
              <div key={key} className="grid grid-cols-[minmax(0,1fr)_3.5rem] gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-medium text-ink">{meta.label}</div>
                  {meta.description ? <div className="mt-0.5 text-xs leading-5 text-slate-500">{meta.description}</div> : null}
                  <div className="mt-2 h-1.5 overflow-hidden rounded bg-slate-100">
                    <div
                      className="h-full rounded bg-teal"
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
                <div className="text-right text-sm font-semibold text-ink">{formatNumber(score, 1, locale)}</div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-slate-500">-</p>
      )}
    </section>
  );
}

function PlanFields({
  title,
  data,
  locale,
  omitKeys = []
}: {
  title: string;
  data: Record<string, unknown> | null | undefined;
  locale: Locale;
  omitKeys?: string[];
}) {
  const { labelFor } = useAppI18n();
  const entries = Object.entries(data ?? {}).filter(([key]) => !omitKeys.includes(key));

  return (
    <section className="border-t border-line pt-3">
      <h3 className="mb-2 text-sm font-semibold text-ink">{title}</h3>
      {entries.length ? (
        <dl className="grid gap-2">
          {entries.map(([key, value]) => (
            <div
              key={key}
              className="grid gap-1 rounded-md border border-line bg-panel/70 px-3 py-2 text-sm sm:grid-cols-[8rem_minmax(0,1fr)] sm:gap-3"
            >
              <dt className="min-w-0 break-words text-slate-500">{labelFor("plan", key)}</dt>
              <dd className="min-w-0 break-words font-semibold leading-6 text-ink">
                {formatDetailValue(value, locale, labelFor)}
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-sm text-slate-500">-</p>
      )}
    </section>
  );
}
