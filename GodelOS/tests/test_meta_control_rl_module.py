"""
Unit tests for the MetaControlRLModule component.

This module contains tests for the Meta-Control Reinforcement Learning Module (MCRL) component
of the Learning System.
"""

import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from typing import List, Dict, Any

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode, ConnectiveNode
from godelOS.learning_system.meta_control_rl_module import (
    MetaControlRLModule,
    MetaAction,
    RLConfig,
    ReplayBuffer,
    DQNModel
)


class TestMetaControlRLModule(unittest.TestCase):
    """Test cases for the MetaControlRLModule class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mkb_interface = MagicMock()
        
        # Define a simple state feature extractor function
        def mock_state_feature_extractor(mkb) -> List[float]:
            return [0.5, 0.3, 0.7, 0.2, 0.9]
        
        self.state_feature_extractor = mock_state_feature_extractor
        
        # Define action space
        self.action_space = [
            MetaAction(action_type="SelectInferenceStrategy", parameters={"prover_id": "resolution"}),
            MetaAction(action_type="SelectInferenceStrategy", parameters={"prover_id": "tableau"}),
            MetaAction(action_type="SetResourceLimit", parameters={"component_id": "prover", "resource_type": "time", "value": 1000}),
            MetaAction(action_type="BoostGoalUtility", parameters={"goal_id": "goal1", "factor": 1.5}),
            MetaAction(action_type="TriggerLearningModule", parameters={"module_id": "ilp_engine", "target_data": "recent_failures"})
        ]
        
        # Create RLConfig with smaller values for testing
        self.rl_config = RLConfig(
            learning_rate=0.01,
            discount_factor=0.9,
            exploration_rate=0.2,
            exploration_decay=0.99,
            min_exploration_rate=0.05,
            batch_size=4,
            target_update_frequency=10,
            replay_buffer_size=100,
            hidden_layer_sizes=[8, 8]
        )
        
        # Create MetaControlRLModule instance
        self.mcrl = MetaControlRLModule(
            mkb_interface=self.mkb_interface,
            action_space=self.action_space,
            state_feature_extractor=self.state_feature_extractor,
            rl_config=self.rl_config
        )

    def test_meta_action(self):
        """Test the MetaAction class."""
        action = MetaAction(
            action_type="SelectInferenceStrategy",
            parameters={"prover_id": "resolution"}
        )
        
        self.assertEqual(action.action_type, "SelectInferenceStrategy")
        self.assertEqual(action.parameters["prover_id"], "resolution")
        
        # Test string representation
        self.assertEqual(str(action), "SelectInferenceStrategy(prover_id=resolution)")
        
        # Test equality
        action2 = MetaAction(
            action_type="SelectInferenceStrategy",
            parameters={"prover_id": "resolution"}
        )
        self.assertEqual(action, action2)
        
        # Test inequality
        action3 = MetaAction(
            action_type="SelectInferenceStrategy",
            parameters={"prover_id": "tableau"}
        )
        self.assertNotEqual(action, action3)

    def test_rl_config(self):
        """Test the RLConfig class."""
        config = RLConfig(
            learning_rate=0.001,
            discount_factor=0.99,
            exploration_rate=0.1,
            exploration_decay=0.995,
            min_exploration_rate=0.01,
            batch_size=32,
            target_update_frequency=100,
            replay_buffer_size=10000,
            hidden_layer_sizes=[64, 64]
        )
        
        self.assertEqual(config.learning_rate, 0.001)
        self.assertEqual(config.discount_factor, 0.99)
        self.assertEqual(config.exploration_rate, 0.1)
        self.assertEqual(config.exploration_decay, 0.995)
        self.assertEqual(config.min_exploration_rate, 0.01)
        self.assertEqual(config.batch_size, 32)
        self.assertEqual(config.target_update_frequency, 100)
        self.assertEqual(config.replay_buffer_size, 10000)
        self.assertEqual(config.hidden_layer_sizes, [64, 64])

    def test_replay_buffer(self):
        """Test the ReplayBuffer class."""
        buffer = ReplayBuffer(capacity=5)
        
        # Test adding transitions
        buffer.add([0.1, 0.2], 0, 1.0, [0.2, 0.3], False)
        buffer.add([0.2, 0.3], 1, 0.5, [0.3, 0.4], False)
        buffer.add([0.3, 0.4], 0, 0.0, [0.4, 0.5], False)
        
        # Test buffer size
        self.assertEqual(len(buffer), 3)
        
        # Test sampling
        with patch('numpy.random.choice', return_value=[0, 2]):
            states, actions, rewards, next_states, dones = buffer.sample(2)
            
            # Check shapes
            self.assertEqual(states.shape, (2, 2))
            self.assertEqual(actions.shape, (2,))
            self.assertEqual(rewards.shape, (2,))
            self.assertEqual(next_states.shape, (2, 2))
            self.assertEqual(dones.shape, (2,))
            
            # Check values
            self.assertEqual(actions[0], 0)
            self.assertEqual(actions[1], 0)
            self.assertEqual(rewards[0], 1.0)
            self.assertEqual(rewards[1], 0.0)
        
        # Test capacity limit
        buffer.add([0.4, 0.5], 1, 0.3, [0.5, 0.6], False)
        buffer.add([0.5, 0.6], 0, 0.7, [0.6, 0.7], False)
        buffer.add([0.6, 0.7], 1, 0.2, [0.7, 0.8], True)
        
        # Buffer should be at capacity (5)
        self.assertEqual(len(buffer), 5)
        
        # Adding one more should maintain the capacity
        buffer.add([0.7, 0.8], 0, 0.1, [0.8, 0.9], False)
        self.assertEqual(len(buffer), 5)

    def test_dqn_model(self):
        """Test the DQNModel class."""
        model = DQNModel(
            state_dim=5,
            action_dim=3,
            hidden_layer_sizes=[8, 8],
            learning_rate=0.01
        )
        
        # Test initialization
        self.assertEqual(model.state_dim, 5)
        self.assertEqual(model.action_dim, 3)
        self.assertEqual(model.hidden_layer_sizes, [8, 8])
        self.assertEqual(model.learning_rate, 0.01)
        
        # Test weight initialization
        self.assertIn('W1', model.weights)
        self.assertIn('b1', model.weights)
        self.assertIn('W2', model.weights)
        self.assertIn('b2', model.weights)
        self.assertIn('W3', model.weights)
        self.assertIn('b3', model.weights)
        
        self.assertEqual(model.weights['W1'].shape, (5, 8))
        self.assertEqual(model.weights['b1'].shape, (8,))
        self.assertEqual(model.weights['W2'].shape, (8, 8))
        self.assertEqual(model.weights['b2'].shape, (8,))
        self.assertEqual(model.weights['W3'].shape, (8, 3))
        self.assertEqual(model.weights['b3'].shape, (3,))
        
        # Test prediction
        state = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        q_values = model.predict(state)
        
        self.assertEqual(q_values.shape, (1, 3))
        
        # Test batch prediction
        batch_states = np.array([
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.5, 0.4, 0.3, 0.2, 0.1]
        ])
        batch_q_values = model.predict(batch_states)
        
        self.assertEqual(batch_q_values.shape, (2, 3))
        
        # Test weight copying
        model2 = DQNModel(
            state_dim=5,
            action_dim=3,
            hidden_layer_sizes=[8, 8],
            learning_rate=0.01
        )
        
        # Modify model2 weights
        for key in model2.weights:
            model2.weights[key] = np.ones_like(model2.weights[key])
        
        # Copy weights from model2 to model
        model.copy_weights_from(model2)
        
        # Check that weights were copied
        for key in model.weights:
            self.assertTrue(np.array_equal(model.weights[key], np.ones_like(model.weights[key])))

    def test_initialization(self):
        """Test the initialization of the MetaControlRLModule."""
        self.assertEqual(self.mcrl.mkb_interface, self.mkb_interface)
        self.assertEqual(self.mcrl.action_space, self.action_space)
        self.assertEqual(self.mcrl.state_feature_extractor, self.state_feature_extractor)
        self.assertEqual(self.mcrl.config, self.rl_config)
        
        # Test action mapping
        self.assertEqual(len(self.mcrl.action_to_index), len(self.action_space))
        self.assertEqual(len(self.mcrl.index_to_action), len(self.action_space))
        
        for i, action in enumerate(self.action_space):
            self.assertEqual(self.mcrl.action_to_index[action], i)
            self.assertEqual(self.mcrl.index_to_action[i], action)
        
        # Test model initialization
        self.assertIsNotNone(self.mcrl.main_model)
        self.assertIsNotNone(self.mcrl.target_model)
        
        # Test replay buffer initialization
        self.assertIsNotNone(self.mcrl.replay_buffer)
        
        # Test initialization with default config
        mcrl_default_config = MetaControlRLModule(
            mkb_interface=self.mkb_interface,
            action_space=self.action_space,
            state_feature_extractor=self.state_feature_extractor
        )
        self.assertIsNotNone(mcrl_default_config.config)
        self.assertIsInstance(mcrl_default_config.config, RLConfig)

    def test_select_meta_action(self):
        """Test the select_meta_action method."""
        state_features = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Test exploration (force exploration by setting exploration_rate to 1.0)
        self.mcrl.exploration_rate = 1.0
        with patch('random.choice', return_value=2):
            action = self.mcrl.select_meta_action(state_features)
            self.assertEqual(action, self.action_space[2])
        
        # Test exploitation (force exploitation by setting exploration_rate to 0.0)
        self.mcrl.exploration_rate = 0.0
        
        # Mock the main_model.predict method to return fixed Q-values
        q_values = np.array([[0.1, 0.2, 0.5, 0.3, 0.4]])
        with patch.object(self.mcrl.main_model, 'predict', return_value=q_values):
            action = self.mcrl.select_meta_action(state_features)
            self.assertEqual(action, self.action_space[2])  # Index 2 has the highest Q-value (0.5)
        
        # Test with available_actions_mask
        mask = [False, True, False, True, False]  # Only actions 1 and 3 are available
        
        # Mock the main_model.predict method to return fixed Q-values
        q_values = np.array([[0.1, 0.2, 0.5, 0.3, 0.4]])
        with patch.object(self.mcrl.main_model, 'predict', return_value=q_values):
            action = self.mcrl.select_meta_action(state_features, available_actions_mask=mask)
            self.assertEqual(action, self.action_space[3])  # Index 3 has the highest Q-value among available actions

    def test_learn_from_transition(self):
        """Test the learn_from_transition method."""
        state_features = [0.1, 0.2, 0.3, 0.4, 0.5]
        action = self.action_space[2]
        reward = 1.0
        next_state_features = [0.2, 0.3, 0.4, 0.5, 0.6]
        episode_done = False
        
        # Mock the replay buffer's add method
        with patch.object(self.mcrl.replay_buffer, 'add') as mock_add:
            self.mcrl.learn_from_transition(state_features, action, reward, next_state_features, episode_done)
            
            # Verify that add was called with the correct arguments
            mock_add.assert_called_once()
            call_args = mock_add.call_args[0]
            self.assertEqual(call_args[0], state_features)
            self.assertEqual(call_args[1], 2)  # Action index
            self.assertEqual(call_args[2], reward)
            self.assertEqual(call_args[3], next_state_features)
            self.assertEqual(call_args[4], episode_done)
        
        # Test with enough samples for training
        # First, fill the replay buffer
        for _ in range(self.rl_config.batch_size):
            self.mcrl.replay_buffer.add(state_features, 2, reward, next_state_features, episode_done)
        
        # Mock the replay buffer's sample method
        states = np.array([state_features] * self.rl_config.batch_size)
        actions = np.array([2] * self.rl_config.batch_size)
        rewards = np.array([reward] * self.rl_config.batch_size)
        next_states = np.array([next_state_features] * self.rl_config.batch_size)
        dones = np.array([episode_done] * self.rl_config.batch_size)
        
        with patch.object(self.mcrl.replay_buffer, 'sample', return_value=(states, actions, rewards, next_states, dones)):
            # Mock the target model's predict method
            next_q_values = np.array([[0.1, 0.2, 0.3, 0.4, 0.5]] * self.rl_config.batch_size)
            with patch.object(self.mcrl.target_model, 'predict', return_value=next_q_values):
                # Mock the main model's update method
                with patch.object(self.mcrl.main_model, 'update', return_value=0.1) as mock_update:
                    # Mock the target model's copy_weights_from method
                    with patch.object(self.mcrl.target_model, 'copy_weights_from') as mock_copy:
                        # Call learn_from_transition
                        self.mcrl.learn_from_transition(state_features, action, reward, next_state_features, episode_done)
                        
                        # Verify that update was called
                        mock_update.assert_called_once()
                        
                        # Verify that copy_weights_from was not called (since training_steps is not a multiple of target_update_frequency)
                        mock_copy.assert_not_called()
                        
                        # Call learn_from_transition multiple times to trigger target model update
                        for _ in range(self.rl_config.target_update_frequency - 1):
                            self.mcrl.learn_from_transition(state_features, action, reward, next_state_features, episode_done)
                        
                        # Verify that copy_weights_from was called
                        mock_copy.assert_called_once()

    def test_get_action_space(self):
        """Test the get_action_space method."""
        action_space = self.mcrl.get_action_space()
        self.assertEqual(action_space, self.action_space)

    def test_get_state_features(self):
        """Test the get_state_features method."""
        state_features = self.mcrl.get_state_features()
        self.assertEqual(state_features, self.state_feature_extractor(self.mkb_interface))


if __name__ == '__main__':
    unittest.main()