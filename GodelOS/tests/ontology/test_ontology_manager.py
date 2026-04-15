"""
Unit tests for the OntologyManager component.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.ontology.ontology_manager import OntologyManager

class TestOntologyManager(unittest.TestCase):
    """Test cases for the OntologyManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.om = OntologyManager()
        
        # Add some test concepts
        self.om.add_concept("concept1", {"name": "Concept 1", "description": "Test concept 1"})
        self.om.add_concept("concept2", {"name": "Concept 2", "description": "Test concept 2"})
        self.om.add_concept("concept3", {"name": "Concept 3", "description": "Test concept 3"})
        
        # Add some test relations
        self.om.add_relation("relation1", {"name": "Relation 1", "description": "Test relation 1"})
        self.om.add_relation("relation2", {"name": "Relation 2", "description": "Test relation 2"})
        
        # Add some test properties
        self.om.add_property("property1", {"name": "Property 1", "description": "Test property 1"})
        self.om.add_property("property2", {"name": "Property 2", "description": "Test property 2"})
    
    def test_add_concept(self):
        """Test adding a concept."""
        # Test adding a new concept
        result = self.om.add_concept("concept4", {"name": "Concept 4", "description": "Test concept 4"})
        self.assertTrue(result)
        self.assertIn("concept4", self.om._concepts)
        
        # Test adding an existing concept
        result = self.om.add_concept("concept1", {"name": "Concept 1 New", "description": "Updated concept 1"})
        self.assertFalse(result)
    
    def test_remove_concept(self):
        """Test removing a concept."""
        # Test removing an existing concept
        result = self.om.remove_concept("concept1")
        self.assertTrue(result)
        self.assertNotIn("concept1", self.om._concepts)
        
        # Test removing a non-existent concept
        result = self.om.remove_concept("nonexistent")
        self.assertFalse(result)
    
    def test_update_concept(self):
        """Test updating a concept."""
        # Test updating an existing concept
        result = self.om.update_concept("concept1", {"name": "Concept 1 Updated", "description": "Updated concept 1"})
        self.assertTrue(result)
        self.assertEqual("Concept 1 Updated", self.om._concepts["concept1"]["name"])
        
        # Test updating a non-existent concept
        result = self.om.update_concept("nonexistent", {"name": "Nonexistent"})
        self.assertFalse(result)
    
    def test_get_concept(self):
        """Test retrieving a concept."""
        # Test retrieving an existing concept
        concept = self.om.get_concept("concept1")
        self.assertIsNotNone(concept)
        self.assertEqual("Concept 1", concept["name"])
        
        # Test retrieving a non-existent concept
        concept = self.om.get_concept("nonexistent")
        self.assertIsNone(concept)
    
    def test_get_all_concepts(self):
        """Test retrieving all concepts."""
        concepts = self.om.get_all_concepts()
        self.assertEqual(3, len(concepts))
        self.assertIn("concept1", concepts)
        self.assertIn("concept2", concepts)
        self.assertIn("concept3", concepts)
    
    def test_add_relation(self):
        """Test adding a relation."""
        # Test adding a new relation
        result = self.om.add_relation("relation3", {"name": "Relation 3", "description": "Test relation 3"})
        self.assertTrue(result)
        self.assertIn("relation3", self.om._relations)
        
        # Test adding an existing relation
        result = self.om.add_relation("relation1", {"name": "Relation 1 New", "description": "Updated relation 1"})
        self.assertFalse(result)
    
    def test_add_relation_instance(self):
        """Test adding a relation instance."""
        # Test adding a valid relation instance
        result = self.om.add_relation_instance("relation1", "concept1", "concept2")
        self.assertTrue(result)
        self.assertIn("relation1", self.om._concept_relations["concept1"])
        self.assertIn(("concept1", "concept2"), self.om._relation_concepts["relation1"])
        
        # Test adding with non-existent relation
        result = self.om.add_relation_instance("nonexistent", "concept1", "concept2")
        self.assertFalse(result)
        
        # Test adding with non-existent subject concept
        result = self.om.add_relation_instance("relation1", "nonexistent", "concept2")
        self.assertFalse(result)
        
        # Test adding with non-existent object concept
        result = self.om.add_relation_instance("relation1", "concept1", "nonexistent")
        self.assertFalse(result)
    
    def test_remove_relation_from_concept(self):
        """Test removing a relation from a concept."""
        # Add a relation instance first
        self.om.add_relation_instance("relation1", "concept1", "concept2")
        
        # Test removing an existing relation
        result = self.om.remove_relation_from_concept("concept1", "relation1")
        self.assertTrue(result)
        self.assertNotIn("relation1", self.om._concept_relations["concept1"])
        
        # Test removing a non-existent relation
        result = self.om.remove_relation_from_concept("concept1", "nonexistent")
        self.assertFalse(result)
        
        # Test removing from a non-existent concept
        result = self.om.remove_relation_from_concept("nonexistent", "relation1")
        self.assertFalse(result)
    
    def test_add_property(self):
        """Test adding a property."""
        # Test adding a new property
        result = self.om.add_property("property3", {"name": "Property 3", "description": "Test property 3"})
        self.assertTrue(result)
        self.assertIn("property3", self.om._properties)
        
        # Test adding an existing property
        result = self.om.add_property("property1", {"name": "Property 1 New", "description": "Updated property 1"})
        self.assertFalse(result)
    
    def test_set_concept_property(self):
        """Test setting a property for a concept."""
        # Test setting a valid property
        result = self.om.set_concept_property("concept1", "property1", "value1")
        self.assertTrue(result)
        self.assertEqual("value1", self.om._concept_properties["concept1"]["property1"])
        
        # Test setting with non-existent concept
        result = self.om.set_concept_property("nonexistent", "property1", "value1")
        self.assertFalse(result)
        
        # Test setting with non-existent property
        result = self.om.set_concept_property("concept1", "nonexistent", "value1")
        self.assertFalse(result)
    
    def test_get_concept_property(self):
        """Test retrieving a property for a concept."""
        # Set a property first
        self.om.set_concept_property("concept1", "property1", "value1")
        
        # Test retrieving an existing property
        value = self.om.get_concept_property("concept1", "property1")
        self.assertEqual("value1", value)
        
        # Test retrieving a non-existent property
        value = self.om.get_concept_property("concept1", "nonexistent")
        self.assertIsNone(value)
        
        # Test retrieving from a non-existent concept
        value = self.om.get_concept_property("nonexistent", "property1")
        self.assertIsNone(value)
    
    def test_get_related_concepts(self):
        """Test retrieving concepts related to a concept."""
        # Add some relation instances
        self.om.add_relation_instance("relation1", "concept1", "concept2")
        self.om.add_relation_instance("relation1", "concept1", "concept3")
        self.om.add_relation_instance("relation2", "concept1", "concept3")
        
        # Test retrieving related concepts
        related = self.om.get_related_concepts("concept1", "relation1")
        self.assertEqual(2, len(related))
        self.assertIn("concept2", related)
        self.assertIn("concept3", related)
        
        # Test retrieving with a specific relation
        related = self.om.get_related_concepts("concept1", "relation2")
        self.assertEqual(1, len(related))
        self.assertIn("concept3", related)
        
        # Test retrieving with a non-existent concept
        related = self.om.get_related_concepts("nonexistent", "relation1")
        self.assertEqual(0, len(related))
        
        # Test retrieving with a non-existent relation
        related = self.om.get_related_concepts("concept1", "nonexistent")
        self.assertEqual(0, len(related))
    
    def test_get_concepts_with_property(self):
        """Test retrieving concepts with a specific property."""
        # Set some properties
        self.om.set_concept_property("concept1", "property1", "value1")
        self.om.set_concept_property("concept2", "property1", "value1")
        self.om.set_concept_property("concept3", "property1", "value2")
        
        # Test retrieving concepts with a property
        concepts = self.om.get_concepts_with_property("property1")
        self.assertEqual(3, len(concepts))
        self.assertIn("concept1", concepts)
        self.assertIn("concept2", concepts)
        self.assertIn("concept3", concepts)
        
        # Test retrieving concepts with a property and value
        concepts = self.om.get_concepts_with_property("property1", "value1")
        self.assertEqual(2, len(concepts))
        self.assertIn("concept1", concepts)
        self.assertIn("concept2", concepts)
        
        # Test retrieving with a non-existent property
        concepts = self.om.get_concepts_with_property("nonexistent")
        self.assertEqual(0, len(concepts))
    
    def test_taxonomic_relations(self):
        """Test taxonomic relation methods."""
        # Add some taxonomic relations
        self.om.add_relation("is_a", {"type": "taxonomic"})
        self.om.add_relation("has_part", {"type": "taxonomic"})
        
        # Add some taxonomic relation instances
        self.om.add_relation_instance("is_a", "concept1", "concept2")
        self.om.add_relation_instance("is_a", "concept2", "concept3")
        self.om.add_relation_instance("has_part", "concept3", "concept1")
        
        # Test get_parent_concepts
        parents = self.om.get_parent_concepts("concept1")
        self.assertEqual(1, len(parents))
        self.assertIn("concept2", parents)
        
        # Test get_child_concepts
        children = self.om.get_child_concepts("concept2")
        self.assertEqual(1, len(children))
        self.assertIn("concept1", children)
        
        # Test get_part_concepts
        parts = self.om.get_part_concepts("concept3")
        self.assertEqual(1, len(parts))
        self.assertIn("concept1", parts)
        
        # Test get_whole_concepts
        wholes = self.om.get_whole_concepts("concept1")
        self.assertEqual(1, len(wholes))
        self.assertIn("concept3", wholes)
    
    def test_check_consistency(self):
        """Test checking ontology consistency."""
        # Create a circular is_a relationship
        self.om.add_relation("is_a", {"type": "taxonomic"})
        self.om.add_relation_instance("is_a", "concept1", "concept2")
        self.om.add_relation_instance("is_a", "concept2", "concept3")
        self.om.add_relation_instance("is_a", "concept3", "concept1")
        
        # Test consistency check
        inconsistencies = self.om.check_consistency()
        self.assertGreater(len(inconsistencies), 0)
        
        # Test with a dangling relation
        self.om.remove_concept("concept1")
        inconsistencies = self.om.check_consistency()
        self.assertGreater(len(inconsistencies), 0)
    
    def test_repair_inconsistencies(self):
        """Test repairing ontology inconsistencies."""
        # Create a circular is_a relationship
        self.om.add_relation("is_a", {"type": "taxonomic"})
        self.om.add_relation_instance("is_a", "concept1", "concept2")
        self.om.add_relation_instance("is_a", "concept2", "concept3")
        self.om.add_relation_instance("is_a", "concept3", "concept1")
        
        # Test repair
        repairs = self.om.repair_inconsistencies()
        self.assertGreater(repairs, 0)
        
        # Check if inconsistencies were fixed
        inconsistencies = self.om.check_consistency()
        self.assertEqual(0, len(inconsistencies))
    
    def test_export_to_kr_system(self):
        """Test exporting the ontology to the KR system."""
        # Add some test data
        self.om.add_relation_instance("relation1", "concept1", "concept2")
        self.om.set_concept_property("concept1", "property1", "value1")
        
        # Test export
        export_data = self.om.export_to_kr_system()
        self.assertIn("concepts", export_data)
        self.assertIn("relations", export_data)
        self.assertIn("properties", export_data)
        self.assertIn("relation_instances", export_data)
        self.assertIn("property_instances", export_data)
    
    def test_import_from_kr_system(self):
        """Test importing the ontology from the KR system."""
        # Create test import data
        import_data = {
            "concepts": {
                "import1": {"name": "Import 1", "description": "Imported concept 1"},
                "import2": {"name": "Import 2", "description": "Imported concept 2"}
            },
            "relations": {
                "import_rel": {"name": "Import Relation", "description": "Imported relation"}
            },
            "properties": {
                "import_prop": {"name": "Import Property", "description": "Imported property"}
            },
            "relation_instances": {
                "import_rel": [("import1", "import2")]
            },
            "property_instances": {
                "import1": {"import_prop": "import_value"}
            }
        }
        
        # Test import
        result = self.om.import_from_kr_system(import_data)
        self.assertTrue(result)
        
        # Check if import was successful
        self.assertIn("import1", self.om._concepts)
        self.assertIn("import_rel", self.om._relations)
        self.assertIn("import_prop", self.om._properties)
        self.assertIn(("import1", "import2"), self.om._relation_concepts["import_rel"])
        self.assertEqual("import_value", self.om._concept_properties["import1"]["import_prop"])

if __name__ == "__main__":
    unittest.main()