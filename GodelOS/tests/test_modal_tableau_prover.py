"""
Unit tests for the Modal Tableau Prover.

This module contains unit tests for the ModalTableauProver class, which implements
the tableau method for modal logics (e.g., K, T, D, B, S4, S5).
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional, Set

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode, ConnectiveNode, ModalOpNode
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.types import AtomicType
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.inference_engine.base_prover import ResourceLimits
from godelOS.inference_engine.modal_tableau_prover import (
    ModalTableauProver, ModalSystem, FormulaType, SignedFormula, World, Branch, Tableau,
    AccessibilityRelation, TableauRuleApplicator
)


class TestModalTableauProver(unittest.TestCase):
    """Tests for the ModalTableauProver class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock KnowledgeStoreInterface
        self.kr_system_interface = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create a mock TypeSystemManager
        self.type_system = MagicMock(spec=TypeSystemManager)
        
        # Create a ModalTableauProver
        self.prover = ModalTableauProver(
            self.kr_system_interface,
            self.type_system
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
        """Test the capabilities of the ModalTableauProver."""
        capabilities = self.prover.capabilities
        
        self.assertTrue(capabilities["modal_logic"])
        self.assertTrue(capabilities["propositional_logic"])
        self.assertTrue(capabilities["first_order_logic"])
        self.assertFalse(capabilities["higher_order_logic"])
        self.assertFalse(capabilities["arithmetic"])
        self.assertFalse(capabilities["constraint_solving"])
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Create a modal formula: □P
        box_p = ModalOpNode("NECESSARY", self.p_pred, self.bool_type)
        
        # Create a simple context: {Q}
        context = {self.q_pred}
        
        # Mock the coordinator methods
        with patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_modal_operator', return_value=True):
            # The prover should be able to handle this goal and context
            self.assertTrue(self.prover.can_handle(box_p, context))
    
    def test_cannot_handle_non_modal(self):
        """Test the can_handle method with non-modal operators."""
        # Create a simple goal: P
        goal = self.p_pred
        
        # Create a simple context: {Q}
        context = {self.q_pred}
        
        # Mock the coordinator methods
        with patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_modal_operator', return_value=False):
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
        
        # Test negating a negation: ¬¬P -> P
        double_negation = ConnectiveNode("NOT", [ConnectiveNode("NOT", [self.p_pred], self.bool_type)], self.bool_type)
        result = self.prover._negate_formula(double_negation)
        self.assertEqual(str(result), str(self.p_pred))
    
    def test_create_initial_tableau_validity(self):
        """Test creating an initial tableau for validity checking."""
        # Create a simple formula: P
        formula = self.p_pred
        
        # Create an empty context
        context = set()
        
        # Create the initial tableau for validity checking
        tableau = self.prover._create_initial_tableau(formula, context, True)
        
        # Check that the tableau has one branch
        self.assertEqual(len(tableau.branches), 1)
        
        # Check that the branch has one world
        branch = tableau.branches[0]
        self.assertEqual(len(branch.worlds), 1)
        
        # Check that the world has the negated formula
        world = branch.worlds[0]
        expected_formula = SignedFormula(ConnectiveNode("NOT", [self.p_pred], self.bool_type), True)
        self.assertTrue(any(str(f) == str(expected_formula) for f in world.formulas))
    
    def test_create_initial_tableau_satisfiability(self):
        """Test creating an initial tableau for satisfiability checking."""
        # Create a simple formula: P
        formula = self.p_pred
        
        # Create an empty context
        context = set()
        
        # Create the initial tableau for satisfiability checking
        tableau = self.prover._create_initial_tableau(formula, context, False)
        
        # Check that the tableau has one branch
        self.assertEqual(len(tableau.branches), 1)
        
        # Check that the branch has one world
        branch = tableau.branches[0]
        self.assertEqual(len(branch.worlds), 1)
        
        # Check that the world has the formula
        world = branch.worlds[0]
        expected_formula = SignedFormula(self.p_pred, True)
        self.assertTrue(any(str(f) == str(expected_formula) for f in world.formulas))
    
    def test_signed_formula(self):
        """Test the SignedFormula class."""
        # Create a signed formula: T: P
        formula = SignedFormula(self.p_pred, True)
        
        # Check the string representation
        self.assertEqual(str(formula), "T: P")
        
        # Check negation
        negated = formula.negate()
        self.assertEqual(str(negated), "F: P")
    
    def test_world_contains_contradiction(self):
        """Test checking if a world contains a contradiction."""
        # Create a world
        world = World(0)
        
        # Add a formula: T: P
        formula = SignedFormula(self.p_pred, True)
        world.add_formula(formula)
        
        # Check that the world doesn't contain a contradiction
        self.assertFalse(world.contains_contradiction())
        
        # Add the negation: F: P
        negated = formula.negate()
        world.add_formula(negated)
        
        # Check that the world now contains a contradiction
        self.assertTrue(world.contains_contradiction())
    
    def test_branch_is_closed(self):
        """Test checking if a branch is closed."""
        # Create a branch
        branch = Branch()
        
        # Add a world
        world = World(0)
        branch.add_world(world)
        
        # Check that the branch is not closed
        self.assertFalse(branch.is_closed())
        
        # Add a contradiction to the world
        formula = SignedFormula(self.p_pred, True)
        world.add_formula(formula)
        world.add_formula(formula.negate())
        
        # Check that the branch is now closed
        self.assertTrue(branch.is_closed())
    
    def test_tableau_is_closed(self):
        """Test checking if a tableau is closed."""
        # Create a tableau
        tableau = Tableau()
        
        # Add a branch
        branch1 = Branch()
        world1 = World(0)
        branch1.add_world(world1)
        tableau.add_branch(branch1)
        
        # Add another branch
        branch2 = Branch()
        world2 = World(1)
        branch2.add_world(world2)
        tableau.add_branch(branch2)
        
        # Check that the tableau is not closed
        self.assertFalse(tableau.is_closed())
        
        # Add a contradiction to the first world
        formula = SignedFormula(self.p_pred, True)
        world1.add_formula(formula)
        world1.add_formula(formula.negate())
        
        # Check that the tableau is still not closed
        self.assertFalse(tableau.is_closed())
        
        # Add a contradiction to the second world
        world2.add_formula(formula)
        world2.add_formula(formula.negate())
        
        # Check that the tableau is now closed
        self.assertTrue(tableau.is_closed())
    
    def test_formula_type_classification(self):
        """Test classifying formulas by type."""
        rule_applicator = TableauRuleApplicator(ModalSystem.K)
        
        # Test alpha formulas
        # T: A ∧ B
        and_formula = ConnectiveNode("AND", [self.p_pred, self.q_pred], self.bool_type)
        signed_and = SignedFormula(and_formula, True)
        self.assertEqual(rule_applicator.get_formula_type(signed_and), FormulaType.ALPHA)
        
        # F: A ∨ B
        or_formula = ConnectiveNode("OR", [self.p_pred, self.q_pred], self.bool_type)
        signed_or = SignedFormula(or_formula, False)
        self.assertEqual(rule_applicator.get_formula_type(signed_or), FormulaType.ALPHA)
        
        # Test beta formulas
        # T: A ∨ B
        signed_or = SignedFormula(or_formula, True)
        self.assertEqual(rule_applicator.get_formula_type(signed_or), FormulaType.BETA)
        
        # F: A ∧ B
        signed_and = SignedFormula(and_formula, False)
        self.assertEqual(rule_applicator.get_formula_type(signed_and), FormulaType.BETA)
        
        # Test pi formulas
        # T: □A
        box_formula = ModalOpNode("NECESSARY", self.p_pred, self.bool_type)
        signed_box = SignedFormula(box_formula, True)
        self.assertEqual(rule_applicator.get_formula_type(signed_box), FormulaType.PI)
        
        # Test nu formulas
        # T: ◇A
        diamond_formula = ModalOpNode("POSSIBLE", self.p_pred, self.bool_type)
        signed_diamond = SignedFormula(diamond_formula, True)
        self.assertEqual(rule_applicator.get_formula_type(signed_diamond), FormulaType.NU)
    
    def test_simple_proof_validity(self):
        """Test a simple validity proof."""
        # Create a simple formula: P → P
        implication = ConnectiveNode(
            "IMPLIES",
            [self.p_pred, self.p_pred],
            self.bool_type
        )
        
        # Create an empty context
        context = set()
        
        # The formula should be valid
        result = self.prover.prove(implication, context, modal_system_name="K", check_validity=True)
        
        self.assertTrue(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "ModalTableauProver")
    
    def test_simple_proof_satisfiability(self):
        """Test a simple satisfiability proof."""
        # Create a simple formula: P ∧ ¬P
        contradiction = ConnectiveNode(
            "AND",
            [
                self.p_pred,
                ConnectiveNode("NOT", [self.p_pred], self.bool_type)
            ],
            self.bool_type
        )
        
        # Create an empty context
        context = set()
        
        # The formula should be unsatisfiable
        result = self.prover.prove(contradiction, context, modal_system_name="K", check_validity=False)
        
        self.assertFalse(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "ModalTableauProver")
    
    def test_modal_system_properties(self):
        """Test that different modal systems have the expected properties."""
        # Create a modal formula: □P → P (should be valid in T, B, S4, S5, but not in K)
        box_p = ModalOpNode("NECESSARY", self.p_pred, self.bool_type)
        implication = ConnectiveNode(
            "IMPLIES",
            [box_p, self.p_pred],
            self.bool_type
        )
        
        # Create an empty context
        context = set()
        
        # Test in system K (should be invalid)
        result_k = self.prover.prove(implication, context, modal_system_name="K", check_validity=True)
        self.assertFalse(result_k.goal_achieved)
        
        # Test in system T (should be valid due to reflexivity)
        result_t = self.prover.prove(implication, context, modal_system_name="T", check_validity=True)
        self.assertTrue(result_t.goal_achieved)
        
        # Create another modal formula: P → □◇P (should be valid in B, S5, but not in K, T, S4)
        diamond_p = ModalOpNode("POSSIBLE", self.p_pred, self.bool_type)
        box_diamond_p = ModalOpNode("NECESSARY", diamond_p, self.bool_type)
        implication2 = ConnectiveNode(
            "IMPLIES",
            [self.p_pred, box_diamond_p],
            self.bool_type
        )
        
        # Test in system K (should be invalid)
        result_k2 = self.prover.prove(implication2, context, modal_system_name="K", check_validity=True)
        self.assertFalse(result_k2.goal_achieved)
        
        # Test in system B (should be valid due to symmetry)
        result_b = self.prover.prove(implication2, context, modal_system_name="B", check_validity=True)
        self.assertTrue(result_b.goal_achieved)


if __name__ == '__main__':
    unittest.main()