"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Clock3, RefreshCw, Workflow, XCircle } from "lucide-react";
import { useState } from "react";

import { CompactStat } from "@/components/workspace/atoms/stat-card";
import { PaginationControls, StatusPill, TableShell } from "@/components/workspace/common";
import { api, type JobRun } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

const JOB_PAGE_SIZE = 10;

type JobStep = {
  name?: string;
  status?: string;
  summary?: Record<string, unknown>;
};
type Translator = ReturnType<typeof useAppI18n>["t"];

export function AutomationView({ locale }: { locale: Locale }) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [lastRun, setLastRun] = useState<JobRun | null>(null);

  const runs = useQuery({
    queryKey: ["job-runs", page],
    queryFn: () =>
      api.jobRuns({
        limit: JOB_PAGE_SIZE + 1,
        offset: page * JOB_PAGE_SIZE
      })
  });
  const runsCount = useQuery({
    queryKey: ["job-runs-count"],
    queryFn: () => api.jobRunsCount()
  });
  const runJob = useMutation({
    mutationFn: () =>
      api.runAutomationJob({
        evaluate_alerts: true,
        recalculate_outcomes: true,
        refresh_market_data: true
      }),
    onSuccess: async (response) => {
      setLastRun(response);
      setPage(0);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["job-runs"] }),
        queryClient.invalidateQueries({ queryKey: ["job-runs-count"] }),
        queryClient.invalidateQueries({ queryKey: ["candidates"] }),
        queryClient.invalidateQueries({ queryKey: ["candidates-count"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["pa-setups"] }),
        queryClient.invalidateQueries({ queryKey: ["pa-setups-count"] }),
        queryClient.invalidateQueries({ queryKey: ["scanner-outcomes"] }),
        queryClient.invalidateQueries({ queryKey: ["scanner-outcomes-count"] }),
        queryClient.invalidateQueries({ queryKey: ["scanner-outcomes-summary"] }),
        queryClient.invalidateQueries({ queryKey: ["alerts"] }),
        queryClient.invalidateQueries({ queryKey: ["alerts-count"] }),
        queryClient.invalidateQueries({ queryKey: ["notifications"] }),
        queryClient.invalidateQueries({ queryKey: ["notifications-count"] })
      ]);
    },
    onError: () => setLastRun(null)
  });

  const rawRows = runs.data ?? [];
  const rows = rawRows.slice(0, JOB_PAGE_SIZE);
  const hasNextPage =
    runsCount.data?.total !== undefined
      ? (page + 1) * JOB_PAGE_SIZE < runsCount.data.total
      : rawRows.length > JOB_PAGE_SIZE;
  const latest = rows[0] ?? lastRun;

  return (
    <section className="flex flex-col gap-4">
      <section className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Workflow size={18} className="text-teal" />
              <h2 className="text-base font-semibold text-ink">{t("automationRunner")}</h2>
            </div>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              {t("automationRunnerHelp")}
            </p>
          </div>
          <button
            className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition-colors hover:bg-teal disabled:cursor-not-allowed disabled:opacity-60"
            disabled={runJob.isPending}
            onClick={() => runJob.mutate()}
            type="button"
          >
            <RefreshCw size={16} className={runJob.isPending ? "animate-spin" : ""} />
            {runJob.isPending ? t("automationRunning") : t("runAutomationJob")}
          </button>
        </div>
        {lastRun || runJob.isError ? (
          <div
            className={`mt-4 rounded-md border px-3 py-2 text-sm ${
              runJob.isError || lastRun?.status === "failed"
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : "border-teal-200 bg-teal-50 text-teal-800"
            }`}
          >
            {runJob.isError
              ? t("automationRunFailed")
              : t("automationRunResult", {
                  records: lastRun?.records_written ?? 0,
                  status: labelFor("status", lastRun?.status)
                })}
          </div>
        ) : null}
      </section>

      <div className="grid gap-3 md:grid-cols-3">
        <CompactStat
          icon={<Clock3 size={18} />}
          label={t("latestJobStatus")}
          value={latest ? labelFor("status", latest.status) : "-"}
        />
        <CompactStat
          icon={<CheckCircle2 size={18} />}
          label={t("latestJobRecords")}
          value={formatNumber(latest?.records_written, 0, locale)}
        />
        <CompactStat
          icon={<Workflow size={18} />}
          label={t("automationRuns")}
          value={runsCount.data?.total ?? rows.length}
        />
      </div>

      <TableShell
        actions={
          <button
            className="focus-ring inline-flex h-8 items-center gap-2 rounded-md border border-line bg-white px-3 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60"
            disabled={runJob.isPending}
            onClick={() => runJob.mutate()}
            type="button"
          >
            <RefreshCw size={15} className={runJob.isPending ? "animate-spin" : ""} />
            {t("runAutomationJob")}
          </button>
        }
        error={runs.isError || runsCount.isError || runJob.isError}
        loading={runs.isLoading || runsCount.isLoading || runJob.isPending}
        locale={locale}
        title={t("automationRuns")}
      >
        <table className="min-w-full table-fixed text-left text-sm">
          <thead className="bg-panel text-xs uppercase tracking-normal text-slate-500">
            <tr>
              <th className="w-36 px-4 py-3">{t("status")}</th>
              <th className="w-44 px-4 py-3">{t("jobType")}</th>
              <th className="w-[32rem] px-4 py-3">{t("jobSummary")}</th>
              <th className="w-28 px-4 py-3">{t("records")}</th>
              <th className="w-40 px-4 py-3">{t("startedAt")}</th>
              <th className="w-28 px-4 py-3">{t("duration")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map((run) => (
              <tr className="bg-white align-top" key={run.run_id}>
                <td className="px-4 py-4">
                  <StatusPill label={labelFor("status", run.status)} tone={jobTone(run.status)} />
                </td>
                <td className="px-4 py-4 font-semibold text-ink">{t("marketRefreshScanJob")}</td>
                <td className="px-4 py-4">
                  <JobRunSummary locale={locale} run={run} />
                </td>
                <td className="px-4 py-4 font-semibold text-ink">
                  {formatNumber(run.records_written, 0, locale)}
                </td>
                <td className="px-4 py-4 text-slate-600">{formatDate(run.started_at, locale)}</td>
                <td className="px-4 py-4 text-slate-600">{formatDuration(run.duration_ms, locale)}</td>
              </tr>
            ))}
            {rows.length === 0 ? (
              <tr>
                <td className="px-4 py-8 text-slate-500" colSpan={6}>
                  {t("noJobRuns")}
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
        <PaginationControls
          hasNext={hasNextPage}
          itemCount={rows.length}
          onPageChange={setPage}
          page={page}
          pageSize={JOB_PAGE_SIZE}
          totalCount={runsCount.data?.total}
        />
      </TableShell>
    </section>
  );
}

function JobRunSummary({ locale, run }: { locale: Locale; run: JobRun }) {
  const { t } = useAppI18n();
  const steps = stepsFromMetadata(run.metadata_json);

  if (run.status === "failed") {
    return (
      <div className="flex items-start gap-2 text-rose-700">
        <XCircle size={16} className="mt-0.5 shrink-0" />
        <span>{run.error_message ?? t("automationRunFailed")}</span>
      </div>
    );
  }

  if (!steps.length) {
    return <span className="text-slate-500">-</span>;
  }

  return (
    <div className="flex flex-col gap-1.5">
      {steps.map((step, index) => (
        <div className="flex flex-wrap items-center gap-2 text-slate-600" key={`${step.name ?? "step"}-${index}`}>
          <span className="font-semibold text-ink">{stepLabel(step.name, t)}</span>
          <span className="text-slate-400">·</span>
          <span>{summaryText(step.summary, locale, t)}</span>
        </div>
      ))}
    </div>
  );
}

function stepsFromMetadata(metadata: Record<string, unknown> | null): JobStep[] {
  const value = metadata?.steps;
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is JobStep => Boolean(item && typeof item === "object"));
}

function stepLabel(name: string | undefined, t: Translator) {
  if (name === "market_refresh_scan") {
    return t("jobStepMarketRefreshScan");
  }
  if (name === "oneil_core_scan") {
    return t("jobStepOneilCoreScan");
  }
  if (name === "scanner_outcomes") {
    return t("jobStepScannerOutcomes");
  }
  if (name === "exit_alerts") {
    return t("jobStepExitAlerts");
  }
  return name ?? "-";
}

function summaryText(summary: Record<string, unknown> | undefined, locale: Locale, t: Translator) {
  if (!summary) {
    return "-";
  }
  const preferredKeys = [
    "bars_written",
    "facts_written",
    "setups_written",
    "candidates_written",
    "outcomes_written",
    "alerts_created",
    "duplicate_alerts"
  ];
  return preferredKeys
    .filter((key) => typeof summary[key] === "number")
    .map((key) => `${summaryLabel(key, t)}: ${formatNumber(summary[key] as number, 0, locale)}`)
    .join(" / ");
}

function summaryLabel(key: string, t: Translator) {
  const labels: Record<string, string> = {
    alerts_created: t("alertsCreated"),
    bars_written: t("barsWritten"),
    candidates_written: t("candidatesWritten"),
    duplicate_alerts: t("duplicateAlerts"),
    facts_written: t("factsWritten"),
    outcomes_written: t("outcomesWritten"),
    setups_written: t("setupsWritten")
  };
  return labels[key] ?? key;
}

function jobTone(status: string) {
  if (status === "succeeded") {
    return "good";
  }
  if (status === "failed") {
    return "bad";
  }
  return "warn";
}

function formatDuration(value: number | null, locale: Locale) {
  if (value === null) {
    return "-";
  }
  if (value < 1000) {
    return `${formatNumber(value, 0, locale)} ms`;
  }
  return `${formatNumber(value / 1000, 1, locale)} s`;
}
