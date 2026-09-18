"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { queryKeys } from "@/lib/query-keys";
import { getAdminUserDetail } from "@/services/admin";

export default function AdminUserDetailPage() {
  const params = useParams<{ id: string }>();
  const userId = params.id;

  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.adminUserDetail(userId),
    queryFn: () => getAdminUserDetail(userId),
    enabled: Boolean(userId),
  });

  if (isLoading) {
    return <p className="text-muted-foreground">Loading user...</p>;
  }

  if (error || !data) {
    return <p className="text-destructive">Failed to load user detail.</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/admin/users" className="text-sm text-slate-500 underline">
          Back to users
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">{data.username}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {data.email} · {data.role} · joined{" "}
          {new Date(data.created_at).toLocaleDateString()}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Repositories ({data.repositories.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {data.repositories.length === 0 ? (
            <p className="text-sm text-slate-500">No repositories yet.</p>
          ) : (
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="pb-3 font-medium">Name</th>
                  <th className="pb-3 font-medium">URL</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Indexing</th>
                  <th className="pb-3 font-medium">Updated</th>
                </tr>
              </thead>
              <tbody>
                {data.repositories.map((repo) => (
                  <tr key={repo.id} className="border-b border-slate-100 last:border-0">
                    <td className="py-3 font-medium">{repo.name}</td>
                    <td className="py-3">
                      <a
                        href={repo.repo_url}
                        target="_blank"
                        rel="noreferrer"
                        className="break-all text-slate-700 underline"
                      >
                        {repo.repo_url}
                      </a>
                    </td>
                    <td className="py-3 capitalize">{repo.status}</td>
                    <td className="py-3 capitalize">{repo.indexing_status}</td>
                    <td className="py-3 text-slate-600">
                      {new Date(repo.updated_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
