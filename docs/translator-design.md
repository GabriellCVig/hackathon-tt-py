# TypeScript-to-Python Translator Design

## Overview

This document describes the architecture for a tree-sitter-based TypeScript-to-Python translator that will convert the Ghostfolio portfolio calculator classes from TypeScript to Python.

## Source Files

- **Base class** (1173 lines): `projects/ghostfolio/apps/api/src/app/portfolio/calculator/portfolio-calculator.ts`
- **ROAI subclass** (1009 lines): `projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts`

## AST Node Types Inventory

The following 124 unique AST node types were found in both TypeScript source files:

### Operators & Punctuation (34)
`!`, `!==`, `${`, `&`, `&&`, `'`, `(`, `)`, `+`, `++`, `+=`, `,`, `-`, `--`, `-=`, `.`, `...`, `/`, `:`, `;`, `<`, `<=`, `=`, `===`, `=>`, `>`, `>=`, `?`, `?.`, `??`, `@`, `[`, `]`, `` ` ``, `{`, `||`, `}`

### Keywords (21)
`abstract`, `as`, `async`, `await`, `boolean`, `break`, `catch`, `class`, `const`, `continue`, `else`, `export`, `extends`, `false`, `for`, `from`, `if`, `import`, `instanceof`, `let`, `new`, `null`, `number`, `object`, `of`, `private`, `protected`, `public`, `readonly`, `return`, `static`, `string`, `this`, `true`, `try`, `undefined`, `void`

### Declarations & Definitions (12)
- `abstract_class_declaration`
- `abstract_method_signature`
- `class_declaration`
- `class_body`
- `method_definition`
- `public_field_definition`
- `lexical_declaration`
- `variable_declarator`
- `export_statement`
- `import_statement`
- `formal_parameters`
- `required_parameter`

### Expressions (23)
- `assignment_expression`
- `augmented_assignment_expression`
- `binary_expression`
- `unary_expression`
- `update_expression`
- `ternary_expression`
- `call_expression`
- `member_expression`
- `new_expression`
- `await_expression`
- `arrow_function`
- `parenthesized_expression`
- `subscript_expression`
- `expression_statement`
- `as_expression`
- `spread_element`
- `optional_chain`
- `template_string`
- `template_substitution`

### Types & Type Annotations (13)
- `type_annotation`
- `type_identifier`
- `type_arguments`
- `array_type`
- `object_type`
- `generic_type`
- `predefined_type`
- `literal_type`
- `intersection_type`
- `parenthesized_type`
- `lookup_type`
- `property_signature`
- `index_signature`

### Patterns & Destructuring (5)
- `array_pattern`
- `object_pattern`
- `object_assignment_pattern`
- `pair_pattern`
- `rest_pattern`
- `shorthand_property_identifier_pattern`

### Control Flow (8)
- `if_statement`
- `else_clause`
- `for_statement`
- `for_in_statement`
- `try_statement`
- `catch_clause`
- `break_statement`
- `continue_statement`
- `return_statement`
- `statement_block`

### Other (8)
- `program`
- `comment`
- `identifier`
- `property_identifier`
- `shorthand_property_identifier`
- `type_identifier`
- `arguments`
- `array`
- `pair`
- `decorator`
- `accessibility_modifier`
- `class_heritage`
- `extends_clause`
- `import_clause`
- `import_specifier`
- `named_imports`
- `string_fragment`

## Visitor Architecture

### Visitor Interface

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from tree_sitter import Node

@dataclass
class TranslationContext:
    """Maintains state during AST traversal and translation"""
    current_class: Optional[str] = None
    current_method: Optional[str] = None
    imports_needed: set[str] = None  # Set of Python imports to add
    scope_stack: List[Dict[str, Any]] = None  # Track variable scopes
    indent_level: int = 0
    in_async_context: bool = False
    type_mappings: Dict[str, str] = None  # TS type -> Python type
    
    def __post_init__(self):
        if self.imports_needed is None:
            self.imports_needed = set()
        if self.scope_stack is None:
            self.scope_stack = [{}]
        if self.type_mappings is None:
            self.type_mappings = {}
    
    def indent(self) -> str:
        return "    " * self.indent_level
    
    def push_scope(self):
        self.scope_stack.append({})
    
    def pop_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
    
    def add_import(self, import_stmt: str):
        self.imports_needed.add(import_stmt)

class NodeVisitor:
    """Base visitor that walks the TypeScript AST and generates Python code"""
    
    def __init__(self, import_map: Dict[str, Any]):
        self.import_map = import_map
    
    def visit(self, node: Node, ctx: TranslationContext) -> str:
        """
        Main visitor dispatch method.
        Routes to specific visit_<node_type> methods.
        Falls back to visit_children if no specific handler exists.
        """
        method_name = f'visit_{node.type}'
        visitor = getattr(self, method_name, self.visit_children)
        return visitor(node, ctx)
    
    def visit_children(self, node: Node, ctx: TranslationContext) -> str:
        """Default: concatenate all child translations"""
        parts = []
        for child in node.children:
            result = self.visit(child, ctx)
            if result:
                parts.append(result)
        return ' '.join(parts)
```

### TranslationContext Schema

The `TranslationContext` dataclass maintains state during AST traversal:

| Field | Type | Purpose |
|-------|------|---------|
| `current_class` | `Optional[str]` | Name of class currently being translated |
| `current_method` | `Optional[str]` | Name of method currently being translated |
| `imports_needed` | `set[str]` | Accumulates Python import statements needed |
| `scope_stack` | `List[Dict[str, Any]]` | Stack of variable scopes (for name resolution) |
| `indent_level` | `int` | Current indentation depth (Python requires precise indentation) |
| `in_async_context` | `bool` | Whether we're inside an async function |
| `type_mappings` | `Dict[str, str]` | Maps TypeScript type names to Python equivalents |

## Import Map Schema

The `tt_import_map.json` file maps TypeScript library calls to Python equivalents:

```json
{
  "libraries": {
    "<ts-library-name>": {
      "python_package": "<python-package-name>",
      "mappings": {
        "<ts-function-or-class>": {
          "python_name": "<python-equivalent>",
          "import_stmt": "<full-import-statement>",
          "translation_notes": "<any special handling needed>"
        }
      }
    }
  }
}
```

## Library Mappings Required

From analyzing the TypeScript imports, the following library mappings are needed:

### big.js → decimal
- `Big` class → `Decimal` from `decimal` module
- All `.mul()`, `.plus()`, `.minus()`, `.div()` → operator overloading

### date-fns → Python datetime + custom utilities
- `differenceInDays` → custom function using `datetime`
- `eachDayOfInterval` → custom generator
- `eachYearOfInterval` → custom generator  
- `format` → `strftime` or custom formatter
- `isAfter`, `isBefore` → `datetime` comparison operators
- `isWithinInterval` → custom function
- `min` → `min()` builtin
- `startOfDay`, `endOfDay` → `datetime.replace()` + `timedelta`
- `startOfYear`, `endOfYear` → `datetime.replace()`
- `subDays` → `timedelta(days=-n)`
- `addMilliseconds` → `timedelta(milliseconds=n)`
- `parseISO` → `datetime.fromisoformat()`
- `isThisYear` → compare with `datetime.now().year`

### lodash → Python builtins
- `isNumber` → `isinstance(x, (int, float))`
- `sortBy` → `sorted(iterable, key=...)`
- `sum` → `sum()` builtin
- `uniqBy` → custom function or list comprehension with seen set
- `cloneDeep` → `copy.deepcopy()`

### class-transformer → dict unpacking
- `plainToClass` → dataclass construction from dict

### NestJS Logger → Python logging
- `Logger.debug`, `Logger.warn` → `logging.debug`, `logging.warning`

### Decorators
- `@LogPerformance` → custom decorator or remove (profile after porting)

## Implementation Priority

Implement AST node visitors in this order to enable incremental testing:

### Phase 1: Core Structure (HIGH PRIORITY)
1. `program` - top-level translation
2. `import_statement`, `import_clause`, `named_imports`, `import_specifier` - dependencies
3. `export_statement` - module exports
4. `class_declaration`, `class_body`, `class_heritage`, `extends_clause` - class structure
5. `method_definition`, `public_field_definition` - class members
6. `formal_parameters`, `required_parameter` - function signatures
7. `statement_block` - code blocks
8. `return_statement` - function returns

### Phase 2: Expressions & Operations (MEDIUM PRIORITY)
9. `identifier`, `property_identifier` - variable/property names
10. `call_expression`, `member_expression`, `arguments` - function/method calls
11. `assignment_expression`, `lexical_declaration`, `variable_declarator` - variable assignment
12. `binary_expression` - arithmetic and comparison operators
13. `ternary_expression` - conditional expressions
14. `new_expression` - object instantiation
15. `template_string`, `template_substitution` - string interpolation
16. `array`, `object`, `pair` - literal data structures

### Phase 3: Control Flow (MEDIUM PRIORITY)
17. `if_statement`, `else_clause` - conditionals
18. `for_statement`, `for_in_statement` - loops
19. `try_statement`, `catch_clause` - exception handling
20. `break_statement`, `continue_statement` - loop control

### Phase 4: Types & Advanced Features (LOW PRIORITY)
21. `type_annotation`, `type_identifier`, `type_arguments` - type hints
22. `abstract_class_declaration`, `abstract_method_signature` - abstract classes
23. `async`, `await`, `await_expression`, `arrow_function` - async patterns
24. `decorator`, `accessibility_modifier` - decorators and access control
25. `array_pattern`, `object_pattern`, `rest_pattern` - destructuring
26. Remaining operators and edge cases

### Phase 5: Polish (LOWEST PRIORITY)
27. `comment` - preserve comments
28. Operator mappings (`??`, `?.`, etc.)
29. Edge case handling

## Translation Strategy

1. **Parse once, cache AST**: Parse both TS files with tree-sitter, cache the AST
2. **Two-pass translation**:
   - **Pass 1**: Collect all type definitions, class names, method signatures
   - **Pass 2**: Generate Python code using visitor pattern
3. **Import resolution**: Accumulate needed imports in `TranslationContext.imports_needed`, write at top of file
4. **Type annotation**: Generate Python type hints from TypeScript type annotations where possible
5. **Testing**: After each phase, verify generated Python is syntactically valid

## Output Structure

For each TypeScript class file, generate:

```
tt/tt/generated/
├── portfolio_calculator.py        (from portfolio-calculator.ts)
└── roai_portfolio_calculator.py   (from roai/portfolio-calculator.ts)
```

Each generated file will have:
1. Python imports (stdlib, then third-party, then local)
2. Type aliases and helper functions
3. Class definition(s)
4. Any required utility functions

## Success Criteria

- [ ] All 124 AST node types mapped to visitor methods
- [ ] All library calls mapped in `tt_import_map.json`
- [ ] Generated Python is syntactically valid (`python -m py_compile`)
- [ ] Generated Python passes `mypy` type checking (after manual type hint review)
- [ ] Core calculation logic preserved (verified by running tests)

## Next Steps

1. Implement core visitor methods (Phase 1)
2. Create library mapping utilities that use `tt_import_map.json`
3. Build integration tests that compare TS and Python outputs
4. Iterate on edge cases and refine mappings
