export function decisionTone(value: string | null | undefined): "good" | "warn" | "bad" | "neutral" {
  if (value === "candidate" || value === "live_allowed") {
    return "good";
  }
  if (value === "watch" || value === "paper_allowed" || value === "shadow_only") {
    return "warn";
  }
  if (value === "avoid" || value === "failed") {
    return "bad";
  }
  return "neutral";
}
