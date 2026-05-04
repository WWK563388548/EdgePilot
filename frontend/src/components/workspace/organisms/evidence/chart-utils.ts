import type { PAEvidenceBar } from "@/lib/api";

export function buildDateTicks(bars: PAEvidenceBar[]) {
  if (bars.length < 2) {
    return [];
  }

  const targetCount = bars.length >= 80 ? 6 : bars.length >= 45 ? 5 : 4;
  const tickCount = Math.min(targetCount, bars.length);
  const indexes = new Set<number>();
  for (let tick = 0; tick < tickCount; tick += 1) {
    indexes.add(Math.round((tick / Math.max(1, tickCount - 1)) * (bars.length - 1)));
  }

  return Array.from(indexes)
    .sort((a, b) => a - b)
    .map((index) => ({ index, ts: bars[index].ts }));
}
