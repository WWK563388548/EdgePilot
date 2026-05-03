"use client";

import { DataState } from "@/components/workspace/atoms/data-state";
import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import { TableShell } from "@/components/workspace/molecules/table-shell";
import type { ExitAlert, JournalTrade, Position } from "@/lib/api";
import { formatDate, formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

type PaginatedTableProps<T> = {
  data: T[];
  loading: boolean;
  error: boolean;
  page: number;
  pageSize: number;
  totalCount?: number;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
  locale: Locale;
};

export function PositionsTable({
  data,
  loading,
  error,
  page,
  pageSize,
  totalCount,
  hasNextPage,
  onPageChange,
  locale
}: PaginatedTableProps<Position>) {
  const { t } = useAppI18n();

  return (
    <TableShell title={t("positions")} loading={loading} error={error} locale={locale}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("symbol")}</th>
            <th className="px-4 py-3">{t("type")}</th>
            <th className="px-4 py-3">{t("qty")}</th>
            <th className="px-4 py-3">{t("entry")}</th>
            <th className="px-4 py-3">{t("stop")}</th>
            <th className="px-4 py-3">{t("status")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <EmptyTableRow
              colSpan={6}
              error={error}
              loading={loading}
              locale={locale}
              message={t("noPositions")}
            />
          ) : null}
          {data.map((row) => (
            <tr key={row.position_id} className="border-t border-line">
              <td className="px-4 py-3 font-medium text-ink">{row.symbol_id}</td>
              <td className="px-4 py-3">{row.asset_type}</td>
              <td className="px-4 py-3">{formatValue(row.quantity)}</td>
              <td className="px-4 py-3">{formatValue(row.entry_price)}</td>
              <td className="px-4 py-3">{formatValue(row.current_stop)}</td>
              <td className="px-4 py-3">{formatValue(row.status)}</td>
            </tr>
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

export function AlertsTable({
  data,
  loading,
  error,
  page,
  pageSize,
  totalCount,
  hasNextPage,
  onPageChange,
  locale
}: PaginatedTableProps<ExitAlert>) {
  const { t } = useAppI18n();

  return (
    <TableShell title={t("alerts")} loading={loading} error={error} locale={locale}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("level")}</th>
            <th className="px-4 py-3">{t("action")}</th>
            <th className="px-4 py-3">{t("reason")}</th>
            <th className="px-4 py-3">{t("newStop")}</th>
            <th className="px-4 py-3">{t("time")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <EmptyTableRow
              colSpan={5}
              error={error}
              loading={loading}
              locale={locale}
              message={t("noAlerts")}
            />
          ) : null}
          {data.map((row) => (
            <tr key={row.alert_id} className="border-t border-line">
              <td className="px-4 py-3">{formatValue(row.level)}</td>
              <td className="px-4 py-3">{formatValue(row.action)}</td>
              <td className="px-4 py-3">{formatValue(row.reason)}</td>
              <td className="px-4 py-3">{formatValue(row.new_stop)}</td>
              <td className="px-4 py-3">{formatDate(row.alert_ts, locale)}</td>
            </tr>
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

export function JournalTable({
  data,
  loading,
  error,
  page,
  pageSize,
  totalCount,
  hasNextPage,
  onPageChange,
  locale
}: PaginatedTableProps<JournalTrade>) {
  const { t } = useAppI18n();

  return (
    <TableShell title={t("journal")} loading={loading} error={error} locale={locale}>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("symbol")}</th>
            <th className="px-4 py-3">{t("entry")}</th>
            <th className="px-4 py-3">{t("exit")}</th>
            <th className="px-4 py-3">{t("netPnl")}</th>
            <th className="px-4 py-3">{t("rMultiple")}</th>
            <th className="px-4 py-3">{t("exitReason")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <EmptyTableRow
              colSpan={6}
              error={error}
              loading={loading}
              locale={locale}
              message={t("noJournal")}
            />
          ) : null}
          {data.map((row) => (
            <tr key={row.trade_id} className="border-t border-line">
              <td className="px-4 py-3 font-medium text-ink">{formatValue(row.symbol_id)}</td>
              <td className="px-4 py-3">{formatDate(row.entry_ts, locale)}</td>
              <td className="px-4 py-3">{formatDate(row.exit_ts, locale)}</td>
              <td className="px-4 py-3">{formatValue(row.net_pnl)}</td>
              <td className="px-4 py-3">{formatValue(row.r_multiple)}</td>
              <td className="px-4 py-3">{formatValue(row.exit_reason)}</td>
            </tr>
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

function EmptyTableRow({
  colSpan,
  error,
  loading,
  locale,
  message
}: {
  colSpan: number;
  error: boolean;
  loading: boolean;
  locale: Locale;
  message: string;
}) {
  return (
    <tr>
      <td className="border-t border-line px-4 py-6 text-sm text-slate-600" colSpan={colSpan}>
        {loading || error ? <DataState isLoading={loading} isError={error} locale={locale} /> : message}
      </td>
    </tr>
  );
}
