"use client";

import { X } from "lucide-react";
import { useCallback, useEffect, useState, type ReactNode } from "react";

export function DetailModalShell({
  children,
  closeLabel,
  onClose,
  subtitle,
  title
}: {
  children: ReactNode;
  closeLabel: string;
  onClose?: () => void;
  subtitle: string;
  title: string;
}) {
  const [closing, setClosing] = useState(false);

  const requestClose = useCallback(() => {
    if (!onClose || closing) {
      return;
    }
    setClosing(true);
    window.setTimeout(onClose, 180);
  }, [closing, onClose]);

  useEffect(() => {
    setClosing(false);
  }, [title, subtitle]);

  useEffect(() => {
    if (!onClose) {
      return undefined;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        requestClose();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, requestClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-6">
      {onClose ? (
        <div
          aria-hidden="true"
          className={`absolute inset-0 cursor-default bg-transparent ${
            closing ? "detail-backdrop-out" : "detail-backdrop-in"
          }`}
          onClick={requestClose}
        />
      ) : null}
      <section
        aria-label={title}
        aria-modal="true"
        className={`relative z-10 flex h-[92vh] w-[calc(100vw-1rem)] max-w-[1480px] flex-col overflow-hidden rounded-lg border border-line bg-white shadow-2xl sm:h-[85vh] sm:w-[85vw] ${
          closing ? "detail-modal-out" : "detail-modal-in"
        }`}
        role="dialog"
      >
        <div className="flex min-h-20 shrink-0 items-center justify-between gap-3 border-b border-line bg-white px-5 py-4 sm:px-6">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-ink">{title}</h2>
            <p className="truncate text-sm text-slate-500">{subtitle}</p>
          </div>
          {onClose ? (
            <button
              className="focus-ring inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-line bg-white text-slate-700 transition-colors hover:border-slate-400 hover:bg-panel"
              onClick={requestClose}
              title={closeLabel}
              type="button"
            >
              <X size={18} />
            </button>
          ) : null}
        </div>
        <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-5 py-5 sm:px-6">{children}</div>
      </section>
    </div>
  );
}
