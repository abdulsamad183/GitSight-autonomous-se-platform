import { apiDelete, apiGet, apiPost } from "@/lib/api-client";
import type { RepositoryGraph } from "@/types/graph";
import type { ChatRequest, ChatResponse, ChatSource, ChatStreamEvent } from "@/types/chat";
import type { SearchParams, SearchResponse, ChunkDetail } from "@/types/search";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  BranchSummary,
  PullRequestListItem,
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

export async function listPullRequests(repositoryId: string): Promise<PullRequestListItem[]> {
  return apiGet<PullRequestListItem[]>(`/api/v1/repositories/${repositoryId}/pull-requests`);
}

export async function getRepositoryGraph(
  repositoryId: string,
  branch?: string,
  graphType = "structure",
): Promise<RepositoryGraph> {
  const params = new URLSearchParams();
  if (branch) params.set("branch", branch);
  if (graphType !== "structure") params.set("type", graphType);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiGet<RepositoryGraph>(`/api/v1/repositories/${repositoryId}/graph${query}`);
}

export async function deleteRepository(repositoryId: string): Promise<void> {
  await apiDelete<void>(`/api/v1/repositories/${repositoryId}`);
}

export async function clearAllRepositories(): Promise<{ deleted_count: number }> {
  return apiDelete<{ deleted_count: number }>("/api/v1/repositories");
}

export async function searchRepository(
  repositoryId: string,
  params: SearchParams,
): Promise<SearchResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set("q", params.q);
  if (params.mode) searchParams.set("mode", params.mode);
  if (params.limit !== undefined) searchParams.set("limit", String(params.limit));
  if (params.offset !== undefined) searchParams.set("offset", String(params.offset));
  if (params.branch) searchParams.set("branch", params.branch);
  return apiGet<SearchResponse>(
    `/api/v1/repositories/${repositoryId}/search?${searchParams.toString()}`,
  );
}

export async function getRepositoryChunk(
  repositoryId: string,
  chunkId: string,
): Promise<ChunkDetail> {
  return apiGet<ChunkDetail>(`/api/v1/repositories/${repositoryId}/chunks/${chunkId}`);
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function chatRepository(
  repositoryId: string,
  body: ChatRequest,
): Promise<ChatResponse> {
  return apiPost<ChatResponse>(`/api/v1/repositories/${repositoryId}/chat`, body);
}

interface StreamChatOptions {
  message: string;
  branch?: string;
  onToken: (token: string) => void;
  onToolStart?: (tool: string, label: string) => void;
  onToolEnd?: (tool: string, success: boolean) => void;
  onDone: (sources: ChatSource[]) => void;
  onError: (message: string) => void;
}

export async function streamChatRepository(
  repositoryId: string,
  options: StreamChatOptions,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/repositories/${repositoryId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    credentials: "include",
    body: JSON.stringify({
      message: options.message,
      branch: options.branch,
      stream: true,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") message = data.detail;
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Streaming not supported");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const payload = JSON.parse(line.slice(5).trim()) as ChatStreamEvent;
      if (payload.type === "token") {
        options.onToken(payload.content);
      } else if (payload.type === "tool_start") {
        options.onToolStart?.(payload.tool, payload.label);
      } else if (payload.type === "tool_end") {
        options.onToolEnd?.(payload.tool, payload.success);
      } else if (payload.type === "done") {
        options.onDone(payload.sources ?? []);
      } else if (payload.type === "error") {
        options.onError(payload.message);
      }
    }
  }
}
