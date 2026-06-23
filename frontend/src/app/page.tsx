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

const features = [
  {
    title: "Repository Ingestion",
    description: "Connect and index codebases for deep analysis.",
  },
  {
    title: "Semantic Code Search",
    description: "Find relevant code across large repositories instantly.",
  },
  {
    title: "AI Engineering Assistant",
    description: "Repository-aware chat, reviews, and engineering audits.",
  },
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-lg font-semibold tracking-tight">GitSight</span>
          <Link href="/dashboard" className={cn(buttonVariants({ variant: "outline" }))}>
            Dashboard
          </Link>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-16 px-6 py-20">
        <section className="flex max-w-3xl flex-col gap-6">
          <p className="text-sm font-medium uppercase tracking-widest text-muted-foreground">
            Autonomous Software Engineering
          </p>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            AI-powered platform for modern software teams
          </h1>
          <p className="text-lg text-muted-foreground">
            GitSight helps you understand, search, and improve your codebase with
            repository-aware AI — from ingestion to PR review and engineering audits.
          </p>
          <div className="flex gap-3">
            <Link href="/dashboard" className={cn(buttonVariants())}>
              Open Dashboard
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Learn More
            </a>
          </div>
        </section>

        <section className="grid gap-6 sm:grid-cols-3">
          {features.map((feature) => (
            <Card key={feature.title}>
              <CardHeader>
                <CardTitle className="text-base">{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
              <CardContent />
            </Card>
          ))}
        </section>
      </main>

      <footer className="border-t py-6 text-center text-sm text-muted-foreground">
        GitSight v0.1.0 — Foundation release
      </footer>
    </div>
  );
}
