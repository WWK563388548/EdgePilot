import type { Locale } from "@/lib/i18n-config";

export type PaginatedTableProps<T> = {
  data: T[];
  loading: boolean;
  error: boolean;
  page: number;
  pageSize: number;
  totalCount?: number;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
  locale: Locale;
};
