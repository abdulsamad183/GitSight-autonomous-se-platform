"use client";

import { FileText, FolderTree, HardDrive } from "lucide-react";

import type { FileDistribution } from "@/types/repository";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface RepositoryFileDistributionProps {
  distribution: FileDistribution;
}

function BreakdownList({
  title,
  items,
  valueSuffix = "",
}: {
  title: string;
  items: Array<[string, number]>;
  valueSuffix?: string;
}) {
  if (items.length === 0) return null;
  const max = Math.max(...items.map(([, count]) => count), 1);

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
      <h3 className="text-sm font-semibold">{title}</h3>
      <ul className="mt-3 space-y-2">
        {items.map(([label, count]) => (
          <li key={label}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="font-medium">{label}</span>
              <span className="tabular-nums text-muted-foreground">
                {count}
                {valueSuffix}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-violet-500"
                style={{ width: `${(count / max) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RepositoryFileDistribution({ distribution }: RepositoryFileDistributionProps) {
  const languageItems = Object.entries(distribution.language_breakdown);
  const extensionItems = Object.entries(distribution.extension_breakdown).slice(0, 8);

  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-base font-semibold">File Distribution</h2>
        <p className="text-sm text-muted-foreground">
          Language mix, extensions, largest files, and top-level folders from indexed metadata
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <FileText className="size-4" />
            Files
          </div>
          <p className="mt-2 text-2xl font-semibold tabular-nums">{distribution.total_files}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {distribution.text_files} text · {distribution.binary_files} binary
          </p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <HardDrive className="size-4" />
            Total size
          </div>
          <p className="mt-2 text-2xl font-semibold tabular-nums">
            {formatBytes(distribution.total_size_bytes)}
          </p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <FolderTree className="size-4" />
            Top folders
          </div>
          <p className="mt-2 text-2xl font-semibold tabular-nums">
            {distribution.largest_folders.length}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">By total file size</p>
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <BreakdownList
          title="Languages"
          items={languageItems.map(([language, count]) => [
            `${language} (${distribution.language_percentages[language] ?? 0}%)`,
            count,
          ])}
        />
        <BreakdownList title="Extensions" items={extensionItems} />
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <h3 className="text-sm font-semibold">Largest files</h3>
          <ul className="mt-3 space-y-2 text-sm">
            {distribution.largest_files.map((file) => (
              <li
                key={file.relative_path}
                className="flex items-start justify-between gap-3 rounded-lg bg-muted/30 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="truncate font-mono text-xs">{file.relative_path}</p>
                  <p className="text-xs text-muted-foreground">
                    {[file.language, file.extension?.replace(".", ""), file.is_binary ? "binary" : "text"]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                </div>
                <span className="shrink-0 tabular-nums text-xs font-medium">
                  {formatBytes(file.size_bytes)}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <h3 className="text-sm font-semibold">Largest folders</h3>
          <ul className="mt-3 space-y-2 text-sm">
            {distribution.largest_folders.map((folder) => (
              <li
                key={folder.folder_path}
                className="flex items-center justify-between gap-3 rounded-lg bg-muted/30 px-3 py-2"
              >
                <div>
                  <p className="font-medium">{folder.folder_path}</p>
                  <p className="text-xs text-muted-foreground">
                    {folder.file_count} file{folder.file_count === 1 ? "" : "s"}
                  </p>
                </div>
                <span className="tabular-nums text-xs font-medium">
                  {formatBytes(folder.total_size_bytes)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
