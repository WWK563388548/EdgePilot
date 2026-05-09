"use client";

import { useAppI18n } from "@/lib/use-app-i18n";

export type CandidateDecisionFilter = "candidate" | "watch" | "all";
export type CandidateStrategyFilter = "all" | "etf_rotation_us_etf" | "oneil_core_us_etf";

export function DecisionFilterControl({
  active,
  onChange
}: {
  active: CandidateDecisionFilter;
  onChange: (filter: CandidateDecisionFilter) => void;
}) {
  const { labelFor, t } = useAppI18n();
  const options: Array<{ value: CandidateDecisionFilter; label: string }> = [
    { value: "candidate", label: labelFor("status", "candidate") },
    { value: "watch", label: labelFor("status", "watch") },
    { value: "all", label: t("allCandidateResults") }
  ];

  return (
    <div
      aria-label={t("candidateDecisionFilter")}
      className="inline-flex h-9 rounded-md border border-line bg-panel p-1"
      role="group"
    >
      {options.map((option) => (
        <button
          aria-pressed={active === option.value}
          className={`focus-ring min-w-16 rounded px-3 text-sm font-semibold transition-colors ${
            active === option.value ? "bg-ink text-white shadow-sm" : "text-slate-600 hover:text-ink"
          }`}
          key={option.value}
          onClick={() => onChange(option.value)}
          type="button"
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function StrategyFilterControl({
  active,
  onChange
}: {
  active: CandidateStrategyFilter;
  onChange: (filter: CandidateStrategyFilter) => void;
}) {
  const { t } = useAppI18n();
  const options: Array<{ value: CandidateStrategyFilter; label: string }> = [
    { value: "all", label: t("allStrategies") },
    { value: "etf_rotation_us_etf", label: t("etfRotationStrategy") },
    { value: "oneil_core_us_etf", label: t("oneilSatelliteStrategy") }
  ];

  return (
    <div
      aria-label={t("candidateStrategyFilter")}
      className="inline-flex h-9 rounded-md border border-line bg-panel p-1"
      role="group"
    >
      {options.map((option) => (
        <button
          aria-pressed={active === option.value}
          className={`focus-ring min-w-16 rounded px-3 text-sm font-semibold transition-colors ${
            active === option.value ? "bg-ink text-white shadow-sm" : "text-slate-600 hover:text-ink"
          }`}
          key={option.value}
          onClick={() => onChange(option.value)}
          type="button"
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
