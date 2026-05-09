"use client";

import { CircleDollarSign, Loader2, X } from "lucide-react";
import type { ReactNode } from "react";

import type { useAppI18n } from "@/lib/use-app-i18n";

export const secondaryButton =
  "focus-ring inline-flex h-8 items-center gap-1.5 rounded-md border border-line bg-white px-2.5 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60";
export const dangerButton =
  "focus-ring inline-flex h-8 items-center gap-1.5 rounded-md border border-rose-200 bg-white px-2.5 text-xs font-semibold text-rose-700 transition-colors hover:border-rose-400 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60";
const primaryButton =
  "focus-ring inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60";

export function ActionPanel({
  busy,
  children,
  description,
  failed,
  onCancel,
  onSubmit,
  submitLabel,
  title,
  t
}: {
  busy: boolean;
  children: ReactNode;
  description: string;
  failed: boolean;
  onCancel: () => void;
  onSubmit: () => void;
  submitLabel: string;
  title: string;
  t: ReturnType<typeof useAppI18n>["t"];
}) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-ink">{title}</p>
        <p className="mt-1 text-xs leading-5 text-slate-600">{description}</p>
        {failed ? <p className="mt-2 text-sm font-medium text-rose-700">{t("positionActionFailed")}</p> : null}
      </div>
      <div className="flex flex-wrap items-end gap-3">{children}</div>
      <div className="flex gap-2">
        <button className={primaryButton} disabled={busy} onClick={onSubmit} type="button">
          {busy ? <Loader2 className="animate-spin" size={15} /> : <CircleDollarSign size={15} />}
          {busy ? t("saving") : submitLabel}
        </button>
        <button className={secondaryButton} disabled={busy} onClick={onCancel} type="button">
          <X size={15} />
          {t("cancel")}
        </button>
      </div>
    </div>
  );
}

export function NumberInput({
  label,
  onChange,
  value
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="grid gap-1 text-xs font-semibold text-slate-600">
      {label}
      <input
        className="focus-ring h-9 w-32 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink"
        min="0"
        onChange={(event) => onChange(event.target.value)}
        step="0.01"
        type="number"
        value={value}
      />
    </label>
  );
}

export function DateInput({
  label,
  onChange,
  value
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="grid gap-1 text-xs font-semibold text-slate-600">
      {label}
      <input
        className="focus-ring h-9 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink"
        onChange={(event) => onChange(event.target.value)}
        type="datetime-local"
        value={value}
      />
    </label>
  );
}

export function TextInput({
  label,
  onChange,
  value
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="grid gap-1 text-xs font-semibold text-slate-600">
      {label}
      <input
        className="focus-ring h-9 w-40 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink"
        onChange={(event) => onChange(event.target.value)}
        type="text"
        value={value}
      />
    </label>
  );
}

export function datetimeLocalValue(date: Date) {
  const timezoneOffsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - timezoneOffsetMs).toISOString().slice(0, 16);
}

export function isoDatetime(value: string) {
  return value ? new Date(value).toISOString() : undefined;
}

export function positiveNumber(value: string) {
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : null;
}

export function optionalPositiveNumber(value: string) {
  if (!value) {
    return undefined;
  }
  return positiveNumber(value);
}
