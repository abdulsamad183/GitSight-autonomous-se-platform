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

function formatLastActive(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
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
      <div className="flex items-center gap-2 rounded-2xl border border-violet-100 bg-white/70 p-5 text-sm text-slate-500">
        <Loader2 className="size-4 animate-spin text-violet-600" />
        Loading analyzed repos...
      </div>
    );
  }

  if (repositories.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-violet-200 bg-white/70 p-8 text-center">
        <FolderGit2 className="mx-auto size-9 text-violet-600" />
        <p className="mt-3 text-sm font-semibold text-slate-950">No analyzed repos yet</p>
        <p className="text-xs text-slate-500">
          Analyze a GitHub URL and it will appear here for quick access.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="hidden grid-cols-[minmax(0,1.6fr)_0.8fr_0.6fr_0.6fr_0.8fr_auto] gap-4 px-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 lg:grid">
          <span>Repo Name</span>
          <span>Status</span>
          <span>Branches</span>
          <span>PRs</span>
          <span>Last Active</span>
          <span />
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleClearAll}
          disabled={clearingAll || deletingId !== null || refreshingId !== null}
          className="ml-auto border-rose-200 bg-rose-50 text-rose-600 hover:bg-rose-100 hover:text-rose-700"
        >
          {clearingAll ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Trash2 className="size-4" />
          )}
          <span className="ml-2">Clear all</span>
        </Button>
      </div>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      <div className="max-h-[520px] space-y-3 overflow-y-auto pr-2">
        {repositories.map((repo) => {
          const displayName = `${repo.owner}/${repo.repository_name}`;
          const isDeleting = deletingId === repo.id;
          const isRefreshing = refreshingId === repo.id;
          const jobActive =
            isJobActive(repo.analysis_status) || activeJobRepositoryId === repo.id;

          return (
            <div
              key={repo.id}
              className="group relative grid gap-4 overflow-hidden rounded-2xl border border-white/80 bg-white/75 p-4 shadow-lg shadow-slate-200/70 transition hover:border-violet-200 hover:bg-white hover:shadow-violet-100/80 lg:grid-cols-[minmax(0,1.6fr)_0.8fr_0.6fr_0.6fr_0.8fr_auto] lg:items-center"
            >
              <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-violet-400 via-fuchsia-400 to-sky-400 opacity-0 transition group-hover:opacity-100" />
              <Link
                href={`/repositories/${repo.id}`}
                onClick={() => onSelect?.(repo.id)}
                className="min-w-0 flex-1"
              >
                <div className="flex items-center gap-2">
                  {statusIcon(repo.status, repo.analysis_status)}
                  <p className="truncate font-semibold text-slate-950">{displayName}</p>
                </div>
                <p className="mt-1 truncate text-xs text-slate-500">{repo.github_url}</p>
              </Link>

              <div className="flex flex-wrap gap-2 text-xs">
                <span className="rounded-full bg-emerald-50 px-2.5 py-1 font-semibold text-emerald-700 ring-1 ring-emerald-200">
                  {repo.analysis_status}
                </span>
                <span className="rounded-full bg-violet-50 px-2.5 py-1 font-semibold text-violet-700 ring-1 ring-violet-200">
                  {repo.files_count} files
                </span>
              </div>

              <div className="text-sm text-slate-800">
                <span className="font-semibold">{repo.branches_count}</span>
                <span className="ml-1 text-xs text-slate-500">
                  branch{repo.branches_count === 1 ? "" : "es"}
                </span>
              </div>

              <div className="text-sm text-slate-800">
                <span className="font-semibold">{repo.total_pull_requests}</span>
                <span className="ml-1 text-xs text-slate-500">PRs</span>
                <p className="mt-1 text-xs text-emerald-600">
                  {repo.open_pull_requests} open / {repo.merged_pull_requests} merged
                </p>
              </div>

              <div className="text-xs text-slate-400">{formatLastActive(repo.updated_at)}</div>

              <div className="flex shrink-0 items-center gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  disabled={jobActive || isDeleting || clearingAll || isRefreshing}
                  onClick={() => void handleRefresh(repo.id)}
                  className="bg-indigo-50 text-indigo-600 opacity-100 transition hover:bg-indigo-100 hover:text-indigo-700"
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
                  className="rounded-lg bg-slate-50 p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-950"
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
                  className="bg-rose-50 text-rose-500 opacity-100 transition hover:bg-rose-100 hover:text-rose-600"
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
    </div>
  );
}
