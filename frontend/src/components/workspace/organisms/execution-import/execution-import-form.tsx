"use client";

import { FileText, Loader2, Upload } from "lucide-react";

import type { ExecutionImportResult } from "@/lib/api";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

import { ExecutionImportResultSummary } from "./execution-import-result";

export const sampleCsv = [
  "executed_at,symbol,side,quantity,price,fees,position_id,execution_id",
  "2026-05-08T14:30:00+00:00,SPY,buy,10,425.50,1.25,pos_spy,exec_1"
].join("\n");

export function ExecutionImportForm({
  broker,
  csvText,
  importError,
  locale,
  onBrokerChange,
  onCsvTextChange,
  onSourceFilenameChange,
  result,
  sourceFilename
}: {
  broker: string;
  csvText: string;
  importError: boolean;
  locale: Locale;
  onBrokerChange: (value: string) => void;
  onCsvTextChange: (value: string) => void;
  onSourceFilenameChange: (value: string) => void;
  result: ExecutionImportResult | null;
  sourceFilename: string;
}) {
  const { t } = useAppI18n();

  const loadFile = async (file: File | undefined) => {
    if (!file) {
      return;
    }
    onSourceFilenameChange(file.name);
    onCsvTextChange(await file.text());
  };

  return (
    <>
      <div className="grid gap-4 border-b border-line bg-white px-4 py-4">
        <p className="max-w-4xl text-sm leading-6 text-slate-600">{t("executionImportHelp")}</p>
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <label className="grid gap-1 text-xs font-semibold text-slate-600">
            {t("broker")}
            <input
              className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm font-medium text-ink"
              onChange={(event) => onBrokerChange(event.target.value)}
              value={broker}
            />
          </label>
          <label className="grid gap-1 text-xs font-semibold text-slate-600">
            {t("sourceFilename")}
            <input
              className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm font-medium text-ink"
              onChange={(event) => onSourceFilenameChange(event.target.value)}
              placeholder="fills.csv"
              value={sourceFilename}
            />
          </label>
        </div>
        <label className="grid gap-1 text-xs font-semibold text-slate-600">
          {t("csvText")}
          <textarea
            className="focus-ring min-h-44 rounded-md border border-line bg-white px-3 py-2 font-mono text-xs leading-5 text-ink"
            onChange={(event) => onCsvTextChange(event.target.value)}
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
            onClick={() => onCsvTextChange(sampleCsv)}
            type="button"
          >
            <FileText size={14} />
            {t("loadCsvExample")}
          </button>
          <span className="text-xs leading-5 text-slate-500">{t("csvImportFormatHelp")}</span>
        </div>
        {importError ? (
          <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
            {t("executionImportFailed")}
          </p>
        ) : null}
        {result ? <ExecutionImportResultSummary locale={locale} result={result} /> : null}
      </div>
    </>
  );
}

export function ExecutionImportSubmitButton({
  canImport,
  importing,
  onSubmit
}: {
  canImport: boolean;
  importing: boolean;
  onSubmit: () => void;
}) {
  const { t } = useAppI18n();

  return (
    <button
      className="focus-ring inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
      disabled={!canImport}
      onClick={onSubmit}
      type="button"
    >
      {importing ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />}
      {importing ? t("importingCsv") : t("importCsv")}
    </button>
  );
}
