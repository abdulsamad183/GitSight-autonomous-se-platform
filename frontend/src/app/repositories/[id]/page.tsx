"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { GitGraph, Loader2, MessageSquare, RefreshCw } from "lucide-react";

import { BranchSelector } from "@/components/branch-selector";
import { JobProgressCard } from "@/components/job-progress-card";
import { PullRequestsSection } from "@/components/pull-requests-section";
import { RepositorySearch } from "@/components/repository-search";
import { RepositoryDetailTabs } from "@/components/repository-detail-tabs";
import { RepositoryHero, RepositoryStatsGrid } from "@/components/repository-stats";
import { Button, buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useJobPolling } from "@/hooks/use-job-polling";
import {
  useRepositoryBranches,
  useRepositoryDetails,
  useRepositoryPullRequests,
} from "@/hooks/use-repository-data";
import { getQueryClient } from "@/lib/query-client";
import { refreshRepository } from "@/services/repositories";
import type { AnalyzeResponse } from "@/types/repository";

export default function RepositoryDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const repositoryId = params.id;

  const branchFromUrl = searchParams.get("branch");
  const [branchOverride, setBranchOverride] = useState<string | null>(null);

  const branchesQuery = useRepositoryBranches(repositoryId);
  const branches = branchesQuery.data ?? [];

  const selectedBranch =
    branchOverride ?? branchFromUrl ?? branches[0]?.branch ?? null;

  const detailsQuery = useRepositoryDetails(repositoryId, selectedBranch);
  const [refreshJob, setRefreshJob] = useState<AnalyzeResponse | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const pullRequestsQuery = useRepositoryPullRequests(repositoryId);

  const detail = detailsQuery.data;
  const pullRequests = pullRequestsQuery.data ?? [];

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  const invalidateRepositoryData = useCallback(() => {
    if (!repositoryId) return;
    void getQueryClient().invalidateQueries({
      queryKey: ["repository", repositoryId],
    });
  }, [repositoryId]);

  const shouldPollRefresh = refreshJob?.job_id && !refreshJob.cached;
  const {
    job: polledRefreshJob,
    error: pollError,
    isPolling,
  } = useJobPolling(shouldPollRefresh ? refreshJob.job_id : null, {
    onTerminal: invalidateRepositoryData,
  });

  const handleBranchSelect = (branch: string) => {
    setBranchOverride(branch);
  };

  const handleRefresh = async () => {
    if (!repositoryId) return;
    setRefreshing(true);
    setRefreshError(null);
    try {
      const result = await refreshRepository(repositoryId);
      setRefreshJob(result);
    } catch (e) {
      setRefreshError(e instanceof Error ? e.message : "Failed to refresh repository");
    } finally {
      setRefreshing(false);
    }
  };

  const initialLoading =
    (branchesQuery.isLoading && branches.length === 0) ||
    (detailsQuery.isLoading && !detail);
  const branchLoading = detailsQuery.isFetching && Boolean(detail);
  const loadError =
    branchesQuery.error instanceof Error
      ? branchesQuery.error.message
      : detailsQuery.error instanceof Error
        ? detailsQuery.error.message
        : null;

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="size-6 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-violet-50/50 via-background to-background dark:from-violet-950/20">
      <header className="border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="bg-gradient-to-r from-violet-600 to-sky-600 bg-clip-text text-lg font-bold text-transparent">
            GitSight
          </span>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="default"
              onClick={() => void handleRefresh()}
              disabled={refreshing || isPolling}
            >
              {refreshing || isPolling ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <RefreshCw className="size-4" />
              )}
              <span>{refreshing || isPolling ? "Refreshing..." : "Refresh Repository"}</span>
            </Button>
            <Link href="/dashboard" className={buttonVariants({ variant: "outline" })}>
              Back to Dashboard
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-10">
        {initialLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="size-8 animate-spin text-violet-500" />
          </div>
        )}

        {loadError && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
            {loadError}
          </div>
        )}

        {refreshError && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
            {refreshError}
          </div>
        )}

        {detail && (
          <>
            <RepositoryHero
              owner={detail.owner}
              repository_name={detail.repository_name}
              github_url={detail.github_url}
              latest_commit_hash={detail.latest_commit_hash}
              default_branch={selectedBranch ?? detail.default_branch}
              analysis_status={detail.analysis_status}
            />

            <BranchSelector
              branches={branches}
              selectedBranch={selectedBranch ?? detail.selected_branch ?? branches[0]?.branch ?? ""}
              onSelect={handleBranchSelect}
              branchesTruncated={detail.branches_truncated}
            />

            {refreshJob?.cached && (
              <JobProgressCard
                job={{
                  id: refreshJob.job_id ?? "",
                  status: "COMPLETED",
                  progress: 100,
                  current_stage: "Loaded from database",
                  error_message: null,
                  events: [],
                }}
                repositoryId={refreshJob.repository_id}
                pollError={null}
                cached
                compact
              />
            )}

            {!refreshJob?.cached && polledRefreshJob && (
              <JobProgressCard
                job={polledRefreshJob}
                repositoryId={refreshJob?.repository_id ?? repositoryId}
                pollError={pollError}
                compact
                isRefresh
              />
            )}

            {!refreshJob?.cached && !polledRefreshJob && isPolling && (
              <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
                Starting refresh job...
              </div>
            )}

            {branchLoading && (
              <div className="flex items-center justify-center gap-2 py-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin text-violet-500" />
                Updating branch data...
              </div>
            )}

            <RepositoryStatsGrid
              files_count={detail.files_count}
              classes_count={detail.classes_count}
              functions_count={detail.functions_count}
              methods_count={detail.methods_count}
              dependencies_count={detail.dependencies_count}
              total_pull_requests={detail.total_pull_requests}
              open_pull_requests={detail.open_pull_requests}
              merged_pull_requests={detail.merged_pull_requests}
            />

            <PullRequestsSection pullRequests={pullRequests} />

            <RepositorySearch
              repositoryId={repositoryId}
              branch={selectedBranch ?? detail.selected_branch}
            />

            <div>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-semibold">
                  Explore Analysis
                  {selectedBranch ? (
                    <span className="ml-2 text-base font-normal text-muted-foreground">
                      — {selectedBranch}
                    </span>
                  ) : null}
                </h2>
                <Link
                  href={`/repositories/${repositoryId}/chat${
                    selectedBranch ? `?branch=${encodeURIComponent(selectedBranch)}` : ""
                  }`}
                  className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-background px-5 py-2.5 text-sm font-medium text-violet-700 transition hover:bg-violet-50 dark:border-violet-900 dark:text-violet-200 dark:hover:bg-violet-950/30"
                >
                  <MessageSquare className="size-4" />
                  AI Chat
                </Link>
                <Link
                  href={`/repositories/${repositoryId}/graph${
                    selectedBranch ? `?branch=${encodeURIComponent(selectedBranch)}` : ""
                  }`}
                  className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-600 via-indigo-600 to-sky-500 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-violet-200/60 transition hover:brightness-110"
                >
                  <GitGraph className="size-4" />
                  View Structure Graph
                </Link>
              </div>
              <RepositoryDetailTabs
                files={detail.files}
                symbols={detail.symbols}
                dependencies={detail.dependencies}
              />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
