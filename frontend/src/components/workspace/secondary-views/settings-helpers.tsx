import type { StatusTone } from "@/components/workspace/atoms/status-pill";
import { ApiError } from "@/lib/api";
import type { Locale } from "@/lib/i18n-config";

export function NumberInput({
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

export function numberOrUndefined(value: string) {
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : undefined;
}

export function percentOrUndefined(value: string) {
  const numeric = numberOrUndefined(value);
  return numeric === undefined ? undefined : numeric / 100;
}

export function capabilityTone(status: string): StatusTone {
  if (status === "available") {
    return "good";
  }
  if (status === "stale" || status === "fallback_used") {
    return "warn";
  }
  if (status === "missing" || status === "invalid") {
    return "bad";
  }
  return "neutral";
}

export function labelCapabilityStatus(status: string, locale: Locale) {
  const labels: Record<string, Record<Locale, string>> = {
    available: { zh: "可用", en: "Available", ja: "利用可" },
    disabled: { zh: "未启用", en: "Disabled", ja: "無効" },
    fallback_used: { zh: "使用回退", en: "Fallback used", ja: "代替使用" },
    invalid: { zh: "无效", en: "Invalid", ja: "無効" },
    missing: { zh: "缺失", en: "Missing", ja: "不足" },
    stale: { zh: "过期", en: "Stale", ja: "古い" }
  };
  return labels[status]?.[locale] ?? status;
}

export function formatDateTime(value: string | null | undefined, locale: Locale) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function errorText(error: unknown) {
  if (error instanceof ApiError) {
    return error.detail ?? error.message;
  }
  return error instanceof Error ? error.message : String(error);
}
