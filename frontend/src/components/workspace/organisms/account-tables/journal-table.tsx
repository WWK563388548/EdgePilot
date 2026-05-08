"use client";

import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import { TableShell } from "@/components/workspace/molecules/table-shell";
import { EmptyTableRow } from "@/components/workspace/organisms/account-tables/empty-table-row";
import type { PaginatedTableProps } from "@/components/workspace/organisms/account-tables/types";
import type { JournalTrade } from "@/lib/api";
import { formatDate, formatValue } from "@/lib/format";
import { useAppI18n } from "@/lib/use-app-i18n";

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
            <th className="px-4 py-3">{t("journalAction")}</th>
            <th className="px-4 py-3">{t("qty")}</th>
            <th className="px-4 py-3">{t("entry")}</th>
            <th className="px-4 py-3">{t("exit")}</th>
            <th className="px-4 py-3">{t("netPnl")}</th>
            <th className="px-4 py-3">{t("rMultiple")}</th>
            <th className="px-4 py-3">{t("notes")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <EmptyTableRow
              colSpan={8}
              error={error}
              loading={loading}
              locale={locale}
              message={t("noJournal")}
            />
          ) : null}
          {data.map((row) => (
            <tr key={row.trade_id} className="border-t border-line">
              <td className="px-4 py-3 font-medium text-ink">{formatValue(row.symbol_id)}</td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex rounded-md px-2 py-1 text-xs font-semibold ${
                    row.exit_reason === "trim"
                      ? "bg-teal-50 text-teal-800 ring-1 ring-teal-200"
                      : "bg-slate-100 text-slate-700 ring-1 ring-slate-200"
                  }`}
                >
                  {journalActionLabel(row.exit_reason, t)}
                </span>
              </td>
              <td className="px-4 py-3">{formatValue(row.quantity)}</td>
              <td className="px-4 py-3">{formatDate(row.entry_ts, locale)}</td>
              <td className="px-4 py-3">{formatDate(row.exit_ts, locale)}</td>
              <td className="px-4 py-3">{formatValue(row.net_pnl)}</td>
              <td className="px-4 py-3">{formatValue(row.r_multiple)}</td>
              <td className="px-4 py-3">
                <div className="font-medium text-ink">{formatValue(row.exit_reason)}</div>
                <div className="mt-1 max-w-72 text-xs leading-5 text-slate-500">{formatValue(row.notes)}</div>
              </td>
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

function journalActionLabel(
  reason: string | null | undefined,
  t: ReturnType<typeof useAppI18n>["t"]
) {
  if (reason === "trim") {
    return t("journalActionTrim");
  }
  if (reason) {
    return t("journalActionClose");
  }
  return t("journalActionOther");
}
