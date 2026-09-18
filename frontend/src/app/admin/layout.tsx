"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (user?.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [isLoading, isAuthenticated, user, router]);

  const handleLogout = async () => {
    router.replace("/");
    await logout();
  };

  if (isLoading || !isAuthenticated || user?.role !== "admin") {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-white to-sky-50 text-slate-950">
      <header className="border-b border-white/70 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-4">
            <Link href="/admin" className="text-sm font-medium text-slate-950">
              Admin
            </Link>
            <Link
              href="/admin/users"
              className="text-sm text-slate-500 transition hover:text-slate-950"
            >
              Users
            </Link>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="text-sm text-slate-500 transition hover:text-slate-950"
            >
              Dashboard
            </Link>
            <Button
              variant="outline"
              onClick={handleLogout}
              className="border-violet-200 bg-white/70 text-slate-700 hover:bg-violet-50"
            >
              Logout
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
