"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { chatRepository, streamChatRepository } from "@/services/repositories";
import type { ChatMessage, ChatSource } from "@/types/chat";

export const STARTER_QUESTIONS = [
  "Explain project architecture.",
  "How does authentication work?",
  "Explain repository structure.",
  "Where is JWT implemented?",
];

interface UseRepositoryChatOptions {
  repositoryId: string;
  branch?: string | null;
}

export function useRepositoryChat({ repositoryId, branch }: UseRepositoryChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = useCallback(
    async (text?: string) => {
      const message = (text ?? input).trim();
      if (!message || loading) return;

      setInput("");
      setError(null);
      setLoading(true);
      setMessages((prev) => [...prev, { role: "user", content: message }]);

      let assistantContent = "";
      let sources: ChatSource[] = [];

      const appendAssistant = (content: string, nextSources?: ChatSource[]) => {
        setMessages((prev) => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          if (last?.role === "assistant") {
            copy[copy.length - 1] = {
              role: "assistant",
              content,
              sources: nextSources ?? last.sources,
            };
          } else {
            copy.push({ role: "assistant", content, sources: nextSources });
          }
          return copy;
        });
      };

      try {
        await streamChatRepository(repositoryId, {
          message,
          branch: branch ?? undefined,
          onToken: (token) => {
            assistantContent += token;
            appendAssistant(assistantContent, sources);
          },
          onDone: (doneSources) => {
            sources = doneSources;
            appendAssistant(assistantContent, doneSources);
          },
          onError: (messageText) => {
            throw new Error(messageText);
          },
        });
      } catch (streamError) {
        try {
          const response = await chatRepository(repositoryId, {
            message,
            branch: branch ?? undefined,
            stream: false,
          });
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = {
                role: "assistant",
                content: response.answer,
                sources: response.sources,
              };
            } else {
              copy.push({
                role: "assistant",
                content: response.answer,
                sources: response.sources,
              });
            }
            return copy;
          });
        } catch (fallbackError) {
          const messageText =
            fallbackError instanceof Error
              ? fallbackError.message
              : streamError instanceof Error
                ? streamError.message
                : "Chat failed";
          setError(messageText);
          setMessages((prev) => prev.filter((item, index) => !(index === prev.length - 1 && item.role === "assistant" && !item.content)));
        }
      } finally {
        setLoading(false);
      }
    },
    [branch, input, loading, repositoryId],
  );

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
    setInput("");
  }, []);

  return {
    messages,
    input,
    setInput,
    loading,
    error,
    sendMessage,
    clear,
    scrollRef,
    starterQuestions: STARTER_QUESTIONS,
  };
}
