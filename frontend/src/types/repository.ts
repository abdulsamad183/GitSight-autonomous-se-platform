export interface AnalyzeRequest {
  github_url: string;
}

export interface AnalyzeResponse {
  repository_id: string;
  job_id: string | null;
  status: string;
  cached: boolean;
}

export interface BranchSummary {
  branch: string;
  commit_hash: string;
  files_count: number;
  classes_count: number;
  functions_count: number;
  methods_count: number;
  dependencies_count: number;
}

export interface RepositorySummary {
  id: string;
  owner: string;
  repository_name: string;
  github_url: string;
  latest_commit_hash: string | null;
  default_branch?: string | null;
  status: string;
  analysis_status: string;
  files_count: number;
  classes_count: number;
  functions_count: number;
  methods_count: number;
  dependencies_count: number;
  branches_count: number;
  branches_truncated: boolean;
  available_branches: string[];
}

export interface RepositoryListItem {
  id: string;
  owner: string;
  repository_name: string;
  github_url: string;
  latest_commit_hash: string | null;
  default_branch?: string | null;
  status: string;
  analysis_status: string;
  files_count: number;
  branches_count: number;
  branches_truncated: boolean;
  updated_at: string;
}

export interface FileItem {
  id: string;
  relative_path: string;
  file_name: string;
  extension: string | null;
  language: string | null;
  size_bytes: number;
  is_binary: boolean;
}

export interface SymbolItem {
  symbol_name: string;
  symbol_type: string;
  file_path: string;
  start_line: number;
  end_line: number;
  signature: string | null;
}

export interface DependencyItem {
  source_path: string;
  target_path: string;
  dependency_type: string;
}

export interface RepositoryDetail extends RepositorySummary {
  selected_branch: string | null;
  files: FileItem[];
  symbols: SymbolItem[];
  dependencies: DependencyItem[];
}
