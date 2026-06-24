"use client";

import { ExternalLink } from "lucide-react";

import type { PullRequestListItem } from "@/types/repository";

interface PullRequestsSectionProps {
  pullRequests: PullRequestListItem[];
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

export function PullRequestsSection({ pullRequests }: PullRequestsSectionProps) {
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Pull Requests</h2>
          <p className="text-sm text-muted-foreground">
            Stored PR metadata discovered during repository analysis.
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
        {pullRequests.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            No pull requests have been synchronized for this repository yet.
          </p>
        ) : (
          <div className="max-h-[420px] divide-y overflow-y-auto">
            {pullRequests.map((pullRequest) => (
              <div
                key={pullRequest.number}
                className="grid gap-3 px-4 py-3 hover:bg-muted/40 md:grid-cols-[minmax(0,1fr)_auto]"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-sm text-muted-foreground">
                      #{pullRequest.number}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                        STATE_STYLES[pullRequest.state]
                      }`}
                    >
                      {pullRequest.state}
                    </span>
                    {pullRequest.is_draft && (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-900/40 dark:text-amber-200">
                        DRAFT
                      </span>
                    )}
                  </div>
                  <div className="mt-1 flex min-w-0 items-center gap-2">
                    <p className="truncate font-medium">{pullRequest.title}</p>
                    {pullRequest.html_url && (
                      <a
                        href={pullRequest.html_url}
                        target="_blank"
                        rel="noreferrer"
                        className="shrink-0 text-muted-foreground transition hover:text-foreground"
                        aria-label={`Open pull request #${pullRequest.number} on GitHub`}
                      >
                        <ExternalLink className="size-4" />
                      </a>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {pullRequest.author} - {pullRequest.source_branch ?? "unknown"} -&gt;{" "}
                    {pullRequest.target_branch ?? "unknown"}
                  </p>
                </div>

                <div className="flex gap-4 text-xs text-muted-foreground md:text-right">
                  <div>
                    <p className="font-medium text-foreground">Created</p>
                    <p>{formatDate(pullRequest.github_created_at)}</p>
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Updated</p>
                    <p>{formatDate(pullRequest.github_updated_at)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
