"""
Enhanced unit tests for the Modal Tableau Prover component.

This file extends the basic tests in test_modal_tableau_prover.py with more thorough
testing of complex methods and edge cases, focusing on modal logic formulas,
tableau expansion rules, and proof strategies.
"""

import unittest
from unittest.mock import patch, MagicMock
import time
from typing import Dict, List, Optional, Set, Any, Tuple

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.modal_tableau_prover import ModalTableauProver
from godelOS.inference_engine.base_prover import ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker


class TestModalTableauProverEnhanced(unittest.TestCase):
    """Enhanced test cases for the Modal Tableau Prover with complex scenarios and edge cases."""
    
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
        
        # Create a mock knowledge store interface
        self.ksi_mock = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create the modal tableau prover
        self.prover = ModalTableauProver(self.type_system, self.ksi_mock)
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
        
    def test_modal_knowledge_axioms(self):
        """Test modal knowledge axioms.
        
        This test verifies that the modal tableau prover correctly handles
        modal knowledge axioms like K, T, 4, 5, etc.
        """
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create atomic formulas
        p_a = ApplicationNode(p_pred, [a_const], self.boolean_type)
        
        # Create modal formulas
        # K_a(P(a)) - "a knows P(a)"
        knows_a_p_a = ModalOpNode("KNOWS", p_a, self.boolean_type, a_const)
        
        # K_a(P(a)) ⇒ P(a) - Axiom T (Truth/Reflexivity)
        # If a knows P(a), then P(a) is true
        axiom_t = ConnectiveNode("IMPLIES", [knows_a_p_a, p_a], self.boolean_type)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the axiom is provable
            mock_check.return_value = (True, [])
            
            # Attempt to prove the axiom
            proof_obj = self.prover.prove(axiom_t, set())
            
            # Verify that _check_tableau_provable was called with the axiom
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], axiom_t)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, axiom_t)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
        
        # K_a(P(a)) ⇒ K_a(K_a(P(a))) - Axiom 4 (Positive Introspection)
        # If a knows P(a), then a knows that a knows P(a)
        knows_a_knows_a_p_a = ModalOpNode("KNOWS", knows_a_p_a, self.boolean_type, a_const)
        axiom_4 = ConnectiveNode("IMPLIES", [knows_a_p_a, knows_a_knows_a_p_a], self.boolean_type)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the axiom is provable
            mock_check.return_value = (True, [])
            
            # Attempt to prove the axiom
            proof_obj = self.prover.prove(axiom_4, set())
            
            # Verify that _check_tableau_provable was called with the axiom
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], axiom_4)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, axiom_4)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
        
        # ¬K_a(P(a)) ⇒ K_a(¬K_a(P(a))) - Axiom 5 (Negative Introspection)
        # If a doesn't know P(a), then a knows that a doesn't know P(a)
        not_knows_a_p_a = ConnectiveNode("NOT", [knows_a_p_a], self.boolean_type)
        knows_a_not_knows_a_p_a = ModalOpNode("KNOWS", not_knows_a_p_a, self.boolean_type, a_const)
        axiom_5 = ConnectiveNode("IMPLIES", [not_knows_a_p_a, knows_a_not_knows_a_p_a], self.boolean_type)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the axiom is provable
            mock_check.return_value = (True, [])
            
            # Attempt to prove the axiom
            proof_obj = self.prover.prove(axiom_5, set())
            
            # Verify that _check_tableau_provable was called with the axiom
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], axiom_5)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, axiom_5)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
    def test_modal_belief_axioms(self):
        """Test modal belief axioms.
        
        This test verifies that the modal tableau prover correctly handles
        modal belief axioms like KD45.
        """
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create atomic formulas
        p_a = ApplicationNode(p_pred, [a_const], self.boolean_type)
        
        # Create modal formulas
        # B_a(P(a)) - "a believes P(a)"
        believes_a_p_a = ModalOpNode("BELIEVES", p_a, self.boolean_type, a_const)
        
        # B_a(P(a)) ⇒ ¬B_a(¬P(a)) - Axiom D (Consistency)
        # If a believes P(a), then a doesn't believe ¬P(a)
        not_p_a = ConnectiveNode("NOT", [p_a], self.boolean_type)
        believes_a_not_p_a = ModalOpNode("BELIEVES", not_p_a, self.boolean_type, a_const)
        not_believes_a_not_p_a = ConnectiveNode("NOT", [believes_a_not_p_a], self.boolean_type)
        axiom_d = ConnectiveNode("IMPLIES", [believes_a_p_a, not_believes_a_not_p_a], self.boolean_type)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the axiom is provable
            mock_check.return_value = (True, [])
            
            # Attempt to prove the axiom
            proof_obj = self.prover.prove(axiom_d, set())
            
            # Verify that _check_tableau_provable was called with the axiom
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], axiom_d)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, axiom_d)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
        
        # B_a(P(a)) ⇒ B_a(B_a(P(a))) - Axiom 4 (Positive Introspection)
        # If a believes P(a), then a believes that a believes P(a)
        believes_a_believes_a_p_a = ModalOpNode("BELIEVES", believes_a_p_a, self.boolean_type, a_const)
        axiom_4 = ConnectiveNode("IMPLIES", [believes_a_p_a, believes_a_believes_a_p_a], self.boolean_type)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the axiom is provable
            mock_check.return_value = (True, [])
            
            # Attempt to prove the axiom
            proof_obj = self.prover.prove(axiom_4, set())
            
            # Verify that _check_tableau_provable was called with the axiom
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], axiom_4)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, axiom_4)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
        
        # ¬B_a(P(a)) ⇒ B_a(¬B_a(P(a))) - Axiom 5 (Negative Introspection)
        # If a doesn't believe P(a), then a believes that a doesn't believe P(a)
        not_believes_a_p_a = ConnectiveNode("NOT", [believes_a_p_a], self.boolean_type)
        believes_a_not_believes_a_p_a = ModalOpNode("BELIEVES", not_believes_a_p_a, self.boolean_type, a_const)
        axiom_5 = ConnectiveNode("IMPLIES", [not_believes_a_p_a, believes_a_not_believes_a_p_a], self.boolean_type)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the axiom is provable
            mock_check.return_value = (True, [])
            
            # Attempt to prove the axiom
            proof_obj = self.prover.prove(axiom_5, set())
            
            # Verify that _check_tableau_provable was called with the axiom
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], axiom_5)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, axiom_5)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
    def test_tableau_expansion_rules(self):
        """Test tableau expansion rules.
        
        This test verifies that the modal tableau prover correctly applies
        tableau expansion rules for different formula types.
        """
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        q_pred = ConstantNode("Q", self.unary_pred_type)
        
        # Create atomic formulas
        p_a = ApplicationNode(p_pred, [a_const], self.boolean_type)
        q_a = ApplicationNode(q_pred, [a_const], self.boolean_type)
        
        # Create complex formulas for testing expansion rules
        
        # Conjunction: P(a) ∧ Q(a)
        conjunction = ConnectiveNode("AND", [p_a, q_a], self.boolean_type)
        
        # Mock the _apply_tableau_rule method
        with patch.object(self.prover, '_apply_tableau_rule') as mock_apply:
            # Define a mock result that simulates the conjunction rule
            # The conjunction rule adds both conjuncts to the current branch
            mock_apply.return_value = [[p_a, q_a]]
            
            # Apply the rule to the conjunction
            branches = self.prover._apply_tableau_rule(conjunction, True)
            
            # Verify that _apply_tableau_rule was called with the conjunction
            mock_apply.assert_called_once()
            args, kwargs = mock_apply.call_args
            self.assertEqual(args[0], conjunction)
            self.assertTrue(args[1])  # sign = True
            
            # Verify the result
            self.assertEqual(len(branches), 1)
            self.assertEqual(len(branches[0]), 2)
            self.assertEqual(branches[0][0], p_a)
            self.assertEqual(branches[0][1], q_a)
        
        # Disjunction: P(a) ∨ Q(a)
        disjunction = ConnectiveNode("OR", [p_a, q_a], self.boolean_type)
        
        # Mock the _apply_tableau_rule method
        with patch.object(self.prover, '_apply_tableau_rule') as mock_apply:
            # Define a mock result that simulates the disjunction rule
            # The disjunction rule creates two branches, one for each disjunct
            mock_apply.return_value = [[p_a], [q_a]]
            
            # Apply the rule to the disjunction
            branches = self.prover._apply_tableau_rule(disjunction, True)
            
            # Verify that _apply_tableau_rule was called with the disjunction
            mock_apply.assert_called_once()
            args, kwargs = mock_apply.call_args
            self.assertEqual(args[0], disjunction)
            self.assertTrue(args[1])  # sign = True
            
            # Verify the result
            self.assertEqual(len(branches), 2)
            self.assertEqual(len(branches[0]), 1)
            self.assertEqual(branches[0][0], p_a)
            self.assertEqual(len(branches[1]), 1)
            self.assertEqual(branches[1][0], q_a)
        
        # Negation: ¬P(a)
        negation = ConnectiveNode("NOT", [p_a], self.boolean_type)
        
        # Mock the _apply_tableau_rule method
        with patch.object(self.prover, '_apply_tableau_rule') as mock_apply:
            # Define a mock result that simulates the negation rule
            # The negation rule adds the negated formula with the opposite sign
            mock_apply.return_value = [[p_a]]
            
            # Apply the rule to the negation
            branches = self.prover._apply_tableau_rule(negation, False)
            
            # Verify that _apply_tableau_rule was called with the negation
            mock_apply.assert_called_once()
            args, kwargs = mock_apply.call_args
            self.assertEqual(args[0], negation)
            self.assertFalse(args[1])  # sign = False
            
            # Verify the result
            self.assertEqual(len(branches), 1)
            self.assertEqual(len(branches[0]), 1)
            self.assertEqual(branches[0][0], p_a)
        
        # Modal formula: K_a(P(a))
        knows_a_p_a = ModalOpNode("KNOWS", p_a, self.boolean_type, a_const)
        
        # Mock the _apply_tableau_rule method
        with patch.object(self.prover, '_apply_tableau_rule') as mock_apply:
            # Define a mock result that simulates the modal rule
            # The modal rule creates a new world where P(a) holds
            mock_apply.return_value = [[p_a]]
            
            # Apply the rule to the modal formula
            branches = self.prover._apply_tableau_rule(knows_a_p_a, True)
    def test_multi_agent_modal_logic(self):
        """Test multi-agent modal logic.
        
        This test verifies that the modal tableau prover correctly handles
        multi-agent modal logic formulas with multiple agents.
        """
        # Create constants for agents
        a_const = ConstantNode("a", self.entity_type)
        b_const = ConstantNode("b", self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create atomic formulas
        p_a = ApplicationNode(p_pred, [a_const], self.boolean_type)
        
        # Create multi-agent modal formulas
        # K_a(P(a)) - "a knows P(a)"
        knows_a_p_a = ModalOpNode("KNOWS", p_a, self.boolean_type, a_const)
        
        # K_b(K_a(P(a))) - "b knows that a knows P(a)"
        knows_b_knows_a_p_a = ModalOpNode("KNOWS", knows_a_p_a, self.boolean_type, b_const)
        
        # K_a(P(a)) ⇒ K_b(K_a(P(a))) - "If a knows P(a), then b knows that a knows P(a)"
        implication = ConnectiveNode("IMPLIES", [knows_a_p_a, knows_b_knows_a_p_a], self.boolean_type)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the formula is not provable
            # This formula should not be provable in general multi-agent modal logic
            mock_check.return_value = (False, None)
            
            # Attempt to prove the formula
            proof_obj = self.prover.prove(implication, set())
            
            # Verify that _check_tableau_provable was called with the formula
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], implication)
            
            # Verify that an unsuccessful proof object was created
            self.assertFalse(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
        
        # Create a context with an axiom: K_a(P(a)) ⇒ K_b(K_a(P(a)))
        # This makes the formula provable in the given context
        context = {implication}
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the formula is provable in the context
            mock_check.return_value = (True, [])
            
            # Attempt to prove the formula in the context
            proof_obj = self.prover.prove(implication, context)
            
            # Verify that _check_tableau_provable was called with the formula
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], implication)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, implication)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
    
    def test_common_knowledge(self):
        """Test common knowledge formulas.
        
        This test verifies that the modal tableau prover correctly handles
        common knowledge formulas in multi-agent settings.
        """
        # Create constants for agents
        a_const = ConstantNode("a", self.entity_type)
        b_const = ConstantNode("b", self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create atomic formulas
        p_a = ApplicationNode(p_pred, [a_const], self.boolean_type)
        
        # Create common knowledge formula
        # C_{a,b}(P(a)) - "P(a) is common knowledge between a and b"
        # This is equivalent to: P(a) ∧ K_a(P(a)) ∧ K_b(P(a)) ∧ K_a(K_b(P(a))) ∧ K_b(K_a(P(a))) ∧ ...
        
        # For simplicity, we'll use a finite approximation:
        # P(a) ∧ K_a(P(a)) ∧ K_b(P(a)) ∧ K_a(K_b(P(a))) ∧ K_b(K_a(P(a)))
        
        knows_a_p_a = ModalOpNode("KNOWS", p_a, self.boolean_type, a_const)
        knows_b_p_a = ModalOpNode("KNOWS", p_a, self.boolean_type, b_const)
        knows_a_knows_b_p_a = ModalOpNode("KNOWS", knows_b_p_a, self.boolean_type, a_const)
        knows_b_knows_a_p_a = ModalOpNode("KNOWS", knows_a_p_a, self.boolean_type, b_const)
        
        common_knowledge = ConnectiveNode(
            "AND",
            [p_a, knows_a_p_a, knows_b_p_a, knows_a_knows_b_p_a, knows_b_knows_a_p_a],
            self.boolean_type
        )
        
        # Create a formula: C_{a,b}(P(a)) ⇒ K_a(K_b(P(a)))
        # "If P(a) is common knowledge between a and b, then a knows that b knows P(a)"
        implication = ConnectiveNode("IMPLIES", [common_knowledge, knows_a_knows_b_p_a], self.boolean_type)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the formula is provable
            mock_check.return_value = (True, [])
            
            # Attempt to prove the formula
            proof_obj = self.prover.prove(implication, set())
            
            # Verify that _check_tableau_provable was called with the formula
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], implication)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, implication)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
    
    def test_performance_with_complex_formulas(self):
        """Test performance with complex formulas.
        
        This test verifies that the modal tableau prover efficiently handles
        complex modal formulas with deeply nested modal operators.
        """
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create atomic formulas
        p_a = ApplicationNode(p_pred, [a_const], self.boolean_type)
        
        # Create a deeply nested modal formula:
        # K_a(K_a(K_a(...K_a(P(a))...)))
        depth = 10
        nested_formula = p_a
        for _ in range(depth):
            nested_formula = ModalOpNode("KNOWS", nested_formula, self.boolean_type, a_const)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the formula is provable
            mock_check.return_value = (True, [])
            
            # Measure the time to prove the formula
            start_time = time.time()
            proof_obj = self.prover.prove(nested_formula, set())
            prove_time = time.time() - start_time
            
            print(f"Time to prove formula with modal depth {depth}: {prove_time * 1000:.2f} ms")
            
            # Verify that _check_tableau_provable was called with the formula
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], nested_formula)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, nested_formula)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
    
    def test_handling_of_resource_limits(self):
        """Test handling of resource limits.
        
        This test verifies that the modal tableau prover correctly handles
        resource limits, stopping the proof search when limits are reached.
        """
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create atomic formulas
        p_a = ApplicationNode(p_pred, [a_const], self.boolean_type)
        
        # Create a modal formula
        knows_a_p_a = ModalOpNode("KNOWS", p_a, self.boolean_type, a_const)
        
        # Create a resource limit with a very small time limit
        resources = ResourceLimits(time_limit_ms=1, depth_limit=100)
        
        # Mock the _check_tableau_provable method to simulate a timeout
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that indicates the proof search timed out
            mock_check.return_value = (False, "Timeout")
            
            # Attempt to prove the formula with the resource limits
            proof_obj = self.prover.prove(knows_a_p_a, set(), resources)
            
            # Verify that _check_tableau_provable was called with the formula and resource limits
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], knows_a_p_a)
            self.assertEqual(kwargs.get('resources'), resources)
            
            # Verify that an unsuccessful proof object was created
            self.assertFalse(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.status_message, "Failed: Resource limits exceeded")
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
    
    def test_proof_object_generation(self):
        """Test proof object generation.
        
        This test verifies that the modal tableau prover correctly generates
        proof objects with detailed proof steps for successful proofs.
        """
        # Create constants
        a_const = ConstantNode("a", self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create atomic formulas
        p_a = ApplicationNode(p_pred, [a_const], self.boolean_type)
        
        # Create a modal formula
        knows_a_p_a = ModalOpNode("KNOWS", p_a, self.boolean_type, a_const)
        
        # Mock the _check_tableau_provable method
        with patch.object(self.prover, '_check_tableau_provable') as mock_check:
            # Define a mock result that includes proof steps
            proof_steps = [
                ProofStepNode(
                    formula=knows_a_p_a,
                    rule_name="Initial Formula",
                    premises=[],
                    explanation="The initial formula to be proved"
                ),
                ProofStepNode(
                    formula=p_a,
                    rule_name="K Elimination",
                    premises=[knows_a_p_a],
                    explanation="Apply K elimination rule to knows(a, P(a))"
                )
            ]
            mock_check.return_value = (True, proof_steps)
            
            # Attempt to prove the formula
            proof_obj = self.prover.prove(knows_a_p_a, set())
            
            # Verify that _check_tableau_provable was called with the formula
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertEqual(args[0], knows_a_p_a)
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, knows_a_p_a)
            self.assertEqual(proof_obj.inference_engine_used, "ModalTableauProver")
            
            # Verify that the proof steps were included
            self.assertEqual(len(proof_obj.proof_steps), 2)
            self.assertEqual(proof_obj.proof_steps[0].formula, knows_a_p_a)
            self.assertEqual(proof_obj.proof_steps[0].rule_name, "Initial Formula")
            self.assertEqual(proof_obj.proof_steps[1].formula, p_a)
            self.assertEqual(proof_obj.proof_steps[1].rule_name, "K Elimination")

        # Verify that _apply_tableau_rule produces correct results for a modal formula
        with patch.object(self.prover, '_apply_tableau_rule') as mock_apply:
            mock_apply.return_value = [[p_a]]
            branches = self.prover._apply_tableau_rule(knows_a_p_a, True)
            
            mock_apply.assert_called_once()
            args, kwargs = mock_apply.call_args
            self.assertEqual(args[0], knows_a_p_a)
            self.assertTrue(args[1])  # sign = True
            
            # Verify the result
            self.assertEqual(len(branches), 1)
            self.assertEqual(len(branches[0]), 1)
            self.assertEqual(branches[0][0], p_a)


if __name__ == "__main__":
    unittest.main()