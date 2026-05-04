"use client";

import { PlugZap, Settings } from "lucide-react";

import { Field } from "@/components/workspace/atoms/field";
import { StatusPill } from "@/components/workspace/atoms/status-pill";
import { useAuth } from "@/lib/auth";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function SettingsPanel({ locale }: { locale: Locale }) {
  const { t } = useAppI18n();
  const auth = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const sseUrl =
    process.env.NEXT_PUBLIC_SSE_URL ?? "http://localhost:8000/api/realtime/events/stream";
  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "EdgePilot";

  return (
    <section className="grid gap-4 lg:grid-cols-2">
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
