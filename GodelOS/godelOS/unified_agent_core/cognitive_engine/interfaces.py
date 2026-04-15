"""
Cognitive Engine Interfaces for GodelOS

This module defines the interfaces for the CognitiveEngine component of the
UnifiedAgentCore architecture, including ThoughtStream, ReflectionEngine,
IdeationEngine, and MetacognitiveMonitor.
"""

import abc
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable
from dataclasses import dataclass, field
import time
import uuid


@dataclass
class Thought:
    """Class representing a thought in the cognitive system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    type: str = "general"  # "general", "question", "insight", "hypothesis", etc.
    priority: float = 0.5  # 0.0 to 1.0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Reflection:
    """Class representing a reflection on a thought."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    thought_id: str = ""
    content: str = ""
    insights: List[str] = field(default_factory=list)
    should_ideate: bool = False
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Idea:
    """Class representing an idea generated from a thought and reflection."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    thought_id: str = ""
    reflection_id: str = ""
    content: str = ""
    novelty_score: float = 0.5  # 0.0 to 1.0
    utility_score: float = 0.5  # 0.0 to 1.0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveContext:
    """Class representing the context for cognitive operations."""
    active_thoughts: List[str] = field(default_factory=list)
    attention_focus: str = ""
    cognitive_load: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ThoughtInterface(Protocol):
    """Protocol for thought-related operations."""
    
    async def add_thought(self, thought: Thought, priority: Optional[float] = None) -> bool:
        """
        Add a thought to the thought stream.
        
        Args:
            thought: The thought to add
            priority: Optional priority override
            
        Returns:
            True if the thought was added successfully, False otherwise
        """
        ...
    
    async def get_priority_thoughts(self, max_thoughts: int = 10) -> List[Thought]:
        """
        Get the highest priority thoughts.
        
        Args:
            max_thoughts: Maximum number of thoughts to return
            
        Returns:
            List of highest priority thoughts
        """
        ...
    
    async def get_thought_by_id(self, thought_id: str) -> Optional[Thought]:
        """
        Get a thought by ID.
        
        Args:
            thought_id: The ID of the thought to get
            
        Returns:
            The thought, or None if not found
        """
        ...
    
    async def update_thought(self, thought_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a thought.
        
        Args:
            thought_id: The ID of the thought to update
            updates: Dictionary of updates to apply to the thought
            
        Returns:
            True if the thought was updated, False if the thought was not found
        """
        ...


@runtime_checkable
class ReflectionEngineInterface(Protocol):
    """Protocol for reflection operations."""
    
    async def reflect(self, thought: Thought, context: CognitiveContext) -> Reflection:
        """
        Reflect on a thought.
        
        Args:
            thought: The thought to reflect on
            context: The cognitive context
            
        Returns:
            A reflection on the thought
        """
        ...
    
    async def get_reflection_by_id(self, reflection_id: str) -> Optional[Reflection]:
        """
        Get a reflection by ID.
        
        Args:
            reflection_id: The ID of the reflection to get
            
        Returns:
            The reflection, or None if not found
        """
        ...
    
    async def get_reflections_for_thought(self, thought_id: str) -> List[Reflection]:
        """
        Get all reflections for a thought.
        
        Args:
            thought_id: The ID of the thought
            
        Returns:
            List of reflections for the thought
        """
        ...


@runtime_checkable
class IdeationEngineInterface(Protocol):
    """Protocol for ideation operations."""
    
    async def generate_ideas(self, thought: Thought, reflection: Reflection, context: CognitiveContext) -> List[Idea]:
        """
        Generate ideas based on a thought and reflection.
        
        Args:
            thought: The thought
            reflection: The reflection on the thought
            context: The cognitive context
            
        Returns:
            List of generated ideas
        """
        ...
    
    async def evaluate_idea(self, idea: Idea, context: CognitiveContext) -> Dict[str, float]:
        """
        Evaluate an idea.
        
        Args:
            idea: The idea to evaluate
            context: The cognitive context
            
        Returns:
            Dictionary of evaluation metrics
        """
        ...
    
    async def get_ideas_for_thought(self, thought_id: str) -> List[Idea]:
        """
        Get all ideas for a thought.
        
        Args:
            thought_id: The ID of the thought
            
        Returns:
            List of ideas for the thought
        """
        ...


@runtime_checkable
class MetacognitiveMonitorInterface(Protocol):
    """Protocol for metacognitive monitoring operations."""
    
    async def update_state(self, thought: Thought, reflection: Optional[Reflection], context: CognitiveContext) -> None:
        """
        Update the metacognitive state.
        
        Args:
            thought: The current thought
            reflection: Optional reflection on the thought
            context: The cognitive context
        """
        ...
    
    async def get_cognitive_load(self) -> float:
        """
        Get the current cognitive load.
        
        Returns:
            The cognitive load (0.0 to 1.0)
        """
        ...
    
    async def get_attention_allocation(self) -> Dict[str, float]:
        """
        Get the current attention allocation.
        
        Returns:
            Dictionary mapping focus areas to allocation values
        """
        ...
    
    async def should_reflect(self, thought: Thought, context: CognitiveContext) -> bool:
        """
        Determine if reflection should be performed on a thought.
        
        Args:
            thought: The thought to consider
            context: The cognitive context
            
        Returns:
            True if reflection should be performed, False otherwise
        """
        ...


class CognitiveEngineInterface(abc.ABC):
    """Abstract base class for cognitive engine implementations."""
    
    @abc.abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the cognitive engine.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def start(self) -> bool:
        """
        Start the cognitive engine.
        
        Returns:
            True if the engine was started successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def stop(self) -> bool:
        """
        Stop the cognitive engine.
        
        Returns:
            True if the engine was stopped successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def process_thought(self, thought_data: Dict[str, Any], resources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a thought.
        
        Args:
            thought_data: The thought data
            resources: The resources allocated for processing
            
        Returns:
            The result of processing the thought
        """
        pass
    
    @abc.abstractmethod
    async def generate_response(self, interaction: Dict[str, Any], initial_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a cognitive response to an interaction.
        
        Args:
            interaction: The interaction
            initial_response: The initial response
            
        Returns:
            The cognitive response
        """
        pass
    
    @abc.abstractmethod
    def set_state(self, state: Any) -> None:
        """
        Set the unified state reference.
        
        Args:
            state: The unified state
        """
        pass
    
    @abc.abstractmethod
    def set_knowledge_store(self, knowledge_store: Any) -> None:
        """
        Set the knowledge store reference.
        
        Args:
            knowledge_store: The unified knowledge store
        """
        pass
    
    @abc.abstractmethod
    def set_resource_manager(self, resource_manager: Any) -> None:
        """
        Set the resource manager reference.
        
        Args:
            resource_manager: The unified resource manager
        """
        pass
    
    @abc.abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the cognitive engine.
        
        Returns:
            Dictionary with status information
        """
        pass


class AbstractCognitiveEngine(CognitiveEngineInterface):
    """
    Abstract implementation of the CognitiveEngineInterface.
    
    This class provides a base implementation of the CognitiveEngineInterface
    with common functionality that concrete implementations can build upon.
    """
    
    def __init__(self):
        """Initialize the abstract cognitive engine."""
        self.thought_stream = None
        self.reflection_engine = None
        self.ideation_engine = None
        self.metacognitive_monitor = None
        self.state = None
        self.knowledge_store = None
        self.resource_manager = None
        self.is_initialized = False
        self.is_running = False
    
    def set_state(self, state: Any) -> None:
        """
        Set the unified state reference.
        
        Args:
            state: The unified state
        """
        self.state = state
    
    def set_knowledge_store(self, knowledge_store: Any) -> None:
        """
        Set the knowledge store reference.
        
        Args:
            knowledge_store: The unified knowledge store
        """
        self.knowledge_store = knowledge_store
    
    def set_resource_manager(self, resource_manager: Any) -> None:
        """
        Set the resource manager reference.
        
        Args:
            resource_manager: The unified resource manager
        """
        self.resource_manager = resource_manager
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the cognitive engine.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "components": {
                "thought_stream": bool(self.thought_stream),
                "reflection_engine": bool(self.reflection_engine),
                "ideation_engine": bool(self.ideation_engine),
                "metacognitive_monitor": bool(self.metacognitive_monitor)
            }
        }