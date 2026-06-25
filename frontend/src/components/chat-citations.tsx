"use client";

import { FileCode2 } from "lucide-react";

import type { ChatSource } from "@/types/chat";
import { TOOL_GROUP_LABELS } from "@/types/chat";
import type { SearchResult } from "@/types/search";

const CHUNK_TYPE_COLORS: Record<string, string> = {
  function: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  method: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-200",
  class: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-200",
  interface: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200",
  enum: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
  diff_hunk: "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200",
  file: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-rose-200",
  section: "bg-slate-100 text-slate-800 dark:bg-slate-900/40 dark:text-slate-200",
};

export function sourceToSearchResult(source: ChatSource): SearchResult {
  return {
    chunk_id: source.chunk_id,
    symbol_name: source.symbol_name,
    file_path: source.file_path,
    chunk_type: source.chunk_type,
    content_snippet: "",
    keyword_score: null,
    semantic_score: null,
    final_score: null,
    start_line: 0,
    end_line: 0,
    branch_name: source.branch_name ?? "",
  };
}

interface ChatCitationsProps {
  sources: ChatSource[];
  onSelect: (result: SearchResult) => void;
}

function uniqueSources(sources: ChatSource[]): ChatSource[] {
  const seen = new Set<string>();
  const unique: ChatSource[] = [];
  for (const source of sources) {
    if (seen.has(source.chunk_id)) continue;
    seen.add(source.chunk_id);
    unique.push(source);
  }
  return unique;
}

function groupSources(sources: ChatSource[]): Map<string, ChatSource[]> {
  const groups = new Map<string, ChatSource[]>();
  for (const source of sources) {
    const key = source.source_tool ?? "search";
    const existing = groups.get(key) ?? [];
    existing.push(source);
    groups.set(key, existing);
  }
  return groups;
}

export function ChatCitations({ sources, onSelect }: ChatCitationsProps) {
  if (sources.length === 0) return null;

  const groups = groupSources(uniqueSources(sources));

  return (
    <div className="mt-3 space-y-3">
      <p className="text-xs font-medium text-muted-foreground">Sources</p>
      {[...groups.entries()].map(([tool, toolSources]) => (
        <div key={tool} className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground">
            {TOOL_GROUP_LABELS[tool] ?? tool}
          </p>
          <div className="flex flex-wrap gap-2">
            {toolSources.map((source, index) => (
              <button
                key={`${source.chunk_id}-${index}`}
                type="button"
                onClick={() => onSelect(sourceToSearchResult(source))}
                className="inline-flex max-w-full items-center gap-2 rounded-lg border bg-muted/40 px-3 py-2 text-left text-xs transition hover:bg-muted"
              >
                <FileCode2 className="size-3.5 shrink-0 text-violet-500" />
                <span className="min-w-0">
                  <span
                    className={`mr-2 rounded-full px-2 py-0.5 font-medium ${
                      CHUNK_TYPE_COLORS[source.chunk_type] ?? "bg-slate-100"
                    }`}
                  >
                    {source.chunk_type}
                  </span>
                  <span className="font-medium">{source.symbol_name}</span>
                  <span className="mt-0.5 block truncate font-mono text-muted-foreground">
                    {source.file_path}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
