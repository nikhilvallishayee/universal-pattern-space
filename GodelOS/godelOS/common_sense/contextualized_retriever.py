"""
Module 9.3: Contextualized Retriever (CR)

This module implements context-aware knowledge retrieval, prioritizing knowledge
based on relevance to the current context, handling ambiguity resolution based on context,
providing methods for retrieving knowledge with different levels of context sensitivity,
and integrating with the Scalability System for efficient retrieval.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
import time
import heapq
from enum import Enum, auto
from dataclasses import dataclass, field

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.common_sense.context_engine import ContextEngine, Context, ContextType
from godelOS.scalability.caching import CachingSystem

# Configure logging
logger = logging.getLogger(__name__)


class ContextRelevanceStrategy(Enum):
    """Enumeration of strategies for determining context relevance."""
    EXACT_MATCH = auto()       # Exact matching of context variables
    SEMANTIC_SIMILARITY = auto()  # Semantic similarity between contexts
    TEMPORAL_RECENCY = auto()   # More recent contexts are more relevant
    HIERARCHICAL = auto()       # Consider context hierarchy
    WEIGHTED = auto()           # Use weighted combination of factors
    CUSTOM = auto()             # Custom relevance function


@dataclass
class RetrievalResult:
    """Represents a result from knowledge retrieval."""
    content: Any
    source: str
    confidence: float
    context_relevance: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def overall_score(self) -> float:
        """Calculate overall score based on confidence and context relevance."""
        return self.confidence * self.context_relevance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content": self.content,
            "source": self.source,
            "confidence": self.confidence,
            "context_relevance": self.context_relevance,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "overall_score": self.overall_score()
        }


class ContextualizedRetriever:
    """Implements context-aware knowledge retrieval.
    
    This class is responsible for retrieving knowledge from various sources
    while taking into account the current context, prioritizing knowledge
    based on relevance to the context, and handling ambiguity resolution.
    """
    
    def __init__(self, 
                 knowledge_store: KnowledgeStoreInterface,
                 context_engine: ContextEngine,
                 cache_system: Optional[CachingSystem] = None,
                 default_relevance_strategy: ContextRelevanceStrategy = ContextRelevanceStrategy.WEIGHTED,
                 relevance_weights: Optional[Dict[str, float]] = None,
                 max_results: int = 10,
                 min_confidence: float = 0.0,
                 min_relevance: float = 0.0):
        """Initialize the Contextualized Retriever.
        
        Args:
            knowledge_store: The knowledge store to retrieve from
            context_engine: The context engine to use for context awareness
            cache_system: Optional caching system from the Scalability module
            default_relevance_strategy: Default strategy for determining context relevance
            relevance_weights: Optional weights for different relevance factors
            max_results: Maximum number of results to return
            min_confidence: Minimum confidence threshold for results
            min_relevance: Minimum context relevance threshold for results
        """
        self.knowledge_store = knowledge_store
        self.context_engine = context_engine
        self.cache_system = cache_system
        self.default_relevance_strategy = default_relevance_strategy
        self.relevance_weights = relevance_weights or {
            "exact_match": 1.0,
            "semantic_similarity": 0.8,
            "temporal_recency": 0.6,
            "hierarchical": 0.7
        }
        self.max_results = max_results
        self.min_confidence = min_confidence
        self.min_relevance = min_relevance
        self.custom_relevance_functions: Dict[str, Callable] = {}
        
        # Register default relevance functions
        self._register_default_relevance_functions()
    
    def retrieve(self, 
                query: Any, 
                context_id: Optional[str] = None,
                relevance_strategy: Optional[ContextRelevanceStrategy] = None,
                max_results: Optional[int] = None,
                min_confidence: Optional[float] = None,
                min_relevance: Optional[float] = None,
                filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """Retrieve knowledge based on a query and context.
        
        Args:
            query: The query to retrieve knowledge for
            context_id: Optional ID of the context to use.
                       If None, use the active context.
            relevance_strategy: Optional strategy for determining context relevance
            max_results: Optional maximum number of results to return
            min_confidence: Optional minimum confidence threshold
            min_relevance: Optional minimum context relevance threshold
            filters: Optional filters to apply to the results
            
        Returns:
            List of retrieval results ordered by relevance
        """
        # Use default values if not specified
        relevance_strategy = relevance_strategy or self.default_relevance_strategy
        max_results = max_results or self.max_results
        min_confidence = min_confidence if min_confidence is not None else self.min_confidence
        min_relevance = min_relevance if min_relevance is not None else self.min_relevance
        
        # Get the context to use
        context = self._get_context(context_id)
        
        # Check cache first if available
        cache_key = self._generate_cache_key(query, context_id, relevance_strategy, filters)
        cached_results = self._get_from_cache(cache_key)
        if cached_results:
            return cached_results
        
        # Retrieve raw results from knowledge store
        raw_results = self._retrieve_from_knowledge_store(query, filters)
        
        # Apply context relevance scoring
        contextualized_results = self._apply_context_relevance(
            raw_results, context, relevance_strategy
        )
        
        # Filter by confidence and relevance thresholds
        filtered_results = [
            result for result in contextualized_results
            if result.confidence >= min_confidence and result.context_relevance >= min_relevance
        ]
        
        # Sort by overall score and limit to max_results
        sorted_results = sorted(
            filtered_results, 
            key=lambda x: x.overall_score(), 
            reverse=True
        )[:max_results]
        
        # Cache the results if caching is available
        if self.cache_system:
            self._save_to_cache(cache_key, sorted_results)
        
        return sorted_results
    
    def retrieve_with_ambiguity_resolution(self, 
                                         query: Any,
                                         context_id: Optional[str] = None,
                                         max_results: int = 1) -> List[RetrievalResult]:
        """Retrieve knowledge with ambiguity resolution based on context.
        
        This method is specifically designed to handle ambiguous queries by using
        context to disambiguate and return the most relevant results.
        
        Args:
            query: The potentially ambiguous query
            context_id: Optional ID of the context to use for disambiguation
            max_results: Maximum number of results to return after disambiguation
            
        Returns:
            List of disambiguated retrieval results
        """
        # First, get a larger set of potential results
        potential_results = self.retrieve(
            query=query,
            context_id=context_id,
            relevance_strategy=ContextRelevanceStrategy.WEIGHTED,
            max_results=max_results * 5,  # Get more results initially for disambiguation
            min_confidence=0.0,  # Lower threshold to get more candidates
            min_relevance=0.0
        )
        
        if not potential_results:
            return []
        
        # Get the context to use for disambiguation
        context = self._get_context(context_id)
        
        # Apply more aggressive context-based disambiguation
        disambiguated_results = self._disambiguate_results(potential_results, context)
        
        # Return the top results after disambiguation
        return disambiguated_results[:max_results]
    
    def retrieve_with_context_sensitivity(self,
                                        query: Any,
                                        context_id: Optional[str] = None,
                                        sensitivity_level: float = 0.5) -> List[RetrievalResult]:
        """Retrieve knowledge with adjustable context sensitivity.
        
        Args:
            query: The query to retrieve knowledge for
            context_id: Optional ID of the context to use
            sensitivity_level: Level of context sensitivity (0.0 to 1.0)
                              0.0 means ignore context completely
                              1.0 means rely heavily on context
            
        Returns:
            List of retrieval results with adjusted context sensitivity
        """
        # Clamp sensitivity level to valid range
        sensitivity_level = max(0.0, min(1.0, sensitivity_level))
        
        # Adjust relevance weights based on sensitivity level
        adjusted_weights = {
            key: value * sensitivity_level
            for key, value in self.relevance_weights.items()
        }
        
        # Create a temporary retriever with adjusted weights
        temp_retriever = ContextualizedRetriever(
            knowledge_store=self.knowledge_store,
            context_engine=self.context_engine,
            cache_system=self.cache_system,
            default_relevance_strategy=self.default_relevance_strategy,
            relevance_weights=adjusted_weights,
            max_results=self.max_results,
            min_confidence=self.min_confidence,
            min_relevance=self.min_relevance * sensitivity_level  # Adjust min relevance too
        )
        
        # Use the temporary retriever to get results
        return temp_retriever.retrieve(query, context_id)
    
    def register_custom_relevance_function(self, name: str, func: Callable) -> None:
        """Register a custom relevance function.
        
        Args:
            name: Name of the custom relevance function
            func: The function to register. It should take a result and a context
                 and return a relevance score between 0.0 and 1.0.
        """
        self.custom_relevance_functions[name] = func
    
    def _register_default_relevance_functions(self) -> None:
        """Register the default relevance functions."""
        self.custom_relevance_functions["exact_match"] = self._exact_match_relevance
        self.custom_relevance_functions["semantic_similarity"] = self._semantic_similarity_relevance
        self.custom_relevance_functions["temporal_recency"] = self._temporal_recency_relevance
        self.custom_relevance_functions["hierarchical"] = self._hierarchical_relevance
    
    def _get_context(self, context_id: Optional[str] = None) -> Optional[Context]:
        """Get the context to use for retrieval.
        
        Args:
            context_id: Optional ID of the context to use.
                       If None, use the active context.
            
        Returns:
            The context to use, or None if not available
        """
        if context_id:
            return self.context_engine.get_context(context_id)
        else:
            return self.context_engine.get_active_context()
    
    def _generate_cache_key(self, 
                           query: Any, 
                           context_id: Optional[str],
                           relevance_strategy: ContextRelevanceStrategy,
                           filters: Optional[Dict[str, Any]]) -> str:
        """Generate a cache key for a retrieval operation.
        
        Args:
            query: The query
            context_id: The context ID
            relevance_strategy: The relevance strategy
            filters: The filters
            
        Returns:
            A string cache key
        """
        # Convert query to string if it's not already
        query_str = str(query)
        
        # Use active context ID if none provided
        if not context_id and self.context_engine.active_context_id:
            context_id = self.context_engine.active_context_id
        
        # Generate key components
        key_parts = [
            f"query:{query_str}",
            f"context:{context_id or 'none'}",
            f"strategy:{relevance_strategy.name}"
        ]
        
        # Add filters if present
        if filters:
            filter_str = ",".join(f"{k}:{v}" for k, v in sorted(filters.items()))
            key_parts.append(f"filters:{filter_str}")
        
        return ":".join(key_parts)
    
    def _get_from_cache(self, key: str) -> Optional[List[RetrievalResult]]:
        """Get results from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached results or None if not found
        """
        if not self.cache_system:
            return None
        
        try:
            cached_data = self.cache_system.get(f"contextualized_retriever:{key}")
            if not cached_data:
                return None
            
            # Convert dictionary data back to RetrievalResult objects
            results = []
            for item in cached_data:
                results.append(RetrievalResult(
                    content=item["content"],
                    source=item["source"],
                    confidence=item["confidence"],
                    context_relevance=item["context_relevance"],
                    metadata=item.get("metadata", {}),
                    timestamp=item.get("timestamp", time.time())
                ))
            
            return results
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {e}")
            return None
    
    def _save_to_cache(self, key: str, results: List[RetrievalResult]) -> None:
        """Save results to cache.
        
        Args:
            key: Cache key
            results: Results to cache
        """
        if not self.cache_system:
            return
        
        try:
            # Convert RetrievalResult objects to dictionaries
            cache_data = [result.to_dict() for result in results]
            
            # Cache with a reasonable TTL (e.g., 1 hour)
            self.cache_system.set(f"contextualized_retriever:{key}", cache_data, ttl=3600)
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")
    
    def _retrieve_from_knowledge_store(self, 
                                      query: Any, 
                                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve raw results from the knowledge store.
        
        Args:
            query: The query
            filters: Optional filters to apply
            
        Returns:
            List of raw results from the knowledge store
        """
        # This would be implemented based on the specific knowledge store interface
        # For now, we'll use a simplified approach
        
        try:
            # Determine the type of query and use appropriate retrieval method
            if isinstance(query, str):
                if query.startswith("entity:"):
                    entity_id = query[7:]
                    return self._retrieve_entity(entity_id, filters)
                elif query.startswith("relation:"):
                    relation_parts = query[9:].split(":")
                    if len(relation_parts) >= 2:
                        source = relation_parts[0]
                        relation_type = relation_parts[1]
                        target = relation_parts[2] if len(relation_parts) > 2 else None
                        return self._retrieve_relations(source, relation_type, target, filters)
                else:
                    # Assume it's a text query
                    return self._retrieve_by_text(query, filters)
            elif isinstance(query, dict):
                # Structured query
                return self._retrieve_structured(query, filters)
            else:
                logger.warning(f"Unsupported query type: {type(query)}")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving from knowledge store: {e}")
            return []
    
    def _retrieve_entity(self, 
                        entity_id: str, 
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve information about an entity.
        
        Args:
            entity_id: The entity ID
            filters: Optional filters
            
        Returns:
            List of entity information
        """
        # This would call the appropriate method on the knowledge store
        # For now, we'll return a placeholder result
        
        try:
            # Get entity properties
            properties = self.knowledge_store.get_entity_properties(entity_id)
            
            # Get entity relations
            relations = self.knowledge_store.get_entity_relations(entity_id)
            
            # Combine into a result
            result = {
                "content": {
                    "entity_id": entity_id,
                    "properties": properties,
                    "relations": relations
                },
                "source": "knowledge_store",
                "confidence": 1.0,
                "metadata": {
                    "type": "entity",
                    "retrieval_time": time.time()
                }
            }
            
            return [result]
            
        except Exception as e:
            logger.warning(f"Error retrieving entity {entity_id}: {e}")
            return []
    
    def _retrieve_relations(self, 
                           source: str, 
                           relation_type: str, 
                           target: Optional[str] = None,
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve relations between entities.
        
        Args:
            source: Source entity ID
            relation_type: Type of relation
            target: Optional target entity ID
            filters: Optional filters
            
        Returns:
            List of relation information
        """
        try:
            # Get relations
            if target:
                # Get specific relation
                relation = self.knowledge_store.get_relation(source, relation_type, target)
                relations = [relation] if relation else []
            else:
                # Get all relations of this type from the source
                relations = self.knowledge_store.get_relations_from(source, relation_type)
            
            # Convert to results
            results = []
            for relation in relations:
                result = {
                    "content": relation,
                    "source": "knowledge_store",
                    "confidence": relation.get("confidence", 1.0),
                    "metadata": {
                        "type": "relation",
                        "retrieval_time": time.time()
                    }
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.warning(f"Error retrieving relations for {source} {relation_type} {target}: {e}")
            return []
    
    def _retrieve_by_text(self, 
                         text: str, 
                         filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve knowledge based on text query.
        
        Args:
            text: Text query
            filters: Optional filters
            
        Returns:
            List of results matching the text query
        """
        try:
            # This would use a text search capability of the knowledge store
            # For now, we'll return a placeholder result
            
            # Assume the knowledge store has a search_text method
            search_results = self.knowledge_store.search_text(text, filters)
            
            # Convert to results
            results = []
            for item in search_results:
                result = {
                    "content": item["content"],
                    "source": "knowledge_store",
                    "confidence": item.get("score", 0.5),
                    "metadata": {
                        "type": "text_search",
                        "retrieval_time": time.time()
                    }
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.warning(f"Error retrieving by text '{text}': {e}")
            return []
    
    def _retrieve_structured(self, 
                            query: Dict[str, Any], 
                            filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve knowledge based on structured query.
        
        Args:
            query: Structured query
            filters: Optional filters
            
        Returns:
            List of results matching the structured query
        """
        try:
            # This would use a structured query capability of the knowledge store
            # For now, we'll return a placeholder result
            
            # Assume the knowledge store has a query method
            query_results = self.knowledge_store.query(query, filters)
            
            # Convert to results
            results = []
            for item in query_results:
                result = {
                    "content": item["content"],
                    "source": "knowledge_store",
                    "confidence": item.get("confidence", 0.5),
                    "metadata": {
                        "type": "structured_query",
                        "retrieval_time": time.time()
                    }
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.warning(f"Error retrieving by structured query: {e}")
            return []
    
    def _apply_context_relevance(self, 
                                raw_results: List[Dict[str, Any]], 
                                context: Optional[Context],
                                relevance_strategy: ContextRelevanceStrategy) -> List[RetrievalResult]:
        """Apply context relevance scoring to raw results.
        
        Args:
            raw_results: Raw results from knowledge store
            context: Context to use for relevance scoring
            relevance_strategy: Strategy for determining context relevance
            
        Returns:
            List of results with context relevance scores
        """
        # If no context is available, return results with neutral relevance
        if not context:
            return [
                RetrievalResult(
                    content=result["content"],
                    source=result["source"],
                    confidence=result.get("confidence", 0.5),
                    context_relevance=0.5,  # Neutral relevance
                    metadata=result.get("metadata", {})
                )
                for result in raw_results
            ]
        
        # Apply the selected relevance strategy
        if relevance_strategy == ContextRelevanceStrategy.EXACT_MATCH:
            return self._apply_exact_match_strategy(raw_results, context)
        elif relevance_strategy == ContextRelevanceStrategy.SEMANTIC_SIMILARITY:
            return self._apply_semantic_similarity_strategy(raw_results, context)
        elif relevance_strategy == ContextRelevanceStrategy.TEMPORAL_RECENCY:
            return self._apply_temporal_recency_strategy(raw_results, context)
        elif relevance_strategy == ContextRelevanceStrategy.HIERARCHICAL:
            return self._apply_hierarchical_strategy(raw_results, context)
        elif relevance_strategy == ContextRelevanceStrategy.WEIGHTED:
            return self._apply_weighted_strategy(raw_results, context)
        elif relevance_strategy == ContextRelevanceStrategy.CUSTOM:
            return self._apply_custom_strategy(raw_results, context)
        else:
            # Default to weighted strategy
            return self._apply_weighted_strategy(raw_results, context)
    
    def _apply_exact_match_strategy(self, 
                                   raw_results: List[Dict[str, Any]], 
                                   context: Context) -> List[RetrievalResult]:
        """Apply exact match relevance strategy.
        
        Args:
            raw_results: Raw results
            context: Context
            
        Returns:
            Results with relevance scores
        """
        results = []
        
        for result in raw_results:
            relevance = self._exact_match_relevance(result, context)
            
            results.append(RetrievalResult(
                content=result["content"],
                source=result["source"],
                confidence=result.get("confidence", 0.5),
                context_relevance=relevance,
                metadata=result.get("metadata", {})
            ))
        
        return results
    
    def _apply_semantic_similarity_strategy(self, 
                                          raw_results: List[Dict[str, Any]], 
                                          context: Context) -> List[RetrievalResult]:
        """Apply semantic similarity relevance strategy.
        
        Args:
            raw_results: Raw results
            context: Context
            
        Returns:
            Results with relevance scores
        """
        results = []
        
        for result in raw_results:
            relevance = self._semantic_similarity_relevance(result, context)
            
            results.append(RetrievalResult(
                content=result["content"],
                source=result["source"],
                confidence=result.get("confidence", 0.5),
                context_relevance=relevance,
                metadata=result.get("metadata", {})
            ))
        
        return results
    
    def _apply_temporal_recency_strategy(self, 
                                        raw_results: List[Dict[str, Any]], 
                                        context: Context) -> List[RetrievalResult]:
        """Apply temporal recency relevance strategy.
        
        Args:
            raw_results: Raw results
            context: Context
            
        Returns:
            Results with relevance scores
        """
        results = []
        
        for result in raw_results:
            relevance = self._temporal_recency_relevance(result, context)
            
            results.append(RetrievalResult(
                content=result["content"],
                source=result["source"],
                confidence=result.get("confidence", 0.5),
                context_relevance=relevance,
                metadata=result.get("metadata", {})
            ))
        
        return results
    
    def _apply_hierarchical_strategy(self, 
                                    raw_results: List[Dict[str, Any]], 
                                    context: Context) -> List[RetrievalResult]:
        """Apply hierarchical relevance strategy.
        
        Args:
            raw_results: Raw results
            context: Context
            
        Returns:
            Results with relevance scores
        """
        results = []
        
        for result in raw_results:
            relevance = self._hierarchical_relevance(result, context)
            
            results.append(RetrievalResult(
                content=result["content"],
                source=result["source"],
                confidence=result.get("confidence", 0.5),
                context_relevance=relevance,
                metadata=result.get("metadata", {})
            ))
        
        return results
    
    def _apply_weighted_strategy(self, 
                                raw_results: List[Dict[str, Any]], 
                                context: Context) -> List[RetrievalResult]:
        """Apply weighted combination relevance strategy.
        
        Args:
            raw_results: Raw results
            context: Context
            
        Returns:
            Results with relevance scores
        """
        results = []
        
        for result in raw_results:
            # Calculate individual relevance scores
            exact_match_score = self._exact_match_relevance(result, context)
            semantic_score = self._semantic_similarity_relevance(result, context)
            temporal_score = self._temporal_recency_relevance(result, context)
            hierarchical_score = self._hierarchical_relevance(result, context)
            
            # Calculate weighted average
            total_weight = sum(self.relevance_weights.values())
            weighted_score = (
                exact_match_score * self.relevance_weights.get("exact_match", 0.0) +
                semantic_score * self.relevance_weights.get("semantic_similarity", 0.0) +
                temporal_score * self.relevance_weights.get("temporal_recency", 0.0) +
                hierarchical_score * self.relevance_weights.get("hierarchical", 0.0)
            ) / total_weight if total_weight > 0 else 0.5
            
            results.append(RetrievalResult(
                content=result["content"],
                source=result["source"],
                confidence=result.get("confidence", 0.5),
                context_relevance=weighted_score,
                metadata=result.get("metadata", {})
            ))
        
        return results
    
    def _apply_custom_strategy(self, 
                              raw_results: List[Dict[str, Any]], 
                              context: Context) -> List[RetrievalResult]:
        """Apply custom relevance strategy.
        
        Args:
            raw_results: Raw results
            context: Context
            
        Returns:
            Results with relevance scores
        """
        results = []
        
        # Use all registered custom relevance functions
        for result in raw_results:
            # Calculate relevance using each custom function
            relevance_scores = []
            for func_name, func in self.custom_relevance_functions.items():
                try:
                    score = func(result, context)
                    relevance_scores.append(score)
                except Exception as e:
                    logger.warning(f"Error in custom relevance function {func_name}: {e}")
            
            # Use average of all scores
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.5
            
            results.append(RetrievalResult(
                content=result["content"],
                source=result["source"],
                confidence=result.get("confidence", 0.5),
                context_relevance=avg_relevance,
                metadata=result.get("metadata", {})
            ))
        
        return results
    
    def _exact_match_relevance(self, 
                              result: Dict[str, Any], 
                              context: Context) -> float:
        """Calculate relevance based on exact matches with context variables.
        
        Args:
            result: Result to evaluate
            context: Context to match against
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Extract content as string or dict
        content = result["content"]
        
        # Get context variables
        context_vars = {name: var.value for name, var in context.variables.items()}
        
        # Count matches
        matches = 0
        total_vars = len(context_vars)
        
        if isinstance(content, dict):
            # For dictionary content, check if context variables appear as keys or values
            for var_name, var_value in context_vars.items():
                # Check if variable name appears as a key
                if var_name in content:
                    matches += 0.5
                
                # Check if variable value appears as a value
                if var_value in content.values():
                    matches += 0.5
                
                # Check for exact match of key-value pair
                if content.get(var_name) == var_value:
                    matches += 1
        else:
            # For string content, check if context variable values appear in the string
            content_str = str(content).lower()
            for var_value in context_vars.values():
                if str(var_value).lower() in content_str:
                    matches += 1
        
        # Calculate relevance score
        return matches / (total_vars + 1) if total_vars > 0 else 0.5
    
    def _semantic_similarity_relevance(self, 
                                      result: Dict[str, Any], 
                                      context: Context) -> float:
        """Calculate relevance based on semantic similarity with context.
        
        Args:
            result: Result to evaluate
            context: Context to match against
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # In a real implementation, this would use semantic similarity metrics
        # For now, we'll use a simplified approach based on keyword overlap
        
        # Extract content as string
        if isinstance(result["content"], dict):
            content_str = " ".join(str(v) for v in result["content"].values())
        else:
            content_str = str(result["content"])
        
        content_str = content_str.lower()
        
        # Get context variables as strings
        context_strs = [str(var.value).lower() for var in context.variables.values()]
        
        # Count word overlap
        content_words = set(content_str.split())
        total_matches = 0
        
        for context_str in context_strs:
            context_words = set(context_str.split())
            if context_words:
                # Calculate Jaccard similarity
                intersection = len(content_words.intersection(context_words))
                union = len(content_words.union(context_words))
                if union > 0:
                    total_matches += intersection / union
        
        # Calculate average similarity
        avg_similarity = total_matches / len(context_strs) if context_strs else 0.5
        
        return avg_similarity
    
    def _temporal_recency_relevance(self, 
                                   result: Dict[str, Any], 
                                   context: Context) -> float:
        """Calculate relevance based on temporal recency.
        
        Args:
            result: Result to evaluate
            context: Context to match against
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Get result timestamp
        result_time = result.get("metadata", {}).get("retrieval_time", time.time())
        
        # Get context creation time
        context_time = context.created_at
        
        # Calculate time difference in hours
        time_diff_hours = abs(result_time - context_time) / 3600
        
        # Calculate recency score (newer is more relevant)
        # Use exponential decay with half-life of 24 hours
        recency_score = 2 ** (-time_diff_hours / 24)
        
        return recency_score
    
    def _hierarchical_relevance(self, 
                               result: Dict[str, Any], 
                               context: Context) -> float:
        """Calculate relevance based on context hierarchy.
        
        Args:
            result: Result to evaluate
            context: Context to match against
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Get the context hierarchy
        hierarchy = self.context_engine.get_context_hierarchy(context.id)
        
        if not hierarchy:
            return 0.5
        
        # Calculate relevance for each context in the hierarchy
        relevance_scores = []
        
        for i, ctx in enumerate(hierarchy):
            # Calculate exact match relevance for this context
            exact_score = self._exact_match_relevance(result, ctx)
            
            # Apply distance penalty (contexts further up the hierarchy have less influence)
            distance_factor = 0.8 ** i  # Exponential decay with distance
            weighted_score = exact_score * distance_factor
            
            relevance_scores.append(weighted_score)
        
        # Use the maximum relevance from any context in the hierarchy
        return max(relevance_scores) if relevance_scores else 0.5
    
    def _disambiguate_results(self, 
                             results: List[RetrievalResult], 
                             context: Optional[Context]) -> List[RetrievalResult]:
        """Disambiguate results based on context.
        
        Args:
            results: Results to disambiguate
            context: Context to use for disambiguation
            
        Returns:
            Disambiguated results
        """
        if not results or not context:
            return results
        
        # Group results by content type or category
        grouped_results = {}
        
        for result in results:
            # Determine the category of the result
            category = self._get_result_category(result)
            
            if category not in grouped_results:
                grouped_results[category] = []
            
            grouped_results[category].append(result)
        
        # For each group, select the most contextually relevant result
        disambiguated = []
        
        for category, group in grouped_results.items():
            # Sort by context relevance
            sorted_group = sorted(group, key=lambda x: x.context_relevance, reverse=True)
            
            # Take the most relevant result from each group
            disambiguated.append(sorted_group[0])
        
        # Sort the final results by overall score
        return sorted(disambiguated, key=lambda x: x.overall_score(), reverse=True)
    
    def _get_result_category(self, result: RetrievalResult) -> str:
        """Determine the category of a result for disambiguation.
        
        Args:
            result: The result to categorize
            
        Returns:
            Category string
        """
        # This would be implemented based on the specific knowledge representation
        # For now, we'll use a simplified approach
        
        content = result.content
        
        if isinstance(content, dict):
            # For dictionary content, use the type if available
            if "type" in content:
                return str(content["type"])
            elif "entity_id" in content:
                return f"entity:{content['entity_id']}"
            else:
                # Use the first key as a category
                return next(iter(content.keys()), "unknown")
        else:
            # For string content, use the first word
            return str(content).split()[0] if str(content).strip() else "unknown"
    
    def register_custom_relevance_function(self, name: str, func: callable):
        """Register a custom relevance function.
        
        Args:
            name: Name of the custom relevance function
            func: The function to register. It should take a result and a context
                 and return a relevance score between 0.0 and 1.0.
        """
        self.custom_relevance_functions[name] = func