"use client";

import { Eye } from "lucide-react";

import { DataState } from "@/components/workspace/atoms/data-state";
import { StatusPill } from "@/components/workspace/atoms/status-pill";
import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import type { PASetup } from "@/lib/api";
import { formatDate, formatNumber, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { decisionTone } from "@/lib/presentation";
import { useAppI18n } from "@/lib/use-app-i18n";

export function PASetupTable({
  rows,
  selectedSetupId,
  loading,
  error,
  locale,
  page,
  pageSize,
  hasNextPage,
  onPageChange,
  onSelect
}: {
  rows: PASetup[];
  selectedSetupId: string | null;
  loading: boolean;
  error: boolean;
  locale: Locale;
  page: number;
  pageSize: number;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
  onSelect: (setupId: string) => void;
}) {
  const { labelFor, t } = useAppI18n();

  return (
    <>
      <div className="overflow-x-auto">
        <table className="min-w-full table-fixed text-left text-sm">
          <thead className="bg-panel text-xs uppercase text-slate-500">
            <tr>
              <th className="w-24 px-4 py-3">{t("symbol")}</th>
              <th className="w-48 px-4 py-3">{t("setup")}</th>
              <th className="w-20 px-4 py-3">{t("grade")}</th>
              <th className="w-24 px-4 py-3">{t("score")}</th>
              <th className="w-32 px-4 py-3">{t("validation")}</th>
              <th className="w-28 px-4 py-3">{t("status")}</th>
              <th className="w-40 px-4 py-3">{t("detected")}</th>
              <th className="w-20 px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {!rows.length ? (
              <tr>
                <td className="px-4 py-6 text-sm text-slate-600" colSpan={8}>
                  {loading || error ? (
                    <DataState isLoading={loading} isError={error} locale={locale} />
                  ) : (
                    t("noSetup")
                  )}
                </td>
              </tr>
            ) : null}
            {rows.map((setup) => (
              <tr
                key={setup.setup_id}
                className={`border-t border-line transition-colors hover:bg-panel/70 ${
                  selectedSetupId === setup.setup_id ? "bg-teal-50/60" : ""
                }`}
              >
                <td className="px-4 py-3 font-semibold text-ink">{setup.symbol_id}</td>
                <td className="truncate px-4 py-3" title={setup.setup_type}>
                  {labelFor("setup", setup.setup_type)}
                </td>
                <td className="px-4 py-3">{formatValue(setup.setup_grade)}</td>
                <td className="px-4 py-3 font-medium text-ink">{formatNumber(setup.pa_quality_score, 1, locale)}</td>
                <td className="px-4 py-3">
                  <StatusPill
                    label={labelFor("status", setup.validation_status ?? "unknown")}
                    tone={decisionTone(setup.validation_status)}
                  />
                </td>
                <td className="px-4 py-3">{labelFor("status", setup.status)}</td>
                <td className="px-4 py-3">{formatDate(setup.detected_ts, locale)}</td>
                <td className="px-4 py-3">
                  <button
                    className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-slate-700 hover:border-slate-400"
                    onClick={() => onSelect(setup.setup_id)}
                    title={t("openDetail")}
                    type="button"
                  >
                    <Eye size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <PaginationControls
        hasNext={hasNextPage}
        itemCount={rows.length}
        onPageChange={onPageChange}
        page={page}
        pageSize={pageSize}
      />
    </>
  );
}
