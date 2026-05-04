import { formatValue } from "@/lib/format";

export function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium text-ink">{formatValue(value)}</dd>
    </div>
  );
}
