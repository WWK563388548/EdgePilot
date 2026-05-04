"use client";

import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";
import type { ReactNode } from "react";

import { useAppI18n } from "@/lib/use-app-i18n";

export function ChartControls({
  canMoveNewer,
  canMoveOlder,
  canZoomIn,
  canZoomOut,
  onMoveNewer,
  onMoveOlder,
  onZoomIn,
  onZoomOut,
  visibleCount
}: {
  canMoveNewer: boolean;
  canMoveOlder: boolean;
  canZoomIn: boolean;
  canZoomOut: boolean;
  onMoveNewer: () => void;
  onMoveOlder: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  visibleCount: number;
}) {
  const { t } = useAppI18n();

  return (
    <div className="flex items-center gap-1">
      <IconButton disabled={!canMoveOlder} label={t("olderBars")} onClick={onMoveOlder}>
        <ChevronLeft size={15} />
      </IconButton>
      <IconButton disabled={!canMoveNewer} label={t("newerBars")} onClick={onMoveNewer}>
        <ChevronRight size={15} />
      </IconButton>
      <IconButton disabled={!canZoomIn} label={t("zoomIn")} onClick={onZoomIn}>
        <ZoomIn size={15} />
      </IconButton>
      <IconButton disabled={!canZoomOut} label={t("zoomOut")} onClick={onZoomOut}>
        <ZoomOut size={15} />
      </IconButton>
      <span className="ml-1 min-w-12 text-right text-xs font-semibold text-slate-500">{visibleCount}D</span>
    </div>
  );
}

function IconButton({
  children,
  disabled,
  label,
  onClick
}: {
  children: ReactNode;
  disabled: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-slate-700 hover:border-slate-400 disabled:cursor-not-allowed disabled:opacity-40"
      disabled={disabled}
      onClick={onClick}
      title={label}
      type="button"
    >
      {children}
    </button>
  );
}
