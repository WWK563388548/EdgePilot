import { formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";

export function formatPercent(value: number | null, locale: Locale) {
  if (value === null) {
    return "-";
  }
  return `${formatNumber(value * 100, 1, locale)}%`;
}

export function formatMultiple(value: number | null, locale: Locale) {
  if (value === null) {
    return "-";
  }
  return `${formatNumber(value, 2, locale)}x`;
}
