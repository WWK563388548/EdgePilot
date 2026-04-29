"use client";

import { BookOpen, CircleDot } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function StatusPill({
  label,
  tone = "neutral"
}: {
  label: string;
  tone?: "good" | "warn" | "bad" | "neutral";
}) {
  const variants = {
    good: "success",
    warn: "warning",
    bad: "destructive",
    neutral: "default"
  } as const;

  return <Badge variant={variants[tone]}>{label}</Badge>;
}

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
    return <span className="text-sm text-slate-500">{t("loading")}</span>;
  }
  if (isError) {
    return <span className="text-sm text-rose-700">{t("apiUnavailable")}</span>;
  }
  return null;
}

export function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="mb-3 flex items-center justify-between text-slate-500">
        {icon}
        <CircleDot size={14} />
      </div>
      <div className="text-2xl font-semibold text-ink">{value}</div>
      <div className="mt-1 text-sm text-slate-600">{label}</div>
    </div>
  );
}

export function CompactStat({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-line bg-white px-4 py-3 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="mb-2 flex items-center justify-between text-slate-500">
        {icon}
        <span className="text-xs uppercase">{label}</span>
      </div>
      <div className="truncate text-xl font-semibold text-ink">{value}</div>
    </div>
  );
}

export function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium text-ink">{formatValue(value)}</dd>
    </div>
  );
}

export function TableShell({
  title,
  loading,
  error,
  locale,
  children
}: {
  title: string;
  loading: boolean;
  error: boolean;
  locale: Locale;
  children: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-md border border-line bg-white shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="flex items-center justify-between gap-3 border-b border-line bg-white px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <BookOpen size={18} className="shrink-0 text-teal" />
          <h2 className="truncate text-base font-semibold text-ink">{title}</h2>
        </div>
        <DataState isLoading={loading} isError={error} locale={locale} />
      </div>
      <div className="overflow-x-auto">{children}</div>
    </section>
  );
}
