export type AdminStats = {
  total_users: number;
  total_repositories: number;
  repos_by_status: Record<string, number>;
  repos_by_indexing_status: Record<string, number>;
  signups_last_7_days: number;
  repos_added_last_7_days: number;
};

export type AdminUserListItem = {
  id: string;
  username: string;
  email: string;
  role: string;
  created_at: string;
  repository_count: number;
};

export type AdminUserListResponse = {
  items: AdminUserListItem[];
  total: number;
  page: number;
  limit: number;
};

export type AdminRepositoryItem = {
  id: string;
  name: string;
  repo_url: string;
  status: string;
  indexing_status: string;
  created_at: string;
  updated_at: string;
};

export type AdminUserDetail = {
  id: string;
  username: string;
  email: string;
  role: string;
  created_at: string;
  repositories: AdminRepositoryItem[];
};
