from __future__ import annotations
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Node
    from ..context import TranslationContext


def visit_object_pattern(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Translate object destructuring pattern to Python assignments.
    const {a, b, c} = obj -> a = obj['a']; b = obj['b']; c = obj['c']
    const {a: renamed} = obj -> renamed = obj['a']
    const {a, ...rest} = obj -> a = obj['a']; rest = {k:v for k,v in obj.items() if k != 'a'}
    """
    parts = []
    rest_name = None
    collected_keys = []
    
    for child in node.children:
        if child.type == '{' or child.type == '}' or child.type == ',':
            continue
        
        if child.type == 'rest_pattern':
            # Extract rest variable name
            rest_child = child.child_by_field_name('name')
            if rest_child:
                rest_name = rest_child.text.decode()
        
        elif child.type == 'pair_pattern':
            # Renamed destructuring: {key: newName}
            key_node = child.child_by_field_name('key')
            value_node = child.child_by_field_name('value')
            if key_node and value_node:
                key = key_node.text.decode()
                new_name = value_node.text.decode()
                collected_keys.append(key)
                parts.append(f"{new_name} = obj['{key}']")
        
        elif child.type == 'shorthand_property_identifier_pattern':
            # Simple destructuring: {a}
            name = child.text.decode()
            collected_keys.append(name)
            parts.append(f"{name} = obj['{name}']")
    
    # Add rest pattern if present
    if rest_name and collected_keys:
        excluded = ', '.join(f"'{k}'" for k in collected_keys)
        parts.append(f"{rest_name} = {{k:v for k,v in obj.items() if k not in [{excluded}]}}")
    elif rest_name:
        parts.append(f"{rest_name} = dict(obj)")
    
    return '; '.join(parts)


def visit_array_pattern(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Translate array destructuring pattern to Python tuple unpacking.
    const [a, b] = arr -> a, b = arr
    const [first, ...rest] = arr -> first, *rest = arr
    """
    elements = []
    
    for child in node.children:
        if child.type == '[' or child.type == ']' or child.type == ',':
            continue
        
        if child.type == 'rest_pattern':
            # Rest element: ...rest
            rest_child = child.child_by_field_name('name')
            if rest_child:
                elements.append(f"*{rest_child.text.decode()}")
        else:
            # Regular element
            elements.append(visit_node(child, ctx))
    
    return ', '.join(elements)


def visit_template_string(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Translate template string to Python f-string.
    `hello ${name} world` -> f'hello {name} world'
    """
    parts = []
    
    for child in node.children:
        if child.type == '`':
            continue
        elif child.type == 'string_fragment':
            parts.append(child.text.decode())
        elif child.type == 'template_substitution':
            # Extract expression from ${...}
            expr_text = child.text.decode()[2:-1]  # Remove ${ and }
            parts.append(f"{{{expr_text}}}")
    
    content = ''.join(parts)
    return f"f'{content}'"


def visit_spread_element(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Translate spread element to Python unpacking.
    ...arr -> *arr (in most contexts)
    """
    expr = None
    for child in node.children:
        if child.type == '...':
            continue
        expr = visit_node(child, ctx)
    
    return f"*{expr}" if expr else "*"


def visit_nullish_coalescing(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Translate nullish coalescing operator.
    x ?? y -> x if x is not None else y
    """
    left = node.child_by_field_name('left')
    right = node.child_by_field_name('right')
    
    if not left or not right:
        return node.text.decode()
    
    left_expr = visit_node(left, ctx)
    right_expr = visit_node(right, ctx)
    
    return f"{left_expr} if {left_expr} is not None else {right_expr}"


def visit_optional_chain(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Translate optional chaining operator.
    x?.y -> getattr(x, 'y', None)
    x?.y?.z -> nested getattr
    x?.method(args) -> x.method(args) if x is not None else None
    """
    obj = node.child_by_field_name('object')
    prop = node.child_by_field_name('property')
    
    if not obj:
        return node.text.decode()
    
    obj_expr = visit_node(obj, ctx)
    
    # Check if this is a method call
    parent = node.parent
    if parent and parent.type == 'call_expression':
        # x?.method(args) - handle at call_expression level
        if prop:
            prop_name = prop.text.decode()
            return f"{obj_expr}.{prop_name} if {obj_expr} is not None else None"
    
    # Property access: x?.y
    if prop:
        prop_name = prop.text.decode()
        return f"getattr({obj_expr}, '{prop_name}', None)"
    
    return obj_expr


def visit_type_annotation(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Convert TypeScript type annotations to Python type hints.
    : string -> : str
    : number -> : float
    : boolean -> : bool
    Complex types: strip or convert
    """
    type_node = None
    for child in node.children:
        if child.type == ':':
            continue
        type_node = child
        break
    
    if not type_node:
        return ""
    
    ts_type = type_node.text.decode().strip()
    
    # Basic type mappings
    type_map = {
        'string': 'str',
        'number': 'float',
        'boolean': 'bool',
        'void': 'None',
        'any': 'Any',
        'object': 'dict',
        'undefined': 'None'
    }
    
    # Check for exact match
    if ts_type in type_map:
        return f": {type_map[ts_type]}"
    
    # Check for array type: Type[]
    if ts_type.endswith('[]'):
        inner_type = ts_type[:-2]
        inner_mapped = type_map.get(inner_type, inner_type)
        return f": list[{inner_mapped}]"
    
    # For complex types, just strip or return as-is
    # This includes generic types, union types, etc.
    return f": {ts_type}"


def visit_non_null_assertion(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Strip TypeScript non-null assertion operator.
    x! -> x
    """
    for child in node.children:
        if child.type == '!':
            continue
        return visit_node(child, ctx)
    
    return node.text.decode()
