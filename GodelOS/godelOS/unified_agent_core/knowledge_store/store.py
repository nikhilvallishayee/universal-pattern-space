"""
Unified Knowledge Store Implementation for GodelOS

This module implements the UnifiedKnowledgeStore class, which provides integrated
knowledge management across semantic, episodic, and working memory systems.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union, Type
import asyncio
import uuid

from godelOS.unified_agent_core.knowledge_store.interfaces import (
    Knowledge, Fact, Belief, Hypothesis, Rule, Concept, Experience, Procedure,
    MemoryType, KnowledgeType, Query, QueryResult,
    AbstractUnifiedKnowledgeStore
)
from godelOS.unified_agent_core.knowledge_store.knowledge_integrator import KnowledgeIntegrator

logger = logging.getLogger(__name__)


class MemoryImplementationError(Exception):
    """Exception raised when a memory implementation is missing or invalid."""
    pass


class SemanticMemory:
    """
    Simple implementation of semantic memory.
    
    In a real implementation, this would be more sophisticated, possibly using
    a graph database or other specialized storage.
    """
    
    def __init__(self):
        """Initialize semantic memory."""
        self.items: Dict[str, Union[Fact, Belief, Concept, Rule]] = {}
        self.concept_relations: Dict[str, List[str]] = {}  # concept_id -> related concept_ids
        self.fact_beliefs: Dict[str, List[str]] = {}  # fact_id -> belief_ids
        self.concept_rules: Dict[str, List[str]] = {}  # concept_id -> rule_ids
        self.lock = asyncio.Lock()
    
    async def store(self, item: Union[Fact, Belief, Concept, Rule]) -> bool:
        """Store an item in semantic memory."""
        async with self.lock:
            start = time.perf_counter()
            self.items[item.id] = item
            
            # Update relationships
            if isinstance(item, Concept) and item.related_concepts:
                self.concept_relations[item.id] = item.related_concepts
                
                # Update reverse relationships
                for related_id in item.related_concepts:
                    if related_id in self.items and isinstance(self.items[related_id], Concept):
                        if related_id not in self.concept_relations:
                            self.concept_relations[related_id] = []
                        
                        if item.id not in self.concept_relations[related_id]:
                            self.concept_relations[related_id].append(item.id)
            
            elif isinstance(item, Belief) and hasattr(item, "evidence"):
                for evidence_id in item.evidence:
                    if evidence_id in self.items and isinstance(self.items[evidence_id], Fact):
                        if evidence_id not in self.fact_beliefs:
                            self.fact_beliefs[evidence_id] = []
                        
                        if item.id not in self.fact_beliefs[evidence_id]:
                            self.fact_beliefs[evidence_id].append(item.id)
            
            elif isinstance(item, Rule):
                # Link rule to concepts it references
                for condition in item.conditions:
                    if "concept_id" in condition:
                        concept_id = condition["concept_id"]
                        
                        if concept_id not in self.concept_rules:
                            self.concept_rules[concept_id] = []
                        
                        if item.id not in self.concept_rules[concept_id]:
                            self.concept_rules[concept_id].append(item.id)
            
            dur = time.perf_counter() - start
            if dur > 0.5:
                logger.warning(f"Slow semantic memory store: {dur:.3f}s for item {item.id}")
            else:
                logger.debug(f"Semantic memory store took {dur:.3f}s for item {item.id}")
            return True
    
    async def retrieve(self, item_id: str) -> Optional[Union[Fact, Belief, Concept, Rule]]:
        """Retrieve an item from semantic memory."""
        async with self.lock:
            item = self.items.get(item_id)
            
            if item:
                # Update last accessed time
                item.last_accessed = time.time()
            
            return item
    
    async def query(self, query: Query) -> QueryResult:
        """Query items from semantic memory."""
        async with self.lock:
            start_time = time.time()
            
            # Filter by knowledge types
            if query.knowledge_types:
                items = [
                    item for item in self.items.values()
                    if item.type in query.knowledge_types
                ]
            else:
                items = list(self.items.values())
            
            # Apply content filters if specified
            if "text" in query.content:
                text = query.content["text"].lower()
                items = [
                    item for item in items
                    if isinstance(item.content, dict) and
                    any(str(v).lower().find(text) >= 0 for v in item.content.values())
                ]
            
            # Sort by relevance (simplified)
            items.sort(key=lambda x: x.last_accessed, reverse=True)
            
            # Apply limit
            total_items = len(items)
            items = items[:query.max_results]
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                query_id=query.id,
                items=items,
                total_items=total_items,
                execution_time=execution_time
            )
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update an item in semantic memory."""
        async with self.lock:
            if item_id not in self.items:
                return False
            
            item = self.items[item_id]
            
            # Update item attributes
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            
            return True
    
    async def delete(self, item_id: str) -> bool:
        """Delete an item from semantic memory."""
        async with self.lock:
            if item_id not in self.items:
                return False
            
            # Remove from items
            del self.items[item_id]
            
            # Remove from relationships
            if item_id in self.concept_relations:
                # Remove reverse relationships
                for related_id in self.concept_relations[item_id]:
                    if related_id in self.concept_relations:
                        if item_id in self.concept_relations[related_id]:
                            self.concept_relations[related_id].remove(item_id)
                
                del self.concept_relations[item_id]
            
            if item_id in self.fact_beliefs:
                del self.fact_beliefs[item_id]
            
            if item_id in self.concept_rules:
                del self.concept_rules[item_id]
            
            return True
    
    async def get_related_concepts(self, concept_id: str) -> List[Concept]:
        """Get concepts related to a concept."""
        async with self.lock:
            if concept_id not in self.concept_relations:
                return []
            
            related_ids = self.concept_relations[concept_id]
            return [
                self.items[related_id] for related_id in related_ids
                if related_id in self.items and isinstance(self.items[related_id], Concept)
            ]
    
    async def get_beliefs_for_fact(self, fact_id: str) -> List[Belief]:
        """Get beliefs related to a fact."""
        async with self.lock:
            if fact_id not in self.fact_beliefs:
                return []
            
            belief_ids = self.fact_beliefs[fact_id]
            return [
                self.items[belief_id] for belief_id in belief_ids
                if belief_id in self.items and isinstance(self.items[belief_id], Belief)
            ]
    
    async def get_rules_for_concept(self, concept_id: str) -> List[Rule]:
        """Get rules related to a concept."""
        async with self.lock:
            if concept_id not in self.concept_rules:
                return []
            
            rule_ids = self.concept_rules[concept_id]
            return [
                self.items[rule_id] for rule_id in rule_ids
                if rule_id in self.items and isinstance(self.items[rule_id], Rule)
            ]


class EpisodicMemory:
    """
    Simple implementation of episodic memory.
    
    In a real implementation, this would be more sophisticated, possibly using
    a temporal database or other specialized storage.
    """
    
    def __init__(self):
        """Initialize episodic memory."""
        self.items: Dict[str, Experience] = {}
        self.time_index: Dict[int, List[str]] = {}  # day timestamp -> list of experience_ids
        self.context_index: Dict[str, Dict[str, List[str]]] = {}  # context_key -> {context_value -> list of experience_ids}
        self.lock = asyncio.Lock()
    
    async def store(self, item: Experience) -> bool:
        """Store an item in episodic memory."""
        async with self.lock:
            start = time.perf_counter()
            self.items[item.id] = item
            
            # Index by day
            day_timestamp = int(item.timestamp / 86400) * 86400  # Round to day
            if day_timestamp not in self.time_index:
                self.time_index[day_timestamp] = []
            
            self.time_index[day_timestamp].append(item.id)
            
            # Index by context
            for key, value in item.context.items():
                if key not in self.context_index:
                    self.context_index[key] = {}
                
                str_value = str(value)
                if str_value not in self.context_index[key]:
                    self.context_index[key][str_value] = []
                
                self.context_index[key][str_value].append(item.id)
            
            dur = time.perf_counter() - start
            if dur > 0.5:
                logger.warning(f"Slow episodic memory store: {dur:.3f}s for item {item.id}")
            else:
                logger.debug(f"Episodic memory store took {dur:.3f}s for item {item.id}")
            return True
    
    async def retrieve(self, item_id: str) -> Optional[Experience]:
        """Retrieve an item from episodic memory."""
        async with self.lock:
            item = self.items.get(item_id)
            
            if item:
                # Update last accessed time
                item.last_accessed = time.time()
            
            return item
    
    async def query(self, query: Query) -> QueryResult:
        """Query items from episodic memory."""
        async with self.lock:
            start_time = time.time()
            
            # Start with all items
            item_ids = set(self.items.keys())
            
            # Apply time range filter if specified
            if "start_time" in query.content and "end_time" in query.content:
                start_time_filter = query.content["start_time"]
                end_time_filter = query.content["end_time"]
                
                time_filtered_ids = set()
                for day_timestamp in self.time_index:
                    if day_timestamp + 86400 >= start_time_filter and day_timestamp <= end_time_filter:
                        time_filtered_ids.update(self.time_index[day_timestamp])
                
                item_ids = item_ids.intersection(time_filtered_ids)
            
            # Apply context filters if specified
            if "context" in query.content:
                context_filters = query.content["context"]
                
                for key, value in context_filters.items():
                    if key in self.context_index:
                        str_value = str(value)
                        if str_value in self.context_index[key]:
                            item_ids = item_ids.intersection(set(self.context_index[key][str_value]))
                        else:
                            # No matches for this context filter
                            item_ids = set()
                            break
            
            # Convert IDs to items
            items = [self.items[item_id] for item_id in item_ids if item_id in self.items]
            
            # Sort by timestamp (most recent first)
            items.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            total_items = len(items)
            items = items[:query.max_results]
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                query_id=query.id,
                items=items,
                total_items=total_items,
                execution_time=execution_time
            )
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update an item in episodic memory."""
        async with self.lock:
            if item_id not in self.items:
                return False
            
            item = self.items[item_id]
            
            # Update item attributes
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            
            return True
    
    async def delete(self, item_id: str) -> bool:
        """Delete an item from episodic memory."""
        async with self.lock:
            if item_id not in self.items:
                return False
            
            item = self.items[item_id]
            
            # Remove from items
            del self.items[item_id]
            
            # Remove from time index
            day_timestamp = int(item.timestamp / 86400) * 86400
            if day_timestamp in self.time_index and item_id in self.time_index[day_timestamp]:
                self.time_index[day_timestamp].remove(item_id)
                
                if not self.time_index[day_timestamp]:
                    del self.time_index[day_timestamp]
            
            # Remove from context index
            for key, value in item.context.items():
                str_value = str(value)
                if key in self.context_index and str_value in self.context_index[key]:
                    if item_id in self.context_index[key][str_value]:
                        self.context_index[key][str_value].remove(item_id)
                        
                        if not self.context_index[key][str_value]:
                            del self.context_index[key][str_value]
                            
                            if not self.context_index[key]:
                                del self.context_index[key]
            
            return True
    
    async def get_experiences_in_time_range(self, start_time: float, end_time: float) -> List[Experience]:
        """Get experiences in a time range."""
        async with self.lock:
            # Find relevant day timestamps
            relevant_days = [
                day_timestamp for day_timestamp in self.time_index
                if day_timestamp + 86400 >= start_time and day_timestamp <= end_time
            ]
            
            # Get all experience IDs from relevant days
            experience_ids = []
            for day_timestamp in relevant_days:
                experience_ids.extend(self.time_index[day_timestamp])
            
            # Filter by exact time range and convert to items
            experiences = []
            for experience_id in experience_ids:
                if experience_id in self.items:
                    experience = self.items[experience_id]
                    if experience.timestamp >= start_time and experience.timestamp <= end_time:
                        experiences.append(experience)
            
            # Sort by timestamp
            experiences.sort(key=lambda x: x.timestamp)
            
            return experiences
    
    async def get_experiences_by_context(self, context_key: str, context_value: Any) -> List[Experience]:
        """Get experiences by context."""
        async with self.lock:
            if context_key not in self.context_index:
                return []
            
            str_value = str(context_value)
            if str_value not in self.context_index[context_key]:
                return []
            
            experience_ids = self.context_index[context_key][str_value]
            experiences = [self.items[eid] for eid in experience_ids if eid in self.items]
            
            # Sort by timestamp (most recent first)
            experiences.sort(key=lambda x: x.timestamp, reverse=True)
            
            return experiences
    
    async def get_recent_experiences(self, max_count: int = 10) -> List[Experience]:
        """Get recent experiences."""
        async with self.lock:
            # Get all experiences
            experiences = list(self.items.values())
            
            # Sort by timestamp (most recent first)
            experiences.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            return experiences[:max_count]


class WorkingMemory:
    """
    Simple implementation of working memory.
    
    In a real implementation, this would be more sophisticated, possibly using
    a cache or other fast access storage.
    """
    
    def __init__(self, capacity: int = 100, default_ttl: float = 3600):
        """
        Initialize working memory.
        
        Args:
            capacity: Maximum number of items to store
            default_ttl: Default time-to-live in seconds
        """
        self.items: Dict[str, Knowledge] = {}
        self.priorities: Dict[str, float] = {}
        self.expiration_times: Dict[str, float] = {}
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.lock = asyncio.Lock()
    
    async def store(self, item: Knowledge) -> bool:
        """Store an item in working memory."""
        async with self.lock:
            # Check if we need to make room
            if len(self.items) >= self.capacity and item.id not in self.items:
                await self._evict_items()
            
            self.items[item.id] = item
            
            # Set priority based on item confidence
            self.priorities[item.id] = item.confidence
            
            # Set expiration time
            ttl = item.metadata.get("ttl", self.default_ttl)
            self.expiration_times[item.id] = time.time() + ttl
            
            return True
    
    async def retrieve(self, item_id: str) -> Optional[Knowledge]:
        """Retrieve an item from working memory."""
        async with self.lock:
            # Check if item exists and is not expired
            if item_id in self.items and time.time() < self.expiration_times[item_id]:
                item = self.items[item_id]
                
                # Update last accessed time
                item.last_accessed = time.time()
                
                # Extend expiration time on access
                self.expiration_times[item_id] = time.time() + self.default_ttl
                
                return item
            
            return None
    
    async def query(self, query: Query) -> QueryResult:
        """Query items from working memory."""
        async with self.lock:
            start_time = time.time()
            
            # Filter out expired items
            current_time = time.time()
            valid_items = [
                item for item_id, item in self.items.items()
                if current_time < self.expiration_times[item_id]
            ]
            
            # Filter by knowledge types
            if query.knowledge_types:
                valid_items = [
                    item for item in valid_items
                    if item.type in query.knowledge_types
                ]
            
            # Apply content filters if specified
            if "text" in query.content:
                text = query.content["text"].lower()
                valid_items = [
                    item for item in valid_items
                    if isinstance(item.content, dict) and
                    any(str(v).lower().find(text) >= 0 for v in item.content.values())
                ]
            
            # Sort by priority
            valid_items.sort(key=lambda x: self.priorities.get(x.id, 0), reverse=True)
            
            # Apply limit
            total_items = len(valid_items)
            valid_items = valid_items[:query.max_results]
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                query_id=query.id,
                items=valid_items,
                total_items=total_items,
                execution_time=execution_time
            )
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update an item in working memory."""
        async with self.lock:
            if item_id not in self.items or time.time() >= self.expiration_times[item_id]:
                return False
            
            item = self.items[item_id]
            
            # Update item attributes
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
                    
                    # Update priority if confidence is updated
                    if key == "confidence":
                        self.priorities[item_id] = value
            
            return True
    
    async def delete(self, item_id: str) -> bool:
        """Delete an item from working memory."""
        async with self.lock:
            if item_id not in self.items:
                return False
            
            # Remove item
            del self.items[item_id]
            
            # Remove from priority and expiration maps
            if item_id in self.priorities:
                del self.priorities[item_id]
            
            if item_id in self.expiration_times:
                del self.expiration_times[item_id]
            
            return True
    
    async def set_priority(self, item_id: str, priority: float) -> bool:
        """Set the priority of an item in working memory."""
        async with self.lock:
            if item_id not in self.items or time.time() >= self.expiration_times[item_id]:
                return False
            
            self.priorities[item_id] = priority
            return True
    
    async def get_high_priority_items(self, max_count: int = 10) -> List[Knowledge]:
        """Get high-priority items from working memory."""
        async with self.lock:
            # Filter out expired items
            current_time = time.time()
            valid_items = [
                item for item_id, item in self.items.items()
                if current_time < self.expiration_times[item_id]
            ]
            
            # Sort by priority
            valid_items.sort(key=lambda x: self.priorities.get(x.id, 0), reverse=True)
            
            # Apply limit
            return valid_items[:max_count]
    
    async def clear_expired_items(self) -> int:
        """Clear expired items from working memory."""
        async with self.lock:
            current_time = time.time()
            expired_ids = [
                item_id for item_id in self.items
                if current_time >= self.expiration_times[item_id]
            ]
            
            # Remove expired items
            for item_id in expired_ids:
                del self.items[item_id]
                
                if item_id in self.priorities:
                    del self.priorities[item_id]
                
                if item_id in self.expiration_times:
                    del self.expiration_times[item_id]
            
            return len(expired_ids)
    
    async def _evict_items(self) -> None:
        """Evict items to make room for new ones."""
        # First, clear expired items
        await self.clear_expired_items()
        
        # If still at capacity, evict lowest priority items
        if len(self.items) >= self.capacity:
            # Sort items by priority
            sorted_items = sorted(
                self.items.keys(),
                key=lambda x: self.priorities.get(x, 0)
            )
            
            # Remove lowest priority items
            items_to_remove = sorted_items[:len(self.items) - self.capacity + 1]
            
            for item_id in items_to_remove:
                del self.items[item_id]
                
                if item_id in self.priorities:
                    del self.priorities[item_id]
                
                if item_id in self.expiration_times:
                    del self.expiration_times[item_id]


class UnifiedKnowledgeStore(AbstractUnifiedKnowledgeStore):
    """
    UnifiedKnowledgeStore implementation for GodelOS.
    
    The UnifiedKnowledgeStore provides integrated knowledge management across
    semantic, episodic, and working memory systems.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the unified knowledge store.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        
        self.config = config or {}
        
        # Initialize memory systems
        self.semantic_memory = SemanticMemory()
        self.episodic_memory = EpisodicMemory()
        self.working_memory = WorkingMemory(
            capacity=self.config.get("working_memory_capacity", 100),
            default_ttl=self.config.get("working_memory_ttl", 3600)
        )
        
        # Initialize knowledge integrator
        self.knowledge_integrator = KnowledgeIntegrator()
        self.knowledge_integrator.set_memories(
            self.semantic_memory,
            self.episodic_memory,
            self.working_memory
        )
        
        # Initialize knowledge type mapping
        self.knowledge_type_map: Dict[KnowledgeType, Type[Knowledge]] = {
            KnowledgeType.FACT: Fact,
            KnowledgeType.BELIEF: Belief,
            KnowledgeType.HYPOTHESIS: Hypothesis,
            KnowledgeType.RULE: Rule,
            KnowledgeType.CONCEPT: Concept,
            KnowledgeType.EXPERIENCE: Experience,
            KnowledgeType.PROCEDURE: Procedure
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the knowledge store.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self.is_initialized:
            logger.warning("UnifiedKnowledgeStore is already initialized")
            return True
        
        try:
            logger.info("Initializing UnifiedKnowledgeStore")
            
            self.is_initialized = True
            logger.info("UnifiedKnowledgeStore initialized successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing UnifiedKnowledgeStore: {e}")
            return False
    
    async def start(self) -> bool:
        """
        Start the knowledge store.
        
        Returns:
            True if the store was started successfully, False otherwise
        """
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                return False
        
        if self.is_running:
            logger.warning("UnifiedKnowledgeStore is already running")
            return True
        
        try:
            logger.info("Starting UnifiedKnowledgeStore")
            
            self.is_running = True
            logger.info("UnifiedKnowledgeStore started successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error starting UnifiedKnowledgeStore: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the knowledge store.
        
        Returns:
            True if the store was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("UnifiedKnowledgeStore is not running")
            return True
        
        try:
            logger.info("Stopping UnifiedKnowledgeStore")
            
            # Perform any cleanup
            
            self.is_running = False
            logger.info("UnifiedKnowledgeStore stopped successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error stopping UnifiedKnowledgeStore: {e}")
            return False
    
    async def store_knowledge(self, item: Union[Knowledge, Dict[str, Any]], memory_type: Optional[MemoryType] = None) -> bool:
        """
        Store a knowledge item.
        
        Args:
            item: The knowledge item to store
            memory_type: Optional memory type override
            
        Returns:
            True if the item was stored successfully, False otherwise
        """
        if not self.is_running:
            raise RuntimeError("UnifiedKnowledgeStore is not running")
        
        try:
            # Convert dict to Knowledge object if needed
            if isinstance(item, dict):
                item = self._create_knowledge_from_dict(item)
            
            # Determine memory type if not specified
            if memory_type is None:
                memory_type = self._determine_memory_type(item)
            
            # Get item id for logging
            if isinstance(item, dict):
                item_id = item.get('id', 'unknown')
            else:
                item_id = getattr(item, 'id', 'unknown')
            
            logger.info(f"🔍 DEBUG: Storing knowledge item {item_id} of type {item.type.value if hasattr(item, 'type') else 'unknown'} in {memory_type.value}")
            
            # Integrate knowledge
            success = await self.knowledge_integrator.integrate_knowledge(item, memory_type)
            
            logger.info(f"🔍 DEBUG: Finished storing knowledge item {item_id}, success: {success}")
            return success
        except Exception as e:
            logger.error(f"Error storing knowledge: {e}")
            return False
    
    async def retrieve_knowledge(self, item_id: str, memory_types: Optional[List[MemoryType]] = None) -> Optional[Knowledge]:
        """
        Retrieve a knowledge item by ID.
        
        Args:
            item_id: The ID of the item to retrieve
            memory_types: Optional list of memory types to search
            
        Returns:
            The knowledge item, or None if not found
        """
        if not self.is_running:
            raise RuntimeError("UnifiedKnowledgeStore is not running")
        
        # Default to all memory types
        if memory_types is None:
            memory_types = [MemoryType.WORKING, MemoryType.SEMANTIC, MemoryType.EPISODIC]
        
        # Try working memory first for efficiency
        if MemoryType.WORKING in memory_types:
            item = await self.working_memory.retrieve(item_id)
            if item:
                return item
        
        # Try semantic memory
        if MemoryType.SEMANTIC in memory_types:
            item = await self.semantic_memory.retrieve(item_id)
            if item:
                # Cache in working memory for future access
                await self.working_memory.store(item)
                return item
        
        # Try episodic memory
        if MemoryType.EPISODIC in memory_types:
            item = await self.episodic_memory.retrieve(item_id)
            if item:
                # Cache in working memory for future access
                await self.working_memory.store(item)
                return item
        
        return None
    
    async def query_knowledge(self, query: Union[Query, Dict[str, Any]]) -> QueryResult:
        """
        Query knowledge items.
        
        Args:
            query: The query to execute
            
        Returns:
            The query result
        """
        if not self.is_running:
            raise RuntimeError("UnifiedKnowledgeStore is not running")
        
        # Convert dict to Query object if needed
        if isinstance(query, dict):
            query = self._create_query_from_dict(query)
        
        # Determine memory types to query
        memory_types = query.memory_types or [MemoryType.WORKING, MemoryType.SEMANTIC, MemoryType.EPISODIC]
        
        all_results = []
        total_items = 0
        execution_time = 0
        
        # Query each memory type
        for memory_type in memory_types:
            if memory_type == MemoryType.WORKING:
                result = await self.working_memory.query(query)
            elif memory_type == MemoryType.SEMANTIC:
                result = await self.semantic_memory.query(query)
            elif memory_type == MemoryType.EPISODIC:
                result = await self.episodic_memory.query(query)
            else:
                continue
            
            all_results.extend(result.items)
            total_items += result.total_items
            execution_time += result.execution_time
        
        # Remove duplicates
        unique_items = []
        seen_ids = set()
        
        for item in all_results:
            if item.id not in seen_ids:
                unique_items.append(item)
                seen_ids.add(item.id)
        
        # Sort by relevance (using last accessed time as a proxy)
        unique_items.sort(key=lambda x: x.last_accessed, reverse=True)
        
        # Apply limit
        unique_items = unique_items[:query.max_results]
        
        return QueryResult(
            query_id=query.id,
            items=unique_items,
            total_items=total_items,
            execution_time=execution_time
        )
    
    async def store_thought_result(self, thought: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """
        Store the result of processing a thought.
        
        Args:
            thought: The thought data
            result: The result of processing the thought
            
        Returns:
            True if the result was stored successfully, False otherwise
        """
        if not self.is_running:
            raise RuntimeError("UnifiedKnowledgeStore is not running")
        
        try:
            # Create knowledge items from thought result
            knowledge_items = self._create_knowledge_from_thought_result(thought, result)
            
            # Store each knowledge item
            success = True
            for item in knowledge_items:
                item_success = await self.store_knowledge(item)
                success = success and item_success
            
            return success
        except Exception as e:
            logger.error(f"Error storing thought result: {e}")
            return False
    
    def _create_knowledge_from_dict(self, data: Dict[str, Any]) -> Knowledge:
        """
        Create a Knowledge object from a dictionary.
        
        Args:
            data: The dictionary data
            
        Returns:
            The created Knowledge object
        
        Raises:
            ValueError: If the knowledge type is invalid
        """
        # Get knowledge type
        type_str = data.get("type", "fact")
        try:
            knowledge_type = KnowledgeType(type_str)
        except ValueError:
            logger.warning(f"Invalid knowledge type: {type_str}, defaulting to FACT")
            knowledge_type = KnowledgeType.FACT
        
        # Get knowledge class
        knowledge_class = self.knowledge_type_map.get(knowledge_type)
        if not knowledge_class:
            raise ValueError(f"No knowledge class for type: {knowledge_type}")
        
        # Create knowledge item
        item_id = data.get("id", str(uuid.uuid4()))
        content = data.get("content", {})
        confidence = data.get("confidence", 1.0)
        metadata = data.get("metadata", {})
        
        # Create base knowledge item
        item = knowledge_class(
            id=item_id,
            type=knowledge_type,
            content=content,
            confidence=confidence,
            metadata=metadata
        )
        
        # Set type-specific attributes
        if knowledge_type == KnowledgeType.BELIEF and hasattr(item, "evidence"):
            item.evidence = data.get("evidence", [])
        
        elif knowledge_type == KnowledgeType.HYPOTHESIS:
            if hasattr(item, "evidence_for"):
                item.evidence_for = data.get("evidence_for", [])
            if hasattr(item, "evidence_against"):
                item.evidence_against = data.get("evidence_against", [])
        
        elif knowledge_type == KnowledgeType.RULE:
            if hasattr(item, "conditions"):
                item.conditions = data.get("conditions", [])
            if hasattr(item, "actions"):
                item.actions = data.get("actions", [])
        
        elif knowledge_type == KnowledgeType.CONCEPT:
            if hasattr(item, "related_concepts"):
                item.related_concepts = data.get("related_concepts", [])
        
        elif knowledge_type == KnowledgeType.EXPERIENCE:
            if hasattr(item, "timestamp"):
                item.timestamp = data.get("timestamp", time.time())
            if hasattr(item, "duration"):
                item.duration = data.get("duration", 0.0)
            if hasattr(item, "context"):
                item.context = data.get("context", {})
        
        elif knowledge_type == KnowledgeType.PROCEDURE:
            if hasattr(item, "steps"):
                item.steps = data.get("steps", [])
        
        return item
    
    def _create_query_from_dict(self, data: Dict[str, Any]) -> Query:
        """
        Create a Query object from a dictionary.
        
        Args:
            data: The dictionary data
            
        Returns:
            The created Query object
        """
        # Get query parameters
        query_id = data.get("id", str(uuid.uuid4()))
        content = data.get("content", {})
        max_results = data.get("max_results", 100)
        metadata = data.get("metadata", {})
        
        # Get memory types
        memory_types = []
        if "memory_types" in data:
            for type_str in data["memory_types"]:
                try:
                    memory_types.append(MemoryType(type_str))
                except ValueError:
                    logger.warning(f"Invalid memory type: {type_str}")
        
        # Get knowledge types
        knowledge_types = []
        if "knowledge_types" in data:
            for type_str in data["knowledge_types"]:
                try:
                    knowledge_types.append(KnowledgeType(type_str))
                except ValueError:
                    logger.warning(f"Invalid knowledge type: {type_str}")
        
        return Query(
            id=query_id,
            content=content,
            memory_types=memory_types,
            knowledge_types=knowledge_types,
            max_results=max_results,
            metadata=metadata
        )
    
    def _determine_memory_type(self, item: Knowledge) -> MemoryType:
        """
        Determine the appropriate memory type for a knowledge item.
        
        Args:
            item: The knowledge item
            
        Returns:
            The appropriate memory type
        """
        # Facts, beliefs, concepts, and rules go to semantic memory
        if item.type in [KnowledgeType.FACT, KnowledgeType.BELIEF, KnowledgeType.CONCEPT, KnowledgeType.RULE]:
            return MemoryType.SEMANTIC
        
        # Experiences go to episodic memory
        elif item.type == KnowledgeType.EXPERIENCE:
            return MemoryType.EPISODIC
        
        # Hypotheses and other types go to working memory by default
        else:
            return MemoryType.WORKING
    
    def _create_knowledge_from_thought_result(self, thought: Dict[str, Any], result: Dict[str, Any]) -> List[Knowledge]:
        """
        Create knowledge items from a thought result.
        
        Args:
            thought: The thought data
            result: The result of processing the thought
            
        Returns:
            List of created knowledge items
        """
        knowledge_items = []
        
        # Extract thought content and metadata
        thought_content = thought.get("content", "")
        thought_type = thought.get("type", "general")
        thought_id = thought.get("id", "")
        
        # If the result has insights, create a belief for each insight
        if "insights" in result:
            for i, insight in enumerate(result["insights"]):
                belief = Belief(
                    content={
                        "text": insight,
                        "source": "thought_result",
                        "thought_id": thought_id
                    },
                    confidence=0.8,
                    evidence=[thought_id],
                    metadata={
                        "thought_type": thought_type,
                        "insight_index": i
                    }
                )
                knowledge_items.append(belief)
        
        # If the result has ideas, create a hypothesis for each idea
        if "ideas" in result:
            for i, idea in enumerate(result["ideas"]):
                hypothesis = Hypothesis(
                    content={
                        "text": idea.get("content", ""),
                        "source": "thought_result",
                        "thought_id": thought_id
                    },
                    confidence=idea.get("utility_score", 0.5),
                    evidence_for=[thought_id],
                    evidence_against=[],
                    metadata={
                        "thought_type": thought_type,
                        "idea_index": i,
                        "novelty_score": idea.get("novelty_score", 0.5)
                    }
                )
                knowledge_items.append(hypothesis)
        
        # Create an experience record for the thought processing
        experience = Experience(
            content={
                "text": f"Processed thought: {thought_content}",
                "source": "thought_processing",
                "thought_id": thought_id
            },
            confidence=1.0,
            timestamp=result.get("timestamp", time.time()),
            duration=0.0,
            context={
                "thought_type": thought_type,
                "cognitive_load": result.get("cognitive_load", 0.0)
            },
            metadata={
                "thought_id": thought_id,
                "success": result.get("success", True)
            }
        )
        knowledge_items.append(experience)
        
        return knowledge_items