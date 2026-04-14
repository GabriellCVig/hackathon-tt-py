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


def _handle_big_method_call(obj: str, method: str, args_text: str):
    """Handle Big.js method calls."""
    # Arithmetic methods
    if method == "plus" or method == "add":
        return f"({obj} + {args_text})"
    elif method == "minus":
        return f"({obj} - {args_text})"
    elif method == "mul":
        return f"({obj} * {args_text})"
    elif method == "div":
        return f"({obj} / {args_text})"
    elif method == "abs":
        return f"abs({obj})"
    
    # Comparison methods
    elif method == "eq":
        return f"({obj} == {args_text})"
    elif method == "gt":
        return f"({obj} > {args_text})"
    elif method == "gte":
        return f"({obj} >= {args_text})"
    elif method == "lt":
        return f"({obj} < {args_text})"
    elif method == "lte":
        return f"({obj} <= {args_text})"
    
    # Conversion methods
    elif method == "toNumber":
        return f"float({obj})"
    elif method == "toFixed":
        return f"round({obj}, {args_text})" if args_text else f"round({obj})"
    elif method == "toString":
        return f"str({obj})"
    return None


def _handle_array_method_call(obj: str, method: str, args_text: str):
    """Handle array method calls."""
    if method == "push":
        return f"{obj}.append({args_text})"
    elif method == "filter":
        return f"[x for x in {obj} if ({args_text})(x)]"
    elif method == "map":
        return f"[({args_text})(x) for x in {obj}]"
    elif method == "length":
        return f"len({obj})"
    return None


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
        arg_parts = []
        for child in args_node.children:
            if child.type not in ('(', ')', ','):
                arg_parts.append(visit_node(child, ctx))
        args_text = ', '.join(arg_parts)
    
    # Handle method calls
    if '.' in func_text:
        obj, method = func_text.rsplit('.', 1)
        
        big_result = _handle_big_method_call(obj, method, args_text)
        if big_result:
            return big_result
        
        array_result = _handle_array_method_call(obj, method, args_text)
        if array_result:
            return array_result
    
    # Check for library mapping
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
    
    # Check raw constructor BEFORE snake_casing
    raw_constructor = constructor.text.decode('utf-8') if hasattr(constructor, 'text') else ''
    
    # Special case: Big -> Decimal
    if raw_constructor == 'Big':
        constructor_text = 'Decimal'
    else:
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
    destructured_props = []
    body = None
    
    for child in node.children:
        if child.type == 'formal_parameters':
            # Extract parameters, handling destructuring
            for param_child in child.children:
                if param_child.type == 'identifier':
                    params.append(_snake(param_child.text.decode()))
                elif param_child.type == 'object_pattern':
                    # Destructuring: extract property names
                    for prop_child in param_child.named_children:
                        if prop_child.type == 'shorthand_property_identifier_pattern':
                            prop_name = prop_child.text.decode()
                            destructured_props.append(_snake(prop_name))
        elif child.type == 'identifier':
            params.append(_snake(child.text.decode()))
        elif child.type == 'object_pattern':
            # Destructuring parameter without formal_parameters wrapper
            for prop_child in child.named_children:
                if prop_child.type == 'shorthand_property_identifier_pattern':
                    prop_name = prop_child.text.decode()
                    destructured_props.append(_snake(prop_name))
        elif child.type == '=>':
            continue
        else:
            body = child
    
    if not body:
        return ''
    
    # If we have destructuring but no regular params, use 'x' as the lambda param
    if destructured_props and not params:
        params = ['x']
    
    params_text = ', '.join(params) if params else 'x'
    
    # Single expression body -> lambda
    if body.type != 'statement_block':
        body_text = visit_node(body, ctx)
        # If destructured, access properties
        if destructured_props:
            body_text = f'x.{destructured_props[0]}' if len(destructured_props) == 1 else body_text
        return f'lambda {params_text}: {body_text}'
    
    # Block body with single return statement
    # Check if it's a simple return
    if body.type == 'statement_block':
        statements = [c for c in body.named_children]
        if len(statements) == 1 and statements[0].type == 'return_statement':
            # Simple return - extract the return value
            return_value = None
            for ret_child in statements[0].named_children:
                if ret_child.type != 'return':
                    return_value = ret_child
                    break
            if return_value:
                if return_value.type == 'identifier' and destructured_props:
                    # Returning a destructured property
                    prop_name = return_value.text.decode()
                    snake_prop = _snake(prop_name)
                    if snake_prop in destructured_props:
                        # Use the first param (usually 'x') to access the property
                        param = params[0] if params else 'x'
                        return f'lambda {param}: {param}.{snake_prop}'
                ret_text = visit_node(return_value, ctx)
                # If ret_text references a destructured prop, prepend param access
                if destructured_props and ret_text in destructured_props:
                    param = params[0] if params else 'x'
                    return f'lambda {param}: {param}.{ret_text}'
                return f'lambda {params_text}: {ret_text}'
    
    # Complex block body -> placeholder
    return f'lambda {params_text}: True  # TODO: complex arrow function'


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


def visit_object(node: Node, ctx: TranslationContext, visit_node) -> str:
    """
    Handles object literals: { key1: value1, key2: value2 }
    Translates to Python dict: {"key1": value1, "key2": value2}
    """
    pairs = []
    
    for child in node.named_children:
        if child.type == "pair":
            # Extract key and value
            key_node = None
            value_node = None
            
            for pair_child in child.named_children:
                if key_node is None:
                    key_node = pair_child
                else:
                    value_node = pair_child
                    break
            
            if key_node and value_node:
                # Get key text (could be identifier or string)
                if key_node.type in ("property_identifier", "identifier"):
                    key_text = key_node.text.decode("utf-8")
                    key_str = f"\"{_snake(key_text)}\""
                elif key_node.type == "string":
                    key_str = key_node.text.decode("utf-8")
                else:
                    key_str = visit_node(key_node, ctx)
                
                value_str = visit_node(value_node, ctx)
                pairs.append(f"{key_str}: {value_str}")
        
        elif child.type == "shorthand_property_identifier":
            # Shorthand: {foo} -> {"foo": foo}
            prop_name = child.text.decode("utf-8")
            snake_name = _snake(prop_name)
            pairs.append(f"\"{snake_name}\": {snake_name}")
    
    if pairs:
        return "{" + ", ".join(pairs) + "}"
    return "{}"


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
