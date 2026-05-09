"use client";

import type { ExecutionImportResult } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function ExecutionImportResultSummary({
  locale,
  result
}: {
  locale: Locale;
  result: ExecutionImportResult;
}) {
  const { labelFor, t } = useAppI18n();

  return (
    <div className="rounded-md border border-teal-200 bg-teal-50 px-3 py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-teal-900">{t("importResult")}</p>
          <p className="mt-1 text-xs leading-5 text-teal-800">
            {labelFor("status", result.import_record.status)}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <ResultMetric label={t("rowsTotal")} locale={locale} value={result.import_record.rows_total} />
          <ResultMetric label={t("rowsImported")} locale={locale} value={result.import_record.rows_imported} />
          <ResultMetric label={t("rowsSkipped")} locale={locale} value={result.import_record.rows_skipped} />
          <ResultMetric label={t("rowsFailed")} locale={locale} value={result.import_record.rows_failed} />
        </div>
      </div>
      {result.errors.length ? (
        <div className="mt-3 border-t border-teal-200 pt-3">
          <p className="text-xs font-semibold uppercase text-teal-900">{t("importErrors")}</p>
          <div className="mt-2 grid gap-2">
            {result.errors.map((error) => (
              <div
                className="rounded-md border border-amber-200 bg-white px-2 py-1.5 text-xs leading-5 text-amber-900"
                key={`${error.row_number}-${error.message}`}
              >
                {t("rowNumber", { row: error.row_number })}: {error.message}
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {result.fills.length ? (
        <div className="mt-3 border-t border-teal-200 pt-3 text-xs text-teal-900">
          {t("importedFills", { count: result.fills.length })}
        </div>
      ) : null}
    </div>
  );
}

function ResultMetric({
  label,
  locale,
  value
}: {
  label: string;
  locale: Locale;
  value: number;
}) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase text-teal-700">{label}</div>
      <div className="mt-1 text-base font-bold text-ink">{formatNumber(value, 0, locale)}</div>
    </div>
  );
}
