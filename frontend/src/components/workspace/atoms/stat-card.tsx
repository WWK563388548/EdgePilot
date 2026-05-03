import { CircleDot } from "lucide-react";
import type { ReactNode } from "react";

export function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="mb-3 flex items-center justify-between text-slate-500">
        {icon}
        <CircleDot size={14} />
      </div>
      <div className="text-2xl font-semibold text-ink">{value}</div>
      <div className="mt-1 text-sm text-slate-600">{label}</div>
    </div>
  );
}

export function CompactStat({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-line bg-white px-4 py-3 shadow-[0_1px_0_rgba(22,32,42,0.04)]">
      <div className="mb-2 flex items-center justify-between text-slate-500">
        {icon}
        <span className="text-xs uppercase">{label}</span>
      </div>
      <div className="truncate text-xl font-semibold text-ink">{value}</div>
    </div>
  );
}
