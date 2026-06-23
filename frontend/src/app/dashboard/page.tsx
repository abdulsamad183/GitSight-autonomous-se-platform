"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { getHealth, getVersion } from "@/services/health";

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [healthStatus, setHealthStatus] = useState("loading");
  const [serviceName, setServiceName] = useState("—");
  const [version, setVersion] = useState("—");
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [health, versionInfo] = await Promise.all([getHealth(), getVersion()]);
        setHealthStatus(health.status);
        setServiceName(versionInfo.service);
        setVersion(versionInfo.version);
      } catch (e) {
        setApiError(e instanceof Error ? e.message : "Failed to reach API");
      }
    };
    void fetchStatus();
  }, []);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-lg font-semibold tracking-tight">GitSight</span>
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground">
              Home
            </Link>
            <Button variant="outline" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-12">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-2 text-muted-foreground">
            Welcome back, <span className="font-medium text-foreground">{user?.username}</span>
            {user?.email ? ` (${user.email})` : ""}
          </p>
        </div>

        {apiError && (
          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">API Connection Error</CardTitle>
              <CardDescription>{apiError}</CardDescription>
            </CardHeader>
          </Card>
        )}

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>API Health</CardTitle>
              <CardDescription>Backend service status</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold capitalize">{healthStatus}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Service</CardTitle>
              <CardDescription>Registered service name</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">{serviceName}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Version</CardTitle>
              <CardDescription>Current API version</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">{version}</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Coming Soon</CardTitle>
            <CardDescription>Planned capabilities for this dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
              <li>Repository management and ingestion</li>
              <li>Job monitoring and progress tracking</li>
              <li>Code search and AI chat</li>
              <li>PR review and engineering audits</li>
            </ul>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
