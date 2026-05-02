"use client";

import { BarChart3, LogIn } from "lucide-react";

import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function AuthScreen({
  status,
  locale,
  action,
  secondaryAction,
  secondaryLabel
}: {
  status: string;
  locale: Locale;
  action?: () => Promise<void>;
  secondaryAction?: () => Promise<void>;
  secondaryLabel?: string;
}) {
  const { t } = useAppI18n();

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#eef2f5] px-4">
      <section className="w-full max-w-sm rounded-md border border-line bg-white p-5 shadow-[0_1px_0_rgba(22,32,42,0.05)]">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-ink text-white">
            <BarChart3 size={22} />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-ink">EdgePilot</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
        </div>
        {action ? (
          <div className="grid gap-2">
            <button
              className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
              onClick={() => void action()}
              type="button"
            >
              <LogIn size={16} />
              {secondaryAction ? t("resendVerificationEmail") : t("signIn")}
            </button>
            {secondaryAction ? (
              <button
                className="focus-ring inline-flex w-full items-center justify-center rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:border-slate-400"
                onClick={() => void secondaryAction()}
                type="button"
              >
                {secondaryLabel}
              </button>
            ) : null}
          </div>
        ) : (
          <div className="h-2 rounded-md bg-panel" />
        )}
      </section>
    </main>
  );
}
