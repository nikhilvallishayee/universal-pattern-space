"""
Unit tests for the BaseProver abstract class and ResourceLimits.

This module tests the functionality of the ResourceLimits class and provides
a test implementation of BaseProver to verify its contract.
"""

import unittest
from unittest.mock import MagicMock, patch
import logging
from typing import Optional, Set

from godelOS.core_kr.ast.nodes import AST_Node
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject


# Create a concrete implementation of BaseProver for testing
class TestProverImplementation(BaseProver):
    """A concrete implementation of BaseProver for testing purposes."""
    
    def __init__(self, name="TestProver", capabilities=None):
        self._name = name
        self._capabilities = capabilities or {
            "first_order_logic": True,
            "propositional_logic": True
        }
    
    def prove(self, goal_ast: AST_Node, context_asts: Set[AST_Node], 
             resources: Optional[ResourceLimits] = None) -> ProofObject:
        """Implementation of the prove method for testing."""
        # Just return a success proof object
        return ProofObject.create_success(
            conclusion_ast=goal_ast,
            inference_engine_used=self.name,
            time_taken_ms=100.0,
            resources_consumed={"test_resource": 1.0}
        )
    
    def can_handle(self, goal_ast: AST_Node, context_asts: Set[AST_Node]) -> bool:
        """Implementation of the can_handle method for testing."""
        # This test implementation can handle all goals
        return True
    
    @property
    def name(self) -> str:
        """Implementation of the name property for testing."""
        return self._name
    
    @property
    def capabilities(self):
        """Override the capabilities property for testing."""
        return self._capabilities


class TestResourceLimits(unittest.TestCase):
    """Test cases for the ResourceLimits class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging for debugging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up TestResourceLimits tests")
    
    def test_resource_limits_creation(self):
        """Test creating ResourceLimits with various parameters."""
        self.logger.debug("Testing ResourceLimits creation")
        
        # Create with default values
        limits = ResourceLimits()
        self.assertIsNone(limits.time_limit_ms)
        self.assertIsNone(limits.depth_limit)
        self.assertIsNone(limits.memory_limit_mb)
        self.assertIsNone(limits.nodes_limit)
        self.assertEqual(limits.additional_limits, {})
        
        # Create with specific values
        limits = ResourceLimits(
            time_limit_ms=1000.0,
            depth_limit=10,
            memory_limit_mb=100.0,
            nodes_limit=1000,
            custom_limit=50
        )
        self.assertEqual(limits.time_limit_ms, 1000.0)
        self.assertEqual(limits.depth_limit, 10)
        self.assertEqual(limits.memory_limit_mb, 100.0)
        self.assertEqual(limits.nodes_limit, 1000)
        self.assertEqual(limits.additional_limits, {"custom_limit": 50})
    
    def test_get_limit(self):
        """Test the get_limit method."""
        self.logger.debug("Testing ResourceLimits.get_limit")
        
        # Create ResourceLimits with various limits
        limits = ResourceLimits(
            time_limit_ms=1000.0,
            depth_limit=10,
            custom_limit=50,
            another_custom_limit=100
        )
        
        # Test getting standard limits
        self.assertEqual(limits.get_limit("time_limit_ms"), 1000.0)
        self.assertEqual(limits.get_limit("depth_limit"), 10)
        self.assertIsNone(limits.get_limit("memory_limit_mb"))
        
        # Test getting custom limits
        self.assertEqual(limits.get_limit("custom_limit"), 50)
        self.assertEqual(limits.get_limit("another_custom_limit"), 100)
        
        # Test getting non-existent limit with default
        self.assertIsNone(limits.get_limit("non_existent_limit"))
        self.assertEqual(limits.get_limit("non_existent_limit", 42), 42)
    
    def test_str_representation(self):
        """Test the string representation of ResourceLimits."""
        self.logger.debug("Testing ResourceLimits.__str__")
        
        # Create ResourceLimits with various limits
        limits = ResourceLimits(
            time_limit_ms=1000.0,
            depth_limit=10,
            custom_limit=50
        )
        
        # Get string representation
        str_repr = str(limits)
        
        # Verify it contains all limits
        self.assertIn("time_limit_ms=1000.0", str_repr)
        self.assertIn("depth_limit=10", str_repr)
        self.assertIn("custom_limit=50", str_repr)
        
        # Create ResourceLimits with no limits
        empty_limits = ResourceLimits()
        
        # Get string representation
        empty_str_repr = str(empty_limits)
        
        # Verify it's a valid representation
        self.assertEqual(empty_str_repr, "ResourceLimits()")


class TestBaseProver(unittest.TestCase):
    """Test cases for the BaseProver abstract class using a concrete implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging for debugging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up TestBaseProver tests")
        
        # Create mock AST_Node
        self.mock_goal = MagicMock(spec=AST_Node)
        self.mock_context = {MagicMock(spec=AST_Node), MagicMock(spec=AST_Node)}
        
        # Create a concrete implementation of BaseProver
        self.prover = TestProverImplementation()
    
    def test_prove_method(self):
        """Test the prove method of the BaseProver implementation."""
        self.logger.debug("Testing BaseProver.prove")
        
        # Call the prove method
        result = self.prover.prove(self.mock_goal, self.mock_context)
        
        # Verify the result is a ProofObject
        self.assertIsInstance(result, ProofObject)
        self.assertTrue(result.goal_achieved)
        self.assertEqual(result.conclusion_ast, self.mock_goal)
        self.assertEqual(result.inference_engine_used, "TestProver")
    
    def test_can_handle_method(self):
        """Test the can_handle method of the BaseProver implementation."""
        self.logger.debug("Testing BaseProver.can_handle")
        
        # Call the can_handle method
        result = self.prover.can_handle(self.mock_goal, self.mock_context)
        
        # Verify the result is a boolean
        self.assertIsInstance(result, bool)
        self.assertTrue(result)  # Our test implementation always returns True
    
    def test_name_property(self):
        """Test the name property of the BaseProver implementation."""
        self.logger.debug("Testing BaseProver.name")
        
        # Get the name
        name = self.prover.name
        
        # Verify the name
        self.assertEqual(name, "TestProver")
    
    def test_capabilities_property(self):
        """Test the capabilities property of the BaseProver implementation."""
        self.logger.debug("Testing BaseProver.capabilities")
        
        # Get the capabilities
        capabilities = self.prover.capabilities
        
        # Verify the capabilities
        self.assertIsInstance(capabilities, dict)
        self.assertTrue(capabilities["first_order_logic"])
        self.assertTrue(capabilities["propositional_logic"])
        
        # Create a prover with custom capabilities
        custom_capabilities = {
            "modal_logic": True,
            "arithmetic": True
        }
        custom_prover = TestProverImplementation(capabilities=custom_capabilities)
        
        # Get the capabilities
        custom_prover_capabilities = custom_prover.capabilities
        
        # Verify the capabilities
        self.assertEqual(custom_prover_capabilities, custom_capabilities)


if __name__ == '__main__':
    unittest.main()