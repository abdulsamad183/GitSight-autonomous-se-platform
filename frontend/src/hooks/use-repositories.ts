"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/lib/query-keys";
import {
  clearAllRepositories,
  deleteRepository,
  listRepositories,
} from "@/services/repositories";
import type { RepositoryListItem } from "@/types/repository";

export function useRepositories() {
  return useQuery({
    queryKey: queryKeys.repositories,
    queryFn: listRepositories,
  });
}

export function useDeleteRepository() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteRepository,
    onMutate: async (repositoryId: string) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.repositories });
      const previous = queryClient.getQueryData<RepositoryListItem[]>(queryKeys.repositories);
      queryClient.setQueryData<RepositoryListItem[]>(queryKeys.repositories, (current) =>
        current?.filter((repo) => repo.id !== repositoryId) ?? [],
      );
      return { previous };
    },
    onError: (_error, _repositoryId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.repositories, context.previous);
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.repositories });
    },
  });
}

export function useClearAllRepositories() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clearAllRepositories,
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: queryKeys.repositories });
      const previous = queryClient.getQueryData<RepositoryListItem[]>(queryKeys.repositories);
      queryClient.setQueryData<RepositoryListItem[]>(queryKeys.repositories, []);
      return { previous };
    },
    onError: (_error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.repositories, context.previous);
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.repositories });
    },
  });
}
