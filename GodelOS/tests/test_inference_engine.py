"""
Unit tests for the Inference Engine Architecture.

This module contains unit tests for the Inference Engine Architecture components,
including the ProofObject data structure and the InferenceCoordinator.
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional, Set

from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.types import AtomicType
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.coordinator import InferenceCoordinator, StrategyKnowledgeBase


class TestProofObject(unittest.TestCase):
    """Tests for the ProofObject data structure."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple type for testing
        self.bool_type = AtomicType("Boolean")
        
        # Create a simple constant node for testing
        self.true_const = ConstantNode("true", self.bool_type, True)
        
        # Create a simple variable node for testing
        self.var_x = VariableNode("?x", 1, self.bool_type)
    
    def test_create_success(self):
        """Test creating a successful proof object."""
        proof_obj = ProofObject.create_success(
            conclusion_ast=self.true_const,
            bindings={self.var_x: self.true_const},
            proof_steps=[],
            used_axioms_rules=set(),
            inference_engine_used="TestProver",
            time_taken_ms=100.0,
            resources_consumed={"depth": 5}
        )
        
        self.assertTrue(proof_obj.goal_achieved)
        self.assertEqual(proof_obj.conclusion_ast, self.true_const)
        self.assertEqual(proof_obj.bindings, {self.var_x: self.true_const})
        self.assertEqual(proof_obj.status_message, "Proved")
        self.assertEqual(proof_obj.inference_engine_used, "TestProver")
        self.assertEqual(proof_obj.time_taken_ms, 100.0)
        self.assertEqual(proof_obj.resources_consumed, {"depth": 5})
    
    def test_create_failure(self):
        """Test creating a failed proof object."""
        proof_obj = ProofObject.create_failure(
            status_message="Failed: Timeout",
            inference_engine_used="TestProver",
            time_taken_ms=200.0,
            resources_consumed={"depth": 10}
        )
        
        self.assertFalse(proof_obj.goal_achieved)
        self.assertIsNone(proof_obj.conclusion_ast)
        self.assertIsNone(proof_obj.bindings)
        self.assertEqual(proof_obj.status_message, "Failed: Timeout")
        self.assertEqual(proof_obj.inference_engine_used, "TestProver")
        self.assertEqual(proof_obj.time_taken_ms, 200.0)
        self.assertEqual(proof_obj.resources_consumed, {"depth": 10})
    
    def test_with_time_and_resources(self):
        """Test updating a proof object with new time and resource information."""
        proof_obj = ProofObject.create_success(
            conclusion_ast=self.true_const,
            inference_engine_used="TestProver"
        )
        
        updated_proof_obj = proof_obj.with_time_and_resources(
            time_taken_ms=150.0,
            resources_consumed={"depth": 7, "nodes": 100}
        )
        
        self.assertTrue(updated_proof_obj.goal_achieved)
        self.assertEqual(updated_proof_obj.conclusion_ast, self.true_const)
        self.assertEqual(updated_proof_obj.inference_engine_used, "TestProver")
        self.assertEqual(updated_proof_obj.time_taken_ms, 150.0)
        self.assertEqual(updated_proof_obj.resources_consumed, {"depth": 7, "nodes": 100})


class MockProver(BaseProver):
    """A mock prover for testing the InferenceCoordinator."""
    
    def __init__(self, name: str, can_handle_result: bool = True, prove_result: Optional[ProofObject] = None):
        """
        Initialize the mock prover.
        
        Args:
            name: The name of this prover
            can_handle_result: The result to return from can_handle
            prove_result: The result to return from prove
        """
        self._name = name
        self._can_handle_result = can_handle_result
        self._prove_result = prove_result
    
    @property
    def name(self) -> str:
        """Get the name of this prover."""
        return self._name
    
    def can_handle(self, goal_ast: AST_Node, context_asts: Set[AST_Node]) -> bool:
        """
        Determine if this prover can handle the given goal and context.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            
        Returns:
            The predetermined result
        """
        return self._can_handle_result
    
    def prove(self, goal_ast: AST_Node, context_asts: Set[AST_Node], 
             resources: Optional[ResourceLimits] = None) -> ProofObject:
        """
        Attempt to prove a goal.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            resources: Optional resource limits for the proof attempt
            
        Returns:
            The predetermined result
        """
        if self._prove_result is not None:
            return self._prove_result
        
        # Default to a successful proof
        return ProofObject.create_success(
            conclusion_ast=goal_ast,
            inference_engine_used=self._name,
            time_taken_ms=10.0,
            resources_consumed={"depth": 3}
        )


class TestInferenceCoordinator(unittest.TestCase):
    """Tests for the InferenceCoordinator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock KnowledgeStoreInterface
        self.ksi_mock = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create a simple type for testing
        self.bool_type = AtomicType("Boolean")
        
        # Create a simple constant node for testing
        self.true_const = ConstantNode("true", self.bool_type, True)
        
        # Create a simple goal for testing
        self.goal_ast = ApplicationNode(
            operator=ConstantNode("Prove", self.bool_type),
            arguments=[self.true_const],
            type_ref=self.bool_type
        )
        
        # Create mock provers
        self.prover1 = MockProver("Prover1", can_handle_result=True)
        self.prover2 = MockProver("Prover2", can_handle_result=False)
        
        # Create a strategy knowledge base
        self.strategy_kb = StrategyKnowledgeBase()
        self.strategy_kb.add_strategy_rule(
            "test_rule",
            lambda goal, _: True,  # Always applies
            "Prover1",
            priority=10
        )
        
        # Create the inference coordinator
        self.coordinator = InferenceCoordinator(
            kr_system_interface=self.ksi_mock,
            provers_map={"Prover1": self.prover1, "Prover2": self.prover2},
            strategy_kb=self.strategy_kb
        )
    
    def test_submit_goal_with_suitable_prover(self):
        """Test submitting a goal when a suitable prover is available."""
        result = self.coordinator.submit_goal(
            goal_ast=self.goal_ast,
            context_ast_set=set(),
            strategy_hint=None,
            resources=ResourceLimits(time_limit_ms=1000)
        )
        
        self.assertTrue(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "Prover1")
    
    def test_submit_goal_with_strategy_hint(self):
        """Test submitting a goal with a strategy hint."""
        result = self.coordinator.submit_goal(
            goal_ast=self.goal_ast,
            context_ast_set=set(),
            strategy_hint="Prover1",
            resources=ResourceLimits(time_limit_ms=1000)
        )
        
        self.assertTrue(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "Prover1")
    
    def test_submit_goal_with_no_suitable_prover(self):
        """Test submitting a goal when no suitable prover is available."""
        # Create a coordinator with only Prover2, which can't handle the goal
        coordinator = InferenceCoordinator(
            kr_system_interface=self.ksi_mock,
            provers_map={"Prover2": self.prover2},
            strategy_kb=self.strategy_kb
        )
        
        result = coordinator.submit_goal(
            goal_ast=self.goal_ast,
            context_ast_set=set(),
            strategy_hint=None,
            resources=ResourceLimits(time_limit_ms=1000)
        )
        
        self.assertFalse(result.goal_achieved)
        self.assertEqual(result.status_message, "No suitable prover found or strategy failed.")
    
    def test_submit_goal_with_prover_error(self):
        """Test submitting a goal when the prover raises an error."""
        # Create a prover that raises an exception
        error_prover = MockProver("ErrorProver", can_handle_result=True)
        error_prover.prove = MagicMock(side_effect=Exception("Test error"))
        
        # Create a coordinator with the error prover
        coordinator = InferenceCoordinator(
            kr_system_interface=self.ksi_mock,
            provers_map={"ErrorProver": error_prover},
            strategy_kb=self.strategy_kb
        )
        
        result = coordinator.submit_goal(
            goal_ast=self.goal_ast,
            context_ast_set=set(),
            strategy_hint="ErrorProver",
            resources=ResourceLimits(time_limit_ms=1000)
        )
        
        self.assertFalse(result.goal_achieved)
        self.assertEqual(result.status_message, "Error: Test error")
        self.assertEqual(result.inference_engine_used, "ErrorProver")


if __name__ == '__main__':
    unittest.main()