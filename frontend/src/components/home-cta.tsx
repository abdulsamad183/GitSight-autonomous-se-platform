"use client";

import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const primaryCtaClass =
  "bg-[#2B59FF] text-white shadow-md shadow-blue-200/60 hover:bg-[#2448d6]";

const outlineCtaClass =
  "border-violet-200 bg-white/70 text-slate-700 shadow-sm backdrop-blur hover:bg-violet-50 hover:text-slate-950";

interface HomeCTAProps {
  className?: string;
  size?: "default" | "lg";
}

export function HomeCTA({ className, size = "default" }: HomeCTAProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const heightClass = size === "lg" ? "h-11 px-6 text-base" : "h-10 px-5";

  if (isLoading) {
    return (
      <div className={cn("flex flex-wrap gap-3", className)}>
        <span
          className={cn(
            buttonVariants(),
            primaryCtaClass,
            heightClass,
            "pointer-events-none opacity-50",
          )}
        >
          Loading...
        </span>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className={cn("flex flex-wrap gap-3", className)}>
        <Link href="/dashboard" className={cn(buttonVariants(), primaryCtaClass, heightClass)}>
          Open Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-wrap gap-3", className)}>
      <Link href="/login" className={cn(buttonVariants(), primaryCtaClass, heightClass)}>
        Sign in
      </Link>
      <Link
        href="/register"
        className={cn(buttonVariants({ variant: "outline" }), outlineCtaClass, heightClass)}
      >
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
      <Link href="/dashboard" className={cn(buttonVariants({ variant: "outline" }), outlineCtaClass, "h-10 px-5")}>
        Dashboard
      </Link>
    );
  }

  return (
    <Link href="/login" className={cn(buttonVariants({ variant: "outline" }), outlineCtaClass, "h-10 px-5")}>
      Sign in
    </Link>
  );
}
