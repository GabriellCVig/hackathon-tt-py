from __future__ import annotations
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Node
    from ..context import TranslationContext

def _snake(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case"""
    s1 = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def visit_call_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles function/method calls.
    Maps Big.js methods to operators, array methods to Python equivalents.
    """
    # Get the function being called and arguments
    func_node = None
    args_node = None
    
    for child in node.children:
        if child.type in ('identifier', 'member_expression'):
            func_node = child
        elif child.type == 'arguments':
            args_node = child
    
    if not func_node:
        return ''
    
    func_text = visit_node(func_node, ctx)
    args_text = ''
    
    if args_node:
        # Extract argument expressions (skip parentheses)
        arg_parts = []
        for child in args_node.children:
            if child.type not in ('(', ')', ','):
                arg_parts.append(visit_node(child, ctx))
        args_text = ', '.join(arg_parts)
    
    # Handle Big.js method calls
    if '.' in func_text:
        obj, method = func_text.rsplit('.', 1)
        
        # Big.js arithmetic methods -> operators
        if method == 'plus':
            return f'({obj} + {args_text})'
        elif method == 'minus':
            return f'({obj} - {args_text})'
        elif method == 'mul':
            return f'({obj} * {args_text})'
        elif method == 'div':
            return f'({obj} / {args_text})'
        elif method == 'toNumber':
            return f'float({obj})'
        elif method == 'toFixed':
            if args_text:
                return f'round({obj}, {args_text})'
            return f'round({obj})'
        elif method == 'toString':
            return f'str({obj})'
        
        # Array methods
        elif method == 'push':
            return f'{obj}.append({args_text})'
        elif method == 'filter':
            # .filter(predicate) -> list comprehension or filter()
            return f'[x for x in {obj} if ({args_text})(x)]'
        elif method == 'map':
            # .map(fn) -> list comprehension
            return f'[({args_text})(x) for x in {obj}]'
        elif method == 'length':
            return f'len({obj})'
    
    # Check if function needs library mapping
    # Assumption: ctx has import_mapper method or attribute
    if hasattr(ctx, 'import_mapper'):
        mapped = ctx.import_mapper.get(func_text)
        if mapped:
            func_text = mapped
    
    return f'{func_text}({args_text})'


def visit_binary_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles binary operations: arithmetic, comparison, logical.
    Maps TS operators to Python equivalents.
    """
    left = None
    operator = None
    right = None
    
    for child in node.children:
        if child.type in ('===', '!==', '&&', '||', '??'):
            operator = child.text.decode()
        elif operator is None:
            left = child
        else:
            right = child
    
    if not (left and operator and right):
        return ''
    
    # Map TypeScript operators to Python
    op_map = {
        '===': '==',
        '!==': '!=',
        '&&': 'and',
        '||': 'or',
        '??': 'or'  # Nullish coalescing -> logical or (approximation)
    }
    
    py_op = op_map.get(operator, operator)
    left_text = visit_node(left, ctx)
    right_text = visit_node(right, ctx)
    
    return f'{left_text} {py_op} {right_text}'


def visit_member_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles property access: obj.property or obj?.property
    """
    obj_node = None
    prop_node = None
    is_optional = False
    
    for child in node.children:
        if child.type == '?.':
            is_optional = True
        elif obj_node is None and child.type not in ('.', '?.'):
            obj_node = child
        elif child.type in ('property_identifier', 'identifier') and obj_node is not None:
            prop_node = child
    
    if not obj_node:
        return ''
    
    obj_text = visit_node(obj_node, ctx)
    
    # Handle 'this' -> 'self'
    if obj_text == 'this':
        obj_text = 'self'
    
    if prop_node:
        prop_text = prop_node.text.decode()
        prop_text = _snake(prop_text)
        
        if is_optional:
            # Optional chaining: obj?.prop -> getattr(obj, 'prop', None)
            return f"getattr({obj_text}, '{prop_text}', None)"
        else:
            return f'{obj_text}.{prop_text}'
    
    return obj_text


def visit_new_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles object construction: new ClassName(args)
    Maps via import_mapper (e.g., Big -> Decimal)
    """
    constructor = None
    args_node = None
    
    for child in node.children:
        if child.type == 'new':
            continue
        elif child.type == 'arguments':
            args_node = child
        elif constructor is None:
            constructor = child
    
    if not constructor:
        return ''
    
    constructor_text = visit_node(constructor, ctx)
    
    # Map constructor via import_mapper
    if hasattr(ctx, 'import_mapper'):
        mapped = ctx.import_mapper.get(constructor_text)
        if mapped:
            constructor_text = mapped
    
    args_text = ''
    if args_node:
        arg_parts = []
        for child in args_node.children:
            if child.type not in ('(', ')', ','):
                arg_parts.append(visit_node(child, ctx))
        args_text = ', '.join(arg_parts)
    
    return f'{constructor_text}({args_text})'


def visit_ternary_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles ternary: condition ? consequent : alternative
    Translates to: consequent if condition else alternative
    """
    condition = None
    consequent = None
    alternative = None
    
    state = 'condition'
    for child in node.children:
        if child.type == '?':
            state = 'consequent'
        elif child.type == ':':
            state = 'alternative'
        elif state == 'condition':
            condition = child
        elif state == 'consequent':
            consequent = child
        elif state == 'alternative':
            alternative = child
    
    if not (condition and consequent and alternative):
        return ''
    
    cond_text = visit_node(condition, ctx)
    cons_text = visit_node(consequent, ctx)
    alt_text = visit_node(alternative, ctx)
    
    return f'{cons_text} if {cond_text} else {alt_text}'


def visit_arrow_function(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles arrow functions: (params) => expr or (params) => { block }
    Translates to lambda for single expressions, or inline def for blocks.
    """
    params = []
    body = None
    
    for child in node.children:
        if child.type in ('formal_parameters', 'identifier'):
            # Extract parameter names
            if child.type == 'identifier':
                params.append(child.text.decode())
            else:
                for param_child in child.children:
                    if param_child.type == 'identifier':
                        params.append(param_child.text.decode())
        elif child.type == '=>':
            continue
        else:
            body = child
    
    if not body:
        return ''
    
    params_text = ', '.join(params)
    
    # Single expression body -> lambda
    if body.type != 'statement_block':
        body_text = visit_node(body, ctx)
        return f'lambda {params_text}: {body_text}'
    
    # Block body -> needs multi-line function (not ideal for inline)
    # For now, return a placeholder comment
    return f'# TODO: multi-line arrow function with params ({params_text})'


def visit_assignment_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles assignment: left = right or left op= right
    """
    left = None
    operator = None
    right = None
    
    for child in node.children:
        if child.type in ('=', '+=', '-=', '*=', '/='):
            operator = child.text.decode()
        elif operator is None:
            left = child
        else:
            right = child
    
    if not (left and operator and right):
        return ''
    
    left_text = visit_node(left, ctx)
    right_text = visit_node(right, ctx)
    
    return f'{left_text} {operator} {right_text}'


def visit_update_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles increment/decrement: x++ or x-- or ++x or --x
    Translates to: x += 1 or x -= 1
    """
    operand = None
    operator = None
    
    for child in node.children:
        if child.type in ('++', '--'):
            operator = child.text.decode()
        else:
            operand = child
    
    if not (operand and operator):
        return ''
    
    operand_text = visit_node(operand, ctx)
    
    if operator == '++':
        return f'{operand_text} += 1'
    else:  # '--'
        return f'{operand_text} -= 1'


def visit_await_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles await: await expression
    """
    expr = None
    for child in node.children:
        if child.type != 'await':
            expr = child
            break
    
    if not expr:
        return ''
    
    expr_text = visit_node(expr, ctx)
    return f'await {expr_text}'


def visit_unary_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles unary operators: !x, -x, typeof x
    """
    operator = None
    operand = None
    
    for child in node.children:
        if child.type in ('!', '-', 'typeof', '+'):
            operator = child.text.decode()
        else:
            operand = child
    
    if not operand:
        return ''
    
    operand_text = visit_node(operand, ctx)
    
    # Map operators
    if operator == '!':
        return f'not {operand_text}'
    elif operator == 'typeof':
        return f'type({operand_text}).__name__'
    elif operator in ('-', '+'):
        return f'{operator}{operand_text}'
    
    return operand_text


def visit_parenthesized_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles parenthesized expressions: (expr)
    """
    inner = None
    for child in node.children:
        if child.type not in ('(', ')'):
            inner = child
            break
    
    if not inner:
        return ''
    
    inner_text = visit_node(inner, ctx)
    return f'({inner_text})'


def visit_subscript_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles subscript/indexing: obj[key]
    """
    obj = None
    index = None
    
    for child in node.children:
        if child.type in ('[', ']'):
            continue
        elif obj is None:
            obj = child
        else:
            index = child
    
    if not (obj and index):
        return ''
    
    obj_text = visit_node(obj, ctx)
    index_text = visit_node(index, ctx)
    
    return f'{obj_text}[{index_text}]'


def visit_as_expression(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles type assertions: expr as Type
    Strips the type cast, just returns the expression.
    """
    expr = None
    for child in node.children:
        if child.type not in ('as', 'type_identifier'):
            expr = child
            break
    
    if not expr:
        return ''
    
    return visit_node(expr, ctx)
