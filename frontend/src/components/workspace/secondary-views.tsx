"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, PlugZap, Save, Settings } from "lucide-react";
import { useEffect, useState } from "react";

import { Field } from "@/components/workspace/atoms/field";
import { StatusPill } from "@/components/workspace/atoms/status-pill";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function SettingsPanel({ locale }: { locale: Locale }) {
  const { t } = useAppI18n();
  const auth = useAuth();
  const queryClient = useQueryClient();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const sseUrl =
    process.env.NEXT_PUBLIC_SSE_URL ?? "http://localhost:8000/api/realtime/events/stream";
  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "EdgePilot";
  const riskSettings = useQuery({
    queryKey: ["risk-settings"],
    queryFn: api.riskSettings
  });
  const [riskForm, setRiskForm] = useState({
    accountEquity: "",
    maxOpenPositions: "",
    maxRiskDistancePct: "",
    maxRiskPerTradePct: "",
    maxTotalRiskPct: "",
    shadowOnlyRequiresPaper: true
  });
  useEffect(() => {
    if (!riskSettings.data) {
      return;
    }
    setRiskForm({
      accountEquity: String(riskSettings.data.account_equity),
      maxOpenPositions: String(riskSettings.data.max_open_positions),
      maxRiskDistancePct: String(riskSettings.data.max_risk_distance_pct * 100),
      maxRiskPerTradePct: String(riskSettings.data.max_risk_per_trade_pct * 100),
      maxTotalRiskPct: String(riskSettings.data.max_total_risk_pct * 100),
      shadowOnlyRequiresPaper: riskSettings.data.shadow_only_requires_paper
    });
  }, [riskSettings.data]);
  const updateRiskSettings = useMutation({
    mutationFn: () =>
      api.updateRiskSettings({
        account_equity: numberOrUndefined(riskForm.accountEquity),
        max_open_positions: numberOrUndefined(riskForm.maxOpenPositions),
        max_risk_distance_pct: percentOrUndefined(riskForm.maxRiskDistancePct),
        max_risk_per_trade_pct: percentOrUndefined(riskForm.maxRiskPerTradePct),
        max_total_risk_pct: percentOrUndefined(riskForm.maxTotalRiskPct),
        shadow_only_requires_paper: riskForm.shadowOnlyRequiresPaper
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["risk-settings"] }),
        queryClient.invalidateQueries({ queryKey: ["candidate-plan-preview"] }),
        queryClient.invalidateQueries({ queryKey: ["portfolio-risk"] }),
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] })
      ]);
    }
  });

  return (
    <section className="grid gap-4 lg:grid-cols-2">
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
            onChange={(accountEquity) => setRiskForm((value) => ({ ...value, accountEquity }))}
            suffix="USD"
            value={riskForm.accountEquity}
          />
          <NumberInput
            label={t("maxRiskPerTrade")}
            onChange={(maxRiskPerTradePct) => setRiskForm((value) => ({ ...value, maxRiskPerTradePct }))}
            suffix="%"
            value={riskForm.maxRiskPerTradePct}
          />
          <NumberInput
            label={t("maxPortfolioRisk")}
            onChange={(maxTotalRiskPct) => setRiskForm((value) => ({ ...value, maxTotalRiskPct }))}
            suffix="%"
            value={riskForm.maxTotalRiskPct}
          />
          <NumberInput
            label={t("maxOpenPositions")}
            onChange={(maxOpenPositions) => setRiskForm((value) => ({ ...value, maxOpenPositions }))}
            value={riskForm.maxOpenPositions}
          />
          <NumberInput
            label={t("maxRiskDistance")}
            onChange={(maxRiskDistancePct) => setRiskForm((value) => ({ ...value, maxRiskDistancePct }))}
            suffix="%"
            value={riskForm.maxRiskDistancePct}
          />
        </div>
        <label className="mt-4 flex items-center gap-2 text-sm font-medium text-ink">
          <input
            checked={riskForm.shadowOnlyRequiresPaper}
            className="h-4 w-4 accent-teal"
            onChange={(event) =>
              setRiskForm((value) => ({
                ...value,
                shadowOnlyRequiresPaper: event.target.checked
              }))
            }
            type="checkbox"
          />
          {t("shadowOnlyRequiresPaper")}
        </label>
        <div className="mt-4 flex items-center gap-3">
          <button
            className="focus-ring inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
            disabled={riskSettings.isLoading || updateRiskSettings.isPending}
            onClick={() => updateRiskSettings.mutate()}
            type="button"
          >
            {updateRiskSettings.isPending ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
            {updateRiskSettings.isPending ? t("saving") : t("saveRiskSettings")}
          </button>
          {updateRiskSettings.isError ? (
            <span className="text-sm font-medium text-rose-700">{t("riskSettingsSaveFailed")}</span>
          ) : null}
          {updateRiskSettings.isSuccess ? (
            <span className="text-sm font-medium text-teal-700">{t("riskSettingsSaved")}</span>
          ) : null}
        </div>
      </div>

      <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">{t("runtime")}</h2>
          <Settings size={18} className="text-teal" />
        </div>
        <dl className="grid gap-3">
          <Field label={t("app")} value={appName} />
          <Field label={t("apiBaseUrl")} value={apiBaseUrl} />
          <Field label={t("sseUrl")} value={sseUrl} />
          <Field label={t("auth")} value={t("authRequired")} />
          <Field label={t("user")} value={auth.userLabel} />
          <Field label={t("email")} value={auth.emailVerified ? t("emailVerified") : t("emailPending")} />
        </dl>
      </div>

      <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">{t("connections")}</h2>
          <PlugZap size={18} className="text-teal" />
        </div>
        <div className="grid gap-3">
          <div className="flex items-center justify-between border-b border-line pb-3">
            <span className="text-sm font-medium text-ink">{t("backendApi")}</span>
            <StatusPill label={apiBaseUrl ? t("configured") : t("missing")} tone={apiBaseUrl ? "good" : "bad"} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-ink">{t("realtimeStream")}</span>
            <StatusPill label={sseUrl ? t("configured") : t("missing")} tone={sseUrl ? "good" : "bad"} />
          </div>
        </div>
      </div>
    </section>
  );
}

function NumberInput({
  label,
  onChange,
  suffix,
  value
}: {
  label: string;
  onChange: (value: string) => void;
  suffix?: string;
  value: string;
}) {
  return (
    <label className="grid gap-1 text-xs font-semibold text-slate-600">
      {label}
      <div className="flex overflow-hidden rounded-md border border-line bg-white">
        <input
          className="focus-ring h-9 min-w-0 flex-1 border-0 px-2 text-sm font-medium text-ink outline-none"
          min="0"
          onChange={(event) => onChange(event.target.value)}
          step="0.01"
          type="number"
          value={value}
        />
        {suffix ? (
          <span className="flex items-center border-l border-line bg-panel px-2 text-xs text-slate-500">
            {suffix}
          </span>
        ) : null}
      </div>
    </label>
  );
}

function numberOrUndefined(value: string) {
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : undefined;
}

function percentOrUndefined(value: string) {
  const numeric = numberOrUndefined(value);
  return numeric === undefined ? undefined : numeric / 100;
}
