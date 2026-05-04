"use client";

import { BarChart3, Gauge, RefreshCw, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";

import { useAppI18n } from "@/lib/use-app-i18n";

export function ScannerOutcomeGuide() {
  const { t } = useAppI18n();
  const items = [
    {
      icon: <Gauge size={17} />,
      title: t("outcomeGuideSampleTitle"),
      body: t("outcomeGuideSampleBody")
    },
    {
      icon: <BarChart3 size={17} />,
      title: t("outcomeGuideSignalTitle"),
      body: t("outcomeGuideSignalBody")
    },
    {
      icon: <ShieldAlert size={17} />,
      title: t("outcomeGuideRiskTitle"),
      body: t("outcomeGuideRiskBody")
    },
    {
      icon: <RefreshCw size={17} />,
      title: t("outcomeGuideRecalculateTitle"),
      body: t("outcomeGuideRecalculateBody")
    }
  ];

  return (
    <section className="rounded-md border border-teal/20 bg-teal-50/55 p-4 text-sm shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="flex flex-col gap-1.5 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-ink">{t("outcomeGuideTitle")}</h3>
          <p className="mt-1 max-w-5xl leading-6 text-slate-700">{t("outcomeGuideIntro")}</p>
        </div>
      </div>
      <div className="mt-4 grid gap-3 lg:grid-cols-4">
        {items.map((item) => (
          <GuideCard body={item.body} icon={item.icon} key={item.title} title={item.title} />
        ))}
      </div>
    </section>
  );
}

function GuideCard({ icon, title, body }: { icon: ReactNode; title: string; body: string }) {
  return (
    <div className="rounded-md border border-white/80 bg-white/85 p-3">
      <div className="flex items-center gap-2 font-semibold text-ink">
        <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-teal/20 bg-teal-50 text-teal">
          {icon}
        </span>
        <span>{title}</span>
      </div>
      <p className="mt-2 leading-6 text-slate-600">{body}</p>
    </div>
  );
}
