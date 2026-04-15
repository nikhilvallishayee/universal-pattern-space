"""
Unified Knowledge Store Interfaces for GodelOS

This module defines the interfaces for the UnifiedKnowledgeStore component of the
UnifiedAgentCore architecture, including SemanticMemory, EpisodicMemory,
WorkingMemory, and KnowledgeIntegrator.
"""

import abc
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable, TypeVar, Generic, Union
from dataclasses import dataclass, field
import time
import uuid
from enum import Enum


class MemoryType(Enum):
    """Enum representing different types of memory."""
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    WORKING = "working"
    PROCEDURAL = "procedural"


class KnowledgeType(Enum):
    """Enum representing different types of knowledge."""
    FACT = "fact"
    BELIEF = "belief"
    HYPOTHESIS = "hypothesis"
    RULE = "rule"
    CONCEPT = "concept"
    EXPERIENCE = "experience"
    PROCEDURE = "procedure"
    RELATIONSHIP = "relationship"


@dataclass
class Knowledge:
    """Base class for knowledge items in the system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: KnowledgeType = KnowledgeType.FACT
    content: Any = None
    confidence: float = 1.0  # 0.0 to 1.0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Fact(Knowledge):
    """Class representing a factual knowledge item."""
    type: KnowledgeType = KnowledgeType.FACT
    content: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Belief(Knowledge):
    """Class representing a belief knowledge item."""
    type: KnowledgeType = KnowledgeType.BELIEF
    content: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)  # List of knowledge IDs supporting this belief


@dataclass
class Hypothesis(Knowledge):
    """Class representing a hypothesis knowledge item."""
    type: KnowledgeType = KnowledgeType.HYPOTHESIS
    content: Dict[str, Any] = field(default_factory=dict)
    evidence_for: List[str] = field(default_factory=list)  # List of knowledge IDs supporting this hypothesis
    evidence_against: List[str] = field(default_factory=list)  # List of knowledge IDs contradicting this hypothesis


@dataclass
class Rule(Knowledge):
    """Class representing a rule knowledge item."""
    type: KnowledgeType = KnowledgeType.RULE
    content: Dict[str, Any] = field(default_factory=dict)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Concept(Knowledge):
    """Class representing a concept knowledge item."""
    type: KnowledgeType = KnowledgeType.CONCEPT
    content: Dict[str, Any] = field(default_factory=dict)
    related_concepts: List[str] = field(default_factory=list)  # List of related concept IDs


@dataclass
class Experience(Knowledge):
    """Class representing an experiential knowledge item."""
    type: KnowledgeType = KnowledgeType.EXPERIENCE
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Procedure(Knowledge):
    """Class representing a procedural knowledge item."""
    type: KnowledgeType = KnowledgeType.PROCEDURE
    content: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Relationship(Knowledge):
    """Class representing a relationship between two knowledge items."""
    type: KnowledgeType = KnowledgeType.RELATIONSHIP
    source_id: str = ""
    target_id: str = ""
    relation_type: str = ""
    content: Dict[str, Any] = field(default_factory=dict) # To store the original sentence/context


@dataclass
class Query:
    """Class representing a query to the knowledge store."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: Dict[str, Any] = field(default_factory=dict)
    memory_types: List[MemoryType] = field(default_factory=list)
    knowledge_types: List[KnowledgeType] = field(default_factory=list)
    max_results: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """Class representing the result of a query to the knowledge store."""
    query_id: str = ""
    items: List[Knowledge] = field(default_factory=list)
    total_items: int = 0
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar('T', bound=Knowledge)


@runtime_checkable
class MemoryInterface(Protocol, Generic[T]):
    """Protocol for memory operations."""
    
    async def store(self, item: T) -> bool:
        """
        Store an item in memory.
        
        Args:
            item: The item to store
            
        Returns:
            True if the item was stored successfully, False otherwise
        """
        ...
    
    async def retrieve(self, item_id: str) -> Optional[T]:
        """
        Retrieve an item from memory by ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item, or None if not found
        """
        ...
    
    async def query(self, query: Query) -> QueryResult:
        """
        Query items from memory.
        
        Args:
            query: The query to execute
            
        Returns:
            The query result
        """
        ...
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an item in memory.
        
        Args:
            item_id: The ID of the item to update
            updates: Dictionary of updates to apply to the item
            
        Returns:
            True if the item was updated, False if the item was not found
        """
        ...
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete an item from memory.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if the item was deleted, False if the item was not found
        """
        ...


@runtime_checkable
class SemanticMemoryInterface(MemoryInterface[Union[Fact, Belief, Concept, Rule, Relationship]], Protocol):
    """Protocol for semantic memory operations."""
    
    async def get_related_concepts(self, concept_id: str) -> List[Concept]:
        """
        Get concepts related to a concept.
        
        Args:
            concept_id: The ID of the concept
            
        Returns:
            List of related concepts
        """
        ...
    
    async def get_beliefs_for_fact(self, fact_id: str) -> List[Belief]:
        """
        Get beliefs related to a fact.
        
        Args:
            fact_id: The ID of the fact
            
        Returns:
            List of related beliefs
        """
        ...
    
    async def get_rules_for_concept(self, concept_id: str) -> List[Rule]:
        """
        Get rules related to a concept.
        
        Args:
            concept_id: The ID of the concept
            
        Returns:
            List of related rules
        """
        ...


@runtime_checkable
class EpisodicMemoryInterface(MemoryInterface[Experience], Protocol):
    """Protocol for episodic memory operations."""
    
    async def get_experiences_in_time_range(self, start_time: float, end_time: float) -> List[Experience]:
        """
        Get experiences in a time range.
        
        Args:
            start_time: The start time
            end_time: The end time
            
        Returns:
            List of experiences in the time range
        """
        ...
    
    async def get_experiences_by_context(self, context_key: str, context_value: Any) -> List[Experience]:
        """
        Get experiences by context.
        
        Args:
            context_key: The context key
            context_value: The context value
            
        Returns:
            List of experiences matching the context
        """
        ...
    
    async def get_recent_experiences(self, max_count: int = 10) -> List[Experience]:
        """
        Get recent experiences.
        
        Args:
            max_count: Maximum number of experiences to return
            
        Returns:
            List of recent experiences
        """
        ...


@runtime_checkable
class WorkingMemoryInterface(MemoryInterface[Knowledge], Protocol):
    """Protocol for working memory operations."""
    
    async def set_priority(self, item_id: str, priority: float) -> bool:
        """
        Set the priority of an item in working memory.
        
        Args:
            item_id: The ID of the item
            priority: The priority (0.0 to 1.0)
            
        Returns:
            True if the priority was set, False if the item was not found
        """
        ...
    
    async def get_high_priority_items(self, max_count: int = 10) -> List[Knowledge]:
        """
        Get high-priority items from working memory.
        
        Args:
            max_count: Maximum number of items to return
            
        Returns:
            List of high-priority items
        """
        ...
    
    async def clear_expired_items(self) -> int:
        """
        Clear expired items from working memory.
        
        Returns:
            Number of items cleared
        """
        ...


@runtime_checkable
class KnowledgeIntegratorInterface(Protocol):
    """Protocol for knowledge integration operations."""
    
    async def integrate_knowledge(self, item: Knowledge, memory_type: MemoryType) -> bool:
        """
        Integrate a knowledge item into the appropriate memory.
        
        Args:
            item: The knowledge item to integrate
            memory_type: The target memory type
            
        Returns:
            True if the item was integrated successfully, False otherwise
        """
        ...
    
    async def consolidate_memories(self) -> Dict[str, int]:
        """
        Consolidate memories (e.g., from working to long-term).
        
        Returns:
            Dictionary mapping memory types to number of items consolidated
        """
        ...
    
    async def resolve_conflicts(self) -> Dict[str, int]:
        """
        Resolve conflicts in knowledge.
        
        Returns:
            Dictionary mapping conflict types to number of conflicts resolved
        """
        ...
    
    async def generate_inferences(self) -> List[Knowledge]:
        """
        Generate inferences from existing knowledge.
        
        Returns:
            List of inferred knowledge items
        """
        ...


class UnifiedKnowledgeStoreInterface(abc.ABC):
    """Abstract base class for unified knowledge store implementations."""
    
    @abc.abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the knowledge store.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def start(self) -> bool:
        """
        Start the knowledge store.
        
        Returns:
            True if the store was started successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def stop(self) -> bool:
        """
        Stop the knowledge store.
        
        Returns:
            True if the store was stopped successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def store_knowledge(self, item: Knowledge, memory_type: Optional[MemoryType] = None) -> bool:
        """
        Store a knowledge item.
        
        Args:
            item: The knowledge item to store
            memory_type: Optional memory type override
            
        Returns:
            True if the item was stored successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def retrieve_knowledge(self, item_id: str, memory_types: Optional[List[MemoryType]] = None) -> Optional[Knowledge]:
        """
        Retrieve a knowledge item by ID.
        
        Args:
            item_id: The ID of the item to retrieve
            memory_types: Optional list of memory types to search
            
        Returns:
            The knowledge item, or None if not found
        """
        pass
    
    @abc.abstractmethod
    async def query_knowledge(self, query: Query) -> QueryResult:
        """
        Query knowledge items.
        
        Args:
            query: The query to execute
            
        Returns:
            The query result
        """
        pass
    
    @abc.abstractmethod
    async def store_thought_result(self, thought: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """
        Store the result of processing a thought.
        
        Args:
            thought: The thought data
            result: The result of processing the thought
            
        Returns:
            True if the result was stored successfully, False otherwise
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
        Get the status of the knowledge store.
        
        Returns:
            Dictionary with status information
        """
        pass


class AbstractUnifiedKnowledgeStore(UnifiedKnowledgeStoreInterface):
    """
    Abstract implementation of the UnifiedKnowledgeStoreInterface.
    
    This class provides a base implementation of the UnifiedKnowledgeStoreInterface
    with common functionality that concrete implementations can build upon.
    """
    
    def __init__(self):
        """Initialize the abstract unified knowledge store."""
        self.semantic_memory = None
        self.episodic_memory = None
        self.working_memory = None
        self.knowledge_integrator = None
        self.state = None
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
    
    def set_resource_manager(self, resource_manager: Any) -> None:
        """
        Set the resource manager reference.
        
        Args:
            resource_manager: The unified resource manager
        """
        self.resource_manager = resource_manager
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the knowledge store.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "components": {
                "semantic_memory": bool(self.semantic_memory),
                "episodic_memory": bool(self.episodic_memory),
                "working_memory": bool(self.working_memory),
                "knowledge_integrator": bool(self.knowledge_integrator)
            }
        }