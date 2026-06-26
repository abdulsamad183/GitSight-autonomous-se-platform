import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { ApiError } from "@/lib/api-client";

const getMeMock = vi.fn();
const loginMock = vi.fn();
const logoutMock = vi.fn();
const clearClientSessionStateMock = vi.fn();

vi.mock("@/services/auth", () => ({
  getMe: () => getMeMock(),
  login: (...args: unknown[]) => loginMock(...args),
  register: vi.fn(),
  logout: () => logoutMock(),
}));

vi.mock("@/lib/clear-client-session", () => ({
  clearClientSessionState: () => clearClientSessionStateMock(),
  RECENT_SEARCHES_KEY: "gitsight_recent_searches",
}));

import { AuthProvider, useAuthContext } from "./auth-context";

function TestConsumer() {
  const { isAuthenticated, user, isLoading, login, logout } = useAuthContext();
  if (isLoading) return <div>Loading auth</div>;
  return (
    <div>
      <span data-testid="auth-status">{isAuthenticated ? "authenticated" : "guest"}</span>
      <span data-testid="username">{user?.username ?? "none"}</span>
      <button type="button" onClick={() => void login({ email: "b@example.com", password: "pass" })}>
        Login
      </button>
      <button type="button" onClick={() => void logout()}>
        Logout
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    getMeMock.mockReset();
    loginMock.mockReset();
    logoutMock.mockReset();
    clearClientSessionStateMock.mockReset();
    logoutMock.mockResolvedValue(undefined);
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

  it("clears client session state on logout", async () => {
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

    fireEvent.click(screen.getByRole("button", { name: "Logout" }));

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1);
      expect(clearClientSessionStateMock).toHaveBeenCalledTimes(1);
      expect(screen.getByTestId("auth-status")).toHaveTextContent("guest");
    });
  });

  it("clears client session state on login", async () => {
    getMeMock.mockRejectedValue(new ApiError(401, "Not authenticated"));
    loginMock.mockResolvedValue({
      id: "2",
      username: "bob",
      email: "b@example.com",
      created_at: "2026-01-01T00:00:00Z",
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent("guest");
    });

    fireEvent.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => {
      expect(clearClientSessionStateMock).toHaveBeenCalledTimes(1);
      expect(loginMock).toHaveBeenCalledTimes(1);
      expect(screen.getByTestId("username")).toHaveTextContent("bob");
    });

    expect(clearClientSessionStateMock.mock.invocationCallOrder[0]).toBeLessThan(
      loginMock.mock.invocationCallOrder[0],
    );
  });
});
