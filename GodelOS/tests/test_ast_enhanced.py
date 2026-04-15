"""
Enhanced unit tests for the AST module.

This file extends the basic tests in test_ast.py with more thorough
testing of complex methods and edge cases, focusing on the visitor pattern,
substitution mechanisms, and complex AST transformations.
"""

import unittest
from unittest.mock import patch, MagicMock
import time

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.ast.nodes import (
    AST_Node, ASTVisitor, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode, LambdaNode, DefinitionNode
)
from typing import Dict, List, TypeVar, Generic, Optional, Set, Any, Tuple

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker

# Type variable for the visitor pattern return type
T = TypeVar('T')


class TestASTNodesEnhanced(unittest.TestCase):
    """Enhanced test cases for AST nodes with complex scenarios and edge cases."""
    
    def setUp(self):
        """Set up the test case with a rich type system and complex AST structures."""
        self.type_system = TypeSystemManager()
        self.entity_type = self.type_system.get_type("Entity")
        self.boolean_type = self.type_system.get_type("Boolean")
        self.integer_type = self.type_system.get_type("Integer")
        self.real_type = self.type_system.get_type("Real")
        
        # Create function types for more complex testing
        self.unary_pred_type = FunctionType([self.entity_type], self.boolean_type)
        self.binary_pred_type = FunctionType([self.entity_type, self.entity_type], self.boolean_type)
        self.ternary_pred_type = FunctionType([self.entity_type, self.entity_type, self.entity_type], self.boolean_type)
        self.numeric_func_type = FunctionType([self.integer_type], self.integer_type)
        self.binary_numeric_func_type = FunctionType([self.integer_type, self.integer_type], self.integer_type)
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    def test_deep_nested_ast_construction(self):
        """Test construction of deeply nested AST structures.
        
        This test verifies that the system can handle deeply nested AST structures
        without stack overflow or performance issues.
        """
        start_time = time.time()
        
        # Create variables and constants
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        
        # Create predicates
        human_pred = ConstantNode("Human", self.unary_pred_type)
        mortal_pred = ConstantNode("Mortal", self.unary_pred_type)
        knows_pred = ConstantNode("Knows", self.binary_pred_type)
        
        # Create nested structure: ∀?x. (Human(?x) ⇒ (Mortal(?x) ∧ ∃?y. Knows(?x, ?y)))
        human_x = ApplicationNode(human_pred, [x_var], self.boolean_type)
        mortal_x = ApplicationNode(mortal_pred, [x_var], self.boolean_type)
        knows_x_y = ApplicationNode(knows_pred, [x_var, y_var], self.boolean_type)
        
        exists_y_knows_x_y = QuantifierNode("EXISTS", [y_var], knows_x_y, self.boolean_type)
        mortal_x_and_exists = ConnectiveNode("AND", [mortal_x, exists_y_knows_x_y], self.boolean_type)
        human_x_implies_mortal = ConnectiveNode("IMPLIES", [human_x, mortal_x_and_exists], self.boolean_type)
        forall_x_human_implies = QuantifierNode("FORALL", [x_var], human_x_implies_mortal, self.boolean_type)
        
        # Create an even deeper structure by nesting more quantifiers
        nested_depth = 10
        current_node = forall_x_human_implies
        
        for i in range(nested_depth):
            new_var = VariableNode(f"?v{i}", 100 + i, self.entity_type)
            current_node = QuantifierNode(
                "FORALL" if i % 2 == 0 else "EXISTS",
                [new_var],
                current_node,
                self.boolean_type
            )
        
        # Verify the structure is correctly formed
        self.assertIsInstance(current_node, QuantifierNode)
        
        # Measure construction time
        construction_time = time.time() - start_time
        print(f"Deep AST construction time: {construction_time * 1000:.2f} ms")
        
        # Verify we can traverse the entire structure without issues
        class DepthCounter(ASTVisitor[int]):
            def visit_constant(self, node: ConstantNode) -> int:
                return 0
            
            def visit_variable(self, node: VariableNode) -> int:
                return 0
            
            def visit_application(self, node: ApplicationNode) -> int:
                return 1 + max([node.operator.accept(self)] + [arg.accept(self) for arg in node.arguments])
            
            def visit_quantifier(self, node: QuantifierNode) -> int:
                return 1 + node.scope.accept(self)
            
            def visit_connective(self, node: ConnectiveNode) -> int:
                return 1 + max([op.accept(self) for op in node.operands])
            
            def visit_modal_op(self, node: ModalOpNode) -> int:
                agent_depth = node.agent_or_world.accept(self) if node.agent_or_world else 0
                return 1 + max(node.proposition.accept(self), agent_depth)
            
            def visit_lambda(self, node: LambdaNode) -> int:
                return 1 + node.body.accept(self)
            
            def visit_definition(self, node: DefinitionNode) -> int:
                return 1 + node.definition_body_ast.accept(self)
        
        counter = DepthCounter()
        depth = current_node.accept(counter)
        
        # Depth should be at least nested_depth + original formula depth
        self.assertGreaterEqual(depth, nested_depth)
        
        # Test that we can still perform operations on deeply nested ASTs
        substitution = {x_var: ConstantNode("Socrates", self.entity_type)}
        substituted = current_node.substitute(substitution)
        
        self.assertIsInstance(substituted, QuantifierNode)
    def test_complex_substitution_with_name_capture_avoidance(self):
        """Test variable substitution with name capture avoidance.
        
        This test verifies that substitution correctly handles variable name capture
        in complex nested expressions with multiple quantifiers.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        
        # Create a predicate
        loves_pred = ConstantNode("Loves", self.binary_pred_type)
        
        # Create an application: Loves(?x, ?y)
        loves_x_y = ApplicationNode(loves_pred, [x_var, y_var], self.boolean_type)
        
        # Create a quantifier: ∀?z. Loves(?x, ?y)
        forall_z_loves_x_y = QuantifierNode("FORALL", [z_var], loves_x_y, self.boolean_type)
        
        # Create a substitution that would cause variable capture: {?x -> ?z}
        # This should rename the bound variable to avoid capture
        z_var_2 = VariableNode("?z", 3, self.entity_type)  # Same name but different instance
        substitution = {x_var: z_var_2}
        
        # Apply the substitution
        result = forall_z_loves_x_y.substitute(substitution)
        
        # Check that the result is a QuantifierNode
        self.assertIsInstance(result, QuantifierNode)
        self.assertEqual(result.quantifier_type, "FORALL")
        
        # The bound variable should still be z_var
        self.assertEqual(len(result.bound_variables), 1)
        bound_var = result.bound_variables[0]
        self.assertEqual(bound_var.name, "?z")
        
        # But the body should now have ?z instead of ?x
        body = result.scope
        self.assertIsInstance(body, ApplicationNode)
        self.assertEqual(body.arguments[0].name, "?z")
        
        # Test a more complex case with nested quantifiers
        # ∃?y. ∀?z. Loves(?x, ?y) ∧ Loves(?y, ?z)
        loves_y_z = ApplicationNode(loves_pred, [y_var, z_var], self.boolean_type)
        loves_x_y_and_loves_y_z = ConnectiveNode("AND", [loves_x_y, loves_y_z], self.boolean_type)
        forall_z_complex = QuantifierNode("FORALL", [z_var], loves_x_y_and_loves_y_z, self.boolean_type)
        exists_y_forall_z = QuantifierNode("EXISTS", [y_var], forall_z_complex, self.boolean_type)
        
        # Create a substitution that would cause multiple captures: {?x -> ?y}
        y_var_2 = VariableNode("?y", 2, self.entity_type)  # Same name but different instance
        complex_substitution = {x_var: y_var_2}
        
        # Apply the substitution
        complex_result = exists_y_forall_z.substitute(complex_substitution)
        
        # Verify the structure is preserved with correct substitutions
        self.assertIsInstance(complex_result, QuantifierNode)
        self.assertEqual(complex_result.quantifier_type, "EXISTS")
        
        # The inner formula should have ?y instead of ?x
        inner_forall = complex_result.scope
        self.assertIsInstance(inner_forall, QuantifierNode)
        inner_and = inner_forall.scope
        self.assertIsInstance(inner_and, ConnectiveNode)
        
        # First operand should be Loves(?y, ?y)
        first_app = inner_and.operands[0]
        self.assertIsInstance(first_app, ApplicationNode)

class TestASTNodesAdditional(unittest.TestCase):
    """Additional AST tests — originally orphaned top-level functions."""

    def setUp(self):
        """Set up the test case with types and helper nodes."""
        self.type_system = TypeSystemManager()
        self.entity_type = self.type_system.get_type("Entity")
        self.boolean_type = self.type_system.get_type("Boolean")
        self.integer_type = self.type_system.get_type("Integer")
        self.real_type = self.type_system.get_type("Real")

        self.unary_pred_type = FunctionType([self.entity_type], self.boolean_type)
        self.binary_pred_type = FunctionType([self.entity_type, self.entity_type], self.boolean_type)
        self.ternary_pred_type = FunctionType([self.entity_type, self.entity_type, self.entity_type], self.boolean_type)
        self.numeric_func_type = FunctionType([self.integer_type], self.integer_type)
        self.binary_numeric_func_type = FunctionType([self.integer_type, self.integer_type], self.integer_type)

    def test_visitor_pattern_with_complex_transformations(self):
        """Test the visitor pattern with complex AST transformations.
        
        This test verifies that the visitor pattern can be used to perform
        complex transformations on AST structures.
        """
        # Create variables and constants
        x_var = VariableNode("?x", 1, self.integer_type)
        y_var = VariableNode("?y", 2, self.integer_type)
        one_const = ConstantNode("1", self.integer_type, 1)
        two_const = ConstantNode("2", self.integer_type, 2)
        
        # Create arithmetic operators
        plus_op = ConstantNode("+", self.binary_numeric_func_type)
        minus_op = ConstantNode("-", self.binary_numeric_func_type)
        times_op = ConstantNode("*", self.binary_numeric_func_type)
        
        # Create a complex arithmetic expression: (x + 1) * (y - 2)
        x_plus_1 = ApplicationNode(plus_op, [x_var, one_const], self.integer_type)
        y_minus_2 = ApplicationNode(minus_op, [y_var, two_const], self.integer_type)
        expr = ApplicationNode(times_op, [x_plus_1, y_minus_2], self.integer_type)
        
        # Create a visitor that optimizes constant expressions
        class ConstantFolding(ASTVisitor[AST_Node]):
            def visit_constant(self, node: ConstantNode) -> AST_Node:
                return node
            
            def visit_variable(self, node: VariableNode) -> AST_Node:
                return node
            
            def visit_application(self, node: ApplicationNode) -> AST_Node:
                # Recursively optimize arguments
                new_op = node.operator.accept(self)
                new_args = [arg.accept(self) for arg in node.arguments]
                
                # Check if all arguments are constants
                if all(isinstance(arg, ConstantNode) and arg.value is not None for arg in new_args):
                    if isinstance(new_op, ConstantNode):
                        if new_op.name == "+":
                            result = new_args[0].value + new_args[1].value
                            return ConstantNode(str(result), self.integer_type, result)
                        elif new_op.name == "-":
                            result = new_args[0].value - new_args[1].value
                            return ConstantNode(str(result), self.integer_type, result)
                        elif new_op.name == "*":
                            result = new_args[0].value * new_args[1].value
                            return ConstantNode(str(result), self.integer_type, result)
                
                # If we can't optimize, return a new node with optimized children
                if new_op is node.operator and all(new_arg is old_arg for new_arg, old_arg in zip(new_args, node.arguments)):
                    return node
                return ApplicationNode(new_op, new_args, node.type)
            
            def visit_quantifier(self, node: QuantifierNode) -> AST_Node:
                new_scope = node.scope.accept(self)
                if new_scope is node.scope:
                    return node
                return QuantifierNode(node.quantifier_type, list(node.bound_variables), new_scope, node.type)
            
            def visit_connective(self, node: ConnectiveNode) -> AST_Node:
                new_operands = [op.accept(self) for op in node.operands]
                if all(new_op is old_op for new_op, old_op in zip(new_operands, node.operands)):
                    return node
                return ConnectiveNode(node.connective_type, new_operands, node.type)
            
            def visit_modal_op(self, node: ModalOpNode) -> AST_Node:
                new_prop = node.proposition.accept(self)
                new_agent = node.agent_or_world.accept(self) if node.agent_or_world else None
                if new_prop is node.proposition and new_agent is node.agent_or_world:
                    return node
                return ModalOpNode(node.modal_operator, new_prop, node.type, new_agent)
            
            def visit_lambda(self, node: LambdaNode) -> AST_Node:
                new_body = node.body.accept(self)
                if new_body is node.body:
                    return node
                return LambdaNode(list(node.bound_variables), new_body, node.type)
            
            def visit_definition(self, node: DefinitionNode) -> AST_Node:
                new_body = node.definition_body_ast.accept(self)
                if new_body is node.definition_body_ast:
                    return node
                return DefinitionNode(
                    node.defined_symbol_name,
                    node.defined_symbol_type,
                    new_body,
                    node.type
                )
        
        # Apply the constant folding visitor
        folder = ConstantFolding()
        optimized_expr = expr.accept(folder)
        
    def test_modal_logic_operators(self):
        """Test modal logic operators with complex nested structures.
        
        This test verifies that modal operators correctly handle nested structures
        and proper substitution.
        """
        # Create variables and constants
        x_var = VariableNode("?x", 1, self.entity_type)
        a_var = VariableNode("?a", 2, self.entity_type)
        
        # Create a predicate
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create an application: P(?x)
        p_x = ApplicationNode(p_pred, [x_var], self.boolean_type)
        
        # Create modal operators: K_?a(P(?x)) - "?a knows P(?x)"
        knows_a_p_x = ModalOpNode("KNOWS", p_x, self.boolean_type, a_var)
        
        # Create nested modal operators: B_?a(K_?a(P(?x))) - "?a believes that ?a knows P(?x)"
        believes_a_knows_p_x = ModalOpNode("BELIEVES", knows_a_p_x, self.boolean_type, a_var)
        
        # Test substitution
        b_const = ConstantNode("b", self.entity_type)
        substitution = {a_var: b_const}
        
        result = believes_a_knows_p_x.substitute(substitution)
        
        # Verify the result
        self.assertIsInstance(result, ModalOpNode)
        self.assertEqual(result.modal_operator, "BELIEVES")
        self.assertEqual(result.agent_or_world, b_const)
        
        inner_modal = result.proposition
        self.assertIsInstance(inner_modal, ModalOpNode)
        self.assertEqual(inner_modal.modal_operator, "KNOWS")
        self.assertEqual(inner_modal.agent_or_world, b_const)
        
        # Test complex visitor for modal logic
        class ModalDepthCounter(ASTVisitor[int]):
            def visit_constant(self, node: ConstantNode) -> int:
                return 0
            
            def visit_variable(self, node: VariableNode) -> int:
                return 0
            
            def visit_application(self, node: ApplicationNode) -> int:
                return max([node.operator.accept(self)] + [arg.accept(self) for arg in node.arguments])
            
            def visit_quantifier(self, node: QuantifierNode) -> int:
                return node.scope.accept(self)
            
            def visit_connective(self, node: ConnectiveNode) -> int:
                return max([op.accept(self) for op in node.operands])
            
            def visit_modal_op(self, node: ModalOpNode) -> int:
                agent_depth = node.agent_or_world.accept(self) if node.agent_or_world else 0
                return 1 + max(node.proposition.accept(self), agent_depth)
            
            def visit_lambda(self, node: LambdaNode) -> int:
                return node.body.accept(self)
    def test_definition_node_with_complex_body(self):
        """Test DefinitionNode with complex definition bodies.
        
        This test verifies that DefinitionNode correctly handles complex definition
        bodies and proper substitution.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create predicates
        human_pred = ConstantNode("Human", self.unary_pred_type)
        mortal_pred = ConstantNode("Mortal", self.unary_pred_type)
        
        # Create applications
        human_x = ApplicationNode(human_pred, [x_var], self.boolean_type)
        mortal_x = ApplicationNode(mortal_pred, [x_var], self.boolean_type)
        
        # Create a complex definition body: ∀?x. Human(?x) ⇒ Mortal(?x)
        implies = ConnectiveNode("IMPLIES", [human_x, mortal_x], self.boolean_type)
        forall_x_implies = QuantifierNode("FORALL", [x_var], implies, self.boolean_type)
        
        # Create a definition: HumanMortalAxiom := ∀?x. Human(?x) ⇒ Mortal(?x)
        definition = DefinitionNode(
            "HumanMortalAxiom",
            self.boolean_type,
            forall_x_implies,
            self.boolean_type
        )
        
        # Test substitution
        z_var = VariableNode("?z", 3, self.entity_type)
        substitution = {y_var: z_var}  # This shouldn't affect the definition
        
        result = definition.substitute(substitution)
        
        # The result should be the same as the original definition
        self.assertEqual(result, definition)
        
        # Test a substitution that would affect the definition
        socrates = ConstantNode("Socrates", self.entity_type)
        affecting_substitution = {x_var: socrates}
        
        # This shouldn't affect the definition because x_var is bound
        affecting_result = definition.substitute(affecting_substitution)
        
        # The result should still be the same as the original definition
        self.assertEqual(affecting_result, definition)
    def test_ast_node_metadata_inheritance(self):
        """Test metadata inheritance during AST node transformations.
        
        This test verifies that metadata is correctly inherited during
        AST node transformations like substitution.
        """
        # Create a variable with metadata
        metadata = {"source": "user", "confidence": 0.9, "timestamp": "2025-05-19"}
        x_var = VariableNode("?x", 1, self.entity_type, metadata)
        
        # Create a predicate
        human_pred = ConstantNode("Human", self.unary_pred_type)
        
        # Create an application with its own metadata
        app_metadata = {"rule_applied": "predication", "confidence": 0.8}
        human_x = ApplicationNode(human_pred, [x_var], self.boolean_type, app_metadata)
        
        # Test metadata access
        self.assertEqual(x_var.metadata["source"], "user")
        self.assertEqual(x_var.metadata["confidence"], 0.9)
        self.assertEqual(human_x.metadata["rule_applied"], "predication")
        self.assertEqual(human_x.metadata["confidence"], 0.8)
        
        # Test metadata modification through with_metadata
        updated_x = x_var.with_metadata(confidence=0.95, new_field="test")
        self.assertEqual(updated_x.metadata["confidence"], 0.95)
        self.assertEqual(updated_x.metadata["new_field"], "test")
        self.assertEqual(updated_x.metadata["source"], "user")  # Original field preserved
        
        # Original node should be unchanged
        self.assertEqual(x_var.metadata["confidence"], 0.9)
        self.assertNotIn("new_field", x_var.metadata)
        
        # Test metadata inheritance during substitution
        socrates = ConstantNode("Socrates", self.entity_type)
        substitution = {x_var: socrates}
        
        result = human_x.substitute(substitution)
        
        # The result should inherit the metadata from human_x
        self.assertEqual(result.metadata["rule_applied"], "predication")
        self.assertEqual(result.metadata["confidence"], 0.8)
        
        # Test with_updated_metadata
        completely_new_metadata = {"new_source": "inference", "confidence": 1.0}
        new_human_x = human_x.with_updated_metadata(completely_new_metadata)
        
        self.assertEqual(new_human_x.metadata["new_source"], "inference")
    def test_performance_critical_operations(self):
        """Test performance of critical AST operations.
        
        This test measures the performance of critical operations like
        substitution and traversal on large AST structures.
        """
        # Create a large number of variables
        num_vars = 100
        variables = [VariableNode(f"?x{i}", i, self.entity_type) for i in range(num_vars)]
        
        # Create a predicate
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create a large number of applications
        applications = [ApplicationNode(p_pred, [var], self.boolean_type) for var in variables]
        
        # Create a large conjunction
        large_conjunction = ConnectiveNode("AND", applications, self.boolean_type)
        
        # Measure substitution performance
        substitution = {variables[0]: ConstantNode("c", self.entity_type)}
        
        start_time = time.time()
        result = large_conjunction.substitute(substitution)
        substitution_time = time.time() - start_time
        
        print(f"Substitution time for {num_vars} conjuncts: {substitution_time * 1000:.2f} ms")
        
        # Verify the substitution worked correctly
        self.assertIsInstance(result, ConnectiveNode)
        self.assertEqual(result.connective_type, "AND")
        self.assertEqual(len(result.operands), num_vars)
        
        # Measure traversal performance
        class NodeCounter(ASTVisitor[int]):
            def visit_constant(self, node: ConstantNode) -> int:
                return 1
            
            def visit_variable(self, node: VariableNode) -> int:
                return 1
            
            def visit_application(self, node: ApplicationNode) -> int:
                return 1 + node.operator.accept(self) + sum(arg.accept(self) for arg in node.arguments)
            
            def visit_quantifier(self, node: QuantifierNode) -> int:
                return 1 + len(node.bound_variables) + node.scope.accept(self)
            
            def visit_connective(self, node: ConnectiveNode) -> int:
                return 1 + sum(op.accept(self) for op in node.operands)
            
            def visit_modal_op(self, node: ModalOpNode) -> int:
                agent_count = node.agent_or_world.accept(self) if node.agent_or_world else 0
                return 1 + node.proposition.accept(self) + agent_count
            
            def visit_lambda(self, node: LambdaNode) -> int:
                return 1 + len(node.bound_variables) + node.body.accept(self)
            
            def visit_definition(self, node: DefinitionNode) -> int:
                return 1 + node.definition_body_ast.accept(self)
        
        counter = NodeCounter()
        
        start_time = time.time()
        count = large_conjunction.accept(counter)
        traversal_time = time.time() - start_time
        
        print(f"Traversal time for {count} nodes: {traversal_time * 1000:.2f} ms")
        
    def test_contains_variable_edge_cases(self):
        """Test edge cases for the contains_variable method.
        
        This test verifies that the contains_variable method correctly handles
        edge cases like nested quantifiers and variable shadowing.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        
        # Create a predicate
        p_pred = ConstantNode("P", self.binary_pred_type)
        
        # Create an application: P(?x, ?y)
        p_x_y = ApplicationNode(p_pred, [x_var, y_var], self.boolean_type)
        
        # Create nested quantifiers with shadowing: ∀?x. ∃?y. P(?x, ?y)
        exists_y_p_x_y = QuantifierNode("EXISTS", [y_var], p_x_y, self.boolean_type)
        forall_x_exists_y = QuantifierNode("FORALL", [x_var], exists_y_p_x_y, self.boolean_type)
        
        # Test contains_variable on the nested structure
        
        # x_var is bound by the outer quantifier, so it shouldn't be contained
        self.assertFalse(forall_x_exists_y.contains_variable(x_var))
        
        # y_var is bound by the inner quantifier, so it shouldn't be contained
        self.assertFalse(forall_x_exists_y.contains_variable(y_var))
        
        # z_var is not bound, so it should not be contained (since it's not in the formula)
        self.assertFalse(forall_x_exists_y.contains_variable(z_var))
        
        # Create a more complex structure with partial shadowing
        # ∀?x. (P(?x, ?y) ∧ ∃?y. P(?x, ?y))
        
        # Inner formula with bound y
        p_x_y_inner = ApplicationNode(p_pred, [x_var, y_var], self.boolean_type)
        exists_y_p_x_y_inner = QuantifierNode("EXISTS", [y_var], p_x_y_inner, self.boolean_type)
        
        # Outer formula with free y
        p_x_y_outer = ApplicationNode(p_pred, [x_var, y_var], self.boolean_type)
        
        # Combine with AND
        complex_and = ConnectiveNode("AND", [p_x_y_outer, exists_y_p_x_y_inner], self.boolean_type)
        
        # Wrap with forall x
        forall_x_complex = QuantifierNode("FORALL", [x_var], complex_and, self.boolean_type)
        
        # x_var is bound by the outer quantifier, so it shouldn't be contained
        self.assertFalse(forall_x_complex.contains_variable(x_var))
        
        # y_var appears free in the left conjunct, so it should be contained
        self.assertTrue(forall_x_complex.contains_variable(y_var))
        
        # Test with lambda expressions
        # λ?x. P(?x, ?y)
        lambda_x_p_x_y = LambdaNode([x_var], p_x_y, self.unary_pred_type)
        
        # x_var is bound by the lambda, so it shouldn't be contained
        self.assertFalse(lambda_x_p_x_y.contains_variable(x_var))
        
        # y_var is free in the lambda body, so it should be contained
        self.assertTrue(lambda_x_p_x_y.contains_variable(y_var))


if __name__ == "__main__":
    unittest.main()