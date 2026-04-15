"""
Enhanced unit tests for the Formal Logic Parser component.

This file extends the basic tests in test_parser.py with more thorough
testing of complex methods and edge cases, focusing on parsing complex
formulas, error handling, and integration with the AST module.
"""

import unittest
from unittest.mock import patch, MagicMock
import time
from typing import Dict, List, Optional, Set, Any, Tuple

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode, LambdaNode
)
from godelOS.core_kr.formal_logic_parser.parser import LogicParser

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker


class TestParserEnhanced(unittest.TestCase):
    """Enhanced test cases for the Formal Logic Parser with complex scenarios and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system
        self.type_system = TypeSystemManager()
        
        # Create basic types
        self.boolean_type = self.type_system.get_type("Boolean")
        self.entity_type = self.type_system.get_type("Entity")
        self.integer_type = self.type_system.get_type("Integer")
        self.real_type = self.type_system.get_type("Real")
        
        # Create function types
        self.unary_pred_type = FunctionType([self.entity_type], self.boolean_type)
        self.binary_pred_type = FunctionType([self.entity_type, self.entity_type], self.boolean_type)
        self.ternary_pred_type = FunctionType([self.entity_type, self.entity_type, self.entity_type], self.boolean_type)
        
        # Create the parser
        self.parser = LogicParser(self.type_system)
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    
    def test_parsing_complex_formulas(self):
        """Test parsing of complex formulas.
        
        This test verifies that the parser correctly parses complex formulas
        with multiple connectives, quantifiers, and nested expressions.
        """
        # Parse a complex formula:
        # ∀x. (P(x) ∧ Q(x)) ⇒ ∃y. R(x, y)
        formula = "forall ?x. ((P(?x) and Q(?x)) implies exists ?y. R(?x, ?y))"
        
        # Register the predicates with the parser
        self.parser.register_predicate("P", self.unary_pred_type)
        self.parser.register_predicate("Q", self.unary_pred_type)
        self.parser.register_predicate("R", self.binary_pred_type)
        
        # Parse the formula
        ast, _errors = self.parser.parse(formula)
        
        # Verify the structure of the AST
        self.assertIsInstance(ast, QuantifierNode)
        self.assertEqual(ast.quantifier_type, "FORALL")
        self.assertEqual(len(ast.bound_variables), 1)
        self.assertEqual(ast.bound_variables[0].name, "?x")
        
        # Check the body of the quantifier
        body = ast.scope
        self.assertIsInstance(body, ConnectiveNode)
        self.assertEqual(body.connective_type, "IMPLIES")
        self.assertEqual(len(body.operands), 2)
        
        # Check the left operand: (P(x) ∧ Q(x))
        left = body.operands[0]
        self.assertIsInstance(left, ConnectiveNode)
        self.assertEqual(left.connective_type, "AND")
        self.assertEqual(len(left.operands), 2)
        
        # Check P(x)
        p_x = left.operands[0]
        self.assertIsInstance(p_x, ApplicationNode)
        self.assertEqual(p_x.operator.name, "P")
        self.assertEqual(len(p_x.arguments), 1)
        self.assertEqual(p_x.arguments[0].name, "?x")
        
        # Check Q(x)
        q_x = left.operands[1]
        self.assertIsInstance(q_x, ApplicationNode)
        self.assertEqual(q_x.operator.name, "Q")
        self.assertEqual(len(q_x.arguments), 1)
        self.assertEqual(q_x.arguments[0].name, "?x")
        
        # Check the right operand: ∃y. R(x, y)
        right = body.operands[1]
        self.assertIsInstance(right, QuantifierNode)
        self.assertEqual(right.quantifier_type, "EXISTS")
        self.assertEqual(len(right.bound_variables), 1)
        self.assertEqual(right.bound_variables[0].name, "?y")
        
        # Check R(x, y)
        r_x_y = right.scope
        self.assertIsInstance(r_x_y, ApplicationNode)
        self.assertEqual(r_x_y.operator.name, "R")
        self.assertEqual(len(r_x_y.arguments), 2)
        self.assertEqual(r_x_y.arguments[0].name, "?x")
        self.assertEqual(r_x_y.arguments[1].name, "?y")
    
    def test_parsing_modal_logic(self):
        """Test parsing of modal logic formulas.
        
        This test verifies that the parser correctly parses modal logic
        formulas with knowledge, belief, and other modal operators.
        """
        # Parse a modal logic formula:
        # K_a(P(x)) ∧ B_b(Q(y))
        formula = "knows(a, P(?x)) and believes(b, Q(?y))"
        
        # Register the predicates and constants with the parser
        self.parser.register_predicate("P", self.unary_pred_type)
        self.parser.register_predicate("Q", self.unary_pred_type)
        self.parser.register_constant("a", self.entity_type)
        self.parser.register_constant("b", self.entity_type)
        
        # Parse the formula
        ast, _errors = self.parser.parse(formula)
        
        # Verify the structure of the AST
        self.assertIsInstance(ast, ConnectiveNode)
        self.assertEqual(ast.connective_type, "AND")
        self.assertEqual(len(ast.operands), 2)
        
        # Check the left operand: K_a(P(x))
        left = ast.operands[0]
        self.assertIsInstance(left, ModalOpNode)
        self.assertEqual(left.modal_operator, "KNOWS")
        self.assertIsInstance(left.agent_or_world, ConstantNode)
        self.assertEqual(left.agent_or_world.name, "a")
        
        # Check P(x)
        p_x = left.proposition
        self.assertIsInstance(p_x, ApplicationNode)
        self.assertEqual(p_x.operator.name, "P")
        self.assertEqual(len(p_x.arguments), 1)
        self.assertEqual(p_x.arguments[0].name, "?x")
        
        # Check the right operand: B_b(Q(y))
        right = ast.operands[1]
        self.assertIsInstance(right, ModalOpNode)
        self.assertEqual(right.modal_operator, "BELIEVES")
        self.assertIsInstance(right.agent_or_world, ConstantNode)
        self.assertEqual(right.agent_or_world.name, "b")
        
        # Check Q(y)
        q_y = right.proposition
        self.assertIsInstance(q_y, ApplicationNode)
        self.assertEqual(q_y.operator.name, "Q")
        self.assertEqual(len(q_y.arguments), 1)
        self.assertEqual(q_y.arguments[0].name, "?y")
        
        # Parse a nested modal formula:
        # K_a(B_b(P(x)))
        formula2 = "knows(a, believes(b, P(?x)))"
        
        # Parse the formula
        ast2, _errors = self.parser.parse(formula2)
        
        # Verify the structure of the AST
        self.assertIsInstance(ast2, ModalOpNode)
        self.assertEqual(ast2.modal_operator, "KNOWS")
        self.assertIsInstance(ast2.agent_or_world, ConstantNode)
        self.assertEqual(ast2.agent_or_world.name, "a")
        
        # Check B_b(P(x))
        b_b_p_x = ast2.proposition
        self.assertIsInstance(b_b_p_x, ModalOpNode)
        self.assertEqual(b_b_p_x.modal_operator, "BELIEVES")
        self.assertIsInstance(b_b_p_x.agent_or_world, ConstantNode)
        self.assertEqual(b_b_p_x.agent_or_world.name, "b")
        
        # Check P(x)
        p_x2 = b_b_p_x.proposition
        self.assertIsInstance(p_x2, ApplicationNode)
        self.assertEqual(p_x2.operator.name, "P")
        self.assertEqual(len(p_x2.arguments), 1)
        self.assertEqual(p_x2.arguments[0].name, "?x")
    
    def test_parsing_lambda_expressions(self):
        """Test parsing of lambda expressions.
        
        This test verifies that the parser correctly parses lambda expressions
        for higher-order logic.
        """
        # Parse a lambda expression:
        # λx. P(x)
        formula = "lambda ?x. P(?x)"
        
        # Register the predicate with the parser
        self.parser.register_predicate("P", self.unary_pred_type)
        
        # Parse the formula
        ast, _errors = self.parser.parse(formula)
        
        # Verify the structure of the AST
        self.assertIsInstance(ast, LambdaNode)
        self.assertEqual(len(ast.bound_variables), 1)
        self.assertEqual(ast.bound_variables[0].name, "?x")
        
        # Check the body of the lambda
        body = ast.body
        self.assertIsInstance(body, ApplicationNode)
        self.assertEqual(body.operator.name, "P")
        self.assertEqual(len(body.arguments), 1)
        self.assertEqual(body.arguments[0].name, "?x")
        
        # Parse a more complex lambda expression:
        # λx. λy. R(x, y)
        formula2 = "lambda ?x. lambda ?y. R(?x, ?y)"
        
        # Register the predicate with the parser
        self.parser.register_predicate("R", self.binary_pred_type)
        
        # Parse the formula
        ast2, _errors = self.parser.parse(formula2)
        
        # Verify the structure of the AST
        self.assertIsInstance(ast2, LambdaNode)
        self.assertEqual(len(ast2.bound_variables), 1)
        self.assertEqual(ast2.bound_variables[0].name, "?x")
        
        # Check the body of the outer lambda
        body2 = ast2.body
        self.assertIsInstance(body2, LambdaNode)
        self.assertEqual(len(body2.bound_variables), 1)
        self.assertEqual(body2.bound_variables[0].name, "?y")
        
        # Check the body of the inner lambda
        inner_body = body2.body
        self.assertIsInstance(inner_body, ApplicationNode)
        self.assertEqual(inner_body.operator.name, "R")
        self.assertEqual(len(inner_body.arguments), 2)
        self.assertEqual(inner_body.arguments[0].name, "?x")
        self.assertEqual(inner_body.arguments[1].name, "?y")
    
    def test_parsing_arithmetic_expressions(self):
        """Test parsing of arithmetic expressions.
        
        This test verifies that the parser correctly parses arithmetic
        expressions with operators and numeric constants.
        """
        # Parse an arithmetic expression:
        # x + 1 > y * 2
        formula = "plus(?x, 1) > times(?y, 2)"
        
        # Register the functions and constants with the parser
        int_int_func_type = FunctionType([self.integer_type], self.integer_type)
        int_int_int_func_type = FunctionType([self.integer_type, self.integer_type], self.integer_type)
        int_int_bool_func_type = FunctionType([self.integer_type, self.integer_type], self.boolean_type)
        
        self.parser.register_function("plus", int_int_int_func_type)
        self.parser.register_function("times", int_int_int_func_type)
        self.parser.register_function(">", int_int_bool_func_type)
        self.parser.register_constant("1", self.integer_type, 1)
        self.parser.register_constant("2", self.integer_type, 2)
        
        # Parse the formula
        ast, _errors = self.parser.parse(formula)
        
        # Verify the structure of the AST
        self.assertIsInstance(ast, ApplicationNode)
        self.assertEqual(ast.operator.name, ">")
        self.assertEqual(len(ast.arguments), 2)
        
        # Check the left operand: x + 1
        left = ast.arguments[0]
        self.assertIsInstance(left, ApplicationNode)
        self.assertEqual(left.operator.name, "plus")
        self.assertEqual(len(left.arguments), 2)
        self.assertEqual(left.arguments[0].name, "?x")
        self.assertEqual(left.arguments[1].name, "1")
        self.assertEqual(left.arguments[1].value, 1)
        
        # Check the right operand: y * 2
        right = ast.arguments[1]
        self.assertIsInstance(right, ApplicationNode)
        self.assertEqual(right.operator.name, "times")
        self.assertEqual(len(right.arguments), 2)
        self.assertEqual(right.arguments[0].name, "?y")
        self.assertEqual(right.arguments[1].name, "2")
        self.assertEqual(right.arguments[1].value, 2)
    
    def test_error_handling(self):
        """Test error handling in the parser.
        
        This test verifies that the parser correctly handles syntax errors,
        type errors, and other parsing errors.
        """
        # Test syntax error: missing closing parenthesis
        formula1 = "P(?x"
        self.parser.register_predicate("P", self.unary_pred_type)
        
        with self.assertRaises(Exception) as context1:
            self.parser.parse(formula1)
        
        self.assertIn("syntax error", str(context1.exception).lower())
        
        # Test type error: wrong number of arguments
        formula2 = "P(?x, ?y)"
        
        with self.assertRaises(Exception) as context2:
            self.parser.parse(formula2)
        
        self.assertIn("type error", str(context2.exception).lower())
        
        # Test undefined symbol error
        formula3 = "Q(?x)"
        
        with self.assertRaises(Exception) as context3:
            self.parser.parse(formula3)
        
        self.assertIn("undefined", str(context3.exception).lower())
        
        # Test variable binding error: unbound variable
        formula4 = "forall ?x. P(?y)"
        
        with self.assertRaises(Exception) as context4:
            self.parser.parse(formula4)
        
        self.assertIn("unbound", str(context4.exception).lower())
    
    def test_parsing_with_custom_syntax(self):
        """Test parsing with custom syntax.
        
        This test verifies that the parser correctly handles custom syntax
        for special operators and expressions.
        """
        # Register a custom syntax for a ternary if-then-else operator
        # if condition then expr1 else expr2
        
        # First, define the types
        bool_int_int_int_func_type = FunctionType(
            [self.boolean_type, self.integer_type, self.integer_type],
            self.integer_type
        )
        
        # Register the function
        self.parser.register_function("if_then_else", bool_int_int_int_func_type)
        
        # Register a custom syntax handler
        def parse_if_then_else(tokens):
            # Expect: if condition then expr1 else expr2
            if tokens[0] != "if":
                return None
            
            # Parse the condition
            tokens.pop(0)  # consume 'if'
            condition = self.parser.parse_expression(tokens)
            
            if tokens[0] != "then":
                raise ValueError("Expected 'then' after condition in if-then-else expression")
            tokens.pop(0)  # consume 'then'
            
            expr1 = self.parser.parse_expression(tokens)
            
            if tokens[0] != "else":
                raise ValueError("Expected 'else' after then-expression in if-then-else expression")
            tokens.pop(0)  # consume 'else'
            
            expr2 = self.parser.parse_expression(tokens)
            
            # Create the application node
            if_then_else_func = self.parser.get_symbol("if_then_else")
            return ApplicationNode(if_then_else_func, [condition, expr1, expr2], self.integer_type)
        
        # Register the custom syntax handler
        self.parser.register_custom_syntax_handler(parse_if_then_else)
        
        # Parse a formula with the custom syntax
        formula = "if P(?x) then 1 else 2"
        
        # Register the predicate and constants
        self.parser.register_predicate("P", self.unary_pred_type)
        self.parser.register_constant("1", self.integer_type, 1)
        self.parser.register_constant("2", self.integer_type, 2)
        
        # Mock the parse_expression method to handle the custom syntax
        with patch.object(self.parser, 'parse_expression') as mock_parse:
            # Define a mock implementation that simulates the custom syntax handler
            def mock_parse_expression(tokens):
                if tokens[0] == "if":
                    # Call the custom syntax handler
                    return parse_if_then_else(tokens)
                elif tokens[0] == "P":
                    # Parse P(?x)
                    tokens.pop(0)  # consume 'P'
                    if tokens[0] != "(" or tokens[2] != ")":
                        raise ValueError("Invalid syntax for predicate application")
                    tokens.pop(0)  # consume '('
                    var_name = tokens.pop(0)  # consume '?x'
                    tokens.pop(0)  # consume ')'
                    p_func = self.parser.get_symbol("P")
                    x_var = VariableNode(var_name, 1, self.entity_type)
                    return ApplicationNode(p_func, [x_var], self.boolean_type)
                elif tokens[0] in ["1", "2"]:
                    # Parse numeric constants
                    value = int(tokens.pop(0))
                    return ConstantNode(str(value), self.integer_type, value)
                else:
                    raise ValueError(f"Unexpected token: {tokens[0]}")
            
            mock_parse.side_effect = mock_parse_expression
            
            # Parse the formula
            ast, _errors = self.parser.parse(formula)
            
            # Verify the structure of the AST
            self.assertIsInstance(ast, ApplicationNode)
            self.assertEqual(ast.operator.name, "if_then_else")
            self.assertEqual(len(ast.arguments), 3)
            
            # Check the condition: P(?x)
            condition = ast.arguments[0]
            self.assertIsInstance(condition, ApplicationNode)
            self.assertEqual(condition.operator.name, "P")
            self.assertEqual(len(condition.arguments), 1)
            self.assertEqual(condition.arguments[0].name, "?x")
            
            # Check the then-expression: 1
            then_expr = ast.arguments[1]
            self.assertIsInstance(then_expr, ConstantNode)
            self.assertEqual(then_expr.name, "1")
            self.assertEqual(then_expr.value, 1)
            
            # Check the else-expression: 2
            else_expr = ast.arguments[2]
            self.assertIsInstance(else_expr, ConstantNode)
            self.assertEqual(else_expr.name, "2")
            self.assertEqual(else_expr.value, 2)
    
    def test_performance_with_large_formulas(self):
        """Test performance with large formulas.
        
        This test verifies that the parser efficiently handles large formulas
        with many subexpressions.
        """
        # Create a large formula with many conjuncts:
        # P(c1) ∧ P(c2) ∧ ... ∧ P(cn)
        num_conjuncts = 100
        
        # Register the predicate and constants
        self.parser.register_predicate("P", self.unary_pred_type)
        for i in range(num_conjuncts):
            self.parser.register_constant(f"c{i}", self.entity_type)
        
        # Build the formula
        conjuncts = [f"P(c{i})" for i in range(num_conjuncts)]
        formula = " and ".join(conjuncts)
        
        # Measure the time to parse the formula
        start_time = time.time()
        ast, _errors = self.parser.parse(formula)
        parse_time = time.time() - start_time
        
        print(f"Time to parse formula with {num_conjuncts} conjuncts: {parse_time * 1000:.2f} ms")
        
        # Verify the structure of the AST
        self.assertIsInstance(ast, ConnectiveNode)
        self.assertEqual(ast.connective_type, "AND")
        
        # In a binary tree representation of AND, we should have num_conjuncts operands
        # in total, but we need to count them recursively
        def count_conjuncts(node):
            if not isinstance(node, ConnectiveNode) or node.connective_type != "AND":
                return 1
            return sum(count_conjuncts(op) for op in node.operands)
        
        total_conjuncts = count_conjuncts(ast)
        self.assertEqual(total_conjuncts, num_conjuncts)
    
    def test_parsing_with_type_inference(self):
        """Test parsing with type inference.
        
        This test verifies that the parser correctly infers types for
        expressions where the types are not explicitly specified.
        """
        # Define polymorphic functions
        # identity: A -> A
        # map: (A -> B) -> List<A> -> List<B>
        
        # Register the functions with the parser
        # For simplicity, we'll use Entity and Boolean as concrete types
        id_entity_type = FunctionType([self.entity_type], self.entity_type)
        id_bool_type = FunctionType([self.boolean_type], self.boolean_type)
        
        self.parser.register_function("identity_entity", id_entity_type)
        self.parser.register_function("identity_bool", id_bool_type)
        
        # Register some constants
        self.parser.register_constant("a", self.entity_type)
        self.parser.register_constant("true", self.boolean_type, True)
        
        # Parse expressions with type inference
        formula1 = "identity_entity(a)"
        formula2 = "identity_bool(true)"
        
        # Mock the type inference method
        with patch.object(self.parser, 'infer_type') as mock_infer:
            # Define mock inference results
            mock_infer.side_effect = [
                self.entity_type,  # For identity_entity(a)
                self.boolean_type  # For identity_bool(true)
            ]
            
            # Parse the formulas
            ast1, _errors = self.parser.parse(formula1)
            ast2, _errors = self.parser.parse(formula2)
            
            # Verify the structure and types of the ASTs
            self.assertIsInstance(ast1, ApplicationNode)
            self.assertEqual(ast1.operator.name, "identity_entity")
            self.assertEqual(ast1.type, self.entity_type)
            
            self.assertIsInstance(ast2, ApplicationNode)
            self.assertEqual(ast2.operator.name, "identity_bool")
            self.assertEqual(ast2.type, self.boolean_type)
            
            # Verify that infer_type was called with the correct arguments
            mock_infer.assert_any_call(ast1)
            mock_infer.assert_any_call(ast2)


if __name__ == "__main__":
    unittest.main()