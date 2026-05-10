import { create } from "zustand";

export type WorkspaceView =
  | "overview"
  | "candidates"
  | "pa_lab"
  | "outcomes"
  | "paper_review"
  | "positions"
  | "alerts"
  | "notifications"
  | "automation"
  | "execution"
  | "journal"
  | "settings";

type WorkspaceState = {
  view: WorkspaceView;
  setView: (view: WorkspaceView) => void;
};

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  view: "overview",
  setView: (view) => set({ view })
}));
