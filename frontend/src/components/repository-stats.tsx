"use client";

import {
  Box,
  FileCode2,
  FunctionSquare,
  GitBranch,
  GitCommit,
  Link2,
  Workflow,
} from "lucide-react";

const STAT_CONFIG = [
  {
    key: "files",
    label: "Files",
    icon: FileCode2,
    gradient: "from-blue-500 to-cyan-500",
    bg: "bg-blue-50 dark:bg-blue-950/30",
  },
  {
    key: "classes",
    label: "Classes",
    icon: Box,
    gradient: "from-violet-500 to-purple-500",
    bg: "bg-violet-50 dark:bg-violet-950/30",
  },
  {
    key: "functions",
    label: "Functions",
    icon: FunctionSquare,
    gradient: "from-emerald-500 to-teal-500",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
  },
  {
    key: "methods",
    label: "Methods",
    icon: Workflow,
    gradient: "from-amber-500 to-orange-500",
    bg: "bg-amber-50 dark:bg-amber-950/30",
  },
  {
    key: "dependencies",
    label: "Dependencies",
    icon: Link2,
    gradient: "from-rose-500 to-pink-500",
    bg: "bg-rose-50 dark:bg-rose-950/30",
  },
] as const;

interface RepositoryStatsGridProps {
  files_count: number;
  classes_count: number;
  functions_count: number;
  methods_count: number;
  dependencies_count: number;
}

export function RepositoryStatsGrid(props: RepositoryStatsGridProps) {
  const values: Record<string, number> = {
    files: props.files_count,
    classes: props.classes_count,
    functions: props.functions_count,
    methods: props.methods_count,
    dependencies: props.dependencies_count,
  };

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      {STAT_CONFIG.map(({ key, label, icon: Icon, gradient, bg }) => (
        <div
          key={key}
          className={`relative overflow-hidden rounded-2xl border p-5 shadow-sm ${bg}`}
        >
          <div
            className={`absolute -right-4 -top-4 size-20 rounded-full bg-gradient-to-br opacity-20 ${gradient}`}
          />
          <div className={`inline-flex rounded-lg bg-gradient-to-br p-2 text-white ${gradient}`}>
            <Icon className="size-5" />
          </div>
          <p className="mt-4 text-3xl font-bold tracking-tight">{values[key]}</p>
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
        </div>
      ))}
    </div>
  );
}

interface RepositoryHeroProps {
  owner: string;
  repository_name: string;
  github_url: string;
  latest_commit_hash: string | null;
  default_branch?: string | null;
  analysis_status: string;
}

export function RepositoryHero({
  owner,
  repository_name,
  github_url,
  latest_commit_hash,
  default_branch,
  analysis_status,
}: RepositoryHeroProps) {
  const isComplete = analysis_status === "COMPLETED";

  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-violet-600 via-indigo-600 to-sky-600 p-8 text-white shadow-xl">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.2),transparent_50%)]" />
      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-violet-100">Repository Analysis</p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight sm:text-4xl">
              {owner}/{repository_name}
            </h1>
          </div>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              isComplete ? "bg-emerald-400/20 text-emerald-100" : "bg-white/20 text-white"
            }`}
          >
            {analysis_status}
          </span>
        </div>

        <div className="mt-6 flex flex-wrap gap-4 text-sm text-violet-100">
          <a
            href={github_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-3 py-1.5 transition hover:bg-white/20"
          >
            <GitBranch className="size-4" />
            View on GitHub
          </a>
          {default_branch && (
            <span className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-3 py-1.5">
              <GitBranch className="size-4" />
              {default_branch}
            </span>
          )}
          {latest_commit_hash && (
            <span className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-3 py-1.5 font-mono text-xs">
              <GitCommit className="size-4" />
              {latest_commit_hash.slice(0, 12)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
