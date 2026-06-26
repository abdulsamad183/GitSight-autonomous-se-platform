"use client";

import { GitSightLogo } from "@/components/gitsight-logo";

interface DashboardHeroProps {
  username?: string;
}

export function DashboardHero({ username }: DashboardHeroProps) {
  return (
    <div className="flex w-full flex-col items-center justify-center text-center">
      <GitSightLogo height={110} className="mb-6" />
      <h1 className="text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
        {username ? `Welcome back, ${username}` : "Welcome back"}
      </h1>
      <p className="mt-3 max-w-md text-sm text-slate-600 sm:text-base">
        Paste a GitHub URL below to analyze your repository.
      </p>
    </div>
  );
}
