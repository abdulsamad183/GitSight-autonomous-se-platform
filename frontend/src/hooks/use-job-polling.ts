"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getJob } from "@/services/jobs";
import type { JobStatusResponse } from "@/types/job";

const POLL_INTERVAL_MS = 1000;
const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED"]);

export function useJobPolling(jobId: string | null) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const poll = useCallback(async () => {
    if (!jobId) return;

    try {
      const status = await getJob(jobId);
      setJob(status);
      setError(null);
      if (TERMINAL_STATUSES.has(status.status)) {
        stopPolling();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch job status");
      stopPolling();
    }
  }, [jobId, stopPolling]);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      setError(null);
      stopPolling();
      return;
    }

    setIsPolling(true);
    void poll();
    intervalRef.current = setInterval(() => {
      void poll();
    }, POLL_INTERVAL_MS);

    return () => {
      stopPolling();
    };
  }, [jobId, poll, stopPolling]);

  return { job, error, isPolling };
}
