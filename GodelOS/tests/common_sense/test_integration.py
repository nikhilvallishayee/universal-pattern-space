"""
Integration tests for the Common Sense & Context System.

These tests verify the interaction between different components of the
Common Sense & Context System and integration with other GödelOS modules.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile

from godelOS.common_sense.manager import CommonSenseContextManager
from godelOS.common_sense.external_kb_interface import ExternalCommonSenseKB_Interface
from godelOS.common_sense.context_engine import ContextEngine, ContextType
from godelOS.common_sense.contextualized_retriever import ContextualizedRetriever, ContextRelevanceStrategy
from godelOS.common_sense.default_reasoning import DefaultReasoningModule, Default, Exception as ReasoningException


class TestCommonSenseContextIntegration(unittest.TestCase):
    """Integration tests for the Common Sense & Context System."""
    
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
        self.manager.shutdown()
    
    def test_initialization(self):
        """Test initialization of the manager and its components."""
        # Check that all components were initialized
        self.assertIsNotNone(self.manager.context_engine)
        self.assertIsNotNone(self.manager.external_kb_interface)
        self.assertIsNotNone(self.manager.contextualized_retriever)
        self.assertIsNotNone(self.manager.default_reasoning_module)
        
        # Check that the default context was created
        self.assertIsNotNone(self.manager.context_engine.get_active_context())
        self.assertEqual(self.manager.context_engine.get_active_context().name, "Default")
    
    def test_context_management(self):
        """Test context management through the manager."""
        # Create a context
        context_info = self.manager.create_context(
            name="Test Context",
            context_type=ContextType.TASK,
            metadata={"description": "A test context"}
        )
        
        # Check the context info
        self.assertEqual(context_info["name"], "Test Context")
        self.assertEqual(context_info["type"], "TASK")
        
        # Set a variable
        result = self.manager.set_context_variable(
            name="test_var",
            value="test_value",
            context_id=context_info["id"]
        )
        
        # Check the result
        self.assertTrue(result)
        
        # Get the variable
        value = self.manager.get_context_variable(
            name="test_var",
            context_id=context_info["id"]
        )
        
        # Check the value
        self.assertEqual(value, "test_value")
        
        # Set as active context
        result = self.manager.set_active_context(context_info["id"])
        
        # Check the result
        self.assertTrue(result)
        
        # Get the active context
        active_context = self.manager.get_active_context()
        
        # Check the active context
        self.assertEqual(active_context["id"], context_info["id"])
        
        # Get a context snapshot
        snapshot = self.manager.get_context_snapshot(context_info["id"])
        
        # Check the snapshot
        self.assertEqual(snapshot["test_var"], "test_value")
    
    def test_external_kb_integration(self):
        """Test integration with external knowledge bases."""
        # Mock the query_concept method to return predefined data
        self.manager.external_kb_interface.query_concept = Mock(return_value={
            "concept": "test",
            "relations": [
                {
                    "source": "test",
                    "relation": "is_a",
                    "target": "concept",
                    "weight": 0.9,
                    "source_kb": "test"
                }
            ],
            "definitions": ["A test definition"],
            "source": ["test"]
        })
        
        # Query a concept
        result = self.manager.query_concept("test")
        
        # Check the result
        self.assertEqual(result["concept"], "test")
        self.assertEqual(len(result["relations"]), 1)
        self.assertEqual(result["relations"][0]["source"], "test")
        self.assertEqual(result["relations"][0]["relation"], "is_a")
        self.assertEqual(result["relations"][0]["target"], "concept")
        
        # Get common sense facts
        facts = self.manager.get_common_sense_facts("test", limit=2)
        
        # Check the facts
        self.assertEqual(len(facts), 2)
        self.assertEqual(facts[0], "test is a type of concept.")
        self.assertEqual(facts[1], "test is defined as: A test definition")
    
    def test_contextualized_retrieval(self):
        """Test contextualized retrieval."""
        # Create a context with variables
        context_info = self.manager.create_context(
            name="Retrieval Context",
            context_type=ContextType.TASK,
            variables={"topic": "science", "subtopic": "physics"}
        )
        
        # Mock the contextualized_retriever.retrieve method
        self.manager.contextualized_retriever.retrieve = Mock(return_value=[
            MagicMock(
                content="Physics is the study of matter and energy",
                source="test_source",
                confidence=0.9,
                context_relevance=0.8,
                to_dict=lambda: {
                    "content": "Physics is the study of matter and energy",
                    "source": "test_source",
                    "confidence": 0.9,
                    "context_relevance": 0.8,
                    "overall_score": 0.72
                }
            )
        ])
        
        # Retrieve with context
        results = self.manager.retrieve(
            query="What is physics?",
            context_id=context_info["id"]
        )
        
        # Check the results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "Physics is the study of matter and energy")
        self.assertEqual(results[0]["source"], "test_source")
        self.assertEqual(results[0]["confidence"], 0.9)
        self.assertEqual(results[0]["context_relevance"], 0.8)
        self.assertEqual(results[0]["overall_score"], 0.72)
        
        # Check that the retriever was called with the correct arguments
        self.manager.contextualized_retriever.retrieve.assert_called_with(
            query="What is physics?",
            context_id=context_info["id"],
            relevance_strategy=None,
            max_results=None,
            min_confidence=None,
            min_relevance=None,
            filters=None
        )
    
    def test_default_reasoning(self):
        """Test default reasoning."""
        # Mock the default_reasoning_module.apply_defaults method
        self.manager.default_reasoning_module.apply_defaults = Mock(return_value={
            "success": True,
            "conclusion": "Birds can fly",
            "confidence": 0.8,
            "explanation": "Derived from default rule: birds_fly",
            "method": "default_reasoning",
            "defaults_used": ["birds_fly"],
            "exceptions_applied": []
        })
        
        # Apply defaults
        result = self.manager.apply_defaults(
            query="Can birds fly?",
            context_id=None,
            confidence_threshold=0.5
        )
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["conclusion"], "Birds can fly")
        self.assertEqual(result["confidence"], 0.8)
        self.assertEqual(result["defaults_used"], ["birds_fly"])
        
        # Check that the module was called with the correct arguments
        self.manager.default_reasoning_module.apply_defaults.assert_called_with(
            query="Can birds fly?",
            context_id=None,
            confidence_threshold=0.5
        )
    
    def test_combined_workflow(self):
        """Test the combined workflow for answering queries."""
        # Create a context
        context_info = self.manager.create_context(
            name="Combined Workflow Context",
            context_type=ContextType.TASK,
            variables={"topic": "animals", "subtopic": "birds"}
        )
        
        # Mock the inference_coordinator.prove method to fail
        self.inference_coordinator.prove = Mock(return_value=MagicMock(success=False))
        
        # Mock the contextualized_retriever.retrieve method to return empty results
        self.manager.contextualized_retriever.retrieve = Mock(return_value=[])
        
        # Mock the default_reasoning_module.apply_defaults method
        self.manager.default_reasoning_module.apply_defaults = Mock(return_value={
            "success": True,
            "conclusion": "Birds can fly",
            "confidence": 0.8,
            "explanation": "Derived from default rule: birds_fly",
            "method": "default_reasoning",
            "defaults_used": ["birds_fly"],
            "exceptions_applied": []
        })
        
        # Answer a query
        answer = self.manager.answer_query(
            query="Can birds fly?",
            context_id=context_info["id"],
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
        self.manager.contextualized_retriever.retrieve.assert_called_once()
        self.manager.default_reasoning_module.apply_defaults.assert_called_once()
    
    def test_context_enrichment(self):
        """Test context enrichment with common sense knowledge."""
        # Create a context
        context_info = self.manager.create_context(
            name="Enrichment Context",
            context_type=ContextType.TASK,
            variables={"topic": "birds"}
        )
        
        # Mock the get_common_sense_facts method
        self.manager.external_kb_interface.get_common_sense_facts = Mock(return_value=[
            "Birds have feathers",
            "Most birds can fly",
            "Birds lay eggs"
        ])
        
        # Enrich the context
        result = self.manager.enrich_context(
            context_id=context_info["id"],
            concepts=["birds"],
            max_facts_per_concept=3
        )
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["context_id"], context_info["id"])
        self.assertEqual(result["concepts_enriched"], ["birds"])
        self.assertEqual(result["facts_added"], 3)
        self.assertEqual(len(result["facts"]), 3)
        self.assertIn("Birds have feathers", result["facts"])
        
        # Get a context snapshot to verify the enrichment
        snapshot = self.manager.get_context_snapshot(context_info["id"])
        
        # Check that the facts were added to the context
        self.assertEqual(snapshot["fact_birds_0"], "Birds have feathers")
        self.assertEqual(snapshot["fact_birds_1"], "Most birds can fly")
        self.assertEqual(snapshot["fact_birds_2"], "Birds lay eggs")


if __name__ == '__main__':
    unittest.main()