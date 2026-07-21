"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeftRight, Loader2, Route, Target } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getGraphBlastRadius,
  getGraphImportSummary,
  getGraphPath,
} from "@/services/repositories";
import type {
  BlastRadiusResponse,
  GraphPathResponse,
  ImportGraphSummary,
} from "@/types/graph";

interface GraphImpactToolsProps {
  repositoryId: string;
  branch?: string | null;
  /** Fallback when import summary is still loading or unavailable */
  filePaths?: string[];
}

type ToolMode = "blast" | "path";

function suggestDirection(
  path: string,
  summary: ImportGraphSummary | null | undefined,
): "dependents" | "dependencies" {
  if (!summary || !path) return "dependents";
  const isSource = summary.source_files.includes(path);
  const isTarget = summary.target_files.includes(path);
  if (isTarget && !isSource) return "dependents";
  if (isSource && !isTarget) return "dependencies";
  return "dependents";
}

export function GraphImpactTools({
  repositoryId,
  branch,
  filePaths = [],
}: GraphImpactToolsProps) {
  const [mode, setMode] = useState<ToolMode>("blast");
  const [filePath, setFilePath] = useState("");
  const [direction, setDirection] = useState<"dependents" | "dependencies">("dependents");
  const [maxDepth, setMaxDepth] = useState(3);
  const [sourceFile, setSourceFile] = useState("");
  const [targetFile, setTargetFile] = useState("");
  const [pathDepth, setPathDepth] = useState(5);
  const [bidirectional, setBidirectional] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blastResult, setBlastResult] = useState<BlastRadiusResponse | null>(null);
  const [pathResult, setPathResult] = useState<GraphPathResponse | null>(null);

  const summaryQuery = useQuery({
    queryKey: ["graph-import-summary", repositoryId, branch ?? null],
    queryFn: () =>
      getGraphImportSummary(repositoryId, {
        branch: branch ?? undefined,
        edge_limit: 12,
      }),
    enabled: Boolean(repositoryId),
  });
  const summary = summaryQuery.data ?? null;
  const summaryLoading = summaryQuery.isLoading || summaryQuery.isFetching;

  const connectedPaths = useMemo(() => {
    if (summary?.connected_files.length) return summary.connected_files;
    return [...filePaths].sort();
  }, [summary, filePaths]);

  const datalistId = "graph-impact-file-paths";

  const onBlastFileChange = (value: string) => {
    setFilePath(value);
    if (summary?.connected_files.includes(value)) {
      setDirection(suggestDirection(value, summary));
    }
  };

  const fillFromEdge = (source: string, target: string) => {
    if (mode === "blast") {
      onBlastFileChange(target);
    } else {
      setSourceFile(source);
      setTargetFile(target);
    }
  };

  const swapPathFiles = () => {
    setSourceFile(targetFile);
    setTargetFile(sourceFile);
    setPathResult(null);
  };

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
        bidirectional,
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
            {summary && !summaryLoading
              ? ` · ${summary.total_edges} edge${summary.total_edges === 1 ? "" : "s"}`
              : ""}
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
        {connectedPaths.map((path) => (
          <option key={path} value={path} />
        ))}
      </datalist>

      {summary && summary.edges.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Sample import edges — click to fill
          </p>
          <ul className="flex max-h-24 flex-wrap gap-1.5 overflow-y-auto">
            {summary.edges.map((edge) => (
              <li key={`${edge.source_path}->${edge.target_path}`}>
                <button
                  type="button"
                  onClick={() => fillFromEdge(edge.source_path, edge.target_path)}
                  className="rounded-md border bg-muted/30 px-2 py-1 font-mono text-[10px] text-left hover:bg-muted/60"
                  title={
                    mode === "blast"
                      ? `Analyze ${edge.target_path}`
                      : `Path ${edge.source_path} → ${edge.target_path}`
                  }
                >
                  <span className="text-sky-700">{edge.source_path}</span>
                  <span className="mx-1 text-muted-foreground">→</span>
                  <span className="text-amber-800">{edge.target_path}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!summaryLoading && summary?.total_edges === 0 && (
        <p className="rounded-lg border border-dashed px-3 py-2 text-xs text-muted-foreground">
          No import dependency edges indexed for this branch yet. Re-index the repository after
          parsing completes.
        </p>
      )}

      {mode === "blast" ? (
        <div className="grid gap-2 sm:grid-cols-[1fr_auto_auto_auto]">
          <Input
            list={datalistId}
            value={filePath}
            onChange={(event) => onBlastFileChange(event.target.value)}
            placeholder="Connected file path (suggestions from import graph)"
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
        <div className="space-y-2">
          <div className="grid gap-2 sm:grid-cols-[1fr_auto_1fr_auto_auto]">
            <Input
              list={datalistId}
              value={sourceFile}
              onChange={(event) => setSourceFile(event.target.value)}
              placeholder="Source (importer)"
              aria-label="Path finder source file"
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={swapPathFiles}
              aria-label="Swap source and target"
              title="Swap source and target"
            >
              <ArrowLeftRight className="size-4" />
            </Button>
            <Input
              list={datalistId}
              value={targetFile}
              onChange={(event) => setTargetFile(event.target.value)}
              placeholder="Target (imported)"
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
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={bidirectional}
              onChange={(event) => setBidirectional(event.target.checked)}
              className="size-3.5 rounded border"
            />
            Also search reverse (if no forward import path)
          </label>
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
            <div className="space-y-2 rounded-lg border border-dashed px-3 py-4 text-sm text-muted-foreground">
              <p>{blastResult.message ?? "No related files found for this path and depth."}</p>
              {blastResult.suggested_direction && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setDirection(blastResult.suggested_direction!);
                    setBlastResult(null);
                  }}
                >
                  Switch to {blastResult.suggested_direction}
                </Button>
              )}
            </div>
          ) : (
            <ul className="max-h-48 space-y-1 overflow-y-auto rounded-lg border p-2 text-sm">
              {blastResult.nodes.map((node) => (
                <li
                  key={`${node.hop}-${node.file_path}`}
                  className="flex items-center justify-between gap-3 rounded-md bg-muted/40 px-3 py-1.5"
                >
                  <button
                    type="button"
                    className="truncate font-mono text-xs text-left hover:underline"
                    onClick={() => onBlastFileChange(node.file_path)}
                  >
                    {node.file_path}
                  </button>
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
            {pathResult.max_depth}
            {pathResult.bidirectional ? ", reverse allowed" : ""})
          </p>
          {pathResult.total_paths === 0 ? (
            <p className="rounded-lg border border-dashed px-3 py-4 text-sm text-muted-foreground">
              {pathResult.message ?? "No import path between these files within the depth limit."}
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
