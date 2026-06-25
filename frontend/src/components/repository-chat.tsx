"use client";

import { Loader2, Send, Sparkles } from "lucide-react";
import { useState } from "react";

import { ChatCitations } from "@/components/chat-citations";
import { ChatMessageBubble } from "@/components/chat-message";
import { SearchResultDrawer } from "@/components/search-result-drawer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRepositoryChat } from "@/hooks/use-repository-chat";
import type { SearchResult } from "@/types/search";

interface RepositoryChatProps {
  repositoryId: string;
  branch?: string | null;
}

export function RepositoryChat({ repositoryId, branch }: RepositoryChatProps) {
  const {
    messages,
    input,
    setInput,
    loading,
    error,
    toolStatus,
    sendMessage,
    scrollRef,
    starterQuestions,
  } = useRepositoryChat({ repositoryId, branch });

  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);

  return (
    <div className="flex h-[calc(100vh-12rem)] min-h-[32rem] flex-col rounded-2xl border bg-card shadow-sm">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && !loading && (
          <div className="space-y-4 py-8 text-center">
            <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-violet-100 dark:bg-violet-900/40">
              <Sparkles className="size-6 text-violet-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Repository AI Chat</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Ask questions about this repository using indexed code context.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {starterQuestions.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => void sendMessage(question)}
                  className="rounded-full border bg-background px-3 py-1.5 text-sm transition hover:bg-muted"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`}>
            <ChatMessageBubble role={message.role} content={message.content} />
            {message.role === "assistant" && message.sources && message.sources.length > 0 && (
              <ChatCitations sources={message.sources} onSelect={setSelectedResult} />
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin text-violet-500" />
            {toolStatus ?? "Thinking..."}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
            {error}
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      <form
        className="flex items-center gap-2 border-t p-4"
        onSubmit={(event) => {
          event.preventDefault();
          void sendMessage();
        }}
      >
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about this repository..."
          disabled={loading}
        />
        <Button type="submit" disabled={loading || !input.trim()}>
          {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
        </Button>
      </form>

      <SearchResultDrawer
        repositoryId={repositoryId}
        result={selectedResult}
        onClose={() => setSelectedResult(null)}
      />
    </div>
  );
}
