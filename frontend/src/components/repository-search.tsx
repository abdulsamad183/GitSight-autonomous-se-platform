"use client";

import { Loader2, Search, X } from "lucide-react";
import { useState } from "react";

import { SearchResultDrawer } from "@/components/search-result-drawer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRepositorySearch } from "@/hooks/use-repository-search";
import type { SearchMode, SearchResult } from "@/types/search";

const MODE_OPTIONS: { value: SearchMode; label: string }[] = [
  { value: "hybrid", label: "Hybrid" },
  { value: "keyword", label: "Keyword" },
  { value: "semantic", label: "Semantic" },
];

const CHUNK_TYPE_OPTIONS = [
  { value: "", label: "All types" },
  { value: "function", label: "Function" },
  { value: "method", label: "Method" },
  { value: "class", label: "Class" },
  { value: "interface", label: "Interface" },
  { value: "enum", label: "Enum" },
  { value: "module", label: "Module" },
  { value: "file", label: "File" },
  { value: "section", label: "Section" },
  { value: "diff_hunk", label: "Diff hunk" },
] as const;

/** Visible rows in the results viewport; API fetches this many per page. */
const RESULTS_PAGE_SIZE = 5;
/** Approximate height of one result row for the 5-item scroll viewport. */
const RESULT_ROW_HEIGHT_REM = 7.5;

const CHUNK_TYPE_COLORS: Record<string, string> = {
  function: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  method: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-200",
  class: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-200",
  interface: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200",
  enum: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
};

function HighlightedHtml({ html }: { html: string }) {
  return (
    <span
      className="[&_mark]:rounded [&_mark]:bg-yellow-200 [&_mark]:px-0.5 dark:[&_mark]:bg-yellow-800/60"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

interface RepositorySearchProps {
  repositoryId: string;
  branch?: string | null;
}

export function RepositorySearch({ repositoryId, branch }: RepositorySearchProps) {
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [filePath, setFilePath] = useState("");
  const [chunkType, setChunkType] = useState("");
  const [language, setLanguage] = useState("");

  const {
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
    hasMore,
    recentSearches,
  } = useRepositorySearch({
    repositoryId,
    branch,
    mode,
    limit: RESULTS_PAGE_SIZE,
    filters: { filePath, chunkType, language },
  });

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") search();
  };

  const clearFilters = () => {
    setFilePath("");
    setChunkType("");
    setLanguage("");
  };

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold">Search Repository</h2>
        <p className="text-sm text-muted-foreground">
          Search code by keyword, natural language, or hybrid retrieval
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search symbols, files, or describe what you're looking for..."
            className="pl-9 pr-9"
          />
          {query && (
            <button
              type="button"
              onClick={clear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="size-4" />
            </button>
          )}
        </div>

        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as SearchMode)}
          className="h-9 rounded-md border bg-background px-3 text-sm"
        >
          {MODE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <Button type="button" onClick={() => search()} disabled={loading || !query.trim()}>
          {loading ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
          Search
        </Button>
      </div>

      <div className="grid gap-2 sm:grid-cols-3">
        <Input
          value={filePath}
          onChange={(e) => setFilePath(e.target.value)}
          placeholder="Path prefix (e.g. src/)"
          aria-label="Filter by file path"
        />
        <select
          value={chunkType}
          onChange={(e) => setChunkType(e.target.value)}
          className="h-9 rounded-md border bg-background px-3 text-sm"
          aria-label="Filter by chunk type"
        >
          {CHUNK_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value || "all"} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <div className="flex gap-2">
          <Input
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            placeholder="Language (e.g. python)"
            aria-label="Filter by language"
          />
          {(filePath || chunkType || language) && (
            <Button type="button" variant="outline" onClick={clearFilters}>
              Clear
            </Button>
          )}
        </div>
      </div>

      {recentSearches.length > 0 && !query && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted-foreground">Recent:</span>
          {recentSearches.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                setQuery(item);
                search(item);
              }}
              className="rounded-full bg-muted px-3 py-1 hover:bg-muted/80"
            >
              {item}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
          {error}
        </div>
      )}

      {query.trim() && !loading && !error && results.length === 0 && (
        <div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">
          No matches found for &ldquo;{query}&rdquo;
        </div>
      )}

      {(results.length > 0 || loading) && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {loading && results.length === 0
                ? "Searching..."
                : `${totalResults} result${totalResults === 1 ? "" : "s"}`}
              {results.length > 0 && (
                <span className="ml-1">
                  (showing {results.length}
                  {hasMore ? `, scroll for more` : ""})
                </span>
              )}
              {executionTimeMs !== null && !loading && (
                <span className="ml-2">({executionTimeMs.toFixed(0)}ms)</span>
              )}
            </span>
            {branch && <span>Branch: {branch}</span>}
          </div>

          <div className="rounded-2xl border bg-card shadow-sm">
            <div
              className="divide-y overflow-y-auto overscroll-contain"
              style={{ maxHeight: `${RESULTS_PAGE_SIZE * RESULT_ROW_HEIGHT_REM}rem` }}
            >
              {results.map((result) => (
                <button
                  key={result.chunk_id}
                  type="button"
                  onClick={() => setSelectedResult(result)}
                  className="w-full shrink-0 px-4 py-3 text-left hover:bg-muted/40"
                  style={{ minHeight: `${RESULT_ROW_HEIGHT_REM}rem` }}
                >
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      CHUNK_TYPE_COLORS[result.chunk_type] ?? "bg-slate-100 text-slate-700"
                    }`}
                  >
                    {result.chunk_type}
                  </span>
                  <span className="font-semibold">
                    <HighlightedHtml html={result.symbol_name} />
                  </span>
                  <span className="text-xs text-muted-foreground">
                    L{result.start_line}–{result.end_line}
                  </span>
                </div>
                <p className="mt-1 truncate font-mono text-xs text-muted-foreground">
                  {result.file_path}
                </p>
                <p className="mt-2 line-clamp-3 font-mono text-xs leading-relaxed">
                  <HighlightedHtml html={result.content_snippet} />
                </p>
                <p className="mt-1 text-[10px] text-muted-foreground/70">
                  {result.keyword_score !== null && `kw: ${result.keyword_score.toFixed(3)}`}
                  {result.semantic_score !== null &&
                    ` · sem: ${result.semantic_score.toFixed(3)}`}
                  {result.final_score !== null && ` · final: ${result.final_score.toFixed(3)}`}
                </p>
              </button>
            ))}

              {loading && (
                <div className="flex min-h-[3rem] items-center justify-center py-4">
                  <Loader2 className="size-5 animate-spin text-violet-500" />
                </div>
              )}
            </div>
          </div>

          {hasMore && !loading && (
            <Button type="button" variant="outline" onClick={loadMore} className="w-full">
              Load more results
            </Button>
          )}
        </div>
      )}

      <SearchResultDrawer
        repositoryId={repositoryId}
        result={selectedResult}
        onClose={() => setSelectedResult(null)}
      />
    </section>
  );
}
