"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getJob } from "@/services/jobs";
import type { JobStatusResponse } from "@/types/job";

const POLL_INTERVAL_MS = 1000;
const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED"]);

interface UseJobPollingOptions {
  onTerminal?: () => void;
}

export function useJobPolling(jobId: string | null, options?: UseJobPollingOptions) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onTerminal = options?.onTerminal;

  const clearPollingInterval = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const poll = useCallback(async () => {
    if (!jobId) return;

    try {
      const status = await getJob(jobId);
      setJob(status);
      setError(null);
      if (TERMINAL_STATUSES.has(status.status)) {
        clearPollingInterval();
        setIsPolling(false);
        onTerminal?.();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch job status");
      clearPollingInterval();
      setIsPolling(false);
    }
  }, [jobId, onTerminal, clearPollingInterval]);

  useEffect(() => {
    if (!jobId) {
      clearPollingInterval();
      return;
    }

    let cancelled = false;

    void (async () => {
      if (!cancelled) {
        setIsPolling(true);
      }
      await poll();
    })();

    intervalRef.current = setInterval(() => {
      void poll();
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearPollingInterval();
    };
  }, [jobId, poll, clearPollingInterval]);

  return {
    job: jobId ? job : null,
    error: jobId ? error : null,
    isPolling: jobId ? isPolling : false,
  };
}
