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

export interface BlastRadiusNode {
  file_path: string;
  hop: number;
}

export interface BlastRadiusResponse {
  file_path: string;
  direction: "dependents" | "dependencies";
  max_depth: number;
  branch: string | null;
  nodes: BlastRadiusNode[];
  total: number;
  message?: string | null;
  suggested_direction?: "dependents" | "dependencies" | null;
}

export interface GraphPathResponse {
  source_file: string;
  target_file: string;
  max_depth: number;
  branch: string | null;
  paths: string[][];
  total_paths: number;
  bidirectional?: boolean;
  message?: string | null;
}

export interface ImportEdgeItem {
  source_path: string;
  target_path: string;
  dependency_type: string;
}

export interface ImportGraphSummary {
  branch: string | null;
  edges: ImportEdgeItem[];
  connected_files: string[];
  source_files: string[];
  target_files: string[];
  total_edges: number;
}
