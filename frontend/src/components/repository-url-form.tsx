"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api-client";
import { analyzeRepository } from "@/services/repositories";
import type { AnalyzeResponse } from "@/types/repository";

interface RepositoryUrlFormProps {
  onAnalyzeStarted: (result: AnalyzeResponse) => void;
}

export function RepositoryUrlForm({ onAnalyzeStarted }: RepositoryUrlFormProps) {
  const [githubUrl, setGithubUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const result = await analyzeRepository({ github_url: githubUrl.trim() });
      onAnalyzeStarted(result);
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message);
      } else {
        setError(e instanceof Error ? e.message : "Failed to start analysis");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="github-url" className="text-slate-700">
          GitHub Repository URL
        </Label>
        <Input
          id="github-url"
          type="url"
          placeholder="https://github.com/owner/repository"
          value={githubUrl}
          onChange={(e) => setGithubUrl(e.target.value)}
          required
          className="border-violet-100 bg-white/80 text-slate-950 placeholder:text-slate-400 shadow-sm focus-visible:ring-violet-300/60"
        />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <Button
        type="submit"
        disabled={isSubmitting || !githubUrl.trim()}
        className="h-10 w-full bg-gradient-to-r from-violet-600 via-indigo-600 to-sky-600 text-white shadow-lg shadow-violet-200 hover:from-violet-500 hover:via-indigo-500 hover:to-sky-500"
      >
        {isSubmitting ? "Starting..." : "Analyze"}
      </Button>
    </form>
  );
}
