"use client";

import { Loader2, X } from "lucide-react";
import { useEffect, useState } from "react";

import { getRepositoryChunk } from "@/services/repositories";
import type { ChunkDetail, SearchResult } from "@/types/search";

interface SearchResultDrawerProps {
  repositoryId: string;
  result: SearchResult | null;
  onClose: () => void;
}

export function SearchResultDrawer({
  repositoryId,
  result,
  onClose,
}: SearchResultDrawerProps) {
  const [chunk, setChunk] = useState<ChunkDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!result) {
      setChunk(null);
      setError(null);
      return;
    }

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getRepositoryChunk(repositoryId, result.chunk_id);
        if (!cancelled) setChunk(data);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load chunk");
          setChunk(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [repositoryId, result]);

  if (!result) return null;

  const lines = chunk?.content.split("\n") ?? [];
  const startLine = chunk?.start_line ?? result.start_line;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40" onClick={onClose}>
      <div
        className="flex h-full w-full max-w-2xl flex-col bg-background shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="min-w-0">
            <p className="truncate font-semibold">
              {result.symbol_name.replace(/<[^>]+>/g, "")}
            </p>
            <p className="truncate font-mono text-xs text-muted-foreground">{result.file_path}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-2 hover:bg-muted"
            aria-label="Close"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-6 animate-spin text-violet-500" />
            </div>
          )}
          {error && (
            <p className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
              {error}
            </p>
          )}
          {chunk && !loading && (
            <pre className="overflow-x-auto rounded-lg bg-muted/50 p-4 font-mono text-xs leading-relaxed">
              {lines.map((line, index) => {
                const lineNumber = startLine + index;
                const isHighlighted =
                  lineNumber >= chunk.start_line && lineNumber <= chunk.end_line;
                return (
                  <div
                    key={`${lineNumber}-${index}`}
                    className={isHighlighted ? "bg-violet-100 dark:bg-violet-900/40" : ""}
                  >
                    <span className="mr-4 inline-block w-8 select-none text-right text-muted-foreground">
                      {lineNumber}
                    </span>
                    <span>{line}</span>
                  </div>
                );
              })}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
