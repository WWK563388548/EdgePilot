"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, FileText, Loader2, Upload } from "lucide-react";
import { useState } from "react";

import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import { TableShell } from "@/components/workspace/molecules/table-shell";
import { api, type ExecutionFill, type ExecutionImport, type ExecutionImportResult, type Position } from "@/lib/api";
import { formatDate, formatNumber, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

const EXECUTION_PAGE_SIZE = 8;

const sampleCsv = [
  "executed_at,symbol,side,quantity,price,fees,position_id,execution_id",
  "2026-05-08T14:30:00+00:00,SPY,buy,10,425.50,1.25,pos_spy,exec_1"
].join("\n");

export function ExecutionImportView({ locale }: { locale: Locale }) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const [broker, setBroker] = useState("edgepilot_generic_csv");
  const [sourceFilename, setSourceFilename] = useState("");
  const [csvText, setCsvText] = useState("");
  const [result, setResult] = useState<ExecutionImportResult | null>(null);
  const [importPage, setImportPage] = useState(0);
  const [fillPage, setFillPage] = useState(0);

  const imports = useQuery({
    queryKey: ["execution-imports", importPage],
    queryFn: () =>
      api.executionImports({
        limit: EXECUTION_PAGE_SIZE + 1,
        offset: importPage * EXECUTION_PAGE_SIZE
      })
  });
  const importsCount = useQuery({
    queryKey: ["execution-imports-count"],
    queryFn: () => api.executionImportsCount()
  });
  const fills = useQuery({
    queryKey: ["execution-fills", fillPage],
    queryFn: () =>
      api.executionFills({
        limit: EXECUTION_PAGE_SIZE + 1,
        offset: fillPage * EXECUTION_PAGE_SIZE
      })
  });
  const fillsCount = useQuery({
    queryKey: ["execution-fills-count"],
    queryFn: () => api.executionFillsCount()
  });
  const reviewNeeded = useQuery({
    queryKey: ["positions", "review_needed", 0],
    queryFn: () =>
      api.positions({
        limit: 5,
        offset: 0,
        status: "review_needed"
      })
  });
  const reviewNeededCount = useQuery({
    queryKey: ["positions-count", "review_needed"],
    queryFn: () => api.positionsCount({ status: "review_needed" })
  });

  const importCsv = useMutation({
    mutationFn: () =>
      api.importExecutionCsv({
        broker: broker.trim() || "edgepilot_generic_csv",
        csv_text: csvText,
        source_filename: sourceFilename.trim() || null
      }),
    onSuccess: async (response) => {
      setResult(response);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["execution-imports"] }),
        queryClient.invalidateQueries({ queryKey: ["execution-imports-count"] }),
        queryClient.invalidateQueries({ queryKey: ["execution-fills"] }),
        queryClient.invalidateQueries({ queryKey: ["execution-fills-count"] }),
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] }),
        queryClient.invalidateQueries({ queryKey: ["portfolio-risk"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      ]);
    }
  });

  const importRows = (imports.data ?? []).slice(0, EXECUTION_PAGE_SIZE);
  const fillRows = (fills.data ?? []).slice(0, EXECUTION_PAGE_SIZE);
  const reviewRows = reviewNeeded.data ?? [];
  const hasImportNext =
    importsCount.data?.total !== undefined
      ? (importPage + 1) * EXECUTION_PAGE_SIZE < importsCount.data.total
      : (imports.data ?? []).length > EXECUTION_PAGE_SIZE;
  const hasFillNext =
    fillsCount.data?.total !== undefined
      ? (fillPage + 1) * EXECUTION_PAGE_SIZE < fillsCount.data.total
      : (fills.data ?? []).length > EXECUTION_PAGE_SIZE;

  const canImport = csvText.trim().length > 0 && !importCsv.isPending;
  const loadFile = async (file: File | undefined) => {
    if (!file) {
      return;
    }
    setSourceFilename(file.name);
    setCsvText(await file.text());
  };

  return (
    <div className="grid gap-5">
      <TableShell
        title={t("executionImport")}
        loading={importCsv.isPending}
        error={importCsv.isError}
        locale={locale}
        actions={
          <button
            className="focus-ring inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
            disabled={!canImport}
            onClick={() => importCsv.mutate()}
            type="button"
          >
            {importCsv.isPending ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />}
            {importCsv.isPending ? t("importingCsv") : t("importCsv")}
          </button>
        }
      >
        <div className="grid gap-4 border-b border-line bg-white px-4 py-4">
          <p className="max-w-4xl text-sm leading-6 text-slate-600">{t("executionImportHelp")}</p>
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <label className="grid gap-1 text-xs font-semibold text-slate-600">
              {t("broker")}
              <input
                className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm font-medium text-ink"
                onChange={(event) => setBroker(event.target.value)}
                value={broker}
              />
            </label>
            <label className="grid gap-1 text-xs font-semibold text-slate-600">
              {t("sourceFilename")}
              <input
                className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm font-medium text-ink"
                onChange={(event) => setSourceFilename(event.target.value)}
                placeholder="fills.csv"
                value={sourceFilename}
              />
            </label>
          </div>
          <label className="grid gap-1 text-xs font-semibold text-slate-600">
            {t("csvText")}
            <textarea
              className="focus-ring min-h-44 rounded-md border border-line bg-white px-3 py-2 font-mono text-xs leading-5 text-ink"
              onChange={(event) => setCsvText(event.target.value)}
              placeholder={sampleCsv}
              value={csvText}
            />
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <label className="focus-ring inline-flex h-8 cursor-pointer items-center gap-2 rounded-md border border-line bg-white px-3 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal">
              <Upload size={14} />
              {t("selectCsvFile")}
              <input
                accept=".csv,text/csv"
                className="sr-only"
                onChange={(event) => {
                  void loadFile(event.target.files?.[0]);
                  event.target.value = "";
                }}
                type="file"
              />
            </label>
            <button
              className="focus-ring inline-flex h-8 items-center gap-2 rounded-md border border-line bg-white px-3 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal"
              onClick={() => setCsvText(sampleCsv)}
              type="button"
            >
              <FileText size={14} />
              {t("loadCsvExample")}
            </button>
            <span className="text-xs leading-5 text-slate-500">{t("csvImportFormatHelp")}</span>
          </div>
          {importCsv.isError ? (
            <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
              {t("executionImportFailed")}
            </p>
          ) : null}
          {result ? <ImportResultSummary result={result} locale={locale} /> : null}
        </div>
      </TableShell>

      <ReviewNeededPanel
        data={reviewRows}
        error={reviewNeeded.isError || reviewNeededCount.isError}
        loading={reviewNeeded.isLoading || reviewNeededCount.isLoading}
        locale={locale}
        totalCount={reviewNeededCount.data?.total}
      />

      <TableShell
        title={t("importHistory")}
        loading={imports.isLoading}
        error={imports.isError}
        locale={locale}
      >
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
            {!importRows.length ? (
              <EmptyRow colSpan={7} message={t("noExecutionImports")} />
            ) : null}
            {importRows.map((row) => (
              <ExecutionImportRow key={row.import_id} locale={locale} row={row} />
            ))}
          </tbody>
        </table>
        <PaginationControls
          hasNext={hasImportNext}
          itemCount={importRows.length}
          onPageChange={setImportPage}
          page={importPage}
          pageSize={EXECUTION_PAGE_SIZE}
          totalCount={importsCount.data?.total}
        />
      </TableShell>

      <TableShell
        title={t("fillLedger")}
        loading={fills.isLoading}
        error={fills.isError}
        locale={locale}
      >
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
            {!fillRows.length ? <EmptyRow colSpan={7} message={t("noExecutionFills")} /> : null}
            {fillRows.map((row) => (
              <ExecutionFillRow key={row.fill_id} locale={locale} row={row} />
            ))}
          </tbody>
        </table>
        <PaginationControls
          hasNext={hasFillNext}
          itemCount={fillRows.length}
          onPageChange={setFillPage}
          page={fillPage}
          pageSize={EXECUTION_PAGE_SIZE}
          totalCount={fillsCount.data?.total}
        />
      </TableShell>
    </div>
  );

  function ImportResultSummary({ result, locale }: { result: ExecutionImportResult; locale: Locale }) {
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
            <ResultMetric label={t("rowsTotal")} value={result.import_record.rows_total} />
            <ResultMetric label={t("rowsImported")} value={result.import_record.rows_imported} />
            <ResultMetric label={t("rowsSkipped")} value={result.import_record.rows_skipped} />
            <ResultMetric label={t("rowsFailed")} value={result.import_record.rows_failed} />
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

  function ResultMetric({ label, value }: { label: string; value: number }) {
    return (
      <div>
        <div className="text-xs font-semibold uppercase text-teal-700">{label}</div>
        <div className="mt-1 text-base font-bold text-ink">{formatNumber(value, 0, locale)}</div>
      </div>
    );
  }
}

function ReviewNeededPanel({
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
