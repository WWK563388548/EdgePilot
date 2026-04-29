"use client";

import { BarChart3, LogOut, RefreshCcw, type LucideIcon } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { StatusPill } from "@/components/workspace/common";
import { useAuth } from "@/lib/auth";
import { isLocale, localeOptions, type Locale } from "@/lib/i18n-config";
import type { WorkspaceView } from "@/lib/store";
import { useAppI18n } from "@/lib/use-app-i18n";

export type WorkspaceNavItem = {
  id: WorkspaceView;
  labelKey: string;
  icon: LucideIcon;
};

export function WorkspaceHeader({
  locale,
  riskMode,
  riskTone
}: {
  locale: Locale;
  riskMode: string;
  riskTone: "good" | "warn" | "bad" | "neutral";
}) {
  const { labelFor, t } = useAppI18n();

  return (
    <header className="border-b border-line bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-ink text-white">
            <BarChart3 size={22} />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-normal text-ink">EdgePilot</h1>
            <p className="text-sm text-slate-600">{t("subtitle")}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill label={labelFor("status", riskMode)} tone={riskTone} />
          <LanguageSwitcher locale={locale} />
          <AuthButton />
          <div className="inline-flex h-10 items-center gap-2 rounded-md border border-line bg-panel px-3 text-sm text-slate-700">
            <RefreshCcw size={16} />
            {t("refresh")}
          </div>
        </div>
      </div>
    </header>
  );
}

export function WorkspaceNav({
  activeView,
  items,
  locale,
  onChange
}: {
  activeView: WorkspaceView;
  items: WorkspaceNavItem[];
  locale: Locale;
  onChange: (view: WorkspaceView) => void;
}) {
  const { t } = useAppI18n();

  return (
    <section className="border-b border-line bg-panel">
      <div className="mx-auto flex max-w-7xl gap-2 overflow-x-auto px-4 py-3 sm:px-6 lg:px-8">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              className={`focus-ring inline-flex h-9 items-center gap-2 whitespace-nowrap rounded-md px-3 text-sm font-medium ${
                isActive
                  ? "bg-ink text-white"
                  : "border border-line bg-white text-slate-700 hover:border-slate-400"
              }`}
              onClick={() => onChange(item.id)}
              type="button"
            >
              <Icon size={16} />
              {t(item.labelKey)}
            </button>
          );
        })}
      </div>
    </section>
  );
}

export function WorkspaceFrame({ children }: { children: ReactNode }) {
  return <main className="min-h-screen bg-[#eef2f5]">{children}</main>;
}

function LanguageSwitcher({ locale }: { locale: Locale }) {
  const pathname = usePathname();
  const router = useRouter();

  const switchLocale = (nextLocale: Locale) => {
    const segments = pathname.split("/");
    if (isLocale(segments[1])) {
      segments[1] = nextLocale;
    } else {
      segments.splice(1, 0, nextLocale);
    }
    router.replace(segments.join("/") || `/${nextLocale}`);
  };

  return (
    <div className="inline-flex h-10 rounded-md border border-line bg-panel p-1">
      {localeOptions.map((option) => (
        <button
          className={`focus-ring min-w-16 rounded px-2.5 text-xs font-medium ${
            locale === option.id ? "bg-ink text-white" : "text-slate-700 hover:bg-white"
          }`}
          key={option.id}
          onClick={() => switchLocale(option.id)}
          type="button"
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function AuthButton() {
  const auth = useAuth();
  return (
    <button
      className="focus-ring inline-flex h-10 max-w-[240px] items-center gap-2 rounded-md border border-line bg-panel px-3 text-sm text-slate-700 hover:border-slate-400"
      onClick={() => auth.logout()}
      type="button"
    >
      <LogOut size={16} className="shrink-0" />
      <span className="truncate">{auth.userLabel}</span>
    </button>
  );
}
