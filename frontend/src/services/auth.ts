import { apiGet, apiPost } from "@/lib/api-client";
import type { LoginInput, RegisterInput, User } from "@/types/auth";

const AUTH_PREFIX = "/api/v1/auth";

export function register(input: RegisterInput): Promise<User> {
  return apiPost<User>(`${AUTH_PREFIX}/register`, input);
}

export function login(input: LoginInput): Promise<User> {
  return apiPost<User>(`${AUTH_PREFIX}/login`, input);
}

export function getMe(): Promise<User> {
  return apiGet<User>(`${AUTH_PREFIX}/me`);
}

export function logout(): Promise<void> {
  return apiPost<void>(`${AUTH_PREFIX}/logout`);
}
