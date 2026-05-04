export function decisionTone(value: string | null | undefined): "good" | "warn" | "bad" | "neutral" {
  if (value === "candidate" || value === "live_allowed" || value === "matured_60d") {
    return "good";
  }
  if (value === "watch" || value === "paper_allowed" || value === "shadow_only" || value === "pending") {
    return "warn";
  }
  if (value === "avoid" || value === "failed" || value === "missing_reference") {
    return "bad";
  }
  return "neutral";
}
