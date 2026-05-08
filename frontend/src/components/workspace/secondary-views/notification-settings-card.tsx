"use client";

import { Loader2, Save, Settings } from "lucide-react";

import { useAppI18n } from "@/lib/use-app-i18n";

export type NotificationFormState = {
  emailEnabled: boolean;
  emailTo: string;
  inAppEnabled: boolean;
  minSeverity: string;
  smsEnabled: boolean;
};

export function NotificationSettingsCard({
  form,
  isError,
  isLoading,
  isPending,
  isSuccess,
  onChange,
  onSave
}: {
  form: NotificationFormState;
  isError: boolean;
  isLoading: boolean;
  isPending: boolean;
  isSuccess: boolean;
  onChange: (patch: Partial<NotificationFormState>) => void;
  onSave: () => void;
}) {
  const { t } = useAppI18n();

  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-ink">{t("notificationSettings")}</h2>
          <p className="mt-1 text-xs text-slate-600">{t("notificationSettingsHelp")}</p>
        </div>
        <Settings size={18} className="text-teal" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex items-center gap-2 text-sm font-medium text-ink">
          <input
            checked={form.inAppEnabled}
            className="h-4 w-4 accent-teal"
            onChange={(event) => onChange({ inAppEnabled: event.target.checked })}
            type="checkbox"
          />
          {t("inAppNotifications")}
        </label>
        <label className="flex items-center gap-2 text-sm font-medium text-ink">
          <input
            checked={form.emailEnabled}
            className="h-4 w-4 accent-teal"
            onChange={(event) => onChange({ emailEnabled: event.target.checked })}
            type="checkbox"
          />
          {t("emailNotifications")}
        </label>
        <label className="grid gap-1 text-xs font-semibold text-slate-600">
          {t("minSeverity")}
          <select
            className="focus-ring h-9 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink outline-none"
            onChange={(event) => onChange({ minSeverity: event.target.value })}
            value={form.minSeverity}
          >
            <option value="info">{t("severityInfo")}</option>
            <option value="warning">{t("severityWarning")}</option>
            <option value="action_required">{t("severityActionRequired")}</option>
          </select>
        </label>
        <label className="grid gap-1 text-xs font-semibold text-slate-600">
          {t("emailTo")}
          <input
            className="focus-ring h-9 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink outline-none"
            onChange={(event) => onChange({ emailTo: event.target.value })}
            placeholder="alerts@example.com"
            type="email"
            value={form.emailTo}
          />
        </label>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-600">{t("externalDeliveryNotLive")}</p>
      <div className="mt-4 flex items-center gap-3">
        <button
          className="focus-ring inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isLoading || isPending}
          onClick={onSave}
          type="button"
        >
          {isPending ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
          {isPending ? t("saving") : t("saveNotificationSettings")}
        </button>
        {isError ? (
          <span className="text-sm font-medium text-rose-700">{t("notificationSettingsSaveFailed")}</span>
        ) : null}
        {isSuccess ? (
          <span className="text-sm font-medium text-teal-700">{t("notificationSettingsSaved")}</span>
        ) : null}
      </div>
    </div>
  );
}
