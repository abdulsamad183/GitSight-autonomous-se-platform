from app.services.file_distribution_service import FileDistributionInput, compute_file_distribution


def test_compute_file_distribution_empty():
    result = compute_file_distribution([])
    assert result.total_files == 0
    assert result.text_files == 0
    assert result.binary_files == 0
    assert result.total_size_bytes == 0
    assert result.language_breakdown == {}
    assert result.largest_files == []


def test_compute_file_distribution_aggregates_language_extension_and_folders():
    files = [
        FileDistributionInput("src/main.py", ".py", "python", 1000, False),
        FileDistributionInput("src/utils.py", ".py", "python", 500, False),
        FileDistributionInput("README.md", ".md", "markdown", 200, False),
        FileDistributionInput("assets/logo.png", ".png", None, 8000, True),
        FileDistributionInput("config.json", ".json", "json", 120, False),
    ]
    result = compute_file_distribution(files, top_files=3, top_folders=3)

    assert result.total_files == 5
    assert result.text_files == 4
    assert result.binary_files == 1
    assert result.total_size_bytes == 9820
    assert result.language_breakdown == {
        "python": 2,
        "markdown": 1,
        "json": 1,
        "unknown": 1,
    }
    assert result.language_percentages["python"] == 40.0
    assert result.extension_breakdown[".py"] == 2
    assert result.extension_breakdown[".png"] == 1
    assert result.largest_files[0].relative_path == "assets/logo.png"
    assert result.largest_files[0].size_bytes == 8000
    folder_paths = {item.folder_path: item for item in result.largest_folders}
    assert folder_paths["src"].file_count == 2
    assert folder_paths["src"].total_size_bytes == 1500
    assert folder_paths["assets"].total_size_bytes == 8000


def test_compute_file_distribution_root_files_grouped():
    files = [
        FileDistributionInput("main.py", ".py", "python", 100, False),
        FileDistributionInput("README.md", ".md", "markdown", 50, False),
    ]
    result = compute_file_distribution(files)
    assert result.largest_folders[0].folder_path == "(root)"
    assert result.largest_folders[0].file_count == 2
