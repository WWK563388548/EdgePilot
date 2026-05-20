"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BadgeCheck, PauseCircle, PlayCircle, ShieldCheck } from "lucide-react";

import { CompactStat, StatusPill, TableShell } from "@/components/workspace/common";
import { api, type StrategyReadiness, type ValidationGateStatus } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function ValidationView({ locale }: { locale: Locale }) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const readiness = useQuery({
    queryKey: ["validation-readiness"],
    queryFn: api.validationReadiness
  });
  const evaluate = useMutation({
    mutationFn: (strategyName: string) => api.evaluateValidationStrategy(strategyName),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["validation-readiness"] })
  });
  const killSwitch = useMutation({
    mutationFn: ({ strategyName, paused }: { strategyName: string; paused: boolean }) =>
      api.updateStrategyKillSwitch(strategyName, {
        status: paused ? "paused" : "active",
        reason: paused ? "manual_pause" : null
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["validation-readiness"] })
  });

  const rows = readiness.data ?? [];
  const blockedCount = rows.filter((row) => row.gate.status === "blocked").length;
  const shadowCount = rows.filter((row) => row.gate.status === "shadow_only").length;
  const paperCount = rows.filter((row) => row.gate.status === "paper_only").length;
  const allowedCount = rows.filter((row) => row.gate.status === "micro_live_allowed").length;

  return (
    <section className="flex flex-col gap-4">
      <section className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-teal/20 bg-teal/5 text-teal">
            <ShieldCheck size={20} />
          </div>
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-ink">{t("validationEngine")}</h2>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
              {t("validationEngineHelp")}
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-3 md:grid-cols-4">
        <CompactStat icon={<BadgeCheck size={18} />} label={t("microLiveAllowed")} value={allowedCount} />
        <CompactStat icon={<PlayCircle size={18} />} label={t("paperOnly")} value={paperCount} />
        <CompactStat icon={<PauseCircle size={18} />} label={t("shadowOnly")} value={shadowCount} />
        <CompactStat icon={<ShieldCheck size={18} />} label={t("blocked")} value={blockedCount} />
      </div>

      <TableShell
        error={readiness.isError || evaluate.isError || killSwitch.isError}
        loading={readiness.isLoading || evaluate.isPending || killSwitch.isPending}
        locale={locale}
        title={t("strategyReadiness")}
      >
        <table className="min-w-full table-fixed text-left text-sm">
          <thead className="bg-panel text-xs uppercase tracking-normal text-slate-500">
            <tr>
              <th className="w-52 px-4 py-3">{t("strategy")}</th>
              <th className="w-36 px-4 py-3">{t("gateStatus")}</th>
              <th className="w-36 px-4 py-3">{t("strategyStage")}</th>
              <th className="w-64 px-4 py-3">{t("evidence")}</th>
              <th className="w-64 px-4 py-3">{t("gateReasons")}</th>
              <th className="w-48 px-4 py-3">{t("actions")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map((row) => {
              const paused = row.kill_switch?.status === "paused" || row.kill_switch?.status === "blocked";
              return (
                <tr className="bg-white align-top" key={row.strategy_name}>
                  <td className="px-4 py-4">
                    <div className="font-semibold text-ink">
                      {labelFor("plan", row.strategy_name)}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">{row.strategy_name}</div>
                  </td>
                  <td className="px-4 py-4">
                    <StatusPill label={labelFor("status", row.gate.status)} tone={gateTone(row.gate.status)} />
                  </td>
                  <td className="px-4 py-4 font-semibold text-ink">
                    {labelFor("status", row.gate.stage)}
                  </td>
                  <td className="px-4 py-4">
                    <EvidenceSummary locale={locale} row={row} />
                  </td>
                  <td className="px-4 py-4 text-slate-600">
                    {row.gate.reasons.length ? (
                      <ul className="flex flex-col gap-1">
                        {row.gate.reasons.map((reason) => (
                          <li key={reason}>{labelFor("plan", reason)}</li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-teal">{t("noBlockingReasons")}</span>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-wrap gap-2">
                      <button
                        className="focus-ring inline-flex h-8 items-center gap-2 rounded-md border border-line bg-white px-3 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={evaluate.isPending}
                        onClick={() => evaluate.mutate(row.strategy_name)}
                        type="button"
                      >
                        <BadgeCheck size={14} />
                        {t("evaluateGate")}
                      </button>
                      <button
                        className="focus-ring inline-flex h-8 items-center gap-2 rounded-md border border-line bg-white px-3 text-xs font-semibold text-ink transition-colors hover:border-teal hover:text-teal disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={killSwitch.isPending}
                        onClick={() => killSwitch.mutate({ strategyName: row.strategy_name, paused: !paused })}
                        type="button"
                      >
                        {paused ? <PlayCircle size={14} /> : <PauseCircle size={14} />}
                        {paused ? t("resumeStrategy") : t("pauseStrategy")}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 ? (
              <tr>
                <td className="px-4 py-8 text-slate-500" colSpan={6}>
                  {t("noValidationReadiness")}
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </TableShell>
    </section>
  );
}

function EvidenceSummary({ locale, row }: { locale: Locale; row: StrategyReadiness }) {
  const { t } = useAppI18n();
  const latest = row.latest_test_run;

  return (
    <div className="flex flex-col gap-1 text-slate-600">
      <div>
        {t("currentTrades")}:{" "}
        <span className="font-semibold text-ink">
          {formatNumber(row.gate.current_trades, 0, locale)} /{" "}
          {formatNumber(row.gate.required_trades, 0, locale)}
        </span>
      </div>
      <div>
        {t("profitFactor")}:{" "}
        <span className="font-semibold text-ink">
          {formatNumber(row.gate.current_profit_factor, 2, locale)}
        </span>
      </div>
      <div>
        {t("expectancyR")}:{" "}
        <span className="font-semibold text-ink">
          {formatNumber(row.gate.current_expectancy_r, 2, locale)}
        </span>
      </div>
      <div className="text-xs text-slate-500">
        {latest?.completed_at ? formatDate(latest.completed_at, locale) : t("noCompletedTestRun")}
      </div>
    </div>
  );
}

function gateTone(status: ValidationGateStatus) {
  if (status === "micro_live_allowed") {
    return "good";
  }
  if (status === "paper_only" || status === "shadow_only") {
    return "warn";
  }
  return "bad";
}
