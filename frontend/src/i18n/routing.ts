import { defineRouting } from "next-intl/routing";

import { defaultLocale, locales } from "@/lib/i18n-config";

export const routing = defineRouting({
  defaultLocale,
  localePrefix: "always",
  locales
});
