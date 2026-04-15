"""
Test cases for the Default Reasoning Module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import tempfile

from godelOS.common_sense.default_reasoning import (
    DefaultReasoningModule, Default, Exception as ReasoningException, DefaultType
)


class TestDefaultReasoningModule(unittest.TestCase):
    """Test cases for the DefaultReasoningModule."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.knowledge_store = Mock()
        self.inference_coordinator = Mock()
        self.context_engine = Mock()
        
        # Create the module
        self.module = DefaultReasoningModule(
            knowledge_store=self.knowledge_store,
            inference_coordinator=self.inference_coordinator,
            context_engine=self.context_engine
        )
    
    def test_initialization(self):
        """Test initialization of the module."""
        self.assertEqual(self.module.knowledge_store, self.knowledge_store)
        self.assertEqual(self.module.inference_coordinator, self.inference_coordinator)
        self.assertEqual(self.module.context_engine, self.context_engine)
        self.assertEqual(self.module.defaults, {})
        self.assertEqual(self.module.exceptions, {})
        self.assertEqual(self.module.exception_by_default, {})
    
    def test_add_default(self):
        """Test adding a default rule."""
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)",
            type=DefaultType.NORMAL,
            priority=1,
            confidence=0.9,
            metadata={"description": "Birds can fly"}
        )
        
        # Add the default rule
        self.module.add_default(default)
        
        # Check that the default was added
        self.assertIn("birds_fly", self.module.defaults)
        self.assertEqual(self.module.defaults["birds_fly"], default)
        
        # Check that the exception mapping was initialized
        self.assertIn("birds_fly", self.module.exception_by_default)
        self.assertEqual(self.module.exception_by_default["birds_fly"], [])
        
        # Check that the knowledge store was called
        self.knowledge_store.add_entity.assert_called_with("default:birds_fly")
        self.knowledge_store.add_property.assert_called()
    
    def test_add_exception(self):
        """Test adding an exception to a default rule."""
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)",
            type=DefaultType.NORMAL,
            priority=1,
            confidence=0.9
        )
        
        # Add the default rule
        self.module.add_default(default)
        
        # Create an exception
        exception = ReasoningException(
            id="penguins_exception",
            default_id="birds_fly",
            condition="is_penguin(X)",
            priority=2,
            confidence=0.95
        )
        
        # Add the exception
        self.module.add_exception(exception)
        
        # Check that the exception was added
        self.assertIn("penguins_exception", self.module.exceptions)
        self.assertEqual(self.module.exceptions["penguins_exception"], exception)
        
        # Check that the exception was added to the mapping
        self.assertIn("penguins_exception", self.module.exception_by_default["birds_fly"])
        
        # Check that the knowledge store was called
        self.knowledge_store.add_entity.assert_called_with("exception:penguins_exception")
        self.knowledge_store.add_property.assert_called()
        self.knowledge_store.add_relation.assert_called_with(
            "exception:penguins_exception", "excepts", "default:birds_fly"
        )
    
    def test_remove_default(self):
        """Test removing a default rule."""
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)"
        )
        
        # Add the default rule
        self.module.add_default(default)
        
        # Create an exception
        exception = ReasoningException(
            id="penguins_exception",
            default_id="birds_fly",
            condition="is_penguin(X)"
        )
        
        # Add the exception
        self.module.add_exception(exception)
        
        # Remove the default rule
        result = self.module.remove_default("birds_fly")
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the default was removed
        self.assertNotIn("birds_fly", self.module.defaults)
        
        # Check that the exception was removed
        self.assertNotIn("penguins_exception", self.module.exceptions)
        
        # Check that the exception mapping was removed
        self.assertNotIn("birds_fly", self.module.exception_by_default)
        
        # Check that the knowledge store was called
        self.knowledge_store.remove_entity.assert_called_with("default:birds_fly")
        
        # Try to remove a non-existent default
        result = self.module.remove_default("non_existent")
        
        # Check that the remove failed
        self.assertFalse(result)
    
    def test_remove_exception(self):
        """Test removing an exception."""
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)"
        )
        
        # Add the default rule
        self.module.add_default(default)
        
        # Create an exception
        exception = ReasoningException(
            id="penguins_exception",
            default_id="birds_fly",
            condition="is_penguin(X)"
        )
        
        # Add the exception
        self.module.add_exception(exception)
        
        # Remove the exception
        result = self.module.remove_exception("penguins_exception")
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the exception was removed
        self.assertNotIn("penguins_exception", self.module.exceptions)
        
        # Check that the exception was removed from the mapping
        self.assertNotIn("penguins_exception", self.module.exception_by_default["birds_fly"])
        
        # Check that the knowledge store was called
        self.knowledge_store.remove_entity.assert_called_with("exception:penguins_exception")
        
        # Try to remove a non-existent exception
        result = self.module.remove_exception("non_existent")
        
        # Check that the remove failed
        self.assertFalse(result)
    
    def test_get_default(self):
        """Test getting a default rule by ID."""
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)"
        )
        
        # Add the default rule
        self.module.add_default(default)
        
        # Get the default rule
        retrieved = self.module.get_default("birds_fly")
        
        # Check that the correct default was returned
        self.assertEqual(retrieved, default)
        
        # Try to get a non-existent default
        retrieved = self.module.get_default("non_existent")
        
        # Check that None was returned
        self.assertIsNone(retrieved)
    
    def test_get_exception(self):
        """Test getting an exception by ID."""
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)"
        )
        
        # Add the default rule
        self.module.add_default(default)
        
        # Create an exception
        exception = ReasoningException(
            id="penguins_exception",
            default_id="birds_fly",
            condition="is_penguin(X)"
        )
        
        # Add the exception
        self.module.add_exception(exception)
        
        # Get the exception
        retrieved = self.module.get_exception("penguins_exception")
        
        # Check that the correct exception was returned
        self.assertEqual(retrieved, exception)
        
        # Try to get a non-existent exception
        retrieved = self.module.get_exception("non_existent")
        
        # Check that None was returned
        self.assertIsNone(retrieved)
    
    def test_get_exceptions_for_default(self):
        """Test getting all exceptions for a default rule."""
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X) and not(is_ostrich(X)))",
            consequent="can_fly(X)"
        )
        
        # Add the default rule
        self.module.add_default(default)
        
        # Create exceptions
        exception1 = ReasoningException(
            id="penguins_exception",
            default_id="birds_fly",
            condition="is_penguin(X)"
        )
        
        exception2 = ReasoningException(
            id="ostrich_exception",
            default_id="birds_fly",
            condition="is_ostrich(X)"
        )
        
        # Add the exceptions
        self.module.add_exception(exception1)
        self.module.add_exception(exception2)
        
        # Get the exceptions
        exceptions = self.module.get_exceptions_for_default("birds_fly")
        
        # Check that the correct exceptions were returned
        self.assertEqual(len(exceptions), 2)
        self.assertIn(exception1, exceptions)
        self.assertIn(exception2, exceptions)
        
        # Try to get exceptions for a non-existent default
        exceptions = self.module.get_exceptions_for_default("non_existent")
        
        # Check that an empty list was returned
        self.assertEqual(exceptions, [])
    
    def test_apply_defaults_standard_inference_success(self):
        """Test applying defaults when standard inference succeeds."""
        # Mock the inference coordinator to succeed
        self.inference_coordinator.prove = Mock(return_value=MagicMock(
            success=True,
            explanation="Proven by standard inference"
        ))
        
        # Apply defaults
        result = self.module.apply_defaults("can_fly(tweety)")
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(result["method"], "standard_inference")
        self.assertEqual(result["defaults_used"], [])
        self.assertEqual(result["exceptions_applied"], [])
        
        # Check that the inference coordinator was called
        self.inference_coordinator.prove.assert_called_with("can_fly(tweety)")
    
    def test_apply_defaults_with_default_rules(self):
        """Test applying defaults when standard inference fails."""
        # Mock the inference coordinator to fail
        self.inference_coordinator.prove = Mock(return_value=MagicMock(success=False))
        
        # Mock the _is_prerequisite_satisfied method to return True
        self.module._is_prerequisite_satisfied = Mock(return_value=True)
        
        # Mock the _is_justification_consistent method to return True
        self.module._is_justification_consistent = Mock(return_value=True)
        
        # Mock the _is_exception_applicable method to return False
        self.module._is_exception_applicable = Mock(return_value=False)
        
        # Mock the _directly_answers_query method to return True
        self.module._directly_answers_query = Mock(return_value=True)
        
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)",
            confidence=0.9
        )
        
        # Add the default rule
        self.module.add_default(default)
        
        # Apply defaults
        result = self.module.apply_defaults("can_fly(tweety)")
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["confidence"], 0.9)
        self.assertEqual(result["method"], "default_reasoning")
        self.assertEqual(result["defaults_used"], ["birds_fly"])
        self.assertEqual(result["exceptions_applied"], [])
    
    def test_apply_defaults_with_exceptions(self):
        """Test applying defaults with exceptions."""
        # Mock the inference coordinator to fail
        self.inference_coordinator.prove = Mock(return_value=MagicMock(success=False))
        
        # Mock the _is_prerequisite_satisfied method to return True
        self.module._is_prerequisite_satisfied = Mock(return_value=True)
        
        # Mock the _is_justification_consistent method to return True
        self.module._is_justification_consistent = Mock(return_value=True)
        
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)",
            confidence=0.9
        )
        
        # Add the default rule
        self.module.add_default(default)
        
        # Create an exception
        exception = ReasoningException(
            id="penguins_exception",
            default_id="birds_fly",
            condition="is_penguin(X)"
        )
        
        # Add the exception
        self.module.add_exception(exception)
        
        # Mock the _is_exception_applicable method to return True for the exception
        self.module._is_exception_applicable = Mock(return_value=True)
        
        # Apply defaults
        result = self.module.apply_defaults("can_fly(tweety)")
        
        # Check the result
        self.assertFalse(result["success"])
        self.assertEqual(result["method"], "default_reasoning")
        self.assertEqual(result["defaults_used"], ["birds_fly"])
        self.assertEqual(result["exceptions_applied"], ["penguins_exception"])
    
    def test_check_consistency(self):
        """Test checking consistency of a statement."""
        # Mock the inference coordinator to fail for the negation (meaning the statement is consistent)
        self.inference_coordinator.prove = Mock(return_value=MagicMock(success=False))
        
        # Check consistency
        result = self.module.check_consistency("can_fly(tweety)")
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the inference coordinator was called with the negation
        self.inference_coordinator.prove.assert_called_with("not (can_fly(tweety))")
        
        # Mock the inference coordinator to succeed for the negation (meaning the statement is inconsistent)
        self.inference_coordinator.prove = Mock(return_value=MagicMock(success=True))
        
        # Check consistency
        result = self.module.check_consistency("can_fly(tweety)")
        
        # Check the result
        self.assertFalse(result)


class TestDefault(unittest.TestCase):
    """Test cases for the Default class."""
    
    def test_initialization(self):
        """Test initialization of a default rule."""
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)",
            type=DefaultType.NORMAL,
            priority=1,
            confidence=0.9,
            metadata={"description": "Birds can fly"}
        )
        
        # Check the default rule
        self.assertEqual(default.id, "birds_fly")
        self.assertEqual(default.prerequisite, "is_bird(X)")
        self.assertEqual(default.justification, "not(is_penguin(X))")
        self.assertEqual(default.consequent, "can_fly(X)")
        self.assertEqual(default.type, DefaultType.NORMAL)
        self.assertEqual(default.priority, 1)
        self.assertEqual(default.confidence, 0.9)
        self.assertEqual(default.metadata, {"description": "Birds can fly"})
    
    def test_to_dict(self):
        """Test converting a default rule to a dictionary."""
        # Create a default rule
        default = Default(
            id="birds_fly",
            prerequisite="is_bird(X)",
            justification="not(is_penguin(X))",
            consequent="can_fly(X)",
            type=DefaultType.NORMAL,
            priority=1,
            confidence=0.9,
            metadata={"description": "Birds can fly"}
        )
        
        # Convert to dictionary
        default_dict = default.to_dict()
        
        # Check the dictionary
        self.assertEqual(default_dict["id"], "birds_fly")
        self.assertEqual(default_dict["prerequisite"], "is_bird(X)")
        self.assertEqual(default_dict["justification"], "not(is_penguin(X))")
        self.assertEqual(default_dict["consequent"], "can_fly(X)")
        self.assertEqual(default_dict["type"], "NORMAL")
        self.assertEqual(default_dict["priority"], 1)
        self.assertEqual(default_dict["confidence"], 0.9)
        self.assertEqual(default_dict["metadata"], {"description": "Birds can fly"})
    
    def test_from_dict(self):
        """Test creating a default rule from a dictionary."""
        # Create a dictionary
        default_dict = {
            "id": "birds_fly",
            "prerequisite": "is_bird(X)",
            "justification": "not(is_penguin(X))",
            "consequent": "can_fly(X)",
            "type": "NORMAL",
            "priority": 1,
            "confidence": 0.9,
            "metadata": {"description": "Birds can fly"}
        }
        
        # Create a default rule from the dictionary
        default = Default.from_dict(default_dict)
        
        # Check the default rule
        self.assertEqual(default.id, "birds_fly")
        self.assertEqual(default.prerequisite, "is_bird(X)")
        self.assertEqual(default.justification, "not(is_penguin(X))")
        self.assertEqual(default.consequent, "can_fly(X)")
        self.assertEqual(default.type, DefaultType.NORMAL)
        self.assertEqual(default.priority, 1)
        self.assertEqual(default.confidence, 0.9)
        self.assertEqual(default.metadata, {"description": "Birds can fly"})


class TestException(unittest.TestCase):
    """Test cases for the Exception class."""
    
    def test_initialization(self):
        """Test initialization of an exception."""
        # Create an exception
        exception = ReasoningException(
            id="penguins_exception",
            default_id="birds_fly",
            condition="is_penguin(X)",
            priority=2,
            confidence=0.95,
            metadata={"description": "Penguins can't fly"}
        )
        
        # Check the exception
        self.assertEqual(exception.id, "penguins_exception")
        self.assertEqual(exception.default_id, "birds_fly")
        self.assertEqual(exception.condition, "is_penguin(X)")
        self.assertEqual(exception.priority, 2)
        self.assertEqual(exception.confidence, 0.95)
        self.assertEqual(exception.metadata, {"description": "Penguins can't fly"})
    
    def test_to_dict(self):
        """Test converting an exception to a dictionary."""
        # Create an exception
        exception = ReasoningException(
            id="penguins_exception",
            default_id="birds_fly",
            condition="is_penguin(X)",
            priority=2,
            confidence=0.95,
            metadata={"description": "Penguins can't fly"}
        )
        
        # Convert to dictionary
        exception_dict = exception.to_dict()
        
        # Check the dictionary
        self.assertEqual(exception_dict["id"], "penguins_exception")
        self.assertEqual(exception_dict["default_id"], "birds_fly")
        self.assertEqual(exception_dict["condition"], "is_penguin(X)")
        self.assertEqual(exception_dict["priority"], 2)
        self.assertEqual(exception_dict["confidence"], 0.95)
        self.assertEqual(exception_dict["metadata"], {"description": "Penguins can't fly"})
    
    def test_from_dict(self):
        """Test creating an exception from a dictionary."""
        # Create a dictionary
        exception_dict = {
            "id": "penguins_exception",
            "default_id": "birds_fly",
            "condition": "is_penguin(X)",
            "priority": 2,
            "confidence": 0.95,
            "metadata": {"description": "Penguins can't fly"}
        }
        
        # Create an exception from the dictionary
        exception = ReasoningException.from_dict(exception_dict)
        
        # Check the exception
        self.assertEqual(exception.id, "penguins_exception")
        self.assertEqual(exception.default_id, "birds_fly")
        self.assertEqual(exception.condition, "is_penguin(X)")
        self.assertEqual(exception.priority, 2)
        self.assertEqual(exception.confidence, 0.95)
        self.assertEqual(exception.metadata, {"description": "Penguins can't fly"})


if __name__ == '__main__':
    unittest.main()