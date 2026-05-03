import { Badge } from "@/components/ui/badge";

export type StatusTone = "good" | "warn" | "bad" | "neutral";

export function StatusPill({
  label,
  tone = "neutral"
}: {
  label: string;
  tone?: StatusTone;
}) {
  const variants = {
    good: "success",
    warn: "warning",
    bad: "destructive",
    neutral: "default"
  } as const;

  return <Badge variant={variants[tone]}>{label}</Badge>;
}
