from uuid import uuid4

from app.services.analysis.dependency_extractor import DependencyExtractor
from app.services.analysis.tree_sitter_parser import ImportDraft


def test_resolve_python_import():
    target_id = uuid4()
    source_id = uuid4()
    path_map = {"utils/helper.py": target_id, "main.py": source_id}
    extractor = DependencyExtractor(path_map)

    edges = extractor.resolve_edges(
        source_file_id=source_id,
        source_relative_path="main.py",
        language="python",
        imports=[ImportDraft(module_path="utils.helper", dependency_type="FROM_IMPORT")],
    )

    assert len(edges) == 1
    assert edges[0].target_file_id == target_id
    assert edges[0].dependency_type == "FROM_IMPORT"


def test_resolve_js_relative_import():
    target_id = uuid4()
    source_id = uuid4()
    path_map = {"src/utils/foo.js": target_id, "src/index.js": source_id}
    extractor = DependencyExtractor(path_map)

    edges = extractor.resolve_edges(
        source_file_id=source_id,
        source_relative_path="src/index.js",
        language="javascript",
        imports=[ImportDraft(module_path="./utils/foo", dependency_type="IMPORT")],
    )

    assert len(edges) == 1
    assert edges[0].target_file_id == target_id


def test_skip_unresolvable_import():
    source_id = uuid4()
    extractor = DependencyExtractor({"main.py": source_id})

    edges = extractor.resolve_edges(
        source_file_id=source_id,
        source_relative_path="main.py",
        language="python",
        imports=[ImportDraft(module_path="external.package", dependency_type="IMPORT")],
    )

    assert edges == []


def test_resolve_go_import():
    target_id = uuid4()
    source_id = uuid4()
    path_map = {"internal/util/helper.go": target_id, "main.go": source_id}
    extractor = DependencyExtractor(path_map)

    edges = extractor.resolve_edges(
        source_file_id=source_id,
        source_relative_path="main.go",
        language="go",
        imports=[
            ImportDraft(module_path="example.com/project/internal/util", dependency_type="IMPORT")
        ],
    )

    assert len(edges) == 1
    assert edges[0].target_file_id == target_id


def test_resolve_c_include():
    target_id = uuid4()
    source_id = uuid4()
    path_map = {"src/foo.h": target_id, "src/main.c": source_id}
    extractor = DependencyExtractor(path_map)

    edges = extractor.resolve_edges(
        source_file_id=source_id,
        source_relative_path="src/main.c",
        language="c",
        imports=[ImportDraft(module_path="foo.h", dependency_type="INCLUDE")],
    )

    assert len(edges) == 1
    assert edges[0].target_file_id == target_id
