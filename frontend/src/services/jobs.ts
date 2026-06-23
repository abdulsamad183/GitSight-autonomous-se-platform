import { apiGet } from "@/lib/api-client";
import type { JobStatusResponse } from "@/types/job";

export async function getJob(jobId: string): Promise<JobStatusResponse> {
  return apiGet<JobStatusResponse>(`/api/v1/jobs/${jobId}`);
}
