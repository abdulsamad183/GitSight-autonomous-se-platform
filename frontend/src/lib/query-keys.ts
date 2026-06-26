export const queryKeys = {
  repositories: ["repositories"] as const,
  repositoryBranches: (repositoryId: string) =>
    ["repository", repositoryId, "branches"] as const,
  repositoryDetails: (repositoryId: string, branch?: string | null) =>
    ["repository", repositoryId, "details", branch ?? ""] as const,
  repositoryPullRequests: (repositoryId: string) =>
    ["repository", repositoryId, "pull-requests"] as const,
  repositoryGraph: (repositoryId: string, branch?: string | null) =>
    ["repository", repositoryId, "graph", branch ?? ""] as const,
  repositoryDocumentation: (repositoryId: string, branch?: string | null) =>
    ["repository", repositoryId, "documentation", branch ?? ""] as const,
  repositoryDocumentationType: (
    repositoryId: string,
    documentType: string,
    branch?: string | null,
  ) => ["repository", repositoryId, "documentation", documentType, branch ?? ""] as const,
  repositoryPullRequestReview: (repositoryId: string, pullRequestId: string) =>
    ["repository", repositoryId, "pull-requests", pullRequestId, "review"] as const,
};
