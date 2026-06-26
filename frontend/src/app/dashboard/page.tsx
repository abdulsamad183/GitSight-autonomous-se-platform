"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { DashboardAnalysisStage } from "@/components/dashboard-analysis-stage";
import { DashboardAnalyzeDock } from "@/components/dashboard-analyze-dock";
import { DashboardRepoStrip } from "@/components/dashboard-repo-strip";
import { Button } from "@/components/ui/button";
import { useJobPolling } from "@/hooks/use-job-polling";
import { useAuth } from "@/hooks/use-auth";
import { useRepositories } from "@/hooks/use-repositories";
import { queryKeys } from "@/lib/query-keys";
import { getQueryClient } from "@/lib/query-client";
import type { AnalyzeResponse } from "@/types/repository";

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const { data: analyzedRepos = [], isLoading: reposLoading } = useRepositories();
  const [activeJob, setActiveJob] = useState<{
    result: AnalyzeResponse;
    cached: boolean;
    isRefresh: boolean;
  } | null>(null);

  const refreshRepos = useCallback(() => {
    void getQueryClient().invalidateQueries({ queryKey: queryKeys.repositories });
  }, []);

  const shouldPoll = activeJob?.result.job_id && !activeJob.cached;
  const { job, error: pollError, isPolling } = useJobPolling(
    shouldPoll ? activeJob.result.job_id : null,
    { onTerminal: refreshRepos },
  );

  const handleJobStarted = (result: AnalyzeResponse, isRefresh = false) => {
    if (result.cached) {
      setActiveJob({ result, cached: true, isRefresh: false });
      router.push(`/repositories/${result.repository_id}`);
      return;
    }
    setActiveJob({ result, cached: false, isRefresh });
  };

  const handleAnalyzeStarted = (result: AnalyzeResponse) => {
    handleJobStarted(result, false);
  };

  const handleRefreshStarted = (result: AnalyzeResponse) => {
    handleJobStarted(result, true);
  };

  const handleLogout = async () => {
    router.replace("/");
    await logout();
  };

  const showReposLoading = reposLoading && analyzedRepos.length === 0;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-gradient-to-br from-violet-50 via-white to-sky-50 text-slate-950">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-[-15%] top-[-20%] size-[520px] rounded-full bg-violet-300/40 blur-3xl" />
        <div className="absolute right-[-10%] top-[10%] size-[420px] rounded-full bg-sky-300/30 blur-3xl" />
      </div>

      <header className="shrink-0 border-b border-white/70 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-end px-6 py-3">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm text-slate-500 transition hover:text-slate-950">
              Home
            </Link>
            <Button
              variant="outline"
              onClick={handleLogout}
              className="border-violet-200 bg-white/70 text-slate-700 hover:bg-violet-50"
            >
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <DashboardRepoStrip
          repositories={analyzedRepos}
          isLoading={showReposLoading}
          activeJobRepositoryId={
            activeJob && !activeJob.cached ? activeJob.result.repository_id : null
          }
          onRefreshStarted={handleRefreshStarted}
        />

        <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <div className="mx-auto flex h-full w-full max-w-3xl flex-col px-4 sm:px-6">
            <div className="flex min-h-0 flex-1 flex-col items-center justify-center">
              <DashboardAnalysisStage
                username={user?.username}
                activeJob={activeJob}
                job={job}
                pollError={pollError}
                isPolling={isPolling}
              />
            </div>
            <div className="shrink-0 pb-5 pt-2">
              <DashboardAnalyzeDock onAnalyzeStarted={handleAnalyzeStarted} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
