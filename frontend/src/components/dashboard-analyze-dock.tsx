"use client";

import { RepositoryUrlForm } from "@/components/repository-url-form";
import type { AnalyzeResponse } from "@/types/repository";

interface DashboardAnalyzeDockProps {
  onAnalyzeStarted: (result: AnalyzeResponse) => void;
}

export function DashboardAnalyzeDock({ onAnalyzeStarted }: DashboardAnalyzeDockProps) {
  return (
    <div className="w-full">
      <RepositoryUrlForm variant="dock" onAnalyzeStarted={onAnalyzeStarted} />
    </div>
  );
}
