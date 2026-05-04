"use client";

import { useQuery } from "@tanstack/react-query";
import { Eye, Layers, SlidersHorizontal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { CompactStat } from "@/components/workspace/atoms/stat-card";
import { PASetupDetailPanel } from "@/components/workspace/detail-panels";
import { PALabFilterBar } from "@/components/workspace/organisms/pa-lab-filter-bar";
import { PASetupTable } from "@/components/workspace/organisms/pa-setup-table";
import { api } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

const PA_LAB_PAGE_SIZE = 10;

export function PALabView({ locale }: { locale: Locale }) {
  const { t } = useAppI18n();
  const [symbol, setSymbol] = useState("");
  const [setupType, setSetupType] = useState("");
  const [validationStatus, setValidationStatus] = useState("");
  const [page, setPage] = useState(0);
  const [selectedSetupId, setSelectedSetupId] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const baseFilters = {
    symbol: symbol.trim().toUpperCase() || undefined,
    setupType: setupType || undefined,
    validationStatus: validationStatus || undefined,
    timeframe: "1d"
  };
  const filters = {
    ...baseFilters,
    limit: PA_LAB_PAGE_SIZE + 1,
    offset: page * PA_LAB_PAGE_SIZE
  };
  const setups = useQuery({
    queryKey: ["pa-setups", filters],
    queryFn: () => api.paSetups(filters)
  });
  const setupsCount = useQuery({
    queryKey: ["pa-setups-count", baseFilters],
    queryFn: () => api.paSetupsCount(baseFilters)
  });
  const rawRows = setups.data ?? [];
  const rows = rawRows.slice(0, PA_LAB_PAGE_SIZE);
  const hasNextPage =
    setupsCount.data?.total !== undefined
      ? (page + 1) * PA_LAB_PAGE_SIZE < setupsCount.data.total
      : rawRows.length > PA_LAB_PAGE_SIZE;
  const selectedSetup = detailOpen ? rows.find((setup) => setup.setup_id === selectedSetupId) ?? rows[0] ?? null : null;
  const topScore = useMemo(
    () => rows.reduce<number | null>((best, row) => Math.max(best ?? 0, row.pa_quality_score ?? 0), null),
    [rows]
  );

  useEffect(() => {
    if (selectedSetupId && !rows.some((setup) => setup.setup_id === selectedSetupId)) {
      setSelectedSetupId(null);
      setDetailOpen(false);
    }
  }, [rows, selectedSetupId]);

  return (
    <section className="flex flex-col gap-4">
      <div className="grid gap-3 md:grid-cols-3">
        <CompactStat icon={<Layers size={18} />} label={t("paUniverse")} value={setupsCount.data?.total ?? rows.length} />
        <CompactStat icon={<SlidersHorizontal size={18} />} label={t("topScore")} value={formatNumber(topScore, 1, locale)} />
        <CompactStat icon={<Eye size={18} />} label={t("selected")} value={selectedSetup?.symbol_id ?? "-"} />
      </div>

      <section>
        <section className="overflow-hidden rounded-md border border-line bg-white shadow-[0_1px_0_rgba(22,32,42,0.04)]">
          <PALabFilterBar
            error={setups.isError}
            loading={setups.isLoading}
            locale={locale}
            onSetupTypeChange={(value) => {
              setSetupType(value);
              setPage(0);
            }}
            onSymbolChange={(value) => {
              setSymbol(value);
              setPage(0);
            }}
            onValidationStatusChange={(value) => {
              setValidationStatus(value);
              setPage(0);
            }}
            setupType={setupType}
            symbol={symbol}
            validationStatus={validationStatus}
          />
          <PASetupTable
            error={setups.isError}
            hasNextPage={hasNextPage}
            loading={setups.isLoading}
            locale={locale}
            onPageChange={setPage}
            onSelect={(setupId) => {
              setSelectedSetupId(setupId);
              setDetailOpen(true);
            }}
            page={page}
            pageSize={PA_LAB_PAGE_SIZE}
            rows={rows}
            selectedSetupId={selectedSetup?.setup_id ?? null}
            totalCount={setupsCount.data?.total}
          />
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
