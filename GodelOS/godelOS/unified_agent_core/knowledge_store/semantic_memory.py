"""
Semantic Memory Store Implementation for GodelOS

This module implements a specialized semantic memory store that handles facts,
beliefs, concepts, and rules with semantic network connections and methods for
concept similarity and relation traversal.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Union, Set, Tuple
import uuid
from dataclasses import dataclass, field
import numpy as np
from collections import defaultdict

from godelOS.unified_agent_core.knowledge_store.interfaces import (
    Knowledge, Fact, Belief, Concept, Rule, 
    KnowledgeType, Query, QueryResult,
    SemanticMemoryInterface
)

logger = logging.getLogger(__name__)


class SemanticMemory(SemanticMemoryInterface):
    """
    Specialized implementation of semantic memory for GodelOS.
    
    This implementation provides:
    - Efficient storage and retrieval for facts, beliefs, concepts, and rules
    - Semantic network connections between related concepts
    - Methods for concept similarity and relation traversal
    - Support for concept hierarchies and inheritance
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize semantic memory.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Primary storage for knowledge items
        self.items: Dict[str, Union[Fact, Belief, Concept, Rule]] = {}
        
        # Semantic network connections
        self.concept_relations: Dict[str, Dict[str, float]] = {}  # concept_id -> {related_concept_id: strength}
        self.concept_hierarchies: Dict[str, List[str]] = {}  # concept_id -> parent_concept_ids
        self.concept_children: Dict[str, List[str]] = {}  # concept_id -> child_concept_ids
        
        # Indexing structures
        self.fact_beliefs: Dict[str, List[str]] = {}  # fact_id -> belief_ids
        self.concept_rules: Dict[str, List[str]] = {}  # concept_id -> rule_ids
        self.concept_facts: Dict[str, List[str]] = {}  # concept_id -> fact_ids
        self.concept_properties: Dict[str, Dict[str, Any]] = {}  # concept_id -> {property: value}
        
        # For concept similarity
        self.concept_embeddings: Dict[str, np.ndarray] = {}  # concept_id -> vector embedding
        
        # Type-specific indexes
        self.type_index: Dict[KnowledgeType, Set[str]] = {
            KnowledgeType.FACT: set(),
            KnowledgeType.BELIEF: set(),
            KnowledgeType.CONCEPT: set(),
            KnowledgeType.RULE: set(),
        }
        
        # Text search index
        self.text_index: Dict[str, Set[str]] = defaultdict(set)  # term -> item_ids
        
        # Thread safety
        self.lock = asyncio.Lock()
        
        # Performance optimization
        self.cache_size = self.config.get("cache_size", 1000)
        self.recently_accessed: List[str] = []  # LRU cache of item_ids
    
    async def store(self, item: Union[Fact, Belief, Concept, Rule]) -> bool:
        """
        Store an item in semantic memory.
        
        Args:
            item: The item to store
            
        Returns:
            True if the item was stored successfully, False otherwise
        """
        async with self.lock:
            try:
                # Store the item
                self.items[item.id] = item
                
                # Update type index
                if item.type in self.type_index:
                    self.type_index[item.type].add(item.id)
                
                # Update text index
                self._index_text(item)
                
                # Process based on item type
                if isinstance(item, Concept):
                    await self._process_concept(item)
                elif isinstance(item, Fact):
                    await self._process_fact(item)
                elif isinstance(item, Belief):
                    await self._process_belief(item)
                elif isinstance(item, Rule):
                    await self._process_rule(item)
                
                # Update LRU cache
                self._update_recently_accessed(item.id)
                
                logger.debug(f"Stored {item.type.value} with ID {item.id} in semantic memory")
                return True
            except Exception as e:
                logger.error(f"Error storing item in semantic memory: {e}")
                return False
    
    async def retrieve(self, item_id: str) -> Optional[Union[Fact, Belief, Concept, Rule]]:
        """
        Retrieve an item from semantic memory.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item, or None if not found
        """
        async with self.lock:
            item = self.items.get(item_id)
            
            if item:
                # Update last accessed time
                item.last_accessed = time.time()
                
                # Update LRU cache
                self._update_recently_accessed(item_id)
            
            return item
    
    async def query(self, query: Query) -> QueryResult:
        """
        Query items from semantic memory.
        
        Args:
            query: The query to execute
            
        Returns:
            The query result
        """
        async with self.lock:
            start_time = time.time()
            
            # Start with all items or filtered by knowledge types
            if query.knowledge_types:
                item_ids = set()
                for knowledge_type in query.knowledge_types:
                    if knowledge_type in self.type_index:
                        item_ids.update(self.type_index[knowledge_type])
            else:
                item_ids = set(self.items.keys())
            
            # Apply content filters
            if query.content:
                filtered_ids = await self._apply_content_filters(query.content, item_ids)
                item_ids = item_ids.intersection(filtered_ids) if filtered_ids else item_ids
            
            # Convert IDs to items
            items = [self.items[item_id] for item_id in item_ids if item_id in self.items]
            
            # Sort results (by relevance, confidence, or recency)
            sort_by = query.metadata.get("sort_by", "relevance")
            if sort_by == "confidence":
                items.sort(key=lambda x: x.confidence, reverse=True)
            elif sort_by == "recency":
                items.sort(key=lambda x: x.created_at, reverse=True)
            else:  # Default to relevance (last accessed)
                items.sort(key=lambda x: x.last_accessed, reverse=True)
            
            # Apply limit
            total_items = len(items)
            items = items[:query.max_results]
            
            # Update access time for returned items
            for item in items:
                item.last_accessed = time.time()
                self._update_recently_accessed(item.id)
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                query_id=query.id,
                items=items,
                total_items=total_items,
                execution_time=execution_time,
                metadata={"memory_type": "semantic"}
            )
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an item in semantic memory.
        
        Args:
            item_id: The ID of the item to update
            updates: Dictionary of updates to apply to the item
            
        Returns:
            True if the item was updated, False if the item was not found
        """
        async with self.lock:
            if item_id not in self.items:
                return False
            
            item = self.items[item_id]
            old_content = item.content.copy() if hasattr(item, "content") else None
            
            # Update item attributes
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            
            # If content changed, update indexes
            if hasattr(item, "content") and old_content != item.content:
                self._remove_from_text_index(item_id)
                self._index_text(item)
            
            # Update based on item type
            if isinstance(item, Concept):
                await self._update_concept_relations(item)
            
            # Update last accessed time
            item.last_accessed = time.time()
            self._update_recently_accessed(item_id)
            
            return True
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete an item from semantic memory.
        
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
            if item.type in self.type_index and item_id in self.type_index[item.type]:
                self.type_index[item.type].remove(item_id)
            
            # Remove from text index
            self._remove_from_text_index(item_id)
            
            # Remove from specific indexes based on type
            if isinstance(item, Concept):
                await self._remove_concept(item)
            elif isinstance(item, Fact):
                await self._remove_fact(item)
            elif isinstance(item, Belief):
                await self._remove_belief(item)
            elif isinstance(item, Rule):
                await self._remove_rule(item)
            
            # Remove from main storage
            del self.items[item_id]
            
            # Remove from LRU cache
            if item_id in self.recently_accessed:
                self.recently_accessed.remove(item_id)
            
            return True
    
    async def get_related_concepts(self, concept_id: str) -> List[Concept]:
        """
        Get concepts related to a concept.
        
        Args:
            concept_id: The ID of the concept
            
        Returns:
            List of related concepts
        """
        async with self.lock:
            if concept_id not in self.concept_relations:
                return []
            
            # Get related concept IDs with their relation strength
            related_ids_with_strength = self.concept_relations[concept_id].items()
            
            # Sort by relation strength (strongest first)
            sorted_related = sorted(related_ids_with_strength, key=lambda x: x[1], reverse=True)
            
            # Convert to concept objects
            related_concepts = []
            for related_id, _ in sorted_related:
                if related_id in self.items and isinstance(self.items[related_id], Concept):
                    related_concepts.append(self.items[related_id])
            
            return related_concepts
    
    async def get_beliefs_for_fact(self, fact_id: str) -> List[Belief]:
        """
        Get beliefs related to a fact.
        
        Args:
            fact_id: The ID of the fact
            
        Returns:
            List of related beliefs
        """
        async with self.lock:
            if fact_id not in self.fact_beliefs:
                return []
            
            belief_ids = self.fact_beliefs[fact_id]
            return [
                self.items[belief_id] for belief_id in belief_ids
                if belief_id in self.items and isinstance(self.items[belief_id], Belief)
            ]
    
    async def get_rules_for_concept(self, concept_id: str) -> List[Rule]:
        """
        Get rules related to a concept.
        
        Args:
            concept_id: The ID of the concept
            
        Returns:
            List of related rules
        """
        async with self.lock:
            if concept_id not in self.concept_rules:
                return []
            
            rule_ids = self.concept_rules[concept_id]
            return [
                self.items[rule_id] for rule_id in rule_ids
                if rule_id in self.items and isinstance(self.items[rule_id], Rule)
            ]
    
    # Additional specialized methods for semantic memory
    
    async def get_concept_similarity(self, concept_id1: str, concept_id2: str) -> float:
        """
        Calculate similarity between two concepts.
        
        Args:
            concept_id1: ID of the first concept
            concept_id2: ID of the second concept
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        async with self.lock:
            # Check if both concepts exist
            if concept_id1 not in self.items or concept_id2 not in self.items:
                return 0.0
            
            # Check if they're the same concept
            if concept_id1 == concept_id2:
                return 1.0
            
            # If we have embeddings, use vector similarity
            if concept_id1 in self.concept_embeddings and concept_id2 in self.concept_embeddings:
                vec1 = self.concept_embeddings[concept_id1]
                vec2 = self.concept_embeddings[concept_id2]
                return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
            
            # Otherwise use relation-based similarity
            similarity = 0.0
            
            # Check direct relations
            if concept_id1 in self.concept_relations and concept_id2 in self.concept_relations[concept_id1]:
                similarity = max(similarity, self.concept_relations[concept_id1][concept_id2])
            
            # Check common parents (shared inheritance)
            if concept_id1 in self.concept_hierarchies and concept_id2 in self.concept_hierarchies:
                parents1 = set(self.concept_hierarchies[concept_id1])
                parents2 = set(self.concept_hierarchies[concept_id2])
                common_parents = parents1.intersection(parents2)
                
                if common_parents:
                    # More common parents = higher similarity
                    similarity = max(similarity, len(common_parents) / max(len(parents1), len(parents2)))
            
            # Check property overlap
            if concept_id1 in self.concept_properties and concept_id2 in self.concept_properties:
                props1 = set(self.concept_properties[concept_id1].keys())
                props2 = set(self.concept_properties[concept_id2].keys())
                
                if props1 and props2:
                    common_props = props1.intersection(props2)
                    similarity = max(similarity, len(common_props) / max(len(props1), len(props2)))
            
            return similarity
    
    async def get_concept_hierarchy(self, concept_id: str, max_depth: int = -1) -> Dict[str, Any]:
        """
        Get the concept hierarchy (parents and children) for a concept.
        
        Args:
            concept_id: The ID of the concept
            max_depth: Maximum depth to traverse (-1 for unlimited)
            
        Returns:
            Dictionary representing the concept hierarchy
        """
        async with self.lock:
            if concept_id not in self.items:
                return {}
            
            concept = self.items[concept_id]
            
            # Build hierarchy recursively
            hierarchy = {
                "id": concept.id,
                "name": concept.content.get("name", ""),
                "parents": [],
                "children": []
            }
            
            # Add parents
            if concept_id in self.concept_hierarchies and (max_depth != 0):
                for parent_id in self.concept_hierarchies[concept_id]:
                    if parent_id in self.items:
                        if max_depth > 0:
                            parent_hierarchy = await self.get_concept_hierarchy(parent_id, max_depth - 1)
                            hierarchy["parents"].append(parent_hierarchy)
                        else:
                            parent = self.items[parent_id]
                            hierarchy["parents"].append({
                                "id": parent.id,
                                "name": parent.content.get("name", "")
                            })
            
            # Add children
            if concept_id in self.concept_children and (max_depth != 0):
                for child_id in self.concept_children[concept_id]:
                    if child_id in self.items:
                        if max_depth > 0:
                            child_hierarchy = await self.get_concept_hierarchy(child_id, max_depth - 1)
                            hierarchy["children"].append(child_hierarchy)
                        else:
                            child = self.items[child_id]
                            hierarchy["children"].append({
                                "id": child.id,
                                "name": child.content.get("name", "")
                            })
            
            return hierarchy
    
    async def find_path_between_concepts(self, start_concept_id: str, end_concept_id: str, max_depth: int = 5) -> List[str]:
        """
        Find a path between two concepts in the semantic network.
        
        Args:
            start_concept_id: The starting concept ID
            end_concept_id: The target concept ID
            max_depth: Maximum path length to search
            
        Returns:
            List of concept IDs forming a path, or empty list if no path found
        """
        async with self.lock:
            if start_concept_id not in self.items or end_concept_id not in self.items:
                return []
            
            # Breadth-first search
            visited = {start_concept_id}
            queue = [(start_concept_id, [start_concept_id])]
            
            while queue and len(queue[0][1]) <= max_depth:
                current_id, path = queue.pop(0)
                
                # Check if we've reached the target
                if current_id == end_concept_id:
                    return path
                
                # Explore neighbors
                if current_id in self.concept_relations:
                    for neighbor_id in self.concept_relations[current_id]:
                        if neighbor_id not in visited:
                            visited.add(neighbor_id)
                            queue.append((neighbor_id, path + [neighbor_id]))
            
            return []  # No path found
    
    async def get_concept_properties(self, concept_id: str, include_inherited: bool = True) -> Dict[str, Any]:
        """
        Get all properties of a concept, optionally including inherited properties.
        
        Args:
            concept_id: The ID of the concept
            include_inherited: Whether to include properties inherited from parent concepts
            
        Returns:
            Dictionary of property names to values
        """
        async with self.lock:
            if concept_id not in self.items:
                return {}
            
            # Get direct properties
            properties = {}
            if concept_id in self.concept_properties:
                properties.update(self.concept_properties[concept_id])
            
            # Include inherited properties if requested
            if include_inherited and concept_id in self.concept_hierarchies:
                for parent_id in self.concept_hierarchies[concept_id]:
                    parent_props = await self.get_concept_properties(parent_id, include_inherited)
                    
                    # Only add properties that don't already exist (child properties override parent)
                    for prop, value in parent_props.items():
                        if prop not in properties:
                            properties[prop] = value
            
            return properties
    
    # Private helper methods
    
    async def _process_concept(self, concept: Concept) -> None:
        """Process a concept when it's stored."""
        # Extract and store concept properties
        if "properties" in concept.content:
            self.concept_properties[concept.id] = concept.content["properties"]
        
        # Process related concepts
        if concept.related_concepts:
            if concept.id not in self.concept_relations:
                self.concept_relations[concept.id] = {}
            
            # Add relations with default strength
            for related_id in concept.related_concepts:
                self.concept_relations[concept.id][related_id] = 0.5  # Default strength
                
                # Add reverse relation
                if related_id not in self.concept_relations:
                    self.concept_relations[related_id] = {}
                self.concept_relations[related_id][concept.id] = 0.5  # Default strength
        
        # Process concept hierarchy
        if "parent_concepts" in concept.content:
            parent_ids = concept.content["parent_concepts"]
            self.concept_hierarchies[concept.id] = parent_ids
            
            # Update children for each parent
            for parent_id in parent_ids:
                if parent_id not in self.concept_children:
                    self.concept_children[parent_id] = []
                
                if concept.id not in self.concept_children[parent_id]:
                    self.concept_children[parent_id].append(concept.id)
        
        # Generate concept embedding if not present
        if concept.id not in self.concept_embeddings:
            # Simple placeholder - in a real system, this would use more sophisticated embedding generation
            # For example, using word embeddings or neural networks
            embedding = np.random.rand(100)  # 100-dimensional random vector
            self.concept_embeddings[concept.id] = embedding / np.linalg.norm(embedding)  # Normalize
    
    async def _process_fact(self, fact: Fact) -> None:
        """Process a fact when it's stored."""
        # Link fact to concepts it references
        if "concept_id" in fact.content:
            concept_id = fact.content["concept_id"]
            
            if concept_id not in self.concept_facts:
                self.concept_facts[concept_id] = []
            
            if fact.id not in self.concept_facts[concept_id]:
                self.concept_facts[concept_id].append(fact.id)
    
    async def _process_belief(self, belief: Belief) -> None:
        """Process a belief when it's stored."""
        # Link belief to facts it references as evidence
        if hasattr(belief, "evidence"):
            for evidence_id in belief.evidence:
                if evidence_id in self.items and isinstance(self.items[evidence_id], Fact):
                    if evidence_id not in self.fact_beliefs:
                        self.fact_beliefs[evidence_id] = []
                    
                    if belief.id not in self.fact_beliefs[evidence_id]:
                        self.fact_beliefs[evidence_id].append(belief.id)
    
    async def _process_rule(self, rule: Rule) -> None:
        """Process a rule when it's stored."""
        # Link rule to concepts it references
        for condition in rule.conditions:
            if "concept_id" in condition:
                concept_id = condition["concept_id"]
                
                if concept_id not in self.concept_rules:
                    self.concept_rules[concept_id] = []
                
                if rule.id not in self.concept_rules[concept_id]:
                    self.concept_rules[concept_id].append(rule.id)
    
    async def _update_concept_relations(self, concept: Concept) -> None:
        """Update concept relations when a concept is updated."""
        # Clear existing relations
        if concept.id in self.concept_relations:
            # Remove reverse relations
            for related_id in self.concept_relations[concept.id]:
                if related_id in self.concept_relations and concept.id in self.concept_relations[related_id]:
                    del self.concept_relations[related_id][concept.id]
            
            # Clear direct relations
            self.concept_relations[concept.id] = {}
        
        # Add new relations
        if concept.related_concepts:
            if concept.id not in self.concept_relations:
                self.concept_relations[concept.id] = {}
            
            for related_id in concept.related_concepts:
                self.concept_relations[concept.id][related_id] = 0.5  # Default strength
                
                # Add reverse relation
                if related_id not in self.concept_relations:
                    self.concept_relations[related_id] = {}
                self.concept_relations[related_id][concept.id] = 0.5  # Default strength
    
    async def _remove_concept(self, concept: Concept) -> None:
        """Clean up indexes when a concept is removed."""
        # Remove from concept relations
        if concept.id in self.concept_relations:
            # Remove reverse relations
            for related_id in self.concept_relations[concept.id]:
                if related_id in self.concept_relations and concept.id in self.concept_relations[related_id]:
                    del self.concept_relations[related_id][concept.id]
            
            del self.concept_relations[concept.id]
        
        # Remove from concept hierarchy
        if concept.id in self.concept_hierarchies:
            # Update children lists for parents
            for parent_id in self.concept_hierarchies[concept.id]:
                if parent_id in self.concept_children and concept.id in self.concept_children[parent_id]:
                    self.concept_children[parent_id].remove(concept.id)
            
            del self.concept_hierarchies[concept.id]
        
        # Remove from concept children
        if concept.id in self.concept_children:
            # Update parent lists for children
            for child_id in self.concept_children[concept.id]:
                if child_id in self.concept_hierarchies and concept.id in self.concept_hierarchies[child_id]:
                    self.concept_hierarchies[child_id].remove(concept.id)
            
            del self.concept_children[concept.id]
        
        # Remove from concept properties
        if concept.id in self.concept_properties:
            del self.concept_properties[concept.id]
        
        # Remove from concept embeddings
        if concept.id in self.concept_embeddings:
            del self.concept_embeddings[concept.id]
        
        # Remove from concept facts
        if concept.id in self.concept_facts:
            del self.concept_facts[concept.id]
        
        # Remove from concept rules
        if concept.id in self.concept_rules:
            del self.concept_rules[concept.id]
    
    async def _remove_fact(self, fact: Fact) -> None:
        """Clean up indexes when a fact is removed."""
        # Remove from fact beliefs
        if fact.id in self.fact_beliefs:
            del self.fact_beliefs[fact.id]
        
        # Remove from concept facts
        for concept_id, fact_ids in self.concept_facts.items():
            if fact.id in fact_ids:
                fact_ids.remove(fact.id)
    
    async def _remove_belief(self, belief: Belief) -> None:
        """Clean up indexes when a belief is removed."""
        # Remove from fact beliefs
        for fact_id, belief_ids in self.fact_beliefs.items():
            if belief.id in belief_ids:
                belief_ids.remove(belief.id)
    
    async def _remove_rule(self, rule: Rule) -> None:
        """Clean up indexes when a rule is removed."""
        # Remove from concept rules
        for concept_id, rule_ids in self.concept_rules.items():
            if rule.id in rule_ids:
                rule_ids.remove(rule.id)
    
    def _index_text(self, item: Knowledge) -> None:
        """Index an item's text content for search."""
        # Extract text from content
        text = ""
        
        if hasattr(item, "content") and isinstance(item.content, dict):
            # Concatenate all string values in content
            for value in item.content.values():
                if isinstance(value, str):
                    text += " " + value
        
        # Tokenize and index
        if text:
            terms = self._tokenize_text(text)
            
            for term in terms:
                self.text_index[term].add(item.id)
    
    def _remove_from_text_index(self, item_id: str) -> None:
        """Remove an item from the text index."""
        for term, item_ids in self.text_index.items():
            if item_id in item_ids:
                item_ids.remove(item_id)
                
                # Clean up empty entries
                if not item_ids:
                    del self.text_index[term]
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into searchable terms."""
        # Simple tokenization - in a real system, this would be more sophisticated
        return [term.lower() for term in text.split() if term]
    
    async def _apply_content_filters(self, content: Dict[str, Any], item_ids: Set[str]) -> Set[str]:
        """Apply content filters to a set of item IDs."""
        result_ids = item_ids.copy()
        
        # Text search
        if "text" in content:
            text = content["text"].lower()
            terms = self._tokenize_text(text)
            
            if terms:
                # Find items matching all terms
                matching_ids = set()
                for term in terms:
                    # Partial matching
                    for indexed_term, term_items in self.text_index.items():
                        if term in indexed_term:
                            matching_ids.update(term_items)
                
                result_ids = result_ids.intersection(matching_ids) if matching_ids else set()
        
        # Concept filter
        if "concept_id" in content:
            concept_id = content["concept_id"]
            concept_related_ids = set()
            
            # Add facts related to this concept
            if concept_id in self.concept_facts:
                concept_related_ids.update(self.concept_facts[concept_id])
            
            # Add rules related to this concept
            if concept_id in self.concept_rules:
                concept_related_ids.update(self.concept_rules[concept_id])
            
            # Add the concept itself
            if concept_id in self.items:
                concept_related_ids.add(concept_id)
            
            result_ids = result_ids.intersection(concept_related_ids) if concept_related_ids else set()
        
        # Confidence threshold filter
        if "min_confidence" in content:
            min_confidence = float(content["min_confidence"])
            confident_ids = {
                item_id for item_id in result_ids
                if item_id in self.items and self.items[item_id].confidence >= min_confidence
            }
            result_ids = confident_ids
        
        # Time range filter
        if "created_after" in content:
            created_after = float(content["created_after"])
            recent_ids = {
                item_id for item_id in result_ids
                if item_id in self.items and self.items[item_id].created_at >= created_after
            }
            result_ids = recent_ids
        
        return result_ids
    
    def _update_recently_accessed(self, item_id: str) -> None:
        """Update the LRU cache of recently accessed items."""
        # Remove if already in list
        if item_id in self.recently_accessed:
            self.recently_accessed.remove(item_id)
        
        # Add to front of list
        self.recently_accessed.insert(0, item_id)
        
        # Trim list if needed
        if len(self.recently_accessed) > self.cache_size:
            self.recently_accessed.pop()