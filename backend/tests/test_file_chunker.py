from app.utils.file_chunker import chunk_css_file, chunk_text_file


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
