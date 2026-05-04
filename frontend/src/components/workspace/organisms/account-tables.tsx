"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, RefreshCw, X } from "lucide-react";
import { Fragment, useState } from "react";

import { DataState } from "@/components/workspace/atoms/data-state";
import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import { TableShell } from "@/components/workspace/molecules/table-shell";
import type { ExitAlert, JournalTrade, Position } from "@/lib/api";
import { api } from "@/lib/api";
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
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const [activatingPositionId, setActivatingPositionId] = useState<string | null>(null);
  const [activationForm, setActivationForm] = useState({
    entryDate: datetimeLocalValue(new Date()),
    entryPrice: "",
    quantity: ""
  });
  const activatePosition = useMutation({
    mutationFn: (request: { entryDate?: string; entryPrice: number; positionId: string; quantity?: number }) =>
      api.activatePosition(request.positionId, {
        entry_date: request.entryDate,
        entry_price: request.entryPrice,
        quantity: request.quantity
      }),
    onSuccess: async () => {
      setActivatingPositionId(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["alerts"] }),
        queryClient.invalidateQueries({ queryKey: ["alerts-count"] })
      ]);
    }
  });

  const startActivation = (position: Position) => {
    setActivatingPositionId(position.position_id);
    setActivationForm({
      entryDate: position.entry_date ? datetimeLocalValue(new Date(position.entry_date)) : datetimeLocalValue(new Date()),
      entryPrice: String(position.entry_price ?? ""),
      quantity: position.quantity === null ? "" : String(position.quantity)
    });
    activatePosition.reset();
  };

  const submitActivation = (position: Position) => {
    const entryPrice = Number(activationForm.entryPrice);
    const quantity = activationForm.quantity ? Number(activationForm.quantity) : undefined;
    if (!Number.isFinite(entryPrice) || entryPrice <= 0) {
      return;
    }
    if (quantity !== undefined && (!Number.isFinite(quantity) || quantity <= 0)) {
      return;
    }
    activatePosition.mutate({
      entryDate: activationForm.entryDate ? new Date(activationForm.entryDate).toISOString() : undefined,
      entryPrice,
      positionId: position.position_id,
      quantity
    });
  };

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
            <th className="px-4 py-3">{t("action")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <EmptyTableRow
              colSpan={7}
              error={error}
              loading={loading}
              locale={locale}
              message={t("noPositions")}
            />
          ) : null}
          {data.map((row) => (
            <Fragment key={row.position_id}>
              <tr className="border-t border-line">
                <td className="px-4 py-3 font-medium text-ink">{row.symbol_id}</td>
                <td className="px-4 py-3">{row.asset_type}</td>
                <td className="px-4 py-3">{formatValue(row.quantity)}</td>
                <td className="px-4 py-3">{formatValue(row.entry_price)}</td>
                <td className="px-4 py-3">{formatValue(row.current_stop)}</td>
                <td className="px-4 py-3">{labelFor("status", row.status)}</td>
                <td className="px-4 py-3">
                  {row.status === "planned" ? (
                    <button
                      className="focus-ring inline-flex h-8 items-center gap-1.5 rounded-md border border-line bg-white px-2.5 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal"
                      onClick={() => startActivation(row)}
                      type="button"
                    >
                      <CheckCircle2 size={14} />
                      {t("markEntry")}
                    </button>
                  ) : (
                    <span className="text-slate-400">-</span>
                  )}
                </td>
              </tr>
              {activatingPositionId === row.position_id ? (
                <tr className="border-t border-line bg-teal-50/35">
                  <td className="px-4 py-4" colSpan={7}>
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-ink">{t("markEntryTitle")}</p>
                        <p className="mt-1 text-xs text-slate-600">{t("markEntryHelp")}</p>
                      </div>
                      <label className="grid gap-1 text-xs font-semibold text-slate-600">
                        {t("actualEntry")}
                        <input
                          className="focus-ring h-9 w-32 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink"
                          min="0"
                          onChange={(event) =>
                            setActivationForm((value) => ({ ...value, entryPrice: event.target.value }))
                          }
                          step="0.01"
                          type="number"
                          value={activationForm.entryPrice}
                        />
                      </label>
                      <label className="grid gap-1 text-xs font-semibold text-slate-600">
                        {t("qty")}
                        <input
                          className="focus-ring h-9 w-28 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink"
                          min="0"
                          onChange={(event) =>
                            setActivationForm((value) => ({ ...value, quantity: event.target.value }))
                          }
                          step="0.0001"
                          type="number"
                          value={activationForm.quantity}
                        />
                      </label>
                      <label className="grid gap-1 text-xs font-semibold text-slate-600">
                        {t("entryTime")}
                        <input
                          className="focus-ring h-9 rounded-md border border-line bg-white px-2 text-sm font-medium text-ink"
                          onChange={(event) =>
                            setActivationForm((value) => ({ ...value, entryDate: event.target.value }))
                          }
                          type="datetime-local"
                          value={activationForm.entryDate}
                        />
                      </label>
                      <div className="flex gap-2">
                        <button
                          className="focus-ring inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={activatePosition.isPending}
                          onClick={() => submitActivation(row)}
                          type="button"
                        >
                          {activatePosition.isPending ? <Loader2 className="animate-spin" size={15} /> : <CheckCircle2 size={15} />}
                          {activatePosition.isPending ? t("saving") : t("confirmEntry")}
                        </button>
                        <button
                          className="focus-ring inline-flex h-9 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-semibold text-ink transition-colors hover:border-teal hover:text-teal"
                          onClick={() => setActivatingPositionId(null)}
                          type="button"
                        >
                          <X size={15} />
                          {t("cancel")}
                        </button>
                      </div>
                    </div>
                    {activatePosition.isError ? (
                      <p className="mt-2 text-sm font-medium text-rose-700">{t("markEntryFailed")}</p>
                    ) : null}
                  </td>
                </tr>
              ) : null}
            </Fragment>
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

function datetimeLocalValue(date: Date) {
  const timezoneOffsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - timezoneOffsetMs).toISOString().slice(0, 16);
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
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const [evaluationResult, setEvaluationResult] = useState<string | null>(null);
  const evaluateAlerts = useMutation({
    mutationFn: () => api.evaluateExitAlerts(),
    onSuccess: async (response) => {
      setEvaluationResult(
        response.alerts_created === 0 && response.duplicate_alerts === 0
          ? t("exitAlertEvaluationNoTriggers", {
              positions: response.positions_evaluated,
              skipped: response.skipped_positions
            })
          : t("exitAlertEvaluationResult", {
              alerts: response.alerts_created,
              duplicates: response.duplicate_alerts,
              positions: response.positions_evaluated,
              skipped: response.skipped_positions
            })
      );
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["alerts"] }),
        queryClient.invalidateQueries({ queryKey: ["alerts-count"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] })
      ]);
    },
    onError: () => {
      setEvaluationResult(null);
    }
  });

  return (
    <TableShell
      title={t("alerts")}
      loading={loading || evaluateAlerts.isPending}
      error={error || evaluateAlerts.isError}
      locale={locale}
      actions={
        <button
          className="focus-ring inline-flex h-9 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60"
          disabled={evaluateAlerts.isPending}
          onClick={() => evaluateAlerts.mutate()}
          title={t("exitAlertEvaluationHelp")}
          type="button"
        >
          <RefreshCw size={16} className={evaluateAlerts.isPending ? "animate-spin" : ""} />
          {evaluateAlerts.isPending ? t("evaluatingExitAlerts") : t("evaluateExitAlerts")}
        </button>
      }
    >
      {evaluationResult || evaluateAlerts.isError ? (
        <div
          className={`border-b border-line px-4 py-3 text-sm ${
            evaluateAlerts.isError ? "bg-rose-50 text-rose-700" : "bg-teal-50 text-teal-800"
          }`}
        >
          {evaluateAlerts.isError ? t("exitAlertEvaluationFailed") : evaluationResult}
        </div>
      ) : null}
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
              <td className="px-4 py-3">{labelFor("plan", row.action)}</td>
              <td className="px-4 py-3">{labelFor("plan", row.reason)}</td>
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
