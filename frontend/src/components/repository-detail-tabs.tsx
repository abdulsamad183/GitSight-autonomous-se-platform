"use client";

import { useState } from "react";

import type { DependencyItem, FileItem, SymbolItem } from "@/types/repository";

type Tab = "files" | "symbols" | "dependencies";

const TABS: { id: Tab; label: string; color: string }[] = [
  { id: "files", label: "Files", color: "data-[active=true]:bg-blue-500" },
  { id: "symbols", label: "Symbols", color: "data-[active=true]:bg-violet-500" },
  { id: "dependencies", label: "Dependencies", color: "data-[active=true]:bg-rose-500" },
];

const LANGUAGE_COLORS: Record<string, string> = {
  python: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200",
  javascript: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
  typescript: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200",
};

const SYMBOL_COLORS: Record<string, string> = {
  class: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-200",
  function: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  method: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-200",
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

interface RepositoryDetailTabsProps {
  files: FileItem[];
  symbols: SymbolItem[];
  dependencies: DependencyItem[];
}

export function RepositoryDetailTabs({
  files,
  symbols,
  dependencies,
}: RepositoryDetailTabsProps) {
  const [activeTab, setActiveTab] = useState<Tab>("files");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            data-active={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition data-[active=true]:text-white ${tab.color} bg-muted text-muted-foreground hover:bg-muted/80`}
          >
            {tab.label}
            <span className="ml-2 opacity-80">
              ({tab.id === "files" ? files.length : tab.id === "symbols" ? symbols.length : dependencies.length})
            </span>
          </button>
        ))}
      </div>

      <div className="rounded-2xl border bg-card shadow-sm">
        {activeTab === "files" && (
          <div className="divide-y max-h-[480px] overflow-y-auto">
            {files.length === 0 ? (
              <p className="p-6 text-sm text-muted-foreground">No files indexed.</p>
            ) : (
              files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-muted/40"
                >
                  <div className="min-w-0">
                    <p className="truncate font-mono text-sm">{file.relative_path}</p>
                    <p className="text-xs text-muted-foreground">{formatBytes(file.size_bytes)}</p>
                  </div>
                  {file.language && (
                    <span
                      className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                        LANGUAGE_COLORS[file.language] ?? "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {file.language}
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "symbols" && (
          <div className="divide-y max-h-[480px] overflow-y-auto">
            {symbols.length === 0 ? (
              <p className="p-6 text-sm text-muted-foreground">No symbols extracted.</p>
            ) : (
              symbols.map((symbol, index) => (
                <div key={`${symbol.file_path}-${symbol.symbol_name}-${index}`} className="px-4 py-3 hover:bg-muted/40">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        SYMBOL_COLORS[symbol.symbol_type] ?? "bg-slate-100"
                      }`}
                    >
                      {symbol.symbol_type}
                    </span>
                    <p className="font-semibold">{symbol.symbol_name}</p>
                    <p className="text-xs text-muted-foreground">
                      L{symbol.start_line}–{symbol.end_line}
                    </p>
                  </div>
                  <p className="mt-1 truncate font-mono text-xs text-muted-foreground">
                    {symbol.file_path}
                  </p>
                  {symbol.signature && (
                    <p className="mt-1 truncate font-mono text-xs text-sky-700 dark:text-sky-300">
                      {symbol.signature}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "dependencies" && (
          <div className="divide-y max-h-[480px] overflow-y-auto">
            {dependencies.length === 0 ? (
              <p className="p-6 text-sm text-muted-foreground">No file-level dependencies found.</p>
            ) : (
              dependencies.map((dep, index) => (
                <div key={`${dep.source_path}-${dep.target_path}-${index}`} className="px-4 py-3 hover:bg-muted/40">
                  <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-700 dark:bg-rose-900/40 dark:text-rose-200">
                    {dep.dependency_type}
                  </span>
                  <p className="mt-2 font-mono text-sm">
                    <span className="text-muted-foreground">{dep.source_path}</span>
                    <span className="mx-2 text-violet-500">→</span>
                    <span className="font-medium">{dep.target_path}</span>
                  </p>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
