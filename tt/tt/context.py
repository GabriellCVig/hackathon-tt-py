from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class TranslationContext:
    current_class: str = ''
    current_method: str = ''
    base_class: str = ''
    imports_needed: set = field(default_factory=set)
    indent_level: int = 0
    scope_stack: list = field(default_factory=list)
    is_async: bool = False

    def indent_str(self) -> str:
        return '    ' * self.indent_level

    def indent(self):
        self.indent_level += 1

    def dedent(self):
        self.indent_level = max(0, self.indent_level - 1)

    def add_import(self, stmt: str):
        self.imports_needed.add(stmt)

    def push_scope(self, name: str):
        self.scope_stack.append(name)

    def pop_scope(self):
        if self.scope_stack:
            self.scope_stack.pop()
