"""Visitor functions for TypeScript statements (if/for/return/try/throw)"""
from tree_sitter import Node
from ..context import TranslationContext
from ..parser import get_field, get_text, get_children_by_type


def visit_if_statement(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate if/elif/else"""
    cond_node = get_field(node, "condition")
    cons_node = get_field(node, "consequence")
    alt_node = get_field(node, "alternative")
    
    if not (cond_node and cons_node):
        return ""
    
    cond = visitor_func(cond_node, ctx)
    indent = ctx.get_indent_str()
    result = f"{indent}if {cond}:\n"
    
    ctx.indent()
    cons = visitor_func(cons_node, ctx)
    result += cons if cons else f"{ctx.get_indent_str()}pass\n"
    ctx.dedent()
    
    # Handle else/elif
    if alt_node:
        if alt_node.type == "if_statement":
            # elif
            ctx.indent_level -= 1  # Temporarily dedent for elif
            elif_str = visit_if_statement(alt_node, ctx, visitor_func)
            result += elif_str.replace("if ", "elif ", 1)
            ctx.indent_level += 1
        elif alt_node.type == "else_clause":
            body_node = get_field(alt_node, "body")
            result += f"{indent}else:\n"
            ctx.indent()
            body = visitor_func(body_node, ctx) if body_node else ""
            result += body if body else f"{ctx.get_indent_str()}pass\n"
            ctx.dedent()
    
    return result


def visit_for_in_statement(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate for...in/for...of to Python for loop"""
    left_node = get_field(node, "left")
    right_node = get_field(node, "right")
    body_node = get_field(node, "body")
    
    if not (left_node and right_node):
        return ""
    
    # Get loop variable
    var_name = ""
    if left_node.type == "lexical_declaration":
        declarators = get_children_by_type(left_node, "variable_declarator")
        if declarators:
            name_node = get_field(declarators[0], "name")
            if name_node:
                var_name = get_text(name_node)
    else:
        var_name = get_text(left_node)
    
    iterable = visitor_func(right_node, ctx)
    indent = ctx.get_indent_str()
    result = f"{indent}for {var_name} in {iterable}:\n"
    
    ctx.indent()
    if body_node:
        body = visitor_func(body_node, ctx)
        result += body if body else f"{ctx.get_indent_str()}pass\n"
    else:
        result += f"{ctx.get_indent_str()}pass\n"
    ctx.dedent()
    
    return result


def visit_return_statement(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate return statement"""
    arg_node = get_field(node, "argument")
    indent = ctx.get_indent_str()
    
    if arg_node:
        value = visitor_func(arg_node, ctx)
        return f"{indent}return {value}\n"
    return f"{indent}return\n"


def visit_try_statement(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate try/except"""
    body_node = get_field(node, "body")
    handler_node = get_field(node, "handler")
    
    if not body_node:
        return ""
    
    indent = ctx.get_indent_str()
    result = f"{indent}try:\n"
    
    ctx.indent()
    body = visitor_func(body_node, ctx)
    result += body if body else f"{ctx.get_indent_str()}pass\n"
    ctx.dedent()
    
    # Handle catch clause
    if handler_node:
        param_node = get_field(handler_node, "parameter")
        catch_body = get_field(handler_node, "body")
        
        exc_name = "e"
        if param_node:
            exc_name = get_text(param_node)
        
        result += f"{indent}except Exception as {exc_name}:\n"
        ctx.indent()
        if catch_body:
            catch_str = visitor_func(catch_body, ctx)
            result += catch_str if catch_str else f"{ctx.get_indent_str()}pass\n"
        else:
            result += f"{ctx.get_indent_str()}pass\n"
        ctx.dedent()
    
    return result


def visit_throw_statement(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate throw to raise"""
    arg_node = get_field(node, "argument")
    indent = ctx.get_indent_str()
    
    if arg_node:
        value = visitor_func(arg_node, ctx)
        return f"{indent}raise {value}\n"
    return f"{indent}raise Exception()\n"


def visit_expression_statement(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate expression statement"""
    expr_node = get_field(node, "expression")
    if not expr_node:
        return ""
    
    indent = ctx.get_indent_str()
    expr = visitor_func(expr_node, ctx)
    return f"{indent}{expr}\n"


def visit_break_statement(node: Node, ctx: TranslationContext) -> str:
    """Translate break"""
    indent = ctx.get_indent_str()
    return f"{indent}break\n"


def visit_continue_statement(node: Node, ctx: TranslationContext) -> str:
    """Translate continue"""
    indent = ctx.get_indent_str()
    return f"{indent}continue\n"


def visit_statement_block(node: Node, ctx: TranslationContext, visitor_func) -> str:
    """Translate statement block (sequence of statements)"""
    statements = []
    for child in node.named_children:
        stmt = visitor_func(child, ctx)
        if stmt:
            statements.append(stmt)
    return "".join(statements)
