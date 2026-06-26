from app.services.ai.prompt_builder import DOCUMENTATION_SYSTEM_PROMPT, PromptBuilder


def test_build_documentation_prompt_structure():
    builder = PromptBuilder()
    messages = builder.build_documentation_prompt(
        "Repository Context\n\nFile: auth.py",
        document_type="repository_overview",
        title="Repository Overview",
    )

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert DOCUMENTATION_SYSTEM_PROMPT in messages[0].content
    assert "repository_overview" in messages[1].content
    assert "Repository Overview" in messages[1].content
    assert "auth.py" in messages[1].content
    assert "Do not invent" in messages[0].content
