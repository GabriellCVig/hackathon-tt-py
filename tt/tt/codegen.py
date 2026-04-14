"""Code generator for TypeScript to Python translation.

Walks tree-sitter AST and produces Python code using visitor functions.
"""
from __future__ import annotations

import re
from pathlib import Path

import tree_sitter

from tt.context import TranslationContext
from tt.import_mapper import ImportMapper
from tt.visitors import VISITOR_MAP


def _snake_case(name: str) -> str:
    """Convert camelCase/PascalCase to snake_case."""
    s1 = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class CodeGenerator:
    """Generates Python code from TypeScript AST."""
    
    def __init__(self):
        """Initialize code generator with context and import mapper."""
        self.ctx = TranslationContext()
        self.mapper = ImportMapper()
    
    def generate(self, root_node: tree_sitter.Node) -> str:
        """Generate complete Python source code from AST root.
        
        Args:
            root_node: Root node of the parsed TypeScript AST
            
        Returns:
            Complete Python source code as string
        """
        # Visit the entire tree starting from root
        code = self._visit_internal(root_node, self.ctx)
        return code
    
    def _visit_internal(self, node: tree_sitter.Node, ctx: TranslationContext) -> str:
        """Internal visit method that matches the signature expected by visitors.
        
        This method is passed to visitor functions as the recursive callback.
        Note: ctx parameter is accepted but self.ctx is used for consistency.
        
        Args:
            node: Current AST node to process
            ctx: Translation context (passed by visitors, but self.ctx is used)
            
        Returns:
            Generated Python code for this node
        """
        if node is None:
            return ""
        
        node_type = node.type
        
        # Check VISITOR_MAP for specialized handlers
        if node_type in VISITOR_MAP:
            visitor_func = VISITOR_MAP[node_type]
            # Pass node, self.ctx (not the parameter), and this method as recursive callback
            return visitor_func(node, self.ctx, self._visit_internal)
        
        # Handle leaf nodes and special cases
        if node_type == "identifier":
            return self._handle_identifier(node)
        
        elif node_type == "property_identifier":
            text = node.text.decode("utf-8")
            return _snake_case(text)
        
        elif node_type == "this":
            return "self"
        
        elif node_type in ("true", "false"):
            return node.text.decode("utf-8").capitalize()
        
        elif node_type in ("null", "undefined"):
            return "None"
        
        elif node_type == "number":
            return node.text.decode("utf-8")
        
        elif node_type == "string":
            # Convert to Python string (handle both single and double quotes)
            text = node.text.decode("utf-8")
            # Keep quotes as-is for now
            return text
        
        elif node_type == "comment":
            return self._handle_comment(node)
        
        elif node_type == "program":
            # Visit all top-level children
            parts = []
            for child in node.named_children:
                result = self._visit_internal(child, self.ctx)
                if result and result.strip():
                    parts.append(result)
            return "\n".join(parts)
        
        elif node_type == "export_statement":
            # Visit the declaration inside export
            for child in node.named_children:
                if child.type != "export":
                    return self._visit_internal(child, self.ctx)
            return ""
        
        elif node_type == "import_statement":
            # Skip imports - they are handled by import_mapper
            return ""
        
        # Default: visit children and concatenate
        else:
            parts = []
            for child in node.named_children:
                result = self._visit_internal(child, self.ctx)
                if result:
                    parts.append(result)
            return " ".join(parts) if parts else ""
    
    def _handle_identifier(self, node: tree_sitter.Node) -> str:
        """Handle identifier node conversion.
        
        Args:
            node: Identifier node
            
        Returns:
            Python identifier (snake_case)
        """
        text = node.text.decode("utf-8")
        
        # Special case: this -> self
        if text == "this":
            return "self"
        
        # Convert to snake_case
        return _snake_case(text)
    
    def _handle_comment(self, node: tree_sitter.Node) -> str:
        """Handle comment node conversion.
        
        Args:
            node: Comment node
            
        Returns:
            Python comment
        """
        text = node.text.decode("utf-8")
        
        # Single-line comment: // -> #
        if text.startswith("//"):
            return "#" + text[2:]
        
        # Multi-line comment: /* */ -> triple-quote
        if text.startswith("/*") and text.endswith("*/"):
            inner = text[2:-2].strip()
            return '"""' + inner + '"""'
        
        return text
