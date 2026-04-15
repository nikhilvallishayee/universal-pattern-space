"""
Enhanced test cases for the Context Engine.

This file extends the basic tests in test_context_engine.py with more thorough
testing of complex methods and edge cases, as identified in the test plan.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import os
import tempfile
import time
import uuid

from godelOS.common_sense.context_engine import ContextEngine, Context, ContextType, ContextVariable


class TestContextEngineEnhanced(unittest.TestCase):
    """Enhanced test cases for the ContextEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.knowledge_store = Mock()
        self.engine = ContextEngine(knowledge_store=self.knowledge_store)
        
        # Create some test contexts for reuse
        self.system_context = self.engine.create_context(
            name="System Context",
            context_type=ContextType.SYSTEM,
            variables={
                "system_var1": "system_value1",
                "common_var": "system_common_value"
            }
        )
        
        self.task_context = self.engine.create_context(
            name="Task Context",
            context_type=ContextType.TASK,
            parent_id=self.system_context.id,
            variables={
                "task_var1": "task_value1",
                "common_var": "task_common_value"  # Overrides system_context's common_var
            }
        )
    
    def test_merge_contexts(self):
        """Test merging variables from one context to another."""
        # Create source context with variables
        source_context = self.engine.create_context(
            name="Source Context",
            context_type=ContextType.CUSTOM,
            variables={
                "source_var1": "source_value1",
                "common_var": "source_common_value"
            }
        )
        
        # Create target context with variables
        target_context = self.engine.create_context(
            name="Target Context",
            context_type=ContextType.CUSTOM,
            variables={
                "target_var1": "target_value1",
                "common_var": "target_common_value"
            }
        )
        
        # Test merging without override
        result = self.engine.merge_contexts(source_context.id, target_context.id, override=False)
        self.assertTrue(result, "Merge should succeed")
        
        # Check that unique variables were merged
        target = self.engine.get_context(target_context.id)
        self.assertEqual(target.variables["source_var1"].value, "source_value1", 
                        "Source-only variables should be merged")
        self.assertEqual(target.variables["target_var1"].value, "target_value1", 
                        "Target variables should be preserved")
        
        # Check that common variables were not overridden
        self.assertEqual(target.variables["common_var"].value, "target_common_value", 
                        "Common variables should not be overridden when override=False")
        
        # Test merging with override
        result = self.engine.merge_contexts(source_context.id, target_context.id, override=True)
        self.assertTrue(result, "Merge with override should succeed")
        
        # Check that common variables were overridden
        target = self.engine.get_context(target_context.id)
        self.assertEqual(target.variables["common_var"].value, "source_common_value", 
                        "Common variables should be overridden when override=True")
        
        # Test merging non-existent contexts
        result = self.engine.merge_contexts("non-existent-id", target_context.id)
        self.assertFalse(result, "Merge with non-existent source should fail")
        
        result = self.engine.merge_contexts(source_context.id, "non-existent-id")
        self.assertFalse(result, "Merge with non-existent target should fail")
        
        # Verify knowledge store was updated
        self.knowledge_store.add_entity.assert_called()
        self.knowledge_store.add_property.assert_called()
    
    def test_derive_context(self):
        """Test creating a new context derived from a parent context."""
        # Test deriving with default settings (inherit parent's type and variables)
        derived_context = self.engine.derive_context(
            parent_id=self.system_context.id,
            name="Derived Context"
        )
        
        self.assertIsNotNone(derived_context, "Derived context should be created")
        self.assertEqual(derived_context.parent_id, self.system_context.id, 
                        "Derived context should have correct parent")
        self.assertEqual(derived_context.type, self.system_context.type, 
                        "Derived context should inherit parent's type")
        
        # Check that variables were inherited
        self.assertEqual(derived_context.variables["system_var1"].value, "system_value1", 
                        "Derived context should inherit parent's variables")
        self.assertEqual(derived_context.variables["common_var"].value, "system_common_value", 
                        "Derived context should inherit parent's variables")
        
        # Test deriving with custom type and without inheriting variables
        custom_derived = self.engine.derive_context(
            parent_id=self.system_context.id,
            name="Custom Derived",
            context_type=ContextType.DIALOGUE,
            inherit_variables=False
        )
        
        self.assertEqual(custom_derived.type, ContextType.DIALOGUE, 
                        "Derived context should use specified type")
        self.assertEqual(len(custom_derived.variables), 0, 
                        "Derived context should not inherit variables when inherit_variables=False")
        
        # Test deriving from non-existent parent
        derived_none = self.engine.derive_context(
            parent_id="non-existent-id",
            name="Invalid Derived"
        )
        
        self.assertIsNone(derived_none, "Deriving from non-existent parent should return None")
    
    def test_get_context_hierarchy(self):
        """Test getting a context hierarchy (context and its ancestors)."""
        # Create a multi-level hierarchy
        grandparent = self.engine.create_context(
            name="Grandparent",
            context_type=ContextType.SYSTEM
        )
        
        parent = self.engine.create_context(
            name="Parent",
            context_type=ContextType.TASK,
            parent_id=grandparent.id
        )
        
        child = self.engine.create_context(
            name="Child",
            context_type=ContextType.DIALOGUE,
            parent_id=parent.id
        )
        
        # Get hierarchy starting from child
        hierarchy = self.engine.get_context_hierarchy(child.id)
        
        # Check hierarchy order (child to grandparent)
        self.assertEqual(len(hierarchy), 3, "Hierarchy should have 3 levels")
        self.assertEqual(hierarchy[0].id, child.id, "First in hierarchy should be child")
        self.assertEqual(hierarchy[1].id, parent.id, "Second in hierarchy should be parent")
        self.assertEqual(hierarchy[2].id, grandparent.id, "Third in hierarchy should be grandparent")
        
        # Get hierarchy starting from parent
        hierarchy = self.engine.get_context_hierarchy(parent.id)
        
        # Check hierarchy order (parent to grandparent)
        self.assertEqual(len(hierarchy), 2, "Hierarchy should have 2 levels")
        self.assertEqual(hierarchy[0].id, parent.id, "First in hierarchy should be parent")
        self.assertEqual(hierarchy[1].id, grandparent.id, "Second in hierarchy should be grandparent")
        
        # Test with active context
        self.engine.set_active_context(child.id)
        hierarchy = self.engine.get_context_hierarchy()
        
        # Check hierarchy order (child to grandparent)
        self.assertEqual(len(hierarchy), 3, "Hierarchy should have 3 levels")
        self.assertEqual(hierarchy[0].id, child.id, "First in hierarchy should be child")
        
        # Test with non-existent context
        hierarchy = self.engine.get_context_hierarchy("non-existent-id")
        self.assertEqual(hierarchy, [], "Hierarchy for non-existent context should be empty")
        
        # Test with no active context
        self.engine.active_context_id = None
        hierarchy = self.engine.get_context_hierarchy()
        self.assertEqual(hierarchy, [], "Hierarchy with no active context should be empty")
    
    def test_get_context_snapshot(self):
        """Test getting a snapshot of all variables in a context and its parents."""
        # Create a multi-level hierarchy with variables
        grandparent = self.engine.create_context(
            name="Grandparent",
            context_type=ContextType.SYSTEM,
            variables={
                "var1": "grandparent_value1",
                "var2": "grandparent_value2",
                "common_var": "grandparent_common"
            }
        )
        
        parent = self.engine.create_context(
            name="Parent",
            context_type=ContextType.TASK,
            parent_id=grandparent.id,
            variables={
                "var3": "parent_value3",
                "var2": "parent_value2",  # Overrides grandparent's var2
                "common_var": "parent_common"  # Overrides grandparent's common_var
            }
        )
        
        child = self.engine.create_context(
            name="Child",
            context_type=ContextType.DIALOGUE,
            parent_id=parent.id,
            variables={
                "var4": "child_value4",
                "common_var": "child_common"  # Overrides parent's and grandparent's common_var
            }
        )
        
        # Get snapshot starting from child
        snapshot = self.engine.get_context_snapshot(child.id)
        
        # Check that all variables are included with correct override precedence
        self.assertEqual(len(snapshot), 5, "Snapshot should contain 5 variables")
        self.assertEqual(snapshot["var1"], "grandparent_value1", "Grandparent-only variables should be included")
        self.assertEqual(snapshot["var2"], "parent_value2", "Parent should override grandparent variables")
        self.assertEqual(snapshot["var3"], "parent_value3", "Parent-only variables should be included")
        self.assertEqual(snapshot["var4"], "child_value4", "Child-only variables should be included")
        self.assertEqual(snapshot["common_var"], "child_common", "Child should override all common variables")
        
        # Get snapshot starting from parent
        snapshot = self.engine.get_context_snapshot(parent.id)
        
        # Check that child variables are not included
        self.assertEqual(len(snapshot), 4, "Snapshot should contain 4 variables")
        self.assertNotIn("var4", snapshot, "Child variables should not be included in parent snapshot")
        self.assertEqual(snapshot["common_var"], "parent_common", "Parent should override grandparent common variable")
        
        # Test with active context
        self.engine.set_active_context(child.id)
        snapshot = self.engine.get_context_snapshot()
        
        # Check that all variables are included
        self.assertEqual(len(snapshot), 5, "Snapshot should contain 5 variables")
        
        # Test with non-existent context
        snapshot = self.engine.get_context_snapshot("non-existent-id")
        self.assertEqual(snapshot, {}, "Snapshot for non-existent context should be empty")
        
        # Test with no active context
        self.engine.active_context_id = None
        snapshot = self.engine.get_context_snapshot()
        self.assertEqual(snapshot, {}, "Snapshot with no active context should be empty")
    
    def test_revert_context(self):
        """Test reverting to the previous active context."""
        # Create contexts
        context1 = self.engine.create_context(
            name="Context 1",
            context_type=ContextType.TASK
        )
        
        context2 = self.engine.create_context(
            name="Context 2",
            context_type=ContextType.TASK
        )
        
        context3 = self.engine.create_context(
            name="Context 3",
            context_type=ContextType.TASK
        )
        
        # Set up a history by activating contexts in sequence
        self.engine.set_active_context(context1.id)
        self.engine.set_active_context(context2.id)
        self.engine.set_active_context(context3.id)
        
        # Revert to context2
        result = self.engine.revert_context()
        self.assertTrue(result, "Revert should succeed")
        self.assertEqual(self.engine.active_context_id, context2.id, 
                        "Active context should be reverted to context2")
        
        # Revert to context1
        result = self.engine.revert_context()
        self.assertTrue(result, "Revert should succeed")
        self.assertEqual(self.engine.active_context_id, context1.id, 
                        "Active context should be reverted to context1")
        
        # Revert with empty history
        result = self.engine.revert_context()
        self.assertFalse(result, "Revert with empty history should fail")
        self.assertEqual(self.engine.active_context_id, context1.id, 
                        "Active context should remain unchanged")
    
    def test_save_and_load_contexts(self):
        """Test saving and loading contexts to/from a file."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create a complex set of contexts
            context1 = self.engine.create_context(
                name="Context 1",
                context_type=ContextType.SYSTEM,
                variables={
                    "var1": {"type": "int", "value": 42, "metadata": {"unit": "count"}},
                    "var2": "string value"
                }
            )
            
            context2 = self.engine.create_context(
                name="Context 2",
                context_type=ContextType.TASK,
                parent_id=context1.id,
                variables={
                    "var3": True,
                    "var4": 3.14
                }
            )
            
            # Set active context and build history
            self.engine.set_active_context(context1.id)
            self.engine.set_active_context(context2.id)
            
            # Save contexts to file
            result = self.engine.save_contexts(temp_path)
            self.assertTrue(result, "Save should succeed")
            
            # Create a new engine
            new_engine = ContextEngine(knowledge_store=self.knowledge_store)
            
            # Load contexts from file
            result = new_engine.load_contexts(temp_path)
            self.assertTrue(result, "Load should succeed")
            
            # Check that contexts were loaded correctly
            self.assertEqual(len(new_engine.contexts), 2, "Should have 2 contexts")
            self.assertEqual(new_engine.active_context_id, context2.id, 
                            "Active context should be preserved")
            self.assertEqual(len(new_engine.context_history), 1, 
                            "Context history should be preserved")
            
            # Check that context properties were preserved
            loaded_context1 = new_engine.get_context(context1.id)
            self.assertEqual(loaded_context1.name, "Context 1", "Context name should be preserved")
            self.assertEqual(loaded_context1.type, ContextType.SYSTEM, "Context type should be preserved")
            
            # Check that variables were preserved
            self.assertEqual(loaded_context1.variables["var1"].value, 42, 
                            "Variable value should be preserved")
            self.assertEqual(loaded_context1.variables["var1"].type, "int", 
                            "Variable type should be preserved")
            self.assertEqual(loaded_context1.variables["var1"].metadata, {"unit": "count"}, 
                            "Variable metadata should be preserved")
            
            # Check that parent-child relationships were preserved
            loaded_context2 = new_engine.get_context(context2.id)
            self.assertEqual(loaded_context2.parent_id, context1.id, 
                            "Parent-child relationship should be preserved")
            
            # Test loading with invalid file
            result = new_engine.load_contexts("non-existent-file")
            self.assertFalse(result, "Load with invalid file should fail")
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_complex_variable_inheritance(self):
        """Test complex variable inheritance across context hierarchies."""
        # Create a deep hierarchy with variables at each level
        level1 = self.engine.create_context(
            name="Level 1",
            context_type=ContextType.SYSTEM,
            variables={
                "var_l1": "level1_value",
                "var_all": "level1_all"
            }
        )
        
        level2 = self.engine.create_context(
            name="Level 2",
            context_type=ContextType.TASK,
            parent_id=level1.id,
            variables={
                "var_l2": "level2_value",
                "var_all": "level2_all"
            }
        )
        
        level3 = self.engine.create_context(
            name="Level 3",
            context_type=ContextType.DIALOGUE,
            parent_id=level2.id,
            variables={
                "var_l3": "level3_value",
                "var_all": "level3_all"
            }
        )
        
        level4 = self.engine.create_context(
            name="Level 4",
            context_type=ContextType.USER,
            parent_id=level3.id,
            variables={
                "var_l4": "level4_value",
                "var_all": "level4_all"
            }
        )
        
        # Test variable inheritance at each level
        # Level 4 should see its own variables and all ancestors' variables
        self.assertEqual(self.engine.get_variable("var_l1", level4.id), "level1_value", 
                        "Level 4 should inherit level 1 variables")
        self.assertEqual(self.engine.get_variable("var_l2", level4.id), "level2_value", 
                        "Level 4 should inherit level 2 variables")
        self.assertEqual(self.engine.get_variable("var_l3", level4.id), "level3_value", 
                        "Level 4 should inherit level 3 variables")
        self.assertEqual(self.engine.get_variable("var_l4", level4.id), "level4_value", 
                        "Level 4 should see its own variables")
        self.assertEqual(self.engine.get_variable("var_all", level4.id), "level4_all", 
                        "Level 4 should override common variables")
        
        # Level 3 should see its own variables and ancestors' variables (levels 1-2)
        self.assertEqual(self.engine.get_variable("var_l1", level3.id), "level1_value", 
                        "Level 3 should inherit level 1 variables")
        self.assertEqual(self.engine.get_variable("var_l2", level3.id), "level2_value", 
                        "Level 3 should inherit level 2 variables")
        self.assertEqual(self.engine.get_variable("var_l3", level3.id), "level3_value", 
                        "Level 3 should see its own variables")
        self.assertIsNone(self.engine.get_variable("var_l4", level3.id), 
                        "Level 3 should not see level 4 variables")
        self.assertEqual(self.engine.get_variable("var_all", level3.id), "level3_all", 
                        "Level 3 should override common variables")
        
        # Test setting variables at different levels
        # Set a new variable at level 2
        self.engine.set_variable("new_var", "new_value", context_id=level2.id)
        
        # Level 4 should inherit the new variable from level 2
        self.assertEqual(self.engine.get_variable("new_var", level4.id), "new_value", 
                        "Level 4 should inherit new variable from level 2")
        
        # Level 1 should not see the new variable
        self.assertIsNone(self.engine.get_variable("new_var", level1.id), 
                        "Level 1 should not see variables from descendants")
    
    def test_get_contexts_by_type(self):
        """Test getting contexts by type."""
        # Create contexts of different types
        system1 = self.engine.create_context(
            name="System 1",
            context_type=ContextType.SYSTEM
        )
        
        system2 = self.engine.create_context(
            name="System 2",
            context_type=ContextType.SYSTEM
        )
        
        task1 = self.engine.create_context(
            name="Task 1",
            context_type=ContextType.TASK
        )
        
        # Get contexts by type
        system_contexts = self.engine.get_contexts_by_type(ContextType.SYSTEM)
        task_contexts = self.engine.get_contexts_by_type(ContextType.TASK)
        dialogue_contexts = self.engine.get_contexts_by_type(ContextType.DIALOGUE)
        
        # Check results
        self.assertEqual(len(system_contexts), 3, "Should have 3 system contexts (including from setUp)")
        self.assertEqual(len(task_contexts), 2, "Should have 2 task contexts (including from setUp)")
        self.assertEqual(len(dialogue_contexts), 0, "Should have 0 dialogue contexts")
        
        # Check that the correct contexts were returned
        system_ids = [ctx.id for ctx in system_contexts]
        self.assertIn(system1.id, system_ids, "System 1 should be in system contexts")
        self.assertIn(system2.id, system_ids, "System 2 should be in system contexts")
        
        task_ids = [ctx.id for ctx in task_contexts]
        self.assertIn(task1.id, task_ids, "Task 1 should be in task contexts")
    
    def test_get_contexts_by_variable(self):
        """Test getting contexts by variable."""
        # Create contexts with different variables
        context1 = self.engine.create_context(
            name="Context 1",
            context_type=ContextType.CUSTOM,
            variables={
                "search_var": "value1",
                "common_var": "common1"
            }
        )
        
        context2 = self.engine.create_context(
            name="Context 2",
            context_type=ContextType.CUSTOM,
            variables={
                "other_var": "other_value",
                "common_var": "common2"
            }
        )
        
        context3 = self.engine.create_context(
            name="Context 3",
            context_type=ContextType.CUSTOM,
            variables={
                "search_var": "value2",
                "common_var": "common1"  # Same as context1
            }
        )
        
        # Get contexts by variable name only
        search_var_contexts = self.engine.get_contexts_by_variable("search_var")
        other_var_contexts = self.engine.get_contexts_by_variable("other_var")
        common_var_contexts = self.engine.get_contexts_by_variable("common_var")
        
        # Check results
        self.assertEqual(len(search_var_contexts), 2, "Should have 2 contexts with search_var")
        self.assertEqual(len(other_var_contexts), 1, "Should have 1 context with other_var")
        self.assertEqual(len(common_var_contexts), 5, "Should have 5 contexts with common_var (including from setUp)")
        
        # Get contexts by variable name and value
        value1_contexts = self.engine.get_contexts_by_variable("search_var", "value1")
        value2_contexts = self.engine.get_contexts_by_variable("search_var", "value2")
        common1_contexts = self.engine.get_contexts_by_variable("common_var", "common1")
        
        # Check results
        self.assertEqual(len(value1_contexts), 1, "Should have 1 context with search_var=value1")
        self.assertEqual(len(value2_contexts), 1, "Should have 1 context with search_var=value2")
        self.assertEqual(len(common1_contexts), 2, "Should have 2 contexts with common_var=common1")
        
        # Check that the correct contexts were returned
        self.assertEqual(value1_contexts[0].id, context1.id, "Context 1 should have search_var=value1")
        self.assertEqual(value2_contexts[0].id, context3.id, "Context 3 should have search_var=value2")
    
    def test_integration_with_knowledge_store(self):
        """Test integration with the knowledge representation system."""
        # Create a context with variables
        context = self.engine.create_context(
            name="Test Context",
            context_type=ContextType.TASK,
            variables={
                "int_var": 42,
                "str_var": "string value",
                "bool_var": True,
                "float_var": 3.14
            }
        )
        
        # Verify that the knowledge store was called correctly
        self.knowledge_store.add_entity.assert_called_with(f"context:{context.id}")
        self.knowledge_store.add_property.assert_any_call(f"context:{context.id}", "name", "Test Context")
        self.knowledge_store.add_property.assert_any_call(f"context:{context.id}", "type", "TASK")
        
        # Verify that variables were added to the knowledge store
        for var_name in ["int_var", "str_var", "bool_var", "float_var"]:
            var_id = f"context_var:{context.id}:{var_name}"
            self.knowledge_store.add_entity.assert_any_call(var_id)
            self.knowledge_store.add_relation.assert_any_call(f"context:{context.id}", "has_variable", var_id)
            self.knowledge_store.add_property.assert_any_call(var_id, "name", var_name)
        
        # Update the context
        self.engine.update_context(
            context_id=context.id,
            metadata={"updated": True},
            variables={"new_var": "new_value"}
        )
        
        # Verify that the knowledge store was updated
        # The current implementation removes and re-adds the context
        self.knowledge_store.remove_entity.assert_called_with(f"context:{context.id}")
        
        # Delete the context
        self.engine.delete_context(context.id)
        
        # Verify that the context was removed from the knowledge store
        self.knowledge_store.remove_entity.assert_called_with(f"context:{context.id}")


if __name__ == '__main__':
    unittest.main()