"""Visitor functions for TypeScript patterns (destructuring, templates, spread, optional)"""
import re
from tree_sitter import Node
from ..context import TranslationContext
from ..parser import get_field, get_text, get_children_by_type


def visit_object_pattern(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate object destructuring: {a, b} -> multiple assignments"""
    # Extract property names
    props = []
    for child in node.named_children:
        if child.type in ["pair_pattern", "shorthand_property_identifier_pattern"]:
            if child.type == "shorthand_property_identifier_pattern":
                props.append(get_text(child))
            else:
                key_node = get_field(child, "key")
                if key_node:
                    props.append(get_text(key_node))
    
    # Return comma-separated names (used in assignment context)
    return ", ".join(props)


def visit_array_pattern(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate array destructuring: [a, b] = arr"""
    elements = []
    for child in node.named_children:
        if child.type == "identifier":
            elements.append(get_text(child))
        else:
            elements.append(visitor_func(child, ctx))
    
    return ", ".join(elements)


def visit_template_string(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate template string to f-string: `text ${expr}` -> f'text {expr}'"""
    parts = []
    for child in node.children:
        if child.type == "string_fragment":
            parts.append(get_text(child))
        elif child.type == "template_substitution":
            # Extract expression inside ${}
            expr_node = None
            for subchild in child.children:
                if subchild.type not in ["{", "}", "${"]:
                    expr_node = subchild
                    break
            if expr_node:
                expr = visitor_func(expr_node, ctx)
                parts.append(f"{{{expr}}}")
    
    content = "".join(parts)
    return f"f\'{content}\'"


def visit_spread_element(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate spread: ...arr -> *arr or **obj"""
    expr_node = get_field(node, "expression")
    if not expr_node:
        return ""
    
    expr = visitor_func(expr_node, ctx)
    # Determine if it's array spread (*) or object spread (**)
    # Default to array spread
    return f"*{expr}"


def visit_optional_chain(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate optional chaining: obj?.prop -> getattr(obj, 'prop', None)"""
    obj_node = get_field(node, "object")
    prop_node = get_field(node, "property")
    
    if not (obj_node and prop_node):
        return ""
    
    obj = visitor_func(obj_node, ctx)
    prop = get_text(prop_node)
    
    return f"getattr({obj}, \'{prop}\', None)"


def visit_rest_pattern(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate rest pattern: ...rest"""
    arg_node = get_field(node, "argument")
    if not arg_node:
        return ""
    
    arg = visitor_func(arg_node, ctx)
    return f"*{arg}"


def visit_pair_pattern(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate pair pattern in destructuring"""
    key_node = get_field(node, "key")
    value_node = get_field(node, "value")
    
    if key_node and value_node:
        key = get_text(key_node)
        value = visitor_func(value_node, ctx)
        return f"{value}"
    elif key_node:
        return get_text(key_node)
    return ""
