"""
Episodic Memory Store Implementation for GodelOS

This module implements a specialized episodic memory store that handles
temporal storage and retrieval of experiences with time-based querying,
context-based retrieval, and episodic decay mechanisms.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Union, Set, Tuple
import uuid
from dataclasses import dataclass, field
import heapq
from datetime import datetime
from collections import defaultdict

from godelOS.unified_agent_core.knowledge_store.interfaces import (
    Knowledge, Experience, 
    KnowledgeType, Query, QueryResult,
    EpisodicMemoryInterface
)

logger = logging.getLogger(__name__)


class EpisodicMemory(EpisodicMemoryInterface):
    """
    Specialized implementation of episodic memory for GodelOS.
    
    This implementation provides:
    - Temporal storage and retrieval of experiences
    - Time-based querying and context-based retrieval
    - Episodic decay and consolidation mechanisms
    - Temporal clustering and sequence detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize episodic memory.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Primary storage for experiences
        self.items: Dict[str, Experience] = {}
        
        # Temporal indexing
        self.time_index: Dict[int, List[str]] = {}  # day timestamp -> list of experience_ids
        self.hour_index: Dict[int, List[str]] = {}  # hour timestamp -> list of experience_ids
        self.timeline: List[Tuple[float, str]] = []  # sorted list of (timestamp, experience_id)
        
        # Context indexing
        self.context_index: Dict[str, Dict[str, List[str]]] = {}  # context_key -> {context_value -> list of experience_ids}
        self.location_index: Dict[str, List[str]] = {}  # location -> list of experience_ids
        self.agent_index: Dict[str, List[str]] = {}  # agent_id -> list of experience_ids
        
        # Sequence detection
        self.sequence_index: Dict[str, List[str]] = {}  # sequence_id -> ordered list of experience_ids
        
        # Memory decay parameters
        self.decay_rate = self.config.get("decay_rate", 0.05)  # Rate of memory decay per day
        self.importance_threshold = self.config.get("importance_threshold", 0.2)  # Threshold for memory retention
        self.last_decay_time = time.time()
        
        # Thread safety
        self.lock = asyncio.Lock()
    
    async def store(self, item: Experience) -> bool:
        """
        Store an experience in episodic memory.
        
        Args:
            item: The experience to store
            
        Returns:
            True if the experience was stored successfully, False otherwise
        """
        async with self.lock:
            try:
                # Store the item
                self.items[item.id] = item
                
                # Index by time
                await self._index_by_time(item)
                
                # Index by context
                await self._index_by_context(item)
                
                # Update sequences if applicable
                if "sequence_id" in item.metadata:
                    await self._update_sequence(item)
                
                # Set initial importance if not set
                if "importance" not in item.metadata:
                    item.metadata["importance"] = self._calculate_initial_importance(item)
                
                logger.debug(f"Stored experience with ID {item.id} in episodic memory")
                return True
            except Exception as e:
                logger.error(f"Error storing experience in episodic memory: {e}")
                return False
    
    async def retrieve(self, item_id: str) -> Optional[Experience]:
        """
        Retrieve an experience from episodic memory.
        
        Args:
            item_id: The ID of the experience to retrieve
            
        Returns:
            The experience, or None if not found
        """
        async with self.lock:
            item = self.items.get(item_id)
            
            if item:
                # Update last accessed time
                item.last_accessed = time.time()
                
                # Boost importance on access
                if "importance" in item.metadata:
                    item.metadata["importance"] = min(1.0, item.metadata["importance"] * 1.2)
            
            return item
    
    async def query(self, query: Query) -> QueryResult:
        """
        Query experiences from episodic memory.
        
        Args:
            query: The query to execute
            
        Returns:
            The query result
        """
        async with self.lock:
            start_time = time.time()
            
            # Start with all items
            item_ids = set(self.items.keys())
            
            # Apply time range filter if specified
            if "start_time" in query.content and "end_time" in query.content:
                start_time_filter = query.content["start_time"]
                end_time_filter = query.content["end_time"]
                
                time_filtered_ids = await self._get_experiences_in_time_range(
                    start_time_filter, end_time_filter
                )
                item_ids = item_ids.intersection(time_filtered_ids)
            
            # Apply context filters if specified
            if "context" in query.content:
                context_filters = query.content["context"]
                
                for key, value in context_filters.items():
                    context_filtered_ids = await self._get_experiences_by_context(key, value)
                    item_ids = item_ids.intersection(context_filtered_ids)
            
            # Apply location filter if specified
            if "location" in query.content:
                location = query.content["location"]
                location_filtered_ids = set(self.location_index.get(location, []))
                item_ids = item_ids.intersection(location_filtered_ids)
            
            # Apply agent filter if specified
            if "agent_id" in query.content:
                agent_id = query.content["agent_id"]
                agent_filtered_ids = set(self.agent_index.get(agent_id, []))
                item_ids = item_ids.intersection(agent_filtered_ids)
            
            # Apply sequence filter if specified
            if "sequence_id" in query.content:
                sequence_id = query.content["sequence_id"]
                sequence_filtered_ids = set(self.sequence_index.get(sequence_id, []))
                item_ids = item_ids.intersection(sequence_filtered_ids)
            
            # Convert IDs to items
            items = [self.items[item_id] for item_id in item_ids if item_id in self.items]
            
            # Sort by timestamp (default) or importance
            sort_by = query.metadata.get("sort_by", "timestamp")
            if sort_by == "importance":
                items.sort(key=lambda x: x.metadata.get("importance", 0), reverse=True)
            else:  # Default to timestamp
                items.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            total_items = len(items)
            items = items[:query.max_results]
            
            # Update access time for returned items
            for item in items:
                item.last_accessed = time.time()
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                query_id=query.id,
                items=items,
                total_items=total_items,
                execution_time=execution_time,
                metadata={"memory_type": "episodic"}
            )
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an experience in episodic memory.
        
        Args:
            item_id: The ID of the experience to update
            updates: Dictionary of updates to apply to the experience
            
        Returns:
            True if the experience was updated, False if the experience was not found
        """
        async with self.lock:
            if item_id not in self.items:
                return False
            
            item = self.items[item_id]
            old_timestamp = item.timestamp
            old_context = item.context.copy() if hasattr(item, "context") else {}
            
            # Update item attributes
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            
            # If timestamp changed, update time indexes
            if hasattr(item, "timestamp") and old_timestamp != item.timestamp:
                await self._remove_from_time_indexes(item_id, old_timestamp)
                await self._index_by_time(item)
            
            # If context changed, update context indexes
            if hasattr(item, "context") and old_context != item.context:
                await self._remove_from_context_indexes(item_id, old_context)
                await self._index_by_context(item)
            
            # Update last accessed time
            item.last_accessed = time.time()
            
            return True
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete an experience from episodic memory.
        
        Args:
            item_id: The ID of the experience to delete
            
        Returns:
            True if the experience was deleted, False if the experience was not found
        """
        async with self.lock:
            if item_id not in self.items:
                return False
            
            item = self.items[item_id]
            
            # Remove from time indexes
            await self._remove_from_time_indexes(item_id, item.timestamp)
            
            # Remove from context indexes
            await self._remove_from_context_indexes(item_id, item.context)
            
            # Remove from sequence index if applicable
            if "sequence_id" in item.metadata:
                sequence_id = item.metadata["sequence_id"]
                if sequence_id in self.sequence_index and item_id in self.sequence_index[sequence_id]:
                    self.sequence_index[sequence_id].remove(item_id)
                    
                    if not self.sequence_index[sequence_id]:
                        del self.sequence_index[sequence_id]
            
            # Remove from location index if applicable
            if "location" in item.context:
                location = item.context["location"]
                if location in self.location_index and item_id in self.location_index[location]:
                    self.location_index[location].remove(item_id)
                    
                    if not self.location_index[location]:
                        del self.location_index[location]
            
            # Remove from agent index if applicable
            if "agent_id" in item.context:
                agent_id = item.context["agent_id"]
                if agent_id in self.agent_index and item_id in self.agent_index[agent_id]:
                    self.agent_index[agent_id].remove(item_id)
                    
                    if not self.agent_index[agent_id]:
                        del self.agent_index[agent_id]
            
            # Remove from main storage
            del self.items[item_id]
            
            return True
    
    async def get_experiences_in_time_range(self, start_time: float, end_time: float) -> List[Experience]:
        """
        Get experiences in a time range.
        
        Args:
            start_time: The start time
            end_time: The end time
            
        Returns:
            List of experiences in the time range
        """
        async with self.lock:
            experience_ids = await self._get_experiences_in_time_range(start_time, end_time)
            
            # Convert IDs to experiences and filter by exact time range
            experiences = []
            for exp_id in experience_ids:
                if exp_id in self.items:
                    experience = self.items[exp_id]
                    if start_time <= experience.timestamp <= end_time:
                        experiences.append(experience)
            
            # Sort by timestamp
            experiences.sort(key=lambda x: x.timestamp)
            
            return experiences
    
    async def get_experiences_by_context(self, context_key: str, context_value: Any) -> List[Experience]:
        """
        Get experiences by context.
        
        Args:
            context_key: The context key
            context_value: The context value
            
        Returns:
            List of experiences matching the context
        """
        async with self.lock:
            experience_ids = await self._get_experiences_by_context(context_key, context_value)
            
            # Convert IDs to experiences
            experiences = [self.items[exp_id] for exp_id in experience_ids if exp_id in self.items]
            
            # Sort by timestamp (most recent first)
            experiences.sort(key=lambda x: x.timestamp, reverse=True)
            
            return experiences
    
    async def get_recent_experiences(self, max_count: int = 10) -> List[Experience]:
        """
        Get recent experiences.
        
        Args:
            max_count: Maximum number of experiences to return
            
        Returns:
            List of recent experiences
        """
        async with self.lock:
            # Get all experiences
            experiences = list(self.items.values())
            
            # Sort by timestamp (most recent first)
            experiences.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            return experiences[:max_count]
    
    # Additional specialized methods for episodic memory
    
    async def apply_memory_decay(self) -> int:
        """
        Apply memory decay to all experiences based on their age and importance.
        
        Returns:
            Number of experiences removed due to decay
        """
        async with self.lock:
            current_time = time.time()
            days_since_last_decay = (current_time - self.last_decay_time) / (24 * 3600)
            
            # Only apply decay if at least one day has passed
            if days_since_last_decay < 1:
                return 0
            
            decay_factor = self.decay_rate * days_since_last_decay
            removed_count = 0
            
            # Apply decay to all experiences
            experiences_to_remove = []
            for exp_id, experience in self.items.items():
                # Calculate age in days
                age_days = (current_time - experience.timestamp) / (24 * 3600)
                
                # Get current importance
                importance = experience.metadata.get("importance", 0.5)
                
                # Apply decay based on age
                new_importance = importance * (1 - decay_factor * (1 + 0.1 * age_days))
                
                # Update importance
                experience.metadata["importance"] = max(0, new_importance)
                
                # Check if importance is below threshold
                if new_importance < self.importance_threshold:
                    experiences_to_remove.append(exp_id)
            
            # Remove experiences with importance below threshold
            for exp_id in experiences_to_remove:
                await self.delete(exp_id)
                removed_count += 1
            
            # Update last decay time
            self.last_decay_time = current_time
            
            logger.debug(f"Applied memory decay: removed {removed_count} experiences")
            return removed_count
    
    async def get_experience_sequence(self, sequence_id: str) -> List[Experience]:
        """
        Get a sequence of experiences.
        
        Args:
            sequence_id: The ID of the sequence
            
        Returns:
            List of experiences in the sequence, ordered by timestamp
        """
        async with self.lock:
            if sequence_id not in self.sequence_index:
                return []
            
            # Get experience IDs in the sequence
            exp_ids = self.sequence_index[sequence_id]
            
            # Convert to experiences
            experiences = [self.items[exp_id] for exp_id in exp_ids if exp_id in self.items]
            
            # Sort by timestamp
            experiences.sort(key=lambda x: x.timestamp)
            
            return experiences
    
    async def find_similar_experiences(self, experience: Experience, similarity_threshold: float = 0.7) -> List[Experience]:
        """
        Find experiences similar to the given experience.
        
        Args:
            experience: The reference experience
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of similar experiences, sorted by similarity (highest first)
        """
        async with self.lock:
            similar_experiences = []
            
            # First filter by context overlap
            context_keys = set(experience.context.keys())
            candidate_ids = set(self.items.keys())
            
            for key, value in experience.context.items():
                if key in self.context_index and str(value) in self.context_index[key]:
                    # If this is the first filter, use it directly
                    if len(similar_experiences) == 0:
                        candidate_ids = set(self.context_index[key][str(value)])
                    # Otherwise, intersect with current candidates
                    else:
                        candidate_ids = candidate_ids.intersection(
                            set(self.context_index[key][str(value)])
                        )
            
            # Calculate similarity for each candidate
            for exp_id in candidate_ids:
                if exp_id == experience.id:
                    continue  # Skip the reference experience itself
                
                candidate = self.items[exp_id]
                similarity = self._calculate_experience_similarity(experience, candidate)
                
                if similarity >= similarity_threshold:
                    similar_experiences.append((similarity, candidate))
            
            # Sort by similarity (highest first)
            similar_experiences.sort(key=lambda x: x[0], reverse=True)
            
            # Return just the experiences
            return [exp for _, exp in similar_experiences]
    
    async def detect_patterns(self, min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """
        Detect recurring patterns in experiences.
        
        Args:
            min_occurrences: Minimum number of occurrences to consider a pattern
            
        Returns:
            List of detected patterns
        """
        async with self.lock:
            patterns = []
            
            # Look for recurring context patterns
            context_patterns = self._find_context_patterns(min_occurrences)
            patterns.extend(context_patterns)
            
            # Look for temporal patterns (e.g., daily, weekly)
            temporal_patterns = self._find_temporal_patterns(min_occurrences)
            patterns.extend(temporal_patterns)
            
            return patterns
    
    # Private helper methods
    
    async def _index_by_time(self, experience: Experience) -> None:
        """Index an experience by time."""
        # Index by day
        day_timestamp = int(experience.timestamp / 86400) * 86400  # Round to day
        if day_timestamp not in self.time_index:
            self.time_index[day_timestamp] = []
        
        if experience.id not in self.time_index[day_timestamp]:
            self.time_index[day_timestamp].append(experience.id)
        
        # Index by hour
        hour_timestamp = int(experience.timestamp / 3600) * 3600  # Round to hour
        if hour_timestamp not in self.hour_index:
            self.hour_index[hour_timestamp] = []
        
        if experience.id not in self.hour_index[hour_timestamp]:
            self.hour_index[hour_timestamp].append(experience.id)
        
        # Add to timeline
        self.timeline.append((experience.timestamp, experience.id))
        self.timeline.sort()  # Keep timeline sorted
    
    async def _index_by_context(self, experience: Experience) -> None:
        """Index an experience by context."""
        # Index by context key-value pairs
        for key, value in experience.context.items():
            if key not in self.context_index:
                self.context_index[key] = {}
            
            str_value = str(value)
            if str_value not in self.context_index[key]:
                self.context_index[key][str_value] = []
            
            if experience.id not in self.context_index[key][str_value]:
                self.context_index[key][str_value].append(experience.id)
            
            # Special handling for location
            if key == "location":
                if value not in self.location_index:
                    self.location_index[value] = []
                
                if experience.id not in self.location_index[value]:
                    self.location_index[value].append(experience.id)
            
            # Special handling for agent_id
            if key == "agent_id":
                if value not in self.agent_index:
                    self.agent_index[value] = []
                
                if experience.id not in self.agent_index[value]:
                    self.agent_index[value].append(experience.id)
    
    async def _update_sequence(self, experience: Experience) -> None:
        """Update sequence index with an experience."""
        sequence_id = experience.metadata["sequence_id"]
        
        if sequence_id not in self.sequence_index:
            self.sequence_index[sequence_id] = []
        
        if experience.id not in self.sequence_index[sequence_id]:
            self.sequence_index[sequence_id].append(experience.id)
            
            # Keep sequence ordered by timestamp
            self.sequence_index[sequence_id].sort(
                key=lambda x: self.items[x].timestamp if x in self.items else 0
            )
    
    async def _remove_from_time_indexes(self, experience_id: str, timestamp: float) -> None:
        """Remove an experience from time indexes."""
        # Remove from day index
        day_timestamp = int(timestamp / 86400) * 86400
        if day_timestamp in self.time_index and experience_id in self.time_index[day_timestamp]:
            self.time_index[day_timestamp].remove(experience_id)
            
            if not self.time_index[day_timestamp]:
                del self.time_index[day_timestamp]
        
        # Remove from hour index
        hour_timestamp = int(timestamp / 3600) * 3600
        if hour_timestamp in self.hour_index and experience_id in self.hour_index[hour_timestamp]:
            self.hour_index[hour_timestamp].remove(experience_id)
            
            if not self.hour_index[hour_timestamp]:
                del self.hour_index[hour_timestamp]
        
        # Remove from timeline
        self.timeline = [(ts, eid) for ts, eid in self.timeline if eid != experience_id]
    
    async def _remove_from_context_indexes(self, experience_id: str, context: Dict[str, Any]) -> None:
        """Remove an experience from context indexes."""
        # Remove from context index
        for key, value in context.items():
            str_value = str(value)
            if key in self.context_index and str_value in self.context_index[key]:
                if experience_id in self.context_index[key][str_value]:
                    self.context_index[key][str_value].remove(experience_id)
                    
                    if not self.context_index[key][str_value]:
                        del self.context_index[key][str_value]
                        
                        if not self.context_index[key]:
                            del self.context_index[key]
    
    async def _get_experiences_in_time_range(self, start_time: float, end_time: float) -> Set[str]:
        """Get experience IDs in a time range."""
        experience_ids = set()
        
        # Find relevant day timestamps
        start_day = int(start_time / 86400) * 86400
        end_day = int(end_time / 86400) * 86400
        
        for day_timestamp in range(start_day, end_day + 86400, 86400):
            if day_timestamp in self.time_index:
                experience_ids.update(self.time_index[day_timestamp])
        
        return experience_ids
    
    async def _get_experiences_by_context(self, context_key: str, context_value: Any) -> Set[str]:
        """Get experience IDs by context."""
        if context_key not in self.context_index:
            return set()
        
        str_value = str(context_value)
        if str_value not in self.context_index[context_key]:
            return set()
        
        return set(self.context_index[context_key][str_value])
    
    def _calculate_initial_importance(self, experience: Experience) -> float:
        """Calculate initial importance score for an experience."""
        importance = 0.5  # Default importance
        
        # Adjust based on metadata
        if "emotional_intensity" in experience.metadata:
            importance += 0.1 * experience.metadata["emotional_intensity"]
        
        if "novelty" in experience.metadata:
            importance += 0.1 * experience.metadata["novelty"]
        
        if "relevance" in experience.metadata:
            importance += 0.1 * experience.metadata["relevance"]
        
        # Cap between 0 and 1
        return max(0.0, min(1.0, importance))
    
    def _calculate_experience_similarity(self, exp1: Experience, exp2: Experience) -> float:
        """Calculate similarity between two experiences."""
        similarity = 0.0
        
        # Context similarity (50% weight)
        context_sim = self._calculate_context_similarity(exp1.context, exp2.context)
        similarity += 0.5 * context_sim
        
        # Temporal similarity (30% weight)
        time_diff = abs(exp1.timestamp - exp2.timestamp)
        time_sim = max(0, 1 - (time_diff / (30 * 24 * 3600)))  # Scale over 30 days
        similarity += 0.3 * time_sim
        
        # Duration similarity (20% weight)
        if exp1.duration > 0 and exp2.duration > 0:
            duration_ratio = min(exp1.duration, exp2.duration) / max(exp1.duration, exp2.duration)
            similarity += 0.2 * duration_ratio
        
        return similarity
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two context dictionaries."""
        if not context1 or not context2:
            return 0.0
        
        # Get all keys
        all_keys = set(context1.keys()).union(set(context2.keys()))
        if not all_keys:
            return 0.0
        
        # Count matching keys and values
        matching_keys = set(context1.keys()).intersection(set(context2.keys()))
        matching_values = sum(1 for k in matching_keys if str(context1[k]) == str(context2[k]))
        
        # Calculate similarity
        return matching_values / len(all_keys)
    
    def _find_context_patterns(self, min_occurrences: int) -> List[Dict[str, Any]]:
        """Find recurring context patterns."""
        patterns = []
        
        # Look for frequent context combinations
        context_combinations = defaultdict(int)
        
        for experience in self.items.values():
            # Create a frozenset of context items for counting
            context_items = frozenset((k, str(v)) for k, v in experience.context.items())
            context_combinations[context_items] += 1
        
        # Filter by minimum occurrences
        for context_items, count in context_combinations.items():
            if count >= min_occurrences:
                # Convert back to dictionary
                context_dict = {k: v for k, v in context_items}
                
                patterns.append({
                    "type": "context_pattern",
                    "context": context_dict,
                    "occurrences": count
                })
        
        return patterns
    
    def _find_temporal_patterns(self, min_occurrences: int) -> List[Dict[str, Any]]:
        """Find recurring temporal patterns."""
        patterns = []
        
        # Count occurrences by hour of day
        hour_counts = defaultdict(int)
        # Count occurrences by day of week
        day_of_week_counts = defaultdict(int)
        
        for experience in self.items.values():
            # Get datetime object
            dt = datetime.fromtimestamp(experience.timestamp)
            
            # Hour of day (0-23)
            hour_counts[dt.hour] += 1
            
            # Day of week (0-6, where 0 is Monday)
            day_of_week_counts[dt.weekday()] += 1
        
        # Find hourly patterns
        for hour, count in hour_counts.items():
            if count >= min_occurrences:
                patterns.append({
                    "type": "temporal_pattern",
                    "subtype": "hourly",
                    "hour": hour,
                    "occurrences": count
                })
        
        # Find daily patterns
        for day, count in day_of_week_counts.items():
            if count >= min_occurrences:
                patterns.append({
                    "type": "temporal_pattern",
                    "subtype": "daily",
                    "day_of_week": day,
                    "occurrences": count
                })
        
        return patterns