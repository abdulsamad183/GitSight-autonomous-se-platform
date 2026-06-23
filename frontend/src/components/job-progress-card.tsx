"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { CheckCircle2, Loader2, Sparkles } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { JobStatusResponse } from "@/types/job";

interface JobProgressCardProps {
  job: JobStatusResponse;
  repositoryId: string;
  pollError: string | null;
  cached?: boolean;
  compact?: boolean;
  isRefresh?: boolean;
}

const PHASES = [
  { id: "clone", label: "Clone", minProgress: 0 },
  { id: "discover", label: "Discover", minProgress: 12 },
  { id: "analyze", label: "Analyze", minProgress: 15 },
  { id: "complete", label: "Complete", minProgress: 95 },
] as const;

function getActivePhaseIndex(progress: number, status: string): number {
  if (status === "COMPLETED") return 3;
  if (progress >= 95) return 3;
  if (progress >= 15) return 2;
  if (progress >= 12) return 1;
  return 0;
}

export function JobProgressCard({
  job,
  repositoryId,
  pollError,
  cached = false,
  compact = false,
  isRefresh = false,
}: JobProgressCardProps) {
  const router = useRouter();
  const logEndRef = useRef<HTMLDivElement>(null);
  const isFailed = job.status === "FAILED";
  const isCompleted = job.status === "COMPLETED" || cached;
  const noChanges = job.current_stage === "No changes detected";
  const activePhase = getActivePhaseIndex(job.progress, job.status);
  const events = job.events ?? [];

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  useEffect(() => {
    if (isCompleted && repositoryId && !noChanges) {
      const timer = setTimeout(() => {
        router.push(`/repositories/${repositoryId}`);
      }, cached ? 400 : 1200);
      return () => clearTimeout(timer);
    }
  }, [isCompleted, repositoryId, router, cached, noChanges]);

  const title = cached
    ? "Loaded from cache"
    : isRefresh
      ? "Refreshing repository"
      : "Analysis in progress";

  const content = (
    <div className="space-y-4">
      {!cached && (
        <>
          <p className="text-sm font-medium text-foreground">
            {job.current_stage ?? "Waiting..."}
          </p>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">{job.progress}%</span>
            </div>
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isFailed
                    ? "bg-gradient-to-r from-rose-500 to-red-500"
                    : "bg-gradient-to-r from-violet-500 via-indigo-500 to-sky-500"
                }`}
                style={{ width: `${job.progress}%` }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between gap-1">
            {PHASES.map((phase, index) => {
              const isActive = index === activePhase && !isCompleted;
              const isDone = index < activePhase || isCompleted;
              return (
                <div key={phase.id} className="flex flex-1 flex-col items-center gap-1">
                  <div
                    className={`flex size-7 items-center justify-center rounded-full text-xs font-medium ${
                      isDone
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                        : isActive
                          ? "bg-violet-100 text-violet-700 ring-2 ring-violet-400 dark:bg-violet-900/40 dark:text-violet-200"
                          : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {isDone ? <CheckCircle2 className="size-3.5" /> : index + 1}
                  </div>
                  <span className="text-[10px] text-muted-foreground">{phase.label}</span>
                </div>
              );
            })}
          </div>

          {events.length > 0 && (
            <div className="max-h-40 space-y-1 overflow-y-auto rounded-lg border bg-muted/30 p-3">
              {events.map((event, index) => {
                const isLast = index === events.length - 1;
                const isRunning = job.status === "RUNNING" && isLast;
                return (
                  <div key={`${event.created_at}-${index}`} className="flex items-start gap-2 text-xs">
                    {isRunning ? (
                      <Loader2 className="mt-0.5 size-3 shrink-0 animate-spin text-violet-500" />
                    ) : (
                      <CheckCircle2 className="mt-0.5 size-3 shrink-0 text-emerald-500" />
                    )}
                    <span className="text-muted-foreground">{event.message}</span>
                  </div>
                );
              })}
              <div ref={logEndRef} />
            </div>
          )}
        </>
      )}

      {cached && (
        <p className="text-sm text-muted-foreground">
          This repository was already analyzed. Opening saved results from the database...
        </p>
      )}

      {noChanges && isCompleted && (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200">
          All branches match the latest commits on GitHub. No database updates were needed.
        </p>
      )}

      {pollError && <p className="text-sm text-destructive">{pollError}</p>}
      {isFailed && job.error_message && (
        <p className="text-sm text-destructive">{job.error_message}</p>
      )}

      {isCompleted && !noChanges && (
        <a
          href={`/repositories/${repositoryId}`}
          className={buttonVariants({ variant: "default", size: compact ? "sm" : "default" })}
        >
          View Full Analysis
        </a>
      )}
    </div>
  );

  if (compact) {
    return (
      <div className="mt-6 rounded-xl border border-violet-200 bg-violet-50/30 p-4 dark:border-violet-900 dark:bg-violet-950/20">
        <div className="mb-3 flex items-center gap-2">
          {cached ? (
            <Sparkles className="size-4 text-violet-500" />
          ) : (
            <Loader2 className={`size-4 text-violet-500 ${!isCompleted ? "animate-spin" : ""}`} />
          )}
          <p className="text-sm font-semibold">{title}</p>
          {!cached && (
            <span className="ml-auto text-xs text-muted-foreground">{job.status}</span>
          )}
        </div>
        {content}
      </div>
    );
  }

  return (
    <Card className="overflow-hidden border-violet-200 dark:border-violet-900">
      <div className="h-1 bg-gradient-to-r from-violet-500 via-indigo-500 to-sky-500" />
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {cached ? (
            <>
              <Sparkles className="size-5 text-violet-500" />
              {title}
            </>
          ) : (
            title
          )}
        </CardTitle>
        <CardDescription>
          Status:{" "}
          <span className="font-medium text-foreground">
            {cached ? "CACHED" : job.status}
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  );
}
