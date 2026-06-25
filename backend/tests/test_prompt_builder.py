from app.services.ai.prompt_builder import CHAT_SYSTEM_PROMPT, PromptBuilder


def test_build_chat_prompt_structure():
    builder = PromptBuilder()
    messages = builder.build_chat_prompt("Repository Context\n\nFile: a.py", "How does auth work?")

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert CHAT_SYSTEM_PROMPT in messages[0].content
    assert "internal repository tools" in messages[0].content
    assert "Repository Context" in messages[1].content
    assert "How does auth work?" in messages[1].content
    assert "fenced markdown code blocks" in messages[0].content


def test_build_planning_prompt_includes_tools():
    from app.services.ai.tools.repository_metadata_tool import RepositoryMetadataTool

    builder = PromptBuilder()
    messages = builder.build_planning_prompt(
        "How many branches?",
        "main",
        [RepositoryMetadataTool()],
    )
    assert messages[0].role == "system"
    assert "JSON" in messages[0].content
    assert "repository" in messages[1].content
    assert "How many branches?" in messages[1].content
