"""
Tests for the learning system components.

These tests verify the functionality of the learning system components including:
- InteractionLearner
- CognitiveLearner
- PerformanceTracker
- StrategyOptimizer
- UnifiedLearningManager
"""

import unittest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import json

from godelOS.unified_agent_core.learning.interfaces import (
    UnifiedExperience, LearningResult, StrategyOptimization, LearningMode
)
from godelOS.unified_agent_core.learning.manager import (
    InteractionLearner, CognitiveLearner, PerformanceTracker,
    StrategyOptimizer, UnifiedLearningManager
)


class TestInteractionLearner(unittest.TestCase):
    """Test cases for the InteractionLearner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.learner = InteractionLearner()
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_initialization(self):
        """Test that the InteractionLearner initializes correctly."""
        self.assertEqual(self.learner.learning_rate, 0.1)
        self.assertEqual(self.learner.min_confidence, 0.6)
        self.assertEqual(self.learner.max_patterns, 1000)
        self.assertEqual(self.learner.interaction_patterns, {})
        self.assertEqual(self.learner.response_templates, {})
        self.assertEqual(self.learner.user_preferences, {})

    def test_learn_from_non_interaction_experience(self):
        """Test learning from a non-interaction experience."""
        experience = UnifiedExperience(
            id="test-id",
            type="cognitive",  # Not an interaction
            content={}
        )
        
        result = self.loop.run_until_complete(self.learner.learn(experience))
        
        self.assertFalse(result.success)
        self.assertIn("Cannot learn from experience type", result.message)

    def test_learn_from_interaction_experience(self):
        """Test learning from an interaction experience."""
        experience = UnifiedExperience(
            id="test-id",
            type="interaction",
            content={
                "interaction": {
                    "user_id": "test-user",
                    "type": "query",
                    "content": {"text": "Hello, world!"}
                },
                "response": {
                    "content": {"text": "Hi there!"}
                }
            },
            feedback={"score": 0.8}
        )
        
        result = self.loop.run_until_complete(self.learner.learn(experience))
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.learned_concepts), 0)
        self.assertIn("interaction_pattern:query", result.learned_concepts)
        self.assertGreater(result.confidence, 0)
        self.assertIn("pattern_confidence", result.metrics)

    def test_apply_learning(self):
        """Test applying learning to an interaction."""
        # First learn from an experience
        experience = UnifiedExperience(
            id="test-id",
            type="interaction",
            content={
                "interaction": {
                    "user_id": "test-user",
                    "type": "query",
                    "content": {"text": "Hello, world!"}
                },
                "response": {
                    "content": {"text": "Hi there!"}
                }
            },
            feedback={"score": 0.8}
        )
        
        self.loop.run_until_complete(self.learner.learn(experience))
        
        # Now apply learning to a new interaction
        interaction_data = {
            "user_id": "test-user",
            "type": "query",
            "content": {"text": "Hello again!"}
        }
        
        enhanced_data = self.loop.run_until_complete(self.learner.apply_learning(interaction_data))
        
        self.assertIsNotNone(enhanced_data)
        self.assertIn("metadata", enhanced_data)
        # The pattern insights might not be present if confidence is too low
        # but the structure should be preserved
        self.assertEqual(enhanced_data["user_id"], "test-user")
        self.assertEqual(enhanced_data["type"], "query")


class TestCognitiveLearner(unittest.TestCase):
    """Test cases for the CognitiveLearner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.learner = CognitiveLearner()
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_initialization(self):
        """Test that the CognitiveLearner initializes correctly."""
        self.assertEqual(self.learner.learning_rate, 0.1)
        self.assertEqual(self.learner.min_confidence, 0.6)
        self.assertEqual(self.learner.max_patterns, 1000)
        self.assertEqual(self.learner.thought_patterns, {})
        self.assertEqual(self.learner.concept_relationships, {})
        self.assertEqual(self.learner.reasoning_strategies, {})

    def test_learn_from_non_cognitive_experience(self):
        """Test learning from a non-cognitive experience."""
        experience = UnifiedExperience(
            id="test-id",
            type="interaction",  # Not a cognitive experience
            content={}
        )
        
        result = self.loop.run_until_complete(self.learner.learn(experience))
        
        self.assertFalse(result.success)
        self.assertIn("Cannot learn from experience type", result.message)

    def test_learn_from_cognitive_experience(self):
        """Test learning from a cognitive experience."""
        experience = UnifiedExperience(
            id="test-id",
            type="cognitive",
            content={
                "thought": {
                    "type": "insight",
                    "content": {"text": "This is an insight"},
                    "strategy": "analytical",
                    "concepts": ["insight", "analysis"]
                },
                "result": {
                    "content": {"text": "Result of the thought"},
                    "concepts": ["result", "conclusion"]
                }
            },
            feedback={"score": 0.8}
        )
        
        result = self.loop.run_until_complete(self.learner.learn(experience))
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.learned_concepts), 0)
        self.assertIn("thought_pattern:insight", result.learned_concepts)
        self.assertIn("reasoning_strategy:analytical", result.learned_concepts)
        self.assertGreater(result.confidence, 0)
        self.assertIn("pattern_confidence", result.metrics)
        self.assertIn("strategy_confidence", result.metrics)

    def test_apply_learning(self):
        """Test applying learning to a thought."""
        # First learn from an experience
        experience = UnifiedExperience(
            id="test-id",
            type="cognitive",
            content={
                "thought": {
                    "type": "insight",
                    "content": {"text": "This is an insight"},
                    "strategy": "analytical",
                    "concepts": ["insight", "analysis"]
                },
                "result": {
                    "content": {"text": "Result of the thought"},
                    "concepts": ["result", "conclusion"]
                }
            },
            feedback={"score": 0.8}
        )
        
        self.loop.run_until_complete(self.learner.learn(experience))
        
        # Now apply learning to a new thought
        thought_data = {
            "type": "insight",
            "content": {"text": "Another insight"},
            "concepts": ["insight", "idea"]
        }
        
        enhanced_data = self.loop.run_until_complete(self.learner.apply_learning(thought_data))
        
        self.assertIsNotNone(enhanced_data)
        self.assertIn("metadata", enhanced_data)
        self.assertIn("cognitive_insights", enhanced_data["metadata"])
        self.assertEqual(enhanced_data["type"], "insight")


class TestPerformanceTracker(unittest.TestCase):
    """Test cases for the PerformanceTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = PerformanceTracker()
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_initialization(self):
        """Test that the PerformanceTracker initializes correctly."""
        self.assertEqual(self.tracker.interaction_metrics, {})
        self.assertEqual(self.tracker.cognitive_metrics, {})
        self.assertEqual(self.tracker.system_metrics, {})
        self.assertEqual(self.tracker.time_series, {})
        self.assertEqual(self.tracker.max_time_series_points, 1000)

    def test_track_interaction_experience(self):
        """Test tracking an interaction experience."""
        experience = UnifiedExperience(
            id="test-id",
            type="interaction",
            content={
                "interaction": {
                    "type": "query",
                    "response_time": 0.5
                }
            },
            feedback={"score": 0.8}
        )
        
        self.loop.run_until_complete(self.tracker.track(experience))
        
        # Verify metrics were tracked
        self.assertIn("query", self.tracker.interaction_metrics)
        self.assertEqual(self.tracker.interaction_metrics["query"]["count"], 1)
        self.assertEqual(self.tracker.interaction_metrics["query"]["success_count"], 1)
        self.assertEqual(self.tracker.interaction_metrics["query"]["total_score"], 0.8)
        self.assertEqual(len(self.tracker.interaction_metrics["query"]["response_times"]), 1)
        self.assertEqual(self.tracker.interaction_metrics["query"]["response_times"][0], 0.5)

    def test_track_cognitive_experience(self):
        """Test tracking a cognitive experience."""
        experience = UnifiedExperience(
            id="test-id",
            type="cognitive",
            content={
                "thought": {
                    "type": "insight",
                    "processing_time": 0.3
                }
            },
            feedback={"score": 0.7}
        )
        
        self.loop.run_until_complete(self.tracker.track(experience))
        
        # Verify metrics were tracked
        self.assertIn("insight", self.tracker.cognitive_metrics)
        self.assertEqual(self.tracker.cognitive_metrics["insight"]["count"], 1)
        self.assertEqual(self.tracker.cognitive_metrics["insight"]["success_count"], 1)
        self.assertEqual(self.tracker.cognitive_metrics["insight"]["total_score"], 0.7)
        self.assertEqual(len(self.tracker.cognitive_metrics["insight"]["processing_times"]), 1)
        self.assertEqual(self.tracker.cognitive_metrics["insight"]["processing_times"][0], 0.3)

    def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        # Track some experiences first
        interaction_exp = UnifiedExperience(
            id="test-id1",
            type="interaction",
            content={
                "interaction": {
                    "type": "query",
                    "response_time": 0.5
                }
            },
            feedback={"score": 0.8}
        )
        
        cognitive_exp = UnifiedExperience(
            id="test-id2",
            type="cognitive",
            content={
                "thought": {
                    "type": "insight",
                    "processing_time": 0.3
                }
            },
            feedback={"score": 0.7}
        )
        
        self.loop.run_until_complete(self.tracker.track(interaction_exp))
        self.loop.run_until_complete(self.tracker.track(cognitive_exp))
        
        # Get metrics
        metrics = self.loop.run_until_complete(self.tracker.get_performance_metrics())
        
        # Verify metrics structure
        self.assertIn("interaction", metrics)
        self.assertIn("cognitive", metrics)
        self.assertIn("system", metrics)
        self.assertIn("query", metrics["interaction"])
        self.assertIn("insight", metrics["cognitive"])


class TestStrategyOptimizer(unittest.TestCase):
    """Test cases for the StrategyOptimizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = StrategyOptimizer()
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_initialization(self):
        """Test that the StrategyOptimizer initializes correctly."""
        self.assertEqual(self.optimizer.strategies, {})
        self.assertEqual(self.optimizer.optimization_history, [])
        self.assertEqual(self.optimizer.optimization_interval, 3600)  # Default 1 hour
        self.assertFalse(self.optimizer.is_optimizing)

    def test_get_nonexistent_strategy(self):
        """Test getting a strategy that doesn't exist."""
        strategy = self.loop.run_until_complete(self.optimizer.get_strategy("nonexistent"))
        
        self.assertEqual(strategy, {})

    def test_update_strategy_performance(self):
        """Test updating strategy performance."""
        strategy_name = "test-strategy"
        metrics = {"accuracy": 0.8, "speed": 0.9}
        
        result = self.loop.run_until_complete(
            self.optimizer.update_strategy_performance(strategy_name, metrics)
        )
        
        self.assertTrue(result)
        self.assertIn(strategy_name, self.optimizer.strategies)
        self.assertIn("performance_history", self.optimizer.strategies[strategy_name])
        self.assertEqual(len(self.optimizer.strategies[strategy_name]["performance_history"]), 1)
        self.assertEqual(
            self.optimizer.strategies[strategy_name]["performance_history"][0]["metrics"],
            metrics
        )

    def test_optimize(self):
        """Test optimizing strategies."""
        # Add some strategies to optimize
        strategy_names = ["interaction-strategy", "cognitive-strategy", "resource-strategy"]
        
        for name in strategy_names:
            self.loop.run_until_complete(
                self.optimizer.update_strategy_performance(name, {"accuracy": 0.7})
            )
        
        # Run optimization
        result = self.loop.run_until_complete(self.optimizer.optimize())
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.optimized_strategies), len(strategy_names))
        for name in strategy_names:
            self.assertIn(name, result.optimized_strategies)
        self.assertIn("average_improvement", result.improvement_metrics)


class TestUnifiedLearningManager(unittest.TestCase):
    """Test cases for the UnifiedLearningManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock components
        self.interaction_learner = AsyncMock()
        self.cognitive_learner = AsyncMock()
        self.performance_tracker = AsyncMock()
        self.strategy_optimizer = AsyncMock()
        
        # Create test instance with mocks
        self.learning_manager = UnifiedLearningManager(
            config={
                "interaction_learner": {},
                "cognitive_learner": {},
                "performance_tracker": {},
                "strategy_optimizer": {}
            }
        )
        
        # Replace components with mocks
        self.learning_manager.interaction_learner = self.interaction_learner
        self.learning_manager.cognitive_learner = self.cognitive_learner
        self.learning_manager.performance_tracker = self.performance_tracker
        self.learning_manager.strategy_optimizer = self.strategy_optimizer
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_initialization(self):
        """Test that the UnifiedLearningManager initializes correctly."""
        manager = UnifiedLearningManager()  # Create a fresh instance
        
        self.assertIsInstance(manager.interaction_learner, InteractionLearner)
        self.assertIsInstance(manager.cognitive_learner, CognitiveLearner)
        self.assertIsInstance(manager.performance_tracker, PerformanceTracker)
        self.assertIsInstance(manager.strategy_optimizer, StrategyOptimizer)
        self.assertEqual(manager.experience_buffer.maxlen, 100)
        self.assertFalse(manager.is_initialized)
        self.assertFalse(manager.is_running)

    def test_initialize(self):
        """Test the initialize method."""
        result = self.loop.run_until_complete(self.learning_manager.initialize())
        
        self.assertTrue(result)
        self.assertTrue(self.learning_manager.is_initialized)

    def test_start(self):
        """Test the start method."""
        # Set initialized state
        self.learning_manager.is_initialized = True
        
        result = self.loop.run_until_complete(self.learning_manager.start())
        
        self.assertTrue(result)
        self.assertTrue(self.learning_manager.is_running)

    def test_stop(self):
        """Test the stop method."""
        # Set running state
        self.learning_manager.is_running = True
        
        result = self.loop.run_until_complete(self.learning_manager.stop())
        
        self.assertTrue(result)
        self.assertFalse(self.learning_manager.is_running)

    def test_learn_from_interaction_experience(self):
        """Test learning from an interaction experience."""
        # Mock the interaction learner's learn method
        mock_result = LearningResult(
            success=True,
            learned_concepts=["test-concept"],
            confidence=0.8
        )
        self.interaction_learner.learn.return_value = mock_result
        
        # Create test experience
        experience = UnifiedExperience(
            id="test-id",
            type="interaction",
            content={}
        )
        
        # Set running state
        self.learning_manager.is_running = True
        
        # Learn from experience
        result = self.loop.run_until_complete(
            self.learning_manager.learn_from_experience(experience)
        )
        
        # Verify result
        self.assertEqual(result, mock_result)
        
        # Verify method calls
        self.interaction_learner.learn.assert_called_once_with(experience)
        self.performance_tracker.track.assert_called_once_with(experience)

    def test_learn_from_cognitive_experience(self):
        """Test learning from a cognitive experience."""
        # Mock the cognitive learner's learn method
        mock_result = LearningResult(
            success=True,
            learned_concepts=["test-concept"],
            confidence=0.8
        )
        self.cognitive_learner.learn.return_value = mock_result
        
        # Create test experience
        experience = UnifiedExperience(
            id="test-id",
            type="cognitive",
            content={}
        )
        
        # Set running state
        self.learning_manager.is_running = True
        
        # Learn from experience
        result = self.loop.run_until_complete(
            self.learning_manager.learn_from_experience(experience)
        )
        
        # Verify result
        self.assertEqual(result, mock_result)
        
        # Verify method calls
        self.cognitive_learner.learn.assert_called_once_with(experience)
        self.performance_tracker.track.assert_called_once_with(experience)

    def test_optimize_strategies(self):
        """Test optimizing strategies."""
        # Mock the strategy optimizer's optimize method
        mock_result = StrategyOptimization(
            success=True,
            optimized_strategies=["test-strategy"],
            improvement_metrics={"average_improvement": 0.1}
        )
        self.strategy_optimizer.optimize.return_value = mock_result
        
        # Set running state
        self.learning_manager.is_running = True
        
        # Optimize strategies
        result = self.loop.run_until_complete(
            self.learning_manager.optimize_strategies()
        )
        
        # Verify result
        self.assertEqual(result, mock_result)
        
        # Verify method calls
        self.strategy_optimizer.optimize.assert_called_once()


if __name__ == "__main__":
    unittest.main()