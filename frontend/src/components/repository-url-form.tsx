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
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="github-url">GitHub Repository URL</Label>
        <Input
          id="github-url"
          type="url"
          placeholder="https://github.com/owner/repository"
          value={githubUrl}
          onChange={(e) => setGithubUrl(e.target.value)}
          required
        />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <Button type="submit" disabled={isSubmitting || !githubUrl.trim()}>
        {isSubmitting ? "Starting..." : "Analyze"}
      </Button>
    </form>
  );
}
