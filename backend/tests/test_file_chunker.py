from app.utils.file_chunker import chunk_css_file, chunk_markdown_file, chunk_text_file


def test_chunk_text_file_whole_file_for_small_html():
    content = "<html>\n<body>Hello</body>\n</html>\n"
    chunks = chunk_text_file(file_path="index.html", content=content, whole_file_max_lines=200)
    assert len(chunks) == 1
    assert chunks[0].chunk_type == "file"
    assert "Hello" in chunks[0].content


def test_chunk_text_file_sections_for_large_html():
    lines = "\n".join(f"<p>line {index}</p>" for index in range(250))
    chunks = chunk_text_file(
        file_path="index.html",
        content=lines,
        max_section_lines=100,
        whole_file_max_lines=200,
    )
    assert len(chunks) > 1
    assert all(chunk.chunk_type == "section" for chunk in chunks)


def test_chunk_css_file_splits_rules():
    content = ".a { color: red; }\n.b { color: blue; }\n"
    chunks = chunk_css_file(
        file_path="styles.css",
        content=content,
        whole_file_max_lines=1,
        max_section_lines=50,
    )
    assert len(chunks) >= 1
    assert any(".a" in chunk.content for chunk in chunks)


def test_chunk_markdown_file_splits_on_headings():
    content = (
        "# My Project\n"
        "Overview paragraph.\n"
        "\n"
        "## Installation\n"
        "Run `pip install`.\n"
        "\n"
        "## Usage\n"
        "Import the package.\n"
    )
    chunks = chunk_markdown_file(file_path="README.md", content=content)
    assert len(chunks) == 3
    assert chunks[0].symbol_name == "README.md#My Project"
    assert chunks[1].symbol_name == "README.md#Installation"
    assert "pip install" in chunks[1].content
    assert chunks[2].symbol_name == "README.md#Usage"


def test_chunk_markdown_file_whole_file_without_headings():
    content = "Plain readme with no headings.\nSecond line.\n"
    chunks = chunk_markdown_file(file_path="README.md", content=content)
    assert len(chunks) == 1
    assert chunks[0].chunk_type == "file"
    assert chunks[0].symbol_name == "README.md"


def test_chunk_markdown_file_subdivides_large_heading_section():
    body = "\n".join(f"detail line {index}" for index in range(150))
    content = f"# Setup\n{body}\n"
    chunks = chunk_markdown_file(
        file_path="README.md",
        content=content,
        max_section_lines=50,
        whole_file_max_lines=200,
    )
    assert len(chunks) > 1
    assert all(chunk.chunk_type == "section" for chunk in chunks)
    assert all(chunk.symbol_name.startswith("README.md#Setup") for chunk in chunks)
