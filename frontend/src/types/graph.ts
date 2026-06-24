export type GraphNodeType = "repository" | "file" | "class" | "method";

export interface GraphNode {
  id: string;
  type: GraphNodeType;
  label: string;
  metadata: Record<string, string | number | null | undefined>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
}

export interface GraphStats {
  files_count: number;
  classes_count: number;
  methods_count: number;
  functions_count: number;
}

export interface RepositoryGraph {
  graph_type: string;
  branch: string | null;
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: GraphStats;
  empty_state: string | null;
}
