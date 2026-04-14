"""Visitor module - exports all visitor functions and VISITOR_MAP"""
from .declarations import (
    visit_class_declaration,
    visit_method_definition,
    visit_constructor,
    visit_variable_declaration,
    visit_field_definition,
    to_snake_case,
)

from .expressions import (
    visit_call_expression,
    visit_binary_expression,
    visit_member_expression,
    visit_new_expression,
    visit_ternary_expression,
    visit_arrow_function,
    visit_assignment_expression,
    visit_update_expression,
    visit_await_expression,
    visit_unary_expression,
)

from .statements import (
    visit_if_statement,
    visit_for_in_statement,
    visit_return_statement,
    visit_try_statement,
    visit_throw_statement,
    visit_expression_statement,
    visit_break_statement,
    visit_continue_statement,
    visit_statement_block,
)

from .patterns import (
    visit_object_pattern,
    visit_array_pattern,
    visit_template_string,
    visit_spread_element,
    visit_optional_chain,
    visit_rest_pattern,
    visit_pair_pattern,
)


# Visitor function map: node type -> visitor function
# This maps tree-sitter node types to their corresponding visitor functions
VISITOR_MAP = {
    # Declarations
    "class_declaration": visit_class_declaration,
    "abstract_class_declaration": visit_class_declaration,
    "method_definition": visit_method_definition,
    "public_field_definition": visit_field_definition,
    "lexical_declaration": visit_variable_declaration,
    "variable_declaration": visit_variable_declaration,
    
    # Expressions
    "call_expression": visit_call_expression,
    "binary_expression": visit_binary_expression,
    "member_expression": visit_member_expression,
    "new_expression": visit_new_expression,
    "ternary_expression": visit_ternary_expression,
    "arrow_function": visit_arrow_function,
    "assignment_expression": visit_assignment_expression,
    "update_expression": visit_update_expression,
    "await_expression": visit_await_expression,
    "unary_expression": visit_unary_expression,
    
    # Statements
    "if_statement": visit_if_statement,
    "for_in_statement": visit_for_in_statement,
    "return_statement": visit_return_statement,
    "try_statement": visit_try_statement,
    "throw_statement": visit_throw_statement,
    "expression_statement": visit_expression_statement,
    "break_statement": visit_break_statement,
    "continue_statement": visit_continue_statement,
    "statement_block": visit_statement_block,
    
    # Patterns
    "object_pattern": visit_object_pattern,
    "array_pattern": visit_array_pattern,
    "template_string": visit_template_string,
    "spread_element": visit_spread_element,
    "optional_chain": visit_optional_chain,
    "rest_pattern": visit_rest_pattern,
    "pair_pattern": visit_pair_pattern,
}


__all__ = [
    # Declarations
    "visit_class_declaration",
    "visit_method_definition",
    "visit_constructor",
    "visit_variable_declaration",
    "visit_field_definition",
    "to_snake_case",
    
    # Expressions
    "visit_call_expression",
    "visit_binary_expression",
    "visit_member_expression",
    "visit_new_expression",
    "visit_ternary_expression",
    "visit_arrow_function",
    "visit_assignment_expression",
    "visit_update_expression",
    "visit_await_expression",
    "visit_unary_expression",
    
    # Statements
    "visit_if_statement",
    "visit_for_in_statement",
    "visit_return_statement",
    "visit_try_statement",
    "visit_throw_statement",
    "visit_expression_statement",
    "visit_break_statement",
    "visit_continue_statement",
    "visit_statement_block",
    
    # Patterns
    "visit_object_pattern",
    "visit_array_pattern",
    "visit_template_string",
    "visit_spread_element",
    "visit_optional_chain",
    "visit_rest_pattern",
    "visit_pair_pattern",
    
    # Visitor map
    "VISITOR_MAP",
]
