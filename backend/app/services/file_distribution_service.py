from collections import Counter
from dataclasses import dataclass

from app.schemas.file_distribution import (
    FileDistributionResponse,
    FolderSizeItem,
    LargestFileItem,
)

DEFAULT_TOP_FILES = 10
DEFAULT_TOP_FOLDERS = 10


@dataclass(frozen=True)
class FileDistributionInput:
    relative_path: str
    extension: str | None
    language: str | None
    size_bytes: int
    is_binary: bool


def _top_level_folder(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").strip("/")
    if not normalized or "/" not in normalized:
        return "(root)"
    return normalized.split("/", 1)[0]


def _extension_key(extension: str | None) -> str:
    if not extension:
        return "(none)"
    return extension.lower()


def _language_key(language: str | None) -> str:
    if not language:
        return "unknown"
    return language


def compute_file_distribution(
    files: list[FileDistributionInput],
    *,
    top_files: int = DEFAULT_TOP_FILES,
    top_folders: int = DEFAULT_TOP_FOLDERS,
) -> FileDistributionResponse:
    if not files:
        return FileDistributionResponse(
            total_files=0,
            text_files=0,
            binary_files=0,
            total_size_bytes=0,
        )

    binary_files = sum(1 for file in files if file.is_binary)
    text_files = len(files) - binary_files
    total_size_bytes = sum(file.size_bytes for file in files)

    language_counter: Counter[str] = Counter()
    extension_counter: Counter[str] = Counter()
    folder_sizes: dict[str, tuple[int, int]] = {}

    for file in files:
        language_counter[_language_key(file.language)] += 1
        extension_counter[_extension_key(file.extension)] += 1
        folder = _top_level_folder(file.relative_path)
        count, size = folder_sizes.get(folder, (0, 0))
        folder_sizes[folder] = (count + 1, size + file.size_bytes)

    language_breakdown = dict(
        sorted(language_counter.items(), key=lambda item: (-item[1], item[0]))
    )
    total_files = len(files)
    language_percentages = {
        language: round((count / total_files) * 100, 1)
        for language, count in language_breakdown.items()
    }
    extension_breakdown = dict(
        sorted(extension_counter.items(), key=lambda item: (-item[1], item[0]))
    )

    largest_files = sorted(files, key=lambda file: file.size_bytes, reverse=True)[:top_files]
    largest_folders = sorted(
        (
            FolderSizeItem(
                folder_path=folder,
                file_count=count,
                total_size_bytes=size,
            )
            for folder, (count, size) in folder_sizes.items()
        ),
        key=lambda item: item.total_size_bytes,
        reverse=True,
    )[:top_folders]

    return FileDistributionResponse(
        total_files=total_files,
        text_files=text_files,
        binary_files=binary_files,
        total_size_bytes=total_size_bytes,
        language_breakdown=language_breakdown,
        language_percentages=language_percentages,
        extension_breakdown=extension_breakdown,
        largest_files=[
            LargestFileItem(
                relative_path=file.relative_path,
                size_bytes=file.size_bytes,
                language=file.language,
                extension=file.extension,
                is_binary=file.is_binary,
            )
            for file in largest_files
        ],
        largest_folders=largest_folders,
    )
