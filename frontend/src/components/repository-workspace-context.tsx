"use client";

import { createContext, useContext, useMemo, type ReactNode } from "react";

import type { BranchSummary, RepositoryDetail, RepositorySummary, AnalyzeResponse } from "@/types/repository";

export type RepositoryWorkspaceTab =
  | "overview"
  | "search"
  | "chat"
  | "graph"
  | "docs"
  | "pull-requests";

export interface RepositoryWorkspaceContextValue {
  repositoryId: string;
  activeTab: RepositoryWorkspaceTab;
  branches: BranchSummary[];
  selectedBranch: string | null;
  setSelectedBranch: (branch: string) => void;
  detail: RepositoryDetail | RepositorySummary | null | undefined;
  isLoading: boolean;
  loadError: string | null;
  branchLoading: boolean;
  refreshJob: AnalyzeResponse | null;
  refreshError: string | null;
  isRefreshing: boolean;
  handleRefresh: () => Promise<void>;
}

const RepositoryWorkspaceContext = createContext<RepositoryWorkspaceContextValue | null>(null);

export function RepositoryWorkspaceProvider({
  value,
  children,
}: {
  value: RepositoryWorkspaceContextValue;
  children: ReactNode;
}) {
  const memo = useMemo(() => value, [value]);
  return (
    <RepositoryWorkspaceContext.Provider value={memo}>
      {children}
    </RepositoryWorkspaceContext.Provider>
  );
}

export function useRepositoryWorkspace() {
  const ctx = useContext(RepositoryWorkspaceContext);
  if (!ctx) {
    throw new Error("useRepositoryWorkspace must be used within RepositoryWorkspaceProvider");
  }
  return ctx;
}
