"use client";

import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const primaryCtaClass =
  "h-10 bg-gradient-to-r from-violet-600 via-indigo-600 to-sky-600 px-5 text-white shadow-lg shadow-violet-200 hover:from-violet-500 hover:via-indigo-500 hover:to-sky-500";

const outlineCtaClass =
  "h-10 border-violet-200 bg-white/70 px-5 text-slate-700 shadow-sm backdrop-blur hover:bg-violet-50 hover:text-slate-950";

export function HomeCTA() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex gap-3">
        <span className={cn(buttonVariants(), primaryCtaClass, "pointer-events-none opacity-50")}>
          Loading...
        </span>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="flex gap-3">
        <Link href="/dashboard" className={cn(buttonVariants(), primaryCtaClass)}>
          Open Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <Link href="/login" className={cn(buttonVariants(), primaryCtaClass)}>
        Sign in
      </Link>
      <Link href="/register" className={cn(buttonVariants({ variant: "outline" }), outlineCtaClass)}>
        Register
      </Link>
    </div>
  );
}

export function HomeNav() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    return (
      <Link href="/dashboard" className={cn(buttonVariants({ variant: "outline" }), outlineCtaClass)}>
        Dashboard
      </Link>
    );
  }

  return (
    <Link href="/login" className={cn(buttonVariants({ variant: "outline" }), outlineCtaClass)}>
      Sign in
    </Link>
  );
}
