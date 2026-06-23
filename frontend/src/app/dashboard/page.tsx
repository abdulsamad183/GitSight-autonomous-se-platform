"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { FolderGit2, GitBranch, Sparkles } from "lucide-react";

import { AnalyzedRepositories } from "@/components/analyzed-repositories";
import { JobProgressCard } from "@/components/job-progress-card";
import { RepositoryUrlForm } from "@/components/repository-url-form";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useJobPolling } from "@/hooks/use-job-polling";
import { useAuth } from "@/hooks/use-auth";
import { listRepositories } from "@/services/repositories";
import type { AnalyzeResponse, RepositoryListItem } from "@/types/repository";

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [analyzedRepos, setAnalyzedRepos] = useState<RepositoryListItem[]>([]);
  const [reposLoading, setReposLoading] = useState(true);
  const [activeJob, setActiveJob] = useState<{
    result: AnalyzeResponse;
    cached: boolean;
    isRefresh: boolean;
  } | null>(null);

  const loadRepos = useCallback(async () => {
    try {
      const data = await listRepositories();
      setAnalyzedRepos(data);
    } catch {
      setAnalyzedRepos([]);
    } finally {
      setReposLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const data = await listRepositories();
        if (!cancelled) {
          setAnalyzedRepos(data);
        }
      } catch {
        if (!cancelled) {
          setAnalyzedRepos([]);
        }
      } finally {
        if (!cancelled) {
          setReposLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const shouldPoll = activeJob?.result.job_id && !activeJob.cached;
  const { job, error: pollError, isPolling } = useJobPolling(
    shouldPoll ? activeJob.result.job_id : null,
    { onTerminal: loadRepos },
  );

  const stats = useMemo(() => {
    const totalBranches = analyzedRepos.reduce((sum, repo) => sum + repo.branches_count, 0);
    return {
      repoCount: analyzedRepos.length,
      branchCount: totalBranches,
    };
  }, [analyzedRepos]);

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
    await logout();
    router.push("/login");
  };

  const showProgress =
    activeJob &&
    (activeJob.cached ||
      job ||
      isPolling ||
      (activeJob.result.job_id && !activeJob.cached));

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50/80 via-background to-sky-50/50 dark:from-violet-950/30 dark:via-background dark:to-sky-950/20">
      <header className="border-b bg-background/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="bg-gradient-to-r from-violet-600 to-sky-600 bg-clip-text text-xl font-bold text-transparent">
            GitSight
          </span>
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground">
              Home
            </Link>
            <Button variant="outline" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome back, {user?.username}
          </h1>
          <p className="mt-2 text-muted-foreground">
            Analyze repositories, track live progress, and refresh when branches change on GitHub.
          </p>
        </div>

        {!reposLoading && analyzedRepos.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex items-center gap-3 rounded-xl border bg-background/60 px-4 py-3 backdrop-blur">
              <FolderGit2 className="size-5 text-violet-500" />
              <div>
                <p className="text-2xl font-bold">{stats.repoCount}</p>
                <p className="text-xs text-muted-foreground">Analyzed repos</p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-xl border bg-background/60 px-4 py-3 backdrop-blur">
              <GitBranch className="size-5 text-indigo-500" />
              <div>
                <p className="text-2xl font-bold">{stats.branchCount}</p>
                <p className="text-xs text-muted-foreground">Branches tracked</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid gap-8 lg:grid-cols-5">
          <Card className="overflow-hidden border-violet-200 lg:col-span-3 dark:border-violet-900">
            <div className="h-1 bg-gradient-to-r from-violet-500 via-indigo-500 to-sky-500" />
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="size-5 text-violet-500" />
                Analyze Repository
              </CardTitle>
              <CardDescription>
                Paste a public GitHub URL. All branches (up to 10) will be analyzed and stored.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RepositoryUrlForm onAnalyzeStarted={handleAnalyzeStarted} />

              {showProgress && activeJob.cached && (
                <JobProgressCard
                  job={{
                    id: activeJob.result.job_id ?? "",
                    status: "COMPLETED",
                    progress: 100,
                    current_stage: "Loaded from database",
                    error_message: null,
                    events: [],
                  }}
                  repositoryId={activeJob.result.repository_id}
                  pollError={null}
                  cached
                  compact
                />
              )}

              {showProgress && !activeJob.cached && job && (
                <JobProgressCard
                  job={job}
                  repositoryId={activeJob.result.repository_id}
                  pollError={pollError}
                  compact
                  isRefresh={activeJob.isRefresh}
                />
              )}

              {showProgress && !activeJob.cached && !job && isPolling && (
                <div className="mt-6 rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
                  Starting {activeJob.isRefresh ? "refresh" : "analysis"} job...
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderGit2 className="size-5 text-indigo-500" />
                Analyzed Repos
              </CardTitle>
              <CardDescription>
                Open saved analysis or refresh to pick up new commits on any branch.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AnalyzedRepositories
                repositories={analyzedRepos}
                isLoading={reposLoading}
                onChanged={() => {
                  setReposLoading(true);
                  void loadRepos();
                }}
                onRefreshStarted={handleRefreshStarted}
                activeJobRepositoryId={
                  activeJob && !activeJob.cached ? activeJob.result.repository_id : null
                }
              />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
