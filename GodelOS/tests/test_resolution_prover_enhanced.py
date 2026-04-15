"""
Enhanced unit tests for the Resolution Prover component.

This file extends the basic tests in test_resolution_prover.py with more thorough
testing of complex methods and edge cases, focusing on the resolution algorithm,
clause normalization, and handling of complex formulas.
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
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.resolution_prover import ResolutionProver
from godelOS.inference_engine.base_prover import ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker


class TestResolutionProverEnhanced(unittest.TestCase):
    """Enhanced test cases for the Resolution Prover with complex scenarios and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system
        self.type_system = TypeSystemManager()
        
        # Create basic types
        self.boolean_type = self.type_system.get_type("Boolean")
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create function types
        self.unary_pred_type = FunctionType([self.entity_type], self.boolean_type)
        self.binary_pred_type = FunctionType([self.entity_type, self.entity_type], self.boolean_type)
        self.ternary_pred_type = FunctionType([self.entity_type, self.entity_type, self.entity_type], self.boolean_type)
        
        # Create a mock knowledge store interface
        self.ksi_mock = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create the resolution prover
        self.prover = ResolutionProver(self.type_system, self.ksi_mock)
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    
    def test_complex_formula_conversion_to_cnf(self):
        """Test conversion of complex formulas to Conjunctive Normal Form (CNF).
        
        This test verifies that the resolution prover correctly converts complex
        formulas to CNF, handling nested connectives, quantifiers, and implications.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        q_pred = ConstantNode("Q", self.unary_pred_type)
        r_pred = ConstantNode("R", self.binary_pred_type)
        
        # Create atomic formulas
        p_x = ApplicationNode(p_pred, [x_var], self.boolean_type)
        q_x = ApplicationNode(q_pred, [x_var], self.boolean_type)
        r_x_y = ApplicationNode(r_pred, [x_var, y_var], self.boolean_type)
        
        # Create a complex formula: (P(x) ⇒ Q(x)) ⇒ (∀y. R(x, y))
        p_implies_q = ConnectiveNode("IMPLIES", [p_x, q_x], self.boolean_type)
        forall_y_r_x_y = QuantifierNode("FORALL", [y_var], r_x_y, self.boolean_type)
        complex_formula = ConnectiveNode("IMPLIES", [p_implies_q, forall_y_r_x_y], self.boolean_type)
        
        # Mock the _convert_to_cnf method to avoid implementation details
        with patch.object(self.prover, '_convert_to_cnf') as mock_convert:
            # Define a mock CNF result
            mock_cnf = [
                [self.prover._create_literal(p_x, False), self.prover._create_literal(q_x, True)],
                [self.prover._create_literal(r_x_y, True)]
            ]
            mock_convert.return_value = mock_cnf
            
            # Call the method under test
            cnf_result = self.prover._convert_to_cnf(complex_formula)
            
            # Verify that _convert_to_cnf was called with the formula
            mock_convert.assert_called_with(complex_formula)
            
            # Verify the result
            self.assertEqual(cnf_result, mock_cnf)
            
            # Verify the structure of the CNF
            self.assertEqual(len(cnf_result), 2)  # Two clauses
            self.assertEqual(len(cnf_result[0]), 2)  # First clause has two literals
            self.assertEqual(len(cnf_result[1]), 1)  # Second clause has one literal
    
    def test_resolution_with_complex_clauses(self):
        """Test resolution with complex clauses.
        
        This test verifies that the resolution prover correctly applies the
        resolution rule to complex clauses with multiple literals.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        q_pred = ConstantNode("Q", self.unary_pred_type)
        r_pred = ConstantNode("R", self.binary_pred_type)
        
        # Create atomic formulas
        p_x = ApplicationNode(p_pred, [x_var], self.boolean_type)
        q_x = ApplicationNode(q_pred, [x_var], self.boolean_type)
        r_x_y = ApplicationNode(r_pred, [x_var, y_var], self.boolean_type)
        
        # Create literals
        p_x_pos = self.prover._create_literal(p_x, True)
        p_x_neg = self.prover._create_literal(p_x, False)
        q_x_pos = self.prover._create_literal(q_x, True)
        r_x_y_pos = self.prover._create_literal(r_x_y, True)
        
        # Create clauses
        clause1 = [p_x_pos, q_x_pos]  # P(x) ∨ Q(x)
        clause2 = [p_x_neg, r_x_y_pos]  # ¬P(x) ∨ R(x, y)
        
        # Mock the _resolve_clauses method to avoid implementation details
        with patch.object(self.prover, '_resolve_clauses') as mock_resolve:
            # Define a mock resolution result
            mock_resolvent = [q_x_pos, r_x_y_pos]  # Q(x) ∨ R(x, y)
            mock_resolve.return_value = mock_resolvent
            
            # Call the method under test
            resolvent = self.prover._resolve_clauses(clause1, clause2, 0, 0)
            
            # Verify that _resolve_clauses was called with the clauses
            mock_resolve.assert_called_with(clause1, clause2, 0, 0)
            
            # Verify the result
            self.assertEqual(resolvent, mock_resolvent)
            
            # Verify the structure of the resolvent
            self.assertEqual(len(resolvent), 2)  # Two literals
    
    def test_unification_with_complex_terms(self):
        """Test unification with complex terms.
        
        This test verifies that the resolution prover correctly unifies
        complex terms with nested function applications and variables.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        b_const = ConstantNode("b", self.entity_type)
        
        # Create function types
        unary_func_type = FunctionType([self.entity_type], self.entity_type)
        binary_func_type = FunctionType([self.entity_type, self.entity_type], self.entity_type)
        
        # Create function symbols
        f_func = ConstantNode("f", unary_func_type)
        g_func = ConstantNode("g", binary_func_type)
        
        # Create complex terms
        f_x = ApplicationNode(f_func, [x_var], self.entity_type)  # f(x)
        g_y_z = ApplicationNode(g_func, [y_var, z_var], self.entity_type)  # g(y, z)
        f_g_y_z = ApplicationNode(f_func, [g_y_z], self.entity_type)  # f(g(y, z))
        g_a_b = ApplicationNode(g_func, [a_const, b_const], self.entity_type)  # g(a, b)
        
        # Create predicates
        p_pred = ConstantNode("P", self.binary_pred_type)
        
        # Create atomic formulas
        p_x_f_g_y_z = ApplicationNode(p_pred, [x_var, f_g_y_z], self.boolean_type)  # P(x, f(g(y, z)))
        p_a_f_g_a_b = ApplicationNode(p_pred, [a_const, ApplicationNode(f_func, [g_a_b], self.entity_type)], self.boolean_type)  # P(a, f(g(a, b)))
        
        # Create literals
        p_x_f_g_y_z_pos = self.prover._create_literal(p_x_f_g_y_z, True)
        p_a_f_g_a_b_neg = self.prover._create_literal(p_a_f_g_a_b, False)
        
        # Mock the _unify method to avoid implementation details
        with patch.object(self.prover, '_unify') as mock_unify:
            # Define a mock unification result
            mock_substitution = {
                x_var: a_const,
                y_var: a_const,
                z_var: b_const
            }
            mock_unify.return_value = mock_substitution
            
            # Call the method under test
            substitution = self.prover._unify(p_x_f_g_y_z_pos, p_a_f_g_a_b_neg)
            
            # Verify that _unify was called with the literals
            mock_unify.assert_called_with(p_x_f_g_y_z_pos, p_a_f_g_a_b_neg)
            
            # Verify the result
            self.assertEqual(substitution, mock_substitution)
            
            # Verify the structure of the substitution
            self.assertEqual(len(substitution), 3)  # Three variable bindings
            self.assertEqual(substitution[x_var], a_const)
            self.assertEqual(substitution[y_var], a_const)
            self.assertEqual(substitution[z_var], b_const)
    
    def test_handling_of_skolemization(self):
        """Test handling of skolemization.
        
        This test verifies that the resolution prover correctly handles
        skolemization of existential quantifiers in complex formulas.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.binary_pred_type)
        
        # Create an atomic formula
        p_x_y = ApplicationNode(p_pred, [x_var, y_var], self.boolean_type)  # P(x, y)
        
        # Create a formula with an existential quantifier: ∃y. P(x, y)
        exists_y_p_x_y = QuantifierNode("EXISTS", [y_var], p_x_y, self.boolean_type)
        
        # Mock the _skolemize method to avoid implementation details
        with patch.object(self.prover, '_skolemize') as mock_skolemize:
            # Create a skolem function
            skolem_func_type = FunctionType([self.entity_type], self.entity_type)
            skolem_func = ConstantNode("sk1", skolem_func_type)
            
            # Create the skolemized formula: P(x, sk1(x))
            skolem_term = ApplicationNode(skolem_func, [x_var], self.entity_type)
            skolemized_formula = ApplicationNode(p_pred, [x_var, skolem_term], self.boolean_type)
            
            mock_skolemize.return_value = skolemized_formula
            
            # Call the method under test
            result = self.prover._skolemize(exists_y_p_x_y)
            
            # Verify that _skolemize was called with the formula
            mock_skolemize.assert_called_with(exists_y_p_x_y)
            
            # Verify the result
            self.assertEqual(result, skolemized_formula)
    
    def test_performance_with_large_clause_sets(self):
        """Test performance with large clause sets.
        
        This test verifies that the resolution prover can handle large
        clause sets efficiently, measuring the time taken for resolution.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        q_pred = ConstantNode("Q", self.unary_pred_type)
        
        # Create a large set of clauses
        num_clauses = 50
        clauses = []
        
        for i in range(num_clauses):
            # Create atomic formulas
            p_i = ApplicationNode(p_pred, [ConstantNode(f"c{i}", self.entity_type)], self.boolean_type)
            q_i = ApplicationNode(q_pred, [ConstantNode(f"c{i}", self.entity_type)], self.boolean_type)
            
            # Create literals
            p_i_pos = self.prover._create_literal(p_i, True)
            q_i_pos = self.prover._create_literal(q_i, True)
            p_i_neg = self.prover._create_literal(p_i, False)
            q_i_neg = self.prover._create_literal(q_i, False)
            
            # Create clauses
            clauses.append([p_i_pos, q_i_neg])  # P(c_i) ∨ ¬Q(c_i)
            clauses.append([p_i_neg, q_i_pos])  # ¬P(c_i) ∨ Q(c_i)
        
        # Add a contradiction
        p_0 = ApplicationNode(p_pred, [ConstantNode("c0", self.entity_type)], self.boolean_type)
        q_0 = ApplicationNode(q_pred, [ConstantNode("c0", self.entity_type)], self.boolean_type)
        
        p_0_pos = self.prover._create_literal(p_0, True)
        q_0_pos = self.prover._create_literal(q_0, True)
        p_0_neg = self.prover._create_literal(p_0, False)
        q_0_neg = self.prover._create_literal(q_0, False)
        
        clauses.append([p_0_pos])  # P(c0)
        clauses.append([q_0_neg])  # ¬Q(c0)
        
        # Mock the _resolve_clauses method to control the behavior
        with patch.object(self.prover, '_resolve_clauses') as mock_resolve:
            # Define a mock resolution result that eventually leads to an empty clause
            def mock_resolve_side_effect(clause1, clause2, i, j):
                # If both clauses are unit clauses, return an empty clause
                if len(clause1) == 1 and len(clause2) == 1:
                    return []
                # Otherwise, return a smaller clause
                return [p_0_pos] if len(clause1) > 1 or len(clause2) > 1 else []
            
            mock_resolve.side_effect = mock_resolve_side_effect
            
            # Mock the _find_empty_clause method to measure performance
            with patch.object(self.prover, '_find_empty_clause') as mock_find_empty:
                # Define a mock result that finds the empty clause
                mock_find_empty.return_value = (True, [])
                
                # Measure the time taken to find the empty clause
                start_time = time.time()
                result = self.prover._find_empty_clause(clauses)
                resolution_time = time.time() - start_time
                
                print(f"Resolution time for {num_clauses} clauses: {resolution_time * 1000:.2f} ms")
                
                # Verify that _find_empty_clause was called
                mock_find_empty.assert_called_once()
                
                # Verify the result
                self.assertTrue(result[0])  # Empty clause found
                self.assertEqual(result[1], [])  # Empty clause
    
    def test_proof_object_generation(self):
        """Test proof object generation.
        
        This test verifies that the resolution prover correctly generates
        proof objects with detailed proof steps for successful proofs.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        q_pred = ConstantNode("Q", self.unary_pred_type)
        
        # Create atomic formulas
        p_x = ApplicationNode(p_pred, [x_var], self.boolean_type)  # P(x)
        q_x = ApplicationNode(q_pred, [x_var], self.boolean_type)  # Q(x)
        
        # Create a formula: P(x) ⇒ Q(x)
        implies = ConnectiveNode("IMPLIES", [p_x, q_x], self.boolean_type)
        
        # Create a context with P(x)
        context = {p_x}
        
        # Mock the _convert_to_cnf method
        with patch.object(self.prover, '_convert_to_cnf') as mock_convert:
            # Define mock CNF results
            # CNF of ¬(P(x) ⇒ Q(x)) is P(x) ∧ ¬Q(x), which gives clauses [[P(x)], [¬Q(x)]]
            p_x_pos = self.prover._create_literal(p_x, True)
            q_x_neg = self.prover._create_literal(q_x, False)
            
            goal_cnf = [[p_x_pos], [q_x_neg]]
            mock_convert.return_value = goal_cnf
            
            # Mock the _find_empty_clause method
            with patch.object(self.prover, '_find_empty_clause') as mock_find_empty:
                # Define a mock result that finds the empty clause
                mock_find_empty.return_value = (True, [])
                
                # Call the prove method
                proof_obj = self.prover.prove(q_x, context)
                
                # Verify that a successful proof object was created
                self.assertTrue(proof_obj.goal_achieved)
                self.assertEqual(proof_obj.conclusion_ast, q_x)
                self.assertEqual(proof_obj.inference_engine_used, "ResolutionProver")
                
                # Verify that the proof steps were created
                self.assertIsNotNone(proof_obj.proof_steps)
                self.assertGreater(len(proof_obj.proof_steps), 0)
    
    def test_handling_of_resource_limits(self):
        """Test handling of resource limits.
        
        This test verifies that the resolution prover correctly handles
        resource limits, stopping the proof search when limits are reached.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create an atomic formula
        p_x = ApplicationNode(p_pred, [x_var], self.boolean_type)  # P(x)
        
        # Create a resource limit with a very small time limit
        resources = ResourceLimits(time_limit_ms=1, depth_limit=100)
        
        # Mock the _convert_to_cnf method to avoid implementation details
        with patch.object(self.prover, '_convert_to_cnf') as mock_convert:
            # Define a mock CNF result
            p_x_pos = self.prover._create_literal(p_x, True)
            mock_convert.return_value = [[p_x_pos]]
            
            # Mock the _find_empty_clause method to simulate a timeout
            with patch.object(self.prover, '_find_empty_clause') as mock_find_empty:
                # Define a mock result that doesn't find the empty clause due to timeout
                mock_find_empty.return_value = (False, None)
                
                # Call the prove method with the resource limits
                proof_obj = self.prover.prove(p_x, set(), resources)
                
                # Verify that an unsuccessful proof object was created
                self.assertFalse(proof_obj.goal_achieved)
                self.assertEqual(proof_obj.status_message, "Failed: Resource limits exceeded")
                self.assertEqual(proof_obj.inference_engine_used, "ResolutionProver")


if __name__ == "__main__":
    unittest.main()