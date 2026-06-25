"use client";

import type { HTMLAttributes, ReactNode } from "react";
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

function CodeBlock({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLElement> & { children?: ReactNode }) {
  const match = /language-(\w+)/.exec(className || "");
  const language = match?.[1];
  const code = String(children).replace(/\n$/, "");

  return (
    <div className="my-3 overflow-hidden rounded-lg border bg-zinc-950 text-zinc-100">
      {language && (
        <div className="border-b border-zinc-800 px-3 py-1.5 text-xs font-medium uppercase tracking-wide text-zinc-400">
          {language}
        </div>
      )}
      <pre className="overflow-x-auto p-4 text-xs leading-relaxed">
        <code className={className} {...props}>
          {code}
        </code>
      </pre>
    </div>
  );
}

const assistantComponents: Components = {
  p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
  ul: ({ children }) => <ul className="mb-3 list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="mb-3 list-decimal space-y-1 pl-5">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  a: ({ href, children }) => (
    <a href={href} className="text-violet-600 underline underline-offset-2 hover:text-violet-500">
      {children}
    </a>
  ),
  code: ({ className, children, ...props }) => {
    const isBlock = Boolean(className);
    if (isBlock) {
      return (
        <CodeBlock className={className} {...props}>
          {children}
        </CodeBlock>
      );
    }
    return (
      <code
        className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em]"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children }) => <>{children}</>,
};

export function ChatMessageBubble({ role, content }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
          isUser
            ? "bg-violet-600 text-white"
            : "border bg-card text-foreground"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap leading-relaxed">{content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={assistantComponents}>
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
