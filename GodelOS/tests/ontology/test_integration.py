"""
Integration tests for the Ontological Creativity & Abstraction System.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.ontology.manager import OntologyCreativityManager
from godelOS.ontology.ontology_manager import OntologyManager
from godelOS.ontology.conceptual_blender import ConceptualBlender
from godelOS.ontology.hypothesis_generator import HypothesisGenerator
from godelOS.ontology.abstraction_hierarchy import AbstractionHierarchyModule

class TestOntologyIntegration(unittest.TestCase):
    """Integration tests for the Ontological Creativity & Abstraction System."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = OntologyCreativityManager()
        
        # Get component references
        self.ontology_manager = self.manager.get_ontology_manager()
        self.conceptual_blender = self.manager.get_conceptual_blender()
        self.hypothesis_generator = self.manager.get_hypothesis_generator()
        self.abstraction_hierarchy = self.manager.get_abstraction_hierarchy()
        
        # Initialize the system
        self.manager.initialize()
        
        # Add test concepts
        self._add_test_concepts()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.manager.shutdown()
    
    def _add_test_concepts(self):
        """Add test concepts to the ontology."""
        # Add some basic concepts
        self.ontology_manager.add_concept("bird", {
            "name": "Bird",
            "description": "A warm-blooded egg-laying vertebrate animal distinguished by the possession of feathers, wings, a beak, and typically by being able to fly.",
            "properties": {
                "has_feathers": True,
                "has_wings": True,
                "can_fly": True,
                "lays_eggs": True,
                "size": 2,  # Small
                "habitat": "air"
            }
        })
        
        self.ontology_manager.add_concept("fish", {
            "name": "Fish",
            "description": "A limbless cold-blooded vertebrate animal with gills and fins living wholly in water.",
            "properties": {
                "has_fins": True,
                "has_gills": True,
                "can_swim": True,
                "lays_eggs": True,
                "size": 2,  # Small
                "habitat": "water"
            }
        })
        
        self.ontology_manager.add_concept("airplane", {
            "name": "Airplane",
            "description": "A powered flying vehicle with fixed wings and a weight greater than that of the air it displaces.",
            "properties": {
                "has_wings": True,
                "can_fly": True,
                "is_mechanical": True,
                "size": 5,  # Large
                "habitat": "air"
            }
        })
        
        # Add some relations
        self.ontology_manager.add_relation("lives_in", {"type": "spatial"})
        self.ontology_manager.add_relation("eats", {"type": "functional"})
        self.ontology_manager.add_relation("is_a", {"type": "taxonomic"})
        self.ontology_manager.add_relation("has_part", {"type": "compositional"})
        
        # Add relation instances
        self.ontology_manager.add_relation_instance("lives_in", "bird", "air")
        self.ontology_manager.add_relation_instance("lives_in", "fish", "water")
        self.ontology_manager.add_relation_instance("eats", "bird", "worm")
        self.ontology_manager.add_relation_instance("eats", "fish", "plankton")
        
        # Add some properties
        self.ontology_manager.add_property("color", {"type": "visual", "description": "The color of an object"})
        self.ontology_manager.add_property("weight", {"type": "physical", "description": "The weight of an object"})
        
        # Set property values
        self.ontology_manager.set_concept_property("bird", "color", "varies")
        self.ontology_manager.set_concept_property("bird", "weight", "light")
        self.ontology_manager.set_concept_property("fish", "color", "varies")
        self.ontology_manager.set_concept_property("fish", "weight", "light")
        self.ontology_manager.set_concept_property("airplane", "color", "white")
        self.ontology_manager.set_concept_property("airplane", "weight", "heavy")
    
    def test_concept_blending_workflow(self):
        """Test the complete concept blending workflow."""
        # Execute the concept creation workflow
        result = self.manager.execute_workflow("concept_creation", {
            "concept_type": "blend",
            "source_concepts": ["bird", "fish"],
            "strategy": "property_merge",
            "concept_id": "flying_fish"
        })
        
        # Check that the workflow was successful
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        
        # Get the blended concept
        blended_concept = self.ontology_manager.get_concept("flying_fish")
        self.assertIsNotNone(blended_concept)
        
        # Check that the blended concept has properties from both source concepts
        self.assertTrue(blended_concept["properties"]["lays_eggs"])
        self.assertTrue(blended_concept["properties"]["has_fins"] or blended_concept["properties"]["has_wings"])
        
        # Generate a novel concept based on the blended concept
        result = self.manager.execute_workflow("concept_creation", {
            "concept_type": "novel",
            "seed_concepts": ["flying_fish", "airplane"],
            "novelty_threshold": 0.3,
            "concept_id": "flying_submarine"
        })
        
        # Check that the workflow was successful
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        
        # Get the novel concept
        novel_concept = self.ontology_manager.get_concept("flying_submarine")
        self.assertIsNotNone(novel_concept)
        
        # Check that the novel concept has a novelty score
        self.assertIn("novelty_score", novel_concept)
        self.assertGreaterEqual(novel_concept["novelty_score"], 0.3)
    
    def test_hypothesis_generation_workflow(self):
        """Test the complete hypothesis generation workflow."""
        # Create observations
        observations = [
            {"type": "observation", "concept_id": "bird", "property": "habitat", "value": "water"},
            {"type": "observation", "concept_id": "bird", "property": "can_swim", "value": True}
        ]
        
        # Create context
        context = {
            "environment": "lake",
            "time": "morning",
            "previous_observations": [
                {"type": "observation", "concept_id": "bird", "property": "habitat", "value": "air"}
            ]
        }
        
        # Execute the hypothesis generation workflow
        result = self.manager.execute_workflow("hypothesis_generation", {
            "observations": observations,
            "context": context,
            "strategy": "abductive",
            "max_hypotheses": 3
        })
        
        # Check that the workflow was successful
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        
        # Get the generated hypotheses
        hypotheses = result["result"]["hypotheses"]
        self.assertIsNotNone(hypotheses)
        self.assertGreater(len(hypotheses), 0)
        
        # Check that the hypotheses have the expected structure
        for hypothesis in hypotheses:
            self.assertIn("id", hypothesis)
            self.assertIn("type", hypothesis)
            self.assertIn("explanation", hypothesis)
            self.assertIn("plausibility", hypothesis)
        
        # Get the most plausible hypothesis
        most_plausible = max(hypotheses, key=lambda h: h["plausibility"])
        
        # Test the hypothesis with new observations
        new_observations = [
            {"type": "observation", "concept_id": "bird", "property": "has_fins", "value": False},
            {"type": "observation", "concept_id": "bird", "property": "can_swim", "value": True}
        ]
        
        test_results = self.hypothesis_generator.test_hypothesis(most_plausible, new_observations)
        
        # Check that test results were generated
        self.assertIsNotNone(test_results)
        self.assertIn("success", test_results)
        self.assertIn("confirmation_score", test_results)
    
    def test_abstraction_hierarchy_workflow(self):
        """Test the complete abstraction hierarchy workflow."""
        # Create a hierarchy
        result = self.manager.execute_workflow("abstraction_management", {
            "operation": "create_hierarchy",
            "hierarchy_id": "animal_taxonomy",
            "hierarchy_data": {
                "name": "Animal Taxonomy",
                "description": "A hierarchical classification of animals"
            }
        })
        
        # Check that the workflow was successful
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        
        # Add some more specific animal concepts
        self.ontology_manager.add_concept("sparrow", {
            "name": "Sparrow",
            "description": "A small bird with a short bill.",
            "properties": {
                "has_feathers": True,
                "has_wings": True,
                "can_fly": True,
                "lays_eggs": True,
                "size": 1,  # Very small
                "habitat": "air",
                "species": "Passeridae"
            }
        })
        
        self.ontology_manager.add_concept("salmon", {
            "name": "Salmon",
            "description": "A fish with silver skin that lives in both fresh and salt water.",
            "properties": {
                "has_fins": True,
                "has_gills": True,
                "can_swim": True,
                "lays_eggs": True,
                "size": 3,  # Medium
                "habitat": "water",
                "species": "Salmonidae"
            }
        })
        
        # Add taxonomic relations
        self.ontology_manager.add_relation_instance("is_a", "sparrow", "bird")
        self.ontology_manager.add_relation_instance("is_a", "salmon", "fish")
        self.ontology_manager.add_relation_instance("is_a", "bird", "animal")
        self.ontology_manager.add_relation_instance("is_a", "fish", "animal")
        
        # Add concepts to hierarchy levels
        self.abstraction_hierarchy.add_concept_to_level("animal_taxonomy", "animal", 2)
        self.abstraction_hierarchy.add_concept_to_level("animal_taxonomy", "bird", 1)
        self.abstraction_hierarchy.add_concept_to_level("animal_taxonomy", "fish", 1)
        self.abstraction_hierarchy.add_concept_to_level("animal_taxonomy", "sparrow", 0)
        self.abstraction_hierarchy.add_concept_to_level("animal_taxonomy", "salmon", 0)
        
        # Add abstraction relations
        self.abstraction_hierarchy.add_abstraction_relation("animal_taxonomy", "sparrow", "bird")
        self.abstraction_hierarchy.add_abstraction_relation("animal_taxonomy", "salmon", "fish")
        self.abstraction_hierarchy.add_abstraction_relation("animal_taxonomy", "bird", "animal")
        self.abstraction_hierarchy.add_abstraction_relation("animal_taxonomy", "fish", "animal")
        
        # Generalize from instances
        result = self.manager.execute_workflow("abstraction_management", {
            "operation": "generalize",
            "instance_ids": ["sparrow", "salmon"],
            "hierarchy_id": "animal_taxonomy",
            "abstraction_level": 1
        })
        
        # Check that the workflow was successful
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        
        # Get the abstraction data
        abstraction_data = result["result"]["abstraction_data"]
        self.assertIsNotNone(abstraction_data)
        
        # Check that the abstraction has common properties
        self.assertIn("properties", abstraction_data)
        self.assertTrue(abstraction_data["properties"]["lays_eggs"])
        
        # Find appropriate level for a task
        result = self.manager.execute_workflow("abstraction_management", {
            "operation": "find_level",
            "hierarchy_id": "animal_taxonomy",
            "task_data": {"type": "high_level_overview"}
        })
        
        # Check that the workflow was successful
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
        
        # Check that the appropriate level was found
        self.assertEqual(2, result["result"]["level"])  # Should be the highest level for high_level_overview
        
        # Check hierarchy consistency
        result = self.manager.execute_workflow("abstraction_management", {
            "operation": "check_consistency",
            "hierarchy_id": "animal_taxonomy"
        })
        
        # Check that the workflow was successful
        self.assertTrue(result["success"])
        self.assertEqual("success", result["result"]["status"])
    
    def test_cross_component_integration(self):
        """Test integration between different components."""
        # Create a blended concept
        blended_concept_id = "flying_fish"
        blended_concept = self.conceptual_blender.blend_concepts(["bird", "fish"], "property_merge")
        self.ontology_manager.add_concept(blended_concept_id, blended_concept)
        
        # Create observations related to the blended concept
        observations = [
            {"type": "observation", "concept_id": blended_concept_id, "property": "habitat", "value": "both"},
            {"type": "observation", "concept_id": blended_concept_id, "property": "can_fly", "value": True},
            {"type": "observation", "concept_id": blended_concept_id, "property": "can_swim", "value": True}
        ]
        
        # Generate hypotheses about the blended concept
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            observations,
            {"environment": "coastal"},
            "abductive"
        )
        
        # Check that hypotheses were generated
        self.assertGreater(len(hypotheses), 0)
        
        # Create a hierarchy
        self.abstraction_hierarchy.create_hierarchy("animal_taxonomy", {
            "name": "Animal Taxonomy",
            "description": "A hierarchical classification of animals"
        })
        
        # Add the blended concept to the hierarchy
        self.abstraction_hierarchy.add_concept_to_level("animal_taxonomy", blended_concept_id, 1)
        
        # Add abstraction relations
        self.abstraction_hierarchy.add_abstraction_relation("animal_taxonomy", blended_concept_id, "animal")
        
        # Check that the concept is in the hierarchy
        concepts_at_level = self.abstraction_hierarchy.get_concepts_at_level("animal_taxonomy", 1)
        self.assertIn(blended_concept_id, concepts_at_level)
        
        # Get abstractions of the concept
        abstractions = self.abstraction_hierarchy.get_abstractions("animal_taxonomy", blended_concept_id)
        self.assertIn("animal", abstractions)
    
    def test_integration_with_kr_system(self):
        """Test integration with the Knowledge Representation System."""
        # Export ontology to KR system format
        kr_data = self.ontology_manager.export_to_kr_system()
        
        # Check that the export contains the expected data
        self.assertIn("concepts", kr_data)
        self.assertIn("relations", kr_data)
        self.assertIn("properties", kr_data)
        self.assertIn("relation_instances", kr_data)
        self.assertIn("property_instances", kr_data)
        
        # Modify the exported data
        kr_data["concepts"]["new_concept"] = {
            "name": "New Concept",
            "description": "A concept added via KR system integration"
        }
        
        # Import the modified data back
        result = self.ontology_manager.import_from_kr_system(kr_data)
        self.assertTrue(result)
        
        # Check that the new concept was added
        new_concept = self.ontology_manager.get_concept("new_concept")
        self.assertIsNotNone(new_concept)
        self.assertEqual("New Concept", new_concept["name"])
    
    def test_integration_with_metacognition_system(self):
        """Test integration with the Metacognition System."""
        # This is a simplified simulation of interaction with the Metacognition System
        
        # Create a mock metacognition system that requests concept creation
        metacognition_request = {
            "operation": "create_concept",
            "parameters": {
                "concept_type": "blend",
                "source_concepts": ["bird", "airplane"],
                "strategy": "structure_mapping"
            }
        }
        
        # Process the request
        if metacognition_request["operation"] == "create_concept":
            params = metacognition_request["parameters"]
            
            # Execute the concept creation workflow
            result = self.manager.execute_workflow("concept_creation", {
                "concept_type": params["concept_type"],
                "source_concepts": params["source_concepts"],
                "strategy": params["strategy"],
                "concept_id": "meta_requested_concept"
            })
            
            # Check that the workflow was successful
            self.assertTrue(result["success"])
            self.assertEqual("success", result["result"]["status"])
            
            # Get the created concept
            concept = self.ontology_manager.get_concept("meta_requested_concept")
            self.assertIsNotNone(concept)
            
            # Prepare a response for the metacognition system
            metacognition_response = {
                "status": "success",
                "concept_id": "meta_requested_concept",
                "concept_data": concept
            }
            
            # Check that the response contains the expected data
            self.assertEqual("success", metacognition_response["status"])
            self.assertEqual("meta_requested_concept", metacognition_response["concept_id"])
            self.assertIsNotNone(metacognition_response["concept_data"])

if __name__ == "__main__":
    unittest.main()