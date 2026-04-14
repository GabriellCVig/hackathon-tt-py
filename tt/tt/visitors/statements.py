"""Visitor functions for TypeScript statement nodes"""
from __future__ import annotations

from tree_sitter import Node
from ..context import TranslationContext


def visit_if_statement(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate if statement: if (cond) {...} else if {...} else {...}"""
    condition = node.child_by_field_name("condition")
    consequence = node.child_by_field_name("consequence")
    alternative = node.child_by_field_name("alternative")
    
    if not condition or not consequence:
        return ""
    
    # Translate condition (strip parentheses if present)
    cond_str = visit_node(condition, ctx)
    if cond_str.startswith("(") and cond_str.endswith(")"):
        cond_str = cond_str[1:-1]
    
    indent = ctx.indent()
    result = f"{indent}if {cond_str}:\n"
    
    # Translate consequence block
    ctx.indent_level += 1
    cons_str = visit_node(consequence, ctx)
    ctx.indent_level -= 1
    result += cons_str if cons_str else f"{ctx.indent()}    pass\n"
    
    # Handle alternative (else if / else)
    if alternative:
        alt_indent = ctx.indent()
        # Check if alternative is another if_statement (else if -> elif)
        if alternative.type == "if_statement":
            # Convert "else if" to "elif"
            alt_str = visit_node(alternative, ctx)
            # Replace leading "if" with "elif"
            if alt_str.strip().startswith("if "):
                result += alt_str.replace("if ", "elif ", 1)
            else:
                result += f"{alt_indent}elif {alt_str}"
        else:
            result += f"{alt_indent}else:\n"
            ctx.indent_level += 1
            alt_str = visit_node(alternative, ctx)
            ctx.indent_level -= 1
            result += alt_str if alt_str else f"{ctx.indent()}    pass\n"
    
    return result


def visit_for_in_statement(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate for-in/for-of loop: for (const x of arr) -> for x in arr:"""
    left = node.child_by_field_name("left")
    right = node.child_by_field_name("right")
    body = node.child_by_field_name("body")
    
    if not left or not right or not body:
        return ""
    
    # Get loop variable (handle 'const x' or just 'x')
    if left.type == "lexical_declaration":
        # Extract variable name from declaration
        var_node = left.child_by_field_name("declarator") or left.named_children[0] if left.named_children else None
        if var_node:
            var_name = var_node.child_by_field_name("name")
            loop_var = var_name.text.decode() if var_name else "item"
        else:
            loop_var = "item"
    else:
        loop_var = left.text.decode()
    
    # Get iterable
    iter_str = visit_node(right, ctx)
    
    indent = ctx.indent()
    result = f"{indent}for {loop_var} in {iter_str}:\n"
    
    # Translate body
    ctx.indent_level += 1
    body_str = visit_node(body, ctx)
    ctx.indent_level -= 1
    result += body_str if body_str else f"{ctx.indent()}    pass\n"
    
    return result


def visit_return_statement(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate return statement: return value or just return"""
    value = node.named_children[0] if node.named_children else None
    
    indent = ctx.indent()
    if value:
        value_str = visit_node(value, ctx)
        return f"{indent}return {value_str}\n"
    else:
        return f"{indent}return\n"


def visit_try_statement(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate try-catch-finally: try: ... except Exception as e: ... finally: ..."""
    body = node.child_by_field_name("body")
    handler = node.child_by_field_name("handler")
    finalizer = node.child_by_field_name("finalizer")
    
    if not body:
        return ""
    
    indent = ctx.indent()
    result = f"{indent}try:\n"
    
    # Translate try body
    ctx.indent_level += 1
    body_str = visit_node(body, ctx)
    ctx.indent_level -= 1
    result += body_str if body_str else f"{ctx.indent()}    pass\n"
    
    # Translate catch handler
    if handler:
        # Extract exception variable if present
        param = handler.child_by_field_name("parameter")
        exc_var = param.text.decode() if param else "e"
        
        result += f"{indent}except Exception as {exc_var}:\n"
        
        handler_body = handler.child_by_field_name("body")
        if handler_body:
            ctx.indent_level += 1
            handler_str = visit_node(handler_body, ctx)
            ctx.indent_level -= 1
            result += handler_str if handler_str else f"{ctx.indent()}    pass\n"
    
    # Translate finally block
    if finalizer:
        result += f"{indent}finally:\n"
        ctx.indent_level += 1
        finalizer_str = visit_node(finalizer, ctx)
        ctx.indent_level -= 1
        result += finalizer_str if finalizer_str else f"{ctx.indent()}    pass\n"
    
    return result


def visit_throw_statement(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate throw statement: throw expr -> raise Exception(expr)"""
    expr = node.named_children[0] if node.named_children else None
    
    indent = ctx.indent()
    if expr:
        # Check if it is a new expression (new Error(...))
        if expr.type == "new_expression":
            # Get constructor name and args
            constructor = expr.child_by_field_name("constructor")
            args = expr.child_by_field_name("arguments")
            
            if constructor:
                exc_type = constructor.text.decode()
                # Map common error types
                exc_map = {
                    "Error": "Exception",
                    "TypeError": "TypeError",
                    "ValueError": "ValueError",
                }
                py_exc = exc_map.get(exc_type, "Exception")
                
                if args and args.named_children:
                    args_str = visit_node(args.named_children[0], ctx)
                    return f"{indent}raise {py_exc}({args_str})\n"
                else:
                    return f"{indent}raise {py_exc}()\n"
        
        # Fallback: raise Exception with the expression
        expr_str = visit_node(expr, ctx)
        return f"{indent}raise Exception({expr_str})\n"
    else:
        return f"{indent}raise\n"


def visit_expression_statement(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate expression statement: just visit the inner expression"""
    expr = node.named_children[0] if node.named_children else None
    
    if expr:
        expr_str = visit_node(expr, ctx)
        indent = ctx.indent()
        return f"{indent}{expr_str}\n"
    return ""


def visit_statement_block(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate statement block: visit all children statements with proper indentation"""
    result_lines = []
    
    for child in node.named_children:
        child_str = visit_node(child, ctx)
        if child_str:
            result_lines.append(child_str)
    
    return "".join(result_lines)


def visit_break_statement(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate break statement"""
    indent = ctx.indent()
    return f"{indent}break\n"


def visit_continue_statement(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate continue statement"""
    indent = ctx.indent()
    return f"{indent}continue\n"


def _translate_case_body(case, ctx, visit_node):
    """Translate the body of a single switch case."""
    result = ""
    for stmt in case.named_children[1:]:
        if stmt.type not in ["switch_case", "switch_default"]:
            stmt_str = visit_node(stmt, ctx)
            if stmt_str:
                result += stmt_str
    return result


def visit_switch_statement(node: Node, ctx: TranslationContext, visit_node) -> str:
    """Translate switch statement to if/elif/else chain"""
    value = node.child_by_field_name("value")
    body = node.child_by_field_name("body")
    
    if not value or not body:
        return ""
    
    value_str = visit_node(value, ctx)
    indent = ctx.indent()
    result = ""
    
    # Collect case clauses
    cases = [child for child in body.named_children if child.type == "switch_case"]
    default = [child for child in body.named_children if child.type == "switch_default"]
    
    # Translate each case
    for i, case in enumerate(cases):
        case_value = case.child_by_field_name("value")
        if not case_value:
            continue
        
        case_val_str = visit_node(case_value, ctx)
        kw = "if" if i == 0 else "elif"
        result += f"{indent}{kw} {value_str} == {case_val_str}:\n"
        
        ctx.indent_level += 1
        result += _translate_case_body(case, ctx, visit_node)
        ctx.indent_level -= 1
    
    # Handle default case
    if default:
        result += f"{indent}else:\n"
        ctx.indent_level += 1
        result += _translate_case_body(default[0], ctx, visit_node)
        ctx.indent_level -= 1
    
    return result
