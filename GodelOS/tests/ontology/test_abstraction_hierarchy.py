"""
Unit tests for the AbstractionHierarchyModule component.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.ontology.abstraction_hierarchy import AbstractionHierarchyModule
from godelOS.ontology.ontology_manager import OntologyManager

class TestAbstractionHierarchyModule(unittest.TestCase):
    """Test cases for the AbstractionHierarchyModule."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ontology_manager = OntologyManager()
        self.ahm = AbstractionHierarchyModule(self.ontology_manager)
        
        # Add some test concepts to the ontology
        self.ontology_manager.add_concept("animal", {
            "name": "Animal",
            "description": "A living organism that feeds on organic matter.",
            "properties": {
                "alive": True,
                "mobile": True,
                "sentient": True
            }
        })
        
        self.ontology_manager.add_concept("mammal", {
            "name": "Mammal",
            "description": "A warm-blooded vertebrate animal characterized by the possession of hair or fur.",
            "properties": {
                "alive": True,
                "mobile": True,
                "sentient": True,
                "warm_blooded": True,
                "has_hair": True,
                "produces_milk": True
            }
        })
        
        self.ontology_manager.add_concept("dog", {
            "name": "Dog",
            "description": "A domesticated carnivorous mammal.",
            "properties": {
                "alive": True,
                "mobile": True,
                "sentient": True,
                "warm_blooded": True,
                "has_hair": True,
                "produces_milk": True,
                "barks": True,
                "loyal": True,
                "domesticated": True
            }
        })
        
        self.ontology_manager.add_concept("cat", {
            "name": "Cat",
            "description": "A small domesticated carnivorous mammal.",
            "properties": {
                "alive": True,
                "mobile": True,
                "sentient": True,
                "warm_blooded": True,
                "has_hair": True,
                "produces_milk": True,
                "meows": True,
                "independent": True,
                "domesticated": True
            }
        })
        
        # Create a test hierarchy
        self.ahm.create_hierarchy("taxonomy", {
            "name": "Taxonomic Hierarchy",
            "description": "A hierarchy based on biological taxonomy"
        })
    
    def test_create_hierarchy(self):
        """Test creating a hierarchy."""
        # Test creating a new hierarchy
        result = self.ahm.create_hierarchy("new_hierarchy", {
            "name": "New Hierarchy",
            "description": "A new test hierarchy"
        })
        self.assertTrue(result)
        self.assertIn("new_hierarchy", self.ahm._hierarchies)
        
        # Test creating an existing hierarchy
        result = self.ahm.create_hierarchy("taxonomy", {
            "name": "Duplicate Hierarchy",
            "description": "This should fail"
        })
        self.assertFalse(result)
    
    def test_delete_hierarchy(self):
        """Test deleting a hierarchy."""
        # Test deleting an existing hierarchy
        result = self.ahm.delete_hierarchy("taxonomy")
        self.assertTrue(result)
        self.assertNotIn("taxonomy", self.ahm._hierarchies)
        
        # Test deleting a non-existent hierarchy
        result = self.ahm.delete_hierarchy("nonexistent")
        self.assertFalse(result)
    
    def test_get_hierarchy(self):
        """Test retrieving a hierarchy."""
        # Test retrieving an existing hierarchy
        hierarchy = self.ahm.get_hierarchy("taxonomy")
        self.assertIsNotNone(hierarchy)
        self.assertEqual("Taxonomic Hierarchy", hierarchy["name"])
        
        # Test retrieving a non-existent hierarchy
        hierarchy = self.ahm.get_hierarchy("nonexistent")
        self.assertIsNone(hierarchy)
    
    def test_get_all_hierarchies(self):
        """Test retrieving all hierarchies."""
        # Add another hierarchy
        self.ahm.create_hierarchy("another", {
            "name": "Another Hierarchy",
            "description": "Another test hierarchy"
        })
        
        # Test retrieving all hierarchies
        hierarchies = self.ahm.get_all_hierarchies()
        self.assertEqual(2, len(hierarchies))
        self.assertIn("taxonomy", hierarchies)
        self.assertIn("another", hierarchies)
    
    def test_add_concept_to_level(self):
        """Test adding a concept to a level."""
        # Test adding a concept to a level
        result = self.ahm.add_concept_to_level("taxonomy", "animal", 2)
        self.assertTrue(result)
        self.assertIn("animal", self.ahm._abstraction_levels["taxonomy"][2])
        
        # Test adding to a non-existent hierarchy
        result = self.ahm.add_concept_to_level("nonexistent", "animal", 2)
        self.assertFalse(result)
        
        # Test adding a non-existent concept
        result = self.ahm.add_concept_to_level("taxonomy", "nonexistent", 2)
        self.assertFalse(result)
    
    def test_remove_concept_from_level(self):
        """Test removing a concept from a level."""
        # Add a concept to a level first
        self.ahm.add_concept_to_level("taxonomy", "animal", 2)
        
        # Test removing the concept
        result = self.ahm.remove_concept_from_level("taxonomy", "animal", 2)
        self.assertTrue(result)
        self.assertNotIn("animal", self.ahm._abstraction_levels["taxonomy"].get(2, set()))
        
        # Test removing from a non-existent hierarchy
        result = self.ahm.remove_concept_from_level("nonexistent", "animal", 2)
        self.assertFalse(result)
        
        # Test removing from a non-existent level
        result = self.ahm.remove_concept_from_level("taxonomy", "animal", 999)
        self.assertFalse(result)
        
        # Test removing a non-existent concept
        self.ahm.add_concept_to_level("taxonomy", "animal", 2)
        result = self.ahm.remove_concept_from_level("taxonomy", "nonexistent", 2)
        self.assertFalse(result)
    
    def test_get_concepts_at_level(self):
        """Test retrieving concepts at a level."""
        # Add some concepts to levels
        self.ahm.add_concept_to_level("taxonomy", "animal", 2)
        self.ahm.add_concept_to_level("taxonomy", "mammal", 1)
        self.ahm.add_concept_to_level("taxonomy", "dog", 0)
        self.ahm.add_concept_to_level("taxonomy", "cat", 0)
        
        # Test retrieving concepts at a level
        concepts = self.ahm.get_concepts_at_level("taxonomy", 0)
        self.assertEqual(2, len(concepts))
        self.assertIn("dog", concepts)
        self.assertIn("cat", concepts)
        
        # Test retrieving from a non-existent hierarchy
        concepts = self.ahm.get_concepts_at_level("nonexistent", 0)
        self.assertEqual(0, len(concepts))
        
        # Test retrieving from a non-existent level
        concepts = self.ahm.get_concepts_at_level("taxonomy", 999)
        self.assertEqual(0, len(concepts))
    
    def test_get_concept_level(self):
        """Test retrieving the level of a concept."""
        # Add some concepts to levels
        self.ahm.add_concept_to_level("taxonomy", "animal", 2)
        self.ahm.add_concept_to_level("taxonomy", "mammal", 1)
        self.ahm.add_concept_to_level("taxonomy", "dog", 0)
        
        # Test retrieving the level of a concept
        level = self.ahm.get_concept_level("taxonomy", "animal")
        self.assertEqual(2, level)
        
        # Test retrieving from a non-existent hierarchy
        level = self.ahm.get_concept_level("nonexistent", "animal")
        self.assertIsNone(level)
        
        # Test retrieving a non-existent concept
        level = self.ahm.get_concept_level("taxonomy", "nonexistent")
        self.assertIsNone(level)
    
    def test_get_all_levels(self):
        """Test retrieving all levels in a hierarchy."""
        # Add some concepts to levels
        self.ahm.add_concept_to_level("taxonomy", "animal", 2)
        self.ahm.add_concept_to_level("taxonomy", "mammal", 1)
        self.ahm.add_concept_to_level("taxonomy", "dog", 0)
        
        # Test retrieving all levels
        levels = self.ahm.get_all_levels("taxonomy")
        self.assertEqual(3, len(levels))
        self.assertIn(0, levels)
        self.assertIn(1, levels)
        self.assertIn(2, levels)
        
        # Test retrieving from a non-existent hierarchy
        levels = self.ahm.get_all_levels("nonexistent")
        self.assertEqual(0, len(levels))
    
    def test_add_abstraction_relation(self):
        """Test adding an abstraction relation."""
        # Add some concepts to levels
        self.ahm.add_concept_to_level("taxonomy", "animal", 2)
        self.ahm.add_concept_to_level("taxonomy", "mammal", 1)
        
        # Test adding an abstraction relation
        result = self.ahm.add_abstraction_relation("taxonomy", "mammal", "animal")
        self.assertTrue(result)
        self.assertIn("animal", self.ahm._concept_abstractions["taxonomy"]["mammal"])
        self.assertIn("mammal", self.ahm._concept_specializations["taxonomy"]["animal"])
        
        # Test adding with non-existent hierarchy
        result = self.ahm.add_abstraction_relation("nonexistent", "mammal", "animal")
        self.assertFalse(result)
        
        # Test adding with non-existent specific concept
        result = self.ahm.add_abstraction_relation("taxonomy", "nonexistent", "animal")
        self.assertFalse(result)
        
        # Test adding with non-existent abstract concept
        result = self.ahm.add_abstraction_relation("taxonomy", "mammal", "nonexistent")
        self.assertFalse(result)
        
        # Test adding with invalid levels (specific >= abstract)
        self.ahm.add_concept_to_level("taxonomy", "cat", 3)  # Higher level than animal
        result = self.ahm.add_abstraction_relation("taxonomy", "cat", "animal")
        self.assertFalse(result)
    
    def test_add_abstraction_relation_with_level_assignment(self):
        """Test adding an abstraction relation with automatic level assignment."""
        # Test with no levels assigned
        result = self.ahm.add_abstraction_relation("taxonomy", "dog", "mammal")
        self.assertTrue(result)
        
        # Check that levels were assigned
        dog_level = self.ahm.get_concept_level("taxonomy", "dog")
        mammal_level = self.ahm.get_concept_level("taxonomy", "mammal")
        self.assertIsNotNone(dog_level)
        self.assertIsNotNone(mammal_level)
        self.assertLess(dog_level, mammal_level)
        
        # Test with only specific level assigned
        self.ahm.add_concept_to_level("taxonomy", "cat", 0)
        result = self.ahm.add_abstraction_relation("taxonomy", "cat", "animal")
        self.assertTrue(result)
        
        # Check that abstract level was assigned
        cat_level = self.ahm.get_concept_level("taxonomy", "cat")
        animal_level = self.ahm.get_concept_level("taxonomy", "animal")
        self.assertEqual(0, cat_level)
        self.assertGreater(animal_level, cat_level)
        
        # Test with only abstract level assigned
        self.ahm.remove_concept_from_level("taxonomy", "dog", dog_level)
        # Remove animal from its auto-assigned level before re-assigning
        old_animal_level = self.ahm.get_concept_level("taxonomy", "animal")
        if old_animal_level is not None:
            self.ahm.remove_concept_from_level("taxonomy", "animal", old_animal_level)
        self.ahm.add_concept_to_level("taxonomy", "animal", 2)
        result = self.ahm.add_abstraction_relation("taxonomy", "dog", "animal")
        self.assertTrue(result)
        
        # Check that specific level was assigned
        dog_level = self.ahm.get_concept_level("taxonomy", "dog")
        animal_level = self.ahm.get_concept_level("taxonomy", "animal")
        self.assertEqual(2, animal_level)
        self.assertLess(dog_level, animal_level)
    
    def test_remove_abstraction_relation(self):
        """Test removing an abstraction relation."""
        # Add an abstraction relation first
        self.ahm.add_abstraction_relation("taxonomy", "mammal", "animal")
        
        # Test removing the relation
        result = self.ahm.remove_abstraction_relation("taxonomy", "mammal", "animal")
        self.assertTrue(result)
        self.assertNotIn("animal", self.ahm._concept_abstractions["taxonomy"].get("mammal", {}))
        self.assertNotIn("mammal", self.ahm._concept_specializations["taxonomy"].get("animal", {}))
        
        # Test removing from a non-existent hierarchy
        result = self.ahm.remove_abstraction_relation("nonexistent", "mammal", "animal")
        self.assertFalse(result)
        
        # Test removing a non-existent relation
        result = self.ahm.remove_abstraction_relation("taxonomy", "dog", "cat")
        self.assertFalse(result)
    
    def test_get_abstractions(self):
        """Test retrieving abstractions of a concept."""
        # Add some abstraction relations
        self.ahm.add_abstraction_relation("taxonomy", "dog", "mammal")
        self.ahm.add_abstraction_relation("taxonomy", "mammal", "animal")
        
        # Test retrieving abstractions
        abstractions = self.ahm.get_abstractions("taxonomy", "dog")
        self.assertEqual(1, len(abstractions))
        self.assertIn("mammal", abstractions)
        
        # Test retrieving from a non-existent hierarchy
        abstractions = self.ahm.get_abstractions("nonexistent", "dog")
        self.assertEqual(0, len(abstractions))
        
        # Test retrieving for a non-existent concept
        abstractions = self.ahm.get_abstractions("taxonomy", "nonexistent")
        self.assertEqual(0, len(abstractions))
    
    def test_get_specializations(self):
        """Test retrieving specializations of a concept."""
        # Add some abstraction relations
        self.ahm.add_abstraction_relation("taxonomy", "dog", "mammal")
        self.ahm.add_abstraction_relation("taxonomy", "cat", "mammal")
        self.ahm.add_abstraction_relation("taxonomy", "mammal", "animal")
        
        # Test retrieving specializations
        specializations = self.ahm.get_specializations("taxonomy", "mammal")
        self.assertEqual(2, len(specializations))
        self.assertIn("dog", specializations)
        self.assertIn("cat", specializations)
        
        # Test retrieving from a non-existent hierarchy
        specializations = self.ahm.get_specializations("nonexistent", "mammal")
        self.assertEqual(0, len(specializations))
        
        # Test retrieving for a non-existent concept
        specializations = self.ahm.get_specializations("taxonomy", "nonexistent")
        self.assertEqual(0, len(specializations))
    
    def test_get_all_abstractions(self):
        """Test retrieving all abstractions of a concept, including indirect ones."""
        # Add some abstraction relations
        self.ahm.add_abstraction_relation("taxonomy", "dog", "mammal")
        self.ahm.add_abstraction_relation("taxonomy", "mammal", "animal")
        
        # Test retrieving all abstractions
        all_abstractions = self.ahm.get_all_abstractions("taxonomy", "dog")
        self.assertEqual(2, len(all_abstractions))
        self.assertIn("mammal", all_abstractions)
        self.assertIn("animal", all_abstractions)
    
    def test_get_all_specializations(self):
        """Test retrieving all specializations of a concept, including indirect ones."""
        # Add some abstraction relations
        self.ahm.add_abstraction_relation("taxonomy", "dog", "mammal")
        self.ahm.add_abstraction_relation("taxonomy", "cat", "mammal")
        self.ahm.add_abstraction_relation("taxonomy", "mammal", "animal")
        
        # Test retrieving all specializations
        all_specializations = self.ahm.get_all_specializations("taxonomy", "animal")
        self.assertEqual(3, len(all_specializations))
        self.assertIn("mammal", all_specializations)
        self.assertIn("dog", all_specializations)
        self.assertIn("cat", all_specializations)
    
    def test_generalize_from_instances(self):
        """Test generalizing from instances."""
        # Test generalizing from instances
        abstraction_data = self.ahm.generalize_from_instances(["dog", "cat"])
        
        # Check that an abstraction was created
        self.assertIsNotNone(abstraction_data)
        self.assertEqual("abstraction", abstraction_data["type"])
        self.assertIn("instance_ids", abstraction_data)
        self.assertIn("dog", abstraction_data["instance_ids"])
        self.assertIn("cat", abstraction_data["instance_ids"])
        
        # Check that common properties were extracted
        self.assertIn("properties", abstraction_data)
        self.assertIn("alive", abstraction_data["properties"])
        self.assertIn("warm_blooded", abstraction_data["properties"])
        self.assertIn("domesticated", abstraction_data["properties"])
        
        # Test with a hierarchy
        abstraction_data = self.ahm.generalize_from_instances(["dog", "cat"], "taxonomy", 1)
        
        # Check that the abstraction was added to the hierarchy
        self.assertIsNotNone(abstraction_data)
        
        # Find the abstraction ID that was added to the hierarchy
        abstraction_id = None
        for concept_id, concept_data in self.ontology_manager.get_all_concepts().items():
            if concept_data.get("type") == "abstraction" and "dog" in concept_data.get("instance_ids", []) and "cat" in concept_data.get("instance_ids", []):
                # Only match the one that is actually in the hierarchy
                level = self.ahm.get_concept_level("taxonomy", concept_id)
                if level is not None:
                    abstraction_id = concept_id
                    break
        
        self.assertIsNotNone(abstraction_id)
        
        # Check that it was added to the correct level
        level = self.ahm.get_concept_level("taxonomy", abstraction_id)
        self.assertEqual(1, level)
        
        # Check that abstraction relations were created
        dog_abstractions = self.ahm.get_abstractions("taxonomy", "dog")
        cat_abstractions = self.ahm.get_abstractions("taxonomy", "cat")
        self.assertIn(abstraction_id, dog_abstractions)
        self.assertIn(abstraction_id, cat_abstractions)
    
    def test_generalize_from_instances_invalid_inputs(self):
        """Test generalizing from instances with invalid inputs."""
        # Test with less than 2 instances
        abstraction_data = self.ahm.generalize_from_instances(["dog"])
        self.assertIsNone(abstraction_data)
        
        # Test with non-existent instances
        abstraction_data = self.ahm.generalize_from_instances(["dog", "nonexistent"])
        self.assertIsNone(abstraction_data)
        
        # Test with non-existent hierarchy
        abstraction_data = self.ahm.generalize_from_instances(["dog", "cat"], "nonexistent")
        self.assertIsNotNone(abstraction_data)  # Should still create the abstraction, just not add it to a hierarchy
    
    def test_find_appropriate_abstraction_level(self):
        """Test finding the appropriate abstraction level for a task."""
        # Add some concepts to levels
        self.ahm.add_concept_to_level("taxonomy", "animal", 2)
        self.ahm.add_concept_to_level("taxonomy", "mammal", 1)
        self.ahm.add_concept_to_level("taxonomy", "dog", 0)
        self.ahm.add_concept_to_level("taxonomy", "cat", 0)
        
        # Test finding level for detailed analysis
        level = self.ahm.find_appropriate_abstraction_level("taxonomy", {"type": "detailed_analysis"})
        self.assertEqual(0, level)  # Should return the lowest level
        
        # Test finding level for high-level overview
        level = self.ahm.find_appropriate_abstraction_level("taxonomy", {"type": "high_level_overview"})
        self.assertEqual(2, level)  # Should return the highest level
        
        # Test finding level for a non-existent hierarchy
        level = self.ahm.find_appropriate_abstraction_level("nonexistent", {"type": "detailed_analysis"})
        self.assertIsNone(level)
    
    def test_helper_methods(self):
        """Test helper methods of the AbstractionHierarchyModule."""
        # Test _generate_abstraction_name
        instances = [
            {"name": "Dog"},
            {"name": "Cat"}
        ]
        name = self.ahm._generate_abstraction_name(instances)
        self.assertIsNotNone(name)
        self.assertIn("Dog", name)
        self.assertIn("Cat", name)
        
        # Test _extract_common_properties
        common_properties = self.ahm._extract_common_properties([
            {"properties": {"a": 1, "b": 2, "c": 3}},
            {"properties": {"a": 1, "b": 2, "d": 4}}
        ])
        self.assertEqual(2, len(common_properties))
        self.assertEqual(1, common_properties["a"])
        self.assertEqual(2, common_properties["b"])

if __name__ == "__main__":
    unittest.main()