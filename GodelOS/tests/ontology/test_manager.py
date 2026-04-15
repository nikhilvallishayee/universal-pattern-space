"""
Unit tests for the OntologyCreativityManager component.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open

from godelOS.ontology.manager import OntologyCreativityManager
from godelOS.ontology.ontology_manager import OntologyManager
from godelOS.ontology.conceptual_blender import ConceptualBlender
from godelOS.ontology.hypothesis_generator import HypothesisGenerator
from godelOS.ontology.abstraction_hierarchy import AbstractionHierarchyModule

class TestOntologyCreativityManager(unittest.TestCase):
    """Test cases for the OntologyCreativityManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the json.load function to return a test configuration
        with patch('json.load', return_value={}):
            self.manager = OntologyCreativityManager()
        
        # Add some test concepts to the ontology
        ontology_manager = self.manager.get_ontology_manager()
        ontology_manager.add_concept("concept1", {"name": "Concept 1", "description": "Test concept 1"})
        ontology_manager.add_concept("concept2", {"name": "Concept 2", "description": "Test concept 2"})
    
    def test_initialization(self):
        """Test initialization of the OntologyCreativityManager."""
        # Check that components were initialized
        self.assertIsNotNone(self.manager._ontology_manager)
        self.assertIsNotNone(self.manager._conceptual_blender)
        self.assertIsNotNone(self.manager._hypothesis_generator)
        self.assertIsNotNone(self.manager._abstraction_hierarchy)
        
        # Check that component registry was populated
        self.assertIn("ontology_manager", self.manager._components)
        self.assertIn("conceptual_blender", self.manager._components)
        self.assertIn("hypothesis_generator", self.manager._components)
        self.assertIn("abstraction_hierarchy", self.manager._components)
        
        # Check that workflow registry was populated
        self.assertIn("concept_creation", self.manager._workflows)
        self.assertIn("hypothesis_generation", self.manager._workflows)
        self.assertIn("abstraction_management", self.manager._workflows)
    
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "config"}')
    @patch('os.path.exists', return_value=True)
    def test_load_config(self, mock_exists, mock_file, mock_json_load):
        """Test loading configuration from a file."""
        # Set up the mock
        mock_json_load.return_value = {"test": "config"}
        
        # Create a manager with a config path
        manager = OntologyCreativityManager("test_config.json")
        
        # Check that the file was opened
        mock_file.assert_called_once_with("test_config.json", 'r')
        
        # Check that json.load was called
        mock_json_load.assert_called_once()
    
    def test_get_component(self):
        """Test retrieving a component."""
        # Test retrieving existing components
        ontology_manager = self.manager.get_component("ontology_manager")
        self.assertIsInstance(ontology_manager, OntologyManager)
        
        conceptual_blender = self.manager.get_component("conceptual_blender")
        self.assertIsInstance(conceptual_blender, ConceptualBlender)
        
        hypothesis_generator = self.manager.get_component("hypothesis_generator")
        self.assertIsInstance(hypothesis_generator, HypothesisGenerator)
        
        abstraction_hierarchy = self.manager.get_component("abstraction_hierarchy")
        self.assertIsInstance(abstraction_hierarchy, AbstractionHierarchyModule)
        
        # Test retrieving a non-existent component
        component = self.manager.get_component("nonexistent")
        self.assertIsNone(component)
    
    def test_get_specific_components(self):
        """Test retrieving specific components."""
        # Test retrieving the OntologyManager
        ontology_manager = self.manager.get_ontology_manager()
        self.assertIsInstance(ontology_manager, OntologyManager)
        
        # Test retrieving the ConceptualBlender
        conceptual_blender = self.manager.get_conceptual_blender()
        self.assertIsInstance(conceptual_blender, ConceptualBlender)
        
        # Test retrieving the HypothesisGenerator
        hypothesis_generator = self.manager.get_hypothesis_generator()
        self.assertIsInstance(hypothesis_generator, HypothesisGenerator)
        
        # Test retrieving the AbstractionHierarchyModule
        abstraction_hierarchy = self.manager.get_abstraction_hierarchy()
        self.assertIsInstance(abstraction_hierarchy, AbstractionHierarchyModule)
    
    def test_get_config(self):
        """Test retrieving configuration."""
        # Test retrieving the entire configuration
        config = self.manager.get_config()
        self.assertIsNotNone(config)
        
        # Test retrieving configuration for a specific component
        component_config = self.manager.get_config("conceptual_blender")
        self.assertIsNotNone(component_config)
        self.assertIn("default_strategy", component_config)
    
    def test_update_config(self):
        """Test updating configuration."""
        # Test updating configuration for a specific component
        result = self.manager.update_config("conceptual_blender", {"default_strategy": "new_strategy"})
        self.assertTrue(result)
        
        # Check that the configuration was updated
        component_config = self.manager.get_config("conceptual_blender")
        self.assertEqual("new_strategy", component_config["default_strategy"])
        
        # Test updating configuration for a non-existent component
        result = self.manager.update_config("nonexistent", {"key": "value"})
        self.assertFalse(result)
    
    def test_execute_workflow_concept_creation_blend(self):
        """Test executing the concept creation workflow with blending."""
        # Prepare workflow data
        workflow_data = {
            "concept_type": "blend",
            "source_concepts": ["concept1", "concept2"],
            "strategy": "property_merge",
            "concept_id": "blended_concept"
        }
        
        # Execute the workflow
        result = self.manager.execute_workflow("concept_creation", workflow_data)
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        self.assertEqual("blended_concept", result["result"]["concept_id"])
    
    def test_execute_workflow_concept_creation_novel(self):
        """Test executing the concept creation workflow with novel concept generation."""
        # Prepare workflow data
        workflow_data = {
            "concept_type": "novel",
            "seed_concepts": ["concept1", "concept2"],
            "novelty_threshold": 0.3,
            "concept_id": "novel_concept"
        }
        
        # Execute the workflow
        result = self.manager.execute_workflow("concept_creation", workflow_data)
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        self.assertEqual("novel_concept", result["result"]["concept_id"])
    
    def test_execute_workflow_hypothesis_generation(self):
        """Test executing the hypothesis generation workflow."""
        # Prepare workflow data
        workflow_data = {
            "observations": [
                {"type": "observation", "concept_id": "concept1", "property": "property1", "value": "value1"}
            ],
            "context": {"environment": "test"},
            "strategy": "abductive",
            "max_hypotheses": 2
        }
        
        # Execute the workflow
        result = self.manager.execute_workflow("hypothesis_generation", workflow_data)
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        self.assertIn("hypotheses", result["result"])
    
    def test_execute_workflow_abstraction_management_create_hierarchy(self):
        """Test executing the abstraction management workflow to create a hierarchy."""
        # Prepare workflow data
        workflow_data = {
            "operation": "create_hierarchy",
            "hierarchy_id": "test_hierarchy",
            "hierarchy_data": {"name": "Test Hierarchy", "description": "A test hierarchy"}
        }
        
        # Execute the workflow
        result = self.manager.execute_workflow("abstraction_management", workflow_data)
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        self.assertEqual("test_hierarchy", result["result"]["hierarchy_id"])
    
    def test_execute_workflow_abstraction_management_generalize(self):
        """Test executing the abstraction management workflow to generalize from instances."""
        # Prepare workflow data
        workflow_data = {
            "operation": "generalize",
            "instance_ids": ["concept1", "concept2"],
            "hierarchy_id": "test_hierarchy"
        }
        
        # Create the hierarchy first
        self.manager.execute_workflow("abstraction_management", {
            "operation": "create_hierarchy",
            "hierarchy_id": "test_hierarchy",
            "hierarchy_data": {"name": "Test Hierarchy", "description": "A test hierarchy"}
        })
        
        # Execute the workflow
        result = self.manager.execute_workflow("abstraction_management", workflow_data)
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        self.assertIn("abstraction_data", result["result"])
    
    def test_execute_workflow_abstraction_management_find_level(self):
        """Test executing the abstraction management workflow to find an appropriate abstraction level."""
        # Prepare workflow data
        workflow_data = {
            "operation": "find_level",
            "hierarchy_id": "test_hierarchy",
            "task_data": {"type": "detailed_analysis"}
        }
        
        # Create the hierarchy first
        self.manager.execute_workflow("abstraction_management", {
            "operation": "create_hierarchy",
            "hierarchy_id": "test_hierarchy",
            "hierarchy_data": {"name": "Test Hierarchy", "description": "A test hierarchy"}
        })
        
        # Add some concepts to levels
        abstraction_hierarchy = self.manager.get_abstraction_hierarchy()
        abstraction_hierarchy.add_concept_to_level("test_hierarchy", "concept1", 0)
        abstraction_hierarchy.add_concept_to_level("test_hierarchy", "concept2", 1)
        
        # Execute the workflow
        result = self.manager.execute_workflow("abstraction_management", workflow_data)
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        self.assertIn("level", result["result"])
        self.assertEqual(0, result["result"]["level"])  # Should return the lowest level for detailed_analysis
    
    def test_execute_workflow_abstraction_management_check_consistency(self):
        """Test executing the abstraction management workflow to check hierarchy consistency."""
        # Prepare workflow data
        workflow_data = {
            "operation": "check_consistency",
            "hierarchy_id": "test_hierarchy"
        }
        
        # Create the hierarchy first
        self.manager.execute_workflow("abstraction_management", {
            "operation": "create_hierarchy",
            "hierarchy_id": "test_hierarchy",
            "hierarchy_data": {"name": "Test Hierarchy", "description": "A test hierarchy"}
        })
        
        # Execute the workflow
        result = self.manager.execute_workflow("abstraction_management", workflow_data)
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        self.assertEqual("test_hierarchy", result["result"]["hierarchy_id"])
    
    def test_execute_workflow_invalid_workflow(self):
        """Test executing an invalid workflow."""
        # Execute an invalid workflow
        result = self.manager.execute_workflow("invalid_workflow", {})
        
        # Check the result
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual("Workflow invalid_workflow not found", result["error"])
    
    def test_execute_workflow_invalid_operation(self):
        """Test executing a workflow with an invalid operation."""
        # Prepare workflow data with an invalid operation
        workflow_data = {
            "operation": "invalid_operation"
        }
        
        # Execute the workflow
        result = self.manager.execute_workflow("abstraction_management", workflow_data)
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual("error", result["result"]["status"])
        self.assertIn("message", result["result"])
        self.assertEqual("Unknown operation: invalid_operation", result["result"]["message"])
    
    def test_initialize(self):
        """Test initializing the OntologyCreativityManager."""
        # Test initialization
        result = self.manager.initialize()
        self.assertTrue(result)
        
        # Check that the default hierarchy was created if auto_generalize is enabled
        if self.manager._config["abstraction_hierarchy"]["auto_generalize"]:
            default_hierarchy = self.manager._config["abstraction_hierarchy"]["default_hierarchy"]
            abstraction_hierarchy = self.manager.get_abstraction_hierarchy()
            self.assertIn(default_hierarchy, abstraction_hierarchy.get_all_hierarchies())
    
    def test_shutdown(self):
        """Test shutting down the OntologyCreativityManager."""
        # Test shutdown
        result = self.manager.shutdown()
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()