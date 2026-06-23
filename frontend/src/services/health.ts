import { apiGet } from "@/lib/api-client";
import type { HealthResponse, VersionResponse } from "@/types/api";

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}

export function getVersion(): Promise<VersionResponse> {
  return apiGet<VersionResponse>("/api/v1/version");
}
