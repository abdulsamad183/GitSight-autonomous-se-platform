"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Loader2 } from "lucide-react";

import { BranchSelector } from "@/components/branch-selector";
import { RepositoryDocs } from "@/components/repository-docs";
import { RepositorySubNav } from "@/components/repository-sub-nav";
import { buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useRepositoryBranches, useRepositoryDetails } from "@/hooks/use-repository-data";

export default function RepositoryDocsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const repositoryId = params.id;

  const branchFromUrl = searchParams.get("branch");
  const [branchOverride, setBranchOverride] = useState<string | null>(null);

  const branchesQuery = useRepositoryBranches(repositoryId);
  const branches = branchesQuery.data ?? [];

  const selectedBranch =
    branchOverride ?? branchFromUrl ?? branches[0]?.branch ?? null;

  const detailsQuery = useRepositoryDetails(repositoryId, selectedBranch);
  const detail = detailsQuery.data;

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  const initialLoading =
    (branchesQuery.isLoading && branches.length === 0) ||
    (detailsQuery.isLoading && !detail);
  const loadError =
    branchesQuery.error instanceof Error
      ? branchesQuery.error.message
      : detailsQuery.error instanceof Error
        ? detailsQuery.error.message
        : null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-violet-50/50 via-background to-background dark:from-violet-950/20">
      <header className="border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Link
              href={`/repositories/${repositoryId}${
                selectedBranch ? `?branch=${encodeURIComponent(selectedBranch)}` : ""
              }`}
              className={buttonVariants({ variant: "ghost", size: "sm" })}
            >
              <ArrowLeft className="size-4" />
              Back to Repository
            </Link>
            <span className="bg-gradient-to-r from-violet-600 to-sky-600 bg-clip-text text-lg font-bold text-transparent">
              Documentation
            </span>
          </div>
          {branches.length > 0 && selectedBranch && (
            <BranchSelector
              branches={branches}
              selectedBranch={selectedBranch}
              onSelect={setBranchOverride}
              branchesTruncated={detail?.branches_truncated ?? false}
            />
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        <RepositorySubNav
          repositoryId={repositoryId}
          branch={selectedBranch}
          activeTab="docs"
        />

        {initialLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="size-6 animate-spin text-violet-500" />
          </div>
        )}

        {loadError && (
          <p className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
            {loadError}
          </p>
        )}

        {!initialLoading && !loadError && detail && (
          <RepositoryDocs repositoryId={repositoryId} branch={selectedBranch} />
        )}
      </main>
    </div>
  );
}
