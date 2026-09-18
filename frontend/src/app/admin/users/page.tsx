"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { queryKeys } from "@/lib/query-keys";
import { listAdminUsers } from "@/services/admin";

export default function AdminUsersPage() {
  const [page, setPage] = useState(1);
  const limit = 20;
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.adminUsers(page),
    queryFn: () => listAdminUsers(page, limit),
  });

  if (isLoading) {
    return <p className="text-muted-foreground">Loading users...</p>;
  }

  if (error || !data) {
    return <p className="text-destructive">Failed to load users.</p>;
  }

  const totalPages = Math.max(1, Math.ceil(data.total / limit));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Users</h1>
        <p className="mt-1 text-sm text-slate-500">
          {data.total} registered user{data.total === 1 ? "" : "s"}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">All accounts</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="pb-3 font-medium">Username</th>
                <th className="pb-3 font-medium">Email</th>
                <th className="pb-3 font-medium">Role</th>
                <th className="pb-3 font-medium">Repos</th>
                <th className="pb-3 font-medium">Joined</th>
                <th className="pb-3 font-medium" />
              </tr>
            </thead>
            <tbody>
              {data.items.map((user) => (
                <tr key={user.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-3 font-medium">{user.username}</td>
                  <td className="py-3 text-slate-600">{user.email}</td>
                  <td className="py-3 capitalize">{user.role}</td>
                  <td className="py-3">{user.repository_count}</td>
                  <td className="py-3 text-slate-600">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 text-right">
                    <Link
                      href={`/admin/users/${user.id}`}
                      className="font-medium text-slate-700 underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          Page {page} of {totalPages}
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            disabled={page >= totalPages}
            onClick={() => setPage((current) => current + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
