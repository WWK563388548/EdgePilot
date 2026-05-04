import { BookOpen } from "lucide-react";
import type { ReactNode } from "react";

import { DataState } from "@/components/workspace/atoms/data-state";
import type { Locale } from "@/lib/i18n-config";

export function TableShell({
  title,
  loading,
  error,
  locale,
  actions,
  children
}: {
  title: string;
  loading: boolean;
  error: boolean;
  locale: Locale;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-md border border-line bg-white shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="flex items-center justify-between gap-3 border-b border-line bg-white px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <BookOpen size={18} className="shrink-0 text-teal" />
          <h2 className="truncate text-base font-semibold text-ink">{title}</h2>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {actions}
          <DataState isLoading={loading} isError={error} locale={locale} />
        </div>
      </div>
      <div className="overflow-x-auto">{children}</div>
    </section>
  );
}
