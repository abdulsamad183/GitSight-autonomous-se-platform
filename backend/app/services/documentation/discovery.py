from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.models.repository_document import DocumentType
from app.repositories import code_chunk_repository, snapshot_repository

MIN_DOCUMENT_LENGTH = 50


@dataclass(frozen=True)
class DiscoveredDocument:
    file_path: str
    content: str
    title: str


def _path_priority(document_type: DocumentType, relative_path: str) -> int | None:
    """Lower score = higher priority. None means not a candidate."""
    path = relative_path.replace("\\", "/")
    lower = path.lower()
    name = path.rsplit("/", 1)[-1].lower()

    if document_type == DocumentType.REPOSITORY_OVERVIEW:
        if name == "readme.md" and "/" not in path:
            return 0
        if name.startswith("readme") and name.endswith(".md"):
            return 1 if "/" not in path else 2
        if lower.endswith(".md") and "/" not in path:
            return 3
        return None

    if document_type == DocumentType.ARCHITECTURE_OVERVIEW:
        if lower in {"docs/architecture.md", "architecture.md"}:
            return 0
        if "architecture" in lower and lower.endswith(".md"):
            return 1 if lower.startswith("docs/") else 2
        return None

    if document_type == DocumentType.MODULES:
        if lower.startswith("docs/modules/") and lower.endswith(".md"):
            return 0
        if "module" in lower and lower.endswith(".md") and lower.startswith("docs/"):
            return 1
        return None

    if document_type == DocumentType.CLASSES:
        if lower.startswith("docs/api/") and lower.endswith(".md"):
            return 0
        if "class" in lower and lower.endswith(".md") and lower.startswith("docs/"):
            return 1
        return None

    if document_type == DocumentType.FUNCTIONS:
        if lower.startswith("docs/api/") and lower.endswith(".md"):
            return 0
        if any(k in lower for k in ("function", "api", "reference")) and lower.endswith(".md"):
            return 1 if lower.startswith("docs/") else None
        return None

    if document_type == DocumentType.BRANCH_SUMMARY:
        if lower in {"docs/branches.md", "changelog.md"}:
            return 0
        if "branch" in lower and lower.endswith(".md"):
            return 1
        return None

    return None


async def _list_markdown_files(
    db: AsyncSession,
    *,
    repository_id: UUID,
    branch: str,
) -> list[File]:
    snapshot = await snapshot_repository.get_for_branch(db, repository_id, branch)
    if snapshot is None:
        return []

    result = await db.execute(
        select(File)
        .where(
            File.snapshot_id == snapshot.id,
            File.is_binary.is_(False),
        )
        .order_by(File.relative_path)
    )
    files = list(result.scalars().all())
    return [
        f
        for f in files
        if (f.extension or "").lower() in {".md", ".mdx", ".rst"}
        or (f.file_name or "").lower().startswith("readme")
    ]


async def _reconstruct_file_content(
    db: AsyncSession,
    *,
    repository_id: UUID,
    file_path: str,
    branch: str,
) -> str:
    chunks = await code_chunk_repository.list_by_file(
        db,
        repository_id=repository_id,
        file_path=file_path,
        branch_name=branch,
    )
    if not chunks:
        return ""
    return "\n\n".join(chunk.content.strip() for chunk in chunks if chunk.content.strip())


class ExistingDocumentationDiscovery:
    async def find(
        self,
        db: AsyncSession,
        *,
        repository_id: UUID,
        document_type: DocumentType,
        branch: str,
    ) -> DiscoveredDocument | None:
        files = await _list_markdown_files(db, repository_id=repository_id, branch=branch)
        if not files:
            return None

        scored: list[tuple[int, str, File]] = []
        for file in files:
            priority = _path_priority(document_type, file.relative_path)
            if priority is not None:
                scored.append((priority, file.relative_path, file))

        if not scored:
            if document_type == DocumentType.REPOSITORY_OVERVIEW:
                for file in files:
                    if file.relative_path.lower().endswith(".md"):
                        scored.append((10, file.relative_path, file))
            elif document_type in {
                DocumentType.ARCHITECTURE_OVERVIEW,
                DocumentType.MODULES,
                DocumentType.CLASSES,
                DocumentType.FUNCTIONS,
            }:
                for file in files:
                    path = file.relative_path.replace("\\", "/").lower()
                    if path.startswith("docs/") and path.endswith(".md"):
                        scored.append((10, file.relative_path, file))

        if not scored:
            return None

        scored.sort(key=lambda item: (item[0], item[1]))
        best_path = scored[0][1]

        content = await _reconstruct_file_content(
            db,
            repository_id=repository_id,
            file_path=best_path,
            branch=branch,
        )
        if len(content.strip()) < MIN_DOCUMENT_LENGTH:
            return None

        title = _title_from_path(best_path, document_type)
        return DiscoveredDocument(file_path=best_path, content=content, title=title)


def _title_from_path(file_path: str, document_type: DocumentType) -> str:
    from app.models.repository_document import DOCUMENT_TYPE_TITLES

    if document_type == DocumentType.REPOSITORY_OVERVIEW and file_path.lower().startswith("readme"):
        return DOCUMENT_TYPE_TITLES[document_type]
    name = file_path.rsplit("/", 1)[-1]
    if name.lower().endswith(".md"):
        name = name[:-3]
    return name.replace("-", " ").replace("_", " ").title()
