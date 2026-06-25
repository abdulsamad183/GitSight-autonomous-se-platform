from uuid import uuid4

from app.core.config import Settings
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.tools.types import ToolResult
from app.services.ai.types import ChatSource


def test_context_builder_merges_sections():
    builder = ContextBuilder(Settings(rag_max_context_chars=10_000))
    results = [
        ToolResult(
            tool_name="repository", success=True, text="# Repository Metadata\n\nBranches: 2"
        ),
        ToolResult(
            tool_name="search",
            success=True,
            text="# Retrieved Code\n\ndef auth(): pass",
            sources=[
                ChatSource(
                    chunk_id=uuid4(),
                    file_path="auth.py",
                    symbol_name="auth",
                    chunk_type="function",
                    source_tool="search",
                )
            ],
        ),
    ]
    built = builder.build_from_tool_results(results)
    assert "Repository Metadata" in built.text
    assert "Retrieved Code" in built.text
    assert len(built.sources) == 1
    assert built.sources[0].source_tool == "search"
    assert built.tools_used == ["repository", "search"]


def test_context_builder_deduplicates_sources_by_chunk_id():
    builder = ContextBuilder(Settings(rag_max_context_chars=10_000))
    chunk_id = uuid4()
    shared_source = ChatSource(
        chunk_id=chunk_id,
        file_path="auth.py",
        symbol_name="auth",
        chunk_type="function",
        source_tool="search",
    )
    results = [
        ToolResult(
            tool_name="search",
            success=True,
            text="# Retrieved Code\n\nfirst",
            sources=[shared_source],
        ),
        ToolResult(
            tool_name="search",
            success=True,
            text="# Retrieved Code\n\nsecond",
            sources=[shared_source],
        ),
    ]
    built = builder.build_from_tool_results(results)
    assert len(built.sources) == 1
    assert built.sources[0].chunk_id == chunk_id
    assert built.chunks_used == 1


def test_context_builder_respects_char_budget():
    builder = ContextBuilder(Settings(rag_max_context_chars=100))
    results = [
        ToolResult(tool_name="repository", success=True, text="x" * 80),
        ToolResult(tool_name="search", success=True, text="y" * 80),
    ]
    built = builder.build_from_tool_results(results)
    assert len(built.text) <= 100 or built.tools_used == ["repository"]
