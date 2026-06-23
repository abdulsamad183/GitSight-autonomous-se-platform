from pathlib import Path
from uuid import UUID

from app.schemas.analysis import DependencyCreate
from app.services.analysis.tree_sitter_parser import ImportDraft


class DependencyExtractor:
    def __init__(self, path_to_file_id: dict[str, UUID]) -> None:
        self.path_to_file_id = path_to_file_id

    def resolve_edges(
        self,
        *,
        source_file_id: UUID,
        source_relative_path: str,
        language: str | None,
        imports: list[ImportDraft],
    ) -> list[DependencyCreate]:
        edges: list[DependencyCreate] = []
        seen: set[tuple[UUID, UUID, str]] = set()

        for item in imports:
            target_path = self._resolve_import_path(
                source_relative_path=source_relative_path,
                module_path=item.module_path,
                language=language,
            )
            if target_path is None:
                continue

            target_id = self.path_to_file_id.get(target_path)
            if target_id is None:
                continue

            key = (source_file_id, target_id, item.dependency_type)
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                DependencyCreate(
                    source_file_id=source_file_id,
                    target_file_id=target_id,
                    dependency_type=item.dependency_type,
                )
            )

        return edges

    def _resolve_import_path(
        self,
        *,
        source_relative_path: str,
        module_path: str,
        language: str | None,
    ) -> str | None:
        if language == "python":
            return self._resolve_python_import(module_path)
        if language in {"javascript", "typescript"}:
            return self._resolve_js_import(source_relative_path, module_path)
        return None

    def _resolve_python_import(self, module_path: str) -> str | None:
        clean = module_path.strip()
        if not clean or clean.startswith("."):
            return None

        parts = clean.split(".")
        candidates = [
            "/".join(parts) + ".py",
            "/".join(parts) + "/__init__.py",
        ]
        for candidate in candidates:
            if candidate in self.path_to_file_id:
                return candidate
        return None

    def _resolve_js_import(self, source_relative_path: str, module_path: str) -> str | None:
        if not module_path.startswith("."):
            return None

        source_dir = Path(source_relative_path).parent
        resolved = (source_dir / module_path).as_posix()

        candidates = [
            resolved,
            f"{resolved}.js",
            f"{resolved}.jsx",
            f"{resolved}.ts",
            f"{resolved}.tsx",
            f"{resolved}/index.js",
            f"{resolved}/index.ts",
        ]
        for candidate in candidates:
            normalized = Path(candidate).as_posix()
            if normalized in self.path_to_file_id:
                return normalized
        return None
