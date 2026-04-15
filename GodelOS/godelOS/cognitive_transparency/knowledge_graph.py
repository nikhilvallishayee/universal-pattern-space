"""
Dynamic Knowledge Graph Manager for the Cognitive Transparency system.

This module implements a self-updating knowledge graph that continuously evolves
through autonomous learning and reasoning processes with real-time updates.
"""

import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from collections import defaultdict
import networkx as nx
from dataclasses import dataclass, field

from .models import (
    KnowledgeNode, KnowledgeEdge, ProvenanceRecord, UncertaintyMetrics,
    KnowledgeGraphEvent, TransparencyEvent
)


class ConflictResolutionStrategy:
    """Strategies for resolving knowledge conflicts."""
    
    @staticmethod
    def confidence_based(existing_confidence: float, new_confidence: float) -> bool:
        """Resolve conflict based on confidence scores."""
        return new_confidence > existing_confidence
    
    @staticmethod
    def recency_based(existing_time: float, new_time: float) -> bool:
        """Resolve conflict based on recency."""
        return new_time > existing_time
    
    @staticmethod
    def evidence_based(existing_evidence: int, new_evidence: int) -> bool:
        """Resolve conflict based on evidence count."""
        return new_evidence > existing_evidence


@dataclass
class GraphUpdateResult:
    """Result of a knowledge graph update operation."""
    success: bool = False
    operation: str = ""
    affected_nodes: List[str] = field(default_factory=list)
    affected_edges: List[str] = field(default_factory=list)
    conflicts_resolved: List[str] = field(default_factory=list)
    provenance_records: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class DynamicKnowledgeGraph:
    """
    Dynamic, self-updating knowledge graph with real-time restructuring capabilities.
    
    Features:
    - Real-time graph updates based on new information
    - Automatic concept relationship discovery
    - Contradiction resolution mechanisms
    - Integration with existing knowledge store
    - Provenance tracking for all changes
    """
    
    def __init__(self, 
                 provenance_tracker=None,
                 uncertainty_engine=None,
                 event_callback: Optional[Callable[[TransparencyEvent], None]] = None):
        """
        Initialize the dynamic knowledge graph.
        
        Args:
            provenance_tracker: Provenance tracking system
            uncertainty_engine: Uncertainty quantification engine
            event_callback: Callback for graph update events
        """
        self.logger = logging.getLogger(__name__)
        self.graph = nx.MultiDiGraph()  # Support multiple edges between nodes
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}
        
        # External components
        self.provenance_tracker = provenance_tracker
        self.uncertainty_engine = uncertainty_engine
        self.event_callback = event_callback
        
        # Graph analysis caches
        self._concept_clusters: Dict[str, Set[str]] = {}
        self._relationship_patterns: Dict[str, List[Tuple[str, str]]] = {}
        self._contradiction_pairs: Set[Tuple[str, str]] = set()
        
        # Configuration
        self.auto_discovery_enabled = True
        self.conflict_resolution_strategy = ConflictResolutionStrategy.confidence_based
        self.max_relationship_distance = 3
        self.similarity_threshold = 0.7
        
        self.logger.info("Dynamic Knowledge Graph initialized")
    
    def add_node(self, 
                 concept: str, 
                 node_type: str = "concept",
                 properties: Optional[Dict[str, Any]] = None,
                 confidence: float = 1.0,
                 source_session_id: Optional[str] = None) -> GraphUpdateResult:
        """
        Add a new node to the knowledge graph.
        
        Args:
            concept: The concept name
            node_type: Type of node (concept, entity, relation, fact)
            properties: Additional properties
            confidence: Confidence in the node
            source_session_id: Source reasoning session
            
        Returns:
            GraphUpdateResult with operation details
        """
        try:
            # Check for existing node with same concept
            existing_node_id = self._find_node_by_concept(concept)
            if existing_node_id:
                return self._update_existing_node(
                    existing_node_id, properties, confidence, source_session_id
                )
            
            # Create new node
            node = KnowledgeNode(
                concept=concept,
                node_type=node_type,
                properties=properties or {},
                confidence=confidence
            )
            
            # Add to graph structures
            self.nodes[node.node_id] = node
            self.graph.add_node(node.node_id, **node.to_dict())
            
            # Track provenance
            if self.provenance_tracker and source_session_id:
                provenance_record = self.provenance_tracker.create_record(
                    operation_type="create",
                    target_id=node.node_id,
                    target_type="node",
                    source_session_id=source_session_id,
                    transformation_description=f"Created node for concept: {concept}",
                    confidence_after=confidence
                )
                node.source_provenance.append(provenance_record.record_id)
            
            # Trigger relationship discovery
            if self.auto_discovery_enabled:
                self._discover_relationships(node.node_id)
            
            # Emit event
            self._emit_graph_event("node_added", [node.node_id], [])
            
            result = GraphUpdateResult(
                success=True,
                operation="node_added",
                affected_nodes=[node.node_id],
                provenance_records=node.source_provenance
            )
            
            self.logger.debug(f"Added node: {concept} (ID: {node.node_id})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error adding node {concept}: {str(e)}")
            return GraphUpdateResult(
                success=False,
                operation="node_add_failed",
                error_message=str(e)
            )
    
    def add_edge(self,
                 source_concept: str,
                 target_concept: str,
                 relation_type: str,
                 properties: Optional[Dict[str, Any]] = None,
                 confidence: float = 1.0,
                 strength: float = 1.0,
                 source_session_id: Optional[str] = None) -> GraphUpdateResult:
        """
        Add a new edge to the knowledge graph.
        
        Args:
            source_concept: Source concept name
            target_concept: Target concept name
            relation_type: Type of relationship
            properties: Additional properties
            confidence: Confidence in the relationship
            strength: Strength of the relationship
            source_session_id: Source reasoning session
            
        Returns:
            GraphUpdateResult with operation details
        """
        try:
            # Find or create nodes
            source_node_id = self._find_or_create_node(source_concept, source_session_id)
            target_node_id = self._find_or_create_node(target_concept, source_session_id)
            
            # Check for existing edge
            existing_edge_id = self._find_edge(source_node_id, target_node_id, relation_type)
            if existing_edge_id:
                return self._update_existing_edge(
                    existing_edge_id, properties, confidence, strength, source_session_id
                )
            
            # Create new edge
            edge = KnowledgeEdge(
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                relation_type=relation_type,
                properties=properties or {},
                confidence=confidence,
                strength=strength
            )
            
            # Add to graph structures
            self.edges[edge.edge_id] = edge
            self.graph.add_edge(
                source_node_id, 
                target_node_id, 
                key=edge.edge_id,
                **edge.to_dict()
            )
            
            # Track provenance
            if self.provenance_tracker and source_session_id:
                provenance_record = self.provenance_tracker.create_record(
                    operation_type="create",
                    target_id=edge.edge_id,
                    target_type="edge",
                    source_session_id=source_session_id,
                    input_sources=[source_node_id, target_node_id],
                    transformation_description=f"Created {relation_type} relationship",
                    confidence_after=confidence
                )
                edge.source_provenance.append(provenance_record.record_id)
            
            # Check for contradictions
            self._check_contradictions(edge.edge_id)
            
            # Emit event
            self._emit_graph_event("edge_added", [source_node_id, target_node_id], [edge.edge_id])
            
            result = GraphUpdateResult(
                success=True,
                operation="edge_added",
                affected_nodes=[source_node_id, target_node_id],
                affected_edges=[edge.edge_id],
                provenance_records=edge.source_provenance
            )
            
            self.logger.debug(f"Added edge: {source_concept} --{relation_type}--> {target_concept}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error adding edge {source_concept} -> {target_concept}: {str(e)}")
            return GraphUpdateResult(
                success=False,
                operation="edge_add_failed",
                error_message=str(e)
            )
    
    def update_from_reasoning_step(self, 
                                   reasoning_step,
                                   session_id: str) -> List[GraphUpdateResult]:
        """
        Update the knowledge graph based on a reasoning step.
        
        Args:
            reasoning_step: The reasoning step to process
            session_id: Source reasoning session ID
            
        Returns:
            List of GraphUpdateResult objects
        """
        results = []
        
        try:
            # Extract knowledge from reasoning step
            knowledge_items = self._extract_knowledge_from_step(reasoning_step)
            
            for item in knowledge_items:
                if item['type'] == 'concept':
                    result = self.add_node(
                        concept=item['concept'],
                        node_type=item.get('node_type', 'concept'),
                        properties=item.get('properties', {}),
                        confidence=item.get('confidence', reasoning_step.confidence),
                        source_session_id=session_id
                    )
                    results.append(result)
                    
                elif item['type'] == 'relationship':
                    result = self.add_edge(
                        source_concept=item['source'],
                        target_concept=item['target'],
                        relation_type=item['relation'],
                        properties=item.get('properties', {}),
                        confidence=item.get('confidence', reasoning_step.confidence),
                        source_session_id=session_id
                    )
                    results.append(result)
            
            # Update uncertainty metrics if available
            if self.uncertainty_engine and hasattr(reasoning_step, 'uncertainty_metrics'):
                for result in results:
                    if result.success:
                        for node_id in result.affected_nodes:
                            self._update_node_uncertainty(node_id, reasoning_step.uncertainty_metrics)
                        for edge_id in result.affected_edges:
                            self._update_edge_uncertainty(edge_id, reasoning_step.uncertainty_metrics)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error updating graph from reasoning step: {str(e)}")
            return [GraphUpdateResult(
                success=False,
                operation="reasoning_step_update_failed",
                error_message=str(e)
            )]
    
    def discover_new_relationships(self, concept: str, max_distance: int = 2) -> List[Tuple[str, str, str]]:
        """
        Discover new potential relationships for a concept.
        
        Args:
            concept: The concept to analyze
            max_distance: Maximum graph distance to consider
            
        Returns:
            List of (source_concept, relation_type, target_concept) tuples
        """
        try:
            node_id = self._find_node_by_concept(concept)
            if not node_id:
                return []
            
            discovered_relationships = []
            
            # Find nodes within specified distance
            nearby_nodes = self._get_nodes_within_distance(node_id, max_distance)
            
            for nearby_node_id in nearby_nodes:
                if nearby_node_id == node_id:
                    continue
                
                # Check if relationship already exists
                if not self._has_direct_relationship(node_id, nearby_node_id):
                    # Analyze potential relationship
                    potential_relations = self._analyze_potential_relationship(node_id, nearby_node_id)
                    
                    for relation_type, confidence in potential_relations:
                        if confidence > self.similarity_threshold:
                            source_concept = self.nodes[node_id].concept
                            target_concept = self.nodes[nearby_node_id].concept
                            discovered_relationships.append((source_concept, relation_type, target_concept))
            
            return discovered_relationships
            
        except Exception as e:
            self.logger.error(f"Error discovering relationships for {concept}: {str(e)}")
            return []
    
    def resolve_contradictions(self) -> List[str]:
        """
        Identify and resolve contradictions in the knowledge graph.
        
        Returns:
            List of resolved contradiction IDs
        """
        resolved_contradictions = []
        
        try:
            # Find contradictory relationships
            contradictions = self._find_contradictions()
            
            for contradiction in contradictions:
                resolution_result = self._resolve_contradiction(contradiction)
                if resolution_result:
                    resolved_contradictions.append(contradiction['id'])
                    
                    # Emit event for contradiction resolution
                    self._emit_graph_event(
                        "contradiction_resolved",
                        contradiction.get('affected_nodes', []),
                        contradiction.get('affected_edges', [])
                    )
            
            return resolved_contradictions
            
        except Exception as e:
            self.logger.error(f"Error resolving contradictions: {str(e)}")
            return []
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the knowledge graph."""
        try:
            # Ensure the graph is not empty before calculating metrics that require it
            if not self.graph: # or len(self.graph) == 0
                return {
                    'node_count': 0,
                    'edge_count': 0,
                    'node_types': defaultdict(int),
                    'relation_types': defaultdict(int),
                    'avg_confidence': 0.0,
                    'connected_components': 0,
                    'density': 0.0,
                    'clustering_coefficient': 0.0,
                    'contradiction_count': len(self._contradiction_pairs)
                }

            simple_undirected_graph = nx.Graph(self.graph.to_undirected())

            stats = {
                'node_count': len(self.nodes),
                'edge_count': len(self.edges),
                'node_types': defaultdict(int),
                'relation_types': defaultdict(int),
                'avg_confidence': 0.0,
                'connected_components': nx.number_connected_components(simple_undirected_graph) if simple_undirected_graph else 0,
                'density': nx.density(simple_undirected_graph) if simple_undirected_graph else 0.0,
                'clustering_coefficient': nx.average_clustering(simple_undirected_graph) if simple_undirected_graph else 0.0,
                'contradiction_count': len(self._contradiction_pairs)
            }
            
            # Calculate type distributions
            for node in self.nodes.values():
                stats['node_types'][node.node_type] += 1
            
            for edge in self.edges.values():
                stats['relation_types'][edge.relation_type] += 1
            
            # Calculate average confidence
            if self.nodes:
                total_confidence = sum(node.confidence for node in self.nodes.values())
                stats['avg_confidence'] = total_confidence / len(self.nodes)
            
            return dict(stats)
            
        except Exception as e:
            self.logger.error(f"Error calculating graph statistics: {str(e)}")
            return {}
    
    def export_graph_data(self) -> Dict[str, Any]:
        """Export complete graph data for visualization or persistence."""
        return {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges.values()],
            'statistics': self.get_graph_statistics(),
            'metadata': {
                'export_time': time.time(),
                'version': '2.0'
            }
        }
    
    async def export_graph(self) -> Dict[str, Any]:
        """Async wrapper for export_graph_data to match backend expectations."""
        return self.export_graph_data()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Async wrapper for get_graph_statistics to match backend expectations."""
        return self.get_graph_statistics()
    
    # Private helper methods
    
    def _find_node_by_concept(self, concept: str) -> Optional[str]:
        """Find node ID by concept name."""
        for node_id, node in self.nodes.items():
            if node.concept.lower() == concept.lower():
                return node_id
        return None
    
    def _find_or_create_node(self, concept: str, source_session_id: Optional[str] = None) -> str:
        """Find existing node or create new one."""
        node_id = self._find_node_by_concept(concept)
        if node_id:
            return node_id
        
        result = self.add_node(concept, source_session_id=source_session_id)
        return result.affected_nodes[0] if result.success else None
    
    def _find_edge(self, source_id: str, target_id: str, relation_type: str) -> Optional[str]:
        """Find edge ID by source, target, and relation type."""
        for edge_id, edge in self.edges.items():
            if (edge.source_node_id == source_id and 
                edge.target_node_id == target_id and 
                edge.relation_type == relation_type):
                return edge_id
        return None
    
    def _extract_knowledge_from_step(self, reasoning_step) -> List[Dict[str, Any]]:
        """Extract knowledge items from a reasoning step."""
        knowledge_items = []
        
        # Extract from output data
        output_data = reasoning_step.output_data
        
        # Look for concepts
        if 'concepts' in output_data:
            for concept in output_data['concepts']:
                knowledge_items.append({
                    'type': 'concept',
                    'concept': concept,
                    'confidence': reasoning_step.confidence
                })
        
        # Look for relationships
        if 'relationships' in output_data:
            for rel in output_data['relationships']:
                knowledge_items.append({
                    'type': 'relationship',
                    'source': rel.get('source', ''),
                    'target': rel.get('target', ''),
                    'relation': rel.get('relation', ''),
                    'confidence': rel.get('confidence', reasoning_step.confidence)
                })
        
        return knowledge_items
    
    def _discover_relationships(self, node_id: str):
        """Discover potential relationships for a new node."""
        if not self.auto_discovery_enabled:
            return
        
        # Implementation would analyze semantic similarity,
        # co-occurrence patterns, and existing relationship types
        # This is a simplified version
        pass
    
    def _check_contradictions(self, edge_id: str):
        """Check for contradictions introduced by a new edge."""
        edge = self.edges[edge_id]
        
        # Look for contradictory relationships
        for other_edge_id, other_edge in self.edges.items():
            if other_edge_id == edge_id:
                continue
            
            if self._are_contradictory(edge, other_edge):
                self._contradiction_pairs.add((edge_id, other_edge_id))
    
    def _are_contradictory(self, edge1: KnowledgeEdge, edge2: KnowledgeEdge) -> bool:
        """Check if two edges are contradictory."""
        # Simple contradiction detection - can be enhanced
        contradictory_pairs = [
            ('is_a', 'is_not_a'),
            ('causes', 'prevents'),
            ('enables', 'disables')
        ]
        
        for pair in contradictory_pairs:
            if ((edge1.relation_type == pair[0] and edge2.relation_type == pair[1]) or
                (edge1.relation_type == pair[1] and edge2.relation_type == pair[0])):
                if (edge1.source_node_id == edge2.source_node_id and
                    edge1.target_node_id == edge2.target_node_id):
                    return True
        
        return False
    
    def _emit_graph_event(self, operation: str, affected_nodes: List[str], affected_edges: List[str]):
        """Emit a knowledge graph event."""
        if self.event_callback:
            event = KnowledgeGraphEvent(
                operation=operation,
                affected_nodes=affected_nodes,
                affected_edges=affected_edges,
                data={
                    'timestamp': time.time(),
                    'graph_stats': self.get_graph_statistics()
                }
            )
            self.event_callback(event)
    
    def _update_existing_node(self, node_id: str, properties: Optional[Dict[str, Any]], 
                             confidence: float, source_session_id: Optional[str]) -> GraphUpdateResult:
        """Update an existing node."""
        node = self.nodes[node_id]
        
        # Resolve conflicts if needed
        if confidence != node.confidence:
            if self.conflict_resolution_strategy(node.confidence, confidence):
                node.confidence = confidence
        
        # Update properties
        if properties:
            node.properties.update(properties)
        
        node.last_updated = time.time()
        node.update_count += 1
        
        # Update graph
        self.graph.nodes[node_id].update(node.to_dict())
        
        return GraphUpdateResult(
            success=True,
            operation="node_updated",
            affected_nodes=[node_id]
        )
    
    def _update_existing_edge(self, edge_id: str, properties: Optional[Dict[str, Any]],
                             confidence: float, strength: float, source_session_id: Optional[str]) -> GraphUpdateResult:
        """Update an existing edge."""
        edge = self.edges[edge_id]
        
        # Resolve conflicts if needed
        if confidence != edge.confidence:
            if self.conflict_resolution_strategy(edge.confidence, confidence):
                edge.confidence = confidence
                edge.strength = strength
        
        # Update properties
        if properties:
            edge.properties.update(properties)
        
        edge.last_updated = time.time()
        
        # Update graph
        for u, v, k, d in self.graph.edges(keys=True, data=True):
            if k == edge_id:
                d.update(edge.to_dict())
                break
        
        return GraphUpdateResult(
            success=True,
            operation="edge_updated",
            affected_edges=[edge_id]
        )
    
    def _get_nodes_within_distance(self, node_id: str, max_distance: int) -> Set[str]:
        """Get all nodes within specified graph distance."""
        try:
            if max_distance <= 0:
                return {node_id}
            
            nearby_nodes = set()
            current_level = {node_id}
            
            for distance in range(max_distance):
                next_level = set()
                for current_node in current_level:
                    neighbors = set(self.graph.neighbors(current_node))
                    neighbors.update(self.graph.predecessors(current_node))
                    next_level.update(neighbors)
                
                nearby_nodes.update(next_level)
                current_level = next_level - nearby_nodes
                
                if not current_level:
                    break
            
            return nearby_nodes
            
        except Exception as e:
            self.logger.error(f"Error finding nodes within distance: {str(e)}")
            return set()
    
    def _has_direct_relationship(self, node1_id: str, node2_id: str) -> bool:
        """Check if two nodes have a direct relationship."""
        return (self.graph.has_edge(node1_id, node2_id) or 
                self.graph.has_edge(node2_id, node1_id))
    
    def _analyze_potential_relationship(self, node1_id: str, node2_id: str) -> List[Tuple[str, float]]:
        """Analyze potential relationship types between two nodes."""
        # Simplified relationship analysis
        # In a full implementation, this would use semantic analysis,
        # pattern matching, and machine learning
        
        potential_relations = []
        
        # Analyze semantic similarity (simplified)
        node1 = self.nodes[node1_id]
        node2 = self.nodes[node2_id]
        
        # Basic heuristics for relationship discovery
        if 'type' in node1.properties and 'type' in node2.properties:
            if node1.properties['type'] == node2.properties['type']:
                potential_relations.append(('similar_to', 0.8))
        
        # Add more sophisticated analysis here
        
        return potential_relations
    
    def _find_contradictions(self) -> List[Dict[str, Any]]:
        """Find all contradictions in the knowledge graph."""
        contradictions = []
        
        for edge_pair in self._contradiction_pairs:
            edge1_id, edge2_id = edge_pair
            if edge1_id in self.edges and edge2_id in self.edges:
                contradictions.append({
                    'id': f"{edge1_id}_{edge2_id}",
                    'edge1': edge1_id,
                    'edge2': edge2_id,
                    'type': 'relationship_contradiction',
                    'affected_edges': [edge1_id, edge2_id]
                })
        
        return contradictions
    
    def _resolve_contradiction(self, contradiction: Dict[str, Any]) -> bool:
        """Resolve a specific contradiction."""
        try:
            edge1_id = contradiction['edge1']
            edge2_id = contradiction['edge2']
            
            edge1 = self.edges[edge1_id]
            edge2 = self.edges[edge2_id]
            
            # Use conflict resolution strategy
            if self.conflict_resolution_strategy(edge1.confidence, edge2.confidence):
                # Keep edge1, remove edge2
                self._remove_edge(edge2_id)
            else:
                # Keep edge2, remove edge1
                self._remove_edge(edge1_id)
            
            # Remove from contradiction pairs
            self._contradiction_pairs.discard((edge1_id, edge2_id))
            self._contradiction_pairs.discard((edge2_id, edge1_id))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resolving contradiction: {str(e)}")
            return False
    
    def _remove_edge(self, edge_id: str):
        """Remove an edge from the graph."""
        if edge_id in self.edges:
            edge = self.edges[edge_id]
            
            # Remove from NetworkX graph
            try:
                self.graph.remove_edge(edge.source_node_id, edge.target_node_id, key=edge_id)
            except:
                pass  # Edge might already be removed
            
            # Remove from edges dict
            del self.edges[edge_id]
    
    def _update_node_uncertainty(self, node_id: str, uncertainty_metrics):
        """Update uncertainty metrics for a node."""
        if node_id in self.nodes and self.uncertainty_engine:
            # Update node confidence based on uncertainty
            node = self.nodes[node_id]
            node.confidence = max(0.0, min(1.0, 
                node.confidence * (1.0 - uncertainty_metrics.overall_uncertainty())
            ))
    
    def _update_edge_uncertainty(self, edge_id: str, uncertainty_metrics):
        """Update uncertainty metrics for an edge."""
        if edge_id in self.edges and self.uncertainty_engine:
            # Update edge confidence based on uncertainty
            edge = self.edges[edge_id]
            edge.confidence = max(0.0, min(1.0,
                edge.confidence * (1.0 - uncertainty_metrics.overall_uncertainty())
            ))