"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { queryKeys } from "@/lib/query-keys";
import { getAdminStats } from "@/services/admin";

function StatCard({ title, value }: { title: string; value: string | number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-500">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-semibold tracking-tight">{value}</p>
      </CardContent>
    </Card>
  );
}

export default function AdminPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.adminStats,
    queryFn: getAdminStats,
  });

  if (isLoading) {
    return <p className="text-muted-foreground">Loading stats...</p>;
  }

  if (error || !data) {
    return <p className="text-destructive">Failed to load admin stats.</p>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Usage overview</h1>
          <p className="mt-1 text-sm text-slate-500">
            Platform-wide users and repository analysis activity.
          </p>
        </div>
        <Link href="/admin/users" className="text-sm font-medium text-slate-700 underline">
          View all users
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total users" value={data.total_users} />
        <StatCard title="Total repositories" value={data.total_repositories} />
        <StatCard title="Signups (7d)" value={data.signups_last_7_days} />
        <StatCard title="Repos added (7d)" value={data.repos_added_last_7_days} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Repos by status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(data.repos_by_status).map(([status, count]) => (
              <div key={status} className="flex justify-between text-sm">
                <span className="capitalize text-slate-600">{status}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Repos by indexing status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(data.repos_by_indexing_status).map(([status, count]) => (
              <div key={status} className="flex justify-between text-sm">
                <span className="capitalize text-slate-600">{status}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
