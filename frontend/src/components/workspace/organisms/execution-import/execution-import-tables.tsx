"use client";

import { AlertTriangle } from "lucide-react";

import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import { TableShell } from "@/components/workspace/molecules/table-shell";
import type { ExecutionFill, ExecutionImport, Position } from "@/lib/api";
import { formatDate, formatNumber, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

const EXECUTION_PAGE_SIZE = 8;

export function ReviewNeededPanel({
  data,
  error,
  loading,
  locale,
  totalCount
}: {
  data: Position[];
  error: boolean;
  loading: boolean;
  locale: Locale;
  totalCount?: number;
}) {
  const { t } = useAppI18n();

  return (
    <TableShell title={t("reviewNeededPositions")} loading={loading} error={error} locale={locale}>
      <div className="border-b border-line bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
        <div className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 shrink-0" size={17} />
          <p>{t("reviewNeededHelp", { count: totalCount ?? data.length })}</p>
        </div>
      </div>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("symbol")}</th>
            <th className="px-4 py-3">{t("type")}</th>
            <th className="px-4 py-3">{t("qty")}</th>
            <th className="px-4 py-3">{t("entry")}</th>
            <th className="px-4 py-3">{t("status")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? <EmptyRow colSpan={5} message={t("noReviewNeededPositions")} /> : null}
          {data.map((row) => (
            <tr className="border-t border-line" key={row.position_id}>
              <td className="px-4 py-3 font-semibold text-ink">{row.symbol_id}</td>
              <td className="px-4 py-3">{row.asset_type}</td>
              <td className="px-4 py-3">{formatValue(row.quantity)}</td>
              <td className="px-4 py-3">{formatValue(row.entry_price)}</td>
              <td className="px-4 py-3">{t("reviewNeeded")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableShell>
  );
}

export function ExecutionImportsTable({
  data,
  error,
  hasNextPage,
  loading,
  locale,
  onPageChange,
  page,
  totalCount
}: {
  data: ExecutionImport[];
  error: boolean;
  hasNextPage: boolean;
  loading: boolean;
  locale: Locale;
  onPageChange: (page: number) => void;
  page: number;
  totalCount?: number;
}) {
  const { t } = useAppI18n();

  return (
    <TableShell title={t("importHistory")} loading={loading} error={error} locale={locale}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("time")}</th>
            <th className="px-4 py-3">{t("broker")}</th>
            <th className="px-4 py-3">{t("status")}</th>
            <th className="px-4 py-3">{t("sourceFilename")}</th>
            <th className="px-4 py-3">{t("rowsImported")}</th>
            <th className="px-4 py-3">{t("rowsSkipped")}</th>
            <th className="px-4 py-3">{t("rowsFailed")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? <EmptyRow colSpan={7} message={t("noExecutionImports")} /> : null}
          {data.map((row) => (
            <ExecutionImportRow key={row.import_id} locale={locale} row={row} />
          ))}
        </tbody>
      </table>
      <PaginationControls
        hasNext={hasNextPage}
        itemCount={data.length}
        onPageChange={onPageChange}
        page={page}
        pageSize={EXECUTION_PAGE_SIZE}
        totalCount={totalCount}
      />
    </TableShell>
  );
}

export function ExecutionFillsTable({
  data,
  error,
  hasNextPage,
  loading,
  locale,
  onPageChange,
  page,
  totalCount
}: {
  data: ExecutionFill[];
  error: boolean;
  hasNextPage: boolean;
  loading: boolean;
  locale: Locale;
  onPageChange: (page: number) => void;
  page: number;
  totalCount?: number;
}) {
  const { t } = useAppI18n();

  return (
    <TableShell title={t("fillLedger")} loading={loading} error={error} locale={locale}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("symbol")}</th>
            <th className="px-4 py-3">{t("side")}</th>
            <th className="px-4 py-3">{t("qty")}</th>
            <th className="px-4 py-3">{t("price")}</th>
            <th className="px-4 py-3">{t("fees")}</th>
            <th className="px-4 py-3">{t("position")}</th>
            <th className="px-4 py-3">{t("time")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? <EmptyRow colSpan={7} message={t("noExecutionFills")} /> : null}
          {data.map((row) => (
            <ExecutionFillRow key={row.fill_id} locale={locale} row={row} />
          ))}
        </tbody>
      </table>
      <PaginationControls
        hasNext={hasNextPage}
        itemCount={data.length}
        onPageChange={onPageChange}
        page={page}
        pageSize={EXECUTION_PAGE_SIZE}
        totalCount={totalCount}
      />
    </TableShell>
  );
}

function ExecutionImportRow({ locale, row }: { locale: Locale; row: ExecutionImport }) {
  const { labelFor } = useAppI18n();
  return (
    <tr className="border-t border-line">
      <td className="px-4 py-3">{formatDate(row.created_at, locale)}</td>
      <td className="px-4 py-3">{row.broker}</td>
      <td className="px-4 py-3">
        <span className={statusClass(row.status)}>{labelFor("status", row.status)}</span>
      </td>
      <td className="px-4 py-3">{formatValue(row.source_filename)}</td>
      <td className="px-4 py-3">{formatValue(row.rows_imported)}</td>
      <td className="px-4 py-3">{formatValue(row.rows_skipped)}</td>
      <td className="px-4 py-3">{formatValue(row.rows_failed)}</td>
    </tr>
  );
}

function ExecutionFillRow({ locale, row }: { locale: Locale; row: ExecutionFill }) {
  const { labelFor } = useAppI18n();
  return (
    <tr className="border-t border-line">
      <td className="px-4 py-3 font-semibold text-ink">{row.symbol_id}</td>
      <td className="px-4 py-3">{labelFor("plan", row.side)}</td>
      <td className="px-4 py-3">{formatNumber(row.quantity, 4, locale)}</td>
      <td className="px-4 py-3">{formatNumber(row.price, 4, locale)}</td>
      <td className="px-4 py-3">{formatValue(row.fees)}</td>
      <td className="px-4 py-3">
        <span className="inline-block max-w-56 truncate align-bottom">{formatValue(row.position_id)}</span>
      </td>
      <td className="px-4 py-3">{formatDate(row.executed_at, locale)}</td>
    </tr>
  );
}

function EmptyRow({ colSpan, message }: { colSpan: number; message: string }) {
  return (
    <tr>
      <td className="border-t border-line px-4 py-6 text-sm text-slate-600" colSpan={colSpan}>
        {message}
      </td>
    </tr>
  );
}

function statusClass(status: string) {
  if (status === "completed") {
    return "inline-flex rounded-md bg-teal-50 px-2 py-1 text-xs font-semibold text-teal-800 ring-1 ring-teal-200";
  }
  if (status === "partial") {
    return "inline-flex rounded-md bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800 ring-1 ring-amber-200";
  }
  return "inline-flex rounded-md bg-rose-50 px-2 py-1 text-xs font-semibold text-rose-800 ring-1 ring-rose-200";
}
