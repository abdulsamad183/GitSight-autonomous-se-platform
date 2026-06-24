"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Loader2 } from "lucide-react";

import { BranchSelector } from "@/components/branch-selector";
import { RepositoryStructureGraph } from "@/components/repository-structure-graph";
import { buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { getRepositoryGraph, listBranches } from "@/services/repositories";
import type { RepositoryGraph } from "@/types/graph";
import type { BranchSummary } from "@/types/repository";

export default function RepositoryGraphPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [branches, setBranches] = useState<BranchSummary[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string | null>(
    searchParams.get("branch"),
  );
  const [graph, setGraph] = useState<RepositoryGraph | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  const loadGraph = useCallback(
    async (branch?: string) => {
      if (!params.id) return;
      setLoading(true);
      try {
        const data = await getRepositoryGraph(params.id, branch);
        setGraph(data);
        setSelectedBranch(data.branch ?? branch ?? null);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load graph");
      } finally {
        setLoading(false);
      }
    },
    [params.id],
  );

  useEffect(() => {
    if (!params.id || authLoading || !isAuthenticated) return;

    const load = async () => {
      try {
        const branchList = await listBranches(params.id);
        setBranches(branchList);
        const initialBranch =
          searchParams.get("branch") ?? branchList[0]?.branch ?? undefined;
        await loadGraph(initialBranch);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load graph");
        setLoading(false);
      }
    };

    void load();
  }, [params.id, authLoading, isAuthenticated, loadGraph, searchParams]);

  const handleBranchSelect = (branch: string) => {
    setSelectedBranch(branch);
    void loadGraph(branch);
  };

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
            href={`/repositories/${params.id}`}
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
        {loading && !graph && (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="size-8 animate-spin text-violet-500" />
          </div>
        )}

        {error && (
          <div className="flex h-full items-center justify-center p-6">
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-700">
              {error}
            </div>
          </div>
        )}

        {graph && !error && (
          <div className="absolute inset-0">
            {loading ? (
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
