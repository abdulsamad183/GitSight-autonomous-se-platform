"use client";

import Link from "next/link";
import { useState } from "react";
import {
  CheckCircle2,
  Clock3,
  ExternalLink,
  FolderGit2,
  Loader2,
  RefreshCw,
  Trash2,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import { clearAllRepositories, deleteRepository, refreshRepository } from "@/services/repositories";
import type { AnalyzeResponse, RepositoryListItem } from "@/types/repository";

interface AnalyzedRepositoriesProps {
  repositories: RepositoryListItem[];
  isLoading: boolean;
  onSelect?: (repositoryId: string) => void;
  onChanged?: () => void;
  onRefreshStarted?: (result: AnalyzeResponse) => void;
  activeJobRepositoryId?: string | null;
}

function statusIcon(status: string, analysisStatus: string) {
  if (analysisStatus === "COMPLETED" || status === "active") {
    return <CheckCircle2 className="size-4 text-emerald-500" />;
  }
  if (analysisStatus === "FAILED" || status === "failed") {
    return <XCircle className="size-4 text-rose-500" />;
  }
  if (analysisStatus === "RUNNING" || analysisStatus === "PENDING") {
    return <Loader2 className="size-4 animate-spin text-sky-500" />;
  }
  return <Clock3 className="size-4 text-amber-500" />;
}

function isJobActive(analysisStatus: string) {
  return analysisStatus === "RUNNING" || analysisStatus === "PENDING";
}

export function AnalyzedRepositories({
  repositories,
  isLoading,
  onSelect,
  onChanged,
  onRefreshStarted,
  activeJobRepositoryId,
}: AnalyzedRepositoriesProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [refreshingId, setRefreshingId] = useState<string | null>(null);
  const [clearingAll, setClearingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRefresh = async (repositoryId: string) => {
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

  const handleDelete = async (repositoryId: string, name: string) => {
    if (!window.confirm(`Delete "${name}" and all its analysis data? This cannot be undone.`)) {
      return;
    }

    setDeletingId(repositoryId);
    setError(null);
    try {
      await deleteRepository(repositoryId);
      onChanged?.();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to delete repository");
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (repositories.length === 0) return;
    if (
      !window.confirm(
        `Clear all ${repositories.length} analyzed repositories? All analysis data will be permanently deleted.`,
      )
    ) {
      return;
    }

    setClearingAll(true);
    setError(null);
    try {
      await clearAllRepositories();
      onChanged?.();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to clear repositories");
    } finally {
      setClearingAll(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading analyzed repos...
      </div>
    );
  }

  if (repositories.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-violet-300/60 bg-violet-50/50 p-6 text-center dark:border-violet-500/30 dark:bg-violet-950/20">
        <FolderGit2 className="mx-auto size-8 text-violet-500" />
        <p className="mt-2 text-sm font-medium">No analyzed repos yet</p>
        <p className="text-xs text-muted-foreground">
          Analyze a GitHub URL and it will appear here for quick access.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-end">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleClearAll}
          disabled={clearingAll || deletingId !== null || refreshingId !== null}
          className="border-rose-200 text-rose-600 hover:bg-rose-50 hover:text-rose-700 dark:border-rose-900 dark:text-rose-400 dark:hover:bg-rose-950/40"
        >
          {clearingAll ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Trash2 className="size-4" />
          )}
          <span className="ml-2">Clear all</span>
        </Button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {repositories.map((repo) => {
        const displayName = `${repo.owner}/${repo.repository_name}`;
        const isDeleting = deletingId === repo.id;
        const isRefreshing = refreshingId === repo.id;
        const jobActive =
          isJobActive(repo.analysis_status) || activeJobRepositoryId === repo.id;

        return (
          <div
            key={repo.id}
            className="group flex items-center gap-2 rounded-xl border border-transparent bg-gradient-to-r from-slate-50 to-violet-50 p-4 transition hover:border-violet-200 hover:shadow-md dark:from-slate-900 dark:to-violet-950/40 dark:hover:border-violet-800"
          >
            <Link
              href={`/repositories/${repo.id}`}
              onClick={() => onSelect?.(repo.id)}
              className="min-w-0 flex-1"
            >
              <div className="flex items-center gap-2">
                {statusIcon(repo.status, repo.analysis_status)}
                <p className="truncate font-semibold text-foreground">{displayName}</p>
              </div>
              <p className="mt-1 truncate text-xs text-muted-foreground">{repo.github_url}</p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full bg-violet-100 px-2 py-0.5 font-medium text-violet-700 dark:bg-violet-900/50 dark:text-violet-200">
                  {repo.files_count} files
                </span>
                <span className="rounded-full bg-sky-100 px-2 py-0.5 font-medium text-sky-700 dark:bg-sky-900/50 dark:text-sky-200">
                  {repo.analysis_status}
                </span>
                {repo.branches_count > 0 && (
                  <span className="rounded-full bg-indigo-100 px-2 py-0.5 font-medium text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-200">
                    {repo.branches_count} branch{repo.branches_count === 1 ? "" : "es"}
                  </span>
                )}
              </div>
            </Link>

            <div className="flex shrink-0 items-center gap-1">
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                disabled={jobActive || isDeleting || clearingAll || isRefreshing}
                onClick={() => void handleRefresh(repo.id)}
                className="text-indigo-600 opacity-0 transition hover:bg-indigo-50 hover:text-indigo-700 group-hover:opacity-100 dark:text-indigo-400 dark:hover:bg-indigo-950/40"
                aria-label={`Refresh ${displayName}`}
                title="Check GitHub for new commits"
              >
                {isRefreshing ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <RefreshCw className="size-4" />
                )}
              </Button>
              <Link
                href={`/repositories/${repo.id}`}
                className="rounded-lg p-2 text-muted-foreground opacity-0 transition hover:bg-white/60 hover:text-foreground group-hover:opacity-100 dark:hover:bg-white/10"
                aria-label={`Open ${displayName}`}
              >
                <ExternalLink className="size-4" />
              </Link>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                disabled={isDeleting || clearingAll || isRefreshing}
                onClick={() => void handleDelete(repo.id, displayName)}
                className="text-rose-500 opacity-0 transition hover:bg-rose-50 hover:text-rose-600 group-hover:opacity-100 dark:hover:bg-rose-950/40"
                aria-label={`Delete ${displayName}`}
              >
                {isDeleting ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Trash2 className="size-4" />
                )}
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
