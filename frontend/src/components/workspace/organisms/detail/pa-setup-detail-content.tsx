"use client";

import { useQuery } from "@tanstack/react-query";

import { Field } from "@/components/workspace/atoms/field";
import { PAEvidencePanel } from "@/components/workspace/pa-evidence-chart";
import { DetailFieldPanel } from "@/components/workspace/organisms/detail/detail-field-panel";
import { ExplanationBlock } from "@/components/workspace/organisms/detail/explanation-block";
import { KeyLevelsBlock } from "@/components/workspace/organisms/detail/key-levels-block";
import { PlanFields } from "@/components/workspace/organisms/detail/plan-fields";
import { ScannerDecisionBlock } from "@/components/workspace/organisms/detail/scanner-decision-block";
import { ScoreBreakdownBlock } from "@/components/workspace/organisms/detail/score-breakdown-block";
import type { PASetup } from "@/lib/api";
import { api } from "@/lib/api";
import { formatNumber, nestedRecord } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function PASetupDetailContent({
  setup,
  locale
}: {
  setup: PASetup | null;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const scoreBreakdown = nestedRecord(setup?.entry_plan, "score_breakdown");
  const scannerDecision = nestedRecord(setup?.entry_plan, "scanner_decision");
  const explain = useQuery({
    queryKey: ["pa-setup-explain", setup?.setup_id],
    queryFn: () => api.paSetupExplain(setup?.setup_id as string),
    enabled: Boolean(setup?.setup_id)
  });

  if (!setup) {
    return <p className="text-sm text-slate-600">{t("noSetup")}</p>;
  }

  return (
    <>
      <ExplanationBlock locale={locale} setup={setup} />
      <DetailFieldPanel title={t("overviewDetails")}>
        <Field label={t("setup")} value={labelFor("setup", setup.setup_type)} />
        <Field label={t("grade")} value={setup.setup_grade} />
        <Field label={t("quality")} value={formatNumber(setup.pa_quality_score, 1, locale)} />
        <Field label={t("timeframe")} value={labelFor("plan", setup.timeframe)} />
        <Field label={t("validation")} value={labelFor("status", setup.validation_status)} />
        <Field label={t("status")} value={labelFor("status", setup.status)} />
      </DetailFieldPanel>
      <DetailFieldPanel title={t("scoreSnapshot")}>
        <Field label={t("structure")} value={formatNumber(setup.structure_score, 1, locale)} />
        <Field label={t("location")} value={formatNumber(setup.location_score, 1, locale)} />
        <Field label={t("volume")} value={formatNumber(setup.volume_score, 1, locale)} />
        <Field label={t("trendRs")} value={formatNumber(setup.trend_rs_score, 1, locale)} />
        <Field label={t("context")} value={formatNumber(setup.context_score, 1, locale)} />
        <Field label={t("riskStop")} value={formatNumber(setup.risk_stop_score, 1, locale)} />
      </DetailFieldPanel>
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
  );
}
