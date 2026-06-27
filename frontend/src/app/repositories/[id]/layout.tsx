"use client";

import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import {
  RepositoryWorkspaceProvider,
  type RepositoryWorkspaceTab,
} from "@/components/repository-workspace-context";
import { RepositoryWorkspaceShell } from "@/components/repository-workspace-shell";
import { useAuth } from "@/hooks/use-auth";
import {
  useRepositoryBranches,
  useRepositoryDetails,
} from "@/hooks/use-repository-data";
import { queryKeys } from "@/lib/query-keys";
import { refreshRepository } from "@/services/repositories";
import type { AnalyzeResponse } from "@/types/repository";

function tabFromPathname(pathname: string, repositoryId: string): RepositoryWorkspaceTab {
  const base = `/repositories/${repositoryId}`;
  if (pathname === base) return "overview";
  if (pathname.startsWith(`${base}/search`)) return "search";
  if (pathname.startsWith(`${base}/chat`)) return "chat";
  if (pathname.startsWith(`${base}/graph`)) return "graph";
  if (pathname.startsWith(`${base}/docs`)) return "docs";
  if (pathname.startsWith(`${base}/pull-requests`)) return "pull-requests";
  return "overview";
}

export default function RepositoryLayout({ children }: { children: React.ReactNode }) {
  const params = useParams<{ id: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const queryClient = useQueryClient();
  const repositoryId = params.id;

  const branchFromUrl = searchParams.get("branch");
  const [branchOverride, setBranchOverride] = useState<string | null>(null);
  const [refreshJob, setRefreshJob] = useState<AnalyzeResponse | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const branchesQuery = useRepositoryBranches(repositoryId);
  const branches = useMemo(() => branchesQuery.data ?? [], [branchesQuery.data]);
  const selectedBranch =
    branchOverride ?? branchFromUrl ?? branches[0]?.branch ?? null;

  const detailsQuery = useRepositoryDetails(repositoryId, selectedBranch);
  const detail = detailsQuery.data;

  const activeTab = tabFromPathname(pathname, repositoryId);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/");
    }
  }, [authLoading, isAuthenticated, router]);

  const setSelectedBranch = useCallback(
    (branch: string) => {
      setBranchOverride(branch);
      const params = new URLSearchParams(searchParams.toString());
      params.set("branch", branch);
      router.replace(`${pathname}?${params.toString()}`);
    },
    [pathname, router, searchParams],
  );

  useEffect(() => {
    if (!repositoryId) return;
    void queryClient.prefetchQuery({
      queryKey: queryKeys.repositoryPullRequests(repositoryId),
      queryFn: async () => {
        const { listPullRequests } = await import("@/services/repositories");
        return listPullRequests(repositoryId);
      },
    });
  }, [repositoryId, queryClient]);

  const invalidateRepositoryData = useCallback(() => {
    if (!repositoryId) return;
    void queryClient.invalidateQueries({
      queryKey: ["repository", repositoryId],
    });
  }, [repositoryId, queryClient]);

  const handleRefresh = useCallback(async () => {
    if (!repositoryId) return;
    setRefreshing(true);
    setRefreshError(null);
    try {
      const result = await refreshRepository(repositoryId);
      setRefreshJob(result);
      if (result.cached) {
        invalidateRepositoryData();
      }
    } catch (e) {
      setRefreshError(e instanceof Error ? e.message : "Failed to refresh repository");
    } finally {
      setRefreshing(false);
    }
  }, [repositoryId, invalidateRepositoryData]);

  const isLoading =
    (branchesQuery.isLoading && branches.length === 0) ||
    (detailsQuery.isLoading && !detail);
  const branchLoading = detailsQuery.isFetching && Boolean(detail);
  const loadError =
    branchesQuery.error instanceof Error
      ? branchesQuery.error.message
      : detailsQuery.error instanceof Error
        ? detailsQuery.error.message
        : null;

  const contextValue = useMemo(
    () => ({
      repositoryId,
      activeTab,
      branches,
      selectedBranch,
      setSelectedBranch,
      detail: detail ?? null,
      isLoading,
      loadError,
      branchLoading,
      refreshJob,
      refreshError,
      isRefreshing: refreshing,
      handleRefresh,
    }),
    [
      repositoryId,
      activeTab,
      branches,
      selectedBranch,
      setSelectedBranch,
      detail,
      isLoading,
      loadError,
      branchLoading,
      refreshJob,
      refreshError,
      refreshing,
      handleRefresh,
    ],
  );

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="size-6 animate-spin text-violet-500" />
      </div>
    );
  }

  const fullHeight = activeTab === "graph" || activeTab === "pull-requests";

  return (
    <RepositoryWorkspaceProvider value={contextValue}>
      <RepositoryWorkspaceShell fullHeight={fullHeight}>{children}</RepositoryWorkspaceShell>
    </RepositoryWorkspaceProvider>
  );
}
