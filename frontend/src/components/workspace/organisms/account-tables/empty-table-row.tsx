import { DataState } from "@/components/workspace/atoms/data-state";
import type { Locale } from "@/lib/i18n-config";

export function EmptyTableRow({
  colSpan,
  error,
  loading,
  locale,
  message
}: {
  colSpan: number;
  error: boolean;
  loading: boolean;
  locale: Locale;
  message: string;
}) {
  return (
    <tr>
      <td className="border-t border-line px-4 py-6 text-sm text-slate-600" colSpan={colSpan}>
        {loading || error ? <DataState isLoading={loading} isError={error} locale={locale} /> : message}
      </td>
    </tr>
  );
}
