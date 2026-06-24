export interface SearchResult {
  chunk_id: string;
  symbol_name: string;
  file_path: string;
  chunk_type: string;
  content_snippet: string;
  keyword_score: number | null;
  semantic_score: number | null;
  final_score: number | null;
  start_line: number;
  end_line: number;
  branch_name: string;
}

export interface SearchResponse {
  query: string;
  mode: string;
  total_results: number;
  limit: number;
  offset: number;
  execution_time_ms: number;
  results: SearchResult[];
}

export type SearchMode = "keyword" | "semantic" | "hybrid";

export interface SearchParams {
  q: string;
  mode?: SearchMode;
  limit?: number;
  offset?: number;
  branch?: string;
}

export interface ChunkDetail {
  id: string;
  repository_id: string;
  branch_name: string;
  file_path: string;
  chunk_type: string;
  symbol_name: string;
  parent_symbol: string | null;
  start_line: number;
  end_line: number;
  content: string;
  content_hash: string;
  created_at: string;
  updated_at: string;
}
