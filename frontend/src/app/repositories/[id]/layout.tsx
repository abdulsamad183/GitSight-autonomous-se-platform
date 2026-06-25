"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useEffect } from "react";

import { queryKeys } from "@/lib/query-keys";
import { listBranches, listPullRequests } from "@/services/repositories";

export default function RepositoryLayout({ children }: { children: React.ReactNode }) {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const repositoryId = params.id;

  useEffect(() => {
    if (!repositoryId) return;

    void queryClient.prefetchQuery({
      queryKey: queryKeys.repositoryBranches(repositoryId),
      queryFn: () => listBranches(repositoryId),
    });
    void queryClient.prefetchQuery({
      queryKey: queryKeys.repositoryPullRequests(repositoryId),
      queryFn: () => listPullRequests(repositoryId),
    });
  }, [repositoryId, queryClient]);

  return children;
}
