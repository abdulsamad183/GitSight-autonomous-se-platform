"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Loader2 } from "lucide-react";

import { BranchSelector } from "@/components/branch-selector";
import { RepositoryChat } from "@/components/repository-chat";
import { buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { getRepositoryDetails, listBranches } from "@/services/repositories";
import type { BranchSummary, RepositoryDetail } from "@/types/repository";

export default function RepositoryChatPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [branches, setBranches] = useState<BranchSummary[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string | null>(
    searchParams.get("branch"),
  );
  const [detail, setDetail] = useState<RepositoryDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  const loadDetail = useCallback(
    async (branch?: string) => {
      if (!params.id) return;
      setLoading(true);
      try {
        const data = await getRepositoryDetails(params.id, branch);
        setDetail(data);
        setSelectedBranch(data.selected_branch ?? branch ?? null);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load repository");
      } finally {
        setLoading(false);
      }
    },
    [params.id],
  );

  useEffect(() => {
    if (!params.id || authLoading || !isAuthenticated) return;

    const load = async () => {
      try {
        const branchList = await listBranches(params.id);
        setBranches(branchList);
        const initialBranch =
          searchParams.get("branch") ?? branchList[0]?.branch ?? undefined;
        await loadDetail(initialBranch);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load repository");
        setLoading(false);
      }
    };

    void load();
  }, [params.id, authLoading, isAuthenticated, loadDetail, searchParams]);

  const handleBranchChange = useCallback(
    (branch: string) => {
      setSelectedBranch(branch);
      void loadDetail(branch);
    },
    [loadDetail],
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-violet-50/50 via-background to-background dark:from-violet-950/20">
      <header className="border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Link
              href={`/repositories/${params.id}`}
              className={buttonVariants({ variant: "ghost", size: "sm" })}
            >
              <ArrowLeft className="size-4" />
              Back to Repository
            </Link>
            <span className="bg-gradient-to-r from-violet-600 to-sky-600 bg-clip-text text-lg font-bold text-transparent">
              AI Chat
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-8">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="size-6 animate-spin text-violet-500" />
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
            {error}
          </div>
        )}

        {detail && !loading && (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h1 className="text-2xl font-semibold">
                  {detail.owner}/{detail.repository_name}
                </h1>
                <p className="text-sm text-muted-foreground">
                  Ask natural-language questions about this repository.
                </p>
              </div>
              <BranchSelector
                branches={branches}
                selectedBranch={selectedBranch ?? detail.default_branch ?? branches[0]?.branch ?? ""}
                onSelect={handleBranchChange}
                branchesTruncated={false}
              />
            </div>

            <RepositoryChat
              repositoryId={params.id}
              branch={selectedBranch ?? detail.selected_branch}
            />
          </>
        )}
      </main>
    </div>
  );
}
