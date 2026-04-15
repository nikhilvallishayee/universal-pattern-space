"""
Unit tests for the ProofObject and ProofStepNode classes.

This module tests the functionality of the ProofObject and ProofStepNode classes
from the godelOS.inference_engine.proof_object module.
"""

import unittest
from unittest.mock import MagicMock, patch
import time
import logging

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode


class TestProofStepNode(unittest.TestCase):
    """Test cases for the ProofStepNode class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging for debugging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up TestProofStepNode tests")
        
        # Create mock AST_Node
        self.mock_formula = MagicMock(spec=AST_Node)
    
    def test_proof_step_node_creation(self):
        """Test creating a ProofStepNode."""
        self.logger.debug("Testing ProofStepNode creation")
        
        # Create a ProofStepNode
        node = ProofStepNode(
            formula=self.mock_formula,
            rule_name="TestRule",
            premises=[1, 2, 3],
            explanation="Test explanation"
        )
        
        # Verify attributes
        self.assertEqual(node.formula, self.mock_formula)
        self.assertEqual(node.rule_name, "TestRule")
        self.assertEqual(node.premises, [1, 2, 3])
        self.assertEqual(node.explanation, "Test explanation")
    
    def test_proof_step_node_immutability(self):
        """Test that ProofStepNode is immutable (frozen)."""
        self.logger.debug("Testing ProofStepNode immutability")
        
        # Create a ProofStepNode
        node = ProofStepNode(
            formula=self.mock_formula,
            rule_name="TestRule",
            premises=[1, 2]
        )
        
        # Attempt to modify attributes (should raise AttributeError)
        with self.assertRaises(AttributeError):
            node.formula = MagicMock(spec=AST_Node)
        
        with self.assertRaises(AttributeError):
            node.rule_name = "NewRule"
        
        with self.assertRaises(AttributeError):
            node.premises = [3, 4]
        
        with self.assertRaises(AttributeError):
            node.explanation = "New explanation"


class TestProofObject(unittest.TestCase):
    """Test cases for the ProofObject class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging for debugging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up TestProofObject tests")
        
        # Create mock AST_Node and VariableNode
        self.mock_conclusion = MagicMock(spec=AST_Node)
        self.mock_variable = MagicMock(spec=VariableNode)
        self.mock_value = MagicMock(spec=AST_Node)
        self.mock_axiom = MagicMock(spec=AST_Node)
        
        # Create mock bindings
        self.mock_bindings = {self.mock_variable: self.mock_value}
        
        # Create mock proof steps
        self.mock_formula = MagicMock(spec=AST_Node)
        self.proof_step = ProofStepNode(
            formula=self.mock_formula,
            rule_name="TestRule",
            premises=[],
            explanation="Test step"
        )
        self.proof_steps = [self.proof_step]
        
        # Create mock used axioms
        self.used_axioms = {self.mock_axiom}
        
        # Create resources consumed
        self.resources_consumed = {"depth": 5, "nodes_explored": 100}
    
    def test_proof_object_creation(self):
        """Test creating a ProofObject directly."""
        self.logger.debug("Testing ProofObject creation")
        
        # Create a ProofObject
        proof = ProofObject(
            goal_achieved=True,
            conclusion_ast=self.mock_conclusion,
            bindings=self.mock_bindings,
            status_message="Test status",
            proof_steps=self.proof_steps,
            used_axioms_rules=self.used_axioms,
            inference_engine_used="TestEngine",
            time_taken_ms=100.0,
            resources_consumed=self.resources_consumed
        )
        
        # Verify attributes
        self.assertTrue(proof.goal_achieved)
        self.assertEqual(proof.conclusion_ast, self.mock_conclusion)
        self.assertEqual(proof.bindings, self.mock_bindings)
        self.assertEqual(proof.status_message, "Test status")
        self.assertEqual(proof.proof_steps, self.proof_steps)
        self.assertEqual(proof.used_axioms_rules, self.used_axioms)
        self.assertEqual(proof.inference_engine_used, "TestEngine")
        self.assertEqual(proof.time_taken_ms, 100.0)
        self.assertEqual(proof.resources_consumed, self.resources_consumed)
    
    def test_create_success(self):
        """Test creating a successful ProofObject using the factory method."""
        self.logger.debug("Testing ProofObject.create_success")
        
        # Create a successful ProofObject
        proof = ProofObject.create_success(
            conclusion_ast=self.mock_conclusion,
            bindings=self.mock_bindings,
            proof_steps=self.proof_steps,
            used_axioms_rules=self.used_axioms,
            inference_engine_used="TestEngine",
            time_taken_ms=100.0,
            resources_consumed=self.resources_consumed
        )
        
        # Verify attributes
        self.assertTrue(proof.goal_achieved)
        self.assertEqual(proof.conclusion_ast, self.mock_conclusion)
        self.assertEqual(proof.bindings, self.mock_bindings)
        self.assertEqual(proof.status_message, "Proved")
        self.assertEqual(proof.proof_steps, self.proof_steps)
        self.assertEqual(proof.used_axioms_rules, self.used_axioms)
        self.assertEqual(proof.inference_engine_used, "TestEngine")
        self.assertEqual(proof.time_taken_ms, 100.0)
        self.assertEqual(proof.resources_consumed, self.resources_consumed)
    
    def test_create_failure(self):
        """Test creating a failed ProofObject using the factory method."""
        self.logger.debug("Testing ProofObject.create_failure")
        
        # Create a failed ProofObject
        proof = ProofObject.create_failure(
            status_message="Failed: Test reason",
            inference_engine_used="TestEngine",
            time_taken_ms=50.0,
            resources_consumed=self.resources_consumed
        )
        
        # Verify attributes
        self.assertFalse(proof.goal_achieved)
        self.assertIsNone(proof.conclusion_ast)
        self.assertIsNone(proof.bindings)
        self.assertEqual(proof.status_message, "Failed: Test reason")
        self.assertEqual(proof.proof_steps, [])
        self.assertEqual(proof.used_axioms_rules, set())
        self.assertEqual(proof.inference_engine_used, "TestEngine")
        self.assertEqual(proof.time_taken_ms, 50.0)
        self.assertEqual(proof.resources_consumed, self.resources_consumed)
    
    def test_with_time_and_resources(self):
        """Test updating time and resources using with_time_and_resources method."""
        self.logger.debug("Testing ProofObject.with_time_and_resources")
        
        # Create a ProofObject
        original_proof = ProofObject.create_success(
            conclusion_ast=self.mock_conclusion,
            inference_engine_used="TestEngine",
            time_taken_ms=100.0,
            resources_consumed={"depth": 5}
        )
        
        # Update time and resources
        new_time = 200.0
        new_resources = {"depth": 10, "nodes_explored": 200}
        updated_proof = original_proof.with_time_and_resources(new_time, new_resources)
        
        # Verify original proof is unchanged
        self.assertEqual(original_proof.time_taken_ms, 100.0)
        self.assertEqual(original_proof.resources_consumed, {"depth": 5})
        
        # Verify updated proof has new values
        self.assertEqual(updated_proof.time_taken_ms, new_time)
        self.assertEqual(updated_proof.resources_consumed, new_resources)
        
        # Verify other attributes remain the same
        self.assertEqual(updated_proof.goal_achieved, original_proof.goal_achieved)
        self.assertEqual(updated_proof.conclusion_ast, original_proof.conclusion_ast)
        self.assertEqual(updated_proof.status_message, original_proof.status_message)
    
    def test_proof_object_immutability(self):
        """Test that ProofObject is immutable (frozen)."""
        self.logger.debug("Testing ProofObject immutability")
        
        # Create a ProofObject
        proof = ProofObject.create_success(
            conclusion_ast=self.mock_conclusion,
            inference_engine_used="TestEngine"
        )
        
        # Attempt to modify attributes (should raise AttributeError)
        with self.assertRaises(AttributeError):
            proof.goal_achieved = False
        
        with self.assertRaises(AttributeError):
            proof.conclusion_ast = MagicMock(spec=AST_Node)
        
        with self.assertRaises(AttributeError):
            proof.status_message = "New status"
        
        with self.assertRaises(AttributeError):
            proof.time_taken_ms = 500.0


if __name__ == '__main__':
    unittest.main()