"use client";

import { RepositoryDetailTabs } from "@/components/repository-detail-tabs";
import { RepositoryMetricsRibbon } from "@/components/repository-stats";
import { useRepositoryWorkspace } from "@/components/repository-workspace-context";

export default function RepositoryDetailPage() {
  const { selectedBranch, detail } = useRepositoryWorkspace();

  if (!detail || !("files" in detail)) {
    return null;
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-5">
      <RepositoryMetricsRibbon
        files_count={detail.files_count}
        classes_count={detail.classes_count}
        functions_count={detail.functions_count}
        methods_count={detail.methods_count}
        dependencies_count={detail.dependencies_count}
        total_pull_requests={detail.total_pull_requests}
        open_pull_requests={detail.open_pull_requests}
        merged_pull_requests={detail.merged_pull_requests}
      />

      <div className="flex min-h-0 flex-1 flex-col rounded-xl border bg-card shadow-sm">
        <div className="border-b px-4 py-3">
          <h1 className="text-sm font-semibold">
            Code Explorer
            {selectedBranch ? (
              <span className="ml-2 font-normal text-muted-foreground">— {selectedBranch}</span>
            ) : null}
          </h1>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          <RepositoryDetailTabs
            files={detail.files}
            symbols={detail.symbols}
            dependencies={detail.dependencies}
          />
        </div>
      </div>
    </div>
  );
}
