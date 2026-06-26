import { getQueryClient } from "@/lib/query-client";

export const RECENT_SEARCHES_KEY = "gitsight_recent_searches";

export function clearClientSessionState(): void {
  getQueryClient().clear();

  if (typeof window !== "undefined") {
    localStorage.removeItem(RECENT_SEARCHES_KEY);
  }
}
