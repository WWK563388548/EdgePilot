export type Locale = "zh" | "en" | "ja";

export const defaultLocale: Locale = "zh";
export const locales: Locale[] = ["zh", "en", "ja"];

export const localeOptions: Array<{ id: Locale; label: string }> = [
  { id: "zh", label: "中文" },
  { id: "en", label: "English" },
  { id: "ja", label: "日本語" }
];

export const localeTag: Record<Locale, string> = {
  zh: "zh-CN",
  en: "en-US",
  ja: "ja-JP"
};

export function isLocale(value: string | undefined): value is Locale {
  return locales.includes(value as Locale);
}
