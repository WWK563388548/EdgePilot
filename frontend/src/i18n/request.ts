import { getRequestConfig } from "next-intl/server";

import { defaultLocale, isLocale } from "@/lib/i18n-config";
import { getAppMessages } from "@/lib/i18n";

export default getRequestConfig(async ({ requestLocale }) => {
  const requestedLocale = await requestLocale;
  const locale = isLocale(requestedLocale) ? requestedLocale : defaultLocale;

  return {
    locale,
    messages: getAppMessages(locale),
    timeZone: "Asia/Tokyo"
  };
});
