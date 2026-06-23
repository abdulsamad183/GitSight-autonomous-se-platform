"use client";

import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

export function HomeCTA() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex gap-3">
        <span className={cn(buttonVariants(), "pointer-events-none opacity-50")}>Loading...</span>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="flex gap-3">
        <Link href="/dashboard" className={cn(buttonVariants())}>
          Open Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <Link href="/login" className={cn(buttonVariants())}>
        Sign in
      </Link>
      <Link href="/register" className={cn(buttonVariants({ variant: "outline" }))}>
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
      <Link href="/dashboard" className={cn(buttonVariants({ variant: "outline" }))}>
        Dashboard
      </Link>
    );
  }

  return (
    <Link href="/login" className={cn(buttonVariants({ variant: "outline" }))}>
      Sign in
    </Link>
  );
}
