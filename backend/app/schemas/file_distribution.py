from pydantic import BaseModel, Field


class LargestFileItem(BaseModel):
    relative_path: str
    size_bytes: int
    language: str | None
    extension: str | None
    is_binary: bool


class FolderSizeItem(BaseModel):
    folder_path: str
    file_count: int
    total_size_bytes: int


class FileDistributionResponse(BaseModel):
    total_files: int
    text_files: int
    binary_files: int
    total_size_bytes: int
    language_breakdown: dict[str, int] = Field(default_factory=dict)
    language_percentages: dict[str, float] = Field(default_factory=dict)
    extension_breakdown: dict[str, int] = Field(default_factory=dict)
    largest_files: list[LargestFileItem] = Field(default_factory=list)
    largest_folders: list[FolderSizeItem] = Field(default_factory=list)
