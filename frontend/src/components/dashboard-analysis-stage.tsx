"use client";

import { Loader2 } from "lucide-react";

import { DashboardHero } from "@/components/dashboard-hero";
import { JobProgressCard } from "@/components/job-progress-card";
import { Card, CardContent } from "@/components/ui/card";
import type { JobStatusResponse } from "@/types/job";
import type { AnalyzeResponse } from "@/types/repository";

interface DashboardAnalysisStageProps {
  username?: string;
  activeJob: {
    result: AnalyzeResponse;
    cached: boolean;
    isRefresh: boolean;
  } | null;
  job: JobStatusResponse | null | undefined;
  pollError: string | null;
  isPolling: boolean;
}

function ProgressWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex w-full min-h-0 flex-1 items-center justify-center">
      <div className="flex h-full max-h-[min(420px,100%)] w-full min-h-0 flex-col">
        {children}
      </div>
    </div>
  );
}

export function DashboardAnalysisStage({
  username,
  activeJob,
  job,
  pollError,
  isPolling,
}: DashboardAnalysisStageProps) {
  const showProgress =
    activeJob &&
    (activeJob.cached || job || isPolling || (activeJob.result.job_id && !activeJob.cached));

  if (!showProgress) {
    return (
      <div className="flex w-full min-h-0 flex-1 items-center justify-center overflow-hidden">
        <DashboardHero username={username} />
      </div>
    );
  }

  if (activeJob.cached) {
    return (
      <ProgressWrapper>
        <JobProgressCard
          job={{
            id: activeJob.result.job_id ?? "",
            status: "COMPLETED",
            progress: 100,
            current_stage: "Loaded from database",
            error_message: null,
            events: [],
          }}
          repositoryId={activeJob.result.repository_id}
          pollError={null}
          cached
          constrained
        />
      </ProgressWrapper>
    );
  }

  if (job) {
    return (
      <ProgressWrapper>
        <JobProgressCard
          job={job}
          repositoryId={activeJob.result.repository_id}
          pollError={pollError}
          isRefresh={activeJob.isRefresh}
          constrained
        />
      </ProgressWrapper>
    );
  }

  if (isPolling) {
    return (
      <ProgressWrapper>
        <Card className="flex h-full max-h-full flex-col border-dashed">
          <CardContent className="flex flex-1 items-center justify-center gap-3 p-8 text-sm text-muted-foreground">
            <Loader2 className="size-5 animate-spin text-violet-500" />
            Starting {activeJob.isRefresh ? "refresh" : "analysis"} job...
          </CardContent>
        </Card>
      </ProgressWrapper>
    );
  }

  return (
    <div className="flex w-full min-h-0 flex-1 items-center justify-center overflow-hidden">
      <DashboardHero username={username} />
    </div>
  );
}
