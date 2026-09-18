import { apiGet } from "@/lib/api-client";
import type {
  AdminStats,
  AdminUserDetail,
  AdminUserListResponse,
} from "@/types/admin";

const ADMIN_PREFIX = "/api/v1/admin";

export function getAdminStats(): Promise<AdminStats> {
  return apiGet<AdminStats>(`${ADMIN_PREFIX}/stats`);
}

export function listAdminUsers(page = 1, limit = 20): Promise<AdminUserListResponse> {
  return apiGet<AdminUserListResponse>(`${ADMIN_PREFIX}/users?page=${page}&limit=${limit}`);
}

export function getAdminUserDetail(userId: string): Promise<AdminUserDetail> {
  return apiGet<AdminUserDetail>(`${ADMIN_PREFIX}/users/${userId}`);
}
