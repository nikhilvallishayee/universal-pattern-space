"""
Knowledge Integrator Implementation for GodelOS

This module implements the KnowledgeIntegrator class, which is responsible for
integrating knowledge items into appropriate memory systems, consolidating memories,
resolving conflicts, and generating inferences across memory types.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import uuid
from dataclasses import dataclass

from godelOS.unified_agent_core.knowledge_store.interfaces import (
    Knowledge, Fact, Belief, Concept, Rule, Experience, Hypothesis,
    MemoryType, KnowledgeType, KnowledgeIntegratorInterface,
    SemanticMemoryInterface, EpisodicMemoryInterface, WorkingMemoryInterface,
    Query, QueryResult
)

logger = logging.getLogger(__name__)


class KnowledgeIntegrator(KnowledgeIntegratorInterface):
    """
    KnowledgeIntegrator implementation for GodelOS.
    
    The KnowledgeIntegrator is responsible for:
    - Integrating knowledge items into appropriate memory systems
    - Consolidating memories across memory types
    - Resolving conflicts between contradictory knowledge
    - Generating inferences across memory types
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the knowledge integrator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Memory interfaces
        self.semantic_memory: Optional[SemanticMemoryInterface] = None
        self.episodic_memory: Optional[EpisodicMemoryInterface] = None
        self.working_memory: Optional[WorkingMemoryInterface] = None
        
        # Conflict resolution strategies
        self.conflict_resolution_strategies: Dict[str, Any] = {
            "recency": self._resolve_by_recency,
            "confidence": self._resolve_by_confidence,
            "evidence": self._resolve_by_evidence,
            "consensus": self._resolve_by_consensus
        }
        
        # Inference generators
        self.inference_generators: List[Any] = [
            self._generate_transitive_inferences,
            self._generate_similarity_inferences,
            self._generate_episodic_patterns,
            self._generate_concept_generalizations
        ]
        
        # Memory consolidation parameters
        self.consolidation_threshold = self.config.get("consolidation_threshold", 0.7)
        self.min_access_count = self.config.get("min_access_count", 3)
        
        # Thread safety
        self.lock = asyncio.Lock()
        
        # Knowledge type mapping to memory types
        self.knowledge_type_mapping: Dict[KnowledgeType, MemoryType] = {
            KnowledgeType.FACT: MemoryType.SEMANTIC,
            KnowledgeType.BELIEF: MemoryType.SEMANTIC,
            KnowledgeType.CONCEPT: MemoryType.SEMANTIC,
            KnowledgeType.RULE: MemoryType.SEMANTIC,
            KnowledgeType.EXPERIENCE: MemoryType.EPISODIC,
            KnowledgeType.HYPOTHESIS: MemoryType.WORKING,
            KnowledgeType.PROCEDURE: MemoryType.SEMANTIC
        }
    
    def set_memories(
        self,
        semantic_memory: SemanticMemoryInterface,
        episodic_memory: EpisodicMemoryInterface,
        working_memory: WorkingMemoryInterface
    ) -> None:
        """
        Set the memory interfaces.
        
        Args:
            semantic_memory: The semantic memory interface
            episodic_memory: The episodic memory interface
            working_memory: The working memory interface
        """
        self.semantic_memory = semantic_memory
        self.episodic_memory = episodic_memory
        self.working_memory = working_memory
    
    async def integrate_knowledge(self, item: Knowledge, memory_type: Optional[MemoryType] = None) -> bool:
        """
        Integrate a knowledge item into the appropriate memory.
        
        Args:
            item: The knowledge item to integrate
            memory_type: Optional target memory type override
            
        Returns:
            True if the item was integrated successfully, False otherwise
        """
        async with self.lock:
            # Handle both Knowledge objects and dictionaries for logging
            if isinstance(item, dict):
                item_id = item.get('id', 'unknown')
                item_type_str = item.get('type', 'unknown')
            else:
                item_id = getattr(item, 'id', 'unknown')
                item_type = getattr(item, 'type', None)
                item_type_str = item_type.value if item_type else 'unknown'
            
            logger.info(f"🔍 DEBUG: Integrating knowledge item {item_id} of type {item_type_str}")
            
            if not all([self.semantic_memory, self.episodic_memory, self.working_memory]):
                logger.error("Memory interfaces not properly set up")
                return False
            
            try:
                # Determine target memory if not specified
                if memory_type is None:
                    memory_type = self._determine_target_memory(item)
                
                # Get item id for logging
                if isinstance(item, dict):
                    item_id = item.get('id', 'unknown')
                else:
                    item_id = getattr(item, 'id', 'unknown')
                
                logger.debug(f"Target memory for item {item_id}: {memory_type.value}")
                
                # Check for conflicts before integration
                logger.info(f"🔍 DEBUG: Checking for conflicts for item {item_id}")
                conflict_start = time.perf_counter()
                conflicts = await self._check_for_conflicts(item, memory_type)
                conflict_dur = time.perf_counter() - conflict_start
                logger.info(f"🔍 DEBUG: Found {len(conflicts)} conflicts for item {item_id} (checked in {conflict_dur:.3f}s)")
                
                if conflicts:
                    # Resolve conflicts
                    resolution_result = await self._resolve_conflicts_for_item(item, conflicts)
                    
                    if not resolution_result["success"]:
                        # Get item id for logging
                        if isinstance(item, dict):
                            item_id = item.get('id', 'unknown')
                        else:
                            item_id = getattr(item, 'id', 'unknown')
                        
                        logger.warning(f"Failed to resolve conflicts for item {item_id}: {resolution_result['reason']}")
                        return False
                    
                    # Update item with resolved data if needed
                    if "updated_item" in resolution_result:
                        item = resolution_result["updated_item"]
                
                # Store in appropriate memory
                logger.info(f"🔍 DEBUG: Storing item {item_id} in memory {memory_type.value}")
                store_start = time.perf_counter()
                success = await self._store_in_memory(item, memory_type)
                store_dur = time.perf_counter() - store_start
                logger.info(f"🔍 DEBUG: Stored item {item_id} in memory (took {store_dur:.3f}s), success: {success}")
                
                if success:
                    # Also store in working memory for immediate access if not already there
                    if memory_type != MemoryType.WORKING:
                        # Set a shorter TTL for working memory copy
                        if isinstance(item, dict):
                            if "metadata" not in item:
                                item["metadata"] = {}
                            item["metadata"]["ttl"] = self.config.get("working_memory_ttl", 3600)
                        else:
                            if not hasattr(item, 'metadata'):
                                item.metadata = {}
                            item.metadata["ttl"] = self.config.get("working_memory_ttl", 3600)
                        logger.info(f"🔍 DEBUG: Storing item {item_id} in working memory")
                        wm_start = time.perf_counter()
                        await self.working_memory.store(item)
                        wm_dur = time.perf_counter() - wm_start
                        logger.info(f"🔍 DEBUG: Stored item {item_id} in working memory in {wm_dur:.3f}s")
                    
                    # Generate and store inferences
                    logger.info(f"🔍 DEBUG: Generating inferences for item {item_id}")
                    gen_start = time.perf_counter()
                    await self._generate_and_store_inferences(item, memory_type)
                    gen_dur = time.perf_counter() - gen_start
                    logger.info(f"🔍 DEBUG: Generated inferences for item {item_id} in {gen_dur:.3f}s")
                
                logger.info(f"🔍 DEBUG: Finished integrating item {item_id}, success: {success}")
                return success
            except Exception as e:
                # Get item id for logging
                if isinstance(item, dict):
                    item_id = item.get('id', 'unknown')
                else:
                    item_id = getattr(item, 'id', 'unknown')
                    
                logger.error(f"Error integrating knowledge item {item_id}: {e}")
                return False
    
    async def consolidate_memories(self) -> Dict[str, int]:
        """
        Consolidate memories (e.g., from working to long-term).
        
        Returns:
            Dictionary mapping memory types to number of items consolidated
        """
        async with self.lock:
            logger.debug("Consolidating memories")
            
            if not all([self.semantic_memory, self.episodic_memory, self.working_memory]):
                logger.error("Memory interfaces not properly set up")
                return {"error": "Memory interfaces not properly set up"}
            
            consolidation_results = {
                MemoryType.SEMANTIC.value: 0,
                MemoryType.EPISODIC.value: 0
            }
            
            try:
                # Get high-priority items from working memory
                high_priority_items = await self.working_memory.get_high_priority_items(max_count=100)
                
                for item in high_priority_items:
                    # Check if item meets consolidation criteria
                    if self._should_consolidate(item):
                        # Determine target memory
                        target_memory = self._determine_target_memory(item)
                        
                        if target_memory == MemoryType.SEMANTIC:
                            # Prepare item for semantic memory
                            semantic_item = await self._prepare_for_semantic_memory(item)
                            
                            # Consolidate to semantic memory
                            success = await self.semantic_memory.store(semantic_item)
                            if success:
                                consolidation_results[MemoryType.SEMANTIC.value] += 1
                                
                                # Update working memory version with reference to semantic memory
                                item.metadata["consolidated_to"] = "semantic"
                                item.metadata["consolidated_id"] = semantic_item.id
                                await self.working_memory.update(item.id, {"metadata": item.metadata})
                        
                        elif target_memory == MemoryType.EPISODIC:
                            # Prepare item for episodic memory if it's not already an Experience
                            if not isinstance(item, Experience):
                                episodic_item = await self._prepare_for_episodic_memory(item)
                            else:
                                episodic_item = item
                            
                            # Consolidate to episodic memory
                            success = await self.episodic_memory.store(episodic_item)
                            if success:
                                consolidation_results[MemoryType.EPISODIC.value] += 1
                                
                                # Update working memory version with reference to episodic memory
                                item.metadata["consolidated_to"] = "episodic"
                                item.metadata["consolidated_id"] = episodic_item.id
                                await self.working_memory.update(item.id, {"metadata": item.metadata})
                
                # Clear expired items from working memory
                cleared_count = await self.working_memory.clear_expired_items()
                logger.debug(f"Cleared {cleared_count} expired items from working memory")
                
                # Apply memory decay to episodic memory
                if hasattr(self.episodic_memory, "apply_memory_decay"):
                    decayed_count = await self.episodic_memory.apply_memory_decay()
                    logger.debug(f"Applied decay to {decayed_count} items in episodic memory")
                
                # Apply priority decay to working memory
                if hasattr(self.working_memory, "apply_priority_decay"):
                    await self.working_memory.apply_priority_decay()
                    logger.debug("Applied priority decay to working memory items")
                
                return consolidation_results
            except Exception as e:
                logger.error(f"Error consolidating memories: {e}")
                return {"error": str(e)}
    
    async def resolve_conflicts(self) -> Dict[str, int]:
        """
        Resolve conflicts in knowledge.
        
        Returns:
            Dictionary mapping conflict types to number of conflicts resolved
        """
        async with self.lock:
            logger.debug("Resolving knowledge conflicts")
            
            conflict_types = {
                "contradictions": 0,
                "duplicates": 0,
                "overlaps": 0
            }
            
            try:
                # Find and resolve contradictions in semantic memory
                contradictions = await self._find_contradictions()
                for contradiction in contradictions:
                    resolution = await self._resolve_contradiction(contradiction)
                    if resolution["success"]:
                        conflict_types["contradictions"] += 1
                
                # Find and resolve duplicates across memories
                duplicates = await self._find_duplicates()
                for duplicate_set in duplicates:
                    resolution = await self._resolve_duplicates(duplicate_set)
                    if resolution["success"]:
                        conflict_types["duplicates"] += 1
                
                # Find and resolve overlapping knowledge
                overlaps = await self._find_overlaps()
                for overlap in overlaps:
                    resolution = await self._resolve_overlap(overlap)
                    if resolution["success"]:
                        conflict_types["overlaps"] += 1
                
                return conflict_types
            except Exception as e:
                logger.error(f"Error resolving conflicts: {e}")
                return {"error": str(e)}
    
    async def generate_inferences(self) -> List[Knowledge]:
        """
        Generate inferences from existing knowledge.
        
        Returns:
            List of inferred knowledge items
        """
        async with self.lock:
            logger.debug("Generating inferences")
            
            inferences = []
            
            try:
                # Apply each inference generator
                for generator in self.inference_generators:
                    new_inferences = await generator()
                    inferences.extend(new_inferences)
                
                # Store inferences in working memory
                for inference in inferences:
                    # Set metadata for inferences
                    inference.metadata["source"] = "inference"
                    inference.metadata["generated_at"] = time.time()
                    inference.confidence = min(0.8, inference.confidence)  # Cap confidence for inferences
                    
                    await self.working_memory.store(inference)
                
                logger.debug(f"Generated {len(inferences)} inferences")
                return inferences
            except Exception as e:
                logger.error(f"Error generating inferences: {e}")
# Helper methods for memory preparation
    
    async def _prepare_for_semantic_memory(self, item: Knowledge) -> Knowledge:
        """
        Prepare an item for storage in semantic memory.
        
        Args:
            item: The knowledge item
            
        Returns:
            The prepared knowledge item
        """
        # Create a copy of the item
        semantic_item = item
        
        # Add reference to original item
        semantic_item.metadata["original_id"] = item.id
        semantic_item.metadata["consolidated_from"] = "working"
        
        # Remove temporary metadata
        if "ttl" in semantic_item.metadata:
            del semantic_item.metadata["ttl"]
        
        # Generate a new ID to avoid conflicts
        semantic_item.id = str(uuid.uuid4())
        
        return semantic_item
    
    async def _prepare_for_episodic_memory(self, item: Knowledge) -> Experience:
        """
        Prepare an item for storage in episodic memory.
        
        Args:
            item: The knowledge item
            
        Returns:
            An Experience object
        """
        # Create an Experience from the item
        experience = Experience(
            id=str(uuid.uuid4()),
            content=item.content if hasattr(item, "content") else {},
            confidence=item.confidence,
            timestamp=item.created_at,
            duration=0.0,  # Default duration
            context={
                "source_type": item.type.value,
                "source_id": item.id
            }
        )
        
        # Add any context from the original item
        if "context" in item.metadata:
            experience.context.update(item.metadata["context"])
        
        return experience
    
    # Helper methods for conflict resolution
    
    async def _find_contradictions(self) -> List[Dict[str, Any]]:
        """
        Find contradictions in knowledge.
        
        Returns:
            List of contradictions
        """
        contradictions = []
        
        if not self.semantic_memory:
            return contradictions
        
        # Query facts and beliefs from semantic memory
        query = {
            "content": {},
            "knowledge_types": [KnowledgeType.FACT, KnowledgeType.BELIEF],
            "max_results": 1000
        }
        
        result = await self.semantic_memory.query(self._create_query_from_dict(query))
        items = result.items
        
        # Check all pairs of items for contradictions
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if await self._is_conflicting(items[i], items[j]):
                    contradictions.append({
                        "items": [items[i], items[j]],
                        "conflict_type": "contradiction"
                    })
        
        return contradictions
    
    async def _resolve_contradiction(self, contradiction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve a contradiction.
        
        Args:
            contradiction: The contradiction to resolve
            
        Returns:
            Dictionary with resolution results
        """
        items = contradiction["items"]
        
        # Use confidence-based resolution
        result = await self._resolve_by_confidence(items[0], [{"item": items[1], "conflict_type": "contradiction"}])
        
        if result["success"]:
            # Keep the higher confidence item
            return {"success": True}
        else:
            # The second item has higher confidence
            return {"success": True, "kept_item": items[1].id}
    
    async def _find_duplicates(self) -> List[Set[Knowledge]]:
        """
        Find duplicate knowledge items.
        
        Returns:
            List of sets of duplicate items
        """
        duplicate_sets = []
        
        if not all([self.semantic_memory, self.episodic_memory, self.working_memory]):
            return duplicate_sets
        
        # Find duplicates in semantic memory
        semantic_query = {
            "content": {},
            "max_results": 1000
        }
        semantic_items = (await self.semantic_memory.query(self._create_query_from_dict(semantic_query))).items
        
        # Find duplicates in working memory
        working_query = {
            "content": {},
            "max_results": 1000
        }
        working_items = (await self.working_memory.query(self._create_query_from_dict(working_query))).items
        
        # Group items by content similarity
        content_groups = {}
        
        # Process semantic items
        for item in semantic_items:
            if not hasattr(item, "content") or not item.content:
                continue
                
            content_hash = self._get_content_hash(item)
            if content_hash not in content_groups:
                content_groups[content_hash] = set()
            content_groups[content_hash].add(item)
        
        # Process working items
        for item in working_items:
            if not hasattr(item, "content") or not item.content:
                continue
                
            content_hash = self._get_content_hash(item)
            if content_hash not in content_groups:
                content_groups[content_hash] = set()
            content_groups[content_hash].add(item)
        
        # Find groups with multiple items
        for group in content_groups.values():
            if len(group) > 1:
                duplicate_sets.append(group)
        
        return duplicate_sets
    
    def _get_content_hash(self, item: Knowledge) -> str:
        """
        Get a hash of item content for duplicate detection.
        
        Args:
            item: The knowledge item
            
        Returns:
            A string hash of the content
        """
        if not hasattr(item, "content") or not item.content:
            return ""
        
        # For facts and beliefs, hash subject and predicate
        if item.type in [KnowledgeType.FACT, KnowledgeType.BELIEF]:
            subject = str(item.content.get("subject", ""))
            predicate = str(item.content.get("predicate", ""))
            return f"{subject}:{predicate}"
        
        # For concepts, hash name
        elif item.type == KnowledgeType.CONCEPT:
            name = str(item.content.get("name", ""))
            return f"concept:{name}"
        
        # For experiences, hash context
        elif item.type == KnowledgeType.EXPERIENCE and hasattr(item, "context"):
            location = str(item.context.get("location", ""))
            agent = str(item.context.get("agent_id", ""))
            return f"experience:{location}:{agent}"
        
        # Default to string representation of content
        return str(item.content)
    
    async def _resolve_duplicates(self, duplicate_set: Set[Knowledge]) -> Dict[str, Any]:
        """
        Resolve duplicates.
        
        Args:
            duplicate_set: Set of duplicate items
            
        Returns:
            Dictionary with resolution results
        """
        if not duplicate_set:
            return {"success": False, "reason": "Empty duplicate set"}
        
        # Find the item with highest confidence
        best_item = max(duplicate_set, key=lambda x: x.confidence)
        
        # Keep only the best item
        for item in duplicate_set:
            if item.id != best_item.id:
                # If in working memory, delete it
                if hasattr(item, "metadata") and item.metadata.get("memory_type") == "working":
                    await self.working_memory.delete(item.id)
        
        return {"success": True, "kept_item": best_item.id}
    
    async def _find_overlaps(self) -> List[Dict[str, Any]]:
        """
        Find overlapping knowledge.
        
        Returns:
            List of overlaps
        """
        overlaps = []
        
        # This is a more complex analysis that would involve semantic understanding
        # For this implementation, we'll return an empty list as a placeholder
        
        return overlaps
    
    async def _resolve_overlap(self, overlap: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve an overlap.
        
        Args:
            overlap: The overlap to resolve
            
        Returns:
            Dictionary with resolution results
        """
        # This is a placeholder implementation
        return {"success": False, "reason": "Not implemented"}
    
    # Helper methods for inference generation
    
    async def _generate_transitive_inferences(self) -> List[Knowledge]:
        """
        Generate transitive inferences.
        
        Returns:
            List of inferred knowledge items
        """
        inferences = []
        
        if not self.semantic_memory:
            return inferences
        
        # Query concepts from semantic memory
        query = {
            "content": {},
            "knowledge_types": [KnowledgeType.CONCEPT],
            "max_results": 100
        }
        
        concepts = (await self.semantic_memory.query(self._create_query_from_dict(query))).items
        
        # Find transitive relationships (A related to B, B related to C => A related to C)
        for concept_a in concepts:
            if not isinstance(concept_a, Concept):
                continue
                
            # Get related concepts
            related_to_a = await self.semantic_memory.get_related_concepts(concept_a.id)
            
            for concept_b in related_to_a:
                # Get concepts related to B
                related_to_b = await self.semantic_memory.get_related_concepts(concept_b.id)
                
                for concept_c in related_to_b:
                    # Check if C is not already directly related to A
                    if concept_c.id != concept_a.id and concept_c.id not in concept_a.related_concepts:
                        # Create a new concept with the transitive relationship
                        new_concept = Concept(
                            id=str(uuid.uuid4()),
                            content=concept_a.content.copy(),
                            confidence=min(0.7, concept_a.confidence * 0.8),  # Lower confidence for inferences
                            metadata={"source": "transitive_inference"}
                        )
                        
                        # Add the new relationship
                        new_concept.related_concepts = concept_a.related_concepts.copy()
                        new_concept.related_concepts.append(concept_c.id)
                        
                        inferences.append(new_concept)
        
        return inferences
    
    async def _generate_similarity_inferences(self) -> List[Knowledge]:
        """
        Generate similarity-based inferences.
        
        Returns:
            List of inferred knowledge items
        """
        # This is a placeholder implementation
        return []
    
    async def _generate_episodic_patterns(self) -> List[Knowledge]:
        """
        Generate inferences based on episodic patterns.
        
        Returns:
            List of inferred knowledge items
        """
        inferences = []
        
        if not self.episodic_memory or not hasattr(self.episodic_memory, "detect_patterns"):
            return inferences
        
        # Detect patterns in episodic memory
        patterns = await self.episodic_memory.detect_patterns(min_occurrences=3)
        
        for pattern in patterns:
            if pattern["type"] == "temporal_pattern":
                # Create a rule from the temporal pattern
                rule = Rule(
                    id=str(uuid.uuid4()),
                    content={"pattern_type": "temporal", "pattern_data": pattern},
                    confidence=0.7,
                    metadata={"source": "episodic_pattern"}
                )
                
                # Add conditions and actions based on pattern type
                if pattern["subtype"] == "daily":
                    day_of_week = pattern["day_of_week"]
                    rule.conditions = [{"day_of_week": day_of_week}]
                    rule.actions = [{"predict": "activity", "probability": pattern["occurrences"] / 10}]
                
                elif pattern["subtype"] == "hourly":
                    hour = pattern["hour"]
                    rule.conditions = [{"hour": hour}]
                    rule.actions = [{"predict": "activity", "probability": pattern["occurrences"] / 10}]
                
                inferences.append(rule)
        
        return inferences
    
    async def _generate_concept_generalizations(self) -> List[Knowledge]:
        """
        Generate concept generalizations.
        
        Returns:
            List of inferred knowledge items
        """
        # This is a placeholder implementation
        return []
    
    async def _generate_fact_inferences(self, fact: Knowledge) -> List[Knowledge]:
        """
        Generate inferences from a fact.
        
        Args:
            fact: The fact to generate inferences from
            
        Returns:
            List of inferred knowledge items
        """
        inferences = []
        
        if not isinstance(fact, Fact) or not hasattr(fact, "content"):
            return inferences
        
        # Create a belief from the fact
        if "subject" in fact.content and "predicate" in fact.content:
            belief = Belief(
                id=str(uuid.uuid4()),
                content=fact.content.copy(),
                confidence=min(0.9, fact.confidence),
                evidence=[fact.id],
                metadata={"source": "fact_inference", "source_id": fact.id}
            )
            
            inferences.append(belief)
        
        return inferences
    
    async def _generate_concept_inferences(self, concept: Knowledge) -> List[Knowledge]:
        """
        Generate inferences from a concept.
        
        Args:
            concept: The concept to generate inferences from
            
        Returns:
            List of inferred knowledge items
        """
        # This is a placeholder implementation
        return []
    
    async def _generate_rule_inferences(self, rule: Knowledge) -> List[Knowledge]:
        """
        Generate inferences from a rule.
        
        Args:
            rule: The rule to generate inferences from
            
        Returns:
            List of inferred knowledge items
        """
        # This is a placeholder implementation
        return []
    
    # Missing conflict resolution methods
    
    async def _resolve_by_recency(self, item: Knowledge, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts by choosing the most recent item.
        
        Args:
            item: The knowledge item
            conflicts: List of conflicting items
            
        Returns:
            Dictionary with resolution results
        """
        most_recent = item
        most_recent_time = item.created_at
        
        for conflict in conflicts:
            conflict_item = conflict["item"]
            if conflict_item.created_at > most_recent_time:
                most_recent = conflict_item
                most_recent_time = conflict_item.created_at
        
        if most_recent.id == item.id:
            return {"success": True, "resolution": "keep_original"}
        else:
            return {"success": False, "resolution": "keep_conflict", "preferred_item": most_recent}
    
    async def _resolve_by_confidence(self, item: Knowledge, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts by choosing the item with highest confidence.
        
        Args:
            item: The knowledge item
            conflicts: List of conflicting items
            
        Returns:
            Dictionary with resolution results
        """
        highest_confidence = item
        max_confidence = item.confidence
        
        for conflict in conflicts:
            conflict_item = conflict["item"]
            if conflict_item.confidence > max_confidence:
                highest_confidence = conflict_item
                max_confidence = conflict_item.confidence
        
        if highest_confidence.id == item.id:
            return {"success": True, "resolution": "keep_original"}
        else:
            return {"success": False, "resolution": "keep_conflict", "preferred_item": highest_confidence}
    
    async def _resolve_by_evidence(self, item: Knowledge, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts by choosing the item with most evidence.
        
        Args:
            item: The knowledge item
            conflicts: List of conflicting items
            
        Returns:
            Dictionary with resolution results
        """
        best_item = item
        max_evidence = len(getattr(item, 'evidence', []))
        
        for conflict in conflicts:
            conflict_item = conflict["item"]
            evidence_count = len(getattr(conflict_item, 'evidence', []))
            if evidence_count > max_evidence:
                best_item = conflict_item
                max_evidence = evidence_count
        
        if best_item.id == item.id:
            return {"success": True, "resolution": "keep_original"}
        else:
            return {"success": False, "resolution": "keep_conflict", "preferred_item": best_item}
    
    async def _resolve_by_consensus(self, item: Knowledge, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts by consensus (placeholder implementation).
        
        Args:
            item: The knowledge item
            conflicts: List of conflicting items
            
        Returns:
            Dictionary with resolution results
        """
        # For now, fall back to confidence-based resolution
        return await self._resolve_by_confidence(item, conflicts)
    
    # Helper methods for conflict detection and resolution
    
    def _determine_target_memory(self, item: Union[Knowledge, Dict[str, Any]]) -> MemoryType:
        """
        Determine the target memory type for a knowledge item.
        Handles both dict and object, robust to enum scoping issues.
        """
        from godelOS.unified_agent_core.knowledge_store.interfaces import KnowledgeType, MemoryType
        item_type = None
        if isinstance(item, dict):
            raw_type = item.get('type', 'fact')
            # Try to convert string to KnowledgeType enum
            if isinstance(raw_type, str):
                # Try direct name match
                try:
                    item_type = KnowledgeType[raw_type.upper()]
                except KeyError:
                    try:
                        item_type = KnowledgeType(raw_type)
                    except Exception:
                        item_type = KnowledgeType.FACT
            elif isinstance(raw_type, KnowledgeType):
                item_type = raw_type
            else:
                item_type = KnowledgeType.FACT
        else:
            # Object: try to get .type attribute
            try:
                item_type = getattr(item, 'type', KnowledgeType.FACT)
                if isinstance(item_type, str):
                    try:
                        item_type = KnowledgeType[item_type.upper()]
                    except KeyError:
                        try:
                            item_type = KnowledgeType(item_type)
                        except Exception:
                            item_type = KnowledgeType.FACT
            except Exception:
                item_type = KnowledgeType.FACT
        return self.knowledge_type_mapping.get(item_type, MemoryType.WORKING)
    
    async def _check_for_conflicts(self, item: Knowledge, memory_type: MemoryType) -> List[Dict[str, Any]]:
        """
        Check for conflicts before integration.
        
        Args:
            item: The knowledge item
            memory_type: The target memory type
            
        Returns:
            List of conflicts found
        """
        conflicts = []
        
        # Simple conflict detection based on content similarity
        if memory_type == MemoryType.SEMANTIC and self.semantic_memory:
            # Query for similar items
            # Handle both Knowledge objects and dictionaries
            from godelOS.unified_agent_core.knowledge_store.interfaces import KnowledgeType
            if isinstance(item, dict):
                item_content = item.get('content', {})
                raw_type = item.get('type', 'fact')
                # Robust conversion to KnowledgeType
                if isinstance(raw_type, str):
                    try:
                        item_type = KnowledgeType[raw_type.upper()]
                    except KeyError:
                        try:
                            item_type = KnowledgeType(raw_type)
                        except Exception:
                            item_type = KnowledgeType.FACT
                elif isinstance(raw_type, KnowledgeType):
                    item_type = raw_type
                else:
                    item_type = KnowledgeType.FACT
            else:
                item_content = getattr(item, 'content', {})
                raw_type = getattr(item, 'type', KnowledgeType.FACT)
                if isinstance(raw_type, str):
                    try:
                        item_type = KnowledgeType[raw_type.upper()]
                    except KeyError:
                        try:
                            item_type = KnowledgeType(raw_type)
                        except Exception:
                            item_type = KnowledgeType.FACT
                elif isinstance(raw_type, KnowledgeType):
                    item_type = raw_type
                else:
                    item_type = KnowledgeType.FACT
            query = {
                "content": item_content,
                "knowledge_types": [item_type],
                "max_results": 10
            }
            
            result = await self.semantic_memory.query(self._create_query_from_dict(query))
            for existing_item in result.items:
                if await self._is_conflicting(item, existing_item):
                    conflicts.append({
                        "item": existing_item,
                        "conflict_type": "content_conflict"
                    })
        
        return conflicts
    
    async def _is_conflicting(self, item1: Knowledge, item2: Knowledge) -> bool:
        """
        Check if two knowledge items are conflicting.
        
        Args:
            item1: First knowledge item
            item2: Second knowledge item
            
        Returns:
            True if the items are conflicting
        """
        # Simple conflict detection based on content
        if not hasattr(item1, 'content') or not hasattr(item2, 'content'):
            return False
        
        if not item1.content or not item2.content:
            return False
        
        # For facts and beliefs, check if they contradict
        if item1.type in [KnowledgeType.FACT, KnowledgeType.BELIEF] and item2.type in [KnowledgeType.FACT, KnowledgeType.BELIEF]:
            # Check if they have the same subject but different predicates that contradict
            if (item1.content.get("subject") == item2.content.get("subject") and
                item1.content.get("predicate") != item2.content.get("predicate")):
                # Simple contradiction detection (this could be more sophisticated)
                pred1 = str(item1.content.get("predicate", "")).lower()
                pred2 = str(item2.content.get("predicate", "")).lower()
                
                contradictory_pairs = [
                    ("is", "is not"),
                    ("exists", "does not exist"),
                    ("true", "false"),
                    ("yes", "no")
                ]
                
                for pair in contradictory_pairs:
                    if (pred1 in pair[0] and pred2 in pair[1]) or (pred1 in pair[1] and pred2 in pair[0]):
                        return True
        
        return False
    
    async def _resolve_conflicts_for_item(self, item: Knowledge, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts for a specific item.
        
        Args:
            item: The knowledge item
            conflicts: List of conflicts
            
        Returns:
            Dictionary with resolution results
        """
        if not conflicts:
            return {"success": True}
        
        # Use the default resolution strategy (confidence)
        strategy = self.conflict_resolution_strategies.get("confidence")
        if strategy:
            return await strategy(item, conflicts)
        else:
            return {"success": False, "reason": "No resolution strategy available"}
    
    async def _store_in_memory(self, item: Knowledge, memory_type: MemoryType) -> bool:
        """
        Store an item in the appropriate memory.
        
        Args:
            item: The knowledge item
            memory_type: The target memory type
            
        Returns:
            True if storage was successful
        """
        try:
            if memory_type == MemoryType.SEMANTIC and self.semantic_memory:
                return await self.semantic_memory.store(item)
            elif memory_type == MemoryType.EPISODIC and self.episodic_memory:
                return await self.episodic_memory.store(item)
            elif memory_type == MemoryType.WORKING and self.working_memory:
                return await self.working_memory.store(item)
            else:
                logger.error(f"Unknown memory type or memory not available: {memory_type}")
                return False
        except Exception as e:
            logger.error(f"Error storing item {item.id} in {memory_type.value}: {e}")
            return False
    
    async def _generate_and_store_inferences(self, item: Knowledge, memory_type: MemoryType) -> None:
        """
        Generate and store inferences for an item.
        
        Args:
            item: The knowledge item
            memory_type: The memory type where the item was stored
        """
        try:
            inferences = []
            
            # Generate specific inferences based on item type
            if item.type == KnowledgeType.FACT:
                inferences.extend(await self._generate_fact_inferences(item))
            elif item.type == KnowledgeType.CONCEPT:
                inferences.extend(await self._generate_concept_inferences(item))
            elif item.type == KnowledgeType.RULE:
                inferences.extend(await self._generate_rule_inferences(item))
            
            # Store inferences in working memory
            for inference in inferences:
                if self.working_memory:
                    await self.working_memory.store(inference)
            
            if inferences:
                logger.debug(f"Generated and stored {len(inferences)} inferences for item {item.id}")
        except Exception as e:
            logger.error(f"Error generating inferences for item {item.id}: {e}")
    
    def _should_consolidate(self, item: Knowledge) -> bool:
        """
        Check if an item should be consolidated to long-term memory.
        
        Args:
            item: The knowledge item
            
        Returns:
            True if the item should be consolidated
        """
        # Check access count
        access_count = item.metadata.get("access_count", 0)
        if access_count < self.min_access_count:
            return False
        
        # Check time since creation
        time_since_creation = time.time() - item.created_at
        min_age = self.config.get("min_consolidation_age", 3600)  # 1 hour default
        if time_since_creation < min_age:
            return False
        
        # Check confidence
        if item.confidence < self.consolidation_threshold:
            return False
        
        return True
    
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
            for type_item in data["knowledge_types"]:
                knowledge_types.append(type_item)
        
        return Query(
            id=query_id,
            content=content,
            memory_types=memory_types,
            knowledge_types=knowledge_types,
            max_results=max_results,
            metadata=metadata
        )