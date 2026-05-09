"use client";

import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import { TableShell } from "@/components/workspace/molecules/table-shell";
import { EmptyTableRow } from "@/components/workspace/organisms/account-tables/empty-table-row";
import type { PaginatedTableProps } from "@/components/workspace/organisms/account-tables/types";
import { PositionLifecycleRow } from "@/components/workspace/organisms/position-lifecycle-row";
import type { Position, PositionStatus } from "@/lib/api";
import { useAppI18n } from "@/lib/use-app-i18n";

export function PositionsTable({
  data,
  loading,
  error,
  page,
  pageSize,
  totalCount,
  hasNextPage,
  onPageChange,
  onStatusFilterChange,
  statusFilter,
  locale
}: PaginatedTableProps<Position> & {
  onStatusFilterChange: (filter: PositionStatus | "all") => void;
  statusFilter: PositionStatus | "all";
}) {
  const { labelFor, t } = useAppI18n();
  const filters: Array<PositionStatus | "all"> = [
    "all",
    "planned",
    "open",
    "reduce",
    "exit_pending",
    "review_needed",
    "closed",
    "cancelled"
  ];

  return (
    <TableShell title={t("positions")} loading={loading} error={error} locale={locale}>
      <div className="border-b border-line bg-white px-4 py-4">
        <div className="mb-3 text-sm font-semibold text-ink">{t("positionLifecycleTitle")}</div>
        <div className="grid gap-2 md:grid-cols-4">
          <LifecycleStep label={t("positionLifecyclePlanned")} value={labelFor("status", "planned")} />
          <LifecycleStep label={t("positionLifecycleOpen")} value={labelFor("status", "open")} />
          <LifecycleStep label={t("positionLifecycleReduced")} value={labelFor("status", "reduce")} />
          <LifecycleStep label={t("positionLifecycleClosed")} value={labelFor("status", "closed")} />
        </div>
      </div>
      <div className="flex flex-wrap gap-2 border-b border-line bg-white px-4 py-3">
        {filters.map((filter) => {
          const selected = statusFilter === filter;
          return (
            <button
              className={`focus-ring h-8 rounded-md px-3 text-xs font-semibold transition-colors ${
                selected
                  ? "bg-ink text-white"
                  : "border border-line bg-panel text-slate-700 hover:border-teal hover:text-teal"
              }`}
              key={filter}
              onClick={() => onStatusFilterChange(filter)}
              type="button"
            >
              {filter === "all" ? t("allPositions") : labelFor("status", filter)}
            </button>
          );
        })}
      </div>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("symbol")}</th>
            <th className="px-4 py-3">{t("type")}</th>
            <th className="px-4 py-3">{t("qty")}</th>
            <th className="px-4 py-3">{t("entry")}</th>
            <th className="px-4 py-3">{t("stop")}</th>
            <th className="px-4 py-3">{t("riskAmount")}</th>
            <th className="px-4 py-3">{t("riskPercent")}</th>
            <th className="px-4 py-3">{t("status")}</th>
            <th className="px-4 py-3">{t("action")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <EmptyTableRow
              colSpan={9}
              error={error}
              loading={loading}
              locale={locale}
              message={t("noPositions")}
            />
          ) : null}
          {data.map((row) => (
            <PositionLifecycleRow key={row.position_id} locale={locale} position={row} />
          ))}
        </tbody>
      </table>
      <PaginationControls
        hasNext={hasNextPage}
        itemCount={data.length}
        onPageChange={onPageChange}
        page={page}
        pageSize={pageSize}
        totalCount={totalCount}
      />
    </TableShell>
  );
}

function LifecycleStep({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-panel px-3 py-2">
      <div className="text-xs font-semibold uppercase text-slate-500">{value}</div>
      <div className="mt-1 text-sm font-medium text-ink">{label}</div>
    </div>
  );
}
