from app.services.exceptions import ValidationError
from app.services.graph.graph_query_service import (
    compute_blast_radius,
    find_import_paths,
    _build_adjacency,
    _clamp_depth,
    _reverse_adjacency,
)


def _edges():
    # a -> b -> c
    # a -> d
    # e -> b
    return [
        {"source_path": "a.py", "target_path": "b.py"},
        {"source_path": "b.py", "target_path": "c.py"},
        {"source_path": "a.py", "target_path": "d.py"},
        {"source_path": "e.py", "target_path": "b.py"},
    ]


def test_build_and_reverse_adjacency():
    adj = _build_adjacency(_edges())
    assert set(adj["a.py"]) == {"b.py", "d.py"}
    rev = _reverse_adjacency(adj)
    assert set(rev["b.py"]) == {"a.py", "e.py"}


def test_blast_radius_dependents_multi_hop():
    adj = _build_adjacency(_edges())
    rev = _reverse_adjacency(adj)
    # Who depends on c.py? b imports c, a and e import b
    nodes = compute_blast_radius(rev, start_file="c.py", max_depth=2)
    by_path = {path: hop for path, hop in nodes}
    assert by_path["b.py"] == 1
    assert by_path["a.py"] == 2
    assert by_path["e.py"] == 2
    assert "c.py" not in by_path


def test_blast_radius_dependencies_direction():
    adj = _build_adjacency(_edges())
    nodes = compute_blast_radius(adj, start_file="a.py", max_depth=2)
    by_path = {path: hop for path, hop in nodes}
    assert by_path["b.py"] == 1
    assert by_path["d.py"] == 1
    assert by_path["c.py"] == 2


def test_blast_radius_respects_max_depth():
    adj = _build_adjacency(_edges())
    nodes = compute_blast_radius(adj, start_file="a.py", max_depth=1)
    assert {path for path, _ in nodes} == {"b.py", "d.py"}


def test_find_import_paths():
    adj = _build_adjacency(_edges())
    paths = find_import_paths(adj, source_file="a.py", target_file="c.py", max_depth=5)
    assert paths == [["a.py", "b.py", "c.py"]]


def test_find_import_paths_none_within_depth():
    adj = _build_adjacency(_edges())
    paths = find_import_paths(adj, source_file="a.py", target_file="c.py", max_depth=1)
    assert paths == []


def test_find_import_paths_same_file():
    adj = _build_adjacency(_edges())
    assert find_import_paths(adj, source_file="a.py", target_file="a.py") == []


def test_clamp_depth_rejects_invalid():
    try:
        _clamp_depth(0)
        assert False, "expected ValidationError"
    except ValidationError:
        pass
    try:
        _clamp_depth(99)
        assert False, "expected ValidationError"
    except ValidationError:
        pass
