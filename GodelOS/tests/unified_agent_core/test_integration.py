"""
Integration tests for the unified_agent_core package.

These tests verify that all components work together correctly.
"""

import unittest
import asyncio
import time
from unittest.mock import patch

from godelOS.unified_agent_core.core import UnifiedAgentCore
from godelOS.unified_agent_core.cognitive_engine.engine import CognitiveEngine
from godelOS.unified_agent_core.interaction_engine.engine import InteractionEngine
from godelOS.unified_agent_core.knowledge_store.store import UnifiedKnowledgeStore
from godelOS.unified_agent_core.resource_manager.manager import UnifiedResourceManager


class TestUnifiedAgentCoreIntegration(unittest.TestCase):
    """Test cases for the integration of UnifiedAgentCore components."""

    def setUp(self):
        """Set up test fixtures."""
        # Create real components with minimal configurations
        self.cognitive_engine = CognitiveEngine({
            "thought_stream_capacity": 10,
            "max_parallel_thoughts": 1,
            "max_parallel_reflections": 1,
            "max_parallel_ideations": 1
        })
        
        self.interaction_engine = InteractionEngine({
            "protocol_manager": {}
        })
        
        self.knowledge_store = UnifiedKnowledgeStore({
            "working_memory_capacity": 10,
            "working_memory_ttl": 60
        })
        
        self.resource_manager = UnifiedResourceManager({
            "optimization_interval": 10
        })
        
        # Create the UnifiedAgentCore
        self.agent_core = UnifiedAgentCore(
            cognitive_engine=self.cognitive_engine,
            interaction_engine=self.interaction_engine,
            knowledge_store=self.knowledge_store,
            resource_manager=self.resource_manager
        )
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the agent core if it's running
        if self.agent_core.is_running:
            self.loop.run_until_complete(self.agent_core.stop())
        
        self.loop.close()

    def test_full_lifecycle(self):
        """Test the full lifecycle of the UnifiedAgentCore."""
        # Initialize and start the agent core
        init_result = self.loop.run_until_complete(self.agent_core.initialize())
        self.assertTrue(init_result)
        self.assertTrue(self.agent_core.is_initialized)
        
        start_result = self.loop.run_until_complete(self.agent_core.start())
        self.assertTrue(start_result)
        self.assertTrue(self.agent_core.is_running)
        
        # Stop the agent core
        stop_result = self.loop.run_until_complete(self.agent_core.stop())
        self.assertTrue(stop_result)
        self.assertFalse(self.agent_core.is_running)

    @patch.object(InteractionEngine, 'process_interaction')
    def test_interaction_flow(self, mock_process_interaction):
        """Test the flow of an interaction through the system."""
        # Mock the interaction engine's process_interaction method
        mock_response = {
            "success": True,
            "content": {"text": "Test response"},
            "interaction_id": "test-interaction-id"
        }
        mock_process_interaction.return_value = mock_response
        
        # Initialize and start the agent core
        self.loop.run_until_complete(self.agent_core.initialize())
        self.loop.run_until_complete(self.agent_core.start())
        
        # Process an interaction
        test_interaction = {
            "type": "human",
            "content": {"text": "Hello, world!"}
        }
        
        result = self.loop.run_until_complete(
            self.agent_core.process_interaction(test_interaction)
        )
        
        # Verify the result
        self.assertEqual(result, mock_response)
        
        # Verify the interaction engine was called
        mock_process_interaction.assert_called_once()
        
        # Verify resource allocation and release
        self.assertTrue(self.resource_manager.allocate_resources_for_interaction.called)
        self.assertTrue(self.resource_manager.release_resources.called)

    @patch.object(CognitiveEngine, 'process_thought')
    def test_thought_flow(self, mock_process_thought):
        """Test the flow of a thought through the system."""
        # Mock the cognitive engine's process_thought method
        mock_result = {
            "success": True,
            "insights": ["Test insight"],
            "confidence": 0.9
        }
        mock_process_thought.return_value = mock_result
        
        # Initialize and start the agent core
        self.loop.run_until_complete(self.agent_core.initialize())
        self.loop.run_until_complete(self.agent_core.start())
        
        # Process a thought
        test_thought = {
            "type": "insight",
            "content": {"text": "This is an insight"},
            "confidence": 0.8
        }
        
        result = self.loop.run_until_complete(
            self.agent_core.process_thought(test_thought)
        )
        
        # Verify the result
        self.assertEqual(result, mock_result)
        
        # Verify the cognitive engine was called
        mock_process_thought.assert_called_once()
        
        # Verify resource allocation and release
        self.assertTrue(self.resource_manager.allocate_resources_for_thought.called)
        self.assertTrue(self.resource_manager.release_resources.called)

    def test_knowledge_storage_and_retrieval(self):
        """Test storing and retrieving knowledge through the UnifiedAgentCore."""
        # Initialize and start the agent core
        self.loop.run_until_complete(self.agent_core.initialize())
        self.loop.run_until_complete(self.agent_core.start())
        
        # Store a knowledge item
        test_knowledge = {
            "type": "fact",
            "content": {
                "text": "The sky is blue",
                "source": "observation"
            },
            "confidence": 1.0
        }
        
        # Use the knowledge store directly since UnifiedAgentCore doesn't expose this
        store_result = self.loop.run_until_complete(
            self.knowledge_store.store_knowledge(test_knowledge)
        )
        self.assertTrue(store_result)
        
        # Query for the knowledge
        test_query = {
            "knowledge_types": ["fact"],
            "content": {
                "text": "sky"
            },
            "max_results": 10
        }
        
        query_result = self.loop.run_until_complete(
            self.knowledge_store.query_knowledge(test_query)
        )
        
        # Verify we got a result
        self.assertTrue(query_result.success)
        self.assertGreater(len(query_result.items), 0)
        
        # Verify the content matches
        found = False
        for item in query_result.items:
            if item.content.get("text") == "The sky is blue":
                found = True
                break
        
        self.assertTrue(found, "Stored knowledge item was not retrieved")


if __name__ == "__main__":
    unittest.main()