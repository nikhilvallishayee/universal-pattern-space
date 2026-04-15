"""
Unit tests for the ConceptualBlender component.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.ontology.conceptual_blender import ConceptualBlender
from godelOS.ontology.ontology_manager import OntologyManager

class TestConceptualBlender(unittest.TestCase):
    """Test cases for the ConceptualBlender."""
    
    def setUp(self):
        """Set up test fixtures."""
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
        
        # Add relation instances
        self.ontology_manager.add_relation_instance("lives_in", "bird", "air")
        self.ontology_manager.add_relation_instance("lives_in", "fish", "water")
        self.ontology_manager.add_relation_instance("eats", "bird", "worm")
        self.ontology_manager.add_relation_instance("eats", "fish", "plankton")
    
    def test_blend_concepts_property_merge(self):
        """Test blending concepts using property merge strategy."""
        # Blend bird and fish
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge")
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        self.assertEqual("property_merge", blended_concept["blend_strategy"])
        
        # Check that common properties were preserved
        self.assertTrue(blended_concept["properties"]["lays_eggs"])
        self.assertEqual(2, blended_concept["properties"]["size"])
        
        # Check that conflicting properties were handled
        self.assertIn("habitat", blended_concept["properties"])
        
        # Check that source concepts were recorded
        self.assertIn("bird", blended_concept["source_concepts"])
        self.assertIn("fish", blended_concept["source_concepts"])
    
    def test_blend_concepts_structure_mapping(self):
        """Test blending concepts using structure mapping strategy."""
        # Blend bird and airplane
        blended_concept = self.blender.blend_concepts(["bird", "airplane"], "structure_mapping")
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        self.assertEqual("structure_mapping", blended_concept["blend_strategy"])
        
        # Check that common structural elements were preserved
        self.assertTrue(blended_concept["properties"]["has_wings"])
        self.assertTrue(blended_concept["properties"]["can_fly"])
        
        # Check that source concepts were recorded
        self.assertIn("bird", blended_concept["source_concepts"])
        self.assertIn("airplane", blended_concept["source_concepts"])
    
    def test_blend_concepts_with_constraints(self):
        """Test blending concepts with constraints."""
        # Create constraints to exclude certain properties
        constraints = {
            "excluded_properties": ["habitat"],
            "excluded_relations": ["eats"]
        }
        
        # Blend bird and fish with constraints
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge", constraints)
        
        # Check that the blend was created
        self.assertIsNotNone(blended_concept)
        
        # Check that excluded properties were not included
        self.assertNotIn("habitat", blended_concept["properties"])
        
        # Check that excluded relations were not included
        for relation in blended_concept["relations"]:
            self.assertNotEqual("eats", relation["relation_id"])
    
    def test_blend_concepts_invalid_inputs(self):
        """Test blending concepts with invalid inputs."""
        # Test with less than 2 concepts
        blended_concept = self.blender.blend_concepts(["bird"], "property_merge")
        self.assertIsNone(blended_concept)
        
        # Test with non-existent concepts
        blended_concept = self.blender.blend_concepts(["bird", "nonexistent"], "property_merge")
        self.assertIsNone(blended_concept)
        
        # Test with invalid strategy
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "invalid_strategy")
        self.assertIsNone(blended_concept)
    
    def test_blend_caching(self):
        """Test that blends are cached."""
        # Blend bird and fish
        blended_concept1 = self.blender.blend_concepts(["bird", "fish"], "property_merge")
        
        # Blend the same concepts again
        blended_concept2 = self.blender.blend_concepts(["bird", "fish"], "property_merge")
        
        # Check that the same blend was returned
        self.assertEqual(blended_concept1, blended_concept2)
        
        # Check cache directly
        cache_key = (tuple(sorted(["bird", "fish"])), "property_merge", str({}))
        self.assertIn(cache_key, self.blender._blend_cache)
        self.assertEqual(blended_concept1, self.blender._blend_cache[cache_key])
    
    def test_create_analogy(self):
        """Test creating an analogy between concepts."""
        # Create an analogy between bird and airplane
        analogy = self.blender.create_analogy("bird", "airplane", "structure_mapping")
        
        # Check that the analogy was created
        self.assertIsNotNone(analogy)
        self.assertEqual("bird", analogy["source_id"])
        self.assertEqual("airplane", analogy["target_id"])
        self.assertEqual("structure_mapping", analogy["strategy"])
        
        # Check that correspondences were found
        self.assertIn("correspondences", analogy)
    
    def test_create_analogy_invalid_inputs(self):
        """Test creating an analogy with invalid inputs."""
        # Test with non-existent source
        analogy = self.blender.create_analogy("nonexistent", "airplane", "structure_mapping")
        self.assertIsNone(analogy)
        
        # Test with non-existent target
        analogy = self.blender.create_analogy("bird", "nonexistent", "structure_mapping")
        self.assertIsNone(analogy)
        
        # Test with invalid strategy
        analogy = self.blender.create_analogy("bird", "airplane", "invalid_strategy")
        self.assertIsNone(analogy)
    
    def test_analogy_caching(self):
        """Test that analogies are cached."""
        # Create an analogy
        analogy1 = self.blender.create_analogy("bird", "airplane", "structure_mapping")
        
        # Create the same analogy again
        analogy2 = self.blender.create_analogy("bird", "airplane", "structure_mapping")
        
        # Check that the same analogy was returned
        self.assertEqual(analogy1, analogy2)
        
        # Check cache directly
        cache_key = ("bird", "airplane", "structure_mapping", str({}))
        self.assertIn(cache_key, self.blender._analogy_cache)
        self.assertEqual(analogy1, self.blender._analogy_cache[cache_key])
    
    def test_detect_novelty(self):
        """Test detecting novelty of a concept."""
        # Create a blended concept
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge")
        
        # Detect novelty
        novelty_score = self.blender.detect_novelty(blended_concept)
        
        # Check that a novelty score was returned
        self.assertIsNotNone(novelty_score)
        self.assertGreaterEqual(novelty_score, 0.0)
        self.assertLessEqual(novelty_score, 1.0)
    
    def test_generate_novel_concept(self):
        """Test generating a novel concept."""
        # Generate a novel concept
        novel_concept = self.blender.generate_novel_concept(["bird", "fish"], 0.3)
        
        # Check that a novel concept was generated
        self.assertIsNotNone(novel_concept)
        self.assertIn("novelty_score", novel_concept)
        self.assertGreaterEqual(novel_concept["novelty_score"], 0.3)
    
    def test_evaluate_concept_utility(self):
        """Test evaluating the utility of a concept."""
        # Create a blended concept
        blended_concept = self.blender.blend_concepts(["bird", "fish"], "property_merge")
        
        # Evaluate utility
        utility_score = self.blender.evaluate_concept_utility(blended_concept)
        
        # Check that a utility score was returned
        self.assertIsNotNone(utility_score)
        self.assertGreaterEqual(utility_score, 0.0)
        self.assertLessEqual(utility_score, 1.0)
    
    def test_helper_methods(self):
        """Test helper methods of the ConceptualBlender."""
        # Test _generate_blend_name
        concepts = [
            {"name": "Bird"},
            {"name": "Fish"}
        ]
        name = self.blender._generate_blend_name(concepts)
        self.assertIsNotNone(name)
        self.assertIn("Bir", name)
        self.assertIn("Fis", name)
        
        # Test _get_concept_properties
        properties = self.blender._get_concept_properties("bird")
        self.assertIsNotNone(properties)
        self.assertIn("has_feathers", properties)
        self.assertTrue(properties["has_feathers"])
        
        # Test _find_structural_correspondences
        correspondences = self.blender._find_structural_correspondences("bird", "airplane")
        self.assertIsNotNone(correspondences)
        self.assertIn("concepts", correspondences)
        self.assertIn("relations", correspondences)
        self.assertIn("properties", correspondences)
        
        # Test _generate_random_constraints
        constraints = self.blender._generate_random_constraints(["bird", "fish"])
        self.assertIsNotNone(constraints)
        self.assertIn("excluded_properties", constraints)
        self.assertIn("excluded_relations", constraints)

if __name__ == "__main__":
    unittest.main()