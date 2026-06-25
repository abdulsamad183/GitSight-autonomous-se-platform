"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { AuthProvider } from "@/contexts/auth-context";
import { getQueryClient } from "@/lib/query-client";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(getQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}
