export interface ChatRequest {
  message: string;
  branch?: string | null;
  stream?: boolean;
}

export interface ChatSource {
  chunk_id: string;
  file_path: string;
  symbol_name: string;
  chunk_type: string;
  branch_name?: string | null;
}

export interface ChatTiming {
  retrieval_ms: number;
  prompt_build_ms: number;
  llm_ms: number;
  total_ms: number;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  execution_time_ms: number;
  timing: ChatTiming;
  token_usage?: TokenUsage | null;
}

export interface ChatStreamTokenEvent {
  type: "token";
  content: string;
}

export interface ChatStreamDoneEvent {
  type: "done";
  sources: ChatSource[];
  execution_time_ms: number;
  timing?: ChatTiming | null;
  token_usage?: TokenUsage | null;
}

export interface ChatStreamErrorEvent {
  type: "error";
  message: string;
}

export type ChatStreamEvent = ChatStreamTokenEvent | ChatStreamDoneEvent | ChatStreamErrorEvent;

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
}
