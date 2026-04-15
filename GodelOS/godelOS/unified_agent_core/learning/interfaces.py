"""
Interfaces for the learning module.

This module defines the interfaces for the learning components of the UnifiedAgentCore.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class LearningMode(Enum):
    """Learning modes for the learning system."""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"
    META = "meta"


@dataclass
class LearningResult:
    """Result of a learning operation."""
    success: bool
    learned_concepts: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None


@dataclass
class StrategyOptimization:
    """Result of a strategy optimization operation."""
    success: bool
    optimized_strategies: List[str] = field(default_factory=list)
    improvement_metrics: Dict[str, float] = field(default_factory=dict)
    message: Optional[str] = None


@dataclass
class UnifiedExperience:
    """
    Represents an experience that can be learned from.
    
    This can be an interaction, a cognitive process, or any other experience
    that the system can learn from.
    """
    id: str
    type: str  # "interaction", "cognitive", "hybrid"
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())
    feedback: Optional[Dict[str, Any]] = None


class InteractionLearnerInterface(ABC):
    """Interface for the interaction learner."""
    
    @abstractmethod
    async def learn(self, experience: UnifiedExperience) -> LearningResult:
        """
        Learn from an interaction experience.
        
        Args:
            experience: The experience to learn from
            
        Returns:
            The learning result
        """
        pass
    
    @abstractmethod
    async def apply_learning(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply learning to an interaction.
        
        Args:
            interaction_data: The interaction data
            
        Returns:
            The enhanced interaction data
        """
        pass


class CognitiveLearnerInterface(ABC):
    """Interface for the cognitive learner."""
    
    @abstractmethod
    async def learn(self, experience: UnifiedExperience) -> LearningResult:
        """
        Learn from a cognitive experience.
        
        Args:
            experience: The experience to learn from
            
        Returns:
            The learning result
        """
        pass
    
    @abstractmethod
    async def apply_learning(self, thought_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply learning to a thought.
        
        Args:
            thought_data: The thought data
            
        Returns:
            The enhanced thought data
        """
        pass


class PerformanceTrackerInterface(ABC):
    """Interface for the performance tracker."""
    
    @abstractmethod
    async def track(self, experience: UnifiedExperience) -> None:
        """
        Track performance metrics for an experience.
        
        Args:
            experience: The experience to track
        """
        pass
    
    @abstractmethod
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            The performance metrics
        """
        pass


class StrategyOptimizerInterface(ABC):
    """Interface for the strategy optimizer."""
    
    @abstractmethod
    async def optimize(self) -> StrategyOptimization:
        """
        Optimize strategies based on performance metrics.
        
        Returns:
            The optimization result
        """
        pass
    
    @abstractmethod
    async def get_strategy(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get a strategy.
        
        Args:
            strategy_name: The name of the strategy
            
        Returns:
            The strategy
        """
        pass


class AbstractUnifiedLearningManager(ABC):
    """Abstract base class for the UnifiedLearningManager."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the learning manager.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the learning manager.
        
        Returns:
            True if the manager was started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the learning manager.
        
        Returns:
            True if the manager was stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def learn_from_experience(self, experience: UnifiedExperience) -> LearningResult:
        """
        Learn from an experience.
        
        Args:
            experience: The experience to learn from
            
        Returns:
            The learning result
        """
        pass
    
    @abstractmethod
    async def optimize_strategies(self) -> StrategyOptimization:
        """
        Optimize strategies based on performance metrics.
        
        Returns:
            The optimization result
        """
        pass