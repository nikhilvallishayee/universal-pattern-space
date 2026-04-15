"""
Test cases for the Common Sense & Context Manager.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import tempfile

from godelOS.common_sense.manager import CommonSenseContextManager
from godelOS.common_sense.context_engine import ContextType


class TestCommonSenseContextManager(unittest.TestCase):
    """Test cases for the CommonSenseContextManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocked dependencies
        self.knowledge_store = Mock()
        self.inference_coordinator = Mock()
        self.cache_system = Mock()
        
        # Create a temporary directory for cache
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Configuration for testing
        self.config = {
            "create_default_context": True,
            "wordnet_enabled": False,  # Disable for testing
            "conceptnet_enabled": False,  # Disable for testing
            "offline_mode": True,  # Use offline mode for testing
            "cache_dir": self.temp_dir.name
        }
        
        # Create mocks for the components
        self.context_engine = Mock()
        self.external_kb_interface = Mock()
        self.contextualized_retriever = Mock()
        self.default_reasoning_module = Mock()
        
        # Patch the initialization methods
        with patch.object(CommonSenseContextManager, '_init_context_engine', return_value=self.context_engine), \
             patch.object(CommonSenseContextManager, '_init_external_kb_interface', return_value=self.external_kb_interface), \
             patch.object(CommonSenseContextManager, '_init_contextualized_retriever', return_value=self.contextualized_retriever), \
             patch.object(CommonSenseContextManager, '_init_default_reasoning_module', return_value=self.default_reasoning_module):
            
            # Create the manager
            self.manager = CommonSenseContextManager(
                knowledge_store=self.knowledge_store,
                inference_coordinator=self.inference_coordinator,
                cache_system=self.cache_system,
                config=self.config
            )
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
    
    def test_initialization(self):
        """Test initialization of the manager."""
        self.assertEqual(self.manager.knowledge_store, self.knowledge_store)
        self.assertEqual(self.manager.inference_coordinator, self.inference_coordinator)
        self.assertEqual(self.manager.cache_system, self.cache_system)
        self.assertEqual(self.manager.config, self.config)
        
        self.assertEqual(self.manager.context_engine, self.context_engine)
        self.assertEqual(self.manager.external_kb_interface, self.external_kb_interface)
        self.assertEqual(self.manager.contextualized_retriever, self.contextualized_retriever)
        self.assertEqual(self.manager.default_reasoning_module, self.default_reasoning_module)
        
        self.assertTrue(self.manager.initialized)
    
    def test_init_context_engine(self):
        """Test initialization of the context engine."""
        # Create a manager without patching
        with patch.object(CommonSenseContextManager, '_init_external_kb_interface', return_value=self.external_kb_interface), \
             patch.object(CommonSenseContextManager, '_init_contextualized_retriever', return_value=self.contextualized_retriever), \
             patch.object(CommonSenseContextManager, '_init_default_reasoning_module', return_value=self.default_reasoning_module):
            
            # Create a mock for the context engine
            mock_context_engine = Mock()
            mock_context_engine.create_context.return_value = MagicMock(id="default_context_id")
            
            # Patch the ContextEngine class
            with patch('godelOS.common_sense.manager.ContextEngine', return_value=mock_context_engine):
                manager = CommonSenseContextManager(
                    knowledge_store=self.knowledge_store,
                    inference_coordinator=self.inference_coordinator,
                    cache_system=self.cache_system,
                    config=self.config
                )
                
                # Check that the context engine was initialized
                self.assertEqual(manager.context_engine, mock_context_engine)
                
                # Check that a default context was created
                mock_context_engine.create_context.assert_called_with(
                    name="Default",
                    context_type=ContextType.SYSTEM,
                    metadata={"description": "Default system context"}
                )
                
                # Check that the default context was set as active
                mock_context_engine.set_active_context.assert_called_with("default_context_id")
    
    def test_init_external_kb_interface(self):
        """Test initialization of the external KB interface."""
        # Create a manager without patching
        with patch.object(CommonSenseContextManager, '_init_context_engine', return_value=self.context_engine), \
             patch.object(CommonSenseContextManager, '_init_contextualized_retriever', return_value=self.contextualized_retriever), \
             patch.object(CommonSenseContextManager, '_init_default_reasoning_module', return_value=self.default_reasoning_module):
            
            # Patch the ExternalCommonSenseKB_Interface class
            with patch('godelOS.common_sense.manager.ExternalCommonSenseKB_Interface') as mock_class:
                mock_class.return_value = self.external_kb_interface
                
                manager = CommonSenseContextManager(
                    knowledge_store=self.knowledge_store,
                    inference_coordinator=self.inference_coordinator,
                    cache_system=self.cache_system,
                    config=self.config
                )
                
                # Check that the interface was initialized
                self.assertEqual(manager.external_kb_interface, self.external_kb_interface)
                
                # Check that the class was called with the correct arguments
                mock_class.assert_called_with(
                    knowledge_store=self.knowledge_store,
                    cache_system=self.cache_system,
                    wordnet_enabled=False,
                    conceptnet_enabled=False,
                    conceptnet_api_url="http://api.conceptnet.io/c/en/",
                    offline_mode=True
                )
    
    def test_init_contextualized_retriever(self):
        """Test initialization of the contextualized retriever."""
        # Create a manager without patching
        with patch.object(CommonSenseContextManager, '_init_context_engine', return_value=self.context_engine), \
             patch.object(CommonSenseContextManager, '_init_external_kb_interface', return_value=self.external_kb_interface), \
             patch.object(CommonSenseContextManager, '_init_default_reasoning_module', return_value=self.default_reasoning_module):
            
            # Patch the ContextualizedRetriever class
            with patch('godelOS.common_sense.manager.ContextualizedRetriever') as mock_class, \
                 patch('godelOS.common_sense.manager.ContextRelevanceStrategy') as mock_enum:
                mock_class.return_value = self.contextualized_retriever
                mock_enum.__getitem__.return_value = "WEIGHTED"
                
                manager = CommonSenseContextManager(
                    knowledge_store=self.knowledge_store,
                    inference_coordinator=self.inference_coordinator,
                    cache_system=self.cache_system,
                    config=self.config
                )
                
                # Check that the retriever was initialized
                self.assertEqual(manager.contextualized_retriever, self.contextualized_retriever)
                
                # Check that the class was called with the correct arguments
                mock_class.assert_called_with(
                    knowledge_store=self.knowledge_store,
                    context_engine=self.context_engine,
                    cache_system=self.cache_system,
                    default_relevance_strategy="WEIGHTED",
                    relevance_weights=None,
                    max_results=10,
                    min_confidence=0.0,
                    min_relevance=0.0
                )
    def test_init_default_reasoning_module(self):
        """Test initialization of the default reasoning module."""
        # Create a manager without patching
        with patch.object(CommonSenseContextManager, '_init_context_engine', return_value=self.context_engine), \
             patch.object(CommonSenseContextManager, '_init_external_kb_interface', return_value=self.external_kb_interface), \
             patch.object(CommonSenseContextManager, '_init_contextualized_retriever', return_value=self.contextualized_retriever):
            
            # Patch the DefaultReasoningModule class
            with patch('godelOS.common_sense.manager.DefaultReasoningModule') as mock_class:
                mock_class.return_value = self.default_reasoning_module
                
                manager = CommonSenseContextManager(
                    knowledge_store=self.knowledge_store,
                    inference_coordinator=self.inference_coordinator,
                    cache_system=self.cache_system,
                    config=self.config
                )
                
                # Check that the module was initialized
                self.assertEqual(manager.default_reasoning_module, self.default_reasoning_module)
                
                # Check that the class was called with the correct arguments
                mock_class.assert_called_with(
                    knowledge_store=self.knowledge_store,
                    inference_coordinator=self.inference_coordinator,
                    context_engine=self.context_engine
                )
    
    def test_shutdown(self):
        """Test shutting down the manager."""
        # Shut down the manager
        self.manager.shutdown()
        
        # Check that the manager is no longer initialized
        self.assertFalse(self.manager.initialized)
    
    def test_create_context(self):
        """Test creating a context through the manager."""
        # Mock the context engine's create_context method
        self.context_engine.create_context.return_value = MagicMock(
            id="test_context_id",
            name="Test Context",
            type=ContextType.TASK,
            parent_id=None,
            created_at=123456789
        )
        
        # Create a context
        context_info = self.manager.create_context(
            name="Test Context",
            context_type=ContextType.TASK,
            metadata={"description": "A test context"}
        )
        
        # Check the context info
        self.assertEqual(context_info["id"], "test_context_id")
        self.assertEqual(context_info["name"], "Test Context")
        self.assertEqual(context_info["type"], "TASK")
        self.assertIsNone(context_info["parent_id"])
        self.assertEqual(context_info["created_at"], 123456789)
        
        # Check that the context engine was called
        self.context_engine.create_context.assert_called_with(
            name="Test Context",
            context_type=ContextType.TASK,
            parent_id=None,
            metadata={"description": "A test context"},
            variables=None
        )
        
        # Test with string context type
        self.manager.create_context(
            name="Test Context 2",
            context_type="SYSTEM"
        )
        
        # Check that the context engine was called with the enum
        self.context_engine.create_context.assert_called_with(
            name="Test Context 2",
            context_type=ContextType.SYSTEM,
            parent_id=None,
            metadata=None,
            variables=None
        )
        
        # Test with invalid context type
        with self.assertRaises(ValueError):
            self.manager.create_context(
                name="Test Context 3",
                context_type="INVALID"
            )
    
    def test_context_operations(self):
        """Test context operations through the manager."""
        # Mock the context engine methods
        self.context_engine.set_active_context.return_value = True
        self.context_engine.get_active_context.return_value = MagicMock(
            id="active_context_id",
            name="Active Context",
            type=ContextType.TASK,
            parent_id=None,
            variables={"var1": MagicMock(value="value1")},
            created_at=123456789,
            updated_at=123456790
        )
        self.context_engine.get_context.return_value = MagicMock(
            id="test_context_id",
            name="Test Context",
            type=ContextType.TASK,
            parent_id=None,
            variables={"var1": MagicMock(value="value1")},
            created_at=123456789,
            updated_at=123456790
        )
        self.context_engine.set_variable.return_value = True
        self.context_engine.get_variable.return_value = "test_value"
        self.context_engine.get_context_snapshot.return_value = {
            "var1": "value1",
            "var2": "value2"
        }
        
        # Test set_active_context
        result = self.manager.set_active_context("test_context_id")
        self.assertTrue(result)
        self.context_engine.set_active_context.assert_called_with("test_context_id")
        
        # Test get_active_context
        active_context = self.manager.get_active_context()
        self.assertEqual(active_context["id"], "active_context_id")
        self.assertEqual(active_context["name"], "Active Context")
        self.assertEqual(active_context["type"], "TASK")
        self.assertIsNone(active_context["parent_id"])
        self.assertEqual(active_context["variables"], {"var1": "value1"})
        
        # Test get_context
        context = self.manager.get_context("test_context_id")
        self.assertEqual(context["id"], "test_context_id")
        self.context_engine.get_context.assert_called_with("test_context_id")
        
        # Test set_context_variable
        result = self.manager.set_context_variable("test_var", "test_value", "test_context_id")
        self.assertTrue(result)
        self.context_engine.set_variable.assert_called_with(
            name="test_var",
            value="test_value",
            context_id="test_context_id"
        )
        
        # Test get_context_variable
        value = self.manager.get_context_variable("test_var", "test_context_id")
        self.assertEqual(value, "test_value")
        self.context_engine.get_variable.assert_called_with(
            name="test_var",
            context_id="test_context_id"
        )
        
        # Test get_context_snapshot
        snapshot = self.manager.get_context_snapshot("test_context_id")
        self.assertEqual(snapshot, {"var1": "value1", "var2": "value2"})
        self.context_engine.get_context_snapshot.assert_called_with("test_context_id")
    
    def test_external_kb_operations(self):
        """Test external KB operations through the manager."""
        # Mock the external KB interface methods
        self.external_kb_interface.query_concept.return_value = {
            "concept": "test",
            "relations": [],
            "definitions": [],
            "source": []
        }
        self.external_kb_interface.query_relation.return_value = []
        self.external_kb_interface.get_common_sense_facts.return_value = [
            "Fact 1",
            "Fact 2"
        ]
        self.external_kb_interface.bulk_import_concepts.return_value = {
            "concept1": True,
            "concept2": False
        }
        
        # Test query_concept
        result = self.manager.query_concept("test")
        self.assertEqual(result["concept"], "test")
        self.external_kb_interface.query_concept.assert_called_with("test", None)
        
        # Test with relation types
        self.manager.query_concept("test", ["is_a", "part_of"])
        self.external_kb_interface.query_concept.assert_called_with("test", ["is_a", "part_of"])
        
        # Test query_relation
        result = self.manager.query_relation("source", "target")
        self.assertEqual(result, [])
        self.external_kb_interface.query_relation.assert_called_with("source", "target", None)
        
        # Test with relation type
        self.manager.query_relation("source", "target", "is_a")
        self.external_kb_interface.query_relation.assert_called_with("source", "target", "is_a")
        
        # Test get_common_sense_facts
        facts = self.manager.get_common_sense_facts("test")
        self.assertEqual(facts, ["Fact 1", "Fact 2"])
        self.external_kb_interface.get_common_sense_facts.assert_called_with("test", 10)
        
        # Test with limit
        self.manager.get_common_sense_facts("test", 5)
        self.external_kb_interface.get_common_sense_facts.assert_called_with("test", 5)
        
        # Test bulk_import_concepts
        result = self.manager.bulk_import_concepts(["concept1", "concept2"])
        self.assertEqual(result, {"concept1": True, "concept2": False})
        self.external_kb_interface.bulk_import_concepts.assert_called_with(["concept1", "concept2"])
        
        self.assertTrue(self.manager.initialized)
    def test_retrieval_operations(self):
        """Test retrieval operations through the manager."""
        # Mock the contextualized retriever methods
        self.contextualized_retriever.retrieve.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "content": "Result 1",
                    "source": "test_source",
                    "confidence": 0.9,
                    "context_relevance": 0.8,
                    "overall_score": 0.72
                }
            )
        ]
        self.contextualized_retriever.retrieve_with_ambiguity_resolution.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "content": "Disambiguated Result",
                    "source": "test_source",
                    "confidence": 0.95,
                    "context_relevance": 0.9,
                    "overall_score": 0.855
                }
            )
        ]
        self.contextualized_retriever.retrieve_with_context_sensitivity.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "content": "Sensitive Result",
                    "source": "test_source",
                    "confidence": 0.8,
                    "context_relevance": 0.7,
                    "overall_score": 0.56
                }
            )
        ]
        
        # Test retrieve
        results = self.manager.retrieve("test query")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "Result 1")
        self.contextualized_retriever.retrieve.assert_called_with(
            query="test query",
            context_id=None,
            relevance_strategy=None,
            max_results=None,
            min_confidence=None,
            min_relevance=None,
            filters=None
        )
        
        # Test retrieve_with_ambiguity_resolution
        results = self.manager.retrieve_with_ambiguity_resolution("ambiguous query")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "Disambiguated Result")
        self.contextualized_retriever.retrieve_with_ambiguity_resolution.assert_called_with(
            query="ambiguous query",
            context_id=None,
            max_results=1
        )
        
        # Test retrieve_with_context_sensitivity
        results = self.manager.retrieve_with_context_sensitivity("context query")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "Sensitive Result")
        self.contextualized_retriever.retrieve_with_context_sensitivity.assert_called_with(
            query="context query",
            context_id=None,
            sensitivity_level=0.5
        )
    
    def test_default_reasoning_operations(self):
        """Test default reasoning operations through the manager."""
        # Mock the default reasoning module methods
        self.default_reasoning_module.add_default.return_value = None
        self.default_reasoning_module.add_exception.return_value = None
        self.default_reasoning_module.apply_defaults.return_value = {
            "success": True,
            "conclusion": "Birds can fly",
            "confidence": 0.8,
            "explanation": "Derived from default rule: birds_fly",
            "method": "default_reasoning",
            "defaults_used": ["birds_fly"],
            "exceptions_applied": []
        }
        
        # Mock the Default and Exception classes
        with patch('godelOS.common_sense.manager.Default') as mock_default, \
             patch('godelOS.common_sense.manager.ReasoningException') as mock_exception:
            
            mock_default.from_dict.return_value = "default_object"
            mock_exception.from_dict.return_value = "exception_object"
            
            # Test add_default_rule
            default_id = self.manager.add_default_rule({
                "id": "birds_fly",
                "prerequisite": "is_bird(X)",
                "justification": "not(is_penguin(X))",
                "consequent": "can_fly(X)"
            })
            self.assertEqual(default_id, "birds_fly")
            mock_default.from_dict.assert_called_once()
            self.default_reasoning_module.add_default.assert_called_with("default_object")
            
            # Test add_exception
            exception_id = self.manager.add_exception({
                "id": "penguins_exception",
                "default_id": "birds_fly",
                "condition": "is_penguin(X)"
            })
            self.assertEqual(exception_id, "penguins_exception")
            mock_exception.from_dict.assert_called_once()
            self.default_reasoning_module.add_exception.assert_called_with("exception_object")
        
        # Test apply_defaults
        result = self.manager.apply_defaults("Can birds fly?")
        self.assertTrue(result["success"])
        self.assertEqual(result["conclusion"], "Birds can fly")
        self.default_reasoning_module.apply_defaults.assert_called_with(
            query="Can birds fly?",
            context_id=None,
            confidence_threshold=0.0
        )
    
    def test_answer_query(self):
        """Test answering a query using all available mechanisms."""
        # Mock the inference coordinator
        self.inference_coordinator.prove.return_value = MagicMock(success=False)
        
        # Mock the contextualized retriever
        self.contextualized_retriever.retrieve.return_value = []
        
        # Mock the default reasoning module
        self.default_reasoning_module.apply_defaults.return_value = {
            "success": True,
            "conclusion": "Birds can fly",
            "confidence": 0.8,
            "explanation": "Derived from default rule: birds_fly",
            "method": "default_reasoning",
            "defaults_used": ["birds_fly"],
            "exceptions_applied": []
        }
        
        # Answer a query
        answer = self.manager.answer_query(
            query="Can birds fly?",
            context_id="test_context_id",
            use_external_kb=True,
            use_default_reasoning=True,
            confidence_threshold=0.5
        )
        
        # Check the answer
        self.assertEqual(answer["answer"], "Birds can fly")
        self.assertEqual(answer["confidence"], 0.8)
        self.assertEqual(answer["method"], "default_reasoning")
        self.assertEqual(answer["defaults_used"], ["birds_fly"])
        
        # Check that the methods were called in the correct order
        self.inference_coordinator.prove.assert_called_once()
        self.contextualized_retriever.retrieve.assert_called_once()
        self.default_reasoning_module.apply_defaults.assert_called_once()
        
        # Test when standard inference succeeds
        self.inference_coordinator.prove.reset_mock()
        self.contextualized_retriever.retrieve.reset_mock()
        self.default_reasoning_module.apply_defaults.reset_mock()
        
        self.inference_coordinator.prove.return_value = MagicMock(
            success=True,
            explanation="Proven by standard inference"
        )
        
        # Answer a query
        answer = self.manager.answer_query("Can birds fly?")
        
        # Check the answer
        self.assertEqual(answer["answer"], "Yes")
        self.assertEqual(answer["confidence"], 1.0)
        self.assertEqual(answer["method"], "standard_inference")
        
        # Check that only standard inference was called
        self.inference_coordinator.prove.assert_called_once()
        self.contextualized_retriever.retrieve.assert_not_called()
        self.default_reasoning_module.apply_defaults.assert_not_called()
    
    def test_enrich_context(self):
        """Test enriching a context with common sense knowledge."""
        # Mock the context engine
        self.context_engine.get_context.return_value = MagicMock(
            id="test_context_id",
            variables={"topic": MagicMock(value="birds")}
        )
        self.context_engine.set_variable.return_value = True
        
        # Mock the external KB interface
        self.external_kb_interface.get_common_sense_facts.return_value = [
            "Birds have feathers",
            "Most birds can fly",
            "Birds lay eggs"
        ]
        
        # Enrich the context
        result = self.manager.enrich_context(
            context_id="test_context_id",
            concepts=["birds"],
            max_facts_per_concept=3
        )
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["context_id"], "test_context_id")
        self.assertEqual(result["concepts_enriched"], ["birds"])
        self.assertEqual(result["facts_added"], 3)
        self.assertEqual(len(result["facts"]), 3)
        self.assertIn("Birds have feathers", result["facts"])
        
        # Check that the external KB interface was called
        self.external_kb_interface.get_common_sense_facts.assert_called_with("birds", 3)
        
        # Check that the context engine was called to set variables
        self.assertEqual(self.context_engine.set_variable.call_count, 3)
        
        # Test with no concepts provided
        self.context_engine.set_variable.reset_mock()
        self.external_kb_interface.get_common_sense_facts.reset_mock()
        
        # Mock the active context
        self.context_engine.get_active_context.return_value = MagicMock(
            id="active_context_id",
            variables={"topic": MagicMock(value="animals")}
        )
        
        # Enrich the active context
        result = self.manager.enrich_context(
            concepts=None,
            max_facts_per_concept=2
        )
        
        # Check that the context engine was called to get the active context
        self.context_engine.get_active_context.assert_called_once()
        
        # Check that the external KB interface was called with the extracted concept
        self.external_kb_interface.get_common_sense_facts.assert_called_with("animals", 2)


if __name__ == '__main__':
    unittest.main()