"""
Knowledge Gap Detector for autonomous learning capabilities.

This module implements gap detection from query processing results and
autonomous gap detection through knowledge graph analysis.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta

from .cognitive_models import (
    KnowledgeGap, KnowledgeGapType, AcquisitionStrategy,
    create_gap_from_query_result
)

logger = logging.getLogger(__name__)


class KnowledgeGapDetector:
    """
    Detects knowledge gaps through various methods:
    1. Query confidence analysis
    2. Knowledge graph connectivity analysis
    3. Relationship completeness checking
    4. Concept isolation detection
    """
    
    def __init__(
        self,
        knowledge_store=None,
        confidence_threshold: float = 0.7,
        isolation_threshold: int = 2,
        analysis_window_hours: int = 24
    ):
        """
        Initialize the knowledge gap detector.
        
        Args:
            knowledge_store: Knowledge storage interface
            confidence_threshold: Minimum confidence for query results
            isolation_threshold: Maximum connections for isolated concepts
            analysis_window_hours: Time window for gap analysis
        """
        self.knowledge_store = knowledge_store
        self.confidence_threshold = confidence_threshold
        self.isolation_threshold = isolation_threshold
        self.analysis_window_hours = analysis_window_hours
        
        # Cache for recently detected gaps
        self.recent_gaps: Dict[str, KnowledgeGap] = {}
        self.gap_cache_duration = timedelta(hours=1)
        
        # Performance tracking
        self.detection_stats = {
            'queries_analyzed': 0,
            'gaps_detected': 0,
            'autonomous_scans': 0,
            'isolated_concepts_found': 0
        }
        
        logger.info("KnowledgeGapDetector initialized")
    
    async def detect_gaps_from_query(
        self,
        query: str,
        result: Dict[str, Any]
    ) -> List[KnowledgeGap]:
        """
        Detect knowledge gaps from a query processing result.
        
        Args:
            query: The original query
            result: Query processing result
            
        Returns:
            List of detected knowledge gaps
        """
        gaps = []
        self.detection_stats['queries_analyzed'] += 1
        
        try:
            # Check for low confidence response
            confidence_gap = create_gap_from_query_result(
                query, result, self.confidence_threshold
            )
            
            if confidence_gap:
                gaps.append(confidence_gap)
                self.detection_stats['gaps_detected'] += 1
            
            # Analyze for specific gap types
            additional_gaps = await self._analyze_query_context(query, result)
            gaps.extend(additional_gaps)
            
            # Cache detected gaps
            for gap in gaps:
                self.recent_gaps[gap.id] = gap
            
            # Clean old gaps from cache
            await self._clean_gap_cache()
            
            logger.debug(f"Detected {len(gaps)} gaps from query: {query[:50]}...")
            return gaps
            
        except Exception as e:
            logger.error(f"Error detecting gaps from query: {e}")
            return []
    
    async def detect_autonomous_gaps(self) -> List[KnowledgeGap]:
        """
        Autonomously detect knowledge gaps through knowledge graph analysis.
        
        Returns:
            List of detected knowledge gaps
        """
        gaps = []
        self.detection_stats['autonomous_scans'] += 1
        
        try:
            # Find isolated concepts
            isolated_gaps = await self._find_isolated_concepts()
            gaps.extend(isolated_gaps)
            
            # Find incomplete relationships
            relationship_gaps = await self._find_incomplete_relationships()
            gaps.extend(relationship_gaps)
            
            # Find missing properties
            property_gaps = await self._find_missing_properties()
            gaps.extend(property_gaps)
            
            # Prioritize gaps based on knowledge graph structure
            prioritized_gaps = await self._prioritize_gaps(gaps)
            
            # Cache detected gaps
            for gap in prioritized_gaps:
                self.recent_gaps[gap.id] = gap
            
            logger.info(f"Autonomous gap detection found {len(prioritized_gaps)} gaps")
            return prioritized_gaps
            
        except Exception as e:
            logger.error(f"Error in autonomous gap detection: {e}")
            return []
    
    async def get_gap_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about gap detection performance.
        
        Returns:
            Dictionary of gap detection statistics
        """
        # Count gaps by type
        gap_types = {}
        for gap in self.recent_gaps.values():
            gap_type = gap.type.value
            gap_types[gap_type] = gap_types.get(gap_type, 0) + 1
        
        # Calculate detection rates
        total_queries = max(self.detection_stats['queries_analyzed'], 1)
        detection_rate = self.detection_stats['gaps_detected'] / total_queries
        
        return {
            'total_gaps_cached': len(self.recent_gaps),
            'gaps_by_type': gap_types,
            'detection_statistics': self.detection_stats.copy(),
            'detection_rate': detection_rate,
            'confidence_threshold': self.confidence_threshold,
            'cache_size': len(self.recent_gaps)
        }
    
    # Private methods
    
    async def _analyze_query_context(
        self,
        query: str,
        result: Dict[str, Any]
    ) -> List[KnowledgeGap]:
        """
        Analyze query context for additional gap types.
        
        Args:
            query: The original query
            result: Query processing result
            
        Returns:
            List of additional detected gaps
        """
        gaps = []
        
        try:
            # Check for missing concepts mentioned in query
            if self.knowledge_store:
                query_concepts = await self._extract_concepts_from_query(query)
                missing_concepts = await self._find_missing_concepts(query_concepts)
                
                if missing_concepts:
                    gap = KnowledgeGap(
                        type=KnowledgeGapType.CONCEPT_MISSING,
                        query=query,
                        confidence=result.get('confidence', 0.0),
                        missing_concepts=missing_concepts,
                        priority=0.8,
                        suggested_acquisitions=[
                            AcquisitionStrategy.CONCEPT_EXPANSION,
                            AcquisitionStrategy.EXTERNAL_SEARCH
                        ]
                    )
                    gaps.append(gap)
            
            # Check for insufficient context
            if result.get('requires_clarification', False):
                gap = KnowledgeGap(
                    type=KnowledgeGapType.CONTEXT_INSUFFICIENT,
                    query=query,
                    confidence=result.get('confidence', 0.0),
                    context_requirements=result.get('clarification_needed', []),
                    priority=0.6,
                    suggested_acquisitions=[
                        AcquisitionStrategy.ANALOGICAL_INFERENCE
                    ]
                )
                gaps.append(gap)
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error analyzing query context: {e}")
            return []
    
    async def _find_isolated_concepts(self) -> List[KnowledgeGap]:
        """
        Find concepts with very few connections in the knowledge graph.
        
        Returns:
            List of gaps for isolated concepts
        """
        gaps = []
        
        if not self.knowledge_store:
            return gaps
        
        try:
            # Query for concepts with few connections
            isolated_concepts = await self._query_isolated_concepts()
            
            for concept in isolated_concepts:
                gap = KnowledgeGap(
                    type=KnowledgeGapType.RELATIONSHIP_INCOMPLETE,
                    missing_concepts=[concept['name']],
                    priority=0.7,
                    suggested_acquisitions=[
                        AcquisitionStrategy.RELATIONSHIP_DISCOVERY,
                        AcquisitionStrategy.CONCEPT_EXPANSION
                    ],
                    metadata={
                        'concept_id': concept.get('id'),
                        'connection_count': concept.get('connections', 0),
                        'isolation_score': concept.get('isolation_score', 1.0)
                    }
                )
                gaps.append(gap)
                self.detection_stats['isolated_concepts_found'] += 1
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error finding isolated concepts: {e}")
            return []
    
    async def _find_incomplete_relationships(self) -> List[KnowledgeGap]:
        """
        Find concepts that should have relationships but don't.
        
        Returns:
            List of gaps for incomplete relationships
        """
        gaps = []
        
        if not self.knowledge_store:
            return gaps
        
        try:
            # Look for concepts that commonly appear together but lack relationships
            incomplete_rels = await self._query_incomplete_relationships()
            
            for rel_data in incomplete_rels:
                gap = KnowledgeGap(
                    type=KnowledgeGapType.RELATIONSHIP_INCOMPLETE,
                    missing_concepts=[rel_data['source'], rel_data['target']],
                    incomplete_relationships=[rel_data],
                    priority=rel_data.get('priority', 0.6),
                    suggested_acquisitions=[
                        AcquisitionStrategy.RELATIONSHIP_DISCOVERY,
                        AcquisitionStrategy.ANALOGICAL_INFERENCE
                    ],
                    metadata={
                        'relationship_type': rel_data.get('suggested_type'),
                        'co_occurrence_score': rel_data.get('co_occurrence', 0.0)
                    }
                )
                gaps.append(gap)
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error finding incomplete relationships: {e}")
            return []
    
    async def _find_missing_properties(self) -> List[KnowledgeGap]:
        """
        Find concepts that are missing common properties.
        
        Returns:
            List of gaps for missing properties
        """
        gaps = []
        
        if not self.knowledge_store:
            return gaps
        
        try:
            # Find concepts missing properties that similar concepts have
            missing_props = await self._query_missing_properties()
            
            for prop_data in missing_props:
                gap = KnowledgeGap(
                    type=KnowledgeGapType.PROPERTY_UNKNOWN,
                    missing_concepts=[prop_data['concept']],
                    priority=0.5,
                    suggested_acquisitions=[
                        AcquisitionStrategy.CONCEPT_EXPANSION,
                        AcquisitionStrategy.ANALOGICAL_INFERENCE
                    ],
                    metadata={
                        'missing_properties': prop_data.get('properties', []),
                        'similar_concepts': prop_data.get('similar_concepts', [])
                    }
                )
                gaps.append(gap)
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error finding missing properties: {e}")
            return []
    
    async def _prioritize_gaps(self, gaps: List[KnowledgeGap]) -> List[KnowledgeGap]:
        """
        Prioritize gaps based on various factors.
        
        Args:
            gaps: List of gaps to prioritize
            
        Returns:
            Prioritized list of gaps
        """
        try:
            # Calculate priority based on multiple factors
            for gap in gaps:
                priority_factors = []
                
                # Factor 1: Isolation score (higher isolation = higher priority)
                if 'isolation_score' in gap.metadata:
                    priority_factors.append(gap.metadata['isolation_score'])
                
                # Factor 2: Co-occurrence frequency
                if 'co_occurrence_score' in gap.metadata:
                    priority_factors.append(gap.metadata['co_occurrence_score'])
                
                # Factor 3: Confidence deficit (lower confidence = higher priority)
                if gap.confidence is not None:
                    priority_factors.append(1.0 - gap.confidence)
                
                # Factor 4: Number of missing concepts
                concept_factor = min(len(gap.missing_concepts) * 0.1, 0.3)
                priority_factors.append(concept_factor)
                
                # Calculate weighted average
                if priority_factors:
                    gap.priority = sum(priority_factors) / len(priority_factors)
                    gap.priority = max(0.0, min(1.0, gap.priority))  # Clamp to [0,1]
            
            # Sort by priority (highest first)
            gaps.sort(key=lambda g: g.priority, reverse=True)
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error prioritizing gaps: {e}")
            return gaps
    
    async def _extract_concepts_from_query(self, query: str) -> List[str]:
        """Extract potential concepts from a query string."""
        # Simple concept extraction - could be enhanced with NLP
        # For now, extract nouns and important terms
        import re
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        # Extract words (simple approach)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        concepts = [word for word in words if word not in stop_words]
        
        return concepts[:10]  # Limit to first 10 potential concepts
    
    async def _find_missing_concepts(self, concepts: List[str]) -> List[str]:
        """Find which concepts are missing from the knowledge store."""
        if not self.knowledge_store:
            return concepts
        
        missing = []
        for concept in concepts:
            # Check if concept exists in knowledge store
            exists = await self._concept_exists(concept)
            if not exists:
                missing.append(concept)
        
        return missing
    
    async def _concept_exists(self, concept: str) -> bool:
        """Check if a concept exists in the knowledge store."""
        # Placeholder implementation - should query actual knowledge store
        try:
            if hasattr(self.knowledge_store, 'get_concept'):
                result = await self.knowledge_store.get_concept(concept)
                return result is not None
            elif hasattr(self.knowledge_store, 'query'):
                # Generic query approach
                result = await self.knowledge_store.query(f"concept:{concept}")
                return bool(result)
            else:
                # Fallback: assume concept exists
                return True
        except Exception:
            return False
    
    async def _query_isolated_concepts(self) -> List[Dict[str, Any]]:
        """Query for isolated concepts in the knowledge graph."""
        # Placeholder implementation
        # Should query knowledge store for concepts with few connections
        return []
    
    async def _query_incomplete_relationships(self) -> List[Dict[str, Any]]:
        """Query for potentially incomplete relationships."""
        # Placeholder implementation
        # Should analyze co-occurrence patterns to find missing relationships
        return []
    
    async def _query_missing_properties(self) -> List[Dict[str, Any]]:
        """Query for concepts missing common properties."""
        # Placeholder implementation
        # Should compare concepts to similar ones to find missing properties
        return []
    
    async def _clean_gap_cache(self) -> None:
        """Clean old gaps from the cache."""
        current_time = datetime.now()
        expired_gaps = []
        
        for gap_id, gap in self.recent_gaps.items():
            if current_time - gap.detected_at > self.gap_cache_duration:
                expired_gaps.append(gap_id)
        
        for gap_id in expired_gaps:
            del self.recent_gaps[gap_id]
        
        if expired_gaps:
            logger.debug(f"Cleaned {len(expired_gaps)} expired gaps from cache")
