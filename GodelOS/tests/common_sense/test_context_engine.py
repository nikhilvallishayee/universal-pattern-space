"""
Test cases for the Context Engine.
"""

import unittest
from unittest.mock import Mock, patch
import json
import os
import tempfile
import time

from godelOS.common_sense.context_engine import ContextEngine, Context, ContextType, ContextVariable


class TestContextEngine(unittest.TestCase):
    """Test cases for the ContextEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.knowledge_store = Mock()
        self.engine = ContextEngine(knowledge_store=self.knowledge_store)
    
    def test_initialization(self):
        """Test initialization of the engine."""
        self.assertEqual(self.engine.knowledge_store, self.knowledge_store)
        self.assertEqual(self.engine.contexts, {})
        self.assertIsNone(self.engine.active_context_id)
        self.assertEqual(self.engine.context_history, [])
        self.assertEqual(self.engine.max_history_length, 100)
    
    def test_create_context(self):
        """Test creating a context."""
        # Create a context
        context = self.engine.create_context(
            name="Test Context",
            context_type=ContextType.TASK,
            metadata={"description": "A test context"}
        )
        
        # Check the context
        self.assertEqual(context.name, "Test Context")
        self.assertEqual(context.type, ContextType.TASK)
        self.assertIsNone(context.parent_id)
        self.assertEqual(context.metadata, {"description": "A test context"})
        self.assertEqual(context.variables, {})
        
        # Check that the context was added to the engine
        self.assertIn(context.id, self.engine.contexts)
        self.assertEqual(self.engine.contexts[context.id], context)
        
        # Check that the knowledge store was called
        self.knowledge_store.add_entity.assert_called_with(f"context:{context.id}")
        self.knowledge_store.add_property.assert_called()
    
    def test_create_context_with_variables(self):
        """Test creating a context with initial variables."""
        # Create a context with variables
        variables = {
            "var1": "value1",
            "var2": {"type": "int", "value": 42, "metadata": {"unit": "count"}}
        }
        
        context = self.engine.create_context(
            name="Test Context",
            context_type=ContextType.TASK,
            variables=variables
        )
        
        # Check the variables
        self.assertEqual(len(context.variables), 2)
        self.assertEqual(context.variables["var1"].value, "value1")
        self.assertEqual(context.variables["var1"].type, "str")
        self.assertEqual(context.variables["var2"].value, 42)
        self.assertEqual(context.variables["var2"].type, "int")
        self.assertEqual(context.variables["var2"].metadata, {"unit": "count"})
    
    def test_create_context_with_parent(self):
        """Test creating a context with a parent."""
        # Create a parent context
        parent = self.engine.create_context(
            name="Parent Context",
            context_type=ContextType.SYSTEM
        )
        
        # Create a child context
        child = self.engine.create_context(
            name="Child Context",
            context_type=ContextType.TASK,
            parent_id=parent.id
        )
        
        # Check the parent-child relationship
        self.assertEqual(child.parent_id, parent.id)
        
        # Check that the knowledge store was called with the relationship
        self.knowledge_store.add_relation.assert_called_with(
            f"context:{child.id}", "has_parent", f"context:{parent.id}"
        )
    
    def test_get_context(self):
        """Test getting a context by ID."""
        # Create a context
        context = self.engine.create_context(
            name="Test Context",
            context_type=ContextType.TASK
        )
        
        # Get the context
        retrieved = self.engine.get_context(context.id)
        
        # Check that the correct context was returned
        self.assertEqual(retrieved, context)
        
        # Try to get a non-existent context
        retrieved = self.engine.get_context("non-existent-id")
        
        # Check that None was returned
        self.assertIsNone(retrieved)
    
    def test_update_context(self):
        """Test updating a context."""
        # Create a context
        context = self.engine.create_context(
            name="Test Context",
            context_type=ContextType.TASK
        )
        
        # Update the context
        metadata = {"description": "Updated description"}
        variables = {"var1": "value1"}
        
        result = self.engine.update_context(
            context_id=context.id,
            metadata=metadata,
            variables=variables
        )
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the context was updated
        updated = self.engine.get_context(context.id)
        self.assertEqual(updated.metadata, metadata)
        self.assertEqual(updated.variables["var1"].value, "value1")
        self.assertEqual(updated.variables["var1"].type, "str")
        
        # Try to update a non-existent context
        result = self.engine.update_context(
            context_id="non-existent-id",
            metadata=metadata
        )
        
        # Check that the update failed
        self.assertFalse(result)
    
    def test_delete_context(self):
        """Test deleting a context."""
        # Create a context
        context = self.engine.create_context(
            name="Test Context",
            context_type=ContextType.TASK
        )
        
        # Set it as the active context
        self.engine.set_active_context(context.id)
        
        # Add it to the history
        self.engine.context_history.append(context.id)
        
        # Delete the context
        result = self.engine.delete_context(context.id)
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the context was removed
        self.assertNotIn(context.id, self.engine.contexts)
        
        # Check that the active context was cleared
        self.assertIsNone(self.engine.active_context_id)
        
        # Check that the context was removed from the history
        self.assertNotIn(context.id, self.engine.context_history)
        
        # Check that the knowledge store was called
        self.knowledge_store.remove_entity.assert_called_with(f"context:{context.id}")
        
        # Try to delete a non-existent context
        result = self.engine.delete_context("non-existent-id")
        
        # Check that the delete failed
        self.assertFalse(result)
    
    def test_set_active_context(self):
        """Test setting the active context."""
        # Create contexts
        context1 = self.engine.create_context(
            name="Context 1",
            context_type=ContextType.TASK
        )
        
        context2 = self.engine.create_context(
            name="Context 2",
            context_type=ContextType.TASK
        )
        
        # Set context1 as active
        result = self.engine.set_active_context(context1.id)
        
        # Check the result
        self.assertTrue(result)
        
        # Check that context1 is active
        self.assertEqual(self.engine.active_context_id, context1.id)
        
        # Set context2 as active
        result = self.engine.set_active_context(context2.id)
        
        # Check the result
        self.assertTrue(result)
        
        # Check that context2 is active
        self.assertEqual(self.engine.active_context_id, context2.id)
        
        # Check that context1 was added to the history
        self.assertIn(context1.id, self.engine.context_history)
        
        # Try to set a non-existent context as active
        result = self.engine.set_active_context("non-existent-id")
        
        # Check that the set failed
        self.assertFalse(result)
        
        # Check that the active context is still context2
        self.assertEqual(self.engine.active_context_id, context2.id)
    
    def test_get_active_context(self):
        """Test getting the active context."""
        # Create a context
        context = self.engine.create_context(
            name="Test Context",
            context_type=ContextType.TASK
        )
        
        # Set it as the active context
        self.engine.set_active_context(context.id)
        
        # Get the active context
        active = self.engine.get_active_context()
        
        # Check that the correct context was returned
        self.assertEqual(active, context)
        
        # Clear the active context
        self.engine.active_context_id = None
        
        # Get the active context
        active = self.engine.get_active_context()
        
        # Check that None was returned
        self.assertIsNone(active)
    
    def test_get_variable(self):
        """Test getting a variable from a context."""
        # Create a context with a variable
        context = self.engine.create_context(
            name="Test Context",
            context_type=ContextType.TASK,
            variables={"var1": "value1"}
        )
        
        # Get the variable
        value = self.engine.get_variable("var1", context.id)
        
        # Check the value
        self.assertEqual(value, "value1")
        
        # Try to get a non-existent variable
        value = self.engine.get_variable("non-existent-var", context.id)
        
        # Check that None was returned
        self.assertIsNone(value)
        
        # Set the context as active
        self.engine.set_active_context(context.id)
        
        # Get the variable without specifying the context
        value = self.engine.get_variable("var1")
        
        # Check the value
        self.assertEqual(value, "value1")
    
    def test_get_variable_from_parent(self):
        """Test getting a variable from a parent context."""
        # Create a parent context with a variable
        parent = self.engine.create_context(
            name="Parent Context",
            context_type=ContextType.SYSTEM,
            variables={"parent_var": "parent_value"}
        )
        
        # Create a child context
        child = self.engine.create_context(
            name="Child Context",
            context_type=ContextType.TASK,
            parent_id=parent.id,
            variables={"child_var": "child_value"}
        )
        
        # Get the parent variable from the child context
        value = self.engine.get_variable("parent_var", child.id)
        
        # Check the value
        self.assertEqual(value, "parent_value")
        
        # Get the child variable from the child context
        value = self.engine.get_variable("child_var", child.id)
        
        # Check the value
        self.assertEqual(value, "child_value")
    
    def test_set_variable(self):
        """Test setting a variable in a context."""
        # Create a context
        context = self.engine.create_context(
            name="Test Context",
            context_type=ContextType.TASK
        )
        
        # Set a variable
        result = self.engine.set_variable(
            name="var1",
            value="value1",
            context_id=context.id
        )
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the variable was set
        value = self.engine.get_variable("var1", context.id)
        self.assertEqual(value, "value1")
        
        # Set a variable with type and metadata
        result = self.engine.set_variable(
            name="var2",
            value=42,
            var_type="int",
            metadata={"unit": "count"},
            context_id=context.id
        )
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the variable was set
        context = self.engine.get_context(context.id)
        self.assertEqual(context.variables["var2"].value, 42)
        self.assertEqual(context.variables["var2"].type, "int")
        self.assertEqual(context.variables["var2"].metadata, {"unit": "count"})