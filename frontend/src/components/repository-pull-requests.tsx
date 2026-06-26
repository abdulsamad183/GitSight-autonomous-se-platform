"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Download, ExternalLink, Loader2, RefreshCw } from "lucide-react";
import { useCallback, useState } from "react";

import { MarkdownViewer } from "@/components/markdown-viewer";
import { Button } from "@/components/ui/button";
import { queryKeys } from "@/lib/query-keys";
import {
  getPullRequestReview,
  listPullRequests,
  regeneratePullRequestReview,
} from "@/services/repositories";
import type { PullRequestReviewResponse } from "@/types/pr-review";
import type { PullRequestListItem } from "@/types/repository";

interface RepositoryPullRequestsProps {
  repositoryId: string;
}

const STATE_STYLES: Record<PullRequestListItem["state"], string> = {
  OPEN: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200",
  CLOSED: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
  MERGED: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-200",
};

function formatDate(value: string | null): string {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatGeneratedAt(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function RepositoryPullRequests({ repositoryId }: RepositoryPullRequestsProps) {
  const queryClient = useQueryClient();
  const [selectedPullRequestId, setSelectedPullRequestId] = useState<string | null>(null);
  const [activeReview, setActiveReview] = useState<PullRequestReviewResponse | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const listQuery = useQuery({
    queryKey: queryKeys.repositoryPullRequests(repositoryId),
    queryFn: () => listPullRequests(repositoryId),
  });

  const reviewMutation = useMutation({
    mutationFn: (pullRequestId: string) => getPullRequestReview(repositoryId, pullRequestId),
    onSuccess: (data, pullRequestId) => {
      setActiveReview(data);
      setActionError(null);
      void queryClient.setQueryData(
        queryKeys.repositoryPullRequestReview(repositoryId, pullRequestId),
        data,
      );
    },
    onError: (error: Error) => {
      setActiveReview(null);
      setActionError(error.message);
    },
  });

  const regenerateMutation = useMutation({
    mutationFn: (pullRequestId: string) =>
      regeneratePullRequestReview(repositoryId, pullRequestId),
    onSuccess: (data) => {
      setActiveReview(data);
      void queryClient.setQueryData(
        queryKeys.repositoryPullRequestReview(repositoryId, data.pull_request_id),
        data,
      );
      setActionError(null);
    },
    onError: (error: Error) => {
      setActionError(error.message);
    },
  });

  const handleSelectReview = (pullRequest: PullRequestListItem) => {
    if (!pullRequest.id) {
      setActionError("This pull request is missing an id. Refresh the page and try again.");
      return;
    }

    setSelectedPullRequestId(pullRequest.id);
    setActionError(null);

    const cached = queryClient.getQueryData<PullRequestReviewResponse>(
      queryKeys.repositoryPullRequestReview(repositoryId, pullRequest.id),
    );
    if (cached) {
      setActiveReview(cached);
      return;
    }

    setActiveReview(null);
    reviewMutation.mutate(pullRequest.id);
  };

  const handleCopy = useCallback(async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
    } catch {
      setActionError("Failed to copy to clipboard");
    }
  }, []);

  const handleDownload = useCallback((review: PullRequestReviewResponse) => {
    const blob = new Blob([review.content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `pr-review-${review.title.replace(/[^\w.-]+/g, "-").slice(0, 80)}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }, []);

  const pullRequests = listQuery.data ?? [];
  const isLoadingReview = reviewMutation.isPending || regenerateMutation.isPending;
  const selectedPullRequest = pullRequests.find((pr) => pr.id === selectedPullRequestId);
  const loadingPullRequestId = reviewMutation.isPending ? reviewMutation.variables : null;

  return (
    <div className="grid h-full min-h-[24rem] grid-cols-1 grid-rows-2 gap-4 lg:grid-cols-2 lg:grid-rows-1">
      {/* Left: PR list */}
      <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="shrink-0 border-b px-4 py-3">
          <h2 className="text-sm font-semibold">Pull Requests</h2>
          <p className="text-xs text-muted-foreground">
            {pullRequests.length} synchronized
          </p>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {listQuery.isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-6 animate-spin text-violet-500" />
            </div>
          )}

          {listQuery.error instanceof Error && (
            <p className="p-4 text-sm text-rose-600">{listQuery.error.message}</p>
          )}

          {!listQuery.isLoading && !listQuery.error && pullRequests.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">
              No pull requests have been synchronized for this repository yet.
            </p>
          )}

          {!listQuery.isLoading && pullRequests.length > 0 && (
            <div className="divide-y">
              {pullRequests.map((pullRequest) => {
                const isSelected = selectedPullRequestId === pullRequest.id;
                const isLoadingThis =
                  reviewMutation.isPending && loadingPullRequestId === pullRequest.id;

                return (
                  <button
                    key={pullRequest.id}
                    type="button"
                    data-selected={isSelected}
                    onClick={() => handleSelectReview(pullRequest)}
                    className="w-full px-4 py-3 text-left transition hover:bg-muted/40 data-[selected=true]:bg-violet-50/70 data-[selected=true]:ring-1 data-[selected=true]:ring-inset data-[selected=true]:ring-violet-300 dark:data-[selected=true]:bg-violet-950/30 dark:data-[selected=true]:ring-violet-800"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs text-muted-foreground">
                        #{pullRequest.number}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          STATE_STYLES[pullRequest.state]
                        }`}
                      >
                        {pullRequest.state}
                      </span>
                      {pullRequest.is_draft && (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700 dark:bg-amber-900/40 dark:text-amber-200">
                          DRAFT
                        </span>
                      )}
                      {isLoadingThis && (
                        <Loader2 className="size-3.5 animate-spin text-violet-500" />
                      )}
                    </div>
                    <div className="mt-1 flex min-w-0 items-center gap-2">
                      <p className="line-clamp-2 text-sm font-medium">{pullRequest.title}</p>
                      {pullRequest.html_url && (
                        <a
                          href={pullRequest.html_url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(event) => event.stopPropagation()}
                          className="shrink-0 text-muted-foreground transition hover:text-foreground"
                          aria-label={`Open pull request #${pullRequest.number} on GitHub`}
                        >
                          <ExternalLink className="size-3.5" />
                        </a>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {pullRequest.author} · {pullRequest.source_branch ?? "unknown"} →{" "}
                      {pullRequest.target_branch ?? "unknown"}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {formatDate(pullRequest.github_created_at)}
                      {pullRequest.changed_files_count !== null &&
                        pullRequest.changed_files_count !== undefined && (
                          <> · {pullRequest.changed_files_count} file(s)</>
                        )}
                    </p>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Right: Review panel */}
      <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="shrink-0 border-b px-4 py-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="text-sm font-semibold">
                {selectedPullRequest
                  ? `#${selectedPullRequest.number} ${selectedPullRequest.title}`
                  : "AI Review"}
              </h2>
              {activeReview ? (
                <p className="text-xs text-muted-foreground">
                  Generated {formatGeneratedAt(activeReview.generated_at)}
                </p>
              ) : (
                <p className="text-xs text-muted-foreground">
                  Select a pull request to view or generate a review
                </p>
              )}
            </div>
            {selectedPullRequestId && (
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={!activeReview}
                  onClick={() => activeReview && void handleCopy(activeReview.content)}
                >
                  <Copy className="mr-1.5 size-3.5" />
                  Copy
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={!activeReview}
                  onClick={() => activeReview && handleDownload(activeReview)}
                >
                  <Download className="mr-1.5 size-3.5" />
                  Download
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={regenerateMutation.isPending}
                  onClick={() => regenerateMutation.mutate(selectedPullRequestId)}
                >
                  {regenerateMutation.isPending ? (
                    <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-1.5 size-3.5" />
                  )}
                  Regenerate
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
          {!selectedPullRequestId && (
            <div className="flex h-full min-h-[12rem] flex-col items-center justify-center gap-2 text-center">
              <p className="text-sm font-medium text-muted-foreground">No pull request selected</p>
              <p className="max-w-xs text-xs text-muted-foreground">
                Choose a pull request from the list to generate or view its AI code review.
              </p>
            </div>
          )}

          {selectedPullRequestId && (
            <>
              {actionError && (
                <p className="mb-4 text-sm text-rose-600 dark:text-rose-400">{actionError}</p>
              )}
              {isLoadingReview && !activeReview && (
                <div className="flex h-full min-h-[12rem] flex-col items-center justify-center gap-3">
                  <Loader2 className="size-6 animate-spin text-violet-500" />
                  <p className="text-sm text-muted-foreground">
                    Generating AI review. This may take a moment…
                  </p>
                </div>
              )}
              {!isLoadingReview && !activeReview && !actionError && (
                <p className="text-sm text-muted-foreground">No review content available.</p>
              )}
              {activeReview && <MarkdownViewer content={activeReview.content} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
