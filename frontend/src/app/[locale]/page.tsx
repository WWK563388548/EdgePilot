import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { EdgePilotWorkspace } from "@/components/workspace/edgepilot-workspace";
import { isLocale, localeOptions, type Locale } from "@/lib/i18n-config";

type PageProps = {
  params: Promise<{ locale: string }>;
};

export function generateStaticParams() {
  return localeOptions.map((option) => ({ locale: option.id }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  return {
    title: "EdgePilot",
    description:
      locale === "zh"
        ? "交易运营工作台"
        : locale === "ja"
          ? "トレード運用ワークスペース"
          : "Trading operations workspace"
  };
}

export default async function LocalePage({ params }: PageProps) {
  const { locale } = await params;
  if (!isLocale(locale)) {
    notFound();
  }

  return <EdgePilotWorkspace locale={locale as Locale} />;
}
