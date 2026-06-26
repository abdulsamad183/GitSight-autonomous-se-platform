import { beforeEach, describe, expect, it, vi } from "vitest";

import { RECENT_SEARCHES_KEY, clearClientSessionState } from "./clear-client-session";

const clearMock = vi.fn();

vi.mock("@/lib/query-client", () => ({
  getQueryClient: () => ({ clear: clearMock }),
}));

describe("clearClientSessionState", () => {
  beforeEach(() => {
    clearMock.mockReset();
    localStorage.clear();
  });

  it("clears the React Query cache", () => {
    clearClientSessionState();
    expect(clearMock).toHaveBeenCalledTimes(1);
  });

  it("removes recent searches from localStorage", () => {
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(["auth"]));
    clearClientSessionState();
    expect(localStorage.getItem(RECENT_SEARCHES_KEY)).toBeNull();
  });
});
