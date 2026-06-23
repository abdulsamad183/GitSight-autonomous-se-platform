import logging
from dataclasses import dataclass

import tree_sitter_javascript as tsjavascript
import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser

logger = logging.getLogger(__name__)

PY_LANGUAGE = Language(tspython.language())
JS_LANGUAGE = Language(tsjavascript.language())


@dataclass
class SymbolDraft:
    symbol_name: str
    symbol_type: str
    start_line: int
    end_line: int
    signature: str | None


@dataclass
class ImportDraft:
    module_path: str
    dependency_type: str


@dataclass
class ParseResult:
    symbols: list[SymbolDraft]
    imports: list[ImportDraft]


class TreeSitterParser:
    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {
            "python": self._build_parser(PY_LANGUAGE),
            "javascript": self._build_parser(JS_LANGUAGE),
            "typescript": self._build_parser(JS_LANGUAGE),
        }

    @staticmethod
    def _build_parser(language: Language) -> Parser:
        parser = Parser(language)
        return parser

    def parse_file(self, *, language: str, source: bytes) -> ParseResult:
        parser = self._parsers.get(language)
        if parser is None:
            return ParseResult(symbols=[], imports=[])

        try:
            tree = parser.parse(source)
            if language == "python":
                return self._parse_python(tree.root_node, source)
            return self._parse_javascript(tree.root_node, source)
        except Exception:
            logger.exception("Tree-sitter parse failed")
            return ParseResult(symbols=[], imports=[])

    def _parse_python(self, root: Node, source: bytes) -> ParseResult:
        symbols: list[SymbolDraft] = []
        imports: list[ImportDraft] = []

        def walk(node: Node, inside_class: bool = False) -> None:
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="class",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        walk(child, inside_class=True)
                return

            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="method" if inside_class else "function",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                return

            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        imports.append(
                            ImportDraft(
                                module_path=self._node_text(child, source),
                                dependency_type="IMPORT",
                            )
                        )
                    elif child.type == "aliased_import":
                        name_node = child.child_by_field_name("name")
                        if name_node:
                            imports.append(
                                ImportDraft(
                                    module_path=self._node_text(name_node, source),
                                    dependency_type="IMPORT",
                                )
                            )
            elif node.type == "import_from_statement":
                module_node = node.child_by_field_name("module_name")
                if module_node:
                    imports.append(
                        ImportDraft(
                            module_path=self._node_text(module_node, source),
                            dependency_type="FROM_IMPORT",
                        )
                    )

            for child in node.children:
                walk(child, inside_class=inside_class)

        walk(root)
        return ParseResult(symbols=symbols, imports=imports)

    def _parse_javascript(self, root: Node, source: bytes) -> ParseResult:
        symbols: list[SymbolDraft] = []
        imports: list[ImportDraft] = []

        def walk(node: Node, inside_class: bool = False) -> None:
            if node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="class",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        walk(child, inside_class=True)
                return

            if node.type in {"function_declaration", "method_definition"}:
                name_node = node.child_by_field_name("name")
                if name_node:
                    symbol_type = "method" if inside_class or node.type == "method_definition" else "function"
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type=symbol_type,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                return

            if node.type == "import_statement":
                source_node = node.child_by_field_name("source")
                if source_node:
                    module = self._node_text(source_node, source).strip("'\"")
                    imports.append(ImportDraft(module_path=module, dependency_type="IMPORT"))

            if node.type == "call_expression":
                function_node = node.child_by_field_name("function")
                if (
                    function_node
                    and function_node.type == "identifier"
                    and self._node_text(function_node, source) == "require"
                ):
                    args = node.child_by_field_name("arguments")
                    if args:
                        for child in args.children:
                            if child.type == "string":
                                module = self._node_text(child, source).strip("'\"")
                                imports.append(
                                    ImportDraft(module_path=module, dependency_type="REQUIRE")
                                )
                                break

            for child in node.children:
                walk(child, inside_class=inside_class)

        walk(root)
        return ParseResult(symbols=symbols, imports=imports)

    @staticmethod
    def _node_text(node: Node, source: bytes) -> str:
        return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
