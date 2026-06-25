"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useState } from "react";
import { Activity, FolderGit2, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";

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
import { useRepositories } from "@/hooks/use-repositories";
import { queryKeys } from "@/lib/query-keys";
import { getQueryClient } from "@/lib/query-client";
import type { AnalyzeResponse } from "@/types/repository";

interface MetricCardProps {
  label: string;
  value: number;
  icon: LucideIcon;
  tone: "violet" | "indigo";
}

function MetricCard({ label, value, icon: Icon, tone }: MetricCardProps) {
  const toneClasses =
    tone === "violet"
      ? "from-violet-500/15 via-fuchsia-500/10 to-transparent text-violet-600 ring-violet-200"
      : "from-sky-500/15 via-indigo-500/10 to-transparent text-sky-600 ring-sky-200";

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/70 bg-white/80 p-5 shadow-xl shadow-violet-100/70 backdrop-blur-xl">
      <div className={`absolute inset-0 bg-gradient-to-br ${toneClasses}`} />
      <div className="absolute -right-8 -top-8 size-24 rounded-full bg-white/80 blur-2xl" />
      <div className="relative flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{label}</p>
          <p className="mt-2 text-4xl font-bold tracking-tight text-slate-950">{value}</p>
        </div>
        <div className={`rounded-2xl bg-white/80 p-3 shadow-sm ring-1 ${toneClasses}`}>
          <Icon className="size-6" />
        </div>
      </div>
      <div className="relative mt-5 flex h-8 items-end gap-1 opacity-70">
        {[28, 42, 34, 58, 44, 68, 52, 78].map((height, index) => (
          <span
            key={index}
            className="flex-1 rounded-t-full bg-gradient-to-t from-violet-200 to-sky-300"
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    </div>
  );
}

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

  const stats = useMemo(() => {
    return {
      repoCount: analyzedRepos.length,
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

  const showReposLoading = reposLoading && analyzedRepos.length === 0;

  return (
    <div className="min-h-screen overflow-hidden bg-gradient-to-br from-violet-50 via-white to-sky-50 text-slate-950">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-[-15%] top-[-20%] size-[520px] rounded-full bg-violet-300/50 blur-3xl" />
        <div className="absolute right-[-10%] top-[10%] size-[420px] rounded-full bg-sky-300/40 blur-3xl" />
        <div className="absolute bottom-[-20%] left-[20%] size-[520px] rounded-full bg-fuchsia-200/40 blur-3xl" />
      </div>

      <header className="border-b border-white/70 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="bg-gradient-to-r from-violet-700 via-fuchsia-600 to-sky-600 bg-clip-text text-xl font-bold text-transparent">
            GitSight
          </span>
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm text-slate-500 transition hover:text-slate-950">
              Home
            </Link>
            <Button
              variant="outline"
              onClick={handleLogout}
              className="border-violet-200 bg-white/70 text-slate-700 hover:bg-violet-50 hover:text-slate-950"
            >
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-10">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-violet-600">
            Repository Intelligence
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-slate-950">
            Welcome back, {user?.username}
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Analyze repositories, track live progress, and refresh when branches change on GitHub.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-8">
            <Card className="relative overflow-hidden border-white/80 bg-white/80 shadow-2xl shadow-violet-100/80 backdrop-blur-xl">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-400/60 to-transparent" />
              <div className="absolute -right-20 -top-20 size-48 rounded-full bg-violet-200/60 blur-3xl" />
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-950">
                  <span className="rounded-xl bg-violet-100 p-2 text-violet-700 ring-1 ring-violet-200">
                    <Sparkles className="size-5" />
                  </span>
                  Analyze Repository
                </CardTitle>
                <CardDescription className="text-slate-600">
                  Paste a public GitHub URL. All branches (up to 10) will be analyzed and stored.
                </CardDescription>
              </CardHeader>
              <CardContent className="relative">
                <RepositoryUrlForm onAnalyzeStarted={handleAnalyzeStarted} />
              </CardContent>
            </Card>

            <Card className="border-white/80 bg-white/80 shadow-2xl shadow-slate-200/70 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-950">
                  <span className="rounded-xl bg-indigo-100 p-2 text-indigo-700 ring-1 ring-indigo-200">
                    <FolderGit2 className="size-5" />
                  </span>
                  Analyzed Repos
                </CardTitle>
                <CardDescription className="text-slate-600">
                  Open saved analysis or refresh to pick up new commits on any branch.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AnalyzedRepositories
                  repositories={analyzedRepos}
                  isLoading={showReposLoading}
                  onRefreshStarted={handleRefreshStarted}
                  activeJobRepositoryId={
                    activeJob && !activeJob.cached ? activeJob.result.repository_id : null
                  }
                />
              </CardContent>
            </Card>
          </div>

          <aside className="space-y-6 lg:sticky lg:top-6 lg:self-start">
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
              />
            )}

            {showProgress && !activeJob.cached && job && (
              <JobProgressCard
                job={job}
                repositoryId={activeJob.result.repository_id}
                pollError={pollError}
                isRefresh={activeJob.isRefresh}
              />
            )}

            {showProgress && !activeJob.cached && !job && isPolling && (
              <Card className="border-dashed">
                <CardContent className="p-4 text-sm text-muted-foreground">
                  Starting {activeJob.isRefresh ? "refresh" : "analysis"} job...
                </CardContent>
              </Card>
            )}

            {!showProgress && (
              <Card className="border-white/80 bg-white/80 shadow-2xl shadow-slate-200/70 backdrop-blur-xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base text-slate-950">
                    <span className="rounded-xl bg-sky-100 p-2 text-sky-700 ring-1 ring-sky-200">
                      <Activity className="size-4" />
                    </span>
                    Analysis Activity
                  </CardTitle>
                  <CardDescription className="text-slate-600">
                    Start an analysis or refresh a repository to watch job progress here.
                  </CardDescription>
                </CardHeader>
              </Card>
            )}

            {!showReposLoading && analyzedRepos.length > 0 && (
              <MetricCard
                label="Analyzed Repos"
                value={stats.repoCount}
                icon={FolderGit2}
                tone="indigo"
              />
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}
