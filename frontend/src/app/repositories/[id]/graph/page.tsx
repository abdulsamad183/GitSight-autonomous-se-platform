"use client";

import { Loader2 } from "lucide-react";

import { GraphImpactTools } from "@/components/graph-impact-tools";
import { RepositoryStructureGraph } from "@/components/repository-structure-graph";
import { useRepositoryWorkspace } from "@/components/repository-workspace-context";
import { useRepositoryGraph } from "@/hooks/use-repository-data";

export default function RepositoryGraphPage() {
  const { repositoryId, selectedBranch, detail } = useRepositoryWorkspace();
  const graphQuery = useRepositoryGraph(repositoryId, selectedBranch);
  const graph = graphQuery.data;

  const branchLoading = graphQuery.isFetching && Boolean(graph);
  const loadError = graphQuery.error instanceof Error ? graphQuery.error.message : null;
  const filePaths =
    detail && "files" in detail ? detail.files.map((file) => file.relative_path) : [];

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <div className="shrink-0">
        <h1 className="text-xl font-semibold">Structure Graph</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Interactive structure visualization plus blast radius and path finder tools.
        </p>
      </div>

      <GraphImpactTools
        repositoryId={repositoryId}
        branch={selectedBranch}
        filePaths={filePaths}
      />

      {graph?.empty_state && (
        <div className="shrink-0 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          {graph.empty_state}
        </div>
      )}

      {loadError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {loadError}
        </div>
      )}

      <div className="relative min-h-0 flex-1 rounded-xl border bg-card">
        {graphQuery.isLoading && !graph && (
          <div className="flex h-full min-h-[400px] items-center justify-center">
            <Loader2 className="size-8 animate-spin text-violet-500" />
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
      </div>
    </div>
  );
}
