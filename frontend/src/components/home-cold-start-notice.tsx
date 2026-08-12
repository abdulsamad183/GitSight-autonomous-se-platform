"use client";

import { useEffect } from "react";
import { Clock } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";
import { getVersion } from "@/services/health";

export function HomeColdStartNotice() {
  const { isLoading } = useAuth();

  useEffect(() => {
    // Lightweight wake ping alongside auth /me (proxied under /api/*).
    void getVersion().catch(() => {});
  }, []);

  return (
    <div className="mt-6 w-full max-w-lg text-left">
      <div className="flex gap-3 rounded-xl border border-amber-200/90 bg-amber-50/90 px-4 py-3">
        <Clock className="mt-0.5 size-4 shrink-0 text-amber-700" aria-hidden />
        <div className="space-y-1.5">
          <p className="text-sm font-medium text-amber-950">Demo hosting note</p>
          <p className="text-sm leading-relaxed text-amber-900/90">
            The API runs on Render&apos;s free tier and sleeps when idle. After inactivity, the first
            visit can take about <span className="font-medium text-amber-950">30–60 seconds</span>{" "}
            while the server wakes. Please wait once — then Sign in / Register should respond
            normally.
          </p>
          {isLoading ? (
            <p className="text-sm font-medium text-amber-950" aria-live="polite">
              Waking the API…
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
