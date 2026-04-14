"""Tree-sitter parser for TypeScript files."""
from __future__ import annotations

from pathlib import Path

import tree_sitter
from tree_sitter_typescript import language_typescript


def parse_file(file_path: str | Path) -> tree_sitter.Node:
    """Parse a TypeScript file and return the root AST node.
    
    Args:
        file_path: Path to the TypeScript file to parse
        
    Returns:
        Root node of the parsed AST
    """
    path = Path(file_path)
    with open(path, rb) as f:
        source_code = f.read()
    
    parser = tree_sitter.Parser(language_typescript())
    tree = parser.parse(source_code)
    return tree.root_node
