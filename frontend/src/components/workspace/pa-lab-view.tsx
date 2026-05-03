"use client";

import { useQuery } from "@tanstack/react-query";
import { Eye, Filter, Layers, SlidersHorizontal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { CompactStat, DataState, StatusPill } from "@/components/workspace/common";
import { PASetupDetailPanel } from "@/components/workspace/detail-panels";
import { api } from "@/lib/api";
import { formatDate, formatNumber, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { decisionTone } from "@/lib/presentation";
import { useAppI18n } from "@/lib/use-app-i18n";

export function PALabView({ locale }: { locale: Locale }) {
  const { labelFor, t } = useAppI18n();
  const [symbol, setSymbol] = useState("");
  const [setupType, setSetupType] = useState("");
  const [validationStatus, setValidationStatus] = useState("");
  const [selectedSetupId, setSelectedSetupId] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const filters = {
    symbol: symbol.trim().toUpperCase() || undefined,
    setupType: setupType || undefined,
    validationStatus: validationStatus || undefined,
    limit: 200
  };
  const setups = useQuery({
    queryKey: ["pa-setups", filters],
    queryFn: () => api.paSetups(filters)
  });
  const rows = setups.data ?? [];
  const selectedSetup = detailOpen ? rows.find((setup) => setup.setup_id === selectedSetupId) ?? rows[0] ?? null : null;
  const topScore = useMemo(
    () => rows.reduce<number | null>((best, row) => Math.max(best ?? 0, row.pa_quality_score ?? 0), null),
    [rows]
  );

  useEffect(() => {
    if (selectedSetupId && !rows.some((setup) => setup.setup_id === selectedSetupId)) {
      setSelectedSetupId(null);
    }
  }, [rows, selectedSetupId]);

  return (
    <section className="flex flex-col gap-4">
      <div className="grid gap-3 md:grid-cols-3">
        <CompactStat icon={<Layers size={18} />} label={t("paUniverse")} value={rows.length} />
        <CompactStat icon={<SlidersHorizontal size={18} />} label={t("topScore")} value={formatNumber(topScore, 1, locale)} />
        <CompactStat icon={<Eye size={18} />} label={t("selected")} value={selectedSetup?.symbol_id ?? "-"} />
      </div>

      <section>
        <section className="overflow-hidden rounded-md border border-line bg-white shadow-[0_1px_0_rgba(22,32,42,0.04)]">
          <div className="border-b border-line bg-white px-4 py-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-2">
                <Filter size={18} className="shrink-0 text-teal" />
                <div className="min-w-0">
                  <h2 className="truncate text-base font-semibold text-ink">{t("setupExplorer")}</h2>
                  <p className="text-xs text-slate-500">{t("paLabDataBoundary")}</p>
                </div>
              </div>
              <DataState isLoading={setups.isLoading} isError={setups.isError} locale={locale} />
            </div>
            <div className="grid gap-2 md:grid-cols-[minmax(120px,180px)_minmax(160px,220px)_minmax(160px,220px)]">
              <input
                className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                onChange={(event) => setSymbol(event.target.value)}
                placeholder={t("symbol")}
                value={symbol}
              />
              <select
                className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                onChange={(event) => setSetupType(event.target.value)}
                value={setupType}
              >
                <option value="">{t("allSetups")}</option>
                <option value="breakout">{labelFor("setup", "breakout")}</option>
                <option value="pullback_to_20ma">{labelFor("setup", "pullback_to_20ma")}</option>
                <option value="failed_breakdown_reclaim">{labelFor("setup", "failed_breakdown_reclaim")}</option>
                <option value="oneil_leader_watch">{labelFor("setup", "oneil_leader_watch")}</option>
              </select>
              <select
                className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
                onChange={(event) => setValidationStatus(event.target.value)}
                value={validationStatus}
              >
                <option value="">{t("allValidation")}</option>
                <option value="shadow_only">{labelFor("status", "shadow_only")}</option>
                <option value="paper_allowed">{labelFor("status", "paper_allowed")}</option>
                <option value="live_allowed">{labelFor("status", "live_allowed")}</option>
              </select>
            </div>
          </div>

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
                      {setups.isLoading || setups.isError ? (
                        <DataState isLoading={setups.isLoading} isError={setups.isError} locale={locale} />
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
                      selectedSetup?.setup_id === setup.setup_id ? "bg-teal-50/60" : ""
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
                        onClick={() => {
                          setSelectedSetupId(setup.setup_id);
                          setDetailOpen(true);
                        }}
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
        </section>

      </section>
      {detailOpen && selectedSetup ? (
        <PASetupDetailPanel
          locale={locale}
          onClose={() => {
            setDetailOpen(false);
            setSelectedSetupId(null);
          }}
          setup={selectedSetup}
        />
      ) : null}
    </section>
  );
}
