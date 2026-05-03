"use client";

import { CircleHelp } from "lucide-react";

import { useAppI18n } from "@/lib/use-app-i18n";

export function ScanActionsHelp() {
  const { t } = useAppI18n();

  return (
    <div className="group relative inline-flex">
      <button
        aria-label={t("scanActionsHelp")}
        className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md border border-line bg-white text-slate-600 transition-colors hover:border-teal hover:text-teal"
        type="button"
      >
        <CircleHelp size={17} />
      </button>
      <div
        className="pointer-events-none absolute right-0 top-full z-30 mt-2 w-80 rounded-md border border-line bg-white p-3 text-left text-xs leading-5 text-slate-600 opacity-0 shadow-lg transition-opacity duration-150 group-focus-within:opacity-100 group-hover:opacity-100"
        role="tooltip"
      >
        <p>
          <span className="font-semibold text-ink">{t("quickRescan")}:</span> {t("quickRescanHelp")}
        </p>
        <p className="mt-2">
          <span className="font-semibold text-ink">{t("refreshBarsAndRescan")}:</span>{" "}
          {t("marketRefreshRescanHelp")}
        </p>
      </div>
    </div>
  );
}
