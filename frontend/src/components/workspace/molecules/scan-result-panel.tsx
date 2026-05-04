"use client";

import type { ETFOneilScannerResponse, ETFUniverseSeedResponse } from "@/lib/api";
import { formatDateOnly, formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export type AccountScanResult = ETFOneilScannerResponse | ETFUniverseSeedResponse;

export function ScanResultPanel({
  result,
  locale
}: {
  result: AccountScanResult;
  locale: Locale;
}) {
  const { labelFor, t } = useAppI18n();
  const candidateCount = result.decision_counts?.candidate ?? 0;
  const watchCount = result.decision_counts?.watch ?? 0;
  const isMarketRefresh = "bars_written" in result;
  const scannedSymbols = "symbols_scanned" in result ? result.symbols_scanned : result.symbols_requested;
  const symbols = scannedSymbols.join(", ");
  const skippedSymbols = result.skipped_symbols.length ? result.skipped_symbols.join(", ") : t("none");
  const metrics = [
    { label: t("scanMode"), value: isMarketRefresh ? t("marketRefreshMode") : t("quickRescanMode") },
    ...(isMarketRefresh
      ? [{ label: t("barsWritten"), value: formatNumber(result.bars_written, 0, locale) }]
      : []),
    { label: t("symbolsScanned"), value: formatNumber(scannedSymbols.length, 0, locale) },
    { label: t("factsWritten"), value: formatNumber(result.facts_written, 0, locale) },
    { label: t("setupsWritten"), value: formatNumber(result.setups_written, 0, locale) },
    { label: t("candidatesWritten"), value: formatNumber(result.candidates_written, 0, locale) },
    { label: t("latestScanDate"), value: formatDateOnly(result.latest_scan_date, locale) },
    { label: t("latestBarDate"), value: formatDateOnly(result.latest_bar_date, locale) }
  ];

  return (
    <div className="flex flex-col gap-3 text-sm">
      <div>
        <p className="font-semibold text-teal-900">
          {t("scanResultSummary", {
            candidates: candidateCount,
            watch: watchCount,
            total: result.candidates_written
          })}
        </p>
        <p className="mt-1 text-xs text-teal-700">
          {labelFor("status", "candidate")}: {formatNumber(candidateCount, 0, locale)}
          {" · "}
          {labelFor("status", "watch")}: {formatNumber(watchCount, 0, locale)}
        </p>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => (
          <div className="rounded-md border border-teal-100 bg-white/70 px-3 py-2" key={metric.label}>
            <div className="text-xs text-slate-500">{metric.label}</div>
            <div className="mt-0.5 font-semibold text-ink">{metric.value}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-2 text-xs leading-5 text-slate-700 lg:grid-cols-2">
        <div>
          <span className="font-semibold text-ink">{t("symbolsScanned")}:</span>{" "}
          <span>{symbols || "-"}</span>
        </div>
        <div>
          <span className="font-semibold text-ink">{t("skippedSymbols")}:</span>{" "}
          <span>{skippedSymbols}</span>
        </div>
      </div>
    </div>
  );
}
