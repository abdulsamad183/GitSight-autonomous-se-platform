import { Bot, Network, Search } from "lucide-react";

import { GitSightLogo } from "@/components/gitsight-logo";
import { HomeCTA, HomeNav } from "@/components/home-cta";

const capabilities = [
  { icon: Network, label: "Repository ingestion" },
  { icon: Search, label: "Code search & graph" },
  { icon: Bot, label: "AI engineering assistant" },
] as const;

export default function Home() {
  return (
    <div className="relative flex min-h-screen flex-1 flex-col bg-white text-slate-950">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-[-10%] top-[-15%] size-[420px] rounded-full bg-blue-100/40 blur-3xl" />
        <div className="absolute right-[-8%] bottom-[-10%] size-[360px] rounded-full bg-slate-100 blur-3xl" />
      </div>

      <header className="absolute inset-x-0 top-0 z-10">
        <div className="mx-auto flex max-w-5xl justify-end px-6 py-4">
          <HomeNav />
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-center justify-center px-6 py-12 text-center">
        <GitSightLogo height={140} priority className="mb-10" />

        <h1 className="max-w-2xl text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
          Understand every repository before you change it.
        </h1>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-slate-600 sm:text-lg">
          Paste a GitHub URL to analyze structure, dependencies, branches, and pull requests.
        </p>

        <HomeCTA className="mt-8 justify-center" />

        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-slate-600">
          {capabilities.map((item) => {
            const Icon = item.icon;
            return (
              <span key={item.label} className="inline-flex items-center gap-2">
                <Icon className="size-4 text-[#2B59FF]" />
                {item.label}
              </span>
            );
          })}
        </div>
      </main>

      <footer className="border-t border-slate-200/80 py-5 text-center text-xs text-slate-400">
        v0.1.0
      </footer>
    </div>
  );
}
