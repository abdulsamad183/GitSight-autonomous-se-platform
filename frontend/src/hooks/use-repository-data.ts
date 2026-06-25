"use client";

import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/lib/query-keys";
import {
  getRepositoryDetails,
  getRepositoryGraph,
  listBranches,
  listPullRequests,
} from "@/services/repositories";

export function useRepositoryBranches(repositoryId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.repositoryBranches(repositoryId ?? ""),
    queryFn: () => listBranches(repositoryId!),
    enabled: Boolean(repositoryId),
  });
}

export function useRepositoryDetails(
  repositoryId: string | undefined,
  branch?: string | null,
) {
  return useQuery({
    queryKey: queryKeys.repositoryDetails(repositoryId ?? "", branch),
    queryFn: () => getRepositoryDetails(repositoryId!, branch ?? undefined),
    enabled: Boolean(repositoryId),
  });
}

export function useRepositoryPullRequests(repositoryId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.repositoryPullRequests(repositoryId ?? ""),
    queryFn: () => listPullRequests(repositoryId!),
    enabled: Boolean(repositoryId),
  });
}

export function useRepositoryGraph(
  repositoryId: string | undefined,
  branch?: string | null,
) {
  return useQuery({
    queryKey: queryKeys.repositoryGraph(repositoryId ?? "", branch),
    queryFn: () => getRepositoryGraph(repositoryId!, branch ?? undefined),
    enabled: Boolean(repositoryId),
  });
}
