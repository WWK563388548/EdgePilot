import type { ReactNode } from "react";

export function DetailFieldPanel({
  children,
  title
}: {
  children: ReactNode;
  title: string;
}) {
  return (
    <section className="rounded-md border border-line bg-panel/45 px-3 py-3">
      <h3 className="mb-3 text-xs font-semibold uppercase text-slate-500">{title}</h3>
      <dl className="grid grid-cols-2 gap-3 md:grid-cols-3">{children}</dl>
    </section>
  );
}
