"""Visitor functions for TypeScript declaration nodes (classes, methods, fields, variables)."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Node
    from tt.context import TranslationContext


def _snake(name: str) -> str:
    """Convert camelCase/PascalCase to snake_case."""
    s = re.sub(r'([a-z0-9])([A-Z])', r'_', name)
    return re.sub(r'([A-Z]+)([A-Z][a-z])', r'_', s).lower()


def visit_class_declaration(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Visit a class_declaration node and generate Python class definition.
    
    Handles:
    - Class name extraction
    - Base class (extends clause)
    - Abstract classes (from ABC)
    - Class body translation
    """
    # Check if abstract
    is_abstract = False
    for child in node.children:
        if child.type == 'abstract':
            is_abstract = True
            ctx.add_import('from abc import ABC, abstractmethod')
            break
    
    # Extract class name
    class_name = None
    for child in node.children:
        if child.type == 'identifier':
            class_name = child.text.decode('utf-8')
            break
    
    if not class_name:
        return ''
    
    # Extract base class from heritage clause
    base_class = 'ABC' if is_abstract else None
    heritage = node.child_by_field_name('heritage')
    if heritage:
        extends_clause = heritage.child_by_field_name('clause')
        if not extends_clause:
            # Look for extends_clause in children
            for child in heritage.children:
                if child.type == 'extends_clause':
                    extends_clause = child
                    break
        
        if extends_clause:
            for child in extends_clause.named_children:
                if child.type == 'identifier' or child.type == 'type_identifier':
                    base_class = child.text.decode('utf-8')
                    break
    
    # Set current class context
    ctx.current_class = class_name
    
    # Build class header
    indent = ctx.indent()
    if base_class:
        result = f"{indent}class {class_name}({base_class}):\n"
    else:
        result = f"{indent}class {class_name}:\n"
    
    # Visit class body
    class_body = node.child_by_field_name('body')
    if class_body:
        ctx.indent_level += 1
        body_parts = []
        for child in class_body.named_children:
            translated = visit_node(child, ctx)
            if translated and translated.strip():
                body_parts.append(translated)
        
        if body_parts:
            result += '\n'.join(body_parts)
        else:
            result += f"{ctx.indent()}pass\n"
        
        ctx.indent_level -= 1
    else:
        ctx.indent_level += 1
        result += f"{ctx.indent()}pass\n"
        ctx.indent_level -= 1
    
    # Clear current class context
    ctx.current_class = None
    
    return result


def visit_method_definition(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Visit a method_definition node and generate Python method.
    
    Handles:
    - Method name conversion to snake_case
    - async methods
    - abstract methods (@abstractmethod)
    - static methods (@staticmethod)
    - Access modifiers (public/private/protected)
    - Parameters (adding self)
    """
    # Check modifiers
    is_async = False
    is_static = False
    is_abstract = False
    access_modifier = None
    
    for child in node.children:
        if child.type == 'async':
            is_async = True
        elif child.type == 'static':
            is_static = True
        elif child.type == 'abstract':
            is_abstract = True
            ctx.add_import('from abc import abstractmethod')
        elif child.type == 'accessibility_modifier':
            access_modifier = child.text.decode('utf-8')
    
    # Extract method name
    method_name = None
    name_node = node.child_by_field_name('name')
    if name_node:
        original_name = name_node.text.decode('utf-8')
        method_name = _snake(original_name)
    
    if not method_name:
        return ''
    
    # Extract parameters
    params_node = node.child_by_field_name('parameters')
    if params_node:
        params_str = visit_node(params_node, ctx)
        # Add self/cls if not static
        if is_static:
            if params_str and params_str != '()':
                # Remove outer parens and use as-is
                params_str = params_str.strip('()')
            else:
                params_str = ''
        else:
            if params_str and params_str != '()':
                # Remove outer parens, prepend self
                params_inner = params_str.strip('()')
                params_str = f"self, {params_inner}"
            else:
                params_str = 'self'
    else:
        params_str = 'self' if not is_static else ''
    
    # Build method signature
    indent = ctx.indent()
    decorators = []
    
    if is_abstract:
        decorators.append(f"{indent}@abstractmethod")
    if is_static:
        decorators.append(f"{indent}@staticmethod")
    
    decorator_str = '\n'.join(decorators) + '\n' if decorators else ''
    
    async_keyword = 'async ' if is_async else ''
    signature = f"{indent}{async_keyword}def {method_name}({params_str}):\n"
    
    # Visit method body
    body_node = node.child_by_field_name('body')
    if body_node:
        ctx.indent_level += 1
        ctx.current_method = method_name
        if is_async:
            ctx.in_async_context = True
        
        body_str = visit_node(body_node, ctx)
        
        ctx.in_async_context = False
        ctx.current_method = None
        ctx.indent_level -= 1
        
        if body_str and body_str.strip():
            result = decorator_str + signature + body_str
        else:
            result = decorator_str + signature + f"{ctx.indent()}    pass\n"
    else:
        result = decorator_str + signature + f"{indent}    pass\n"
    
    return result


def visit_field_definition(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Visit a public_field_definition node and generate Python field assignment.
    
    Handles:
    - Instance fields: name: Type = value -> self.name = value
    - Static fields: static name = value -> class-level attribute
    - Type annotations (stripped)
    """
    is_static = False
    is_readonly = False
    
    # Check for static/readonly modifiers
    for child in node.children:
        if child.type == 'static':
            is_static = True
        elif child.type == 'readonly':
            is_readonly = True
    
    # Extract field name
    field_name = None
    name_node = node.child_by_field_name('name')
    if name_node:
        original_name = name_node.text.decode('utf-8')
        field_name = _snake(original_name)
    
    if not field_name:
        return ''
    
    # Extract initial value if present
    value_node = node.child_by_field_name('value')
    value_str = None
    if value_node:
        value_str = visit_node(value_node, ctx)
    
    indent = ctx.indent()
    
    if is_static:
        # Class-level attribute
        if value_str:
            return f"{indent}{field_name} = {value_str}\n"
        else:
            return f"{indent}{field_name} = None\n"
    else:
        # Instance field - generate as self.field = value
        if value_str:
            return f"{indent}self.{field_name} = {value_str}\n"
        else:
            return f"{indent}self.{field_name} = None\n"


def visit_variable_declaration(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Visit a lexical_declaration node and generate Python variable assignment.
    
    Handles:
    - const/let/var declarations
    - Multiple declarators
    - Destructuring patterns (basic support)
    """
    # lexical_declaration contains variable_declarator children
    results = []
    
    for child in node.named_children:
        if child.type == 'variable_declarator':
            # Extract name
            name_node = child.child_by_field_name('name')
            if not name_node:
                continue
            
            # Handle different name types
            if name_node.type == 'identifier':
                var_name = name_node.text.decode('utf-8')
                var_name = _snake(var_name)
            elif name_node.type in ('array_pattern', 'object_pattern'):
                # Basic destructuring - just get the text
                var_name = name_node.text.decode('utf-8')
            else:
                continue
            
            # Extract value
            value_node = child.child_by_field_name('value')
            if value_node:
                value_str = visit_node(value_node, ctx)
                indent = ctx.indent()
                results.append(f"{indent}{var_name} = {value_str}\n")
            else:
                indent = ctx.indent()
                results.append(f"{indent}{var_name} = None\n")
    
    return '\n'.join(results) if results else ''


def visit_formal_parameters(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Visit a formal_parameters node and generate Python parameter list.
    
    Extracts parameter names, strips type annotations, converts to snake_case.
    Returns parameter string WITH surrounding parentheses.
    """
    params = []
    
    for child in node.named_children:
        if child.type == 'required_parameter':
            # Extract parameter pattern (name)
            pattern_node = child.child_by_field_name('pattern')
            if pattern_node:
                if pattern_node.type == 'identifier':
                    param_name = pattern_node.text.decode('utf-8')
                    param_name = _snake(param_name)
                    params.append(param_name)
                elif pattern_node.type in ('array_pattern', 'object_pattern'):
                    # Destructuring parameter - use raw text
                    param_name = pattern_node.text.decode('utf-8')
                    params.append(param_name)
        elif child.type == 'identifier':
            # Direct identifier child (some tree-sitter versions)
            param_name = child.text.decode('utf-8')
            param_name = _snake(param_name)
            params.append(param_name)
    
    # Return comma-separated params WITH parentheses
    if params:
        return '(' + ', '.join(params) + ')'
    else:
        return '()'
