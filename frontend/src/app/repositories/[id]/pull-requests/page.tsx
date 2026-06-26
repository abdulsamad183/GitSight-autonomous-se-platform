"use client";

import { RepositoryPullRequests } from "@/components/repository-pull-requests";
import { useRepositoryWorkspace } from "@/components/repository-workspace-context";

export default function RepositoryPullRequestsPage() {
  const { repositoryId } = useRepositoryWorkspace();

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="shrink-0">
        <h1 className="text-xl font-semibold">Pull Requests</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Review synchronized pull requests with AI-generated code reviews.
        </p>
      </div>
      <div className="min-h-0 flex-1">
        <RepositoryPullRequests repositoryId={repositoryId} />
      </div>
    </div>
  );
}
