"use client";

import { Database, KeyRound, Loader2, PlugZap, Save } from "lucide-react";

import { StatusPill } from "@/components/workspace/atoms/status-pill";
import type { DataSourceCheckResponse, TenantApiKey, TenantDataCapability } from "@/lib/api";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

import { capabilityTone, errorText, formatDateTime, labelCapabilityStatus } from "./settings-helpers";

export type CredentialFormState = {
  apiKey: string;
  label: string;
};

export type CheckState = {
  data?: DataSourceCheckResponse;
  error: unknown;
  isError: boolean;
  isPending: boolean;
  variables?: string;
};

export type SaveCredentialState = {
  error: unknown;
  isError: boolean;
  isPending: boolean;
  isSuccess: boolean;
};

export function DataCapabilityMatrix({
  checkState,
  capabilities,
  isLoading,
  locale,
  onCheckCapability
}: {
  capabilities: TenantDataCapability[];
  checkState: CheckState;
  isLoading: boolean;
  locale: Locale;
  onCheckCapability: (capabilityKey: string) => void;
}) {
  const { t } = useAppI18n();

  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-ink">{t("dataCapabilityMatrix")}</h2>
          <p className="mt-1 text-xs text-slate-600">{t("dataCapabilityMatrixHelp")}</p>
        </div>
        <Database size={18} className="text-teal" />
      </div>
      <div className="grid gap-3">
        {capabilities.map((capability) => (
          <div
            className="grid gap-2 rounded-md border border-line bg-panel p-3 sm:grid-cols-[1fr_auto]"
            key={capability.capability_id}
          >
            <div>
              <div className="text-sm font-semibold text-ink">{capability.capability_key}</div>
              <div className="mt-1 text-xs text-slate-600">
                {[capability.provider, capability.market, capability.asset_type, capability.timeframe]
                  .filter(Boolean)
                  .join(" · ") || "-"}
              </div>
              <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
                <span>
                  {t("dataSourceSource")}: {capability.source ?? "-"}
                </span>
                <span>
                  {t("dataSourceLastChecked")}: {formatDateTime(capability.last_checked_at, locale)}
                </span>
              </div>
              {capability.reason ? (
                <div className="mt-2 text-xs leading-5 text-slate-600">{capability.reason}</div>
              ) : null}
            </div>
            <div className="flex items-center gap-2 sm:justify-end">
              <StatusPill
                label={labelCapabilityStatus(capability.status, locale)}
                tone={capabilityTone(capability.status)}
              />
              {capability.capability_key === "market_data.us_etf_daily" ? (
                <button
                  className="focus-ring inline-flex h-8 items-center gap-2 rounded-md border border-line bg-white px-2 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={checkState.isPending}
                  onClick={() => onCheckCapability(capability.capability_key)}
                  type="button"
                >
                  {checkState.isPending && checkState.variables === capability.capability_key ? (
                    <Loader2 className="animate-spin" size={14} />
                  ) : (
                    <PlugZap size={14} />
                  )}
                  {t("checkConnection")}
                </button>
              ) : null}
            </div>
          </div>
        ))}
        {isLoading ? <div className="text-sm font-medium text-slate-600">{t("loading")}</div> : null}
        {!isLoading && !capabilities.length ? (
          <div className="text-sm font-medium text-slate-600">{t("noDataCapabilities")}</div>
        ) : null}
        {checkState.isError ? (
          <div className="text-xs font-medium text-rose-700">
            {t("capabilityCheckFailed")}: {errorText(checkState.error)}
          </div>
        ) : null}
        {checkState.data ? (
          <div className="text-xs font-medium text-teal-700">
            {t("checkResult")}: {labelCapabilityStatus(checkState.data.status, locale)}
            {checkState.data.message ? ` · ${checkState.data.message}` : ""}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function ConnectionsCard({
  apiBaseUrl,
  checkCredentialState,
  credentialForm,
  credentials,
  isCredentialsLoading,
  locale,
  onCheckCredential,
  onCredentialChange,
  onSaveCredential,
  polygonCredentialCount,
  polygonUsesEnv,
  saveCredentialState,
  sseUrl
}: {
  apiBaseUrl: string;
  checkCredentialState: CheckState;
  credentialForm: CredentialFormState;
  credentials: TenantApiKey[];
  isCredentialsLoading: boolean;
  locale: Locale;
  onCheckCredential: (credentialId: string) => void;
  onCredentialChange: (patch: Partial<CredentialFormState>) => void;
  onSaveCredential: () => void;
  polygonCredentialCount: number;
  polygonUsesEnv: boolean;
  saveCredentialState: SaveCredentialState;
  sseUrl: string;
}) {
  const { t } = useAppI18n();

  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-ink">{t("connections")}</h2>
          <p className="mt-1 text-xs text-slate-600">{t("connectionsHelp")}</p>
        </div>
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
        <div className="flex items-center justify-between border-t border-line pt-3">
          <span className="inline-flex items-center gap-2 text-sm font-medium text-ink">
            <KeyRound size={15} />
            {t("byokCredentials")}
          </span>
          <StatusPill
            label={credentials.length ? t("configured") : t("notConfigured")}
            tone={credentials.length ? "good" : "neutral"}
          />
        </div>
        <div className="grid gap-2 rounded-md border border-line bg-panel p-3">
          {polygonUsesEnv ? (
            <div className="rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-xs leading-5 text-sky-900">
              {t(polygonCredentialCount > 0 ? "envKeyOverridesSavedCredential" : "envKeyPriorityHelp")}
            </div>
          ) : null}
          <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
            <label className="grid gap-1 text-xs font-semibold text-slate-600">
              {t("credentialLabel")}
              <input
                className="focus-ring h-9 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink outline-none"
                onChange={(event) => onCredentialChange({ label: event.target.value })}
                value={credentialForm.label}
              />
            </label>
            <label className="grid gap-1 text-xs font-semibold text-slate-600">
              {t("polygonApiKey")}
              <input
                className="focus-ring h-9 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink outline-none"
                onChange={(event) => onCredentialChange({ apiKey: event.target.value })}
                placeholder="••••••••"
                type="password"
                value={credentialForm.apiKey}
              />
            </label>
            <button
              className="focus-ring mt-auto inline-flex h-9 items-center justify-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
              disabled={!credentialForm.apiKey || saveCredentialState.isPending}
              onClick={onSaveCredential}
              type="button"
            >
              {saveCredentialState.isPending ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
              {t("saveCredential")}
            </button>
          </div>
          {saveCredentialState.isError ? (
            <div className="text-xs font-medium text-rose-700">
              {t("credentialSaveFailed")}: {errorText(saveCredentialState.error)}
            </div>
          ) : null}
          {saveCredentialState.isSuccess ? (
            <div className="text-xs font-medium text-teal-700">{t("credentialSaved")}</div>
          ) : null}
          <div className="grid gap-2">
            {credentials.map((credential) => (
              <div
                className="flex flex-col gap-2 rounded-md border border-line bg-white p-2 sm:flex-row sm:items-center sm:justify-between"
                key={credential.credential_id}
              >
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-ink">
                    {credential.label ?? credential.provider}
                  </div>
                  <div className="text-xs text-slate-500">
                    {credential.provider} · {credential.key_fingerprint ?? "-"} · {t("dataSourceLastChecked")}:{" "}
                    {formatDateTime(credential.last_verified_at, locale)}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusPill
                    label={credential.status ?? t("unknown")}
                    tone={credential.status === "configured" ? "good" : "neutral"}
                  />
                  <button
                    className="focus-ring inline-flex h-8 items-center gap-2 rounded-md border border-line bg-white px-2 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={checkCredentialState.isPending}
                    onClick={() => onCheckCredential(credential.credential_id)}
                    type="button"
                  >
                    {checkCredentialState.isPending &&
                    checkCredentialState.variables === credential.credential_id ? (
                      <Loader2 className="animate-spin" size={14} />
                    ) : (
                      <PlugZap size={14} />
                    )}
                    {t("testCredential")}
                  </button>
                </div>
              </div>
            ))}
            {!isCredentialsLoading && !credentials.length ? (
              <div className="text-xs font-medium text-slate-600">{t("noCredentials")}</div>
            ) : null}
            {checkCredentialState.isError ? (
              <div className="text-xs font-medium text-rose-700">
                {t("credentialCheckFailed")}: {errorText(checkCredentialState.error)}
              </div>
            ) : null}
            {checkCredentialState.data ? (
              <div className="text-xs font-medium text-teal-700">
                {t("checkResult")}: {labelCapabilityStatus(checkCredentialState.data.status, locale)}
                {checkCredentialState.data.message ? ` · ${checkCredentialState.data.message}` : ""}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
