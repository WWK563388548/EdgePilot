"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Check, Clock3, ExternalLink } from "lucide-react";

import { PaginationControls } from "@/components/workspace/molecules/pagination-controls";
import { TableShell } from "@/components/workspace/molecules/table-shell";
import type { NotificationEvent } from "@/lib/api";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import type { WorkspaceView } from "@/lib/store";
import { useAppI18n } from "@/lib/use-app-i18n";

type NotificationCenterProps = {
  data: NotificationEvent[];
  loading: boolean;
  error: boolean;
  page: number;
  pageSize: number;
  totalCount?: number;
  hasNextPage: boolean;
  onNavigate: (view: WorkspaceView, targetId?: string | null) => void;
  onPageChange: (page: number) => void;
  locale: Locale;
};

export function NotificationCenter({
  data,
  error,
  hasNextPage,
  loading,
  locale,
  onNavigate,
  onPageChange,
  page,
  pageSize,
  totalCount
}: NotificationCenterProps) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const updateNotification = useMutation({
    mutationFn: ({
      notificationId,
      snoozedUntil
    }: {
      notificationId: string;
      snoozedUntil?: string;
    }) =>
      api.updateNotification(
        notificationId,
        snoozedUntil
          ? {
              snoozed_until: snoozedUntil
            }
          : {
              acknowledged: true
            }
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["notifications"] }),
        queryClient.invalidateQueries({ queryKey: ["notifications-count"] }),
        queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] })
      ]);
    }
  });

  return (
    <TableShell title={t("notifications")} loading={loading} error={error} locale={locale}>
      <div className="border-b border-line bg-white px-4 py-3 text-sm text-slate-700">
        {t("notificationsHelp")}
      </div>
      <table className="min-w-full text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">{t("severity")}</th>
            <th className="px-4 py-3">{t("event")}</th>
            <th className="px-4 py-3">{t("message")}</th>
            <th className="px-4 py-3">{t("time")}</th>
            <th className="px-4 py-3">{t("action")}</th>
          </tr>
        </thead>
        <tbody>
          {!data.length ? (
            <tr>
              <td className="px-4 py-8 text-center text-slate-500" colSpan={5}>
                {loading ? t("loading") : error ? t("apiUnavailable") : t("noNotifications")}
              </td>
            </tr>
          ) : null}
          {data.map((row) => {
            const targetView = normalizedTargetView(row.target_view);
            return (
              <tr key={row.notification_id} className="border-t border-line align-top">
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex rounded-md px-2 py-1 text-xs font-semibold ${severityClass(row.severity)}`}
                  >
                    {labelFor("plan", row.severity)}
                  </span>
                </td>
                <td className="px-4 py-3 font-medium text-ink">
                  {labelFor("plan", row.event_type)}
                </td>
                <td className="px-4 py-3">
                  <div className="font-semibold text-ink">{localizedNotificationTitle(t, row)}</div>
                  <div className="mt-1 max-w-2xl text-slate-600">{localizedNotificationBody(t, row)}</div>
                </td>
                <td className="px-4 py-3 text-slate-600">{formatDate(row.created_at, locale)}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-2">
                    {targetView ? (
                      <button
                        className="focus-ring inline-flex h-8 items-center gap-1 rounded-md border border-line bg-white px-2 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal"
                        onClick={() => onNavigate(targetView, row.target_id)}
                        type="button"
                      >
                        <ExternalLink size={14} />
                        {t("openTarget")}
                      </button>
                    ) : null}
                    <button
                      className="focus-ring inline-flex h-8 items-center gap-1 rounded-md border border-line bg-white px-2 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:opacity-60"
                      disabled={updateNotification.isPending}
                      onClick={() =>
                        updateNotification.mutate({
                          notificationId: row.notification_id
                        })
                      }
                      type="button"
                    >
                      <Check size={14} />
                      {t("ackNotification")}
                    </button>
                    <button
                      className="focus-ring inline-flex h-8 items-center gap-1 rounded-md border border-line bg-white px-2 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:opacity-60"
                      disabled={updateNotification.isPending}
                      onClick={() =>
                        updateNotification.mutate({
                          notificationId: row.notification_id,
                          snoozedUntil: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
                        })
                      }
                      type="button"
                    >
                      <Clock3 size={14} />
                      {t("snoozeNotification")}
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
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

export function NotificationBell({
  locale,
  onOpen
}: {
  locale: Locale;
  onOpen: () => void;
}) {
  const { t } = useAppI18n();
  const unreadCount = useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: () =>
      api.notificationsCount({
        acknowledged: false,
        read: false
      })
  });
  const count = unreadCount.data?.total ?? 0;

  return (
    <button
      className="focus-ring relative inline-flex h-10 items-center gap-2 rounded-md border border-line bg-panel px-3 text-sm font-semibold text-slate-700 transition-colors hover:border-teal hover:text-teal"
      onClick={onOpen}
      title={t("openNotifications")}
      type="button"
    >
      <Bell size={16} />
      <span className="hidden sm:inline">{t("notifications")}</span>
      {count > 0 ? (
        <span
          aria-label={t("unreadNotifications", { count })}
          className="absolute -right-2 -top-2 min-w-5 rounded-full bg-rose-700 px-1.5 py-0.5 text-center text-[11px] font-bold text-white"
        >
          {count > 99 ? "99+" : count}
        </span>
      ) : null}
      <span className="sr-only">{locale}</span>
    </button>
  );
}

function normalizedTargetView(value: string | null): WorkspaceView | null {
  const allowed: WorkspaceView[] = [
    "overview",
    "candidates",
    "pa_lab",
    "outcomes",
    "positions",
    "alerts",
    "notifications",
    "journal",
    "settings"
  ];
  return allowed.includes(value as WorkspaceView) ? (value as WorkspaceView) : null;
}

function severityClass(severity: string) {
  if (severity === "action_required") {
    return "bg-rose-50 text-rose-800 ring-1 ring-rose-200";
  }
  if (severity === "warning") {
    return "bg-amber-50 text-amber-800 ring-1 ring-amber-200";
  }
  return "bg-teal-50 text-teal-800 ring-1 ring-teal-200";
}

function localizedNotificationTitle(
  t: ReturnType<typeof useAppI18n>["t"],
  row: NotificationEvent
) {
  const symbol = stringMeta(row, "symbol_id");
  if (row.event_type === "position_entry_triggered") {
    return t("notificationEntryTriggeredTitle", { symbol });
  }
  if (row.event_type === "position_hard_stop") {
    return t("notificationHardStopTitle", { symbol });
  }
  if (row.event_type === "position_trim_target") {
    return t("notificationTrimTitle", { symbol });
  }
  if (row.event_type === "candidate_plan_created") {
    return t("notificationPlanCreatedTitle", { symbol });
  }
  if (row.event_type === "scanner_candidates_updated") {
    return t("notificationScannerUpdatedTitle");
  }
  return row.title || row.event_type;
}

function localizedNotificationBody(
  t: ReturnType<typeof useAppI18n>["t"],
  row: NotificationEvent
) {
  const symbol = stringMeta(row, "symbol_id");
  if (row.event_type === "position_entry_triggered") {
    return t("notificationEntryTriggeredBody", { symbol });
  }
  if (row.event_type === "position_hard_stop") {
    return t("notificationHardStopBody", { symbol });
  }
  if (row.event_type === "position_trim_target") {
    return t("notificationTrimBody", { symbol });
  }
  if (row.event_type === "candidate_plan_created") {
    return t("notificationPlanCreatedBody", { symbol });
  }
  if (row.event_type === "scanner_candidates_updated") {
    return t("notificationScannerUpdatedBody", {
      count: stringMeta(row, "candidates_written")
    });
  }
  return row.body || "-";
}

function stringMeta(row: NotificationEvent, key: string) {
  const value = row.metadata_json?.[key];
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  return String(value);
}
