"""
Unit tests for the InferenceCoordinator and StrategyKnowledgeBase.

This module tests the functionality of the InferenceCoordinator and StrategyKnowledgeBase
classes from the godelOS.inference_engine.coordinator module.
"""

import unittest
from unittest.mock import MagicMock, patch, call
import logging
from typing import Dict, Optional, Set

from godelOS.core_kr.ast.nodes import (
    AST_Node, VariableNode, ConnectiveNode, QuantifierNode, 
    ModalOpNode, ApplicationNode
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject
from godelOS.inference_engine.coordinator import InferenceCoordinator, StrategyKnowledgeBase


# Create a concrete implementation of BaseProver for testing
class MockProver(BaseProver):
    """A mock implementation of BaseProver for testing purposes."""
    
    def __init__(self, name="MockProver", can_handle_result=True, proof_result=None):
        self._name = name
        self._can_handle_result = can_handle_result
        self._proof_result = proof_result
    
    def prove(self, goal_ast: AST_Node, context_asts: Set[AST_Node], 
             resources: Optional[ResourceLimits] = None) -> ProofObject:
        """Mock implementation of the prove method."""
        if self._proof_result:
            return self._proof_result
        
        # Default success proof object
        return ProofObject.create_success(
            conclusion_ast=goal_ast,
            inference_engine_used=self.name,
            time_taken_ms=100.0,
            resources_consumed={"test_resource": 1.0}
        )
    
    def can_handle(self, goal_ast: AST_Node, context_asts: Set[AST_Node]) -> bool:
        """Mock implementation of the can_handle method."""
        return self._can_handle_result
    
    @property
    def name(self) -> str:
        """Implementation of the name property."""
        return self._name
    
    @property
    def capabilities(self):
        """Override the capabilities property."""
        return {
            "first_order_logic": True,
            "propositional_logic": True
        }


class TestStrategyKnowledgeBase(unittest.TestCase):
    """Test cases for the StrategyKnowledgeBase class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging for debugging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up TestStrategyKnowledgeBase tests")
        
        # Create a StrategyKnowledgeBase
        self.strategy_kb = StrategyKnowledgeBase()
        
        # Create mock AST_Node
        self.mock_goal = MagicMock(spec=AST_Node)
        self.mock_context = {MagicMock(spec=AST_Node), MagicMock(spec=AST_Node)}
        
        # Create mock provers
        self.mock_provers = {
            "prover1": MockProver(name="prover1", can_handle_result=True),
            "prover2": MockProver(name="prover2", can_handle_result=True),
            "prover3": MockProver(name="prover3", can_handle_result=False)
        }
    
    def test_add_strategy_rule(self):
        """Test adding a strategy rule to the knowledge base."""
        self.logger.debug("Testing StrategyKnowledgeBase.add_strategy_rule")
        
        # Define a condition function
        def condition_fn(goal, context):
            return True
        
        # Add a rule
        self.strategy_kb.add_strategy_rule(
            rule_name="test_rule",
            condition_fn=condition_fn,
            prover_name="test_prover",
            priority=100
        )
        
        # Verify rule was added
        self.assertEqual(len(self.strategy_kb.strategy_rules), 1)
        rule = self.strategy_kb.strategy_rules[0]
        self.assertEqual(rule["name"], "test_rule")
        self.assertEqual(rule["condition"], condition_fn)
        self.assertEqual(rule["prover"], "test_prover")
        self.assertEqual(rule["priority"], 100)
    
    def test_rule_priority_sorting(self):
        """Test that rules are sorted by priority."""
        self.logger.debug("Testing rule priority sorting")
        
        # Add rules with different priorities
        self.strategy_kb.add_strategy_rule(
            rule_name="low_priority",
            condition_fn=lambda g, c: True,
            prover_name="prover1",
            priority=10
        )
        
        self.strategy_kb.add_strategy_rule(
            rule_name="high_priority",
            condition_fn=lambda g, c: True,
            prover_name="prover2",
            priority=100
        )
        
        self.strategy_kb.add_strategy_rule(
            rule_name="medium_priority",
            condition_fn=lambda g, c: True,
            prover_name="prover3",
            priority=50
        )
        
        # Verify rules are sorted by priority (descending)
        self.assertEqual(len(self.strategy_kb.strategy_rules), 3)
        self.assertEqual(self.strategy_kb.strategy_rules[0]["name"], "high_priority")
        self.assertEqual(self.strategy_kb.strategy_rules[1]["name"], "medium_priority")
        self.assertEqual(self.strategy_kb.strategy_rules[2]["name"], "low_priority")
    
    def test_select_prover_with_hint(self):
        """Test selecting a prover with a strategy hint."""
        self.logger.debug("Testing StrategyKnowledgeBase.select_prover with hint")
        
        # Select a prover with a valid hint
        selected = self.strategy_kb.select_prover(
            self.mock_goal,
            self.mock_context,
            self.mock_provers,
            strategy_hint="prover1"
        )
        
        # Verify the correct prover was selected
        self.assertEqual(selected, "prover1")
        
        # Create a new mock prover that can't handle the goal
        cant_handle_prover = MockProver(name="cant_handle", can_handle_result=False)
        provers_with_cant_handle = {
            "cant_handle": cant_handle_prover
        }
        
        # Select a prover with a hint for a prover that can't handle the goal
        selected = self.strategy_kb.select_prover(
            self.mock_goal,
            self.mock_context,
            provers_with_cant_handle,
            strategy_hint="cant_handle"
        )
        
        # Verify no prover was selected
        self.assertIsNone(selected)
        
        # Select a prover with a non-existent hint
        selected = self.strategy_kb.select_prover(
            self.mock_goal,
            self.mock_context,
            self.mock_provers,
            strategy_hint="non_existent"
        )
        
        # Verify fallback to rules
        self.assertIsNotNone(selected)
    
    def test_select_prover_with_rules(self):
        """Test selecting a prover using strategy rules."""
        self.logger.debug("Testing StrategyKnowledgeBase.select_prover with rules")
        
        # Add rules
        self.strategy_kb.add_strategy_rule(
            rule_name="rule1",
            condition_fn=lambda g, c: False,  # This rule won't match
            prover_name="prover1",
            priority=100
        )
        
        self.strategy_kb.add_strategy_rule(
            rule_name="rule2",
            condition_fn=lambda g, c: True,  # This rule will match
            prover_name="prover2",
            priority=50
        )
        
        # Select a prover
        selected = self.strategy_kb.select_prover(
            self.mock_goal,
            self.mock_context,
            self.mock_provers
        )
        
        # Verify the correct prover was selected
        self.assertEqual(selected, "prover2")
        
        # Add a rule for a prover that can't handle the goal
        self.strategy_kb.add_strategy_rule(
            rule_name="rule3",
            condition_fn=lambda g, c: True,  # This rule will match
            prover_name="prover3",  # But this prover can't handle the goal
            priority=200
        )
        
        # Select a prover
        selected = self.strategy_kb.select_prover(
            self.mock_goal,
            self.mock_context,
            self.mock_provers
        )
        
        # Verify the next matching prover was selected
        self.assertEqual(selected, "prover2")
    
    def test_select_prover_fallback(self):
        """Test fallback when no rule matches."""
        self.logger.debug("Testing StrategyKnowledgeBase.select_prover fallback")
        
        # Add a rule that won't match
        self.strategy_kb.add_strategy_rule(
            rule_name="non_matching",
            condition_fn=lambda g, c: False,
            prover_name="prover1",
            priority=100
        )
        
        # Select a prover
        selected = self.strategy_kb.select_prover(
            self.mock_goal,
            self.mock_context,
            self.mock_provers
        )
        
        # Verify a prover was selected as fallback
        self.assertIsNotNone(selected)
        self.assertIn(selected, ["prover1", "prover2"])  # Either one could be selected
        
        # Test with no matching provers
        no_handle_provers = {
            "prover1": MockProver(name="prover1", can_handle_result=False),
            "prover2": MockProver(name="prover2", can_handle_result=False)
        }
        
        selected = self.strategy_kb.select_prover(
            self.mock_goal,
            self.mock_context,
            no_handle_provers
        )
        
        # Verify no prover was selected
        self.assertIsNone(selected)


class TestInferenceCoordinator(unittest.TestCase):
    """Test cases for the InferenceCoordinator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging for debugging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up TestInferenceCoordinator tests")
        
        # Create mock KnowledgeStoreInterface
        self.mock_kr_interface = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create mock provers
        self.mock_resolution_prover = MockProver(name="resolution_prover")
        self.mock_modal_prover = MockProver(name="modal_tableau_prover")
        self.mock_smt_prover = MockProver(name="smt_interface")
        self.mock_clp_prover = MockProver(name="clp_module")
        
        self.provers_map = {
            "resolution_prover": self.mock_resolution_prover,
            "modal_tableau_prover": self.mock_modal_prover,
            "smt_interface": self.mock_smt_prover,
            "clp_module": self.mock_clp_prover
        }
        
        # Create mock AST_Node
        self.mock_goal = MagicMock(spec=AST_Node)
        self.mock_context = {MagicMock(spec=AST_Node), MagicMock(spec=AST_Node)}
        
        # Create InferenceCoordinator
        self.coordinator = InferenceCoordinator(
            kr_system_interface=self.mock_kr_interface,
            provers_map=self.provers_map
        )
    
    def test_initialization(self):
        """Test initialization of InferenceCoordinator."""
        self.logger.debug("Testing InferenceCoordinator initialization")
        
        # Verify attributes
        self.assertEqual(self.coordinator.kr_system_interface, self.mock_kr_interface)
        self.assertEqual(self.coordinator.provers, self.provers_map)
        self.assertIsNotNone(self.coordinator.strategy_kb)
        
        # Verify default strategy KB was created
        self.assertGreater(len(self.coordinator.strategy_kb.strategy_rules), 0)
    
    def test_create_default_strategy_kb(self):
        """Test creating a default strategy knowledge base."""
        self.logger.debug("Testing InferenceCoordinator._create_default_strategy_kb")
        
        # Create a default strategy KB
        kb = self.coordinator._create_default_strategy_kb()
        
        # Verify it's a StrategyKnowledgeBase
        self.assertIsInstance(kb, StrategyKnowledgeBase)
        
        # Verify it has rules
        self.assertGreater(len(kb.strategy_rules), 0)
        
        # Verify the rules are sorted by priority
        priorities = [rule["priority"] for rule in kb.strategy_rules]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
    
    def test_contains_modal_operator(self):
        """Test the _contains_modal_operator method."""
        self.logger.debug("Testing InferenceCoordinator._contains_modal_operator")
        
        # Create mock nodes
        mock_modal_op = MagicMock(spec=ModalOpNode)
        mock_connective = MagicMock(spec=ConnectiveNode)
        mock_connective.operands = [MagicMock(spec=AST_Node), mock_modal_op]
        
        # Test with a modal operator
        self.assertTrue(self.coordinator._contains_modal_operator(mock_modal_op))
        
        # Test with a connective containing a modal operator
        self.assertTrue(self.coordinator._contains_modal_operator(mock_connective))
        
        # Test with a non-modal node
        mock_non_modal = MagicMock(spec=AST_Node)
        self.assertFalse(self.coordinator._contains_modal_operator(mock_non_modal))
    
    def test_contains_arithmetic(self):
        """Test the _contains_arithmetic method."""
        self.logger.debug("Testing InferenceCoordinator._contains_arithmetic")
        
        # Create mock ApplicationNode with arithmetic operator
        mock_op = MagicMock(spec=AST_Node)
        mock_op.name = "+"
        mock_app = MagicMock(spec=ApplicationNode)
        mock_app.operator = mock_op
        mock_app.arguments = [MagicMock(spec=AST_Node), MagicMock(spec=AST_Node)]
        
        # Test with arithmetic operator
        self.assertTrue(self.coordinator._contains_arithmetic(mock_app))
        
        # Test with non-arithmetic operator
        mock_op.name = "non_arithmetic"
        self.assertFalse(self.coordinator._contains_arithmetic(mock_app))
    
    def test_contains_constraints(self):
        """Test the _contains_constraints method."""
        self.logger.debug("Testing InferenceCoordinator._contains_constraints")
        
        # Create mock ApplicationNode with constraint operator
        mock_op = MagicMock(spec=AST_Node)
        mock_op.name = "AllDifferent"
        mock_app = MagicMock(spec=ApplicationNode)
        mock_app.operator = mock_op
        mock_app.arguments = [MagicMock(spec=AST_Node), MagicMock(spec=AST_Node)]
        
        # Test with constraint operator
        self.assertTrue(self.coordinator._contains_constraints(mock_app))
        
        # Test with non-constraint operator
        mock_op.name = "non_constraint"
        self.assertFalse(self.coordinator._contains_constraints(mock_app))
    
    def test_submit_goal_success(self):
        """Test submitting a goal that succeeds."""
        self.logger.debug("Testing InferenceCoordinator.submit_goal success")
        
        # Create a mock strategy KB that always selects the resolution prover
        mock_strategy_kb = MagicMock(spec=StrategyKnowledgeBase)
        mock_strategy_kb.select_prover.return_value = "resolution_prover"
        self.coordinator.strategy_kb = mock_strategy_kb
        
        # Create a mock proof object
        mock_proof = ProofObject.create_success(
            conclusion_ast=self.mock_goal,
            inference_engine_used="resolution_prover",
            time_taken_ms=100.0,
            resources_consumed={"test_resource": 1.0}
        )
        self.mock_resolution_prover._proof_result = mock_proof
        
        # Submit a goal
        result = self.coordinator.submit_goal(self.mock_goal, self.mock_context)
        
        # Verify the result
        self.assertIsInstance(result, ProofObject)
        self.assertTrue(result.goal_achieved)
        self.assertEqual(result.conclusion_ast, self.mock_goal)
        self.assertEqual(result.inference_engine_used, "resolution_prover")
        
        # Verify the strategy KB was called
        mock_strategy_kb.select_prover.assert_called_once_with(
            self.mock_goal, self.mock_context, self.provers_map, None
        )
        
        # Verify the proof result
        self.assertTrue(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "resolution_prover")
    
    def test_submit_goal_failure(self):
        """Test submitting a goal that fails."""
        self.logger.debug("Testing InferenceCoordinator.submit_goal failure")
        
        # Create a mock strategy KB that always selects the resolution prover
        mock_strategy_kb = MagicMock(spec=StrategyKnowledgeBase)
        mock_strategy_kb.select_prover.return_value = "resolution_prover"
        self.coordinator.strategy_kb = mock_strategy_kb
        
        # Create a mock proof object for failure
        mock_proof = ProofObject.create_failure(
            status_message="Test failure",
            inference_engine_used="resolution_prover",
            time_taken_ms=100.0,
            resources_consumed={"test_resource": 1.0}
        )
        self.mock_resolution_prover._proof_result = mock_proof
        
        # Submit a goal
        result = self.coordinator.submit_goal(self.mock_goal, self.mock_context)
        
        # Verify the result
        self.assertIsInstance(result, ProofObject)
        self.assertFalse(result.goal_achieved)
        self.assertEqual(result.status_message, "Test failure")
        self.assertEqual(result.inference_engine_used, "resolution_prover")
    
    def test_submit_goal_no_prover(self):
        """Test submitting a goal when no prover is available."""
        self.logger.debug("Testing InferenceCoordinator.submit_goal no prover")
        
        # Create a mock strategy KB that returns None (no prover available)
        mock_strategy_kb = MagicMock(spec=StrategyKnowledgeBase)
        mock_strategy_kb.select_prover.return_value = None
        self.coordinator.strategy_kb = mock_strategy_kb
        
        # Submit a goal
        result = self.coordinator.submit_goal(self.mock_goal, self.mock_context)
        
        # Verify the result
        self.assertIsInstance(result, ProofObject)
        self.assertFalse(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "none")
        self.assertIn("No suitable prover", result.status_message)
    
    def test_submit_goal_exception(self):
        """Test submitting a goal that raises an exception."""
        self.logger.debug("Testing InferenceCoordinator.submit_goal exception")
        
        # Create a mock strategy KB that always selects the resolution prover
        mock_strategy_kb = MagicMock(spec=StrategyKnowledgeBase)
        mock_strategy_kb.select_prover.return_value = "resolution_prover"
        self.coordinator.strategy_kb = mock_strategy_kb
        
        # Create a mock prover that raises an exception
        exception_prover = MockProver(name="exception_prover")
        exception_prover.prove = MagicMock(side_effect=Exception("Test exception"))
        
        # Replace the provers map
        self.coordinator.provers = {"exception_prover": exception_prover}
        
        # Update the strategy KB to select the exception prover
        mock_strategy_kb = MagicMock(spec=StrategyKnowledgeBase)
        mock_strategy_kb.select_prover.return_value = "exception_prover"
        self.coordinator.strategy_kb = mock_strategy_kb
        
        # Submit a goal
        result = self.coordinator.submit_goal(self.mock_goal, self.mock_context)
        
        # Verify the result
        self.assertIsInstance(result, ProofObject)
        self.assertFalse(result.goal_achieved)
        self.assertIn("Error:", result.status_message)
        self.assertIn("Test exception", result.status_message)
        self.assertEqual(result.inference_engine_used, "exception_prover")


if __name__ == '__main__':
    unittest.main()