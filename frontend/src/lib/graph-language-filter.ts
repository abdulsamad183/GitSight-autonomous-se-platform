import type { GraphEdge, GraphNode, RepositoryGraph } from "@/types/graph";

function nodeLanguage(node: GraphNode): string | null {
  const value = node.metadata.language;
  if (typeof value !== "string" || !value.trim()) {
    return null;
  }
  return value.trim().toLowerCase();
}

export function listGraphLanguages(graph: RepositoryGraph): string[] {
  const languages = new Set<string>();
  for (const node of graph.nodes) {
    const language = nodeLanguage(node);
    if (language) languages.add(language);
  }
  return Array.from(languages).sort();
}

export function filterGraphByLanguage(
  graph: RepositoryGraph,
  language: string | null,
): RepositoryGraph {
  const selected = language?.trim().toLowerCase() || null;
  if (!selected) {
    return graph;
  }

  const matchingIds = new Set(
    graph.nodes
      .filter((node) => node.type !== "repository" && nodeLanguage(node) === selected)
      .map((node) => node.id),
  );

  const keepIds = new Set(matchingIds);
  for (const node of graph.nodes) {
    if (node.type === "repository") {
      keepIds.add(node.id);
    }
  }

  // Keep parents of matching nodes so the filtered subgraph stays connected.
  let changed = true;
  while (changed) {
    changed = false;
    for (const edge of graph.edges) {
      if (keepIds.has(edge.target) && !keepIds.has(edge.source)) {
        keepIds.add(edge.source);
        changed = true;
      }
    }
  }

  const nodes: GraphNode[] = graph.nodes.filter((node) => keepIds.has(node.id));
  const edges: GraphEdge[] = graph.edges.filter(
    (edge) => keepIds.has(edge.source) && keepIds.has(edge.target),
  );

  return {
    ...graph,
    nodes,
    edges,
  };
}
