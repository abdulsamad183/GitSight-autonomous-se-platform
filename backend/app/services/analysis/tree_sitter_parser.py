import logging
from dataclasses import dataclass

import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_javascript as tsjavascript
import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser

logger = logging.getLogger(__name__)

PY_LANGUAGE = Language(tspython.language())
JS_LANGUAGE = Language(tsjavascript.language())
GO_LANGUAGE = Language(tsgo.language())
C_LANGUAGE = Language(tsc.language())
CPP_LANGUAGE = Language(tscpp.language())


@dataclass
class SymbolDraft:
    symbol_name: str
    symbol_type: str
    start_line: int
    end_line: int
    signature: str | None
    parent_class_name: str | None = None


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
            "go": self._build_parser(GO_LANGUAGE),
            "c": self._build_parser(C_LANGUAGE),
            "cpp": self._build_parser(CPP_LANGUAGE),
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
            if language == "go":
                return self._parse_go(tree.root_node, source)
            if language == "c":
                return self._parse_c(tree.root_node, source)
            if language == "cpp":
                return self._parse_cpp(tree.root_node, source)
            return self._parse_javascript(tree.root_node, source)
        except Exception:
            logger.exception("Tree-sitter parse failed")
            return ParseResult(symbols=[], imports=[])

    def _parse_python(self, root: Node, source: bytes) -> ParseResult:
        symbols: list[SymbolDraft] = []
        imports: list[ImportDraft] = []
        class_stack: list[str] = []

        def _is_enum_class(node: Node) -> bool:
            argument_list = node.child_by_field_name("superclasses")
            if argument_list is None:
                return False
            enum_names = {"Enum", "IntEnum", "StrEnum", "Flag", "IntFlag"}
            for child in argument_list.children:
                if child.type in {"identifier", "attribute"}:
                    base_name = self._node_text(child, source).split(".")[-1]
                    if base_name in enum_names:
                        return True
            return False

        def walk(node: Node, inside_class: bool = False) -> None:
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    class_name = self._node_text(name_node, source)
                    symbol_type = "enum" if _is_enum_class(node) else "class"
                    symbols.append(
                        SymbolDraft(
                            symbol_name=class_name,
                            symbol_type=symbol_type,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                    class_stack.append(class_name)
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        walk(child, inside_class=True)
                if name_node:
                    class_stack.pop()
                return

            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    is_method = inside_class or bool(class_stack)
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="method" if is_method else "function",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                            parent_class_name=(
                                class_stack[-1] if is_method and class_stack else None
                            ),
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
        class_stack: list[str] = []

        def walk(node: Node, inside_class: bool = False) -> None:
            if node.type == "interface_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="interface",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                return

            if node.type == "enum_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="enum",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                return

            if node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    class_name = self._node_text(name_node, source)
                    symbols.append(
                        SymbolDraft(
                            symbol_name=class_name,
                            symbol_type="class",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                    class_stack.append(class_name)
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        walk(child, inside_class=True)
                if name_node:
                    class_stack.pop()
                return

            if node.type in {"function_declaration", "method_definition"}:
                name_node = node.child_by_field_name("name")
                if name_node:
                    is_method = (
                        inside_class or bool(class_stack) or node.type == "method_definition"
                    )
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="method" if is_method else "function",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                            parent_class_name=(
                                class_stack[-1] if is_method and class_stack else None
                            ),
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

    def _parse_go(self, root: Node, source: bytes) -> ParseResult:
        symbols: list[SymbolDraft] = []
        imports: list[ImportDraft] = []

        for node in root.children:
            if node.type == "import_declaration":
                for child in node.children:
                    if child.type == "import_spec":
                        path = self._go_import_path(child, source)
                        if path:
                            imports.append(ImportDraft(module_path=path, dependency_type="IMPORT"))

            if node.type != "type_declaration":
                continue

            for child in node.children:
                if child.type != "type_spec":
                    continue
                name_node = child.child_by_field_name("name")
                if name_node is None:
                    continue
                name = self._node_text(name_node, source)
                for spec_child in child.children:
                    if spec_child.type == "struct_type":
                        symbols.append(
                            SymbolDraft(
                                symbol_name=name,
                                symbol_type="class",
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                                signature=self._node_text(node, source)[:200],
                            )
                        )
                    elif spec_child.type == "interface_type":
                        symbols.append(
                            SymbolDraft(
                                symbol_name=name,
                                symbol_type="interface",
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                                signature=self._node_text(node, source)[:200],
                            )
                        )

        for node in root.children:
            if node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="function",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
            elif node.type == "method_declaration":
                name_node = self._go_method_name(node, source)
                receiver_type = self._go_receiver_type(node, source)
                if name_node:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=name_node,
                            symbol_type="method",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                            parent_class_name=receiver_type,
                        )
                    )

        return ParseResult(symbols=symbols, imports=imports)

    def _parse_c(self, root: Node, source: bytes) -> ParseResult:
        symbols: list[SymbolDraft] = []
        imports: list[ImportDraft] = []

        def walk(node: Node) -> None:
            if node.type == "preproc_include":
                include_path = self._quoted_include_path(node, source)
                if include_path:
                    imports.append(ImportDraft(module_path=include_path, dependency_type="INCLUDE"))
                return

            if node.type == "enum_specifier":
                name_node = self._first_child_of_type(node, "type_identifier")
                if name_node:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="enum",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                return

            if node.type == "struct_specifier":
                name_node = self._first_child_of_type(node, "type_identifier")
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
                return

            if node.type == "function_definition":
                name = self._declarator_name(
                    self._first_child_of_type(node, "function_declarator"), source
                )
                if name:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=name,
                            symbol_type="function",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                return

            for child in node.children:
                walk(child)

        walk(root)
        return ParseResult(symbols=symbols, imports=imports)

    def _parse_cpp(self, root: Node, source: bytes) -> ParseResult:
        symbols: list[SymbolDraft] = []
        imports: list[ImportDraft] = []
        class_stack: list[str] = []

        def walk(node: Node, inside_class: bool = False) -> None:
            if node.type == "preproc_include":
                include_path = self._quoted_include_path(node, source)
                if include_path:
                    imports.append(ImportDraft(module_path=include_path, dependency_type="INCLUDE"))
                return

            if node.type == "enum_specifier":
                name_node = self._first_child_of_type(node, "type_identifier")
                if name_node:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=self._node_text(name_node, source),
                            symbol_type="enum",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                return

            if node.type == "class_specifier":
                name_node = self._first_child_of_type(node, "type_identifier")
                if name_node:
                    class_name = self._node_text(name_node, source)
                    symbols.append(
                        SymbolDraft(
                            symbol_name=class_name,
                            symbol_type="class",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                    class_stack.append(class_name)
                    body = self._first_child_of_type(node, "field_declaration_list")
                    if body:
                        for child in body.children:
                            walk(child, inside_class=True)
                    class_stack.pop()
                return

            if node.type == "function_definition" and not inside_class:
                name = self._declarator_name(
                    self._first_child_of_type(node, "function_declarator"), source
                )
                if name:
                    symbols.append(
                        SymbolDraft(
                            symbol_name=name,
                            symbol_type="function",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=self._node_text(node, source)[:200],
                        )
                    )
                return

            if node.type == "field_declaration" and inside_class:
                declarator = self._first_child_of_type(node, "function_declarator")
                if declarator:
                    name = self._declarator_name(declarator, source)
                    if name and class_stack:
                        symbols.append(
                            SymbolDraft(
                                symbol_name=name,
                                symbol_type="method",
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                                signature=self._node_text(node, source)[:200],
                                parent_class_name=class_stack[-1],
                            )
                        )
                return

            for child in node.children:
                walk(child, inside_class=inside_class)

        walk(root)
        return ParseResult(symbols=symbols, imports=imports)

    @staticmethod
    def _declarator_name(declarator: Node | None, source: bytes) -> str | None:
        if declarator is None:
            return None
        for node_type in ("identifier", "field_identifier"):
            name_node = TreeSitterParser._first_child_of_type(declarator, node_type)
            if name_node:
                return source[name_node.start_byte : name_node.end_byte].decode(
                    "utf-8", errors="replace"
                )
        return None

    @staticmethod
    def _first_child_of_type(node: Node, node_type: str) -> Node | None:
        for child in node.children:
            if child.type == node_type:
                return child
        return None

    @staticmethod
    def _quoted_include_path(node: Node, source: bytes) -> str | None:
        for child in node.children:
            if child.type != "string_literal":
                continue
            text = source[child.start_byte : child.end_byte].decode("utf-8", errors="replace")
            if text.startswith('"') and text.endswith('"'):
                return text.strip('"')
        return None

    @staticmethod
    def _go_import_path(node: Node, source: bytes) -> str | None:
        for child in node.children:
            if child.type == "interpreted_string_literal":
                text = source[child.start_byte : child.end_byte].decode("utf-8", errors="replace")
                return text.strip('"')
        return None

    @staticmethod
    def _go_method_name(node: Node, source: bytes) -> str | None:
        for child in node.children:
            if child.type == "field_identifier":
                return source[child.start_byte : child.end_byte].decode("utf-8", errors="replace")
        return None

    @staticmethod
    def _go_receiver_type(node: Node, source: bytes) -> str | None:
        for child in node.children:
            if child.type != "parameter_list":
                continue
            for param in child.children:
                if param.type != "parameter_declaration":
                    continue
                for type_node in param.children:
                    if type_node.type == "type_identifier":
                        return source[type_node.start_byte : type_node.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                    if type_node.type == "pointer_type":
                        inner = TreeSitterParser._first_child_of_type(type_node, "type_identifier")
                        if inner:
                            return source[inner.start_byte : inner.end_byte].decode(
                                "utf-8", errors="replace"
                            )
        return None

    @staticmethod
    def _node_text(node: Node, source: bytes) -> str:
        return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
