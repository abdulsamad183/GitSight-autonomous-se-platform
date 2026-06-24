"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";

import { BranchSelector } from "@/components/branch-selector";
import { JobProgressCard } from "@/components/job-progress-card";
import { PullRequestsSection } from "@/components/pull-requests-section";
import { RepositoryDetailTabs } from "@/components/repository-detail-tabs";
import { RepositoryHero, RepositoryStatsGrid } from "@/components/repository-stats";
import { Button, buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useJobPolling } from "@/hooks/use-job-polling";
import {
  getRepositoryDetails,
  listBranches,
  listPullRequests,
  refreshRepository,
} from "@/services/repositories";
import type {
  AnalyzeResponse,
  BranchSummary,
  PullRequestListItem,
  RepositoryDetail,
} from "@/types/repository";

export default function RepositoryDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [branches, setBranches] = useState<BranchSummary[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null);
  const [detail, setDetail] = useState<RepositoryDetail | null>(null);
  const [pullRequests, setPullRequests] = useState<PullRequestListItem[]>([]);
  const [refreshJob, setRefreshJob] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  const loadDetail = useCallback(
    async (branch?: string) => {
      if (!params.id) return;
      setLoading(true);
      try {
        const [data, pullRequestList] = await Promise.all([
          getRepositoryDetails(params.id, branch),
          listPullRequests(params.id),
        ]);
        setDetail(data);
        setPullRequests(pullRequestList);
        setSelectedBranch(data.selected_branch ?? branch ?? null);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load repository");
      } finally {
        setLoading(false);
      }
    },
    [params.id],
  );

  const reloadCurrentBranch = useCallback(() => {
    void loadDetail(selectedBranch ?? undefined);
  }, [loadDetail, selectedBranch]);

  const shouldPollRefresh = refreshJob?.job_id && !refreshJob.cached;
  const {
    job: polledRefreshJob,
    error: pollError,
    isPolling,
  } = useJobPolling(shouldPollRefresh ? refreshJob.job_id : null, {
    onTerminal: reloadCurrentBranch,
  });

  useEffect(() => {
    if (!params.id || authLoading || !isAuthenticated) return;

    const load = async () => {
      try {
        const branchList = await listBranches(params.id);
        setBranches(branchList);
        const defaultBranch = branchList[0]?.branch;
        await loadDetail(defaultBranch);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load repository");
        setLoading(false);
      }
    };

    void load();
  }, [params.id, authLoading, isAuthenticated, loadDetail]);

  const handleBranchSelect = (branch: string) => {
    setSelectedBranch(branch);
    void loadDetail(branch);
  };

  const handleRefresh = async () => {
    if (!params.id) return;
    setRefreshing(true);
    setRefreshError(null);
    try {
      const result = await refreshRepository(params.id);
      setRefreshJob(result);
    } catch (e) {
      setRefreshError(e instanceof Error ? e.message : "Failed to refresh repository");
    } finally {
      setRefreshing(false);
    }
  };

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
        {loading && !detail && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="size-8 animate-spin text-violet-500" />
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
            {error}
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
                repositoryId={refreshJob?.repository_id ?? params.id}
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

            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="size-6 animate-spin text-violet-500" />
              </div>
            ) : (
              <>
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

                <div>
                  <h2 className="mb-4 text-xl font-semibold">
                    Explore Analysis
                    {selectedBranch ? (
                      <span className="ml-2 text-base font-normal text-muted-foreground">
                        — {selectedBranch}
                      </span>
                    ) : null}
                  </h2>
                  <RepositoryDetailTabs
                    files={detail.files}
                    symbols={detail.symbols}
                    dependencies={detail.dependencies}
                  />
                </div>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
