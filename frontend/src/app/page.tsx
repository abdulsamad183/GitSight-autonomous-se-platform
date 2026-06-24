import { Bot, GitBranch, Search, Sparkles, Workflow } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { HomeCTA, HomeNav } from "@/components/home-cta";

const features = [
  {
    icon: GitBranch,
    title: "Repository Ingestion",
    description: "Clone, parse, and index repositories with branch-aware analysis.",
    accent: "from-violet-500 to-fuchsia-500",
  },
  {
    icon: Search,
    title: "Semantic Code Search",
    description: "Explore files, symbols, and dependencies with repository intelligence.",
    accent: "from-sky-500 to-indigo-500",
  },
  {
    icon: Bot,
    title: "AI Engineering Assistant",
    description: "Lay the foundation for repository-aware reviews, audits, and automation.",
    accent: "from-emerald-500 to-teal-500",
  },
];

export default function Home() {
  return (
    <div className="relative flex min-h-screen flex-1 flex-col overflow-hidden bg-gradient-to-br from-violet-50 via-white to-sky-50 text-slate-950">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-[-15%] top-[-20%] size-[540px] rounded-full bg-violet-300/50 blur-3xl" />
        <div className="absolute right-[-12%] top-[8%] size-[460px] rounded-full bg-sky-300/40 blur-3xl" />
        <div className="absolute bottom-[-18%] left-[25%] size-[520px] rounded-full bg-fuchsia-200/40 blur-3xl" />
      </div>

      <header className="border-b border-white/70 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="bg-gradient-to-r from-violet-700 via-fuchsia-600 to-sky-600 bg-clip-text text-xl font-bold text-transparent">
            GitSight
          </span>
          <HomeNav />
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-14 px-6 py-16">
        <section className="grid items-center gap-10 lg:grid-cols-[minmax(0,1fr)_420px]">
          <div className="flex max-w-3xl flex-col gap-6">
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-violet-200 bg-white/70 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-violet-700 shadow-sm backdrop-blur">
              <Sparkles className="size-3.5" />
              Repository Intelligence
            </div>
            <div className="space-y-4">
              <h1 className="text-5xl font-bold tracking-tight text-slate-950 sm:text-6xl">
                Understand every repository before you change it.
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-slate-600">
                GitSight turns a GitHub URL into files, symbols, dependency relationships,
                branch metadata, and pull request inventory in one polished workspace.
              </p>
            </div>
            <HomeCTA />
            <div className="grid gap-3 pt-2 text-sm text-slate-600 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/80 bg-white/70 p-4 shadow-lg shadow-violet-100/60 backdrop-blur">
                <p className="text-2xl font-bold text-slate-950">10</p>
                <p>Branches analyzed</p>
              </div>
              <div className="rounded-2xl border border-white/80 bg-white/70 p-4 shadow-lg shadow-sky-100/60 backdrop-blur">
                <p className="text-2xl font-bold text-slate-950">PR</p>
                <p>Inventory sync</p>
              </div>
              <div className="rounded-2xl border border-white/80 bg-white/70 p-4 shadow-lg shadow-fuchsia-100/60 backdrop-blur">
                <p className="text-2xl font-bold text-slate-950">AST</p>
                <p>Symbol extraction</p>
              </div>
            </div>
          </div>

          <Card className="relative overflow-hidden border-white/80 bg-white/80 shadow-2xl shadow-violet-100/80 backdrop-blur-xl">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-400/60 to-transparent" />
            <div className="absolute -right-16 -top-16 size-44 rounded-full bg-violet-200/60 blur-3xl" />
            <CardHeader className="relative">
              <CardTitle className="flex items-center gap-2 text-slate-950">
                <span className="rounded-xl bg-violet-100 p-2 text-violet-700 ring-1 ring-violet-200">
                  <Workflow className="size-5" />
                </span>
                Live Repository Pipeline
              </CardTitle>
              <CardDescription className="text-slate-600">
                A fast path from GitHub URL to usable repository intelligence.
              </CardDescription>
            </CardHeader>
            <CardContent className="relative space-y-4">
              {[
                "Clone repository",
                "Parse source files",
                "Extract dependencies",
                "Synchronize pull requests",
              ].map((step, index) => (
                <div
                  key={step}
                  className="flex items-center gap-3 rounded-2xl border border-violet-100 bg-white/75 p-3 shadow-sm"
                >
                  <span className="flex size-8 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-sky-600 text-sm font-bold text-white">
                    {index + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-slate-950">{step}</p>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-violet-500 to-sky-500"
                        style={{ width: `${58 + index * 10}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-6 sm:grid-cols-3">
          {features.map((feature) => (
            <Card
              key={feature.title}
              className="group relative overflow-hidden border-white/80 bg-white/80 shadow-xl shadow-slate-200/70 backdrop-blur-xl transition hover:-translate-y-1 hover:shadow-2xl hover:shadow-violet-100/80"
            >
              <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${feature.accent}`} />
              <CardHeader>
                <span
                  className={`mb-3 flex size-11 items-center justify-center rounded-2xl bg-gradient-to-br text-white shadow-lg ${feature.accent}`}
                >
                  <feature.icon className="size-5" />
                </span>
                <CardTitle className="text-base text-slate-950">{feature.title}</CardTitle>
                <CardDescription className="text-slate-600">
                  {feature.description}
                </CardDescription>
              </CardHeader>
              <CardContent />
            </Card>
          ))}
        </section>

        <section className="overflow-hidden rounded-3xl border border-white/80 bg-white/80 p-8 shadow-2xl shadow-sky-100/70 backdrop-blur-xl">
          <div className="grid items-center gap-6 md:grid-cols-[minmax(0,1fr)_auto]">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-700">
                Ready to inspect a repo?
              </p>
              <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
                Start with a GitHub URL and build your code intelligence graph.
              </h2>
              <p className="mt-2 text-slate-600">
                Analyze once, refresh anytime, and keep repository metadata synchronized.
              </p>
            </div>
            <HomeCTA />
          </div>
        </section>
      </main>

      <footer className="border-t border-white/70 bg-white/60 py-6 text-center text-sm text-slate-500 backdrop-blur-xl">
        GitSight v0.1.0 - Foundation release
      </footer>
    </div>
  );
}
