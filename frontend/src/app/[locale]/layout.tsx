import { NextIntlClientProvider } from "next-intl";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";

import { isLocale, localeTag } from "@/lib/i18n-config";

export default async function LocaleLayout({
  children,
  params
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) {
    notFound();
  }

  return (
    <NextIntlClientProvider locale={locale}>
      <div data-locale={locale} lang={localeTag[locale]}>
        {children}
      </div>
    </NextIntlClientProvider>
  );
}
