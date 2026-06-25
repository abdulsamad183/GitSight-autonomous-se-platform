from app.services.ai.types import ChatMessage

CHAT_SYSTEM_PROMPT = """You are an expert senior software engineer.

Answer ONLY using the provided repository context.
Do not invent functions, files, or behavior.

If the repository context is insufficient, clearly state that additional context is required.

When possible:
- mention file names
- mention class names
- mention method names

Explain clearly and technically.
Do not fabricate answers.

When showing code from the repository context, use fenced markdown code blocks with a language tag \
(e.g. ```python). Use inline backticks for short identifiers, file names, and symbol names."""


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

    def build_documentation_prompt(
        self, context_text: str, user_question: str
    ) -> list[ChatMessage]:
        raise NotImplementedError("Documentation prompts are not implemented yet")

    def build_bug_detection_prompt(
        self, context_text: str, user_question: str
    ) -> list[ChatMessage]:
        raise NotImplementedError("Bug detection prompts are not implemented yet")

    def build_pr_review_prompt(self, context_text: str, user_question: str) -> list[ChatMessage]:
        raise NotImplementedError("PR review prompts are not implemented yet")

    def build_audit_prompt(self, context_text: str, user_question: str) -> list[ChatMessage]:
        raise NotImplementedError("Audit prompts are not implemented yet")
