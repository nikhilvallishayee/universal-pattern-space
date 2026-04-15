"""
Unit tests for the Resolution Prover.

This module contains unit tests for the ResolutionProver class, which implements
the resolution inference rule for First-Order Logic (FOL) and propositional logic.
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional, Set

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode, ConnectiveNode, QuantifierNode
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.types import AtomicType
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.inference_engine.base_prover import ResourceLimits
from godelOS.inference_engine.resolution_prover import (
    ResolutionProver, CNFConverter, Clause, Literal, ResolutionStrategy
)


class TestCNFConverter(unittest.TestCase):
    """Tests for the CNFConverter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock UnificationEngine
        self.unification_engine = MagicMock(spec=UnificationEngine)
        
        # Create a CNF converter
        self.cnf_converter = CNFConverter(self.unification_engine)
        
        # Create types for testing
        self.bool_type = AtomicType("Boolean")
        self.entity_type = AtomicType("Entity")
        
        # Create constants and variables for testing
        self.true_const = ConstantNode("true", self.bool_type, True)
        self.false_const = ConstantNode("false", self.bool_type, False)
        self.a_const = ConstantNode("a", self.entity_type)
        self.b_const = ConstantNode("b", self.entity_type)
        self.x_var = VariableNode("x", 1, self.entity_type)
        self.y_var = VariableNode("y", 2, self.entity_type)
        
        # Create predicates for testing
        self.p_pred = ConstantNode("P", self.bool_type)
        self.q_pred = ConstantNode("Q", self.bool_type)
        self.r_pred = ConstantNode("R", self.bool_type)
    
    def test_eliminate_implications(self):
        """Test eliminating implications."""
        # Create A → B
        a_implies_b = ConnectiveNode(
            "IMPLIES",
            [self.p_pred, self.q_pred],
            self.bool_type
        )
        
        # Expected result: ¬A ∨ B
        expected = ConnectiveNode(
            "OR",
            [
                ConnectiveNode("NOT", [self.p_pred], self.bool_type),
                self.q_pred
            ],
            self.bool_type
        )
        
        result = self.cnf_converter._eliminate_implications(a_implies_b)
        self.assertEqual(str(result), str(expected))
    
    def test_eliminate_equivalences(self):
        """Test eliminating equivalences."""
        # Create A ↔ B
        a_equiv_b = ConnectiveNode(
            "EQUIV",
            [self.p_pred, self.q_pred],
            self.bool_type
        )
        
        # Expected result: (¬A ∨ B) ∧ (A ∨ ¬B)
        expected = ConnectiveNode(
            "AND",
            [
                ConnectiveNode(
                    "OR",
                    [
                        ConnectiveNode("NOT", [self.p_pred], self.bool_type),
                        self.q_pred
                    ],
                    self.bool_type
                ),
                ConnectiveNode(
                    "OR",
                    [
                        self.p_pred,
                        ConnectiveNode("NOT", [self.q_pred], self.bool_type)
                    ],
                    self.bool_type
                )
            ],
            self.bool_type
        )
        
        result = self.cnf_converter._eliminate_implications(a_equiv_b)
        self.assertEqual(str(result), str(expected))
    
    def test_move_negations_inward(self):
        """Test moving negations inward."""
        # Create ¬(A ∧ B)
        not_a_and_b = ConnectiveNode(
            "NOT",
            [
                ConnectiveNode(
                    "AND",
                    [self.p_pred, self.q_pred],
                    self.bool_type
                )
            ],
            self.bool_type
        )
        
        # Expected result: ¬A ∨ ¬B
        expected = ConnectiveNode(
            "OR",
            [
                ConnectiveNode("NOT", [self.p_pred], self.bool_type),
                ConnectiveNode("NOT", [self.q_pred], self.bool_type)
            ],
            self.bool_type
        )
        
        result = self.cnf_converter._move_negations_inward(not_a_and_b)
        self.assertEqual(str(result), str(expected))
    
    def test_extract_clauses(self):
        """Test extracting clauses from a CNF formula."""
        # Create (A ∨ B) ∧ (¬A ∨ C)
        cnf_formula = ConnectiveNode(
            "AND",
            [
                ConnectiveNode(
                    "OR",
                    [self.p_pred, self.q_pred],
                    self.bool_type
                ),
                ConnectiveNode(
                    "OR",
                    [
                        ConnectiveNode("NOT", [self.p_pred], self.bool_type),
                        self.r_pred
                    ],
                    self.bool_type
                )
            ],
            self.bool_type
        )
        
        clauses = self.cnf_converter._extract_clauses(cnf_formula)
        
        self.assertEqual(len(clauses), 2)
        
        # Check the first clause: A ∨ B
        self.assertEqual(len(clauses[0].literals), 2)
        literals = sorted([str(lit) for lit in clauses[0].literals])
        self.assertEqual(literals, ["P", "Q"])
        
        # Check the second clause: ¬A ∨ C
        self.assertEqual(len(clauses[1].literals), 2)
        literals = sorted([str(lit) for lit in clauses[1].literals])
        self.assertEqual(literals, ["R", "¬P"])


class TestResolutionProver(unittest.TestCase):
    """Tests for the ResolutionProver class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock KnowledgeStoreInterface
        self.kr_system_interface = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create a mock UnificationEngine
        self.unification_engine = MagicMock(spec=UnificationEngine)
        
        # Create a mock CNFConverter
        self.cnf_converter = MagicMock(spec=CNFConverter)
        
        # Create a ResolutionProver
        self.prover = ResolutionProver(
            self.kr_system_interface,
            self.unification_engine,
            self.cnf_converter
        )
        
        # Create types for testing
        self.bool_type = AtomicType("Boolean")
        self.entity_type = AtomicType("Entity")
        
        # Create constants and variables for testing
        self.true_const = ConstantNode("true", self.bool_type, True)
        self.false_const = ConstantNode("false", self.bool_type, False)
        self.a_const = ConstantNode("a", self.entity_type)
        self.b_const = ConstantNode("b", self.entity_type)
        self.x_var = VariableNode("x", 1, self.entity_type)
        self.y_var = VariableNode("y", 2, self.entity_type)
        
        # Create predicates for testing
        self.p_pred = ConstantNode("P", self.bool_type)
        self.q_pred = ConstantNode("Q", self.bool_type)
        self.r_pred = ConstantNode("R", self.bool_type)
    
    def test_capabilities(self):
        """Test the capabilities of the ResolutionProver."""
        capabilities = self.prover.capabilities
        
        self.assertTrue(capabilities["first_order_logic"])
        self.assertTrue(capabilities["propositional_logic"])
        self.assertTrue(capabilities["equality"])
        self.assertTrue(capabilities["uninterpreted_functions"])
        self.assertFalse(capabilities["modal_logic"])
        self.assertFalse(capabilities["higher_order_logic"])
        self.assertFalse(capabilities["arithmetic"])
        self.assertFalse(capabilities["constraint_solving"])
        self.assertFalse(capabilities["analogical_reasoning"])
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Create a simple goal: P
        goal = self.p_pred
        
        # Create a simple context: {Q}
        context = {self.q_pred}
        
        # Mock the coordinator methods
        with patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_modal_operator', return_value=False), \
             patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_arithmetic', return_value=False), \
             patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_constraints', return_value=False):
            
            # The prover should be able to handle this goal and context
            self.assertTrue(self.prover.can_handle(goal, context))
    
    def test_cannot_handle_modal(self):
        """Test the can_handle method with modal operators."""
        # Create a simple goal: P
        goal = self.p_pred
        
        # Create a simple context: {Q}
        context = {self.q_pred}
        
        # Mock the coordinator methods
        with patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_modal_operator', return_value=True), \
             patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_arithmetic', return_value=False), \
             patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_constraints', return_value=False):
            
            # The prover should not be able to handle this goal and context
            self.assertFalse(self.prover.can_handle(goal, context))
    
    def test_negate_formula(self):
        """Test negating a formula."""
        # Create a simple formula: P
        formula = self.p_pred
        
        # Expected result: ¬P
        expected = ConnectiveNode("NOT", [self.p_pred], self.bool_type)
        
        result = self.prover._negate_formula(formula)
        self.assertEqual(str(result), str(expected))
    
    def test_resolve_pair_simple(self):
        """Test resolving a pair of clauses."""
        # Create two clauses: {P} and {¬P}
        clause1 = Clause(frozenset([Literal(self.p_pred, False)]))
        clause2 = Clause(frozenset([Literal(self.p_pred, True)]))
        
        # Mock the unification engine to return a successful unification
        self.unification_engine.unify.return_value = ({}, [])
        
        # The resolution should produce the empty clause
        resolvents = self.prover._resolve_pair(clause1, clause2)
        
        self.assertEqual(len(resolvents), 1)
        self.assertTrue(resolvents[0].is_empty())
    
    def test_is_tautology(self):
        """Test checking if a clause is a tautology."""
        # Create a tautology: P ∨ ¬P
        tautology = Clause(frozenset([
            Literal(self.p_pred, False),
            Literal(self.p_pred, True)
        ]))
        
        # Mock the unification engine to return a successful unification
        self.unification_engine.unify.return_value = ({}, [])
        
        # The clause should be a tautology
        self.assertTrue(self.prover._is_tautology(tautology))
    
    def test_clauses_equivalent(self):
        """Test checking if two clauses are equivalent."""
        # Create two equivalent clauses: {P ∨ Q} and {P ∨ Q}
        clause1 = Clause(frozenset([
            Literal(self.p_pred, False),
            Literal(self.q_pred, False)
        ]))
        
        clause2 = Clause(frozenset([
            Literal(self.p_pred, False),
            Literal(self.q_pred, False)
        ]))
        
        # Mock the unification engine to return a successful unification
        self.unification_engine.unify.return_value = ({}, [])
        
        # The clauses should be equivalent
        self.assertTrue(self.prover._clauses_equivalent(clause1, clause2))
    
    def test_simple_proof(self):
        """Test a simple proof."""
        # Create a simple goal: P
        goal = self.p_pred
        
        # Create a simple context: {P}
        context = {self.p_pred}
        
        # Mock the CNF converter to return appropriate clauses
        self.cnf_converter.convert_to_cnf.side_effect = [
            # For the negated goal: ¬P
            [Clause(frozenset([Literal(self.p_pred, True)]))],
            # For the context: P
            [Clause(frozenset([Literal(self.p_pred, False)]))]
        ]
        
        # Mock the unification engine to return a successful unification
        self.unification_engine.unify.return_value = ({}, [])
        
        # The proof should succeed
        result = self.prover.prove(goal, context)
        
        self.assertTrue(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "ResolutionProver")


if __name__ == '__main__':
    unittest.main()