"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, GitBranch } from "lucide-react";

import type { BranchSummary } from "@/types/repository";

interface BranchSelectorProps {
  branches: BranchSummary[];
  selectedBranch: string;
  onSelect: (branch: string) => void;
}

export function BranchSelector({
  branches,
  selectedBranch,
  onSelect,
}: BranchSelectorProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const activeBranch =
    branches.find((branch) => branch.branch === selectedBranch) ?? branches[0];

  useEffect(() => {
    if (!open) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  if (branches.length === 0 || !activeBranch) {
    return null;
  }

  const handleSelect = (branch: string) => {
    onSelect(branch);
    setOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="listbox"
        className="flex w-full items-center gap-2 rounded-lg border bg-background px-3 py-2 text-left text-sm shadow-sm transition hover:bg-muted/50"
      >
        <GitBranch className="size-4 shrink-0 text-violet-600" />
        <span className="min-w-0 flex-1 truncate font-medium">{activeBranch.branch}</span>
        <ChevronDown
          className={`size-4 shrink-0 text-muted-foreground transition ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <ul
          role="listbox"
          aria-label="Select branch"
          className="absolute left-0 right-0 z-50 mt-1 max-h-56 overflow-y-auto rounded-lg border bg-popover py-1 shadow-lg"
        >
          {branches.map((branch) => {
            const isActive = branch.branch === activeBranch.branch;
            return (
              <li key={branch.branch} role="option" aria-selected={isActive}>
                <button
                  type="button"
                  onClick={() => handleSelect(branch.branch)}
                  className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition hover:bg-muted ${
                    isActive ? "bg-violet-50 text-violet-900 dark:bg-violet-950/40 dark:text-violet-100" : ""
                  }`}
                >
                  <span className="min-w-0 flex-1 truncate font-medium">{branch.branch}</span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {branch.files_count} files
                  </span>
                  {isActive && <Check className="size-4 shrink-0 text-violet-600" />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
