"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import {
  ConnectionsCard,
  DataCapabilityMatrix,
  type CredentialFormState
} from "@/components/workspace/secondary-views/data-source-cards";
import {
  NotificationSettingsCard,
  type NotificationFormState
} from "@/components/workspace/secondary-views/notification-settings-card";
import {
  RiskGuardrailsCard,
  type RiskFormState
} from "@/components/workspace/secondary-views/risk-guardrails-card";
import { RuntimeCard, WorkspaceBoundaryCard } from "@/components/workspace/secondary-views/settings-info-cards";
import { numberOrUndefined, percentOrUndefined } from "@/components/workspace/secondary-views/settings-helpers";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function SettingsPanel({ locale }: { locale: Locale }) {
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
  const authMe = useQuery({
    queryKey: ["auth-me"],
    queryFn: api.me
  });
  const currentTenant = useQuery({
    queryKey: ["current-tenant"],
    queryFn: api.currentTenant
  });
  const dataCapabilities = useQuery({
    queryKey: ["data-capabilities"],
    queryFn: api.dataCapabilities
  });
  const dataCredentials = useQuery({
    queryKey: ["data-credentials"],
    queryFn: api.dataCredentials
  });
  const notificationPreferences = useQuery({
    queryKey: ["notification-preferences"],
    queryFn: api.notificationPreferences
  });
  const [riskForm, setRiskForm] = useState<RiskFormState>({
    accountEquity: "",
    maxOpenPositions: "",
    maxRiskDistancePct: "",
    maxRiskPerTradePct: "",
    maxTotalRiskPct: "",
    shadowOnlyRequiresPaper: true
  });
  const [notificationForm, setNotificationForm] = useState<NotificationFormState>({
    emailEnabled: false,
    emailTo: "",
    inAppEnabled: true,
    minSeverity: "info",
    smsEnabled: false
  });
  const [credentialForm, setCredentialForm] = useState<CredentialFormState>({
    apiKey: "",
    label: "Polygon"
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

  useEffect(() => {
    if (!notificationPreferences.data) {
      return;
    }
    setNotificationForm({
      emailEnabled: notificationPreferences.data.email_enabled,
      emailTo: notificationPreferences.data.email_to ?? "",
      inAppEnabled: notificationPreferences.data.in_app_enabled,
      minSeverity: notificationPreferences.data.min_severity,
      smsEnabled: notificationPreferences.data.sms_enabled
    });
  }, [notificationPreferences.data]);

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
  const updateNotificationPreferences = useMutation({
    mutationFn: () =>
      api.updateNotificationPreferences({
        email_enabled: notificationForm.emailEnabled,
        email_to: notificationForm.emailTo || null,
        in_app_enabled: notificationForm.inAppEnabled,
        min_severity: notificationForm.minSeverity as "info" | "warning" | "action_required",
        sms_enabled: notificationForm.smsEnabled
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
    }
  });
  const createDataCredential = useMutation({
    mutationFn: () =>
      api.createDataCredential({
        provider: "polygon",
        label: credentialForm.label || "Polygon",
        encrypted_payload: credentialForm.apiKey || undefined
      }),
    onSuccess: async () => {
      setCredentialForm((value) => ({ ...value, apiKey: "" }));
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["data-credentials"] }),
        queryClient.invalidateQueries({ queryKey: ["data-capabilities"] })
      ]);
    }
  });
  const checkDataCapability = useMutation({
    mutationFn: (capabilityKey: string) => api.checkDataCapability(capabilityKey),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["data-capabilities"] }),
        queryClient.invalidateQueries({ queryKey: ["data-credentials"] })
      ]);
    }
  });
  const checkDataCredential = useMutation({
    mutationFn: (credentialId: string) => api.checkDataCredential(credentialId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["data-capabilities"] }),
        queryClient.invalidateQueries({ queryKey: ["data-credentials"] })
      ]);
    }
  });
  const polygonCapability = dataCapabilities.data?.find(
    (capability) => capability.capability_key === "market_data.us_etf_daily"
  );
  const polygonUsesEnv = polygonCapability?.source === "env";
  const polygonCredentialCount =
    dataCredentials.data?.filter((credential) => credential.provider === "polygon").length ?? 0;

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <RiskGuardrailsCard
        form={riskForm}
        isError={updateRiskSettings.isError}
        isLoading={riskSettings.isLoading}
        isPending={updateRiskSettings.isPending}
        isSuccess={updateRiskSettings.isSuccess}
        onChange={(patch) => setRiskForm((value) => ({ ...value, ...patch }))}
        onSave={() => updateRiskSettings.mutate()}
      />
      <NotificationSettingsCard
        form={notificationForm}
        isError={updateNotificationPreferences.isError}
        isLoading={notificationPreferences.isLoading}
        isPending={updateNotificationPreferences.isPending}
        isSuccess={updateNotificationPreferences.isSuccess}
        onChange={(patch) => setNotificationForm((value) => ({ ...value, ...patch }))}
        onSave={() => updateNotificationPreferences.mutate()}
      />
      <WorkspaceBoundaryCard
        accountId={authMe.data?.account_id ?? "-"}
        tenantId={currentTenant.data?.tenant_id ?? "-"}
        tenantName={currentTenant.data?.name ?? "-"}
      />
      <DataCapabilityMatrix
        capabilities={dataCapabilities.data ?? []}
        checkState={{
          data: checkDataCapability.data,
          error: checkDataCapability.error,
          isError: checkDataCapability.isError,
          isPending: checkDataCapability.isPending,
          variables: checkDataCapability.variables
        }}
        isLoading={dataCapabilities.isLoading}
        locale={locale}
        onCheckCapability={(capabilityKey) => checkDataCapability.mutate(capabilityKey)}
      />
      <RuntimeCard
        apiBaseUrl={apiBaseUrl}
        appName={appName}
        emailVerified={auth.emailVerified}
        sseUrl={sseUrl}
        userLabel={auth.userLabel}
      />
      <ConnectionsCard
        apiBaseUrl={apiBaseUrl}
        checkCredentialState={{
          data: checkDataCredential.data,
          error: checkDataCredential.error,
          isError: checkDataCredential.isError,
          isPending: checkDataCredential.isPending,
          variables: checkDataCredential.variables
        }}
        credentialForm={credentialForm}
        credentials={dataCredentials.data ?? []}
        isCredentialsLoading={dataCredentials.isLoading}
        locale={locale}
        onCheckCredential={(credentialId) => checkDataCredential.mutate(credentialId)}
        onCredentialChange={(patch) => setCredentialForm((value) => ({ ...value, ...patch }))}
        onSaveCredential={() => createDataCredential.mutate()}
        polygonCredentialCount={polygonCredentialCount}
        polygonUsesEnv={Boolean(polygonUsesEnv)}
        saveCredentialState={{
          error: createDataCredential.error,
          isError: createDataCredential.isError,
          isPending: createDataCredential.isPending,
          isSuccess: createDataCredential.isSuccess
        }}
        sseUrl={sseUrl}
      />
    </section>
  );
}
