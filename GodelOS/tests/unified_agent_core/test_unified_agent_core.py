"""
Tests for the UnifiedAgentCore class.

These tests verify the integration of all components in the UnifiedAgentCore.
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from godelOS.unified_agent_core.core import UnifiedAgentCore
from godelOS.unified_agent_core.state import UnifiedState


class TestUnifiedAgentCore(unittest.TestCase):
    """Test cases for the UnifiedAgentCore class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock components
        self.cognitive_engine = AsyncMock()
        self.interaction_engine = AsyncMock()
        self.knowledge_store = AsyncMock()
        self.resource_manager = AsyncMock()
        
        # Create test instance
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
        self.loop.close()

    def test_initialization(self):
        """Test that the UnifiedAgentCore initializes components correctly."""
        # Verify component references are set correctly
        self.assertEqual(self.agent_core.cognitive_engine, self.cognitive_engine)
        self.assertEqual(self.agent_core.interaction_engine, self.interaction_engine)
        self.assertEqual(self.agent_core.knowledge_store, self.knowledge_store)
        self.assertEqual(self.agent_core.resource_manager, self.resource_manager)
        
        # Verify state is created
        self.assertIsInstance(self.agent_core.state, UnifiedState)
        
        # Verify cross-component references are initialized
        self.cognitive_engine.set_state.assert_called_once()
        self.interaction_engine.set_state.assert_called_once()
        self.knowledge_store.set_state.assert_called_once()
        self.resource_manager.set_state.assert_called_once()
        
        self.cognitive_engine.set_knowledge_store.assert_called_once_with(self.knowledge_store)
        self.interaction_engine.set_knowledge_store.assert_called_once_with(self.knowledge_store)
        
        self.cognitive_engine.set_resource_manager.assert_called_once_with(self.resource_manager)
        self.interaction_engine.set_resource_manager.assert_called_once_with(self.resource_manager)
        self.knowledge_store.set_resource_manager.assert_called_once_with(self.resource_manager)

    def test_initialize(self):
        """Test the initialize method."""
        result = self.loop.run_until_complete(self.agent_core.initialize())
        
        # Verify result
        self.assertTrue(result)
        self.assertTrue(self.agent_core.is_initialized)
        
        # Verify components are initialized in the correct order
        self.resource_manager.initialize.assert_called_once()
        self.knowledge_store.initialize.assert_called_once()
        self.cognitive_engine.initialize.assert_called_once()
        self.interaction_engine.initialize.assert_called_once()

    def test_start(self):
        """Test the start method."""
        # Mock initialize to return True
        self.agent_core.initialize = AsyncMock(return_value=True)
        
        result = self.loop.run_until_complete(self.agent_core.start())
        
        # Verify result
        self.assertTrue(result)
        self.assertTrue(self.agent_core.is_running)
        
        # Verify components are started in the correct order
        self.resource_manager.start.assert_called_once()
        self.knowledge_store.start.assert_called_once()
        self.cognitive_engine.start.assert_called_once()
        self.interaction_engine.start.assert_called_once()

    def test_stop(self):
        """Test the stop method."""
        # Set running state
        self.agent_core.is_running = True
        
        result = self.loop.run_until_complete(self.agent_core.stop())
        
        # Verify result
        self.assertTrue(result)
        self.assertFalse(self.agent_core.is_running)
        
        # Verify components are stopped in the correct order (reverse of start)
        self.interaction_engine.stop.assert_called_once()
        self.cognitive_engine.stop.assert_called_once()
        self.knowledge_store.stop.assert_called_once()
        self.resource_manager.stop.assert_called_once()

    def test_process_interaction(self):
        """Test the process_interaction method."""
        # Set running state
        self.agent_core.is_running = True
        
        # Mock resource allocation
        mock_resources = {"priority": 1}
        self.resource_manager.allocate_resources_for_interaction.return_value = mock_resources
        
        # Mock interaction processing
        mock_response = {"success": True, "content": "Test response"}
        self.interaction_engine.process_interaction.return_value = mock_response
        
        # Mock cognitive response generation
        self.agent_core._should_generate_cognitive_response = Mock(return_value=False)
        
        # Test interaction
        test_interaction = {"type": "test", "content": "Test content"}
        result = self.loop.run_until_complete(self.agent_core.process_interaction(test_interaction))
        
        # Verify result
        self.assertEqual(result, mock_response)
        
        # Verify method calls
        self.resource_manager.allocate_resources_for_interaction.assert_called_once_with(test_interaction)
        self.interaction_engine.process_interaction.assert_called_once_with(test_interaction, mock_resources)
        self.resource_manager.release_resources.assert_called_once_with(mock_resources)

    def test_process_thought(self):
        """Test the process_thought method."""
        # Set running state
        self.agent_core.is_running = True
        
        # Mock resource allocation
        mock_resources = {"priority": 1}
        self.resource_manager.allocate_resources_for_thought.return_value = mock_resources
        
        # Mock thought processing
        mock_result = {"success": True, "insights": ["Test insight"]}
        self.cognitive_engine.process_thought.return_value = mock_result
        
        # Mock storage decision
        self.agent_core._should_store_thought_result = Mock(return_value=False)
        
        # Test thought
        test_thought = {"type": "insight", "content": "Test content"}
        result = self.loop.run_until_complete(self.agent_core.process_thought(test_thought))
        
        # Verify result
        self.assertEqual(result, mock_result)
        
        # Verify method calls
        self.resource_manager.allocate_resources_for_thought.assert_called_once_with(test_thought)
        self.cognitive_engine.process_thought.assert_called_once_with(test_thought, mock_resources)
        self.resource_manager.release_resources.assert_called_once_with(mock_resources)


if __name__ == "__main__":
    unittest.main()