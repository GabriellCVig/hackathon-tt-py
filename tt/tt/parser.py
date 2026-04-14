from __future__ import annotations
import re
from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_typescript as tsts

_LANGUAGE = Language(tsts.language_typescript())
_PARSER = Parser(_LANGUAGE)

def parse_source(source: str):
    tree = _PARSER.parse(source.encode('utf-8'))
    return tree.root_node

def parse_file(path: Path):
    return parse_source(path.read_text(encoding='utf-8'))

def get_children_by_type(node, type_name: str) -> list:
    return [c for c in node.named_children if c.type == type_name]

def get_child_by_field(node, field_name: str):
    return node.child_by_field_name(field_name)

def snake_case(name: str) -> str:
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    return re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s).lower()

def node_text(node) -> str:
    return node.text.decode('utf-8') if node else ''
