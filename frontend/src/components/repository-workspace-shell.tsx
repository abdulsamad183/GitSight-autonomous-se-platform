"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ArrowLeft,
  FileText,
  GitBranch,
  GitPullRequest,
  LayoutDashboard,
  Loader2,
  MessageSquare,
  Network,
  RefreshCw,
  Search,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { BranchSelector } from "@/components/branch-selector";
import { JobProgressCard } from "@/components/job-progress-card";
import {
  type RepositoryWorkspaceTab,
  useRepositoryWorkspace,
} from "@/components/repository-workspace-context";
import { Button, buttonVariants } from "@/components/ui/button";
import { getQueryClient } from "@/lib/query-client";
import { useJobPolling } from "@/hooks/use-job-polling";

const NAV_ITEMS: {
  id: RepositoryWorkspaceTab;
  label: string;
  path: string;
  icon: LucideIcon;
}[] = [
  { id: "overview", label: "Overview", path: "", icon: LayoutDashboard },
  { id: "search", label: "Search", path: "/search", icon: Search },
  { id: "chat", label: "Chat", path: "/chat", icon: MessageSquare },
  { id: "graph", label: "Graph", path: "/graph", icon: Network },
  { id: "docs", label: "Docs", path: "/docs", icon: FileText },
  { id: "pull-requests", label: "Pull Requests", path: "/pull-requests", icon: GitPullRequest },
];

interface RepositoryWorkspaceShellProps {
  children: React.ReactNode;
  pageTitle?: string;
  pageDescription?: string;
  fullHeight?: boolean;
}

export function RepositoryWorkspaceShell({
  children,
  pageTitle,
  pageDescription,
  fullHeight = false,
}: RepositoryWorkspaceShellProps) {
  const pathname = usePathname();
  const {
    repositoryId,
    activeTab,
    branches,
    selectedBranch,
    setSelectedBranch,
    detail,
    isLoading,
    loadError,
    branchLoading,
    refreshJob,
    refreshError,
    isRefreshing,
    handleRefresh,
  } = useRepositoryWorkspace();

  const shouldPollRefresh = refreshJob?.job_id && !refreshJob.cached;
  const {
    job: polledRefreshJob,
    error: pollError,
    isPolling,
  } = useJobPolling(shouldPollRefresh ? refreshJob.job_id : null, {
    onTerminal: () => {
      void getQueryClient().invalidateQueries({
        queryKey: ["repository", repositoryId],
      });
    },
  });

  const branchQuery = selectedBranch ? `?branch=${encodeURIComponent(selectedBranch)}` : "";
  const repoLabel =
    detail && "owner" in detail
      ? `${detail.owner}/${detail.repository_name}`
      : "Repository";

  const hrefFor = (item: (typeof NAV_ITEMS)[number]) => {
    if (item.path.startsWith("#")) {
      return `/repositories/${repositoryId}${branchQuery}${item.path}`;
    }
    return `/repositories/${repositoryId}${item.path}${branchQuery}`;
  };

  const isNavActive = (item: (typeof NAV_ITEMS)[number]) => {
    if (item.id === activeTab) return true;
    if (item.id === "overview" && pathname === `/repositories/${repositoryId}`) return true;
    return false;
  };

  return (
    <div
      className={`flex bg-slate-50 dark:bg-background ${
        fullHeight ? "h-screen overflow-hidden" : "min-h-screen"
      }`}
    >
      <aside className="hidden w-60 shrink-0 flex-col border-r bg-card lg:flex">
        <div className="border-b p-4">
          <Link
            href="/dashboard"
            className={buttonVariants({ variant: "ghost", size: "sm", className: "mb-3 -ml-2" })}
          >
            <ArrowLeft className="mr-2 size-4" />
            Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <div className="flex size-9 items-center justify-center rounded-lg bg-violet-100 text-violet-700 dark:bg-violet-950/50 dark:text-violet-300">
              <GitBranch className="size-4" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{repoLabel}</p>
              <p className="truncate text-xs text-muted-foreground">
                {detail && "analysis_status" in detail ? detail.analysis_status : "Loading..."}
              </p>
            </div>
          </div>
        </div>

        {branches.length > 0 && (
          <div className="border-b p-3">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Branch
            </p>
            <BranchSelector
              branches={branches}
              selectedBranch={selectedBranch ?? branches[0]?.branch ?? ""}
              onSelect={setSelectedBranch}
            />
          </div>
        )}

        <nav className="flex-1 space-y-1 p-3">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.id}
                href={hrefFor(item)}
                data-active={isNavActive(item)}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition data-[active=true]:bg-violet-600 data-[active=true]:text-white text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <Icon className="size-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t p-3">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => void handleRefresh()}
            disabled={isRefreshing || isPolling}
          >
            {isRefreshing || isPolling ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 size-4" />
            )}
            Refresh
          </Button>
        </div>
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="shrink-0 border-b bg-card/80 px-4 py-3 backdrop-blur lg:hidden">
          <div className="mb-3 flex items-center justify-between gap-2">
            <Link href="/dashboard" className={buttonVariants({ variant: "ghost", size: "sm" })}>
              <ArrowLeft className="size-4" />
            </Link>
            <p className="truncate text-sm font-semibold">{repoLabel}</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void handleRefresh()}
              disabled={isRefreshing || isPolling}
            >
              {isRefreshing || isPolling ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <RefreshCw className="size-4" />
              )}
            </Button>
          </div>
          <div className="flex gap-1 overflow-x-auto pb-1">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.id}
                href={hrefFor(item)}
                data-active={isNavActive(item)}
                className="shrink-0 rounded-full px-3 py-1.5 text-xs font-medium transition data-[active=true]:bg-violet-600 data-[active=true]:text-white bg-muted text-muted-foreground"
              >
                {item.label}
              </Link>
            ))}
          </div>
        </header>

        <main
          className={`flex min-h-0 flex-1 flex-col ${
            fullHeight ? "overflow-hidden" : "overflow-y-auto"
          }`}
        >
          <div
            className={`mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 px-4 py-5 sm:px-6 ${
              fullHeight ? "min-h-0 overflow-hidden" : ""
            }`}
          >
            {(pageTitle || pageDescription) && (
              <div className="shrink-0">
                {pageTitle && <h1 className="text-xl font-semibold">{pageTitle}</h1>}
                {pageDescription && (
                  <p className="mt-1 text-sm text-muted-foreground">{pageDescription}</p>
                )}
              </div>
            )}

            {refreshError && (
              <div className="shrink-0 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
                {refreshError}
              </div>
            )}

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

            {isLoading && (
              <div className="flex flex-1 items-center justify-center py-16">
                <Loader2 className="size-8 animate-spin text-violet-500" />
              </div>
            )}

            {loadError && !isLoading && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {loadError}
              </div>
            )}

            {branchLoading && !isLoading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin text-violet-500" />
                Updating branch data...
              </div>
            )}

            {!isLoading && !loadError && detail && (
              <div className={fullHeight ? "flex min-h-0 flex-1 flex-col" : undefined}>
                {children}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
