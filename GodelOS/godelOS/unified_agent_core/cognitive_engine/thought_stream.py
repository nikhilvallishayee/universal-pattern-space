"""
Thought Stream Implementation for GodelOS

This module implements the ThoughtStream class, which manages the flow of thoughts
in the cognitive system, including adding, retrieving, and updating thoughts.
It provides advanced priority calculation, pattern recognition, thought clustering,
and thought history management with forgetting mechanisms.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple
import heapq
import asyncio
from dataclasses import asdict
import re
from collections import defaultdict
import math
import uuid

from godelOS.unified_agent_core.cognitive_engine.interfaces import Thought, ThoughtInterface

logger = logging.getLogger(__name__)


class ThoughtStream(ThoughtInterface):
    """
    Enhanced ThoughtStream implementation for GodelOS.
    
    The ThoughtStream manages the flow of thoughts in the cognitive system,
    including adding, retrieving, and updating thoughts. It provides:
    
    1. Advanced priority calculation based on thought content, context, and metadata
    2. Pattern recognition for related thoughts
    3. Thought clustering and categorization
    4. Thought history management with forgetting mechanisms
    """
    
    def __init__(self, max_capacity: int = 1000, forgetting_threshold: float = 0.2,
                 retention_period: int = 86400, cluster_similarity_threshold: float = 0.6):
        """
        Initialize the thought stream.
        
        Args:
            max_capacity: Maximum number of thoughts to store
            forgetting_threshold: Priority threshold below which thoughts may be forgotten
            retention_period: Time in seconds to retain thoughts before applying forgetting
            cluster_similarity_threshold: Similarity threshold for clustering thoughts
        """
        self.thoughts: Dict[str, Thought] = {}
        self.priority_queue: List[tuple] = []  # (priority, timestamp, thought_id)
        self.max_capacity = max_capacity
        self.lock = asyncio.Lock()
        
        # Advanced features
        self.forgetting_threshold = forgetting_threshold
        self.retention_period = retention_period
        self.cluster_similarity_threshold = cluster_similarity_threshold
        
        # Thought relationships
        self.related_thoughts: Dict[str, Set[str]] = defaultdict(set)  # thought_id -> set of related thought_ids
        self.thought_clusters: Dict[str, List[str]] = {}  # cluster_id -> list of thought_ids
        self.thought_to_cluster: Dict[str, str] = {}  # thought_id -> cluster_id
        self.thought_categories: Dict[str, List[str]] = defaultdict(list)  # category -> list of thought_ids
        
        # Pattern recognition
        self.common_patterns: Dict[str, List[str]] = {}  # pattern -> list of thought_ids
        
        # Thought history
        self.access_history: Dict[str, List[float]] = defaultdict(list)  # thought_id -> list of access timestamps
    
    async def add_thought(self, thought: Thought, priority: Optional[float] = None,
                          context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a thought to the thought stream with advanced priority calculation.
        
        Args:
            thought: The thought to add
            priority: Optional priority override
            context: Optional cognitive context for priority calculation
            
        Returns:
            True if the thought was added successfully, False otherwise
        """
        if not thought.id:
            logger.error("Cannot add thought with empty ID")
            return False
        
        # Calculate priority if not explicitly provided
        if priority is not None:
            thought.priority = priority
        elif context:
            thought.priority = await self._calculate_priority(thought, context)
        
        async with self.lock:
            # Check if we need to make room
            if len(self.thoughts) >= self.max_capacity:
                # Apply forgetting mechanism
                await self._apply_forgetting_mechanism()
                
                # If still at capacity, remove lowest priority thought
                if len(self.thoughts) >= self.max_capacity:
                    await self._remove_lowest_priority_thought()
            
            # Add thought to dictionary
            self.thoughts[thought.id] = thought
            
            # Add to priority queue
            heapq.heappush(
                self.priority_queue,
                (-thought.priority, time.time(), thought.id)
            )
            
            # Update access history
            self.access_history[thought.id].append(time.time())
            
            # Identify related thoughts
            await self._identify_related_thoughts(thought)
            
            # Categorize the thought
            await self._categorize_thought(thought)
            
            # Cluster the thought
            await self._cluster_thought(thought)
            
            # Recognize patterns
            await self._recognize_patterns(thought)
            
            logger.debug(f"Added thought {thought.id} with priority {thought.priority}")
            return True
    
    async def get_priority_thoughts(self, max_thoughts: int = 10,
                                    category: Optional[str] = None,
                                    context: Optional[Dict[str, Any]] = None) -> List[Thought]:
        """
        Get the highest priority thoughts, optionally filtered by category.
        
        Args:
            max_thoughts: Maximum number of thoughts to return
            category: Optional category to filter thoughts
            context: Optional cognitive context for contextual relevance
            
        Returns:
            List of highest priority thoughts
        """
        async with self.lock:
            # Get candidate thought IDs
            candidate_ids = []
            
            if category:
                # Get thoughts in the specified category
                candidate_ids = self.thought_categories.get(category, [])
            else:
                # Use all thoughts
                candidate_ids = list(self.thoughts.keys())
            
            # Create a list of (priority, timestamp, thought_id) tuples for sorting
            if context:
                # Calculate contextual priority for each thought
                priority_tuples = []
                for thought_id in candidate_ids:
                    if thought_id in self.thoughts:
                        thought = self.thoughts[thought_id]
                        contextual_priority = await self._calculate_contextual_priority(thought, context)
                        priority_tuples.append((-contextual_priority, thought.created_at, thought_id))
            else:
                # Use stored priorities
                priority_tuples = [(-self.thoughts[tid].priority, self.thoughts[tid].created_at, tid)
                                  for tid in candidate_ids if tid in self.thoughts]
            
            # Sort by priority
            priority_tuples.sort()
            
            # Extract up to max_thoughts thoughts
            result = []
            for i in range(min(max_thoughts, len(priority_tuples))):
                thought_id = priority_tuples[i][2]
                thought = self.thoughts[thought_id]
                
                # Update access history
                self.access_history[thought_id].append(time.time())
                
                result.append(thought)
            
            return result
    
    async def get_thought_by_id(self, thought_id: str) -> Optional[Thought]:
        """
        Get a thought by ID.
        
        Args:
            thought_id: The ID of the thought to get
            
        Returns:
            The thought, or None if not found
        """
        async with self.lock:
            thought = self.thoughts.get(thought_id)
            
            if thought:
                # Update last accessed time in metadata
                thought.metadata["last_accessed"] = time.time()
                
                # Update access history
                self.access_history[thought_id].append(time.time())
            
            return thought
    
    async def update_thought(self, thought_id: str, updates: Dict[str, Any],
                             context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a thought.
        
        Args:
            thought_id: The ID of the thought to update
            updates: Dictionary of updates to apply to the thought
            context: Optional cognitive context for recalculating priority
            
        Returns:
            True if the thought was updated, False if the thought was not found
        """
        async with self.lock:
            if thought_id not in self.thoughts:
                logger.warning(f"Thought {thought_id} not found for update")
                return False
            
            thought = self.thoughts[thought_id]
            
            # Update thought attributes
            for key, value in updates.items():
                if hasattr(thought, key):
                    setattr(thought, key, value)
            
            # Update access history
            self.access_history[thought_id].append(time.time())
            
            # If content was updated, recategorize and recluster
            if "content" in updates:
                # Remove from old categories and clusters
                await self._remove_from_categories(thought_id)
                await self._remove_from_clusters(thought_id)
                
                # Recategorize and recluster
                await self._categorize_thought(thought)
                await self._cluster_thought(thought)
                await self._recognize_patterns(thought)
                await self._identify_related_thoughts(thought)
            
            # If priority was updated or context provided, recalculate priority
            if "priority" in updates or context:
                if context:
                    thought.priority = await self._calculate_priority(thought, context)
                await self._update_priority_queue()
            
            logger.debug(f"Updated thought {thought_id}")
            return True
    
    async def get_related_thoughts(self, thought_id: str, max_thoughts: int = 10) -> List[Thought]:
        """
        Get thoughts related to the specified thought.
        
        Args:
            thought_id: The ID of the thought to find related thoughts for
            max_thoughts: Maximum number of related thoughts to return
            
        Returns:
            List of related thoughts
        """
        async with self.lock:
            if thought_id not in self.thoughts:
                return []
            
            related_ids = self.related_thoughts.get(thought_id, set())
            
            # Sort related thoughts by priority
            related_thoughts = [self.thoughts[tid] for tid in related_ids if tid in self.thoughts]
            related_thoughts.sort(key=lambda t: t.priority, reverse=True)
            
            # Return up to max_thoughts related thoughts
            result = related_thoughts[:max_thoughts]
            
            # Update access history for returned thoughts
            for thought in result:
                self.access_history[thought.id].append(time.time())
            
            return result
    
    async def get_thoughts_in_cluster(self, cluster_id: str) -> List[Thought]:
        """
        Get all thoughts in a specified cluster.
        
        Args:
            cluster_id: The ID of the cluster
            
        Returns:
            List of thoughts in the cluster
        """
        async with self.lock:
            if cluster_id not in self.thought_clusters:
                return []
            
            thought_ids = self.thought_clusters[cluster_id]
            thoughts = [self.thoughts[tid] for tid in thought_ids if tid in self.thoughts]
            
            # Update access history for returned thoughts
            for thought in thoughts:
                self.access_history[thought.id].append(time.time())
            
            return thoughts
    
    async def get_thoughts_by_category(self, category: str, max_thoughts: int = 10) -> List[Thought]:
        """
        Get thoughts in a specified category.
        
        Args:
            category: The category to get thoughts for
            max_thoughts: Maximum number of thoughts to return
            
        Returns:
            List of thoughts in the category
        """
        async with self.lock:
            if category not in self.thought_categories:
                return []
            
            thought_ids = self.thought_categories[category]
            thoughts = [self.thoughts[tid] for tid in thought_ids if tid in self.thoughts]
            
            # Sort by priority
            thoughts.sort(key=lambda t: t.priority, reverse=True)
            
            # Return up to max_thoughts
            result = thoughts[:max_thoughts]
            
            # Update access history for returned thoughts
            for thought in result:
                self.access_history[thought.id].append(time.time())
            
            return result
    
    async def get_thoughts_by_pattern(self, pattern: str, max_thoughts: int = 10) -> List[Thought]:
        """
        Get thoughts matching a specific pattern.
        
        Args:
            pattern: The pattern to match
            max_thoughts: Maximum number of thoughts to return
            
        Returns:
            List of thoughts matching the pattern
        """
        async with self.lock:
            if pattern not in self.common_patterns:
                return []
            
            thought_ids = self.common_patterns[pattern]
            thoughts = [self.thoughts[tid] for tid in thought_ids if tid in self.thoughts]
            
            # Sort by priority
            thoughts.sort(key=lambda t: t.priority, reverse=True)
            
            # Return up to max_thoughts
            result = thoughts[:max_thoughts]
            
            # Update access history for returned thoughts
            for thought in result:
                self.access_history[thought.id].append(time.time())
            
            return result
    
    async def _remove_lowest_priority_thought(self) -> None:
        """Remove the lowest priority thought from the thought stream."""
        if not self.priority_queue:
            return
        
        # Re-sort the priority queue to ensure we have the correct order
        self.priority_queue.sort()
        
        # Get the lowest priority thought
        _, _, thought_id = self.priority_queue[-1]
        
        # Clean up all references to this thought
        await self._remove_thought(thought_id)
        
        logger.debug(f"Removed lowest priority thought {thought_id}")
    
    async def _remove_thought(self, thought_id: str) -> None:
        """
        Remove a thought and all its references.
        
        Args:
            thought_id: The ID of the thought to remove
        """
        if thought_id not in self.thoughts:
            return
        
        # Remove from main dictionary
        del self.thoughts[thought_id]
        
        # Remove from access history
        if thought_id in self.access_history:
            del self.access_history[thought_id]
        
        # Remove from related thoughts
        for related_set in self.related_thoughts.values():
            related_set.discard(thought_id)
        if thought_id in self.related_thoughts:
            del self.related_thoughts[thought_id]
        
        # Remove from categories
        await self._remove_from_categories(thought_id)
        
        # Remove from clusters
        await self._remove_from_clusters(thought_id)
        
        # Remove from patterns
        for pattern_list in self.common_patterns.values():
            if thought_id in pattern_list:
                pattern_list.remove(thought_id)
        
        # Rebuild priority queue without the removed thought
        await self._update_priority_queue()
    
    async def _remove_from_categories(self, thought_id: str) -> None:
        """
        Remove a thought from all categories.
        
        Args:
            thought_id: The ID of the thought to remove
        """
        for category, thought_list in self.thought_categories.items():
            if thought_id in thought_list:
                thought_list.remove(thought_id)
    
    async def _remove_from_clusters(self, thought_id: str) -> None:
        """
        Remove a thought from its cluster.
        
        Args:
            thought_id: The ID of the thought to remove
        """
        if thought_id in self.thought_to_cluster:
            cluster_id = self.thought_to_cluster[thought_id]
            if cluster_id in self.thought_clusters and thought_id in self.thought_clusters[cluster_id]:
                self.thought_clusters[cluster_id].remove(thought_id)
                
                # If cluster is empty, remove it
                if not self.thought_clusters[cluster_id]:
                    del self.thought_clusters[cluster_id]
            
            del self.thought_to_cluster[thought_id]
    
    async def _update_priority_queue(self) -> None:
        """Update the priority queue based on current thoughts."""
        # Rebuild the priority queue
        self.priority_queue = [
            (-thought.priority, thought.created_at, thought.id)
            for thought in self.thoughts.values()
        ]
        
        # Heapify the queue
        heapq.heapify(self.priority_queue)
    
    async def _apply_forgetting_mechanism(self) -> None:
        """
        Apply multi-level forgetting mechanism to manage thought history using
        cognitive science-inspired memory models.
        
        This implements a sophisticated memory management system with:
        1. Short-term forgetting based on recency and frequency
        2. Long-term memory consolidation for important thoughts
        3. Context-sensitive retention based on relevance
        4. Adaptive forgetting thresholds based on cognitive load
        5. Preservation of thought clusters and patterns
        """
        current_time = time.time()
        thoughts_to_remove = []
        thoughts_to_consolidate = []
        
        # Get current cognitive load
        cognitive_load = len(self.thoughts) / self.max_capacity
        
        # Adjust forgetting threshold based on cognitive load
        # Higher load = more aggressive forgetting
        adaptive_threshold = self.forgetting_threshold
        if cognitive_load > 0.8:  # Very high load
            adaptive_threshold *= 1.3
        elif cognitive_load > 0.6:  # High load
            adaptive_threshold *= 1.15
        elif cognitive_load < 0.3:  # Low load
            adaptive_threshold *= 0.85
        
        # Track cluster and pattern representation to ensure diversity
        cluster_representation = defaultdict(int)
        pattern_representation = defaultdict(int)
        
        # 1. Analyze all thoughts for forgetting and consolidation
        for thought_id, thought in self.thoughts.items():
            # Skip very recently created thoughts (absolute protection period)
            if current_time - thought.created_at < self.retention_period * 0.1:
                continue
                
            # Get thought metadata
            access_times = self.access_history.get(thought_id, [])
            cluster_id = self.thought_to_cluster.get(thought_id)
            
            # Track cluster and pattern representation
            if cluster_id:
                cluster_representation[cluster_id] += 1
                
            # Track patterns this thought represents
            thought_patterns = set()
            for pattern_name, thought_ids in self.common_patterns.items():
                if thought_id in thought_ids:
                    pattern_representation[pattern_name] += 1
                    thought_patterns.add(pattern_name)
            
            # 2. Calculate multi-dimensional forgetting factors
            
            # 2.1 Time-based factors
            
            # Age factor (time since creation)
            age = current_time - thought.created_at
            normalized_age = min(1.0, age / self.retention_period)
            
            # Recency factor (time since last access)
            if access_times:
                last_access = max(access_times)
                recency = current_time - last_access
                normalized_recency = min(1.0, recency / self.retention_period)
            else:
                # If never accessed since creation, use age
                normalized_recency = normalized_age
            
            # 2.2 Usage-based factors
            
            # Frequency factor (number and pattern of accesses)
            if access_times:
                # Recent access frequency (exponentially weighted)
                recent_period = self.retention_period / 2
                recent_accesses = [current_time - t for t in access_times if current_time - t < recent_period]
                
                if recent_accesses:
                    # Weight more recent accesses higher
                    weighted_accesses = sum(math.exp(-0.01 * (current_time - t)) for t in access_times)
                    frequency_factor = math.exp(-0.5 * weighted_accesses)
                else:
                    frequency_factor = 0.9  # High forgetting factor for no recent accesses
            else:
                frequency_factor = 1.0  # Maximum forgetting factor for no accesses
            
            # Access pattern factor (spacing of accesses)
            if len(access_times) >= 2:
                # Calculate intervals between accesses
                sorted_times = sorted(access_times)
                intervals = [sorted_times[i] - sorted_times[i-1] for i in range(1, len(sorted_times))]
                
                # Spaced repetition is better for memory (lower forgetting factor)
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    interval_variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
                    
                    # High variance = spaced repetition = better retention
                    spacing_factor = math.exp(-0.0001 * interval_variance)
                else:
                    spacing_factor = 1.0
            else:
                spacing_factor = 1.0
            
            # 2.3 Content and relationship factors
            
            # Relationship factor (connected to other thoughts)
            related_count = len(self.related_thoughts.get(thought_id, set()))
            relationship_factor = math.exp(-0.2 * related_count)  # More connections = lower forgetting
            
            # Pattern factor (part of identified patterns)
            pattern_factor = math.exp(-0.3 * len(thought_patterns))  # More patterns = lower forgetting
            
            # Cluster importance factor (sole representative of a cluster)
            if cluster_id and cluster_representation[cluster_id] <= 2:
                cluster_factor = 0.3  # Low forgetting for important cluster representatives
            else:
                cluster_factor = 1.0
            
            # 2.4 Priority and metadata factors
            
            # Priority factor
            priority_factor = 1.0 - thought.priority
            
            # Explicit retention metadata
            retention_modifier = 1.0
            if thought.metadata.get("retain", False):
                retention_modifier = 0.3  # Explicitly marked for retention
            elif thought.metadata.get("important", False):
                retention_modifier = 0.5  # Marked as important
            elif thought.metadata.get("temporary", False):
                retention_modifier = 1.5  # Marked as temporary
            
            # 3. Calculate composite forgetting score with weighted factors
            
            # Base temporal forgetting (recency-frequency model)
            temporal_score = 0.4 * normalized_recency + 0.3 * frequency_factor + 0.3 * spacing_factor
            
            # Relationship-based forgetting
            relationship_score = 0.5 * relationship_factor + 0.3 * pattern_factor + 0.2 * cluster_factor
            
            # Content-based forgetting
            content_score = 0.7 * priority_factor + 0.3 * normalized_age
            
            # Final weighted forgetting score
            forgetting_score = (
                0.4 * temporal_score +
                0.3 * relationship_score +
                0.3 * content_score
            ) * retention_modifier
            
            # 4. Make forgetting decisions
            
            # 4.1 Identify thoughts for potential removal
            if forgetting_score > 0.7 and thought.priority < adaptive_threshold:
                # Check if this is the last representative of a pattern
                is_last_pattern_rep = False
                for pattern in thought_patterns:
                    if pattern_representation[pattern] <= 1:
                        is_last_pattern_rep = True
                        break
                
                # Don't remove if it's the last representative of a pattern
                # unless cognitive load is very high
                if not is_last_pattern_rep or cognitive_load > 0.9:
                    thoughts_to_remove.append((thought_id, forgetting_score))
            
            # 4.2 Identify thoughts for memory consolidation
            elif thought.priority > 0.7 and normalized_age > 0.5 and normalized_recency < 0.3:
                # High priority, old enough, recently accessed
                thoughts_to_consolidate.append(thought_id)
        
        # 5. Apply forgetting actions
        
        # 5.1 Sort thoughts by forgetting score (highest first)
        thoughts_to_remove.sort(key=lambda x: x[1], reverse=True)
        
        # 5.2 Determine how many thoughts to remove based on cognitive load
        removal_percentage = 0.05  # Default 5%
        if cognitive_load > 0.9:
            removal_percentage = 0.15  # 15% when very high load
        elif cognitive_load > 0.7:
            removal_percentage = 0.1  # 10% when high load
        elif cognitive_load < 0.4:
            removal_percentage = 0.02  # 2% when low load
            
        max_to_remove = max(1, int(self.max_capacity * removal_percentage))
        
        # 5.3 Remove thoughts
        for thought_id, score in thoughts_to_remove[:max_to_remove]:
            await self._remove_thought(thought_id)
            logger.debug(f"Forgot thought {thought_id} with score {score:.2f} through forgetting mechanism")
        
        # 5.4 Consolidate important thoughts to long-term memory
        for thought_id in thoughts_to_consolidate:
            if thought_id in self.thoughts:  # Check if still exists (not removed)
                thought = self.thoughts[thought_id]
                
                # Mark as consolidated in metadata
                thought.metadata["consolidated"] = True
                thought.metadata["consolidation_time"] = current_time
                
                # Reduce access frequency but maintain the thought
                # This simulates moving to long-term memory
                if thought_id in self.access_history:
                    # Keep only the most recent access
                    most_recent = max(self.access_history[thought_id])
                    self.access_history[thought_id] = [most_recent]
                
                logger.debug(f"Consolidated thought {thought_id} to long-term memory")
    
    async def _calculate_priority(self, thought: Thought, context: Dict[str, Any]) -> float:
        """
        Calculate thought priority based on content, context, and metadata using a multi-dimensional approach.
        
        Args:
            thought: The thought to calculate priority for
            context: The cognitive context
            
        Returns:
            Calculated priority (0.0 to 1.0)
        """
        # Initialize component priorities
        content_priority = 0.0
        context_priority = 0.0
        metadata_priority = 0.0
        temporal_priority = 0.0
        relational_priority = 0.0
        
        # 1. Content-based priority factors
        
        # Content length and complexity
        content_length = len(thought.content)
        normalized_length = min(1.0, content_length / 800)  # Normalize to [0, 1]
        
        # Complexity indicators
        complexity_indicators = {
            "complex": 0.05, "complicated": 0.05, "intricate": 0.05,
            "challenging": 0.04, "difficult": 0.04,
            "multi-faceted": 0.06, "sophisticated": 0.05
        }
        
        content_lower = thought.content.lower()
        complexity_score = sum(weight for term, weight in complexity_indicators.items()
                              if term in content_lower)
        
        # Sentence structure complexity
        sentences = re.split(r'[.!?]', thought.content)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        sentence_complexity = min(0.1, avg_sentence_length / 50)  # Max 0.1 for very complex sentences
        
        # Concept density
        unique_words = set(re.findall(r'\b\w{5,}\b', content_lower))
        concept_density = min(0.15, len(unique_words) / 30)  # Max 0.15 for high concept density
        
        # Type-based priority adjustment with more nuanced categories
        type_factors = {
            "question": 0.2,
            "insight": 0.3,
            "hypothesis": 0.25,
            "problem": 0.28,
            "solution": 0.27,
            "observation": 0.18,
            "decision": 0.26,
            "general": 0.0
        }
        type_adjustment = type_factors.get(thought.type, 0.0)
        
        # Calculate content priority component
        content_priority = (0.2 * normalized_length +
                           0.3 * complexity_score +
                           0.15 * sentence_complexity +
                           0.15 * concept_density +
                           0.2 * type_adjustment)
        
        # 2. Context-based priority factors
        
        # Cognitive load considerations
        cognitive_load = context.get("cognitive_load", 0.5)
        
        # Dynamic adjustment based on cognitive load
        if cognitive_load < 0.3:  # Low cognitive load
            # Prefer complex thoughts when load is low
            load_adjustment = 0.1 * (normalized_length + complexity_score)
        elif cognitive_load > 0.7:  # High cognitive load
            # Prefer simple thoughts when load is high
            load_adjustment = 0.1 * (1.0 - normalized_length - complexity_score)
        else:  # Moderate load
            load_adjustment = 0.05  # Neutral adjustment
        
        # Attention focus alignment
        attention_focus = context.get("attention_focus", "")
        focus_alignment = 0.0
        
        if attention_focus:
            # Direct mention of attention focus
            if attention_focus.lower() in content_lower:
                focus_alignment = 0.25
            else:
                # Check for semantic similarity using key terms
                focus_terms = set(re.findall(r'\b\w{4,}\b', attention_focus.lower()))
                content_terms = set(re.findall(r'\b\w{4,}\b', content_lower))
                
                if focus_terms and content_terms:
                    overlap = len(focus_terms.intersection(content_terms))
                    focus_alignment = min(0.2, 0.05 * overlap)  # Up to 0.2 for partial matches
        
        # Active goals alignment
        active_goals = context.get("active_goals", [])
        goal_alignment = 0.0
        
        for goal in active_goals:
            if goal.lower() in content_lower:
                goal_alignment += 0.1
                break
        
        # Calculate context priority component
        context_priority = load_adjustment + focus_alignment + goal_alignment
        
        # 3. Metadata-based priority factors
        
        # Rich metadata bonus
        metadata_keys = set(thought.metadata.keys()) - {"created_at", "last_accessed"}
        metadata_richness = min(0.1, 0.02 * len(metadata_keys))  # Up to 0.1 for rich metadata
        
        # Explicit priority flags
        explicit_priority = 0.0
        if thought.metadata.get("important", False):
            explicit_priority += 0.2
        if thought.metadata.get("urgent", False):
            explicit_priority += 0.3
        if thought.metadata.get("critical", False):
            explicit_priority += 0.4
        
        # Source credibility
        source_credibility = 0.0
        if "source" in thought.metadata:
            source = thought.metadata["source"]
            credibility_scores = {
                "verified": 0.15,
                "expert": 0.2,
                "reliable": 0.1,
                "uncertain": -0.1,
                "speculative": -0.15
            }
            source_credibility = credibility_scores.get(source, 0.0)
        
        # Calculate metadata priority component
        metadata_priority = metadata_richness + explicit_priority + source_credibility
        
        # 4. Temporal priority factors
        
        # Recency effect
        current_time = time.time()
        creation_time = thought.created_at
        age = current_time - creation_time
        
        # Exponential decay based on age
        recency_factor = math.exp(-0.000001 * age)  # Slow decay
        
        # Novelty bonus for very recent thoughts
        novelty_bonus = 0.0
        if age < 300:  # Less than 5 minutes old
            novelty_bonus = 0.15 * (1 - age/300)
        
        # Calculate temporal priority component
        temporal_priority = 0.1 * recency_factor + novelty_bonus
        
        # 5. Relational priority factors
        
        # Connected thoughts bonus
        connected_thoughts = len(self.related_thoughts.get(thought.id, set()))
        connectivity_score = min(0.2, 0.02 * connected_thoughts)  # Up to 0.2 for highly connected thoughts
        
        # Calculate relational priority component
        relational_priority = connectivity_score
        
        # 6. Calculate weighted final priority
        priority = (
            0.25 * content_priority +
            0.25 * context_priority +
            0.20 * metadata_priority +
            0.15 * temporal_priority +
            0.15 * relational_priority
        )
        
        # Add base priority with reduced weight to allow for dynamic adjustment
        priority = 0.3 * thought.priority + 0.7 * priority
        
        # Ensure priority is in range [0.0, 1.0]
        return max(0.0, min(1.0, priority))
    
    async def _calculate_contextual_priority(self, thought: Thought, context: Dict[str, Any]) -> float:
        """
        Calculate contextual priority for a thought based on current context.
        
        Args:
            thought: The thought to calculate priority for
            context: The cognitive context
            
        Returns:
            Contextual priority (0.0 to 1.0)
        """
        # Start with base priority
        base_priority = thought.priority
        
        # Context-based adjustment
        context_adjustment = 0.0
        
        # Adjust based on active thoughts
        active_thoughts = context.get("active_thoughts", [])
        if thought.id in active_thoughts:
            context_adjustment += 0.2
        
        # Adjust based on attention focus
        attention_focus = context.get("attention_focus", "")
        if attention_focus and attention_focus.lower() in thought.content.lower():
            context_adjustment += 0.25
        
        # Adjust based on recency
        current_time = time.time()
        last_access = max(self.access_history.get(thought.id, [thought.created_at]))
        recency = current_time - last_access
        recency_factor = math.exp(-0.0001 * recency)  # Decay factor
        context_adjustment += 0.1 * recency_factor
        
        # Calculate final contextual priority
        priority = base_priority + context_adjustment
        
        # Ensure priority is in range [0.0, 1.0]
        return max(0.0, min(1.0, priority))
    
    async def _identify_related_thoughts(self, thought: Thought) -> None:
        """
        Identify thoughts related to the given thought using advanced pattern recognition techniques.
        
        Args:
            thought: The thought to find related thoughts for
        """
        # Skip if there are very few thoughts
        if len(self.thoughts) < 3:
            return
        
        # Get content words and phrases
        content_lower = thought.content.lower()
        content_words = set(re.findall(r'\b\w{4,}\b', content_lower))
        content_bigrams = self._extract_bigrams(content_lower)
        content_entities = self._extract_entities(content_lower)
        
        if not content_words and not content_bigrams and not content_entities:
            return
        
        # Extract key concepts from the thought
        key_concepts = self._extract_key_concepts(thought)
        
        # Track relation strengths for later filtering
        relation_strengths = {}
        
        # 1. Content-based similarity analysis
        for other_id, other in self.thoughts.items():
            if other_id == thought.id:
                continue
            
            # Skip already processed relationships to avoid duplicate work
            if other_id in self.related_thoughts[thought.id]:
                continue
                
            other_content = other.content.lower()
            
            # Calculate multiple similarity metrics
            similarity_scores = []
            
            # Word-level Jaccard similarity
            other_words = set(re.findall(r'\b\w{4,}\b', other_content))
            if content_words and other_words:
                intersection = len(content_words.intersection(other_words))
                union = len(content_words.union(other_words))
                if union > 0:
                    word_similarity = intersection / union
                    similarity_scores.append(word_similarity)
            
            # Phrase-level similarity
            other_bigrams = self._extract_bigrams(other_content)
            if content_bigrams and other_bigrams:
                intersection = len(content_bigrams.intersection(other_bigrams))
                union = len(content_bigrams.union(other_bigrams))
                if union > 0:
                    phrase_similarity = intersection / union
                    similarity_scores.append(phrase_similarity * 1.2)  # Weight phrases higher
            
            # Entity-level similarity
            other_entities = self._extract_entities(other_content)
            if content_entities and other_entities:
                intersection = len(content_entities.intersection(other_entities))
                union = len(content_entities.union(other_entities))
                if union > 0:
                    entity_similarity = intersection / union
                    similarity_scores.append(entity_similarity * 1.5)  # Weight entities even higher
            
            # Key concept similarity
            other_concepts = self._extract_key_concepts(other)
            if key_concepts and other_concepts:
                intersection = len(key_concepts.intersection(other_concepts))
                union = len(key_concepts.union(other_concepts))
                if union > 0:
                    concept_similarity = intersection / union
                    similarity_scores.append(concept_similarity * 1.3)  # Weight concepts higher
            
            # Calculate aggregate similarity
            if similarity_scores:
                # Weighted average of similarity scores
                aggregate_similarity = sum(similarity_scores) / len(similarity_scores)
                
                # If similarity is above threshold, consider them related
                if aggregate_similarity > 0.25:  # Lower threshold for multi-metric approach
                    relation_strengths[(thought.id, other_id)] = aggregate_similarity
        
        # 2. Semantic relationship analysis
        for other_id, other in self.thoughts.items():
            if other_id == thought.id:
                continue
            
            # Skip already processed strong relationships
            if (thought.id, other_id) in relation_strengths and relation_strengths[(thought.id, other_id)] > 0.4:
                continue
            
            # Check for semantic relationships
            semantic_relation_score = 0.0
            
            # Question-answer relationship
            if thought.type == "question" and other.type in ["insight", "solution"]:
                # Check if answer addresses the question
                question_terms = set(re.findall(r'\b\w{4,}\b', thought.content.lower()))
                answer_terms = set(re.findall(r'\b\w{4,}\b', other.content.lower()))
                
                if question_terms and answer_terms:
                    overlap = len(question_terms.intersection(answer_terms))
                    if overlap >= 2:  # At least two shared terms
                        semantic_relation_score = 0.4 + (0.05 * overlap)
            
            # Problem-solution relationship
            elif thought.type == "problem" and other.type == "solution":
                problem_terms = set(re.findall(r'\b\w{4,}\b', thought.content.lower()))
                solution_terms = set(re.findall(r'\b\w{4,}\b', other.content.lower()))
                
                if problem_terms and solution_terms:
                    overlap = len(problem_terms.intersection(solution_terms))
                    if overlap >= 2:
                        semantic_relation_score = 0.45 + (0.05 * overlap)
            
            # Cause-effect relationship
            elif "because" in thought.content.lower() and any(term in other.content.lower()
                                                           for term in ["result", "effect", "outcome", "consequence"]):
                semantic_relation_score = 0.4
            
            # Hypothesis-evidence relationship
            elif thought.type == "hypothesis" and any(term in other.content.lower()
                                                   for term in ["evidence", "support", "confirm", "verify", "prove"]):
                semantic_relation_score = 0.45
            
            if semantic_relation_score > 0:
                relation_strengths[(thought.id, other_id)] = max(
                    relation_strengths.get((thought.id, other_id), 0),
                    semantic_relation_score
                )
        
        # 3. Type and metadata analysis
        for other_id, other in self.thoughts.items():
            if other_id == thought.id:
                continue
            
            # Skip already processed strong relationships
            if (thought.id, other_id) in relation_strengths and relation_strengths[(thought.id, other_id)] > 0.5:
                continue
            
            type_metadata_score = 0.0
            
            # Type-based relationships with finer granularity
            type_pairs = [
                (["question"], ["insight", "hypothesis", "solution"]),
                (["problem"], ["solution", "insight"]),
                (["hypothesis"], ["evidence", "insight", "observation"]),
                (["insight"], ["action", "decision", "hypothesis"])
            ]
            
            for primary_types, related_types in type_pairs:
                if thought.type in primary_types and other.type in related_types:
                    type_metadata_score += 0.3
                    break
            
            # Check for shared metadata keys with similar values
            shared_keys = set(thought.metadata.keys()).intersection(set(other.metadata.keys()))
            metadata_match_count = 0
            
            for key in shared_keys:
                if key in ["created_at", "last_accessed"]:
                    continue
                
                # For string values, check for similarity
                if isinstance(thought.metadata[key], str) and isinstance(other.metadata[key], str):
                    t_value = thought.metadata[key].lower()
                    o_value = other.metadata[key].lower()
                    
                    # Calculate string similarity
                    if t_value == o_value:
                        metadata_match_count += 1.0
                    elif t_value in o_value or o_value in t_value:
                        metadata_match_count += 0.7
                    else:
                        # Check for partial matches
                        t_words = set(t_value.split())
                        o_words = set(o_value.split())
                        if t_words and o_words:
                            overlap = len(t_words.intersection(o_words))
                            if overlap > 0:
                                metadata_match_count += 0.3 * (overlap / max(len(t_words), len(o_words)))
                
                # For other values, check for equality
                elif thought.metadata[key] == other.metadata[key]:
                    metadata_match_count += 1.0
            
            # Calculate metadata similarity score
            if shared_keys:
                metadata_score = 0.2 * min(1.0, metadata_match_count / len(shared_keys))
                type_metadata_score += metadata_score
            
            if type_metadata_score > 0:
                relation_strengths[(thought.id, other_id)] = max(
                    relation_strengths.get((thought.id, other_id), 0),
                    type_metadata_score
                )
        
        # 4. Apply the identified relationships with strength thresholds
        for (t_id, o_id), strength in relation_strengths.items():
            if strength >= 0.25:  # Minimum threshold for relationship
                self.related_thoughts[t_id].add(o_id)
                self.related_thoughts[o_id].add(t_id)
                
                # For strong relationships, add metadata about relationship strength
                if strength >= 0.4:
                    if "relationships" not in self.thoughts[t_id].metadata:
                        self.thoughts[t_id].metadata["relationships"] = {}
                    if "relationships" not in self.thoughts[o_id].metadata:
                        self.thoughts[o_id].metadata["relationships"] = {}
                    
                    self.thoughts[t_id].metadata["relationships"][o_id] = strength
                    self.thoughts[o_id].metadata["relationships"][t_id] = strength
    
    def _extract_bigrams(self, text: str) -> Set[str]:
        """
        Extract bigrams (two-word phrases) from text.
        
        Args:
            text: The text to extract bigrams from
            
        Returns:
            Set of bigrams
        """
        words = re.findall(r'\b\w+\b', text.lower())
        return set(' '.join(words[i:i+2]) for i in range(len(words)-1))
    
    def _extract_entities(self, text: str) -> Set[str]:
        """
        Extract potential named entities from text.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            Set of potential entities
        """
        # Simple heuristic: capitalized words not at the start of sentences
        sentences = re.split(r'[.!?]\s+', text)
        entities = set()
        
        for sentence in sentences:
            words = sentence.split()
            
            # Skip first word of sentence
            for word in words[1:]:
                # Check if word starts with capital letter
                if word and word[0].isupper() and len(word) > 1:
                    entities.add(word.lower())
        
        # Also extract potential technical terms
        tech_patterns = [
            r'\b[A-Z][a-z]+[A-Z][a-z]+\w*\b',  # CamelCase
            r'\b[A-Z][A-Z]+\b',  # ACRONYMS
            r'\b\w+\.\w+\b'  # dot.notation
        ]
        
        for pattern in tech_patterns:
            entities.update(w.lower() for w in re.findall(pattern, text))
        
        return entities
    
    def _extract_key_concepts(self, thought: Thought) -> Set[str]:
        """
        Extract key concepts from a thought based on content and type.
        
        Args:
            thought: The thought to extract concepts from
            
        Returns:
            Set of key concepts
        """
        content = thought.content.lower()
        concepts = set()
        
        # Extract concepts based on thought type
        if thought.type == "question":
            # For questions, extract the subject being questioned
            question_words = ["what", "how", "why", "when", "where", "who", "which"]
            for qw in question_words:
                matches = re.findall(fr'\b{qw}\s+\w+\s+(\w+)\b', content)
                concepts.update(matches)
                
                # Also look for noun phrases after question words
                matches = re.findall(fr'\b{qw}\s+\w+\s+\w+\s+(\w+)\b', content)
                concepts.update(matches)
        
        elif thought.type == "insight":
            # For insights, look for key terms after indicator phrases
            indicators = ["realized that", "understood that", "discovered that", "found that"]
            for indicator in indicators:
                if indicator in content:
                    after_indicator = content.split(indicator)[1]
                    words = re.findall(r'\b\w{5,}\b', after_indicator)
                    concepts.update(words[:3])  # Take first 3 significant words
        
        elif thought.type == "hypothesis":
            # For hypotheses, extract terms from if-then structures
            if_then_matches = re.findall(r'\bif\s+(.+?)\s+then\s+(.+?)[\.,]', content)
            for if_part, then_part in if_then_matches:
                concepts.update(re.findall(r'\b\w{5,}\b', if_part))
                concepts.update(re.findall(r'\b\w{5,}\b', then_part))
        
        # Extract emphasized terms (surrounded by * or _)
        emphasized = re.findall(r'[\*_](\w+)[\*_]', thought.content)
        concepts.update(w.lower() for w in emphasized)
        
        # Extract terms from metadata if available
        if "keywords" in thought.metadata and isinstance(thought.metadata["keywords"], list):
            concepts.update(k.lower() for k in thought.metadata["keywords"])
        
        # Extract terms that appear in title case (potential key concepts)
        title_case_words = re.findall(r'\b[A-Z][a-z]{4,}\b', thought.content)
        concepts.update(w.lower() for w in title_case_words)
        
        return concepts
    
    async def _categorize_thought(self, thought: Thought) -> None:
        """
        Categorize a thought based on its content, metadata, and semantic characteristics
        using a multi-dimensional categorization approach.
        
        Args:
            thought: The thought to categorize
        """
        # 1. Type-based categorization with subtypes
        self.thought_categories[f"type:{thought.type}"].append(thought.id)
        
        # Identify subtypes based on content patterns
        content_lower = thought.content.lower()
        
        # Question subtypes
        if thought.type == "question":
            if "why" in content_lower:
                self.thought_categories["type:question:why"].append(thought.id)
            elif "how" in content_lower:
                self.thought_categories["type:question:how"].append(thought.id)
            elif "what" in content_lower:
                self.thought_categories["type:question:what"].append(thought.id)
            elif "when" in content_lower:
                self.thought_categories["type:question:when"].append(thought.id)
            elif "where" in content_lower:
                self.thought_categories["type:question:where"].append(thought.id)
            elif "who" in content_lower:
                self.thought_categories["type:question:who"].append(thought.id)
        
        # Insight subtypes
        elif thought.type == "insight":
            if any(term in content_lower for term in ["pattern", "correlation", "relationship"]):
                self.thought_categories["type:insight:pattern"].append(thought.id)
            elif any(term in content_lower for term in ["cause", "because", "reason"]):
                self.thought_categories["type:insight:causal"].append(thought.id)
            elif any(term in content_lower for term in ["predict", "future", "will", "expect"]):
                self.thought_categories["type:insight:predictive"].append(thought.id)
        
        # Hypothesis subtypes
        elif thought.type == "hypothesis":
            if "if" in content_lower and "then" in content_lower:
                self.thought_categories["type:hypothesis:conditional"].append(thought.id)
            elif any(term in content_lower for term in ["may", "might", "could", "possibly"]):
                self.thought_categories["type:hypothesis:speculative"].append(thought.id)
            elif any(term in content_lower for term in ["should", "must", "need to"]):
                self.thought_categories["type:hypothesis:prescriptive"].append(thought.id)
        
        # 2. Priority-based categorization with finer granularity
        if thought.priority >= 0.9:
            self.thought_categories["priority:critical"].append(thought.id)
        elif thought.priority >= 0.75:
            self.thought_categories["priority:high"].append(thought.id)
        elif thought.priority >= 0.5:
            self.thought_categories["priority:medium"].append(thought.id)
        elif thought.priority >= 0.25:
            self.thought_categories["priority:low"].append(thought.id)
        else:
            self.thought_categories["priority:background"].append(thought.id)
        
        # 3. Content-based categorization with semantic analysis
        
        # Question detection with context
        if "?" in content_lower:
            self.thought_categories["content:explicit_question"].append(thought.id)
        
        if any(q in content_lower for q in ["what", "how", "why", "when", "where", "who"]):
            self.thought_categories["content:implicit_question"].append(thought.id)
        
        # Problem-solution spectrum
        problem_terms = ["problem", "issue", "error", "bug", "difficulty", "challenge",
                         "obstacle", "barrier", "limitation", "constraint", "bottleneck"]
        solution_terms = ["solution", "answer", "resolve", "fix", "approach", "method",
                          "technique", "strategy", "workaround", "remedy", "address"]
        
        # Calculate problem and solution scores
        problem_score = sum(1 for term in problem_terms if term in content_lower)
        solution_score = sum(1 for term in solution_terms if term in content_lower)
        
        # Categorize based on problem-solution balance
        if problem_score > 0 and solution_score > 0:
            self.thought_categories["content:problem_solution_pair"].append(thought.id)
        elif problem_score > 0:
            self.thought_categories["content:problem"].append(thought.id)
            if problem_score >= 3:
                self.thought_categories["content:complex_problem"].append(thought.id)
        elif solution_score > 0:
            self.thought_categories["content:solution"].append(thought.id)
            if solution_score >= 3:
                self.thought_categories["content:comprehensive_solution"].append(thought.id)
        
        # Action-oriented content
        action_terms = ["action", "do", "implement", "create", "build", "develop",
                       "execute", "perform", "accomplish", "achieve", "complete"]
        
        action_score = sum(1 for term in action_terms if term in content_lower)
        if action_score > 0:
            self.thought_categories["content:action"].append(thought.id)
            if action_score >= 3:
                self.thought_categories["content:action_plan"].append(thought.id)
        
        # Emotional content
        positive_emotions = ["happy", "excited", "optimistic", "confident", "satisfied"]
        negative_emotions = ["concerned", "worried", "frustrated", "confused", "disappointed"]
        
        if any(emotion in content_lower for emotion in positive_emotions):
            self.thought_categories["content:positive_emotion"].append(thought.id)
        
        if any(emotion in content_lower for emotion in negative_emotions):
            self.thought_categories["content:negative_emotion"].append(thought.id)
        
        # Temporal orientation
        past_indicators = ["was", "did", "had", "previously", "before", "earlier"]
        present_indicators = ["is", "am", "are", "currently", "now", "present"]
        future_indicators = ["will", "going to", "plan", "expect", "anticipate", "future"]
        
        if any(term in content_lower for term in past_indicators):
            self.thought_categories["content:past_oriented"].append(thought.id)
        
        if any(term in content_lower for term in present_indicators):
            self.thought_categories["content:present_oriented"].append(thought.id)
        
        if any(term in content_lower for term in future_indicators):
            self.thought_categories["content:future_oriented"].append(thought.id)
        
        # 4. Complexity-based categorization
        
        # Count sentences
        sentences = re.split(r'[.!?]', thought.content)
        sentence_count = sum(1 for s in sentences if s.strip())
        
        # Analyze sentence length and structure
        avg_words_per_sentence = 0
        if sentence_count > 0:
            total_words = sum(len(s.split()) for s in sentences if s.strip())
            avg_words_per_sentence = total_words / sentence_count
        
        # Categorize based on complexity metrics
        if sentence_count >= 5 or avg_words_per_sentence >= 20:
            self.thought_categories["complexity:high"].append(thought.id)
        elif sentence_count >= 3 or avg_words_per_sentence >= 12:
            self.thought_categories["complexity:medium"].append(thought.id)
        else:
            self.thought_categories["complexity:low"].append(thought.id)
        
        # 5. Advanced metadata-based categorization
        
        # Process all metadata
        for key, value in thought.metadata.items():
            if key in ["created_at", "last_accessed", "relationships"]:
                continue
            
            # Create category for metadata key
            category_name = f"metadata:{key}"
            self.thought_categories[category_name].append(thought.id)
            
            # For string values, create more specific categories
            if isinstance(value, str):
                # Normalize value for category name
                normalized_value = value.lower().replace(" ", "_")
                category_name = f"metadata:{key}:{normalized_value}"
                self.thought_categories[category_name].append(thought.id)
            
            # For boolean values, create specific true/false categories
            elif isinstance(value, bool):
                state = "true" if value else "false"
                category_name = f"metadata:{key}:{state}"
                self.thought_categories[category_name].append(thought.id)
            
            # For numeric values, create range-based categories
            elif isinstance(value, (int, float)):
                if value > 0.8:
                    range_category = "very_high"
                elif value > 0.6:
                    range_category = "high"
                elif value > 0.4:
                    range_category = "medium"
                elif value > 0.2:
                    range_category = "low"
                else:
                    range_category = "very_low"
                
                category_name = f"metadata:{key}:{range_category}"
                self.thought_categories[category_name].append(thought.id)
        
        # 6. Domain-specific categorization based on content analysis
        
        # Technical domain detection
        technical_terms = [
            "algorithm", "function", "system", "process", "module", "component",
            "interface", "architecture", "framework", "implementation", "protocol"
        ]
        
        if sum(1 for term in technical_terms if term in content_lower) >= 2:
            self.thought_categories["domain:technical"].append(thought.id)
        
        # Conceptual domain detection
        conceptual_terms = [
            "concept", "theory", "principle", "idea", "philosophy", "perspective",
            "viewpoint", "paradigm", "model", "abstraction", "framework"
        ]
        
        if sum(1 for term in conceptual_terms if term in content_lower) >= 2:
            self.thought_categories["domain:conceptual"].append(thought.id)
        
        # Strategic domain detection
        strategic_terms = [
            "strategy", "plan", "goal", "objective", "mission", "vision", "roadmap",
            "outcome", "target", "milestone", "priority", "direction"
        ]
        
        if sum(1 for term in strategic_terms if term in content_lower) >= 2:
            self.thought_categories["domain:strategic"].append(thought.id)
    
    async def _cluster_thought(self, thought: Thought) -> None:
        """
        Cluster a thought with similar thoughts using multi-dimensional similarity metrics
        and hierarchical clustering approach.
        
        Args:
            thought: The thought to cluster
        """
        # Skip if there are very few thoughts
        if len(self.thoughts) < 5:
            # Create a singleton cluster
            cluster_id = str(uuid.uuid4())
            self.thought_clusters[cluster_id] = [thought.id]
            self.thought_to_cluster[thought.id] = cluster_id
            return
        
        # 1. Prepare multi-dimensional feature vectors for similarity calculation
        
        # Content-based features
        content_lower = thought.content.lower()
        content_words = set(re.findall(r'\b\w{4,}\b', content_lower))
        content_bigrams = self._extract_bigrams(content_lower)
        content_entities = self._extract_entities(content_lower)
        key_concepts = self._extract_key_concepts(thought)
        
        if not content_words and not content_bigrams and not content_entities and not key_concepts:
            # Create a singleton cluster if no meaningful content
            cluster_id = str(uuid.uuid4())
            self.thought_clusters[cluster_id] = [thought.id]
            self.thought_to_cluster[thought.id] = cluster_id
            return
        
        # Type and metadata features
        thought_type = thought.type
        thought_metadata_keys = set(k for k in thought.metadata.keys()
                                  if k not in ["created_at", "last_accessed", "relationships"])
        
        # 2. Calculate cluster similarity scores using multiple metrics
        
        cluster_scores = {}  # Map of cluster_id to similarity score
        
        for cluster_id, thought_ids in self.thought_clusters.items():
            # Skip empty clusters
            if not thought_ids:
                continue
                
            # Calculate multi-dimensional similarity with thoughts in cluster
            content_similarities = []
            type_similarities = []
            metadata_similarities = []
            concept_similarities = []
            
            for other_id in thought_ids:
                if other_id not in self.thoughts:
                    continue
                    
                other = self.thoughts[other_id]
                
                # 2.1 Content-based similarity
                
                # Word-level similarity
                other_content = other.content.lower()
                other_words = set(re.findall(r'\b\w{4,}\b', other_content))
                
                if content_words and other_words:
                    intersection = len(content_words.intersection(other_words))
                    union = len(content_words.union(other_words))
                    
                    if union > 0:
                        word_similarity = intersection / union
                        content_similarities.append(word_similarity)
                
                # Phrase-level similarity
                other_bigrams = self._extract_bigrams(other_content)
                
                if content_bigrams and other_bigrams:
                    intersection = len(content_bigrams.intersection(other_bigrams))
                    union = len(content_bigrams.union(other_bigrams))
                    
                    if union > 0:
                        phrase_similarity = intersection / union
                        content_similarities.append(phrase_similarity * 1.2)  # Weight phrases higher
                
                # Entity-level similarity
                other_entities = self._extract_entities(other_content)
                
                if content_entities and other_entities:
                    intersection = len(content_entities.intersection(other_entities))
                    union = len(content_entities.union(other_entities))
                    
                    if union > 0:
                        entity_similarity = intersection / union
                        content_similarities.append(entity_similarity * 1.3)  # Weight entities higher
                
                # 2.2 Concept-based similarity
                
                other_concepts = self._extract_key_concepts(other)
                
                if key_concepts and other_concepts:
                    intersection = len(key_concepts.intersection(other_concepts))
                    union = len(key_concepts.union(other_concepts))
                    
                    if union > 0:
                        concept_similarity = intersection / union
                        concept_similarities.append(concept_similarity)
                
                # 2.3 Type similarity
                
                # Same type or related types
                if thought_type == other.type:
                    type_similarities.append(1.0)
                elif (thought_type == "question" and other.type == "insight") or \
                     (thought_type == "insight" and other.type == "question") or \
                     (thought_type == "problem" and other.type == "solution") or \
                     (thought_type == "solution" and other.type == "problem"):
                    type_similarities.append(0.7)
                else:
                    type_similarities.append(0.3)
                
                # 2.4 Metadata similarity
                
                other_metadata_keys = set(k for k in other.metadata.keys()
                                        if k not in ["created_at", "last_accessed", "relationships"])
                
                # Calculate metadata key overlap
                if thought_metadata_keys or other_metadata_keys:
                    keys_intersection = len(thought_metadata_keys.intersection(other_metadata_keys))
                    keys_union = len(thought_metadata_keys.union(other_metadata_keys))
                    
                    if keys_union > 0:
                        metadata_key_similarity = keys_intersection / keys_union
                        metadata_similarities.append(metadata_key_similarity)
                    
                    # Calculate metadata value similarity for shared keys
                    shared_keys = thought_metadata_keys.intersection(other_metadata_keys)
                    if shared_keys:
                        value_similarities = []
                        
                        for key in shared_keys:
                            t_value = thought.metadata[key]
                            o_value = other.metadata[key]
                            
                            # String value similarity
                            if isinstance(t_value, str) and isinstance(o_value, str):
                                t_value_lower = t_value.lower()
                                o_value_lower = o_value.lower()
                                
                                if t_value_lower == o_value_lower:
                                    value_similarities.append(1.0)
                                elif t_value_lower in o_value_lower or o_value_lower in t_value_lower:
                                    value_similarities.append(0.7)
                                else:
                                    # Word overlap
                                    t_words = set(t_value_lower.split())
                                    o_words = set(o_value_lower.split())
                                    
                                    if t_words and o_words:
                                        overlap = len(t_words.intersection(o_words))
                                        word_overlap = overlap / max(len(t_words), len(o_words))
                                        value_similarities.append(word_overlap * 0.5)
                            
                            # Exact equality for other types
                            elif t_value == o_value:
                                value_similarities.append(1.0)
                        
                        if value_similarities:
                            metadata_similarities.append(sum(value_similarities) / len(value_similarities))
            
            # 3. Calculate weighted aggregate cluster similarity
            
            dimension_weights = {
                "content": 0.4,
                "concept": 0.3,
                "type": 0.15,
                "metadata": 0.15
            }
            
            dimension_scores = []
            
            if content_similarities:
                dimension_scores.append((dimension_weights["content"],
                                        sum(content_similarities) / len(content_similarities)))
            
            if concept_similarities:
                dimension_scores.append((dimension_weights["concept"],
                                        sum(concept_similarities) / len(concept_similarities)))
            
            if type_similarities:
                dimension_scores.append((dimension_weights["type"],
                                        sum(type_similarities) / len(type_similarities)))
            
            if metadata_similarities:
                dimension_scores.append((dimension_weights["metadata"],
                                        sum(metadata_similarities) / len(metadata_similarities)))
            
            # Calculate weighted average if we have any scores
            if dimension_scores:
                total_weight = sum(weight for weight, _ in dimension_scores)
                weighted_score = sum(weight * score for weight, score in dimension_scores) / total_weight
                
                # Store cluster score
                cluster_scores[cluster_id] = weighted_score
        
        # 4. Determine best cluster match or create new cluster
        
        # Find best matching cluster
        best_cluster_id = None
        best_similarity = 0.0
        
        for cluster_id, similarity in cluster_scores.items():
            if similarity > best_similarity:
                best_similarity = similarity
                best_cluster_id = cluster_id
        
        # 5. Apply clustering decision with adaptive threshold
        
        # Adjust threshold based on cluster size to encourage larger clusters
        adaptive_threshold = self.cluster_similarity_threshold
        
        if best_cluster_id:
            cluster_size = len(self.thought_clusters[best_cluster_id])
            # Slightly lower threshold for larger clusters to encourage growth
            if cluster_size >= 10:
                adaptive_threshold -= 0.05
            elif cluster_size >= 5:
                adaptive_threshold -= 0.02
        
        # If similarity is above threshold, add to existing cluster
        if best_similarity >= adaptive_threshold and best_cluster_id:
            self.thought_clusters[best_cluster_id].append(thought.id)
            self.thought_to_cluster[thought.id] = best_cluster_id
            
            # Add cluster information to thought metadata
            if "cluster" not in thought.metadata:
                thought.metadata["cluster"] = {}
            
            thought.metadata["cluster"]["id"] = best_cluster_id
            thought.metadata["cluster"]["similarity"] = best_similarity
            thought.metadata["cluster"]["size"] = len(self.thought_clusters[best_cluster_id])
        else:
            # Create a new cluster
            cluster_id = str(uuid.uuid4())
            self.thought_clusters[cluster_id] = [thought.id]
            self.thought_to_cluster[thought.id] = cluster_id
            
            # Add cluster information to thought metadata
            if "cluster" not in thought.metadata:
                thought.metadata["cluster"] = {}
            
            thought.metadata["cluster"]["id"] = cluster_id
            thought.metadata["cluster"]["similarity"] = 1.0  # Perfect match with itself
            thought.metadata["cluster"]["size"] = 1
    
    async def _recognize_patterns(self, thought: Thought) -> None:
        """
        Recognize linguistic, semantic, and structural patterns in thought content
        using advanced pattern recognition techniques.
        
        Args:
            thought: The thought to recognize patterns in
        """
        content = thought.content
        content_lower = content.lower()
        
        # 1. Linguistic pattern recognition with expanded pattern sets
        
        # Define comprehensive pattern recognition rules with more specific patterns
        linguistic_patterns = [
            # Question patterns with finer granularity
            (r'\bwhy\s+(?:is|are|do|does|did|would|should|could|might)\s+\w+', "why_reasoning_question"),
            (r'\bhow\s+(?:to|do|does|can|could|would|should)\s+\w+', "how_procedural_question"),
            (r'\bhow\s+(?:many|much|long|often)\s+\w+', "how_quantitative_question"),
            (r'\bwhat\s+(?:is|are|was|were)\s+(?:the|a|an)?\s+\w+', "what_definition_question"),
            (r'\bwhat\s+(?:if|would|happens|could)\s+\w+', "what_hypothetical_question"),
            (r'\bwhen\s+(?:is|are|will|would|should|could|did|do|does)\s+\w+', "when_temporal_question"),
            (r'\bwhere\s+(?:is|are|was|were|will|would|should|could)\s+\w+', "where_spatial_question"),
            (r'\bwho\s+(?:is|are|was|were|will|would|should|could)\s+\w+', "who_identity_question"),
            
            # Hypothesis patterns with subtypes
            (r'\bif\s+.{3,50}\s+then\s+.{3,50}', "conditional_hypothesis"),
            (r'\b(?:may|might)\s+(?:be|have|cause|result|lead)\s+\w+', "possibility_hypothesis"),
            (r'\bcould\s+(?:be|have|cause|result|lead)\s+\w+', "potential_hypothesis"),
            (r'\bperhaps\s+.{3,50}', "speculative_hypothesis"),
            (r'\bpossibly\s+.{3,50}', "speculative_hypothesis"),
            (r'\bassume\s+(?:that)?\s+.{3,50}', "assumptive_hypothesis"),
            (r'\blet\'s\s+say\s+.{3,50}', "assumptive_hypothesis"),
            
            # Insight patterns with subtypes
            (r'\b(?:realized|understood|recognized|discovered|found\s+out)\s+(?:that)?\s+.{3,50}', "realization_insight"),
            (r'\bconnection\s+between\s+.{3,50}\s+and\s+.{3,50}', "connection_insight"),
            (r'\bpattern\s+(?:of|in|among)\s+.{3,50}', "pattern_insight"),
            (r'\bkey\s+(?:insight|finding|observation)\s+(?:is|was)\s+.{3,50}', "key_insight"),
            (r'\b(?:surprisingly|interestingly|notably)\s+.{3,50}', "notable_insight"),
            (r'\bthis\s+(?:suggests|indicates|implies|means)\s+(?:that)?\s+.{3,50}', "inferential_insight"),
            
            # Action patterns with subtypes
            (r'\bneed\s+to\s+\w+', "necessity_action"),
            (r'\bshould\s+(?:probably|definitely|possibly)?\s+\w+', "recommendation_action"),
            (r'\bmust\s+(?:definitely|absolutely|certainly)?\s+\w+', "imperative_action"),
            (r'\bplan\s+to\s+\w+', "planned_action"),
            (r'\bgoing\s+to\s+\w+', "intended_action"),
            (r'\bwill\s+(?:need\s+to|have\s+to|be\s+able\s+to)?\s+\w+', "future_action"),
            (r'\blet\'s\s+\w+', "collaborative_action"),
            
            # Reasoning patterns
            (r'\bbecause\s+.{3,50}', "causal_reasoning"),
            (r'\bsince\s+.{3,50}', "causal_reasoning"),
            (r'\bdue\s+to\s+.{3,50}', "causal_reasoning"),
            (r'\btherefore\s+.{3,50}', "deductive_reasoning"),
            (r'\bthus\s+.{3,50}', "deductive_reasoning"),
            (r'\bhence\s+.{3,50}', "deductive_reasoning"),
            (r'\bconsequently\s+.{3,50}', "consequential_reasoning"),
            
            # Comparison patterns
            (r'\bsimilar\s+to\s+.{3,50}', "similarity_comparison"),
            (r'\bdiffers?\s+from\s+.{3,50}', "difference_comparison"),
            (r'\bin\s+contrast\s+to\s+.{3,50}', "contrast_comparison"),
            (r'\bon\s+(?:the|one)\s+hand\s+.{3,50}', "balanced_comparison"),
            (r'\bon\s+the\s+other\s+hand\s+.{3,50}', "balanced_comparison"),
            
            # Problem patterns
            (r'\bissue\s+(?:is|with|that)\s+.{3,50}', "problem_statement"),
            (r'\bchallenge\s+(?:is|with|that)\s+.{3,50}', "problem_statement"),
            (r'\bdifficulty\s+(?:is|with|that)\s+.{3,50}', "problem_statement"),
            (r'\bproblem\s+(?:is|with|that)\s+.{3,50}', "problem_statement"),
            
            # Solution patterns
            (r'\bsolution\s+(?:is|would\s+be|could\s+be|might\s+be)\s+.{3,50}', "solution_proposal"),
            (r'\bapproach\s+(?:is|would\s+be|could\s+be|might\s+be)\s+.{3,50}', "solution_proposal"),
            (r'\bresolve\s+(?:this|the|that)\s+by\s+.{3,50}', "solution_proposal"),
            (r'\bfix\s+(?:this|the|that)\s+by\s+.{3,50}', "solution_proposal"),
        ]
        
        # 2. Semantic pattern recognition
        
        # Define semantic pattern categories and their indicators
        semantic_patterns = {
            "temporal_sequence": [
                "first", "second", "third", "next", "then", "after", "before",
                "previously", "subsequently", "finally", "lastly", "initially"
            ],
            "causal_relationship": [
                "because", "since", "due to", "as a result", "consequently",
                "therefore", "thus", "hence", "leads to", "causes", "affects"
            ],
            "comparison_contrast": [
                "similarly", "likewise", "in contrast", "however", "but",
                "although", "whereas", "unlike", "like", "as", "compared to"
            ],
            "emphasis": [
                "importantly", "significantly", "notably", "critically",
                "essentially", "fundamentally", "particularly", "especially"
            ],
            "uncertainty": [
                "perhaps", "maybe", "possibly", "potentially", "presumably",
                "supposedly", "allegedly", "seemingly", "apparently"
            ],
            "certainty": [
                "definitely", "certainly", "undoubtedly", "clearly",
                "obviously", "evidently", "unquestionably", "absolutely"
            ],
            "evaluation": [
                "good", "bad", "better", "worse", "best", "worst",
                "effective", "ineffective", "successful", "unsuccessful"
            ]
        }
        
        # 3. Structural pattern recognition
        
        # Define structural patterns to identify
        structural_patterns = {
            "list": r'(?:\d+\.\s+.+\n){2,}',  # Numbered list with at least 2 items
            "bullet_points": r'(?:[-•*]\s+.+\n){2,}',  # Bulleted list with at least 2 items
            "definition": r'\b\w+\s+(?:is|are|refers to|means)\s+.{3,50}',
            "example": r'(?:for example|for instance|e\.g\.|such as)\s+.{3,50}',
            "conclusion": r'(?:in conclusion|to summarize|to sum up|in summary|therefore)\s+.{3,50}',
            "introduction": r'(?:^|\n)(?:this|the following|below)\s+(?:discusses|describes|explains|outlines|presents)\s+.{3,50}'
        }
        
        # Process and store recognized patterns
        
        # 1. Process linguistic patterns
        for pattern_regex, pattern_name in linguistic_patterns:
            if re.search(pattern_regex, content_lower):
                # Extract the specific match for more context
                matches = re.findall(pattern_regex, content_lower)
                
                # Add thought to pattern with match context
                if pattern_name not in self.common_patterns:
                    self.common_patterns[pattern_name] = []
                
                if thought.id not in self.common_patterns[pattern_name]:
                    self.common_patterns[pattern_name].append(thought.id)
                    
                    # Store pattern match in thought metadata for future reference
                    if "patterns" not in thought.metadata:
                        thought.metadata["patterns"] = {}
                    
                    if pattern_name not in thought.metadata["patterns"]:
                        thought.metadata["patterns"][pattern_name] = matches[0] if matches else True
        
        # 2. Process semantic patterns
        for semantic_type, indicators in semantic_patterns.items():
            pattern_name = f"semantic:{semantic_type}"
            
            # Check for presence of semantic indicators
            matches = [ind for ind in indicators if ind in content_lower]
            if matches:
                # Add thought to semantic pattern
                if pattern_name not in self.common_patterns:
                    self.common_patterns[pattern_name] = []
                
                if thought.id not in self.common_patterns[pattern_name]:
                    self.common_patterns[pattern_name].append(thought.id)
                    
                    # Store semantic pattern in thought metadata
                    if "patterns" not in thought.metadata:
                        thought.metadata["patterns"] = {}
                    
                    if pattern_name not in thought.metadata["patterns"]:
                        thought.metadata["patterns"][pattern_name] = matches
        
        # 3. Process structural patterns
        for struct_type, pattern_regex in structural_patterns.items():
            pattern_name = f"structure:{struct_type}"
            
            if re.search(pattern_regex, content):
                # Add thought to structural pattern
                if pattern_name not in self.common_patterns:
                    self.common_patterns[pattern_name] = []
                
                if thought.id not in self.common_patterns[pattern_name]:
                    self.common_patterns[pattern_name].append(thought.id)
                    
                    # Store structural pattern in thought metadata
                    if "patterns" not in thought.metadata:
                        thought.metadata["patterns"] = {}
                    
                    if pattern_name not in thought.metadata["patterns"]:
                        thought.metadata["patterns"][pattern_name] = True
        
        # 4. Analyze meta-patterns (combinations of patterns)
        
        # Problem-solution pair
        if (thought.id in self.common_patterns.get("problem_statement", []) and
            thought.id in self.common_patterns.get("solution_proposal", [])):
            meta_pattern = "meta:problem_solution_pair"
            
            if meta_pattern not in self.common_patterns:
                self.common_patterns[meta_pattern] = []
            
            if thought.id not in self.common_patterns[meta_pattern]:
                self.common_patterns[meta_pattern].append(thought.id)
                
                # Store meta-pattern in thought metadata
                if "patterns" not in thought.metadata:
                    thought.metadata["patterns"] = {}
                
                thought.metadata["patterns"][meta_pattern] = True
        
        # Question-reasoning pair
        if (any(thought.id in self.common_patterns.get(p, []) for p in
               ["why_reasoning_question", "what_definition_question", "how_procedural_question"]) and
            thought.id in self.common_patterns.get("causal_reasoning", [])):
            meta_pattern = "meta:question_reasoning_pair"
            
            if meta_pattern not in self.common_patterns:
                self.common_patterns[meta_pattern] = []
            
            if thought.id not in self.common_patterns[meta_pattern]:
                self.common_patterns[meta_pattern].append(thought.id)
                
                # Store meta-pattern in thought metadata
                if "patterns" not in thought.metadata:
                    thought.metadata["patterns"] = {}
                
                thought.metadata["patterns"][meta_pattern] = True