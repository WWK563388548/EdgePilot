"use client";

import { Loader2, Save, Settings } from "lucide-react";

import { useAppI18n } from "@/lib/use-app-i18n";

import { NumberInput } from "./settings-helpers";

export type RiskFormState = {
  accountEquity: string;
  maxOpenPositions: string;
  maxRiskDistancePct: string;
  maxRiskPerTradePct: string;
  maxTotalRiskPct: string;
  shadowOnlyRequiresPaper: boolean;
};

export function RiskGuardrailsCard({
  form,
  isError,
  isLoading,
  isPending,
  isSuccess,
  onChange,
  onSave
}: {
  form: RiskFormState;
  isError: boolean;
  isLoading: boolean;
  isPending: boolean;
  isSuccess: boolean;
  onChange: (patch: Partial<RiskFormState>) => void;
  onSave: () => void;
}) {
  const { t } = useAppI18n();

  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-ink">{t("riskGuardrails")}</h2>
          <p className="mt-1 text-xs text-slate-600">{t("riskGuardrailsHelp")}</p>
        </div>
        <Settings size={18} className="text-teal" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <NumberInput
          label={t("accountEquity")}
          onChange={(accountEquity) => onChange({ accountEquity })}
          suffix="USD"
          value={form.accountEquity}
        />
        <NumberInput
          label={t("maxRiskPerTrade")}
          onChange={(maxRiskPerTradePct) => onChange({ maxRiskPerTradePct })}
          suffix="%"
          value={form.maxRiskPerTradePct}
        />
        <NumberInput
          label={t("maxPortfolioRisk")}
          onChange={(maxTotalRiskPct) => onChange({ maxTotalRiskPct })}
          suffix="%"
          value={form.maxTotalRiskPct}
        />
        <NumberInput
          label={t("maxOpenPositions")}
          onChange={(maxOpenPositions) => onChange({ maxOpenPositions })}
          value={form.maxOpenPositions}
        />
        <NumberInput
          label={t("maxRiskDistance")}
          onChange={(maxRiskDistancePct) => onChange({ maxRiskDistancePct })}
          suffix="%"
          value={form.maxRiskDistancePct}
        />
      </div>
      <label className="mt-4 flex items-center gap-2 text-sm font-medium text-ink">
        <input
          checked={form.shadowOnlyRequiresPaper}
          className="h-4 w-4 accent-teal"
          onChange={(event) => onChange({ shadowOnlyRequiresPaper: event.target.checked })}
          type="checkbox"
        />
        {t("shadowOnlyRequiresPaper")}
      </label>
      <div className="mt-4 flex items-center gap-3">
        <button
          className="focus-ring inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isLoading || isPending}
          onClick={onSave}
          type="button"
        >
          {isPending ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
          {isPending ? t("saving") : t("saveRiskSettings")}
        </button>
        {isError ? <span className="text-sm font-medium text-rose-700">{t("riskSettingsSaveFailed")}</span> : null}
        {isSuccess ? <span className="text-sm font-medium text-teal-700">{t("riskSettingsSaved")}</span> : null}
      </div>
    </div>
  );
}
