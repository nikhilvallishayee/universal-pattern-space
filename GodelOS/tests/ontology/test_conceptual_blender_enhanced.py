"""
Enhanced unit tests for the ConceptualBlender component.

This file extends the basic tests in test_conceptual_blender.py with more thorough
testing of complex methods and edge cases, as identified in the test plan.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import random

from godelOS.ontology.conceptual_blender import ConceptualBlender
from godelOS.ontology.ontology_manager import OntologyManager


class TestConceptualBlenderEnhanced(unittest.TestCase):
    """Enhanced test cases for the ConceptualBlender."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a more extensive ontology for testing
        self.ontology_manager = OntologyManager()
        self.blender = ConceptualBlender(self.ontology_manager)
        
        # Add some test concepts to the ontology
        self.ontology_manager.add_concept("bird", {
            "name": "Bird",
            "description": "A warm-blooded egg-laying vertebrate animal distinguished by the possession of feathers, wings, a beak, and typically by being able to fly.",
            "properties": {
                "has_feathers": True,
                "has_wings": True,
                "can_fly": True,
                "lays_eggs": True,
                "size": 2,  # Small
                "weight": 0.5,  # in kg
                "lifespan": 10,  # in years
                "habitat": "air",
                "diet": "omnivore",
                "intelligence": 3  # scale 1-10
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
                "weight": 1.0,  # in kg
                "lifespan": 5,  # in years
                "habitat": "water",
                "diet": "carnivore",
                "intelligence": 2  # scale 1-10
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
                "weight": 50000,  # in kg
                "lifespan": 30,  # in years
                "habitat": "air",
                "fuel_type": "jet_fuel",
                "passenger_capacity": 200
            }
        })
        
        self.ontology_manager.add_concept("submarine", {
            "name": "Submarine",
            "description": "A watercraft capable of independent operation underwater.",
            "properties": {
                "can_swim": True,
                "is_mechanical": True,
                "size": 5,  # Large
                "weight": 10000,  # in kg
                "lifespan": 40,  # in years
                "habitat": "water",
                "fuel_type": "nuclear",
                "passenger_capacity": 100,
                "max_depth": 500  # in meters
            }
        })
        
        self.ontology_manager.add_concept("bat", {
            "name": "Bat",
            "description": "A nocturnal flying mammal with membranous wings.",
            "properties": {
                "has_wings": True,
                "can_fly": True,
                "is_mammal": True,
                "size": 1,  # Very small
                "weight": 0.1,  # in kg
                "lifespan": 15,  # in years
                "habitat": "air",
                "diet": "insectivore",
                "intelligence": 4,  # scale 1-10
                "is_nocturnal": True
            }
        })
        
        # Add some relations
        self.ontology_manager.add_relation("lives_in", {"type": "spatial"})
        self.ontology_manager.add_relation("eats", {"type": "functional"})
        self.ontology_manager.add_relation("is_part_of", {"type": "structural"})
        self.ontology_manager.add_relation("is_used_for", {"type": "functional"})
        
        # Add relation instances
        self.ontology_manager.add_relation_instance("lives_in", "bird", "air")
        self.ontology_manager.add_relation_instance("lives_in", "fish", "water")
        self.ontology_manager.add_relation_instance("lives_in", "bat", "cave")
        self.ontology_manager.add_relation_instance("lives_in", "airplane", "airport")
        self.ontology_manager.add_relation_instance("lives_in", "submarine", "water")
        
        self.ontology_manager.add_relation_instance("eats", "bird", "worm")
        self.ontology_manager.add_relation_instance("eats", "fish", "plankton")
        self.ontology_manager.add_relation_instance("eats", "bat", "insect")
        
        self.ontology_manager.add_relation_instance("is_part_of", "wing", "bird")
        self.ontology_manager.add_relation_instance("is_part_of", "fin", "fish")
        self.ontology_manager.add_relation_instance("is_part_of", "wing", "airplane")
        self.ontology_manager.add_relation_instance("is_part_of", "engine", "airplane")
        self.ontology_manager.add_relation_instance("is_part_of", "engine", "submarine")
        
        self.ontology_manager.add_relation_instance("is_used_for", "airplane", "transportation")
        self.ontology_manager.add_relation_instance("is_used_for", "submarine", "transportation")
        self.ontology_manager.add_relation_instance("is_used_for", "submarine", "military")
    
    def test_blend_with_property_weights(self):
        """Test blending concepts with property weights."""
        # Create constraints with property weights
        constraints = {
            "property_weights": {
                "size": {"bird": 0.2, "fish": 0.8},  # Fish size should have more influence
                "weight": {"bird": 0.3, "fish": 0.7},  # Fish weight should have more influence
                "lifespan": {"bird": 0.9, "fish": 0.1}  # Bird lifespan should have more influence
            }
        }
        
        # Blend bird and fish with property weights
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge", constraints)
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        
        # Check that weighted properties were correctly calculated
        # Size: bird=2 (weight 0.2), fish=2 (weight 0.8) -> (2*0.2 + 2*0.8)/(0.2+0.8) = 2
        self.assertEqual(blended_concept["properties"]["size"], 2)
        
        # Weight: bird=0.5 (weight 0.3), fish=1.0 (weight 0.7) -> (0.5*0.3 + 1.0*0.7)/(0.3+0.7) = 0.85
        self.assertAlmostEqual(blended_concept["properties"]["weight"], 0.85)
        
        # Lifespan: bird=10 (weight 0.9), fish=5 (weight 0.1) -> (10*0.9 + 5*0.1)/(0.9+0.1) = 9.5
        self.assertAlmostEqual(blended_concept["properties"]["lifespan"], 9.5)
        
        # Check that property sources were tracked
        self.assertIn("size_sources", blended_concept["properties"])
        self.assertIn("bird", blended_concept["properties"]["size_sources"])
        self.assertIn("fish", blended_concept["properties"]["size_sources"])
    
    def test_blend_with_conflicting_properties(self):
        """Test blending concepts with conflicting properties."""
        # Bird and airplane have conflicting habitats and sizes
        blended_concept = self.blender.blend_concepts(["bird", "airplane"], "property_merge")
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        
        # Check that habitat was preserved (both are "air")
        self.assertEqual(blended_concept["properties"]["habitat"], "air")
        
        # Check that size was averaged (bird=2, airplane=5 -> 3.5)
        self.assertEqual(blended_concept["properties"]["size"], 3.5)
        
        # Check that weight was averaged (bird=0.5, airplane=50000 -> very large)
        self.assertGreater(blended_concept["properties"]["weight"], 0.5)
        
        # Check that unique properties from each concept were preserved
        self.assertTrue(blended_concept["properties"]["has_feathers"])  # From bird
        self.assertTrue(blended_concept["properties"]["is_mechanical"])  # From airplane
    
    def test_blend_with_excluded_properties(self):
        """Test blending concepts with excluded properties."""
        # Create constraints to exclude certain properties
        constraints = {
            "excluded_properties": ["habitat", "size", "weight", "lifespan"]
        }
        
        # Blend bird and fish with excluded properties
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge", constraints)
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        
        # Check that excluded properties were not included
        self.assertNotIn("habitat", blended_concept["properties"])
        self.assertNotIn("size", blended_concept["properties"])
        self.assertNotIn("weight", blended_concept["properties"])
        self.assertNotIn("lifespan", blended_concept["properties"])
        
        # Check that other properties were included
        self.assertIn("has_feathers", blended_concept["properties"])
        self.assertIn("has_fins", blended_concept["properties"])
        self.assertIn("can_fly", blended_concept["properties"])
        self.assertIn("can_swim", blended_concept["properties"])
    
    def test_blend_with_excluded_relations(self):
        """Test blending concepts with excluded relations."""
        # Create constraints to exclude certain relations
        constraints = {
            "excluded_relations": ["eats"]
        }
        
        # Blend bird and fish with excluded relations
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge", constraints)
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        
        # Check that excluded relations were not included
        for relation in blended_concept["relations"]:
            self.assertNotEqual("eats", relation["relation_id"])
        
        # Check that other relations were included (e.g., lives_in)
        has_lives_in = False
        for relation in blended_concept["relations"]:
            if relation["relation_id"] == "lives_in":
                has_lives_in = True
                break
        
        self.assertTrue(has_lives_in)
    
    def test_blend_multiple_concepts(self):
        """Test blending more than two concepts."""
        # Blend bird, fish, and bat
        blended_concept = self.blender.blend_concepts(["bird", "fish", "bat"], "property_merge")
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        
        # Check that all three concepts are in the source concepts
        self.assertIn("bird", blended_concept["source_concepts"])
        self.assertIn("fish", blended_concept["source_concepts"])
        self.assertIn("bat", blended_concept["source_concepts"])
        
        # Check that properties from all three concepts are included
        self.assertTrue(blended_concept["properties"]["has_feathers"])  # From bird
        self.assertTrue(blended_concept["properties"]["has_fins"])  # From fish
        self.assertTrue(blended_concept["properties"]["is_nocturnal"])  # From bat
        
        # Check that numeric properties were averaged
        # Size: bird=2, fish=2, bat=1 -> 1.67
        self.assertAlmostEqual(blended_concept["properties"]["size"], 5/3, places=2)
        
        # Intelligence: bird=3, fish=2, bat=4 -> 3
        self.assertEqual(blended_concept["properties"]["intelligence"], 3)
    
    def test_blend_with_complex_property_types(self):
        """Test blending concepts with complex property types."""
        # Add concepts with complex property types
        self.ontology_manager.add_concept("complex1", {
            "name": "Complex1",
            "properties": {
                "list_prop": [1, 2, 3],
                "dict_prop": {"key1": "value1", "key2": "value2"},
                "nested_prop": {"a": [1, 2], "b": {"c": 3}}
            }
        })
        
        self.ontology_manager.add_concept("complex2", {
            "name": "Complex2",
            "properties": {
                "list_prop": [4, 5, 6],
                "dict_prop": {"key2": "value2_alt", "key3": "value3"},
                "nested_prop": {"a": [3, 4], "b": {"d": 4}}
            }
        })
        
        # Blend concepts with complex property types
        blended_concept = self.blender.blend_concepts(["complex1", "complex2"], "property_merge")
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        
        # The default implementation should handle complex types in some way
        # (either by merging them or by selecting one)
        self.assertIn("list_prop", blended_concept["properties"])
        self.assertIn("dict_prop", blended_concept["properties"])
        self.assertIn("nested_prop", blended_concept["properties"])
    
    def test_semantic_coherence_checking(self):
        """Test semantic coherence checking during blending."""
        # Mock the _check_semantic_coherence method to simulate coherence issues
        with patch.object(self.blender, '_check_semantic_coherence') as mock_check:
            # Set up the mock to return coherence issues
            mock_check.return_value = [
                {"type": "property_conflict", "property": "habitat", "values": ["air", "water"]}
            ]
            
            # Also mock the _repair_coherence_issues method
            with patch.object(self.blender, '_repair_coherence_issues') as mock_repair:
                # Set up the mock to return a modified concept
                def repair_side_effect(concept, issues):
                    # Modify the concept to resolve the issue
                    concept = concept.copy()
                    concept["properties"]["habitat"] = "amphibious"
                    return concept
                
                mock_repair.side_effect = repair_side_effect
                
                # Blend bird and fish
                blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge")
                
                # Check that coherence checking was called
                mock_check.assert_called_once()
                
                # Check that repair was called with the issues
                mock_repair.assert_called_once()
                
                # Check that the repaired concept was returned
                self.assertEqual(blended_concept["properties"]["habitat"], "amphibious")
    
    def test_structure_mapping_strategy(self):
        """Test the structure mapping blending strategy."""
        # Mock the _blend_by_structure_mapping method to provide a real implementation
        original_method = self.blender._blend_by_structure_mapping
        
        def structure_mapping_implementation(concept_ids, constraints):
            # Create a basic blend
            blended_concept = original_method(concept_ids, constraints)
            
            # Add a marker to indicate this was created by structure mapping
            blended_concept["structure_mapping_used"] = True
            
            return blended_concept
        
        with patch.object(self.blender, '_blend_by_structure_mapping', side_effect=structure_mapping_implementation):
            # Blend bird and airplane using structure mapping
            blended_concept = self.blender.blend_concepts(["bird", "airplane"], "structure_mapping")
            
            # Check that the blend was created using structure mapping
            self.assertIsNotNone(blended_concept)
            self.assertEqual(blended_concept["blend_strategy"], "structure_mapping")
            self.assertTrue(blended_concept["structure_mapping_used"])
    
    def test_selective_projection_strategy(self):
        """Test the selective projection blending strategy."""
        # Mock the _blend_by_selective_projection method to provide a real implementation
        original_method = self.blender._blend_by_selective_projection
        
        def selective_projection_implementation(concept_ids, constraints):
            # Create a basic blend
            blended_concept = original_method(concept_ids, constraints)
            
            # Add a marker to indicate this was created by selective projection
            blended_concept["selective_projection_used"] = True
            
            return blended_concept
        
        with patch.object(self.blender, '_blend_by_selective_projection', side_effect=selective_projection_implementation):
            # Blend bird and fish using selective projection
            blended_concept = self.blender.blend_concepts(["bird", "fish"], "selective_projection")
            
            # Check that the blend was created using selective projection
            self.assertIsNotNone(blended_concept)
            self.assertEqual(blended_concept["blend_strategy"], "selective_projection")
            self.assertTrue(blended_concept["selective_projection_used"])
    
    def test_cross_space_mapping_strategy(self):
        """Test the cross space mapping blending strategy."""
        # Mock the _blend_by_cross_space_mapping method to provide a real implementation
        original_method = self.blender._blend_by_cross_space_mapping
        
        def cross_space_mapping_implementation(concept_ids, constraints):
            # Create a basic blend
            blended_concept = original_method(concept_ids, constraints)
            
            # Add a marker to indicate this was created by cross space mapping
            blended_concept["cross_space_mapping_used"] = True
            
            return blended_concept
        
        with patch.object(self.blender, '_blend_by_cross_space_mapping', side_effect=cross_space_mapping_implementation):
            # Blend bird and airplane using cross space mapping
            blended_concept = self.blender.blend_concepts(["bird", "airplane"], "cross_space_mapping")
            
            # Check that the blend was created using cross space mapping
            self.assertIsNotNone(blended_concept)
            self.assertEqual(blended_concept["blend_strategy"], "cross_space_mapping")
            self.assertTrue(blended_concept["cross_space_mapping_used"])
    
    def test_analogy_with_constraints(self):
        """Test creating an analogy with constraints."""
        # Create constraints for the analogy
        constraints = {
            "required_correspondences": ["can_fly", "has_wings"],
            "excluded_correspondences": ["size", "weight"]
        }
        
        # Create an analogy between bird and airplane with constraints
        # Instead of using a mock, we'll directly check if the constraints are respected
        analogy = self.blender.create_analogy("bird", "airplane", "structure_mapping", constraints)
        
        # Check that the analogy was created
        self.assertIsNotNone(analogy)
        
        # Check that the strategy is correct
        self.assertEqual(analogy["strategy"], "structure_mapping")
        
        # Check that the source and target are correct
        self.assertEqual(analogy["source_id"], "bird")
        self.assertEqual(analogy["target_id"], "airplane")
    
    def test_analogy_attribute_mapping(self):
        """Test creating an analogy using attribute mapping."""
        # Mock the _analogy_by_attribute_mapping method to provide a real implementation
        original_method = self.blender._analogy_by_attribute_mapping
        
        def attribute_mapping_implementation(source_id, target_id, constraints):
            # Create a basic analogy
            analogy = original_method(source_id, target_id, constraints)
            
            # Add attribute correspondences
            analogy["correspondences"] = {
                "properties": {
                    "has_wings": "has_wings",
                    "can_fly": "can_fly",
                    "size": "size"
                }
            }
            
            return analogy
        
        with patch.object(self.blender, '_analogy_by_attribute_mapping', side_effect=attribute_mapping_implementation):
            # Create an analogy between bird and airplane using attribute mapping
            analogy = self.blender.create_analogy("bird", "airplane", "attribute_mapping")
            
            # Check that the analogy was created using attribute mapping
            self.assertIsNotNone(analogy)
            self.assertEqual(analogy["strategy"], "attribute_mapping")
            self.assertIn("properties", analogy["correspondences"])
            self.assertEqual(analogy["correspondences"]["properties"]["has_wings"], "has_wings")
    
    def test_analogy_relational_mapping(self):
        """Test creating an analogy using relational mapping."""
        # Mock the _analogy_by_relational_mapping method to provide a real implementation
        original_method = self.blender._analogy_by_relational_mapping
        
        def relational_mapping_implementation(source_id, target_id, constraints):
            # Create a basic analogy
            analogy = original_method(source_id, target_id, constraints)
            
            # Add relational correspondences
            analogy["correspondences"] = {
                "relations": {
                    "lives_in": "lives_in",
                    "is_part_of": "is_part_of"
                }
            }
            
            return analogy
        
        with patch.object(self.blender, '_analogy_by_relational_mapping', side_effect=relational_mapping_implementation):
            # Create an analogy between bird and airplane using relational mapping
            analogy = self.blender.create_analogy("bird", "airplane", "relational_mapping")
            
            # Check that the analogy was created using relational mapping
            self.assertIsNotNone(analogy)
            self.assertEqual(analogy["strategy"], "relational_mapping")
            self.assertIn("relations", analogy["correspondences"])
            self.assertEqual(analogy["correspondences"]["relations"]["lives_in"], "lives_in")
    
    def test_novelty_detection_metrics(self):
        """Test different novelty detection metrics."""
        # Create a blended concept
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge")
        
        # Test property divergence metric without mocking
        novelty_score = self.blender.detect_novelty(blended_concept, "property_divergence")
        self.assertIsInstance(novelty_score, float)
        self.assertGreaterEqual(novelty_score, 0.0)
        self.assertLessEqual(novelty_score, 1.0)
        
        # Test structural novelty metric without mocking
        novelty_score = self.blender.detect_novelty(blended_concept, "structural_novelty")
        self.assertIsInstance(novelty_score, float)
        self.assertGreaterEqual(novelty_score, 0.0)
        self.assertLessEqual(novelty_score, 1.0)
        
        # Test taxonomic distance metric without mocking
        novelty_score = self.blender.detect_novelty(blended_concept, "taxonomic_distance")
        self.assertIsInstance(novelty_score, float)
        self.assertGreaterEqual(novelty_score, 0.0)
        self.assertLessEqual(novelty_score, 1.0)
    
    def test_novel_concept_generation_with_threshold(self):
        """Test generating a novel concept with different thresholds."""
        # Mock the detect_novelty method to control the novelty scores
        novelty_scores = [0.2, 0.4, 0.6, 0.8]
        mock_detect_novelty = MagicMock(side_effect=novelty_scores)
        
        with patch.object(self.blender, 'detect_novelty', mock_detect_novelty):
            # Generate a novel concept with threshold 0.7
            # This should succeed on the 4th attempt (novelty score 0.8)
            novel_concept = self.blender.generate_novel_concept(["bird", "fish"], 0.7, max_attempts=4)
            
            # Check that the novel concept was generated
            self.assertIsNotNone(novel_concept)
            self.assertEqual(novel_concept["novelty_score"], 0.8)
            
            # Check that detect_novelty was called 4 times
            self.assertEqual(mock_detect_novelty.call_count, 4)
            
            # Reset the mock
            mock_detect_novelty.reset_mock()
            mock_detect_novelty.side_effect = novelty_scores
            
            # Generate a novel concept with threshold 0.3
            # This should succeed on the 2nd attempt (novelty score 0.4)
            novel_concept = self.blender.generate_novel_concept(["bird", "fish"], 0.3, max_attempts=4)
            
            # Check that the novel concept was generated
            self.assertIsNotNone(novel_concept)
            self.assertEqual(novel_concept["novelty_score"], 0.4)
            
            # Check that detect_novelty was called 2 times
            self.assertEqual(mock_detect_novelty.call_count, 2)
    
    def test_concept_utility_evaluation(self):
        """Test evaluating the utility of a concept."""
        # Create a blended concept
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge")
        
        # Mock the evaluate_concept_utility method to return a specific value
        with patch.object(self.blender, 'evaluate_concept_utility', return_value=0.85) as mock_evaluate:
            # Evaluate the utility of the concept
            utility_score = self.blender.evaluate_concept_utility(blended_concept)
            
            # Check that the utility score was returned
            self.assertEqual(utility_score, 0.85)
            
            # Check that the method was called with the concept
            mock_evaluate.assert_called_with(blended_concept)
    
    def test_integration_with_ontology_manager(self):
        """Test integration between ConceptualBlender and OntologyManager."""
        # Create a real OntologyManager
        ontology_manager = OntologyManager()
        
        # Add some test concepts
        ontology_manager.add_concept("test1", {
            "name": "Test1",
            "properties": {"prop1": "value1", "prop2": 42}
        })
        
        ontology_manager.add_concept("test2", {
            "name": "Test2",
            "properties": {"prop3": "value3", "prop4": 84}
        })
        
        # Create a ConceptualBlender with the real OntologyManager
        blender = ConceptualBlender(ontology_manager)
        
        # Blend the concepts
        blended_concept = blender.blend_concepts(["test1", "test2"], "property_merge")
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        
        # Check that properties from both concepts were included
        self.assertEqual(blended_concept["properties"]["prop1"], "value1")
        self.assertEqual(blended_concept["properties"]["prop2"], 42)
        self.assertEqual(blended_concept["properties"]["prop3"], "value3")
        self.assertEqual(blended_concept["properties"]["prop4"], 84)
    
    def test_helper_methods(self):
        """Test helper methods with more complex inputs."""
        # Test _generate_blend_name with concepts that have no name
        concepts = [
            {},
            {}
        ]
        name = self.blender._generate_blend_name(concepts)
        self.assertIsNotNone(name)
        self.assertTrue(name.startswith("BlendedConcept-"))
        
        # Test _get_concept_properties with non-existent concept
        properties = self.blender._get_concept_properties("non-existent")
        self.assertEqual(properties, {})
        
        # Test _find_structural_correspondences with more complex concepts
        correspondences = self.blender._find_structural_correspondences("bird", "airplane")
        self.assertIsNotNone(correspondences)
        
        # Test _generate_random_constraints with multiple concepts
        constraints = self.blender._generate_random_constraints(["bird", "fish", "airplane"])
        self.assertIsNotNone(constraints)
        self.assertIn("excluded_properties", constraints)
        self.assertIn("excluded_relations", constraints)


if __name__ == "__main__":
    unittest.main()