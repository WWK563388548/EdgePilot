import { create } from "zustand";
import type { Locale } from "@/lib/i18n";

export type WorkspaceView =
  | "overview"
  | "candidates"
  | "pa_lab"
  | "positions"
  | "alerts"
  | "journal"
  | "settings";

type WorkspaceState = {
  view: WorkspaceView;
  locale: Locale;
  setView: (view: WorkspaceView) => void;
  setLocale: (locale: Locale) => void;
};

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  view: "overview",
  locale: "zh",
  setView: (view) => set({ view }),
  setLocale: (locale) => set({ locale })
}));
