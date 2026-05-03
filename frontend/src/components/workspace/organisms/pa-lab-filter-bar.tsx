"use client";

import { Filter } from "lucide-react";

import { DataState } from "@/components/workspace/atoms/data-state";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function PALabFilterBar({
  symbol,
  setupType,
  validationStatus,
  loading,
  error,
  locale,
  onSymbolChange,
  onSetupTypeChange,
  onValidationStatusChange
}: {
  symbol: string;
  setupType: string;
  validationStatus: string;
  loading: boolean;
  error: boolean;
  locale: Locale;
  onSymbolChange: (value: string) => void;
  onSetupTypeChange: (value: string) => void;
  onValidationStatusChange: (value: string) => void;
}) {
  const { labelFor, t } = useAppI18n();

  return (
    <div className="border-b border-line bg-white px-4 py-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <Filter size={18} className="shrink-0 text-teal" />
          <div className="min-w-0">
            <h2 className="truncate text-base font-semibold text-ink">{t("setupExplorer")}</h2>
            <p className="text-xs text-slate-500">{t("paLabDataBoundary")}</p>
          </div>
        </div>
        <DataState isLoading={loading} isError={error} locale={locale} />
      </div>
      <div className="grid gap-2 md:grid-cols-[minmax(120px,180px)_minmax(160px,220px)_minmax(160px,220px)]">
        <input
          className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
          onChange={(event) => onSymbolChange(event.target.value)}
          placeholder={t("symbol")}
          value={symbol}
        />
        <select
          className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
          onChange={(event) => onSetupTypeChange(event.target.value)}
          value={setupType}
        >
          <option value="">{t("allSetups")}</option>
          <option value="breakout">{labelFor("setup", "breakout")}</option>
          <option value="pullback_to_20ma">{labelFor("setup", "pullback_to_20ma")}</option>
          <option value="failed_breakdown_reclaim">{labelFor("setup", "failed_breakdown_reclaim")}</option>
          <option value="oneil_leader_watch">{labelFor("setup", "oneil_leader_watch")}</option>
        </select>
        <select
          className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
          onChange={(event) => onValidationStatusChange(event.target.value)}
          value={validationStatus}
        >
          <option value="">{t("allValidation")}</option>
          <option value="shadow_only">{labelFor("status", "shadow_only")}</option>
          <option value="paper_allowed">{labelFor("status", "paper_allowed")}</option>
          <option value="live_allowed">{labelFor("status", "live_allowed")}</option>
        </select>
      </div>
    </div>
  );
}
