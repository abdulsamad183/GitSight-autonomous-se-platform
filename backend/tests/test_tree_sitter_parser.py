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


def test_python_symbol_extraction():
    parser = TreeSitterParser()
    result = parser.parse_file(language="python", source=PYTHON_SOURCE)

    names = {(s.symbol_name, s.symbol_type) for s in result.symbols}
    assert ("UserService", "class") in names
    assert ("get_user", "method") in names
    assert ("create_user", "function") in names


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


def test_javascript_import_extraction():
    parser = TreeSitterParser()
    result = parser.parse_file(language="javascript", source=JS_SOURCE)

    modules = {item.module_path for item in result.imports}
    assert "./utils/foo" in modules
    assert "../lib/bar" in modules
