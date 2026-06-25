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
};
