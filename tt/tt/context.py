"""Translation context for AST traversal."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TranslationContext:
    """Maintains state during AST traversal and translation."""
    
    current_class: str | None = None
    current_method: str | None = None
    imports_needed: set[str] = field(default_factory=set)
    indent_level: int = 0
    scope_stack: list[dict] = field(default_factory=lambda: [{}])
    in_async_context: bool = False
    type_mappings: dict[str, str] = field(default_factory=dict)
    
    def indent(self) -> str:
        """Return indentation string for current level."""
        return "    " * self.indent_level
    
    def push_scope(self) -> None:
        """Push a new variable scope onto the stack."""
        self.scope_stack.append({})
    
    def pop_scope(self) -> None:
        """Pop the current scope from the stack."""
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
    
    def add_import(self, import_stmt: str) -> None:
        """Add an import statement to the set of needed imports."""
        self.imports_needed.add(import_stmt)
