import { localeTag, type Locale } from "@/lib/i18n-config";

type DetailLabeler = (group: "plan" | "status", value: string | null | undefined) => string;

export function formatValue(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

export function formatNumber(value: number | null | undefined, digits = 1, locale: Locale = "en") {
  if (value === null || value === undefined) {
    return "-";
  }
  return new Intl.NumberFormat(localeTag[locale], {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0
  }).format(value);
}

export function formatDate(value: string | null | undefined, locale: Locale = "en") {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat(localeTag[locale], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function formatDateOnly(value: string | null | undefined, locale: Locale = "en") {
  if (!value) {
    return "-";
  }

  const dateMatch = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  const date = dateMatch
    ? new Date(Number(dateMatch[1]), Number(dateMatch[2]) - 1, Number(dateMatch[3]))
    : new Date(value);

  return new Intl.DateTimeFormat(localeTag[locale], {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(date);
}

export function nestedRecord(
  data: Record<string, unknown> | null | undefined,
  key: string
): Record<string, unknown> | null {
  const value = data?.[key];
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

export function numberFromRecord(data: Record<string, unknown> | null | undefined, key: string) {
  const value = data?.[key];
  return typeof value === "number" ? value : null;
}

export function stringFromRecord(data: Record<string, unknown> | null | undefined, key: string) {
  const value = data?.[key];
  return typeof value === "string" ? value : null;
}

export function formatDetailValue(value: unknown, locale: Locale, labelFor: DetailLabeler): string {
  if (typeof value === "number") {
    return formatNumber(value, 3, locale);
  }
  if (typeof value === "boolean") {
    return labelFor("plan", value ? "true" : "false");
  }
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (Array.isArray(value)) {
    return value.map((item) => formatDetailValue(item, locale, labelFor)).join(", ");
  }
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .filter(([, nestedValue]) => nestedValue !== null && nestedValue !== undefined && nestedValue !== "")
      .map(([nestedKey, nestedValue]) => `${labelFor("plan", nestedKey)}: ${formatDetailValue(nestedValue, locale, labelFor)}`)
      .join(" / ");
  }
  const raw = String(value);
  const planLabel = labelFor("plan", raw);
  if (planLabel !== raw) {
    return planLabel;
  }
  return labelFor("status", raw);
}
