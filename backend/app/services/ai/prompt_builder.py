import json

from app.services.ai.tools.base import AgentTool
from app.services.ai.types import ChatMessage

CHAT_SYSTEM_PROMPT = """You are an expert senior software engineer.

The repository context below was produced by internal repository tools \
(metadata, search, branches, graph).
Use all available evidence from these tool outputs.
Do not invent functions, files, or behavior.

If the tool outputs are insufficient, clearly state that additional context is required.

When possible:
- mention file names
- mention class names
- mention method names

Explain clearly and technically.
Do not fabricate answers.

When showing code from the repository context, use fenced markdown code blocks with a language tag \
(e.g. ```python). Use inline backticks for short identifiers, file names, and symbol names."""

PLANNING_SYSTEM_PROMPT = """You are a repository analysis planner.

Given a user question and a catalog of available tools, decide which tools to run and in what order.
Output JSON only with this shape:
{
  "reasoning": "brief explanation",
  "steps": [
    { "tool": "<tool_name>", "arguments": { ... } }
  ]
}

Rules:
- Select zero or more tools as needed.
- Use only tools from the catalog.
- Provide valid arguments matching each tool schema.
- Order steps so later tools can build on earlier results when helpful.
- For code explanation questions, prefer search with action retrieve_context.
- For metadata counts (branches, files, languages), use repository tool.
- For branch comparisons or feature branches, use branch tool.
- For dependency/import/structure questions, use graph tool.
- If no tools are needed, return an empty steps array."""

DOCUMENTATION_SYSTEM_PROMPT = """You are a technical documentation writer for software repositories.

Generate clear, concise Markdown documentation using ONLY the repository context provided below.
Do not invent files, classes, methods, or behavior that are not supported by the context.

Requirements:
- Output valid Markdown only (no preamble or meta commentary).
- Mention specific file paths, class names, and method names when they appear in the context.
- Use headings, bullet lists, and code fences where appropriate.
- Keep the documentation technically accurate and readable.
- If the context is insufficient for a section, state what is missing rather than guessing."""


class PromptBuilder:
    def build_chat_prompt(self, context_text: str, user_question: str) -> list[ChatMessage]:
        user_content = f"""Repository Context

{context_text}

User Question

{user_question}"""
        return [
            ChatMessage(role="system", content=CHAT_SYSTEM_PROMPT),
            ChatMessage(role="user", content=user_content),
        ]

    def build_planning_prompt(
        self,
        user_question: str,
        branch: str | None,
        tools: list[AgentTool],
    ) -> list[ChatMessage]:
        catalog = []
        for tool in tools:
            catalog.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            )
        branch_line = f"Selected branch: {branch}" if branch else "Selected branch: (default)"
        user_content = f"""User Question:
{user_question}

{branch_line}

Available Tools:
{json.dumps(catalog, indent=2)}

Return a JSON plan selecting the tools needed to answer the question."""
        return [
            ChatMessage(role="system", content=PLANNING_SYSTEM_PROMPT),
            ChatMessage(role="user", content=user_content),
        ]

    def build_documentation_prompt(
        self,
        context_text: str,
        *,
        document_type: str,
        title: str,
    ) -> list[ChatMessage]:
        user_content = f"""Documentation Request

Type: {document_type}
Title: {title}

Repository Context

{context_text}

Generate the requested documentation in Markdown."""
        return [
            ChatMessage(role="system", content=DOCUMENTATION_SYSTEM_PROMPT),
            ChatMessage(role="user", content=user_content),
        ]

    def build_bug_detection_prompt(
        self, context_text: str, user_question: str
    ) -> list[ChatMessage]:
        raise NotImplementedError("Bug detection prompts are not implemented yet")

    def build_pr_review_prompt(self, context_text: str, user_question: str) -> list[ChatMessage]:
        raise NotImplementedError("PR review prompts are not implemented yet")

    def build_audit_prompt(self, context_text: str, user_question: str) -> list[ChatMessage]:
        raise NotImplementedError("Audit prompts are not implemented yet")
