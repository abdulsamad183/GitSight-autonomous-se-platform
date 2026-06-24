"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { searchRepository } from "@/services/repositories";
import type { SearchMode, SearchResult } from "@/types/search";

const DEBOUNCE_MS = 400;
const RECENT_SEARCHES_KEY = "gitsight_recent_searches";
const MAX_RECENT = 5;

interface UseRepositorySearchOptions {
  repositoryId: string;
  branch?: string | null;
  mode?: SearchMode;
  limit?: number;
}

export function useRepositorySearch({
  repositoryId,
  branch,
  mode = "hybrid",
  limit = 20,
}: UseRepositorySearchOptions) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [executionTimeMs, setExecutionTimeMs] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
      if (stored) setRecentSearches(JSON.parse(stored) as string[]);
    } catch {
      // ignore
    }
  }, []);

  const saveRecentSearch = useCallback((q: string) => {
    setRecentSearches((prev) => {
      const next = [q, ...prev.filter((item) => item !== q)].slice(0, MAX_RECENT);
      localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const runSearch = useCallback(
    async (searchQuery: string, searchOffset = 0, append = false) => {
      const trimmed = searchQuery.trim();
      if (!trimmed) {
        setResults([]);
        setTotalResults(0);
        setExecutionTimeMs(null);
        setError(null);
        return;
      }

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);

      try {
        const response = await searchRepository(repositoryId, {
          q: trimmed,
          mode,
          limit,
          offset: searchOffset,
          branch: branch ?? undefined,
        });

        if (controller.signal.aborted) return;

        setResults((prev) => (append ? [...prev, ...response.results] : response.results));
        setTotalResults(response.total_results);
        setExecutionTimeMs(response.execution_time_ms);
        setOffset(searchOffset);
        if (!append) saveRecentSearch(trimmed);
      } catch (e) {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : "Search failed");
        if (!append) setResults([]);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    },
    [repositoryId, mode, limit, branch, saveRecentSearch],
  );

  const search = useCallback(
    (searchQuery?: string) => {
      void runSearch(searchQuery ?? query, 0, false);
    },
    [query, runSearch],
  );

  const loadMore = useCallback(() => {
    if (results.length < totalResults) {
      void runSearch(query, offset + limit, true);
    }
  }, [results.length, totalResults, runSearch, query, offset, limit]);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setQuery("");
    setResults([]);
    setTotalResults(0);
    setExecutionTimeMs(null);
    setError(null);
    setOffset(0);
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults([]);
      setTotalResults(0);
      return;
    }
    debounceRef.current = setTimeout(() => {
      void runSearch(query, 0, false);
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, mode, branch, runSearch]);

  return {
    query,
    setQuery,
    results,
    totalResults,
    executionTimeMs,
    loading,
    error,
    search,
    loadMore,
    clear,
    hasMore: results.length < totalResults,
    recentSearches,
  };
}
