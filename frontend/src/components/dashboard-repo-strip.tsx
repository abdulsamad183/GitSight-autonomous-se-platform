"use client";

import Link from "next/link";
import { useState } from "react";
import {
  CheckCircle2,
  Clock3,
  FileCode2,
  GitBranch,
  GitPullRequest,
  Loader2,
  RefreshCw,
  Trash2,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import {
  useClearAllRepositories,
  useDeleteRepository,
} from "@/hooks/use-repositories";
import { refreshRepository } from "@/services/repositories";
import type { AnalyzeResponse, RepositoryListItem } from "@/types/repository";

interface DashboardRepoStripProps {
  repositories: RepositoryListItem[];
  isLoading: boolean;
  activeJobRepositoryId?: string | null;
  onRefreshStarted?: (result: AnalyzeResponse) => void;
}

function statusIcon(status: string, analysisStatus: string) {
  if (analysisStatus === "COMPLETED" || status === "active") {
    return <CheckCircle2 className="size-3.5 shrink-0 text-emerald-500" />;
  }
  if (analysisStatus === "FAILED" || status === "failed") {
    return <XCircle className="size-3.5 shrink-0 text-rose-500" />;
  }
  if (analysisStatus === "RUNNING" || analysisStatus === "PENDING") {
    return <Loader2 className="size-3.5 shrink-0 animate-spin text-sky-500" />;
  }
  return <Clock3 className="size-3.5 shrink-0 text-amber-500" />;
}

const REPO_STAT_BUBBLES = [
  {
    key: "branches",
    icon: GitBranch,
    getValue: (repo: RepositoryListItem) => repo.branches_count,
    label: "branches",
    bubbleClass:
      "bg-gradient-to-br from-sky-100 to-sky-50 text-sky-800 ring-sky-200/80 shadow-sky-100",
    iconClass: "text-sky-600",
  },
  {
    key: "files",
    icon: FileCode2,
    getValue: (repo: RepositoryListItem) => repo.files_count,
    label: "files",
    bubbleClass:
      "bg-gradient-to-br from-violet-100 to-violet-50 text-violet-800 ring-violet-200/80 shadow-violet-100",
    iconClass: "text-violet-600",
  },
  {
    key: "prs",
    icon: GitPullRequest,
    getValue: (repo: RepositoryListItem) => repo.open_pull_requests,
    label: "PRs",
    bubbleClass:
      "bg-gradient-to-br from-fuchsia-100 to-fuchsia-50 text-fuchsia-800 ring-fuchsia-200/80 shadow-fuchsia-100",
    iconClass: "text-fuchsia-600",
  },
] as const;

function RepoStatBubbles({ repo }: { repo: RepositoryListItem }) {
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {REPO_STAT_BUBBLES.map((stat) => {
        const Icon = stat.icon;
        const value = stat.getValue(repo);

        return (
          <span
            key={stat.key}
            title={`${value} ${stat.label}`}
            className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-semibold shadow-sm ring-1 ${stat.bubbleClass}`}
          >
            <Icon className={`size-3 shrink-0 ${stat.iconClass}`} />
            <span className="tabular-nums">{value}</span>
            <span className="font-medium opacity-75">{stat.label}</span>
          </span>
        );
      })}
    </div>
  );
}

export function DashboardRepoStrip({
  repositories,
  isLoading,
  activeJobRepositoryId,
  onRefreshStarted,
}: DashboardRepoStripProps) {
  const deleteMutation = useDeleteRepository();
  const clearAllMutation = useClearAllRepositories();
  const [refreshingId, setRefreshingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRefresh = async (repositoryId: string, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setRefreshingId(repositoryId);
    setError(null);
    try {
      const result = await refreshRepository(repositoryId);
      onRefreshStarted?.(result);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to refresh repository");
    } finally {
      setRefreshingId(null);
    }
  };

  const handleDelete = async (
    repositoryId: string,
    name: string,
    event: React.MouseEvent,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    if (!window.confirm(`Delete "${name}" and all its analysis data?`)) return;
    setError(null);
    try {
      await deleteMutation.mutateAsync(repositoryId);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to delete repository");
    }
  };

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-white/60 bg-white/50 lg:w-72">
      <div className="shrink-0 border-b border-white/60 px-3 py-3">
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Repositories
            </h2>
            <p className="text-sm font-semibold text-slate-900">{repositories.length} analyzed</p>
          </div>
          {repositories.length > 0 && (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => {
                if (
                  !window.confirm(
                    `Clear all ${repositories.length} analyzed repositories? All analysis data will be permanently deleted.`,
                  )
                ) {
                  return;
                }
                void clearAllMutation.mutateAsync();
              }}
              disabled={clearAllMutation.isPending}
              className="shrink-0 text-rose-600 hover:text-rose-700"
              aria-label="Clear all repositories"
            >
              {clearAllMutation.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Trash2 className="size-4" />
              )}
            </Button>
          )}
        </div>
      </div>

      {error && (
        <p className="shrink-0 border-b border-rose-100 bg-rose-50 px-3 py-2 text-xs text-rose-600">
          {error}
        </p>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {isLoading && (
          <div className="flex items-center gap-2 px-2 py-4 text-sm text-slate-500">
            <Loader2 className="size-4 animate-spin text-violet-600" />
            Loading...
          </div>
        )}

        {!isLoading && repositories.length === 0 && (
          <p className="px-2 py-4 text-xs leading-relaxed text-slate-500">
            No repositories yet. Paste a GitHub URL below to analyze one.
          </p>
        )}

        {!isLoading && repositories.length > 0 && (
          <ul className="space-y-2">
            {repositories.map((repo) => {
              const displayName = `${repo.owner}/${repo.repository_name}`;
              const isActive = activeJobRepositoryId === repo.id;
              const isRefreshing = refreshingId === repo.id;
              const isDeleting = deleteMutation.isPending && deleteMutation.variables === repo.id;

              return (
                <li key={repo.id}>
                  <Link
                    href={`/repositories/${repo.id}`}
                    data-active={isActive}
                    className="group block rounded-lg border border-transparent bg-white/80 p-2.5 shadow-sm transition hover:border-violet-200 hover:bg-white data-[active=true]:border-violet-400 data-[active=true]:bg-violet-50/80 data-[active=true]:ring-1 data-[active=true]:ring-violet-200"
                  >
                    <div className="flex items-start gap-2">
                      {statusIcon(repo.status, repo.analysis_status)}
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-slate-900">{displayName}</p>
                        <RepoStatBubbles repo={repo} />
                      </div>
                    </div>
                    <div className="mt-2 flex items-center gap-1 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100">
                      <button
                        type="button"
                        onClick={(e) => void handleRefresh(repo.id, e)}
                        disabled={isRefreshing || isDeleting || isActive}
                        className="rounded p-1 text-slate-500 hover:bg-indigo-50 hover:text-indigo-600"
                        aria-label={`Refresh ${displayName}`}
                      >
                        {isRefreshing ? (
                          <Loader2 className="size-3.5 animate-spin" />
                        ) : (
                          <RefreshCw className="size-3.5" />
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={(e) => void handleDelete(repo.id, displayName, e)}
                        disabled={isDeleting || isRefreshing}
                        className="rounded p-1 text-slate-500 hover:bg-rose-50 hover:text-rose-600"
                        aria-label={`Delete ${displayName}`}
                      >
                        {isDeleting ? (
                          <Loader2 className="size-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="size-3.5" />
                        )}
                      </button>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
