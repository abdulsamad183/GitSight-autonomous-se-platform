"use client";

import type { BranchSummary } from "@/types/repository";

interface BranchSelectorProps {
  branches: BranchSummary[];
  selectedBranch: string;
  onSelect: (branch: string) => void;
  branchesTruncated: boolean;
}

export function BranchSelector({
  branches,
  selectedBranch,
  onSelect,
  branchesTruncated,
}: BranchSelectorProps) {
  if (branches.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      {branchesTruncated && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
          Only the first 10 branches were analyzed. Re-run analysis after reducing branches or
          increasing the server limit.
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {branches.map((branch) => {
          const isActive = branch.branch === selectedBranch;
          return (
            <button
              key={branch.branch}
              type="button"
              onClick={() => onSelect(branch.branch)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                isActive
                  ? "bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md"
                  : "bg-muted text-muted-foreground hover:bg-violet-100 hover:text-violet-800 dark:hover:bg-violet-950/40 dark:hover:text-violet-200"
              }`}
            >
              <span>{branch.branch}</span>
              <span className={`ml-2 text-xs ${isActive ? "text-violet-100" : "opacity-70"}`}>
                {branch.files_count} files
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
