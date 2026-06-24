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
  total_pull_requests: number;
  open_pull_requests: number;
  closed_pull_requests: number;
  merged_pull_requests: number;
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
  total_pull_requests: number;
  open_pull_requests: number;
  closed_pull_requests: number;
  merged_pull_requests: number;
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

export interface PullRequestListItem {
  number: number;
  title: string;
  state: "OPEN" | "CLOSED" | "MERGED";
  author: string;
  is_merged: boolean;
  is_draft: boolean;
  source_branch: string | null;
  target_branch: string | null;
  html_url: string | null;
  github_created_at: string | null;
  github_updated_at: string | null;
  description?: string | null;
  github_closed_at?: string | null;
  github_merged_at?: string | null;
  last_synced_at?: string | null;
}

export interface RepositoryDetail extends RepositorySummary {
  selected_branch: string | null;
  files: FileItem[];
  symbols: SymbolItem[];
  dependencies: DependencyItem[];
}
