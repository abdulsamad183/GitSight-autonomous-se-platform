from uuid import uuid4

from app.models.file import File
from app.models.repository import Repository, RepositoryStatus
from app.models.symbol import Symbol, SymbolType
from app.services.graph.base import GraphBuildContext
from app.services.graph.structure_graph_builder import StructureGraphBuilder


def _make_repository() -> Repository:
    return Repository(
        id=uuid4(),
        user_id=uuid4(),
        name="MediFlow",
        repo_url="https://github.com/org/mediflow",
        owner="org",
        repository_name="mediflow",
        default_branch="main",
        latest_commit_hash="abc123",
        branches_analyzed_count=1,
        branches_truncated=False,
        status=RepositoryStatus.ACTIVE,
    )


def _make_file(
    *,
    repository_id,
    snapshot_id,
    relative_path: str,
    file_id=None,
) -> File:
    return File(
        id=file_id or uuid4(),
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        relative_path=relative_path,
        file_name=relative_path.split("/")[-1],
        extension=".py",
        language="python",
        size_bytes=100,
        is_binary=False,
    )


def _make_symbol(
    *,
    repository_id,
    snapshot_id,
    file_id,
    symbol_name: str,
    symbol_type: SymbolType,
    start_line: int,
    end_line: int,
    symbol_id=None,
    parent_symbol_id=None,
) -> Symbol:
    return Symbol(
        id=symbol_id or uuid4(),
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        file_id=file_id,
        symbol_name=symbol_name,
        symbol_type=symbol_type,
        start_line=start_line,
        end_line=end_line,
        signature=None,
        parent_symbol_id=parent_symbol_id,
    )


def test_structure_graph_nodes_and_edges():
    repository = _make_repository()
    snapshot_id = uuid4()

    auth_file = _make_file(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        relative_path="backend/services/auth_service.py",
    )
    user_file = _make_file(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        relative_path="backend/services/user_service.py",
    )

    auth_class = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=auth_file.id,
        symbol_name="AuthService",
        symbol_type=SymbolType.CLASS,
        start_line=1,
        end_line=20,
    )
    login = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=auth_file.id,
        symbol_name="login",
        symbol_type=SymbolType.METHOD,
        start_line=2,
        end_line=5,
        parent_symbol_id=auth_class.id,
    )
    logout = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=auth_file.id,
        symbol_name="logout",
        symbol_type=SymbolType.METHOD,
        start_line=6,
        end_line=9,
        parent_symbol_id=auth_class.id,
    )

    user_class = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=user_file.id,
        symbol_name="UserService",
        symbol_type=SymbolType.CLASS,
        start_line=1,
        end_line=15,
    )
    create_user = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=user_file.id,
        symbol_name="create_user",
        symbol_type=SymbolType.METHOD,
        start_line=2,
        end_line=6,
        parent_symbol_id=user_class.id,
    )

    context = GraphBuildContext(
        repository=repository,
        branch="main",
        files=[auth_file, user_file],
        symbols=[
            (auth_class, auth_file.relative_path),
            (login, auth_file.relative_path),
            (logout, auth_file.relative_path),
            (user_class, user_file.relative_path),
            (create_user, user_file.relative_path),
        ],
    )

    result = StructureGraphBuilder().build(context)

    assert result.graph_type == "structure"
    assert result.stats.files_count == 2
    assert result.stats.classes_count == 2
    assert result.stats.methods_count == 3
    assert result.empty_state is None

    node_ids = {node.id for node in result.nodes}
    assert f"repo_{repository.id}" in node_ids
    assert f"file_{auth_file.id}" in node_ids
    assert f"class_{auth_class.id}" in node_ids
    assert f"method_{login.id}" in node_ids

    edge_pairs = {(edge.source, edge.target) for edge in result.edges}
    assert (f"repo_{repository.id}", f"file_{auth_file.id}") in edge_pairs
    assert (f"file_{auth_file.id}", f"class_{auth_class.id}") in edge_pairs
    assert (f"class_{auth_class.id}", f"method_{login.id}") in edge_pairs
    assert (f"class_{auth_class.id}", f"method_{logout.id}") in edge_pairs


def test_method_parent_via_parent_symbol_id():
    repository = _make_repository()
    snapshot_id = uuid4()
    file = _make_file(repository_id=repository.id, snapshot_id=snapshot_id, relative_path="svc.py")

    auth_class = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=file.id,
        symbol_name="AuthService",
        symbol_type=SymbolType.CLASS,
        start_line=1,
        end_line=20,
    )
    login = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=file.id,
        symbol_name="login",
        symbol_type=SymbolType.METHOD,
        start_line=2,
        end_line=5,
        parent_symbol_id=auth_class.id,
    )

    result = StructureGraphBuilder().build(
        GraphBuildContext(
            repository=repository,
            branch="main",
            files=[file],
            symbols=[(auth_class, file.relative_path), (login, file.relative_path)],
        )
    )

    edge_pairs = {(edge.source, edge.target) for edge in result.edges}
    assert (f"class_{auth_class.id}", f"method_{login.id}") in edge_pairs


def test_method_parent_line_range_fallback():
    repository = _make_repository()
    snapshot_id = uuid4()
    file = _make_file(repository_id=repository.id, snapshot_id=snapshot_id, relative_path="svc.py")

    auth_class = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=file.id,
        symbol_name="AuthService",
        symbol_type=SymbolType.CLASS,
        start_line=1,
        end_line=20,
    )
    login = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=file.id,
        symbol_name="login",
        symbol_type=SymbolType.METHOD,
        start_line=2,
        end_line=5,
        parent_symbol_id=None,
    )

    result = StructureGraphBuilder().build(
        GraphBuildContext(
            repository=repository,
            branch="main",
            files=[file],
            symbols=[(auth_class, file.relative_path), (login, file.relative_path)],
        )
    )

    edge_pairs = {(edge.source, edge.target) for edge in result.edges}
    assert (f"class_{auth_class.id}", f"method_{login.id}") in edge_pairs


def test_empty_repository_no_classes():
    repository = _make_repository()
    snapshot_id = uuid4()
    file = _make_file(repository_id=repository.id, snapshot_id=snapshot_id, relative_path="main.py")
    helper = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=file.id,
        symbol_name="main",
        symbol_type=SymbolType.FUNCTION,
        start_line=1,
        end_line=3,
    )

    result = StructureGraphBuilder().build(
        GraphBuildContext(
            repository=repository,
            branch="main",
            files=[file],
            symbols=[(helper, file.relative_path)],
        )
    )

    assert result.stats.classes_count == 0
    assert result.stats.methods_count == 0
    assert result.stats.functions_count == 1
    assert result.empty_state is not None
    assert "No classes found" in result.empty_state

    method_nodes = [node for node in result.nodes if node.type == "method"]
    assert method_nodes == []


def test_excludes_standalone_functions():
    repository = _make_repository()
    snapshot_id = uuid4()
    file = _make_file(repository_id=repository.id, snapshot_id=snapshot_id, relative_path="util.py")

    helper = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=file.id,
        symbol_name="helper",
        symbol_type=SymbolType.FUNCTION,
        start_line=1,
        end_line=3,
    )

    result = StructureGraphBuilder().build(
        GraphBuildContext(
            repository=repository,
            branch="main",
            files=[file],
            symbols=[(helper, file.relative_path)],
        )
    )

    assert all(node.type != "function" for node in result.nodes)
    assert result.stats.functions_count == 1


def test_large_repository():
    repository = _make_repository()
    snapshot_id = uuid4()
    files = []
    symbols = []

    for index in range(50):
        file = _make_file(
            repository_id=repository.id,
            snapshot_id=snapshot_id,
            relative_path=f"src/module_{index}.py",
        )
        files.append(file)

        class_symbol = _make_symbol(
            repository_id=repository.id,
            snapshot_id=snapshot_id,
            file_id=file.id,
            symbol_name=f"Service{index}",
            symbol_type=SymbolType.CLASS,
            start_line=1,
            end_line=30,
        )
        method_symbol = _make_symbol(
            repository_id=repository.id,
            snapshot_id=snapshot_id,
            file_id=file.id,
            symbol_name="run",
            symbol_type=SymbolType.METHOD,
            start_line=2,
            end_line=5,
            parent_symbol_id=class_symbol.id,
        )
        symbols.extend(
            [
                (class_symbol, file.relative_path),
                (method_symbol, file.relative_path),
            ]
        )

    result = StructureGraphBuilder().build(
        GraphBuildContext(
            repository=repository,
            branch="main",
            files=files,
            symbols=symbols,
        )
    )

    assert result.stats.files_count == 50
    assert result.stats.classes_count == 50
    assert result.stats.methods_count == 50
    assert len(result.nodes) == 1 + 50 + 50 + 50
    assert len(result.edges) == 50 + 50 + 50


def test_classes_without_methods_empty_state():
    repository = _make_repository()
    snapshot_id = uuid4()
    file = _make_file(
        repository_id=repository.id, snapshot_id=snapshot_id, relative_path="model.py"
    )
    model_class = _make_symbol(
        repository_id=repository.id,
        snapshot_id=snapshot_id,
        file_id=file.id,
        symbol_name="EmptyModel",
        symbol_type=SymbolType.CLASS,
        start_line=1,
        end_line=5,
    )

    result = StructureGraphBuilder().build(
        GraphBuildContext(
            repository=repository,
            branch="main",
            files=[file],
            symbols=[(model_class, file.relative_path)],
        )
    )

    assert result.stats.classes_count == 1
    assert result.stats.methods_count == 0
    assert result.empty_state == "Classes found but no methods detected."
