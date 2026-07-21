"use client";

import { Loader2, Route, Target } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getGraphBlastRadius, getGraphPath } from "@/services/repositories";
import type { BlastRadiusResponse, GraphPathResponse } from "@/types/graph";

interface GraphImpactToolsProps {
  repositoryId: string;
  branch?: string | null;
  filePaths: string[];
}

type ToolMode = "blast" | "path";

export function GraphImpactTools({ repositoryId, branch, filePaths }: GraphImpactToolsProps) {
  const [mode, setMode] = useState<ToolMode>("blast");
  const [filePath, setFilePath] = useState("");
  const [direction, setDirection] = useState<"dependents" | "dependencies">("dependents");
  const [maxDepth, setMaxDepth] = useState(3);
  const [sourceFile, setSourceFile] = useState("");
  const [targetFile, setTargetFile] = useState("");
  const [pathDepth, setPathDepth] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blastResult, setBlastResult] = useState<BlastRadiusResponse | null>(null);
  const [pathResult, setPathResult] = useState<GraphPathResponse | null>(null);

  const datalistId = "graph-impact-file-paths";
  const sortedPaths = useMemo(() => [...filePaths].sort(), [filePaths]);

  const runBlast = async () => {
    if (!filePath.trim()) return;
    setLoading(true);
    setError(null);
    setPathResult(null);
    try {
      const result = await getGraphBlastRadius(repositoryId, {
        file_path: filePath.trim(),
        direction,
        max_depth: maxDepth,
        branch: branch ?? undefined,
      });
      setBlastResult(result);
    } catch (err) {
      setBlastResult(null);
      setError(err instanceof Error ? err.message : "Blast radius failed");
    } finally {
      setLoading(false);
    }
  };

  const runPath = async () => {
    if (!sourceFile.trim() || !targetFile.trim()) return;
    setLoading(true);
    setError(null);
    setBlastResult(null);
    try {
      const result = await getGraphPath(repositoryId, {
        source_file: sourceFile.trim(),
        target_file: targetFile.trim(),
        max_depth: pathDepth,
        branch: branch ?? undefined,
      });
      setPathResult(result);
    } catch (err) {
      setPathResult(null);
      setError(err instanceof Error ? err.message : "Path finder failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="shrink-0 space-y-3 rounded-xl border bg-card p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold">Impact tools</h2>
          <p className="text-xs text-muted-foreground">
            Blast radius and import path finder using indexed dependency edges
          </p>
        </div>
        <div className="flex gap-1 rounded-lg border bg-muted/40 p-1">
          <button
            type="button"
            onClick={() => setMode("blast")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium ${
              mode === "blast" ? "bg-background shadow-sm" : "text-muted-foreground"
            }`}
          >
            <Target className="size-3.5" />
            Blast radius
          </button>
          <button
            type="button"
            onClick={() => setMode("path")}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium ${
              mode === "path" ? "bg-background shadow-sm" : "text-muted-foreground"
            }`}
          >
            <Route className="size-3.5" />
            Path finder
          </button>
        </div>
      </div>

      <datalist id={datalistId}>
        {sortedPaths.map((path) => (
          <option key={path} value={path} />
        ))}
      </datalist>

      {mode === "blast" ? (
        <div className="grid gap-2 sm:grid-cols-[1fr_auto_auto_auto]">
          <Input
            list={datalistId}
            value={filePath}
            onChange={(event) => setFilePath(event.target.value)}
            placeholder="File path (e.g. src/auth.py)"
            aria-label="Blast radius file path"
          />
          <select
            value={direction}
            onChange={(event) =>
              setDirection(event.target.value as "dependents" | "dependencies")
            }
            className="h-9 rounded-md border bg-background px-3 text-sm"
            aria-label="Blast radius direction"
          >
            <option value="dependents">Dependents (who imports this)</option>
            <option value="dependencies">Dependencies (what this imports)</option>
          </select>
          <select
            value={maxDepth}
            onChange={(event) => setMaxDepth(Number(event.target.value))}
            className="h-9 rounded-md border bg-background px-3 text-sm"
            aria-label="Blast radius depth"
          >
            {[1, 2, 3, 4, 5].map((depth) => (
              <option key={depth} value={depth}>
                Depth {depth}
              </option>
            ))}
          </select>
          <Button type="button" onClick={() => void runBlast()} disabled={loading || !filePath.trim()}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : "Analyze"}
          </Button>
        </div>
      ) : (
        <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto_auto]">
          <Input
            list={datalistId}
            value={sourceFile}
            onChange={(event) => setSourceFile(event.target.value)}
            placeholder="Source file"
            aria-label="Path finder source file"
          />
          <Input
            list={datalistId}
            value={targetFile}
            onChange={(event) => setTargetFile(event.target.value)}
            placeholder="Target file"
            aria-label="Path finder target file"
          />
          <select
            value={pathDepth}
            onChange={(event) => setPathDepth(Number(event.target.value))}
            className="h-9 rounded-md border bg-background px-3 text-sm"
            aria-label="Path finder depth"
          >
            {[2, 3, 4, 5, 6, 7, 8].map((depth) => (
              <option key={depth} value={depth}>
                Depth {depth}
              </option>
            ))}
          </select>
          <Button
            type="button"
            onClick={() => void runPath()}
            disabled={loading || !sourceFile.trim() || !targetFile.trim()}
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : "Find paths"}
          </Button>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </div>
      )}

      {blastResult && mode === "blast" && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">
            {blastResult.total} file{blastResult.total === 1 ? "" : "s"} within {blastResult.max_depth}{" "}
            hop{blastResult.max_depth === 1 ? "" : "s"} ({blastResult.direction})
          </p>
          {blastResult.total === 0 ? (
            <p className="rounded-lg border border-dashed px-3 py-4 text-sm text-muted-foreground">
              No related files found for this path and depth.
            </p>
          ) : (
            <ul className="max-h-48 space-y-1 overflow-y-auto rounded-lg border p-2 text-sm">
              {blastResult.nodes.map((node) => (
                <li
                  key={`${node.hop}-${node.file_path}`}
                  className="flex items-center justify-between gap-3 rounded-md bg-muted/40 px-3 py-1.5"
                >
                  <span className="truncate font-mono text-xs">{node.file_path}</span>
                  <span className="shrink-0 rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-semibold text-violet-800">
                    hop {node.hop}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {pathResult && mode === "path" && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">
            {pathResult.total_paths} path{pathResult.total_paths === 1 ? "" : "s"} found (max depth{" "}
            {pathResult.max_depth})
          </p>
          {pathResult.total_paths === 0 ? (
            <p className="rounded-lg border border-dashed px-3 py-4 text-sm text-muted-foreground">
              No import path between these files within the depth limit.
            </p>
          ) : (
            <ul className="max-h-48 space-y-2 overflow-y-auto rounded-lg border p-2 text-sm">
              {pathResult.paths.map((path, index) => (
                <li key={`${index}-${path.join(">")}`} className="rounded-md bg-muted/40 px-3 py-2">
                  <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                    Path {index + 1}
                  </p>
                  <p className="font-mono text-xs leading-relaxed">{path.join(" → ")}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
