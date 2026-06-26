"use client";

import { RepositoryDocs } from "@/components/repository-docs";
import { useRepositoryWorkspace } from "@/components/repository-workspace-context";

export default function RepositoryDocsPage() {
  const { repositoryId, selectedBranch } = useRepositoryWorkspace();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Documentation</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          AI-generated and repository documentation.
        </p>
      </div>
      <RepositoryDocs repositoryId={repositoryId} branch={selectedBranch} />
    </div>
  );
}
