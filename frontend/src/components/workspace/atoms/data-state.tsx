"use client";

import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function DataState({
  isLoading,
  isError,
  locale
}: {
  isLoading: boolean;
  isError: boolean;
  locale: Locale;
}) {
  const { t } = useAppI18n();

  if (isLoading) {
    return (
      <span className="text-sm text-slate-500" role="status">
        {t("loading")}
      </span>
    );
  }
  if (isError) {
    return (
      <span className="text-sm text-rose-700" role="alert">
        {t("apiUnavailable")}
      </span>
    );
  }
  return null;
}
