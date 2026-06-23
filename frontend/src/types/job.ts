export type JobStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface JobEventItem {
  message: string;
  created_at: string;
}

export interface JobStatusResponse {
  id: string;
  status: JobStatus;
  progress: number;
  current_stage: string | null;
  error_message: string | null;
  events: JobEventItem[];
}
