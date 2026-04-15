"""
Working Memory Store Implementation for GodelOS

This module implements a specialized working memory store that handles
priority-based storage with capacity limits, attention management,
and decay mechanisms for temporary knowledge.
"""

import logging
import time
import asyncio
import heapq
from typing import Dict, List, Optional, Any, Union, Set, Tuple, TypeVar, Generic
import uuid
from dataclasses import dataclass, field

from godelOS.unified_agent_core.knowledge_store.interfaces import (
    Knowledge, KnowledgeType, Query, QueryResult,
    WorkingMemoryInterface
)

logger = logging.getLogger(__name__)


class WorkingMemory(WorkingMemoryInterface):
    """
    Specialized implementation of working memory for GodelOS.
    
    This implementation provides:
    - Priority-based storage with capacity limits
    - Attention management and focus
    - Decay mechanisms for temporary knowledge
    - Efficient retrieval of high-priority items
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize working memory.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Primary storage for knowledge items
        self.items: Dict[str, Knowledge] = {}
        
        # Priority management
        self.priorities: Dict[str, float] = {}  # item_id -> priority (0.0 to 1.0)
        self.priority_heap: List[Tuple[float, str]] = []  # min heap of (-priority, item_id)
        self.priority_dirty = False  # Flag to indicate if heap needs rebuilding
        
        # Attention management
        self.focus_items: List[str] = []  # Currently focused items (ordered by focus time)
        self.focus_timestamps: Dict[str, float] = {}  # item_id -> focus timestamp
        self.max_focus_items = self.config.get("max_focus_items", 7)  # Miller's Law: 7±2 items
        
        # Expiration management
        self.expiration_times: Dict[str, float] = {}  # item_id -> expiration time
        self.default_ttl = self.config.get("default_ttl", 3600)  # Default TTL in seconds
        
        # Capacity management
        self.capacity = self.config.get("capacity", 100)
        
        # Type-specific indexes
        self.type_index: Dict[KnowledgeType, Set[str]] = {}
        for kt in KnowledgeType:
            self.type_index[kt] = set()
        
        # Tag-based indexing
        self.tag_index: Dict[str, Set[str]] = {}  # tag -> set of item_ids
        
        # Thread safety
        self.lock = asyncio.Lock()
        
        # Decay parameters
        self.decay_rate = self.config.get("decay_rate", 0.1)  # Rate of priority decay per hour
        self.last_decay_time = time.time()
    
    async def store(self, item: Knowledge) -> bool:
        """
        Store an item in working memory.
        
        Args:
            item: The item to store
            
        Returns:
            True if the item was stored successfully, False otherwise
        """
        async with self.lock:
            try:
                # Check if we need to make room
                if len(self.items) >= self.capacity and item.id not in self.items:
                    await self._evict_items()
                
                # Store the item
                self.items[item.id] = item
                
                # Set priority based on item confidence or metadata
                priority = self._calculate_initial_priority(item)
                self.priorities[item.id] = priority
                
                # Update priority heap
                heapq.heappush(self.priority_heap, (-priority, item.id))
                
                # Set expiration time
                ttl = item.metadata.get("ttl", self.default_ttl)
                self.expiration_times[item.id] = time.time() + ttl
                
                # Update type index
                self.type_index[item.type].add(item.id)
                
                # Update tag index if tags are present
                if "tags" in item.metadata and isinstance(item.metadata["tags"], list):
                    for tag in item.metadata["tags"]:
                        if tag not in self.tag_index:
                            self.tag_index[tag] = set()
                        self.tag_index[tag].add(item.id)
                
                logger.debug(f"Stored {item.type.value} with ID {item.id} in working memory")
                return True
            except Exception as e:
                logger.error(f"Error storing item in working memory: {e}")
                return False
    
    async def retrieve(self, item_id: str) -> Optional[Knowledge]:
        """
        Retrieve an item from working memory.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item, or None if not found or expired
        """
        async with self.lock:
            # Check if item exists and is not expired
            if item_id in self.items and time.time() < self.expiration_times.get(item_id, 0):
                item = self.items[item_id]
                
                # Update last accessed time
                item.last_accessed = time.time()
                
                # Extend expiration time on access
                self.expiration_times[item_id] = time.time() + self.default_ttl
                
                # Boost priority slightly on access
                await self.set_priority(item_id, min(1.0, self.priorities.get(item_id, 0.5) * 1.05))
                
                # Add to focus if not already there
                await self._update_focus(item_id)
                
                return item
            
            return None
    
    async def query(self, query: Query) -> QueryResult:
        """
        Query items from working memory.
        
        Args:
            query: The query to execute
            
        Returns:
            The query result
        """
        async with self.lock:
            start_time = time.time()
            
            # Filter out expired items
            current_time = time.time()
            valid_item_ids = {
                item_id for item_id in self.items
                if current_time < self.expiration_times.get(item_id, 0)
            }
            
            # Filter by knowledge types
            if query.knowledge_types:
                type_filtered_ids = set()
                for knowledge_type in query.knowledge_types:
                    type_filtered_ids.update(self.type_index.get(knowledge_type, set()))
                valid_item_ids = valid_item_ids.intersection(type_filtered_ids)
            
            # Apply content filters
            if query.content:
                filtered_ids = await self._apply_content_filters(query.content, valid_item_ids)
                valid_item_ids = valid_item_ids.intersection(filtered_ids) if filtered_ids else valid_item_ids
            
            # Convert IDs to items
            valid_items = [self.items[item_id] for item_id in valid_item_ids if item_id in self.items]
            
            # Sort by priority, focus status, or recency
            sort_by = query.metadata.get("sort_by", "priority")
            if sort_by == "focus":
                # Sort by focus status (focused items first, then by focus time)
                valid_items.sort(
                    key=lambda x: (
                        x.id not in self.focus_items,  # False sorts before True
                        -self.focus_timestamps.get(x.id, 0)  # More recent focus time sorts first
                    )
                )
            elif sort_by == "recency":
                valid_items.sort(key=lambda x: x.last_accessed, reverse=True)
            else:  # Default to priority
                valid_items.sort(key=lambda x: self.priorities.get(x.id, 0), reverse=True)
            
            # Apply limit
            total_items = len(valid_items)
            valid_items = valid_items[:query.max_results]
            
            # Update access time for returned items
            for item in valid_items:
                item.last_accessed = time.time()
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                query_id=query.id,
                items=valid_items,
                total_items=total_items,
                execution_time=execution_time,
                metadata={"memory_type": "working"}
            )
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an item in working memory.
        
        Args:
            item_id: The ID of the item to update
            updates: Dictionary of updates to apply to the item
            
        Returns:
            True if the item was updated, False if the item was not found or expired
        """
        async with self.lock:
            # Check if item exists and is not expired
            if item_id not in self.items or time.time() >= self.expiration_times.get(item_id, 0):
                return False
            
            item = self.items[item_id]
            old_type = item.type
            old_tags = item.metadata.get("tags", [])
            
            # Update item attributes
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
                elif key == "metadata" and isinstance(value, dict):
                    # Update metadata dictionary
                    item.metadata.update(value)
            
            # Update priority if confidence is updated
            if "confidence" in updates:
                new_priority = min(1.0, max(0.0, updates["confidence"]))
                await self.set_priority(item_id, new_priority)
            
            # Update type index if type changed
            if "type" in updates and updates["type"] != old_type:
                self.type_index[old_type].discard(item_id)
                self.type_index[item.type].add(item_id)
            
            # Update tag index if tags changed
            new_tags = item.metadata.get("tags", [])
            if new_tags != old_tags:
                # Remove from old tags
                for tag in old_tags:
                    if tag in self.tag_index and item_id in self.tag_index[tag]:
                        self.tag_index[tag].remove(item_id)
                        if not self.tag_index[tag]:
                            del self.tag_index[tag]
                
                # Add to new tags
                for tag in new_tags:
                    if tag not in self.tag_index:
                        self.tag_index[tag] = set()
                    self.tag_index[tag].add(item_id)
            
            # Update expiration time if ttl is in metadata updates
            if "metadata" in updates and "ttl" in updates["metadata"]:
                ttl = updates["metadata"]["ttl"]
                self.expiration_times[item_id] = time.time() + ttl
            
            # Update last accessed time
            item.last_accessed = time.time()
            
            # Add to focus
            await self._update_focus(item_id)
            
            return True
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete an item from working memory.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if the item was deleted, False if the item was not found
        """
        async with self.lock:
            if item_id not in self.items:
                return False
            
            item = self.items[item_id]
            
            # Remove from type index
            self.type_index[item.type].discard(item_id)
            
            # Remove from tag index
            if "tags" in item.metadata:
                for tag in item.metadata["tags"]:
                    if tag in self.tag_index and item_id in self.tag_index[tag]:
                        self.tag_index[tag].remove(item_id)
                        if not self.tag_index[tag]:
                            del self.tag_index[tag]
            
            # Remove from focus
            if item_id in self.focus_items:
                self.focus_items.remove(item_id)
                if item_id in self.focus_timestamps:
                    del self.focus_timestamps[item_id]
            
            # Remove from priority structures
            if item_id in self.priorities:
                del self.priorities[item_id]
                self.priority_dirty = True  # Mark for heap rebuild
            
            # Remove from expiration times
            if item_id in self.expiration_times:
                del self.expiration_times[item_id]
            
            # Remove from main storage
            del self.items[item_id]
            
            return True
    
    async def set_priority(self, item_id: str, priority: float) -> bool:
        """
        Set the priority of an item in working memory.
        
        Args:
            item_id: The ID of the item
            priority: The priority (0.0 to 1.0)
            
        Returns:
            True if the priority was set, False if the item was not found or expired
        """
        async with self.lock:
            # Check if item exists and is not expired
            if item_id not in self.items or time.time() >= self.expiration_times.get(item_id, 0):
                return False
            
            # Update priority
            self.priorities[item_id] = max(0.0, min(1.0, priority))
            self.priority_dirty = True  # Mark heap for rebuild
            
            return True
    
    async def get_high_priority_items(self, max_count: int = 10) -> List[Knowledge]:
        """
        Get high-priority items from working memory.
        
        Args:
            max_count: Maximum number of items to return
            
        Returns:
            List of high-priority items
        """
        async with self.lock:
            # Rebuild priority heap if needed
            if self.priority_dirty:
                await self._rebuild_priority_heap()
            
            # Filter out expired items
            current_time = time.time()
            valid_items = []
            
            # Use a copy of the heap for iteration
            heap_copy = self.priority_heap.copy()
            heapq.heapify(heap_copy)
            
            # Get top items by priority
            while heap_copy and len(valid_items) < max_count:
                _, item_id = heapq.heappop(heap_copy)
                if item_id in self.items and current_time < self.expiration_times.get(item_id, 0):
                    valid_items.append(self.items[item_id])
            
            return valid_items
    
    async def clear_expired_items(self) -> int:
        """
        Clear expired items from working memory.
        
        Returns:
            Number of items cleared
        """
        async with self.lock:
            current_time = time.time()
            expired_ids = [
                item_id for item_id in self.items
                if current_time >= self.expiration_times.get(item_id, 0)
            ]
            
            # Remove expired items
            for item_id in expired_ids:
                await self.delete(item_id)
            
            return len(expired_ids)
    
    # Additional specialized methods for working memory
    
    async def get_focused_items(self) -> List[Knowledge]:
        """
        Get currently focused items.
        
        Returns:
            List of focused items, ordered by focus time (most recent first)
        """
        async with self.lock:
            # Get focused items
            focused_items = [
                self.items[item_id] for item_id in self.focus_items
                if item_id in self.items and time.time() < self.expiration_times.get(item_id, 0)
            ]
            
            return focused_items
    
    async def set_focus(self, item_id: str) -> bool:
        """
        Set focus on a specific item.
        
        Args:
            item_id: The ID of the item to focus on
            
        Returns:
            True if focus was set, False if the item was not found or expired
        """
        async with self.lock:
            # Check if item exists and is not expired
            if item_id not in self.items or time.time() >= self.expiration_times.get(item_id, 0):
                return False
            
            # Update focus
            await self._update_focus(item_id)
            
            # Boost priority
            current_priority = self.priorities.get(item_id, 0.5)
            await self.set_priority(item_id, min(1.0, current_priority * 1.2))
            
            return True
    
    async def clear_focus(self) -> None:
        """Clear all focused items."""
        async with self.lock:
            self.focus_items = []
            self.focus_timestamps = {}
    
    async def apply_priority_decay(self) -> None:
        """
        Apply priority decay to all items based on time since last access.
        """
        async with self.lock:
            current_time = time.time()
            hours_since_last_decay = (current_time - self.last_decay_time) / 3600
            
            # Only apply decay if at least one hour has passed
            if hours_since_last_decay < 1:
                return
            
            decay_factor = self.decay_rate * hours_since_last_decay
            
            # Apply decay to all items
            for item_id, priority in list(self.priorities.items()):
                if item_id in self.items:
                    # Calculate time since last access in hours
                    hours_since_access = (current_time - self.items[item_id].last_accessed) / 3600
                    
                    # Apply decay based on time since access
                    new_priority = priority * (1 - decay_factor * (1 + 0.1 * hours_since_access))
                    
                    # Update priority
                    self.priorities[item_id] = max(0.1, new_priority)  # Minimum priority of 0.1
            
            # Mark heap for rebuild
            self.priority_dirty = True
            
            # Update last decay time
            self.last_decay_time = current_time
            
            logger.debug("Applied priority decay to working memory items")
    
    async def get_items_by_tag(self, tag: str, max_count: int = 10) -> List[Knowledge]:
        """
        Get items with a specific tag.
        
        Args:
            tag: The tag to filter by
            max_count: Maximum number of items to return
            
        Returns:
            List of items with the specified tag
        """
        async with self.lock:
            if tag not in self.tag_index:
                return []
            
            # Filter out expired items
            current_time = time.time()
            valid_items = [
                self.items[item_id] for item_id in self.tag_index[tag]
                if item_id in self.items and current_time < self.expiration_times.get(item_id, 0)
            ]
            
            # Sort by priority
            valid_items.sort(key=lambda x: self.priorities.get(x.id, 0), reverse=True)
            
            # Apply limit
            return valid_items[:max_count]
    
    async def extend_expiration(self, item_id: str, additional_time: float) -> bool:
        """
        Extend the expiration time of an item.
        
        Args:
            item_id: The ID of the item
            additional_time: Additional time in seconds
            
        Returns:
            True if the expiration was extended, False if the item was not found or already expired
        """
        async with self.lock:
            # Check if item exists and is not expired
            current_time = time.time()
            if item_id not in self.items or current_time >= self.expiration_times.get(item_id, 0):
                return False
            
            # Extend expiration time
            self.expiration_times[item_id] += additional_time
            
            return True
    
    # Private helper methods
    
    async def _evict_items(self) -> None:
        """Evict low-priority items to make room for new ones."""
        # First, clear expired items
        await self.clear_expired_items()
        
        # If still at capacity, remove lowest priority items
        if len(self.items) >= self.capacity:
            # Rebuild priority heap if needed
            if self.priority_dirty:
                await self._rebuild_priority_heap()
            
            # Calculate number of items to remove (10% of capacity)
            num_to_remove = max(1, int(self.capacity * 0.1))
            
            # Create a copy of the heap in reverse order (lowest priority first)
            reversed_heap = [(-p, id) for p, id in self.priority_heap]
            heapq.heapify(reversed_heap)
            
            # Remove lowest priority items
            for _ in range(min(num_to_remove, len(reversed_heap))):
                _, item_id = heapq.heappop(reversed_heap)
                if item_id in self.items:
                    await self.delete(item_id)
    
    async def _rebuild_priority_heap(self) -> None:
        """Rebuild the priority heap."""
        # Create new heap
        self.priority_heap = [(-priority, item_id) for item_id, priority in self.priorities.items()]
        heapq.heapify(self.priority_heap)
        
        # Clear dirty flag
        self.priority_dirty = False
    
    async def _update_focus(self, item_id: str) -> None:
        """Update focus for an item."""
        # Remove if already in focus
        if item_id in self.focus_items:
            self.focus_items.remove(item_id)
        
        # Add to front of focus list
        self.focus_items.insert(0, item_id)
        
        # Update focus timestamp
        self.focus_timestamps[item_id] = time.time()
        
        # Trim focus list if needed
        if len(self.focus_items) > self.max_focus_items:
            removed_id = self.focus_items.pop()
            if removed_id in self.focus_timestamps:
                del self.focus_timestamps[removed_id]
    
    def _calculate_initial_priority(self, item: Knowledge) -> float:
        """Calculate initial priority for an item."""
        # Start with confidence as base priority
        priority = item.confidence
        
        # Adjust based on metadata
        if "importance" in item.metadata:
            priority = max(priority, item.metadata["importance"])
        
        if "urgency" in item.metadata:
            priority = max(priority, item.metadata["urgency"])
        
        if "relevance" in item.metadata:
            priority += 0.1 * item.metadata["relevance"]
        
        # Cap between 0 and 1
        return max(0.0, min(1.0, priority))
    
    async def _apply_content_filters(self, content: Dict[str, Any], item_ids: Set[str]) -> Set[str]:
        """Apply content filters to a set of item IDs."""
        result_ids = item_ids.copy()
        
        # Text search
        if "text" in content:
            text = content["text"].lower()
            text_filtered_ids = set()
            
            for item_id in result_ids:
                if item_id in self.items:
                    item = self.items[item_id]
                    
                    # Check in content if it's a dictionary
                    if isinstance(item.content, dict):
                        for value in item.content.values():
                            if isinstance(value, str) and text in value.lower():
                                text_filtered_ids.add(item_id)
                                break
                    
                    # Check in metadata
                    if not item_id in text_filtered_ids:
                        for key, value in item.metadata.items():
                            if isinstance(value, str) and text in value.lower():
                                text_filtered_ids.add(item_id)
                                break
            
            result_ids = text_filtered_ids
        
        # Tag filter
        if "tag" in content:
            tag = content["tag"]
            if tag in self.tag_index:
                result_ids = result_ids.intersection(self.tag_index[tag])
            else:
                result_ids = set()
        
        # Minimum priority filter
        if "min_priority" in content:
            min_priority = float(content["min_priority"])
            priority_filtered_ids = {
                item_id for item_id in result_ids
                if self.priorities.get(item_id, 0) >= min_priority
            }
            result_ids = priority_filtered_ids
        
        # Focus filter
        if "focused" in content and content["focused"]:
            focus_filtered_ids = set(self.focus_items).intersection(result_ids)
            result_ids = focus_filtered_ids
        
        return result_ids