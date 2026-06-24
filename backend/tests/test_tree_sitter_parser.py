from app.services.analysis.tree_sitter_parser import TreeSitterParser

PYTHON_SOURCE = b"""
import os
from utils.helper import helper_fn

class UserService:
    def get_user(self):
        return None

def create_user():
    return UserService()
"""

JS_SOURCE = b"""
import { foo } from './utils/foo';
const bar = require('../lib/bar');

class AppService {
  run() {}
}

function main() {}
"""

PYTHON_ENUM_SOURCE = b"""
from enum import Enum

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
"""


def test_python_symbol_extraction():
    parser = TreeSitterParser()
    result = parser.parse_file(language="python", source=PYTHON_SOURCE)

    names = {(s.symbol_name, s.symbol_type) for s in result.symbols}
    assert ("UserService", "class") in names
    assert ("get_user", "method") in names
    assert ("create_user", "function") in names

    get_user = next(s for s in result.symbols if s.symbol_name == "get_user")
    assert get_user.parent_class_name == "UserService"
    create_user = next(s for s in result.symbols if s.symbol_name == "create_user")
    assert create_user.parent_class_name is None


def test_python_import_extraction():
    parser = TreeSitterParser()
    result = parser.parse_file(language="python", source=PYTHON_SOURCE)

    modules = {item.module_path for item in result.imports}
    assert "os" in modules
    assert "utils.helper" in modules


def test_javascript_symbol_extraction():
    parser = TreeSitterParser()
    result = parser.parse_file(language="javascript", source=JS_SOURCE)

    names = {(s.symbol_name, s.symbol_type) for s in result.symbols}
    assert ("AppService", "class") in names
    assert ("run", "method") in names
    assert ("main", "function") in names

    run_method = next(s for s in result.symbols if s.symbol_name == "run")
    assert run_method.parent_class_name == "AppService"


def test_javascript_import_extraction():
    parser = TreeSitterParser()
    result = parser.parse_file(language="javascript", source=JS_SOURCE)

    modules = {item.module_path for item in result.imports}
    assert "./utils/foo" in modules
    assert "../lib/bar" in modules


def test_python_enum_extraction():
    parser = TreeSitterParser()
    result = parser.parse_file(language="python", source=PYTHON_ENUM_SOURCE)

    names = {(s.symbol_name, s.symbol_type) for s in result.symbols}
    assert ("Status", "enum") in names
