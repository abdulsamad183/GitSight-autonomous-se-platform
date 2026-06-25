from app.services.ai.prompt_builder import CHAT_SYSTEM_PROMPT, PromptBuilder


def test_build_chat_prompt_structure():
    builder = PromptBuilder()
    messages = builder.build_chat_prompt("Repository Context\n\nFile: a.py", "How does auth work?")

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert CHAT_SYSTEM_PROMPT in messages[0].content
    assert "Repository Context" in messages[1].content
    assert "How does auth work?" in messages[1].content
    assert "fenced markdown code blocks" in messages[0].content
