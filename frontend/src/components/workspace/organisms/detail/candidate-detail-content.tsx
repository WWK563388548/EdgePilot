"use client";

import { useQuery } from "@tanstack/react-query";

import { DataState } from "@/components/workspace/atoms/data-state";
import { Field } from "@/components/workspace/atoms/field";
import { PAEvidencePanel } from "@/components/workspace/pa-evidence-chart";
import { DetailFieldPanel } from "@/components/workspace/organisms/detail/detail-field-panel";
import { CandidateTradePlanCard } from "@/components/workspace/organisms/detail/candidate-trade-plan-card";
import { ExplanationBlock } from "@/components/workspace/organisms/detail/explanation-block";
import { KeyLevelsBlock } from "@/components/workspace/organisms/detail/key-levels-block";
import { PlanFields } from "@/components/workspace/organisms/detail/plan-fields";
import { ScannerDecisionBlock } from "@/components/workspace/organisms/detail/scanner-decision-block";
import { ScoreBreakdownBlock } from "@/components/workspace/organisms/detail/score-breakdown-block";
import { StratSignalBlock } from "@/components/workspace/organisms/detail/strat-signal-block";
import type { CandidateDetail } from "@/lib/api";
import { api } from "@/lib/api";
import { formatNumber, nestedRecord } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function CandidateDetailContent({
  detail,
  loading,
  error,
  locale,
  selected
}: {
  detail: CandidateDetail | undefined;
  loading: boolean;
  error: boolean;
  locale: Locale;
  selected: boolean;
}) {
  const { labelFor, t } = useAppI18n();
  const candidate = detail?.candidate;
  const setup = detail?.pa_setup;
  const entryPlan = detail?.entry_plan ?? setup?.entry_plan;
  const exitPlan = detail?.exit_plan ?? setup?.exit_plan;
  const scoreBreakdown = detail?.score_breakdown ?? nestedRecord(entryPlan, "score_breakdown");
  const scannerDecision = detail?.scanner_decision;
  const explain = useQuery({
    queryKey: ["pa-setup-explain", setup?.setup_id],
    queryFn: () => api.paSetupExplain(setup?.setup_id as string),
    enabled: Boolean(setup?.setup_id)
  });

  return (
    <>
      <DataState isLoading={loading} isError={error} locale={locale} />
      {!selected && <p className="text-sm text-slate-600">{t("noSelection")}</p>}
      {candidate ? (
        <>
          <ExplanationBlock locale={locale} setup={setup} candidate={candidate} />

          <DetailFieldPanel title={t("overviewDetails")}>
            <Field label={t("setup")} value={candidate.setup_type ? labelFor("setup", candidate.setup_type) : "-"} />
            <Field label={t("grade")} value={setup?.setup_grade} />
            <Field label={t("validation")} value={labelFor("status", setup?.validation_status)} />
            <Field label={t("status")} value={labelFor("status", setup?.status ?? candidate.decision)} />
            <Field label={t("quality")} value={formatNumber(setup?.pa_quality_score ?? candidate.score_total, 1, locale)} />
            <Field label={t("timeframe")} value={labelFor("plan", setup?.timeframe)} />
          </DetailFieldPanel>

          <KeyLevelsBlock
            candidate={candidate}
            entryPlan={entryPlan}
            exitPlan={exitPlan}
            locale={locale}
            setup={setup}
          />
          <CandidateTradePlanCard
            candidate={candidate}
            entryPlan={entryPlan}
            exitPlan={exitPlan}
            locale={locale}
            setup={setup}
          />
          <StratSignalBlock locale={locale} plan={detail?.strat_plan} signal={detail?.strat_signal} />
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
    </>
  );
}
