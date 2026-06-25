"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Loader2 } from "lucide-react";

import { BranchSelector } from "@/components/branch-selector";
import { RepositoryStructureGraph } from "@/components/repository-structure-graph";
import { buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useRepositoryBranches, useRepositoryGraph } from "@/hooks/use-repository-data";

export default function RepositoryGraphPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const repositoryId = params.id;

  const branchFromUrl = searchParams.get("branch");
  const [branchOverride, setBranchOverride] = useState<string | null>(null);

  const branchesQuery = useRepositoryBranches(repositoryId);
  const branches = branchesQuery.data ?? [];

  const selectedBranch =
    branchOverride ?? branchFromUrl ?? branches[0]?.branch ?? null;

  const graphQuery = useRepositoryGraph(repositoryId, selectedBranch);
  const graph = graphQuery.data;

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  const handleBranchSelect = (branch: string) => {
    setBranchOverride(branch);
  };

  const initialLoading =
    (branchesQuery.isLoading && branches.length === 0) ||
    (graphQuery.isLoading && !graph);
  const branchLoading = graphQuery.isFetching && Boolean(graph);
  const loadError =
    branchesQuery.error instanceof Error
      ? branchesQuery.error.message
      : graphQuery.error instanceof Error
        ? graphQuery.error.message
        : null;

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="size-6 animate-spin text-violet-500" />
      </div>
    );
  }

  const repoLabel =
    graph?.nodes.find((node) => node.type === "repository")?.label ?? "Repository";

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-gradient-to-br from-violet-50 via-white to-sky-50">
      <header className="z-10 flex shrink-0 items-center justify-between gap-4 border-b border-white/70 bg-white/80 px-4 py-2.5 backdrop-blur-xl sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <Link
            href={`/repositories/${repositoryId}${
              selectedBranch ? `?branch=${encodeURIComponent(selectedBranch)}` : ""
            }`}
            className={buttonVariants({ variant: "ghost", size: "sm" })}
          >
            <ArrowLeft className="size-4" />
            <span className="hidden sm:inline">Back</span>
          </Link>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-foreground">{repoLabel}</p>
            <p className="text-xs text-muted-foreground">Structure graph</p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          {graph && (
            <div className="hidden items-center gap-2 text-xs sm:flex">
              <span className="rounded-full bg-sky-100 px-2.5 py-1 font-medium text-sky-700">
                {graph.stats.files_count} files
              </span>
              <span className="rounded-full bg-indigo-100 px-2.5 py-1 font-medium text-indigo-700">
                {graph.stats.classes_count} classes
              </span>
              <span className="rounded-full bg-violet-100 px-2.5 py-1 font-medium text-violet-700">
                {graph.stats.methods_count} methods
              </span>
            </div>
          )}
          {branches.length > 0 && (
            <BranchSelector
              branches={branches}
              selectedBranch={selectedBranch ?? branches[0]?.branch ?? ""}
              onSelect={handleBranchSelect}
              branchesTruncated={false}
            />
          )}
        </div>
      </header>

      {graph?.empty_state && (
        <div className="shrink-0 border-b border-amber-200/80 bg-amber-50 px-4 py-2 text-center text-sm text-amber-800">
          {graph.empty_state}
        </div>
      )}

      <main className="relative min-h-0 flex-1">
        {initialLoading && (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="size-8 animate-spin text-violet-500" />
          </div>
        )}

        {loadError && (
          <div className="flex h-full items-center justify-center p-6">
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-700">
              {loadError}
            </div>
          </div>
        )}

        {graph && !loadError && (
          <div className="absolute inset-0">
            {branchLoading ? (
              <div className="flex h-full items-center justify-center">
                <Loader2 className="size-6 animate-spin text-violet-500" />
              </div>
            ) : (
              <RepositoryStructureGraph graph={graph} branch={graph.branch} />
            )}
          </div>
        )}
      </main>
    </div>
  );
}
