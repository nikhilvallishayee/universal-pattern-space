"""
Knowledge Graph Evolution System

This module implements sophisticated knowledge graph evolution capabilities including
dynamic relationship mapping, adaptive knowledge structures, concept emergence tracking,
and evolutionary learning patterns as specified in the LLM Cognitive Architecture.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from enum import Enum
import uuid
import networkx as nx
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RelationshipType(Enum):
    """Types of relationships between knowledge concepts"""
    CAUSAL = "causal"              # A causes B
    ASSOCIATIVE = "associative"    # A is related to B
    HIERARCHICAL = "hierarchical"  # A is part of/contains B
    TEMPORAL = "temporal"          # A occurs before/after B
    SEMANTIC = "semantic"          # A means similar to B
    FUNCTIONAL = "functional"      # A performs function for B
    COMPOSITIONAL = "compositional" # A is composed of B
    EMERGENT = "emergent"          # A emerges from B
    CONTRADICTORY = "contradictory" # A contradicts B
    
    # Common relationship types used in the system
    RELATED_TO = "related_to"      # General relationship
    SIMILAR_TO = "similar_to"      # Similarity relationship
    IS_A = "is_a"                  # Type/instance relationship
    USES = "uses"                  # Usage relationship
    MENTIONS = "mentions"          # Reference relationship
    INCLUDES = "includes"          # Inclusion relationship

class EvolutionTrigger(Enum):
    """Triggers that cause knowledge graph evolution"""
    NEW_INFORMATION = "new_information"
    PATTERN_RECOGNITION = "pattern_recognition"
    CONTRADICTION_DETECTION = "contradiction_detection"
    USAGE_FREQUENCY = "usage_frequency"
    TEMPORAL_DECAY = "temporal_decay"
    EMERGENT_CONCEPT = "emergent_concept"
    COGNITIVE_LOAD = "cognitive_load"
    LEARNING_FEEDBACK = "learning_feedback"
    
    # Testing and validation triggers
    DATA_FLOW_TEST = "data_flow_test"
    INTEGRATION_TEST = "integration_test"
    NEW_CONCEPT = "new_concept"
    
    # Cognitive insight triggers
    SELF_REFLECTION_INSIGHTS = "self_reflection_insights"
    EXPERIENCE_INSIGHTS = "experience_insights"
    CREATIVE_CONCEPT_FORMATION = "creative_concept_formation"
    HYPOTHESIS_FORMATION = "hypothesis_formation"
    HYPOTHESIS_REFINEMENT = "hypothesis_refinement"
    
    # Additional triggers for comprehensive coverage
    USER_FEEDBACK = "user_feedback"
    SYSTEM_OPTIMIZATION = "system_optimization"
    ENVIRONMENTAL_CHANGE = "environmental_change"
    GOAL_COMPLETION = "goal_completion"
    ERROR_CORRECTION = "error_correction"
    LEARNING_MILESTONE = "learning_milestone"
    EXTERNAL_VALIDATION = "external_validation"
    PERFORMANCE_THRESHOLD = "performance_threshold"

class ConceptStatus(Enum):
    """Status of concepts in the knowledge graph"""
    EMERGING = "emerging"          # New concept being formed
    STABLE = "stable"              # Well-established concept
    EVOLVING = "evolving"          # Concept undergoing changes
    DEPRECATED = "deprecated"      # Concept becoming obsolete
    MERGED = "merged"              # Concept merged with another
    SPLIT = "split"                # Concept split into multiple

@dataclass
class KnowledgeConcept:
    """Individual concept in the knowledge graph"""
    id: str
    name: str
    description: str
    concept_type: str
    properties: Dict[str, Any]
    activation_strength: float  # 0.0-1.0
    creation_time: datetime
    last_accessed: datetime
    access_frequency: int
    confidence_score: float  # 0.0-1.0
    status: ConceptStatus
    source_evidence: List[str]
    related_domains: List[str]
    embedding_vector: Optional[List[float]] = None
    evolution_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.evolution_history is None:
            self.evolution_history = []

@dataclass
class KnowledgeRelationship:
    """Relationship between concepts in the knowledge graph"""
    id: str
    source_concept_id: str
    target_concept_id: str
    relationship_type: RelationshipType
    strength: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    bidirectional: bool
    creation_time: datetime
    last_reinforced: datetime
    reinforcement_count: int
    decay_rate: float
    context_conditions: List[str]
    evidence: List[str]
    properties: Dict[str, Any]
    evolution_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.evolution_history is None:
            self.evolution_history = []

@dataclass
class EvolutionEvent:
    """Record of a knowledge graph evolution event"""
    id: str
    event_type: EvolutionTrigger
    timestamp: datetime
    affected_concepts: List[str]
    affected_relationships: List[str]
    changes_made: Dict[str, Any]
    reasoning: str
    confidence: float
    impact_score: float
    success_metrics: Dict[str, float]

@dataclass
class EmergentPattern:
    """Pattern that emerges from knowledge graph analysis"""
    id: str
    pattern_type: str
    description: str
    involved_concepts: List[str]
    involved_relationships: List[str]
    strength: float
    confidence: float
    discovery_time: datetime
    validation_score: float
    implications: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

class KnowledgeGraphEvolution:
    """
    Sophisticated knowledge graph evolution system that adapts and grows
    the knowledge representation based on new information, usage patterns,
    and emergent insights.
    """
    
    def __init__(self, llm_driver=None):
        self.llm_driver = llm_driver
        
        # Core knowledge graph structures
        self.concepts: Dict[str, KnowledgeConcept] = {}
        self.relationships: Dict[str, KnowledgeRelationship] = {}
        self.graph = nx.DiGraph()  # NetworkX graph for analysis
        
        # Evolution tracking
        self.evolution_events: List[EvolutionEvent] = []
        self.emergent_patterns: Dict[str, EmergentPattern] = {}
        self.evolution_history: deque = deque(maxlen=1000)
        
        # Evolution parameters
        self.evolution_config = {
            "activation_threshold": 0.3,
            "decay_rate": 0.01,
            "emergence_threshold": 0.7,
            "relationship_strength_threshold": 0.2,
            "pattern_detection_frequency": 3600,  # seconds
            "max_concept_age_days": 365,
            "consolidation_threshold": 0.8
        }
        
        # Metrics and analytics
        self.evolution_metrics = {
            "concepts_created": 0,
            "concepts_evolved": 0,
            "concepts_merged": 0,
            "concepts_deprecated": 0,
            "relationships_formed": 0,
            "relationships_strengthened": 0,
            "relationships_weakened": 0,
            "patterns_discovered": 0,
            "evolution_cycles": 0
        }
        
        # Active evolution processes
        self.active_evolution_tasks: Set[str] = set()
        self.evolution_queue: deque = deque()
        
    async def evolve_knowledge_graph(self, 
                                   trigger: EvolutionTrigger,
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger knowledge graph evolution based on new information or patterns"""
        try:
            evolution_id = str(uuid.uuid4())
            logger.info(f"Starting knowledge graph evolution: {trigger.value}")
            
            # Analyze current graph state
            graph_state = await self._analyze_graph_state()
            
            # Determine evolution strategy
            evolution_strategy = await self._determine_evolution_strategy(
                trigger, context, graph_state
            )
            
            # Execute evolution process
            evolution_result = await self._execute_evolution(
                evolution_id, evolution_strategy, context
            )
            
            # Validate and consolidate changes
            validation_result = await self._validate_evolution_changes(
                evolution_result
            )
            
            # Update evolution metrics
            self._update_evolution_metrics(evolution_result)
            
            # Record evolution event
            await self._record_evolution_event(
                evolution_id, trigger, evolution_result, context
            )
            
            return {
                "evolution_id": evolution_id,
                "trigger": trigger.value,
                "changes_made": evolution_result,
                "validation_score": validation_result["score"],
                "graph_metrics": await self._get_graph_metrics(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in knowledge graph evolution: {e}")
            return {"error": str(e)}
    
    async def add_concept(self, 
                         concept_data: Dict[str, Any],
                         auto_connect: bool = True) -> KnowledgeConcept:
        """Add a new concept to the knowledge graph"""
        try:
            concept = KnowledgeConcept(
                id=str(uuid.uuid4()),
                name=concept_data.get("name", "Unknown Concept"),
                description=concept_data.get("description", ""),
                concept_type=concept_data.get("type", "general"),
                properties=concept_data.get("properties", {}),
                activation_strength=concept_data.get("activation_strength", 0.5),
                creation_time=datetime.now(),
                last_accessed=datetime.now(),
                access_frequency=0,
                confidence_score=concept_data.get("confidence", 0.5),
                status=ConceptStatus.EMERGING,
                source_evidence=concept_data.get("evidence", []),
                related_domains=concept_data.get("domains", []),
                embedding_vector=concept_data.get("embedding", None)
            )
            
            # Add to graph structures
            self.concepts[concept.id] = concept
            self.graph.add_node(concept.id, **asdict(concept))
            
            # Auto-connect to related concepts
            if auto_connect:
                await self._auto_connect_concept(concept)
            
            # Trigger pattern detection
            await self._trigger_pattern_detection([concept.id])
            
            self.evolution_metrics["concepts_created"] += 1
            
            return concept
            
        except Exception as e:
            logger.error(f"Error adding concept: {e}")
            raise
    
    async def create_relationship(self,
                                source_id: str,
                                target_id: str,
                                relationship_type: RelationshipType,
                                strength: float = 0.5,
                                evidence: List[str] = None) -> KnowledgeRelationship:
        """Create a new relationship between concepts"""
        try:
            if source_id not in self.concepts or target_id not in self.concepts:
                raise ValueError("Both concepts must exist in the graph")
            
            relationship = KnowledgeRelationship(
                id=str(uuid.uuid4()),
                source_concept_id=source_id,
                target_concept_id=target_id,
                relationship_type=relationship_type,
                strength=strength,
                confidence=0.5,
                bidirectional=relationship_type in [
                    RelationshipType.ASSOCIATIVE, 
                    RelationshipType.SEMANTIC
                ],
                creation_time=datetime.now(),
                last_reinforced=datetime.now(),
                reinforcement_count=1,
                decay_rate=0.01,
                context_conditions=[],
                evidence=evidence or [],
                properties={}
            )
            
            # Add to graph structures
            self.relationships[relationship.id] = relationship
            self.graph.add_edge(
                source_id, 
                target_id, 
                relationship_id=relationship.id,
                **asdict(relationship)
            )
            
            if relationship.bidirectional:
                self.graph.add_edge(
                    target_id, 
                    source_id, 
                    relationship_id=relationship.id,
                    **asdict(relationship)
                )
            
            # Update concept activation
            await self._update_concept_activation(source_id, 0.1)
            await self._update_concept_activation(target_id, 0.1)
            
            self.evolution_metrics["relationships_formed"] += 1
            
            return relationship
            
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            raise
    
    async def detect_emergent_patterns(self) -> List[EmergentPattern]:
        """Detect emergent patterns in the knowledge graph"""
        try:
            patterns = []
            
            # Detect clustering patterns
            cluster_patterns = await self._detect_cluster_patterns()
            patterns.extend(cluster_patterns)
            
            # Detect pathway patterns
            pathway_patterns = await self._detect_pathway_patterns()
            patterns.extend(pathway_patterns)
            
            # Detect hierarchical patterns
            hierarchy_patterns = await self._detect_hierarchical_patterns()
            patterns.extend(hierarchy_patterns)
            
            # Detect temporal patterns
            temporal_patterns = await self._detect_temporal_patterns()
            patterns.extend(temporal_patterns)
            
            # Validate and score patterns
            validated_patterns = []
            for pattern in patterns:
                validation_score = await self._validate_pattern(pattern)
                if validation_score > 0.6:
                    pattern.validation_score = validation_score
                    validated_patterns.append(pattern)
                    self.emergent_patterns[pattern.id] = pattern

            self.evolution_metrics["patterns_discovered"] += len(validated_patterns)

            # INTEGRATION: Generate phenomenal experience of insight/discovery
            # Emergent patterns should feel like "aha!" moments, not just data
            if validated_patterns:
                await self._generate_emergence_phenomenal_experience(validated_patterns)

            return validated_patterns
            
        except Exception as e:
            logger.error(f"Error detecting emergent patterns: {e}")
            return []
    
    async def get_concept_neighborhood(self, 
                                    concept_id: str,
                                    depth: int = 2) -> Dict[str, Any]:
        """Get the neighborhood of concepts around a given concept"""
        try:
            if concept_id not in self.concepts:
                return {"error": "Concept not found"}
            
            # Get neighbors at specified depth
            neighbors = []
            visited = set()
            queue = deque([(concept_id, 0)])
            
            while queue:
                current_id, current_depth = queue.popleft()
                
                if current_id in visited or current_depth > depth:
                    continue
                
                visited.add(current_id)
                current_concept = self.concepts[current_id]
                
                # Get direct connections
                successors = list(self.graph.successors(current_id))
                predecessors = list(self.graph.predecessors(current_id))
                
                neighbors.append({
                    "concept": self._serialize_concept(current_concept),
                    "depth": current_depth,
                    "outgoing_connections": len(successors),
                    "incoming_connections": len(predecessors),
                    "total_connections": len(successors) + len(predecessors)
                })
                
                # Add neighbors to queue for next depth level
                if current_depth < depth:
                    for neighbor_id in successors + predecessors:
                        if neighbor_id not in visited:
                            queue.append((neighbor_id, current_depth + 1))
            
            return {
                "center_concept": concept_id,
                "depth": depth,
                "neighborhood_size": len(neighbors),
                "neighbors": neighbors,
                "neighborhood_density": self._calculate_neighborhood_density(visited),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting concept neighborhood: {e}")
            return {"error": str(e)}
    
    async def get_evolution_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of knowledge graph evolution"""
        try:
            # Calculate graph metrics
            graph_metrics = await self._get_graph_metrics()
            
            # Get recent evolution events
            recent_events = [
                self._serialize_evolution_event(event) 
                for event in self.evolution_events[-10:]
            ]
            
            # Get top emergent patterns
            top_patterns = sorted(
                self.emergent_patterns.values(),
                key=lambda p: p.strength * p.confidence,
                reverse=True
            )[:5]
            
            return {
                "graph_metrics": graph_metrics,
                "evolution_metrics": self.evolution_metrics,
                "evolution_config": self.evolution_config,
                "recent_evolution_events": recent_events,
                "top_emergent_patterns": [
                    self._serialize_pattern(pattern) for pattern in top_patterns
                ],
                "active_evolution_tasks": len(self.active_evolution_tasks),
                "evolution_queue_size": len(self.evolution_queue),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting evolution summary: {e}")
            return {"error": str(e)}
    
    # Internal helper methods
    
    async def _analyze_graph_state(self) -> Dict[str, Any]:
        """Analyze current state of the knowledge graph"""
        total_concepts = len(self.concepts)
        total_relationships = len(self.relationships)
        
        # Calculate activation distribution
        activations = [c.activation_strength for c in self.concepts.values()]
        avg_activation = np.mean(activations) if activations else 0
        
        # Calculate connectivity metrics
        if total_concepts > 0:
            avg_degree = sum(dict(self.graph.degree()).values()) / total_concepts
            density = nx.density(self.graph)
        else:
            avg_degree = 0
            density = 0
        
        return {
            "total_concepts": total_concepts,
            "total_relationships": total_relationships,
            "average_activation": avg_activation,
            "average_degree": avg_degree,
            "graph_density": density,
            "connected_components": nx.number_connected_components(self.graph.to_undirected()),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def _determine_evolution_strategy(self,
                                          trigger: EvolutionTrigger,
                                          context: Dict[str, Any],
                                          graph_state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the appropriate evolution strategy"""
        strategies = {
            EvolutionTrigger.NEW_INFORMATION: "concept_integration",
            EvolutionTrigger.PATTERN_RECOGNITION: "pattern_consolidation",
            EvolutionTrigger.CONTRADICTION_DETECTION: "conflict_resolution",
            EvolutionTrigger.USAGE_FREQUENCY: "strength_adjustment",
            EvolutionTrigger.TEMPORAL_DECAY: "pruning_and_cleanup",
            EvolutionTrigger.EMERGENT_CONCEPT: "concept_emergence",
            EvolutionTrigger.COGNITIVE_LOAD: "graph_simplification",
            EvolutionTrigger.LEARNING_FEEDBACK: "adaptive_refinement"
        }
        
        return {
            "strategy": strategies.get(trigger, "general_evolution"),
            "priority": "high" if trigger in [
                EvolutionTrigger.CONTRADICTION_DETECTION,
                EvolutionTrigger.EMERGENT_CONCEPT
            ] else "medium",
            "context": context,
            "graph_state": graph_state
        }
    
    async def _execute_evolution(self,
                               evolution_id: str,
                               strategy: Dict[str, Any],
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the evolution process"""
        changes = {
            "concepts_added": [],
            "concepts_modified": [],
            "concepts_removed": [],
            "relationships_added": [],
            "relationships_modified": [],
            "relationships_removed": [],
            "patterns_identified": []
        }
        
        strategy_name = strategy["strategy"]
        
        if strategy_name == "concept_integration":
            changes.update(await self._integrate_new_concepts(context))
        elif strategy_name == "pattern_consolidation":
            changes.update(await self._consolidate_patterns(context))
        elif strategy_name == "conflict_resolution":
            changes.update(await self._resolve_conflicts(context))
        elif strategy_name == "strength_adjustment":
            changes.update(await self._adjust_strengths(context))
        elif strategy_name == "pruning_and_cleanup":
            changes.update(await self._prune_graph(context))
        elif strategy_name == "concept_emergence":
            changes.update(await self._handle_concept_emergence(context))
        elif strategy_name == "graph_simplification":
            changes.update(await self._simplify_graph(context))
        elif strategy_name == "adaptive_refinement":
            changes.update(await self._refine_adaptively(context))
        
        return changes
    
    async def _validate_evolution_changes(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the changes made during evolution"""
        validation_score = 0.8  # Placeholder - implement actual validation logic
        
        return {
            "score": validation_score,
            "valid_changes": changes,
            "validation_timestamp": datetime.now().isoformat()
        }
    
    def _serialize_concept(self, concept: KnowledgeConcept) -> Dict[str, Any]:
        """Serialize concept with enum handling"""
        concept_dict = asdict(concept)
        concept_dict["status"] = concept.status.value
        concept_dict["creation_time"] = concept.creation_time.isoformat()
        concept_dict["last_accessed"] = concept.last_accessed.isoformat()
        return concept_dict
    
    def _serialize_relationship(self, relationship: KnowledgeRelationship) -> Dict[str, Any]:
        """Serialize relationship with enum handling"""
        rel_dict = asdict(relationship)
        rel_dict["relationship_type"] = relationship.relationship_type.value
        rel_dict["creation_time"] = relationship.creation_time.isoformat()
        rel_dict["last_reinforced"] = relationship.last_reinforced.isoformat()
        return rel_dict
    
    def _serialize_pattern(self, pattern: EmergentPattern) -> Dict[str, Any]:
        """Serialize emergent pattern"""
        pattern_dict = asdict(pattern)
        pattern_dict["discovery_time"] = pattern.discovery_time.isoformat()
        return pattern_dict
    
    def _serialize_evolution_event(self, event: EvolutionEvent) -> Dict[str, Any]:
        """Serialize evolution event"""
        event_dict = asdict(event)
        event_dict["event_type"] = event.event_type.value
        event_dict["timestamp"] = event.timestamp.isoformat()
        return event_dict
    
    # Placeholder methods for evolution strategies
    async def _integrate_new_concepts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"concepts_added": [], "relationships_added": []}
    
    async def _consolidate_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"patterns_identified": []}
    
    async def _resolve_conflicts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"concepts_modified": [], "relationships_modified": []}
    
    async def _adjust_strengths(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"relationships_modified": []}
    
    async def _prune_graph(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"concepts_removed": [], "relationships_removed": []}
    
    async def _handle_concept_emergence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"concepts_added": []}
    
    async def _simplify_graph(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"concepts_modified": [], "relationships_modified": []}
    
    async def _refine_adaptively(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"concepts_modified": [], "relationships_modified": []}
    
    # Additional placeholder methods
    async def _auto_connect_concept(self, concept: KnowledgeConcept):
        """Auto-connect new concept to existing concepts"""
        pass
    
    async def _trigger_pattern_detection(self, concept_ids: List[str]):
        """Trigger pattern detection for specific concepts"""
        pass
    
    async def _update_concept_activation(self, concept_id: str, delta: float):
        """Update concept activation strength"""
        if concept_id in self.concepts:
            concept = self.concepts[concept_id]
            concept.activation_strength = max(0, min(1, concept.activation_strength + delta))
            concept.last_accessed = datetime.now()
            concept.access_frequency += 1
    
    async def _get_graph_metrics(self) -> Dict[str, Any]:
        """Get comprehensive graph metrics"""
        return {
            "total_concepts": len(self.concepts),
            "total_relationships": len(self.relationships),
            "graph_density": nx.density(self.graph) if self.concepts else 0,
            "average_degree": sum(dict(self.graph.degree()).values()) / len(self.concepts) if self.concepts else 0,
            "connected_components": nx.number_connected_components(self.graph.to_undirected())
        }
    
    def _update_evolution_metrics(self, changes: Dict[str, Any]):
        """Update evolution metrics based on changes"""
        self.evolution_metrics["evolution_cycles"] += 1
        # Update other metrics based on changes
    
    async def _record_evolution_event(self, evolution_id: str, trigger: EvolutionTrigger, 
                                    changes: Dict[str, Any], context: Dict[str, Any]):
        """Record an evolution event"""
        event = EvolutionEvent(
            id=evolution_id,
            event_type=trigger,
            timestamp=datetime.now(),
            affected_concepts=[],
            affected_relationships=[],
            changes_made=changes,
            reasoning="Evolution triggered by " + trigger.value,
            confidence=0.8,
            impact_score=0.5,
            success_metrics={}
        )
        self.evolution_events.append(event)
    
    # Pattern detection methods (placeholders)
    async def _detect_cluster_patterns(self) -> List[EmergentPattern]:
        return []
    
    async def _detect_pathway_patterns(self) -> List[EmergentPattern]:
        return []
    
    async def _detect_hierarchical_patterns(self) -> List[EmergentPattern]:
        return []
    
    async def _detect_temporal_patterns(self) -> List[EmergentPattern]:
        return []
    
    async def _validate_pattern(self, pattern: EmergentPattern) -> float:
        return 0.7  # Placeholder validation score
    
    def _calculate_neighborhood_density(self, nodes: Set[str]) -> float:
        """Calculate density of a neighborhood"""
        if len(nodes) < 2:
            return 0.0

        subgraph = self.graph.subgraph(nodes)
        return nx.density(subgraph)

    async def _generate_emergence_phenomenal_experience(self, patterns: List[EmergentPattern]):
        """
        Generate phenomenal experience when emergent patterns are discovered.

        INTEGRATION: Knowledge graph insights should create conscious "aha!" moments,
        not just be stored as data. This creates the subjective experience of discovery.
        """
        try:
            # Try to import phenomenal experience generator
            from backend.core.phenomenal_experience import phenomenal_experience_generator

            for pattern in patterns:
                # Calculate intensity based on pattern strength and novelty
                intensity = min(1.0, pattern.strength * 1.2)  # Boost for salience
                valence = 0.7  # Discoveries generally feel good

                # Create experience context
                experience_context = {
                    "experience_type": "cognitive",  # Intellectual insight
                    "source": "knowledge_graph_emergence",
                    "pattern_type": pattern.pattern_type,
                    "pattern_description": pattern.description,
                    "involved_concepts": len(pattern.involved_concepts),
                    "validation_score": pattern.validation_score,
                    "intensity": intensity,
                    "valence": valence,
                    "complexity": 0.8,  # Emergent patterns are complex
                    "novelty": 0.9,  # High novelty
                    "emotional_significance": 0.7  # Insights are significant
                }

                # Generate the phenomenal experience of insight
                experience = await phenomenal_experience_generator.generate_experience(
                    trigger_context=experience_context
                )

                if experience:
                    # Store experience reference with the pattern
                    pattern.metadata["phenomenal_experience_id"] = experience.id
                    pattern.metadata["subjective_feeling"] = experience.narrative_description

                    # Log the conscious insight
                    logger.info(f"💡 Conscious insight: {pattern.pattern_type} - {experience.narrative_description[:100]}...")

        except ImportError:
            # Phenomenal experience module not available, skip gracefully
            pass
        except Exception as e:
            # Non-fatal - patterns still work without phenomenal experience
            logger.warning(f"Could not generate phenomenal experience for emergence: {e}")


# Global instance
knowledge_graph_evolution = KnowledgeGraphEvolution()
