"use client";

import { useAppI18n } from "@/lib/use-app-i18n";

export function PaginationControls({
  hasNext,
  itemCount,
  page,
  pageSize,
  onPageChange
}: {
  hasNext: boolean;
  itemCount: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}) {
  const { t } = useAppI18n();
  const start = itemCount ? page * pageSize + 1 : 0;
  const end = page * pageSize + itemCount;

  return (
    <div className="flex flex-col gap-2 border-t border-line bg-white px-4 py-3 text-sm text-slate-600 sm:flex-row sm:items-center sm:justify-between">
      <span>
        {t("pageSummary", {
          end,
          page: page + 1,
          start
        })}
      </span>
      <div className="flex items-center gap-2">
        <button
          className="focus-ring h-8 rounded-md border border-line bg-white px-3 font-semibold text-ink transition-colors hover:border-slate-400 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={page === 0}
          onClick={() => onPageChange(Math.max(0, page - 1))}
          type="button"
        >
          {t("previousPage")}
        </button>
        <button
          className="focus-ring h-8 rounded-md border border-line bg-white px-3 font-semibold text-ink transition-colors hover:border-slate-400 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!hasNext}
          onClick={() => onPageChange(page + 1)}
          type="button"
        >
          {t("nextPage")}
        </button>
      </div>
    </div>
  );
}
