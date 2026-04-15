"""
Complete unit tests for the remaining untested components in meta_knowledge.py.

This file provides comprehensive tests for:
1. LearningEffectivenessModel
2. MetaKnowledgeEncoder
3. MetaKnowledgeRepository
"""

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
import time
import json
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple, Union, Callable, TypeVar, Generic

from godelOS.metacognition.meta_knowledge import (
    MetaKnowledgeBase,
    MetaKnowledgeType,
    MetaKnowledgeEntry,
    LearningEffectivenessModel,
    MetaKnowledgeEncoder,
    MetaKnowledgeRepository,
    create_meta_knowledge_entry
)


# Custom enum for testing MetaKnowledgeEncoder
class TestEnum(Enum):
    """Test enum for MetaKnowledgeEncoder."""
    VALUE1 = "value1"
    VALUE2 = "value2"


# Custom dataclass for testing MetaKnowledgeRepository
@dataclass
class TestEntry(MetaKnowledgeEntry):
    """Test entry class for MetaKnowledgeRepository."""
    test_field: str = "test"


class TestLearningEffectivenessModel(unittest.TestCase):
    """Comprehensive tests for LearningEffectivenessModel."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging for debugging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up TestLearningEffectivenessModel tests")
        
        # Create mocks
        self.mock_kr_interface = MagicMock(spec=['create_context', 'list_contexts', 'retract_matching'])
        self.mock_kr_interface.assert_statement = MagicMock()
        self.mock_type_system = MagicMock()
        
        # Create MetaKnowledgeBase instance
        self.meta_knowledge = MetaKnowledgeBase(
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system,
            meta_knowledge_context_id="TEST_META_KNOWLEDGE"
        )
    
    def test_create_method(self):
        """Test the create class method."""
        self.logger.debug("Testing LearningEffectivenessModel.create method")
        
        # Create a model using the create method
        model = LearningEffectivenessModel.create(
            learning_approach="TestApproach",
            knowledge_gain_rate=0.7,
            convergence_speed=0.8,
            generalization_ability=0.6,
            resource_efficiency=0.5,
            applicable_domains=["domain1", "domain2"],
            limitations=["limitation1", "limitation2"],
            confidence=0.9,
            source="test",
            metadata={"test": "value"}
        )
        
        # Verify the model was created correctly
        self.assertEqual(model.learning_approach, "TestApproach")
        self.assertEqual(model.knowledge_gain_rate, 0.7)
        self.assertEqual(model.convergence_speed, 0.8)
        self.assertEqual(model.generalization_ability, 0.6)
        self.assertEqual(model.resource_efficiency, 0.5)
        self.assertEqual(model.applicable_domains, ["domain1", "domain2"])
        self.assertEqual(model.limitations, ["limitation1", "limitation2"])
        self.assertEqual(model.confidence, 0.9)
        self.assertEqual(model.source, "test")
        self.assertEqual(model.metadata, {"test": "value"})
        self.assertEqual(model.entry_type, MetaKnowledgeType.LEARNING_EFFECTIVENESS)
        self.assertIn("learning_effectiveness_TestApproach", model.entry_id)
    
    def test_create_method_default_values(self):
        """Test the create method with default values."""
        self.logger.debug("Testing LearningEffectivenessModel.create method with default values")
        
        # Create a model with minimal parameters
        model = LearningEffectivenessModel.create(
            learning_approach="TestApproach",
            knowledge_gain_rate=0.7,
            convergence_speed=0.8,
            generalization_ability=0.6,
            resource_efficiency=0.5,
            applicable_domains=["domain1"]
        )
        
        # Verify default values
        self.assertEqual(model.limitations, [])
        self.assertEqual(model.confidence, 1.0)
        self.assertEqual(model.source, "system")
        self.assertEqual(model.metadata, {})
    
    def test_add_learning_effectiveness_model(self):
        """Test adding a learning effectiveness model to the meta-knowledge base."""
        self.logger.debug("Testing add_learning_effectiveness_model")
        
        # Add a model
        entry_id = self.meta_knowledge.add_learning_effectiveness_model(
            learning_approach="TestApproach",
            knowledge_gain_rate=0.7,
            convergence_speed=0.8,
            generalization_ability=0.6,
            resource_efficiency=0.5,
            applicable_domains=["domain1", "domain2"],
            limitations=["limitation1", "limitation2"]
        )
        
        # Verify the model was added
        self.assertIsNotNone(entry_id)
        self.assertIn("learning_effectiveness_TestApproach", entry_id)
        
        # Verify the model can be retrieved
        model = self.meta_knowledge.get_learning_effectiveness_model("TestApproach")
        self.assertIsNotNone(model)
        self.assertEqual(model.learning_approach, "TestApproach")
    
    def test_update_learning_effectiveness_model(self):
        """Test updating a learning effectiveness model."""
        self.logger.debug("Testing updating a learning effectiveness model")
        
        # Add a model
        entry_id = self.meta_knowledge.add_learning_effectiveness_model(
            learning_approach="TestApproach",
            knowledge_gain_rate=0.7,
            convergence_speed=0.8,
            generalization_ability=0.6,
            resource_efficiency=0.5,
            applicable_domains=["domain1"]
        )
        
        # Get the model
        model = self.meta_knowledge.get_learning_effectiveness_model("TestApproach")
        
        # Modify the model
        model.knowledge_gain_rate = 0.8
        model.convergence_speed = 0.9
        model.applicable_domains = ["domain1", "domain2"]
        
        # Update the model
        self.meta_knowledge.update_entry(model)
        
        # Verify the model was updated
        updated_model = self.meta_knowledge.get_learning_effectiveness_model("TestApproach")
        self.assertEqual(updated_model.knowledge_gain_rate, 0.8)
        self.assertEqual(updated_model.convergence_speed, 0.9)
        self.assertEqual(updated_model.applicable_domains, ["domain1", "domain2"])
    
    def test_remove_learning_effectiveness_model(self):
        """Test removing a learning effectiveness model."""
        self.logger.debug("Testing removing a learning effectiveness model")
        
        # Add a model
        entry_id = self.meta_knowledge.add_learning_effectiveness_model(
            learning_approach="TestApproach",
            knowledge_gain_rate=0.7,
            convergence_speed=0.8,
            generalization_ability=0.6,
            resource_efficiency=0.5,
            applicable_domains=["domain1"]
        )
        
        # Verify the model was added
        self.assertIsNotNone(self.meta_knowledge.get_learning_effectiveness_model("TestApproach"))
        
        # Remove the model
        result = self.meta_knowledge.remove_entry(entry_id)
        
        # Verify the model was removed
        self.assertTrue(result)
        self.assertIsNone(self.meta_knowledge.get_learning_effectiveness_model("TestApproach"))


class TestMetaKnowledgeEncoder(unittest.TestCase):
    """Comprehensive tests for MetaKnowledgeEncoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up TestMetaKnowledgeEncoder tests")
        
        # Create an encoder instance
        self.encoder = MetaKnowledgeEncoder()
    
    def test_default_method_with_enum(self):
        """Test the default method with an Enum value."""
        self.logger.debug("Testing MetaKnowledgeEncoder.default with Enum")
        
        # Test with MetaKnowledgeType enum
        enum_value = MetaKnowledgeType.COMPONENT_PERFORMANCE
        result = self.encoder.default(enum_value)
        self.assertEqual(result, "component_performance")
        
        # Test with custom enum
        enum_value = TestEnum.VALUE1
        result = self.encoder.default(enum_value)
        self.assertEqual(result, "value1")
    
    def test_default_method_with_non_enum(self):
        """Test the default method with a non-Enum value."""
        self.logger.debug("Testing MetaKnowledgeEncoder.default with non-Enum")
        
        # Test with a non-Enum value
        with self.assertRaises(TypeError):
            self.encoder.default(object())
    
    def test_json_dumps_with_encoder(self):
        """Test using the encoder with json.dumps."""
        self.logger.debug("Testing json.dumps with MetaKnowledgeEncoder")
        
        # Create a dictionary with enum values
        data = {
            "type1": MetaKnowledgeType.COMPONENT_PERFORMANCE,
            "type2": MetaKnowledgeType.LEARNING_EFFECTIVENESS,
            "name": "test"
        }
        
        # Encode the dictionary
        json_str = json.dumps(data, cls=MetaKnowledgeEncoder)
        
        # Verify the result
        self.assertIn('"type1": "component_performance"', json_str)
        self.assertIn('"type2": "learning_effectiveness"', json_str)
        self.assertIn('"name": "test"', json_str)
    
    def test_json_dumps_with_nested_enums(self):
        """Test using the encoder with nested enum values."""
        self.logger.debug("Testing json.dumps with nested enum values")
        
        # Create a nested dictionary with enum values
        data = {
            "outer": {
                "inner1": MetaKnowledgeType.COMPONENT_PERFORMANCE,
                "inner2": TestEnum.VALUE2
            },
            "list": [
                MetaKnowledgeType.FAILURE_PATTERN,
                TestEnum.VALUE1
            ]
        }
        
        # Encode the dictionary
        json_str = json.dumps(data, cls=MetaKnowledgeEncoder)
        
        # Verify the result
        self.assertIn('"inner1": "component_performance"', json_str)
        self.assertIn('"inner2": "value2"', json_str)
        self.assertIn('"failure_pattern"', json_str)
        self.assertIn('"value1"', json_str)


class TestMetaKnowledgeRepository(unittest.TestCase):
    """Comprehensive tests for MetaKnowledgeRepository."""
    
    def setUp(self):
        """Set up test fixtures."""
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up TestMetaKnowledgeRepository tests")
    
    def test_initialization(self):
        """Test initialization of the repository."""
        self.logger.debug("Testing MetaKnowledgeRepository initialization")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Verify the repository was initialized correctly
        self.assertEqual(repo.entry_type, MetaKnowledgeEntry)
        self.assertEqual(repo.entries, {})
    
    def test_add_method(self):
        """Test the add method."""
        self.logger.debug("Testing MetaKnowledgeRepository.add")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Create an entry
        entry = MetaKnowledgeEntry(
            entry_id="test_entry",
            entry_type=MetaKnowledgeType.COMPONENT_PERFORMANCE,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.9,
            source="test",
            metadata={"test": "value"}
        )
        
        # Add the entry
        repo.add(entry)
        
        # Verify the entry was added
        self.assertEqual(len(repo.entries), 1)
        self.assertIn("test_entry", repo.entries)
        self.assertEqual(repo.entries["test_entry"], entry)
    
    def test_add_method_wrong_type(self):
        """Test the add method with an entry of the wrong type."""
        self.logger.debug("Testing MetaKnowledgeRepository.add with wrong type")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Try to add an entry of the wrong type
        with self.assertRaises(TypeError):
            repo.add("not an entry")
    
    def test_get_method(self):
        """Test the get method."""
        self.logger.debug("Testing MetaKnowledgeRepository.get")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Create an entry
        entry = MetaKnowledgeEntry(
            entry_id="test_entry",
            entry_type=MetaKnowledgeType.COMPONENT_PERFORMANCE,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.9,
            source="test",
            metadata={"test": "value"}
        )
        
        # Add the entry
        repo.add(entry)
        
        # Get the entry
        retrieved_entry = repo.get("test_entry")
        
        # Verify the entry was retrieved
        self.assertEqual(retrieved_entry, entry)
        
        # Try to get a non-existent entry
        self.assertIsNone(repo.get("non_existent"))
    
    def test_update_method(self):
        """Test the update method."""
        self.logger.debug("Testing MetaKnowledgeRepository.update")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Create an entry
        entry = MetaKnowledgeEntry(
            entry_id="test_entry",
            entry_type=MetaKnowledgeType.COMPONENT_PERFORMANCE,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.9,
            source="test",
            metadata={"test": "value"}
        )
        
        # Add the entry
        repo.add(entry)
        
        # Create an updated entry
        updated_entry = MetaKnowledgeEntry(
            entry_id="test_entry",
            entry_type=MetaKnowledgeType.COMPONENT_PERFORMANCE,
            creation_time=entry.creation_time,
            last_updated=time.time(),
            confidence=0.8,
            source="test",
            metadata={"test": "updated"}
        )
        
        # Update the entry
        repo.update(updated_entry)
        
        # Verify the entry was updated
        retrieved_entry = repo.get("test_entry")
        self.assertEqual(retrieved_entry.confidence, 0.8)
        self.assertEqual(retrieved_entry.metadata, {"test": "updated"})
    
    def test_update_method_wrong_type(self):
        """Test the update method with an entry of the wrong type."""
        self.logger.debug("Testing MetaKnowledgeRepository.update with wrong type")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Try to update with an entry of the wrong type
        with self.assertRaises(TypeError):
            repo.update("not an entry")
    
    def test_update_method_non_existent(self):
        """Test the update method with a non-existent entry."""
        self.logger.debug("Testing MetaKnowledgeRepository.update with non-existent entry")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Create an entry
        entry = MetaKnowledgeEntry(
            entry_id="test_entry",
            entry_type=MetaKnowledgeType.COMPONENT_PERFORMANCE,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.9,
            source="test",
            metadata={"test": "value"}
        )
        
        # Try to update a non-existent entry
        with self.assertRaises(KeyError):
            repo.update(entry)
    
    def test_remove_method(self):
        """Test the remove method."""
        self.logger.debug("Testing MetaKnowledgeRepository.remove")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Create an entry
        entry = MetaKnowledgeEntry(
            entry_id="test_entry",
            entry_type=MetaKnowledgeType.COMPONENT_PERFORMANCE,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.9,
            source="test",
            metadata={"test": "value"}
        )
        
        # Add the entry
        repo.add(entry)
        
        # Remove the entry
        repo.remove("test_entry")
        
        # Verify the entry was removed
        self.assertEqual(len(repo.entries), 0)
        self.assertIsNone(repo.get("test_entry"))
        
        # Try to remove a non-existent entry (should not raise an exception)
        repo.remove("non_existent")
    
    def test_list_all_method(self):
        """Test the list_all method."""
        self.logger.debug("Testing MetaKnowledgeRepository.list_all")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Create entries
        entry1 = MetaKnowledgeEntry(
            entry_id="entry1",
            entry_type=MetaKnowledgeType.COMPONENT_PERFORMANCE,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.9,
            source="test",
            metadata={"test": "value1"}
        )
        
        entry2 = MetaKnowledgeEntry(
            entry_id="entry2",
            entry_type=MetaKnowledgeType.REASONING_STRATEGY,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.8,
            source="test",
            metadata={"test": "value2"}
        )
        
        # Add the entries
        repo.add(entry1)
        repo.add(entry2)
        
        # List all entries
        entries = repo.list_all()
        
        # Verify the entries were listed
        self.assertEqual(len(entries), 2)
        self.assertIn(entry1, entries)
        self.assertIn(entry2, entries)
    
    def test_find_by_attribute_method(self):
        """Test the find_by_attribute method."""
        self.logger.debug("Testing MetaKnowledgeRepository.find_by_attribute")
        
        # Create a repository
        repo = MetaKnowledgeRepository(MetaKnowledgeEntry)
        
        # Create entries
        entry1 = MetaKnowledgeEntry(
            entry_id="entry1",
            entry_type=MetaKnowledgeType.COMPONENT_PERFORMANCE,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.9,
            source="test1",
            metadata={"test": "value1"}
        )
        
        entry2 = MetaKnowledgeEntry(
            entry_id="entry2",
            entry_type=MetaKnowledgeType.REASONING_STRATEGY,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.8,
            source="test2",
            metadata={"test": "value2"}
        )
        
        entry3 = MetaKnowledgeEntry(
            entry_id="entry3",
            entry_type=MetaKnowledgeType.COMPONENT_PERFORMANCE,
            creation_time=time.time(),
            last_updated=time.time(),
            confidence=0.7,
            source="test1",
            metadata={"test": "value3"}
        )
        
        # Add the entries
        repo.add(entry1)
        repo.add(entry2)
        repo.add(entry3)
        
        # Find entries by entry_type
        entries = repo.find_by_attribute("entry_type", MetaKnowledgeType.COMPONENT_PERFORMANCE)
        
        # Verify the entries were found
        self.assertEqual(len(entries), 2)
        self.assertIn(entry1, entries)
        self.assertIn(entry3, entries)
        
        # Find entries by source
        entries = repo.find_by_attribute("source", "test1")
        
        # Verify the entries were found
        self.assertEqual(len(entries), 2)
        self.assertIn(entry1, entries)
        self.assertIn(entry3, entries)
        
        # Find entries by confidence
        entries = repo.find_by_attribute("confidence", 0.8)
        
        # Verify the entries were found
        self.assertEqual(len(entries), 1)
        self.assertIn(entry2, entries)
        
        # Find entries by non-existent attribute
        entries = repo.find_by_attribute("non_existent", "value")
        
        # Verify no entries were found
        self.assertEqual(len(entries), 0)
        
        # Find entries by non-existent value
        entries = repo.find_by_attribute("source", "non_existent")
        
        # Verify no entries were found
        self.assertEqual(len(entries), 0)


if __name__ == "__main__":
    unittest.main()