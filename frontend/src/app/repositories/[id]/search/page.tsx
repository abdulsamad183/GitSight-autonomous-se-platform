"use client";

import { RepositorySearch } from "@/components/repository-search";
import { useRepositoryWorkspace } from "@/components/repository-workspace-context";

export default function RepositorySearchPage() {
  const { repositoryId, selectedBranch, detail } = useRepositoryWorkspace();

  if (!detail) return null;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Search</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Search code, symbols, and documentation in this repository.
        </p>
      </div>
      <div className="rounded-xl border bg-card p-4 shadow-sm">
        <RepositorySearch
          repositoryId={repositoryId}
          branch={selectedBranch ?? ("selected_branch" in detail ? detail.selected_branch : null)}
        />
      </div>
    </div>
  );
}
