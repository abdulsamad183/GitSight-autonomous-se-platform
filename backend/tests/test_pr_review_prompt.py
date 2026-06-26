from app.services.ai.prompt_builder import PR_REVIEW_SYSTEM_PROMPT, PromptBuilder


def test_build_pr_review_prompt_structure():
    builder = PromptBuilder()
    messages = builder.build_pr_review_prompt(
        "Repository Context\n\n# Pull Request Metadata\n\nNumber: #1",
        pr_title="Fix login bug",
        pr_number=7,
    )

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert PR_REVIEW_SYSTEM_PROMPT in messages[0].content
    assert "# Summary" in messages[0].content
    assert "# Code Quality" in messages[0].content
    assert "# Architecture" in messages[0].content
    assert "# Potential Bugs" in messages[0].content
    assert "# Security" in messages[0].content
    assert "# Breaking Changes" in messages[0].content
    assert "# Testing" in messages[0].content
    assert "# Suggestions" in messages[0].content
    assert "# Recommendation" in messages[0].content
    assert "Approve" in messages[0].content
    assert "Request Changes" in messages[0].content
    assert "Do not invent" in messages[0].content
    assert "PR #7: Fix login bug" in messages[1].content
    assert "Pull Request Metadata" in messages[1].content
