"""
Enhanced unit tests for the Unification Engine component.

This file extends the basic tests in test_unification.py with more thorough
testing of complex methods and edge cases, focusing on the unification algorithm,
substitution application, and handling of complex term structures.
"""

import unittest
from unittest.mock import patch, MagicMock
import time
from typing import Dict, List, Optional, Set, Any, Tuple

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode
)
from godelOS.core_kr.unification_engine.engine import UnificationEngine

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker


class TestUnificationEngineEnhanced(unittest.TestCase):
    """Enhanced test cases for the Unification Engine with complex scenarios and edge cases."""
    
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
        self.unary_func_type = FunctionType([self.entity_type], self.entity_type)
        self.binary_func_type = FunctionType([self.entity_type, self.entity_type], self.entity_type)
        self.unary_pred_type = FunctionType([self.entity_type], self.boolean_type)
        self.binary_pred_type = FunctionType([self.entity_type, self.entity_type], self.boolean_type)
        
        # Create the unification engine
        self.unification_engine = UnificationEngine(self.type_system)
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    
    def test_unification_with_complex_terms(self):
        """Test unification with complex nested terms.
        
        This test verifies that the unification engine correctly unifies
        complex terms with nested function applications and variables.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        b_const = ConstantNode("b", self.entity_type)
        c_const = ConstantNode("c", self.entity_type)
        
        # Create function symbols
        f_func = ConstantNode("f", self.unary_func_type)
        g_func = ConstantNode("g", self.binary_func_type)
        
        # Create complex terms
        # f(x)
        f_x = ApplicationNode(f_func, [x_var], self.entity_type)
        
        # g(y, z)
        g_y_z = ApplicationNode(g_func, [y_var, z_var], self.entity_type)
        
        # f(g(y, z))
        f_g_y_z = ApplicationNode(f_func, [g_y_z], self.entity_type)
        
        # f(g(a, b))
        g_a_b = ApplicationNode(g_func, [a_const, b_const], self.entity_type)
        f_g_a_b = ApplicationNode(f_func, [g_a_b], self.entity_type)
        
        # Unify f(x) with f(g(y, z))
        substitution1 = self.unification_engine.unify(f_x, f_g_y_z)
        
        # Verify the substitution
        self.assertIsNotNone(substitution1)
        self.assertIn(x_var, substitution1)
        self.assertEqual(substitution1[x_var], g_y_z)
        
        # Unify f(g(y, z)) with f(g(a, b))
        substitution2 = self.unification_engine.unify(f_g_y_z, f_g_a_b)
        
        # Verify the substitution
        self.assertIsNotNone(substitution2)
        self.assertIn(y_var, substitution2)
        self.assertIn(z_var, substitution2)
        self.assertEqual(substitution2[y_var], a_const)
        self.assertEqual(substitution2[z_var], b_const)
        
        # Unify f(g(y, z)) with f(g(y, c))
        g_y_c = ApplicationNode(g_func, [y_var, c_const], self.entity_type)
        f_g_y_c = ApplicationNode(f_func, [g_y_c], self.entity_type)
        
        substitution3 = self.unification_engine.unify(f_g_y_z, f_g_y_c)
        
        # Verify the substitution
        self.assertIsNotNone(substitution3)
        self.assertIn(z_var, substitution3)
        self.assertEqual(substitution3[z_var], c_const)
        self.assertNotIn(y_var, substitution3)  # y is the same in both terms
    
    def test_occurs_check(self):
        """Test the occurs check in unification.
        
        This test verifies that the unification engine correctly performs
        the occurs check to prevent circular substitutions.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        
        # Create function symbols
        f_func = ConstantNode("f", self.unary_func_type)
        
        # Create terms
        # f(x)
        f_x = ApplicationNode(f_func, [x_var], self.entity_type)
        
        # Attempt to unify x with f(x), which should fail due to occurs check
        substitution = self.unification_engine.unify(x_var, f_x)
        
        # Verify that unification failed
        self.assertIsNone(substitution)
        
        # Create a more complex case
        # g(x, f(x))
        g_func = ConstantNode("g", self.binary_func_type)
        g_x_f_x = ApplicationNode(g_func, [x_var, f_x], self.entity_type)
        
        # Create another variable
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Attempt to unify y with g(y, f(y)), which should fail
        g_y_f_y = ApplicationNode(g_func, [y_var, ApplicationNode(f_func, [y_var], self.entity_type)], self.entity_type)
        
        substitution = self.unification_engine.unify(y_var, g_y_f_y)
        
        # Verify that unification failed
        self.assertIsNone(substitution)
    
    def test_unification_with_multiple_occurrences(self):
        """Test unification with multiple occurrences of the same variable.
        
        This test verifies that the unification engine correctly handles
        terms with multiple occurrences of the same variable.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        b_const = ConstantNode("b", self.entity_type)
        
        # Create function symbols
        f_func = ConstantNode("f", self.binary_func_type)
        
        # Create terms with repeated variables
        # f(x, x)
        f_x_x = ApplicationNode(f_func, [x_var, x_var], self.entity_type)
        
        # f(a, a)
        f_a_a = ApplicationNode(f_func, [a_const, a_const], self.entity_type)
        
        # f(a, b)
        f_a_b = ApplicationNode(f_func, [a_const, b_const], self.entity_type)
        
        # Unify f(x, x) with f(a, a)
        substitution1 = self.unification_engine.unify(f_x_x, f_a_a)
        
        # Verify the substitution
        self.assertIsNotNone(substitution1)
        self.assertIn(x_var, substitution1)
        self.assertEqual(substitution1[x_var], a_const)
        
        # Attempt to unify f(x, x) with f(a, b), which should fail
        substitution2 = self.unification_engine.unify(f_x_x, f_a_b)
        
        # Verify that unification failed
        self.assertIsNone(substitution2)
        
        # Create terms with different variables
        # f(x, y)
        f_x_y = ApplicationNode(f_func, [x_var, y_var], self.entity_type)
        
        # Unify f(x, y) with f(a, b)
        substitution3 = self.unification_engine.unify(f_x_y, f_a_b)
        
        # Verify the substitution
        self.assertIsNotNone(substitution3)
        self.assertIn(x_var, substitution3)
        self.assertIn(y_var, substitution3)
        self.assertEqual(substitution3[x_var], a_const)
        self.assertEqual(substitution3[y_var], b_const)
    
    def test_substitution_application(self):
        """Test application of substitutions to terms.
        
        This test verifies that the unification engine correctly applies
        substitutions to terms, replacing variables with their values.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        b_const = ConstantNode("b", self.entity_type)
        
        # Create function symbols
        f_func = ConstantNode("f", self.unary_func_type)
        g_func = ConstantNode("g", self.binary_func_type)
        
        # Create a substitution
        substitution = {
            x_var: a_const,
            y_var: b_const,
            z_var: ApplicationNode(f_func, [a_const], self.entity_type)  # f(a)
        }
        
        # Create a term to apply the substitution to
        # g(x, f(y))
        f_y = ApplicationNode(f_func, [y_var], self.entity_type)
        g_x_f_y = ApplicationNode(g_func, [x_var, f_y], self.entity_type)
        
        # Apply the substitution
        result = self.unification_engine.apply_substitution(g_x_f_y, substitution)
        
        # Verify the result: g(a, f(b))
        self.assertIsInstance(result, ApplicationNode)
        self.assertEqual(result.operator, g_func)
        self.assertEqual(len(result.arguments), 2)
        self.assertEqual(result.arguments[0], a_const)
        
        f_b = result.arguments[1]
        self.assertIsInstance(f_b, ApplicationNode)
        self.assertEqual(f_b.operator, f_func)
        self.assertEqual(len(f_b.arguments), 1)
        self.assertEqual(f_b.arguments[0], b_const)
        
        # Create a more complex term
        # g(z, f(x))
        f_x = ApplicationNode(f_func, [x_var], self.entity_type)
        g_z_f_x = ApplicationNode(g_func, [z_var, f_x], self.entity_type)
        
        # Apply the substitution
        result = self.unification_engine.apply_substitution(g_z_f_x, substitution)
        
        # Verify the result: g(f(a), f(a))
        self.assertIsInstance(result, ApplicationNode)
        self.assertEqual(result.operator, g_func)
        self.assertEqual(len(result.arguments), 2)
        
        f_a = result.arguments[0]
        self.assertIsInstance(f_a, ApplicationNode)
        self.assertEqual(f_a.operator, f_func)
        self.assertEqual(len(f_a.arguments), 1)
        self.assertEqual(f_a.arguments[0], a_const)
        
        f_a2 = result.arguments[1]
        self.assertIsInstance(f_a2, ApplicationNode)
        self.assertEqual(f_a2.operator, f_func)
        self.assertEqual(len(f_a2.arguments), 1)
        self.assertEqual(f_a2.arguments[0], a_const)
    
    def test_composition_of_substitutions(self):
        """Test composition of substitutions.
        
        This test verifies that the unification engine correctly composes
        substitutions, applying one substitution after another.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        b_const = ConstantNode("b", self.entity_type)
        c_const = ConstantNode("c", self.entity_type)
        
        # Create the first substitution: {x -> y, z -> c}
        substitution1 = {
            x_var: y_var,
            z_var: c_const
        }
        
        # Create the second substitution: {y -> a, z -> b}
        substitution2 = {
            y_var: a_const,
            z_var: b_const
        }
        
        # Compose the substitutions
        composed = self.unification_engine.compose_substitutions(substitution1, substitution2)
        
        # Verify the composed substitution: {x -> a, y -> a, z -> c}
        self.assertIn(x_var, composed)
        self.assertIn(y_var, composed)
        self.assertIn(z_var, composed)
        self.assertEqual(composed[x_var], a_const)  # x -> y -> a
        self.assertEqual(composed[y_var], a_const)  # y -> a
        self.assertEqual(composed[z_var], c_const)  # z -> c (not overridden)
        
        # Create a more complex substitution with function terms
        f_func = ConstantNode("f", self.unary_func_type)
        f_y = ApplicationNode(f_func, [y_var], self.entity_type)
        
        # {x -> f(y), y -> a}
        substitution3 = {
            x_var: f_y,
            y_var: a_const
        }
        
        # Apply this substitution to itself (compose with itself)
        composed2 = self.unification_engine.compose_substitutions(substitution3, substitution3)
        
        # Verify the composed substitution: {x -> f(a), y -> a}
        self.assertIn(x_var, composed2)
        self.assertIn(y_var, composed2)
        
        f_a = composed2[x_var]
        self.assertIsInstance(f_a, ApplicationNode)
        self.assertEqual(f_a.operator, f_func)
        self.assertEqual(len(f_a.arguments), 1)
        self.assertEqual(f_a.arguments[0], a_const)
        
        self.assertEqual(composed2[y_var], a_const)
    
    def test_most_general_unifier(self):
        """Test finding the most general unifier.
        
        This test verifies that the unification engine finds the most
        general unifier (MGU) for unifiable terms.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        
        # Create function symbols
        f_func = ConstantNode("f", self.unary_func_type)
        g_func = ConstantNode("g", self.binary_func_type)
        
        # Create terms to unify
        # f(x) and f(y)
        f_x = ApplicationNode(f_func, [x_var], self.entity_type)
        f_y = ApplicationNode(f_func, [y_var], self.entity_type)
        
        # Find the MGU
        mgu1 = self.unification_engine.unify(f_x, f_y)
        
        # Verify the MGU: {x -> y} or {y -> x}
        self.assertIsNotNone(mgu1)
        self.assertEqual(len(mgu1), 1)
        if x_var in mgu1:
            self.assertEqual(mgu1[x_var], y_var)
        else:
            self.assertEqual(mgu1[y_var], x_var)
        
        # Create more complex terms to unify
        # g(x, f(y)) and g(z, f(a))
        g_x_f_y = ApplicationNode(g_func, [x_var, f_y], self.entity_type)
        f_a = ApplicationNode(f_func, [a_const], self.entity_type)
        g_z_f_a = ApplicationNode(g_func, [z_var, f_a], self.entity_type)
        
        # Find the MGU
        mgu2 = self.unification_engine.unify(g_x_f_y, g_z_f_a)
        
        # Verify the MGU: {x -> z, y -> a}
        self.assertIsNotNone(mgu2)
        self.assertEqual(len(mgu2), 2)
        self.assertIn(x_var, mgu2)
        self.assertIn(y_var, mgu2)
        self.assertEqual(mgu2[x_var], z_var)
        self.assertEqual(mgu2[y_var], a_const)
    
    def test_performance_with_large_terms(self):
        """Test performance with large terms.
        
        This test verifies that the unification engine efficiently handles
        unification of large terms with many subterms.
        """
        # Create function symbols
        f_func = ConstantNode("f", self.unary_func_type)
        
        # Create a deeply nested term: f(f(f(...f(x)...)))
        depth = 100
        x_var = VariableNode("?x", 1, self.entity_type)
        
        term1 = x_var
        for _ in range(depth):
            term1 = ApplicationNode(f_func, [term1], self.entity_type)
        
        # Create another deeply nested term: f(f(f(...f(y)...)))
        y_var = VariableNode("?y", 2, self.entity_type)
        
        term2 = y_var
        for _ in range(depth):
            term2 = ApplicationNode(f_func, [term2], self.entity_type)
        
        # Measure the time to unify the terms
        start_time = time.time()
        substitution = self.unification_engine.unify(term1, term2)
        unification_time = time.time() - start_time
        
        print(f"Time to unify terms of depth {depth}: {unification_time * 1000:.2f} ms")
        
        # Verify the substitution
        self.assertIsNotNone(substitution)
        self.assertEqual(len(substitution), 1)
        if x_var in substitution:
            self.assertEqual(substitution[x_var], y_var)
        else:
            self.assertEqual(substitution[y_var], x_var)
    
    def test_unification_failure_cases(self):
        """Test cases where unification should fail.
        
        This test verifies that the unification engine correctly identifies
        cases where terms cannot be unified.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        b_const = ConstantNode("b", self.entity_type)
        
        # Create function symbols
        f_func = ConstantNode("f", self.unary_func_type)
        g_func = ConstantNode("g", self.unary_func_type)
        
        # Case 1: Different constants
        # Attempt to unify a with b
        substitution1 = self.unification_engine.unify(a_const, b_const)
        
        # Verify that unification failed
        self.assertIsNone(substitution1)
        
        # Case 2: Different function symbols
        # Attempt to unify f(x) with g(x)
        f_x = ApplicationNode(f_func, [x_var], self.entity_type)
        g_x = ApplicationNode(g_func, [x_var], self.entity_type)
        
        substitution2 = self.unification_engine.unify(f_x, g_x)
        
        # Verify that unification failed
        self.assertIsNone(substitution2)
        
        # Case 3: Different arities
        # Create a binary function symbol
        h_func = ConstantNode("h", self.binary_func_type)
        
        # Attempt to unify f(x) with h(x, x)
        h_x_x = ApplicationNode(h_func, [x_var, x_var], self.entity_type)
        
        substitution3 = self.unification_engine.unify(f_x, h_x_x)
        
        # Verify that unification failed
        self.assertIsNone(substitution3)
        
        # Case 4: Occurs check
        # Attempt to unify x with f(x)
        substitution4 = self.unification_engine.unify(x_var, f_x)
        
        # Verify that unification failed
        self.assertIsNone(substitution4)
    
    def test_unification_with_predicates(self):
        """Test unification with predicate expressions.
        
        This test verifies that the unification engine correctly unifies
        predicate expressions, handling both the predicate and its arguments.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        b_const = ConstantNode("b", self.entity_type)
        
        # Create predicate symbols
        p_pred = ConstantNode("P", self.unary_pred_type)
        q_pred = ConstantNode("Q", self.binary_pred_type)
        
        # Create predicate expressions
        # P(x)
        p_x = ApplicationNode(p_pred, [x_var], self.boolean_type)
        
        # P(a)
        p_a = ApplicationNode(p_pred, [a_const], self.boolean_type)
        
        # Q(x, y)
        q_x_y = ApplicationNode(q_pred, [x_var, y_var], self.boolean_type)
        
        # Q(a, b)
        q_a_b = ApplicationNode(q_pred, [a_const, b_const], self.boolean_type)
        
        # Unify P(x) with P(a)
        substitution1 = self.unification_engine.unify(p_x, p_a)
        
        # Verify the substitution
        self.assertIsNotNone(substitution1)
        self.assertIn(x_var, substitution1)
        self.assertEqual(substitution1[x_var], a_const)
        
        # Unify Q(x, y) with Q(a, b)
        substitution2 = self.unification_engine.unify(q_x_y, q_a_b)
        
        # Verify the substitution
        self.assertIsNotNone(substitution2)
        self.assertIn(x_var, substitution2)
        self.assertIn(y_var, substitution2)
        self.assertEqual(substitution2[x_var], a_const)
        self.assertEqual(substitution2[y_var], b_const)
        
        # Attempt to unify P(x) with Q(a, b), which should fail
        substitution3 = self.unification_engine.unify(p_x, q_a_b)
        
        # Verify that unification failed
        self.assertIsNone(substitution3)


if __name__ == "__main__":
    unittest.main()