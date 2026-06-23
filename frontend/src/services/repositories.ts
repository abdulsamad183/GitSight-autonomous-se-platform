import { apiDelete, apiGet, apiPost } from "@/lib/api-client";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  BranchSummary,
  RepositoryDetail,
  RepositoryListItem,
  RepositorySummary,
} from "@/types/repository";

export async function listRepositories(): Promise<RepositoryListItem[]> {
  return apiGet<RepositoryListItem[]>("/api/v1/repositories");
}

export async function analyzeRepository(data: AnalyzeRequest): Promise<AnalyzeResponse> {
  return apiPost<AnalyzeResponse>("/api/v1/repositories/analyze", data);
}

export async function refreshRepository(repositoryId: string): Promise<AnalyzeResponse> {
  return apiPost<AnalyzeResponse>(`/api/v1/repositories/${repositoryId}/refresh`, {});
}

export async function getRepository(repositoryId: string): Promise<RepositorySummary> {
  return apiGet<RepositorySummary>(`/api/v1/repositories/${repositoryId}`);
}

export async function getRepositoryDetails(
  repositoryId: string,
  branch?: string,
): Promise<RepositoryDetail> {
  const query = branch ? `?branch=${encodeURIComponent(branch)}` : "";
  return apiGet<RepositoryDetail>(`/api/v1/repositories/${repositoryId}/details${query}`);
}

export async function listBranches(repositoryId: string): Promise<BranchSummary[]> {
  return apiGet<BranchSummary[]>(`/api/v1/repositories/${repositoryId}/branches`);
}

export async function deleteRepository(repositoryId: string): Promise<void> {
  await apiDelete<void>(`/api/v1/repositories/${repositoryId}`);
}

export async function clearAllRepositories(): Promise<{ deleted_count: number }> {
  return apiDelete<{ deleted_count: number }>("/api/v1/repositories");
}
