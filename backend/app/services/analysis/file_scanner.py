from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.schemas.analysis import FileCreate
from app.utils.file_filter import (
    detect_language,
    is_binary_content,
    is_parseable_file,
    is_too_large,
    read_binary_sample,
    should_skip_dir,
    should_skip_file,
)


@dataclass
class ScannedFile:
    draft: FileCreate
    absolute_path: Path
    parseable: bool


class FileScanner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def scan(self, root: Path) -> list[ScannedFile]:
        results: list[ScannedFile] = []

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if any(should_skip_dir(part) for part in path.relative_to(root).parts[:-1]):
                continue

            if should_skip_file(path.name):
                continue

            try:
                size_bytes = path.stat().st_size
            except OSError:
                continue

            if is_too_large(size_bytes, self.settings.max_file_size_bytes):
                continue

            extension = path.suffix.lower() if path.suffix else None
            language = detect_language(extension)

            is_binary = False
            try:
                sample = read_binary_sample(path)
                is_binary = is_binary_content(sample)
            except OSError:
                continue

            relative_path = path.relative_to(root).as_posix()
            draft = FileCreate(
                relative_path=relative_path,
                file_name=path.name,
                extension=extension,
                language=language,
                size_bytes=size_bytes,
                is_binary=is_binary,
            )
            parseable = is_parseable_file(extension, language, is_binary)
            results.append(ScannedFile(draft=draft, absolute_path=path, parseable=parseable))

        return results
