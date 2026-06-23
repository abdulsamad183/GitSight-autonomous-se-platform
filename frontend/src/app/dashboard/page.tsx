import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getHealth, getVersion } from "@/services/health";

export default async function DashboardPage() {
  let healthStatus = "unavailable";
  let serviceName = "—";
  let version = "—";
  let error: string | null = null;

  try {
    const [health, versionInfo] = await Promise.all([getHealth(), getVersion()]);
    healthStatus = health.status;
    serviceName = versionInfo.service;
    version = versionInfo.version;
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to reach API";
  }

  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-lg font-semibold tracking-tight">GitSight</span>
          <Link href="/" className={cn(buttonVariants({ variant: "outline" }))}>
            Home
          </Link>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-12">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-2 text-muted-foreground">
            Platform overview and API status. Full features coming soon.
          </p>
        </div>

        {error && (
          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">API Connection Error</CardTitle>
              <CardDescription>{error}</CardDescription>
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
