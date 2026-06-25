from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.ai.types import ChatSource


@dataclass
class ToolExecutionContext:
    db: AsyncSession
    user_id: UUID
    repository_id: UUID
    branch: str | None
    settings: Settings


@dataclass(frozen=True)
class ToolInvocation:
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolPlan:
    reasoning: str = ""
    invocations: list[ToolInvocation] = field(default_factory=list)


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    text: str
    data: dict[str, Any] = field(default_factory=dict)
    sources: list[ChatSource] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class ToolExecutionBundle:
    results: list[ToolResult]
    tools_used: list[str]
    reasoning: str = ""
