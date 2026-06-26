"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type RepositorySubNavTab = "overview" | "search" | "chat" | "graph" | "docs" | "pull-requests";

const TABS: { id: RepositorySubNavTab; label: string; path: string }[] = [
  { id: "overview", label: "Overview", path: "" },
  { id: "search", label: "Search", path: "" },
  { id: "chat", label: "Chat", path: "/chat" },
  { id: "graph", label: "Graph", path: "/graph" },
  { id: "docs", label: "Docs", path: "/docs" },
  { id: "pull-requests", label: "Pull Requests", path: "/pull-requests" },
];

interface RepositorySubNavProps {
  repositoryId: string;
  branch?: string | null;
  activeTab: RepositorySubNavTab;
}

export function RepositorySubNav({ repositoryId, branch, activeTab }: RepositorySubNavProps) {
  const pathname = usePathname();
  const branchQuery = branch ? `?branch=${encodeURIComponent(branch)}` : "";

  const hrefFor = (tab: (typeof TABS)[number]) => {
    if (tab.id === "search") {
      return `/repositories/${repositoryId}${branchQuery}#search`;
    }
    return `/repositories/${repositoryId}${tab.path}${branchQuery}`;
  };

  const isActive = (tab: (typeof TABS)[number]) => {
    if (tab.id === activeTab) return true;
    if (tab.id === "overview" && pathname === `/repositories/${repositoryId}` && activeTab === "overview") {
      return true;
    }
    return false;
  };

  return (
    <nav className="flex flex-wrap gap-2 border-b pb-4">
      {TABS.map((tab) => (
        <Link
          key={tab.id}
          href={hrefFor(tab)}
          data-active={isActive(tab)}
          className="rounded-full px-4 py-2 text-sm font-medium transition data-[active=true]:bg-violet-600 data-[active=true]:text-white bg-muted text-muted-foreground hover:bg-muted/80"
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}
