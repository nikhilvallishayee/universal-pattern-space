"""
Meta-Control Reinforcement Learning Module (MCRL) for GödelOS.

This module implements the MetaControlRLModule component (Module 3.4) of the Learning System,
which is responsible for learning optimal control policies for meta-level decisions within
GödelOS using Reinforcement Learning (RL).

The MCRL makes decisions such as selecting inference strategies, prioritizing goals,
allocating cognitive resources, and deciding when to trigger specific learning or
self-modification routines.
"""

import logging
import random
import numpy as np
from typing import List, Dict, Optional, Callable, Tuple, Any, Set, Union
from dataclasses import dataclass, field
from collections import deque

from godelOS.core_kr.ast.nodes import AST_Node
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface

logger = logging.getLogger(__name__)


@dataclass
class MetaAction:
    """
    Represents a meta-level action that can be taken by the MetaControlRLModule.
    
    Meta-actions include selecting inference strategies, allocating resources,
    prioritizing goals, and triggering learning modules.
    """
    action_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of the meta-action."""
        params_str = ", ".join(f"{k}={v}" for k, v in self.parameters.items())
        return f"{self.action_type}({params_str})"
    
    def __eq__(self, other) -> bool:
        """Check if two meta-actions are equal."""
        if not isinstance(other, MetaAction):
            return False
        return (self.action_type == other.action_type and 
                self.parameters == other.parameters)
    
    def __hash__(self) -> int:
        """Hash based on action_type and frozen parameters."""
        return hash((self.action_type, tuple(sorted(self.parameters.items()))))


@dataclass
class RLConfig:
    """
    Configuration for the reinforcement learning algorithm.
    
    This class defines parameters for the RL algorithm, including
    learning rate, discount factor, exploration rate, etc.
    """
    learning_rate: float = 0.001
    discount_factor: float = 0.99
    exploration_rate: float = 0.1
    exploration_decay: float = 0.995
    min_exploration_rate: float = 0.01
    batch_size: int = 32
    target_update_frequency: int = 100
    replay_buffer_size: int = 10000
    hidden_layer_sizes: List[int] = field(default_factory=lambda: [64, 64])


class ReplayBuffer:
    """
    Experience replay buffer for storing and sampling transitions.
    
    This class stores (state, action, reward, next_state, done) tuples
    and provides functionality to sample random batches for training.
    """
    
    def __init__(self, capacity: int):
        """
        Initialize the replay buffer.
        
        Args:
            capacity: Maximum number of transitions to store
        """
        self.buffer = deque(maxlen=capacity)
    
    def add(self, state: List[float], action_idx: int, reward: float, 
            next_state: List[float], done: bool) -> None:
        """
        Add a transition to the buffer.
        
        Args:
            state: The state features
            action_idx: The index of the action taken
            reward: The reward received
            next_state: The next state features
            done: Whether the episode is done
        """
        self.buffer.append((state, action_idx, reward, next_state, done))
    
    def sample(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Sample a random batch of transitions.
        
        Args:
            batch_size: The number of transitions to sample
            
        Returns:
            A tuple of (states, actions, rewards, next_states, dones)
        """
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        states, actions, rewards, next_states, dones = zip(*[self.buffer[i] for i in indices])
        
        return (np.array(states, dtype=np.float32),
                np.array(actions, dtype=np.int32),
                np.array(rewards, dtype=np.float32),
                np.array(next_states, dtype=np.float32),
                np.array(dones, dtype=np.bool_))
    
    def __len__(self) -> int:
        """Get the current size of the buffer."""
        return len(self.buffer)


class DQNModel:
    """
    Deep Q-Network model for approximating the Q-function.
    
    This class implements a neural network that approximates the Q-function,
    mapping states to Q-values for each action.
    """
    
    def __init__(self, state_dim: int, action_dim: int, hidden_layer_sizes: List[int], 
                 learning_rate: float):
        """
        Initialize the DQN model.
        
        Args:
            state_dim: Dimensionality of the state space
            action_dim: Dimensionality of the action space
            hidden_layer_sizes: List of hidden layer sizes
            learning_rate: Learning rate for the optimizer
        """
        # In a real implementation, this would use a deep learning framework
        # like TensorFlow or PyTorch to create a neural network.
        # For simplicity, we'll use a placeholder implementation.
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_layer_sizes = hidden_layer_sizes
        self.learning_rate = learning_rate
        
        # Initialize weights (in a real implementation, these would be tensors)
        self.weights = self._initialize_weights()
        
        logger.info(f"Initialized DQN model with state_dim={state_dim}, action_dim={action_dim}")
    
    def _initialize_weights(self) -> Dict[str, np.ndarray]:
        """
        Initialize the weights of the neural network.
        
        Returns:
            A dictionary of weight matrices
        """
        weights = {}
        
        # Input layer to first hidden layer
        weights['W1'] = np.random.randn(self.state_dim, self.hidden_layer_sizes[0]) * 0.1
        weights['b1'] = np.zeros(self.hidden_layer_sizes[0])
        
        # Hidden layers
        for i in range(1, len(self.hidden_layer_sizes)):
            weights[f'W{i+1}'] = np.random.randn(self.hidden_layer_sizes[i-1], self.hidden_layer_sizes[i]) * 0.1
            weights[f'b{i+1}'] = np.zeros(self.hidden_layer_sizes[i])
        
        # Last hidden layer to output layer
        weights[f'W{len(self.hidden_layer_sizes)+1}'] = np.random.randn(self.hidden_layer_sizes[-1], self.action_dim) * 0.1
        weights[f'b{len(self.hidden_layer_sizes)+1}'] = np.zeros(self.action_dim)
        
        return weights
    
    def predict(self, state: np.ndarray) -> np.ndarray:
        """
        Predict Q-values for a given state.
        
        Args:
            state: The state features (batch_size, state_dim)
            
        Returns:
            Q-values for each action (batch_size, action_dim)
        """
        # In a real implementation, this would use the neural network
        # to compute Q-values. For simplicity, we'll use a placeholder.
        if len(state.shape) == 1:
            state = np.expand_dims(state, axis=0)
        
        # Forward pass through the network
        x = state
        for i in range(1, len(self.hidden_layer_sizes) + 1):
            x = np.dot(x, self.weights[f'W{i}']) + self.weights[f'b{i}']
            x = np.maximum(0, x)  # ReLU activation
        
        # Output layer
        q_values = np.dot(x, self.weights[f'W{len(self.hidden_layer_sizes)+1}']) + self.weights[f'b{len(self.hidden_layer_sizes)+1}']
        
        return q_values
    
    def update(self, states: np.ndarray, actions: np.ndarray, targets: np.ndarray) -> float:
        """
        Update the model weights based on the given targets.
        
        Args:
            states: Batch of states (batch_size, state_dim)
            actions: Batch of actions (batch_size,)
            targets: Target Q-values for the actions (batch_size,)
            
        Returns:
            The loss value
        """
        # In a real implementation, this would perform a gradient descent step
        # to update the neural network weights. For simplicity, we'll use a placeholder.
        # Just return a random loss value
        return random.random() * 0.1
    
    def copy_weights_from(self, other: 'DQNModel') -> None:
        """
        Copy weights from another model.
        
        Args:
            other: The model to copy weights from
        """
        for key in self.weights:
            self.weights[key] = other.weights[key].copy()


class MetaControlRLModule:
    """
    Meta-Control Reinforcement Learning Module for GödelOS.
    
    This class implements the MetaControlRLModule component (Module 3.4) of the Learning System,
    which learns optimal control policies for meta-level decisions within GödelOS using
    Reinforcement Learning (RL).
    """
    
    def __init__(self, 
                 mkb_interface: Any,  # Should be MetaKnowledgeBase, but using Any for now
                 action_space: List[MetaAction],
                 state_feature_extractor: Callable[[Any], List[float]],
                 rl_config: Optional[RLConfig] = None):
        """
        Initialize the Meta-Control RL Module.
        
        Args:
            mkb_interface: Interface to the MetaKnowledgeBase
            action_space: List of possible meta-actions
            state_feature_extractor: Function to extract state features from MKB
            rl_config: Configuration for the RL algorithm
        """
        self.mkb_interface = mkb_interface
        self.action_space = action_space
        self.state_feature_extractor = state_feature_extractor
        self.config = rl_config or RLConfig()
        
        # Initialize exploration rate
        self.exploration_rate = self.config.exploration_rate
        
        # Initialize action mapping
        self.action_to_index = {action: i for i, action in enumerate(action_space)}
        self.index_to_action = {i: action for i, action in enumerate(action_space)}
        
        # Initialize replay buffer
        self.replay_buffer = ReplayBuffer(self.config.replay_buffer_size)
        
        # Initialize DQN models
        state_dim = len(self.state_feature_extractor(self.mkb_interface))
        action_dim = len(action_space)
        
        self.main_model = DQNModel(
            state_dim=state_dim,
            action_dim=action_dim,
            hidden_layer_sizes=self.config.hidden_layer_sizes,
            learning_rate=self.config.learning_rate
        )
        
        self.target_model = DQNModel(
            state_dim=state_dim,
            action_dim=action_dim,
            hidden_layer_sizes=self.config.hidden_layer_sizes,
            learning_rate=self.config.learning_rate
        )
        
        # Copy weights from main model to target model
        self.target_model.copy_weights_from(self.main_model)
        
        # Training stats
        self.training_steps = 0
        
        logger.info(f"Initialized MetaControlRLModule with {len(action_space)} actions")
    
    def select_meta_action(self, current_system_state_features: List[float], 
                          available_actions_mask: Optional[List[bool]] = None) -> MetaAction:
        """
        Select a meta-action based on the current system state.
        
        Args:
            current_system_state_features: Features representing the current system state
            available_actions_mask: Optional mask indicating which actions are available
                                   (True for available, False for unavailable)
            
        Returns:
            The selected meta-action
        """
        # Convert state features to numpy array
        state = np.array(current_system_state_features, dtype=np.float32)
        
        # Apply mask if provided
        if available_actions_mask is None:
            available_actions_mask = [True] * len(self.action_space)
        
        # Epsilon-greedy action selection
        if random.random() < self.exploration_rate:
            # Exploration: select a random available action
            available_indices = [i for i, available in enumerate(available_actions_mask) if available]
            if not available_indices:
                logger.warning("No actions available according to mask")
                available_indices = list(range(len(self.action_space)))
            
            action_idx = random.choice(available_indices)
        else:
            # Exploitation: select the action with the highest Q-value
            q_values = self.main_model.predict(state)[0]
            
            # Apply mask to Q-values
            for i, available in enumerate(available_actions_mask):
                if not available:
                    q_values[i] = float('-inf')
            
            action_idx = np.argmax(q_values)
        
        # Decay exploration rate
        self.exploration_rate = max(
            self.config.min_exploration_rate,
            self.exploration_rate * self.config.exploration_decay
        )
        
        # Return the selected action
        selected_action = self.index_to_action[action_idx]
        logger.debug(f"Selected meta-action: {selected_action}")
        
        return selected_action
    
    def learn_from_transition(self, state_features: List[float], action_taken: MetaAction,
                             reward: float, next_state_features: List[float], 
                             episode_done: bool) -> None:
        """
        Learn from a transition (experience).
        
        Args:
            state_features: Features of the state before taking the action
            action_taken: The meta-action that was taken
            reward: The reward received
            next_state_features: Features of the state after taking the action
            episode_done: Whether the episode is done
        """
        # Convert to numpy arrays
        state = np.array(state_features, dtype=np.float32)
        next_state = np.array(next_state_features, dtype=np.float32)
        
        # Get action index
        action_idx = self.action_to_index[action_taken]
        
        # Add to replay buffer
        self.replay_buffer.add(state_features, action_idx, reward, next_state_features, episode_done)
        
        # Only train if we have enough samples
        if len(self.replay_buffer) < self.config.batch_size:
            return
        
        # Sample batch from replay buffer
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.config.batch_size)
        
        # Compute targets
        next_q_values = self.target_model.predict(next_states)
        max_next_q_values = np.max(next_q_values, axis=1)
        targets = rewards + (1 - dones.astype(np.float32)) * self.config.discount_factor * max_next_q_values
        
        # Update main model
        loss = self.main_model.update(states, actions, targets)
        
        # Periodically update target model
        self.training_steps += 1
        if self.training_steps % self.config.target_update_frequency == 0:
            self.target_model.copy_weights_from(self.main_model)
            logger.debug(f"Updated target model (step {self.training_steps})")
        
        logger.debug(f"Training step {self.training_steps}, loss: {loss:.4f}")
    
    def save_model(self, path: str) -> None:
        """
        Save the model to a file.
        
        Args:
            path: Path to save the model
        """
        # In a real implementation, this would save the model weights
        # to a file. For simplicity, we'll just log a message.
        logger.info(f"Saving model to {path} (not implemented)")
    
    def load_model(self, path: str) -> None:
        """
        Load the model from a file.
        
        Args:
            path: Path to load the model from
        """
        # In a real implementation, this would load the model weights
        # from a file. For simplicity, we'll just log a message.
        logger.info(f"Loading model from {path} (not implemented)")
    
    def get_action_space(self) -> List[MetaAction]:
        """
        Get the action space.
        
        Returns:
            The list of possible meta-actions
        """
        return self.action_space
    
    def get_state_features(self) -> List[float]:
        """
        Get the current state features.
        
        Returns:
            The current state features
        """
        return self.state_feature_extractor(self.mkb_interface)