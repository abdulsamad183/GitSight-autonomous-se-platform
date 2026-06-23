import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { ApiError } from "@/lib/api-client";

const getMeMock = vi.fn();

vi.mock("@/services/auth", () => ({
  getMe: () => getMeMock(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}));

import { AuthProvider, useAuthContext } from "./auth-context";

function TestConsumer() {
  const { isAuthenticated, user, isLoading } = useAuthContext();
  if (isLoading) return <div>Loading auth</div>;
  return (
    <div>
      <span data-testid="auth-status">{isAuthenticated ? "authenticated" : "guest"}</span>
      <span data-testid="username">{user?.username ?? "none"}</span>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    getMeMock.mockReset();
  });

  it("sets authenticated state when getMe succeeds", async () => {
    getMeMock.mockResolvedValue({
      id: "1",
      username: "alice",
      email: "alice@example.com",
      created_at: "2026-01-01T00:00:00Z",
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent("authenticated");
    });
    expect(screen.getByTestId("username")).toHaveTextContent("alice");
  });

  it("sets guest state when getMe returns 401", async () => {
    getMeMock.mockRejectedValue(new ApiError(401, "Not authenticated"));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent("guest");
    });
  });
});
