"use client";

import type { GraphNodeType } from "@/types/graph";
import { cn } from "@/lib/utils";

const typeLabels: Record<GraphNodeType, string> = {
  repository: "Repository",
  file: "File",
  class: "Class",
  method: "Method",
};

const themes: Record<
  GraphNodeType,
  { header: string; chip: string; dot: string }
> = {
  repository: {
    header: "from-violet-600 via-indigo-600 to-sky-500",
    chip: "bg-violet-100 text-violet-700",
    dot: "bg-violet-500",
  },
  file: {
    header: "from-sky-500 via-cyan-500 to-teal-400",
    chip: "bg-sky-100 text-sky-700",
    dot: "bg-sky-500",
  },
  class: {
    header: "from-indigo-500 via-violet-500 to-purple-500",
    chip: "bg-indigo-100 text-indigo-700",
    dot: "bg-indigo-500",
  },
  method: {
    header: "from-fuchsia-500 via-violet-500 to-indigo-500",
    chip: "bg-fuchsia-100 text-fuchsia-700",
    dot: "bg-fuchsia-500",
  },
};

interface GraphNodeHoverCardProps {
  label: string;
  nodeType: GraphNodeType;
  metadata: Record<string, string | number | null | undefined>;
  branch?: string | null;
}

function DetailChip({
  label,
  value,
  chipClass,
}: {
  label: string;
  value: string | number | null | undefined;
  chipClass: string;
}) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className={cn("rounded-lg px-2.5 py-1.5", chipClass)}>
      <p className="text-[10px] font-semibold uppercase tracking-wider opacity-70">{label}</p>
      <p className="mt-0.5 max-w-[220px] truncate text-xs font-medium">{value}</p>
    </div>
  );
}

export function GraphNodeHoverCard({
  label,
  nodeType,
  metadata,
  branch,
}: GraphNodeHoverCardProps) {
  const theme = themes[nodeType];
  const meta = metadata;

  return (
    <div className="pointer-events-none w-64 overflow-hidden rounded-2xl border border-white/80 bg-white shadow-2xl shadow-violet-200/60 backdrop-blur-xl">
      <div className={cn("bg-gradient-to-r px-3 py-2.5 text-white", theme.header)}>
        <div className="flex items-center gap-2">
          <span className={cn("size-2 rounded-full bg-white/90 shadow-sm", theme.dot)} />
          <span className="text-[10px] font-bold uppercase tracking-widest text-white/90">
            {typeLabels[nodeType]}
          </span>
        </div>
        <p className="mt-1 truncate text-sm font-semibold">{label}</p>
      </div>

      <div className="grid grid-cols-2 gap-1.5 p-2">
        {nodeType === "repository" && (
          <>
            <DetailChip label="Branch" value={branch} chipClass={theme.chip} />
            <DetailChip label="Files" value={meta.files_count as number} chipClass={theme.chip} />
            <DetailChip label="Classes" value={meta.classes_count as number} chipClass={theme.chip} />
            <DetailChip label="Methods" value={meta.methods_count as number} chipClass={theme.chip} />
            <div className={cn("col-span-2 rounded-lg px-2.5 py-1.5", theme.chip)}>
              <p className="text-[10px] font-semibold uppercase tracking-wider opacity-70">GitHub</p>
              <p className="mt-0.5 truncate text-xs font-medium">{meta.github_url as string}</p>
            </div>
          </>
        )}

        {nodeType === "file" && (
          <>
            <DetailChip label="Language" value={meta.language as string} chipClass={theme.chip} />
            <DetailChip
              label="Classes"
              value={meta.classes_count as number}
              chipClass={theme.chip}
            />
            <DetailChip
              label="Methods"
              value={meta.methods_count as number}
              chipClass={theme.chip}
            />
            <div className={cn("col-span-2 rounded-lg px-2.5 py-1.5", theme.chip)}>
              <p className="text-[10px] font-semibold uppercase tracking-wider opacity-70">Path</p>
              <p className="mt-0.5 break-all text-xs font-medium">{meta.path as string}</p>
            </div>
          </>
        )}

        {nodeType === "class" && (
          <>
            <DetailChip
              label="Methods"
              value={meta.method_count as number}
              chipClass={theme.chip}
            />
            <DetailChip label="Start" value={meta.start_line as number} chipClass={theme.chip} />
            <DetailChip label="End" value={meta.end_line as number} chipClass={theme.chip} />
            <div className={cn("col-span-2 rounded-lg px-2.5 py-1.5", theme.chip)}>
              <p className="text-[10px] font-semibold uppercase tracking-wider opacity-70">File</p>
              <p className="mt-0.5 break-all text-xs font-medium">{meta.file_path as string}</p>
            </div>
          </>
        )}

        {nodeType === "method" && (
          <>
            <DetailChip
              label="Class"
              value={meta.parent_class as string}
              chipClass={theme.chip}
            />
            <DetailChip label="Start" value={meta.start_line as number} chipClass={theme.chip} />
            <DetailChip label="End" value={meta.end_line as number} chipClass={theme.chip} />
            <div className={cn("col-span-2 rounded-lg px-2.5 py-1.5", theme.chip)}>
              <p className="text-[10px] font-semibold uppercase tracking-wider opacity-70">File</p>
              <p className="mt-0.5 break-all text-xs font-medium">{meta.file_path as string}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
