import { Field } from "@/components/workspace/atoms/field";
import type { PASetupExplain } from "@/lib/api";
import { formatNumber, numberFromRecord } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";
import { formatMultiple, formatPercent } from "@/components/workspace/organisms/evidence/chart-format";

export function EvidenceMetricsGrid({
  facts,
  locale
}: {
  facts: PASetupExplain["evidence"]["latest_facts"] | undefined;
  locale: Locale;
}) {
  const { t } = useAppI18n();

  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      <Field label={t("latestClose")} value={formatNumber(numberFromRecord(facts, "close"), 2, locale)} />
      <Field label={t("relativeVolume")} value={formatMultiple(numberFromRecord(facts, "relative_volume"), locale)} />
      <Field label={t("sma20")} value={formatNumber(numberFromRecord(facts, "sma_20"), 2, locale)} />
      <Field label={t("sma50")} value={formatNumber(numberFromRecord(facts, "sma_50"), 2, locale)} />
      <Field label={t("sma200")} value={formatNumber(numberFromRecord(facts, "sma_200"), 2, locale)} />
      <Field label={t("closeVs20")} value={formatPercent(numberFromRecord(facts, "distance_to_sma_20_pct"), locale)} />
      <Field label={t("closeVs50")} value={formatPercent(numberFromRecord(facts, "distance_to_sma_50_pct"), locale)} />
      <Field label={t("from52wHigh")} value={formatPercent(numberFromRecord(facts, "pct_from_52w_high"), locale)} />
      <Field label={t("baseDepth")} value={formatPercent(numberFromRecord(facts, "base_depth_60d"), locale)} />
      <Field label={t("rangePosition")} value={formatPercent(numberFromRecord(facts, "close_position_in_range"), locale)} />
      <Field label={t("return3m")} value={formatPercent(numberFromRecord(facts, "return_3m"), locale)} />
      <Field label={t("return6m")} value={formatPercent(numberFromRecord(facts, "return_6m"), locale)} />
    </div>
  );
}
