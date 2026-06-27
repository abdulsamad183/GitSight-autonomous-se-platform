"use client";

import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col items-center justify-center bg-white px-6 text-center text-slate-950">
        <h1 className="text-2xl font-semibold">Something went wrong</h1>
        <p className="mt-2 max-w-md text-sm text-slate-600">
          {error.message || "An unexpected error occurred."}
        </p>
        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={reset}
            className="rounded-md bg-[#2B59FF] px-4 py-2 text-sm font-medium text-white"
          >
            Try again
          </button>
          <Link href="/" className="rounded-md border border-slate-200 px-4 py-2 text-sm">
            Go home
          </Link>
        </div>
      </body>
    </html>
  );
}
