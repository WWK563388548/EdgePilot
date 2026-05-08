"use client";

import { Building2, Settings } from "lucide-react";

import { Field } from "@/components/workspace/atoms/field";
import { useAppI18n } from "@/lib/use-app-i18n";

export function WorkspaceBoundaryCard({
  accountId,
  tenantId,
  tenantName
}: {
  accountId: string;
  tenantId: string;
  tenantName: string;
}) {
  const { t } = useAppI18n();

  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-ink">{t("workspaceBoundary")}</h2>
          <p className="mt-1 text-xs text-slate-600">{t("workspaceBoundaryHelp")}</p>
        </div>
        <Building2 size={18} className="text-teal" />
      </div>
      <dl className="grid gap-3">
        <Field label={t("tenantName")} value={tenantName} />
        <Field label={t("tenantId")} value={tenantId} />
        <Field label={t("account")} value={accountId} />
      </dl>
    </div>
  );
}

export function RuntimeCard({
  apiBaseUrl,
  appName,
  emailVerified,
  sseUrl,
  userLabel
}: {
  apiBaseUrl: string;
  appName: string;
  emailVerified: boolean;
  sseUrl: string;
  userLabel: string;
}) {
  const { t } = useAppI18n();

  return (
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
        <Field label={t("user")} value={userLabel} />
        <Field label={t("email")} value={emailVerified ? t("emailVerified") : t("emailPending")} />
      </dl>
    </div>
  );
}
