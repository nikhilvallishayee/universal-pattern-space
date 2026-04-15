"""
Provenance Tracking System for the Cognitive Transparency system.

This module provides comprehensive cognitive auditability for all knowledge updates,
reasoning step provenance chains, and temporal versioning of knowledge changes.
"""

import logging
import time
import json
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum

from .models import (
    ProvenanceRecord, ReasoningStep, KnowledgeNode, KnowledgeEdge,
    ProvenanceEvent, TransparencyEvent
)


class ProvenanceQueryType(Enum):
    """Types of provenance queries."""
    FORWARD_TRACE = "forward_trace"  # What was derived from this?
    BACKWARD_TRACE = "backward_trace"  # What led to this?
    INFLUENCE_ANALYSIS = "influence_analysis"  # What influenced this decision?
    DEPENDENCY_GRAPH = "dependency_graph"  # Full dependency structure
    TEMPORAL_EVOLUTION = "temporal_evolution"  # How did this evolve over time?


@dataclass
class ProvenanceChain:
    """Represents a chain of provenance records."""
    chain_id: str = field(default_factory=lambda: f"chain_{int(time.time())}")
    records: List[ProvenanceRecord] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    chain_type: str = "reasoning"  # reasoning, learning, inference, revision
    confidence_evolution: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'chain_id': self.chain_id,
            'records': [record.to_dict() for record in self.records],
            'start_time': self.start_time,
            'end_time': self.end_time,
            'chain_type': self.chain_type,
            'confidence_evolution': self.confidence_evolution
        }


@dataclass
class ProvenanceSnapshot:
    """Represents a snapshot of knowledge state at a specific time."""
    snapshot_id: str = field(default_factory=lambda: f"snapshot_{int(time.time())}")
    timestamp: float = field(default_factory=time.time)
    knowledge_state: Dict[str, Any] = field(default_factory=dict)
    active_sessions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProvenanceTracker:
    """
    Comprehensive provenance tracking system for cognitive transparency.
    
    Features:
    - Full cognitive auditability for all knowledge updates
    - Reasoning step provenance chains
    - Knowledge source tracking and attribution
    - Temporal versioning of knowledge changes
    - Rollback capabilities for knowledge updates
    """
    
    def __init__(self, 
                 max_history_size: int = 10000,
                 snapshot_interval: int = 3600,  # 1 hour
                 event_callback: Optional[callable] = None):
        """
        Initialize the provenance tracker.
        
        Args:
            max_history_size: Maximum number of provenance records to keep
            snapshot_interval: Interval between automatic snapshots (seconds)
            event_callback: Callback for provenance events
        """
        self.logger = logging.getLogger(__name__)
        
        # Core storage
        self.records: Dict[str, ProvenanceRecord] = {}
        self.chains: Dict[str, ProvenanceChain] = {}
        self.snapshots: Dict[str, ProvenanceSnapshot] = {}
        
        # Indexing for efficient queries
        self.target_index: Dict[str, Set[str]] = defaultdict(set)  # target_id -> record_ids
        self.session_index: Dict[str, Set[str]] = defaultdict(set)  # session_id -> record_ids
        self.temporal_index: List[Tuple[float, str]] = []  # (timestamp, record_id)
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)  # target_id -> dependencies
        
        # Configuration
        self.max_history_size = max_history_size
        self.snapshot_interval = snapshot_interval
        self.event_callback = event_callback
        self.auto_snapshot_enabled = True
        
        # State tracking
        self.last_snapshot_time = time.time()
        self.active_chains: Dict[str, str] = {}  # session_id -> chain_id
        
        self.logger.info("Provenance Tracker initialized")
    
    def create_record(self,
                     operation_type: str,
                     target_id: str,
                     target_type: str,
                     source_reasoning_step_id: Optional[str] = None,
                     source_session_id: Optional[str] = None,
                     input_sources: Optional[List[str]] = None,
                     transformation_description: str = "",
                     confidence_before: Optional[float] = None,
                     confidence_after: Optional[float] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> ProvenanceRecord:
        """
        Create a new provenance record.
        
        Args:
            operation_type: Type of operation (create, update, delete, infer, revise)
            target_id: ID of the target knowledge item
            target_type: Type of target (node, edge, fact, rule)
            source_reasoning_step_id: ID of the reasoning step that caused this
            source_session_id: ID of the reasoning session
            input_sources: List of input knowledge item IDs
            transformation_description: Description of the transformation
            confidence_before: Confidence before the operation
            confidence_after: Confidence after the operation
            metadata: Additional metadata
            
        Returns:
            ProvenanceRecord object
        """
        try:
            record = ProvenanceRecord(
                operation_type=operation_type,
                target_id=target_id,
                target_type=target_type,
                source_reasoning_step_id=source_reasoning_step_id,
                source_session_id=source_session_id,
                input_sources=input_sources or [],
                transformation_description=transformation_description,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                metadata=metadata or {}
            )
            
            # Store record
            self.records[record.record_id] = record
            
            # Update indices
            self._update_indices(record)
            
            # Add to active chain if session is active
            if source_session_id and source_session_id in self.active_chains:
                chain_id = self.active_chains[source_session_id]
                if chain_id in self.chains:
                    self.chains[chain_id].records.append(record)
                    if confidence_after is not None:
                        self.chains[chain_id].confidence_evolution.append(confidence_after)
            
            # Emit event
            self._emit_provenance_event(record)
            
            # Check if we need to create a snapshot
            if self.auto_snapshot_enabled:
                self._check_snapshot_needed()
            
            # Cleanup old records if needed
            self._cleanup_old_records()
            
            self.logger.debug(f"Created provenance record: {record.record_id}")
            return record
            
        except Exception as e:
            self.logger.error(f"Error creating provenance record: {str(e)}")
            raise
    
    def start_chain(self, 
                   session_id: str, 
                   chain_type: str = "reasoning") -> str:
        """
        Start a new provenance chain for a session.
        
        Args:
            session_id: ID of the reasoning session
            chain_type: Type of chain (reasoning, learning, inference, revision)
            
        Returns:
            Chain ID
        """
        try:
            chain = ProvenanceChain(chain_type=chain_type)
            self.chains[chain.chain_id] = chain
            self.active_chains[session_id] = chain.chain_id
            
            self.logger.debug(f"Started provenance chain: {chain.chain_id} for session: {session_id}")
            return chain.chain_id
            
        except Exception as e:
            self.logger.error(f"Error starting provenance chain: {str(e)}")
            raise
    
    def end_chain(self, session_id: str) -> Optional[str]:
        """
        End the provenance chain for a session.
        
        Args:
            session_id: ID of the reasoning session
            
        Returns:
            Chain ID if successful, None otherwise
        """
        try:
            if session_id in self.active_chains:
                chain_id = self.active_chains[session_id]
                if chain_id in self.chains:
                    self.chains[chain_id].end_time = time.time()
                
                del self.active_chains[session_id]
                
                self.logger.debug(f"Ended provenance chain: {chain_id} for session: {session_id}")
                return chain_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error ending provenance chain: {str(e)}")
            return None
    
    def query_provenance(self,
                        target_id: str,
                        query_type: ProvenanceQueryType,
                        max_depth: int = 10,
                        time_window: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Query provenance information for a target.
        
        Args:
            target_id: ID of the target to query
            query_type: Type of provenance query
            max_depth: Maximum depth for traversal queries
            time_window: Optional time window (start_time, end_time)
            
        Returns:
            Query results
        """
        try:
            if query_type == ProvenanceQueryType.BACKWARD_TRACE:
                return self._backward_trace(target_id, max_depth, time_window)
            elif query_type == ProvenanceQueryType.FORWARD_TRACE:
                return self._forward_trace(target_id, max_depth, time_window)
            elif query_type == ProvenanceQueryType.INFLUENCE_ANALYSIS:
                return self._influence_analysis(target_id, time_window)
            elif query_type == ProvenanceQueryType.DEPENDENCY_GRAPH:
                return self._dependency_graph(target_id, max_depth)
            elif query_type == ProvenanceQueryType.TEMPORAL_EVOLUTION:
                return self._temporal_evolution(target_id, time_window)
            else:
                return {'error': f'Unknown query type: {query_type}'}
                
        except Exception as e:
            self.logger.error(f"Error querying provenance: {str(e)}")
            return {'error': str(e)}
    
    def create_snapshot(self, 
                       knowledge_state: Dict[str, Any],
                       active_sessions: Optional[List[str]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a snapshot of the current knowledge state.
        
        Args:
            knowledge_state: Current state of knowledge
            active_sessions: List of active session IDs
            metadata: Additional metadata
            
        Returns:
            Snapshot ID
        """
        try:
            snapshot = ProvenanceSnapshot(
                knowledge_state=knowledge_state,
                active_sessions=active_sessions or [],
                metadata=metadata or {}
            )
            
            self.snapshots[snapshot.snapshot_id] = snapshot
            self.last_snapshot_time = time.time()
            
            self.logger.info(f"Created knowledge snapshot: {snapshot.snapshot_id}")
            return snapshot.snapshot_id
            
        except Exception as e:
            self.logger.error(f"Error creating snapshot: {str(e)}")
            raise
    
    def rollback_to_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Get rollback information for a specific snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to rollback to
            
        Returns:
            Rollback information and instructions
        """
        try:
            if snapshot_id not in self.snapshots:
                return {'error': f'Snapshot {snapshot_id} not found'}
            
            snapshot = self.snapshots[snapshot_id]
            
            # Find all records after the snapshot
            records_to_undo = []
            for record_id, record in self.records.items():
                if record.timestamp > snapshot.timestamp:
                    records_to_undo.append(record)
            
            # Sort by timestamp (newest first for undo)
            records_to_undo.sort(key=lambda r: r.timestamp, reverse=True)
            
            rollback_info = {
                'snapshot_id': snapshot_id,
                'snapshot_time': snapshot.timestamp,
                'knowledge_state': snapshot.knowledge_state,
                'records_to_undo': [r.to_dict() for r in records_to_undo],
                'undo_count': len(records_to_undo)
            }
            
            return rollback_info
            
        except Exception as e:
            self.logger.error(f"Error preparing rollback: {str(e)}")
            return {'error': str(e)}
    
    def get_attribution_chain(self, target_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete attribution chain for a knowledge item.
        
        Args:
            target_id: ID of the target knowledge item
            
        Returns:
            List of attribution records
        """
        try:
            attribution_chain = []
            visited = set()
            queue = deque([target_id])
            
            while queue and len(attribution_chain) < 100:  # Prevent infinite loops
                current_id = queue.popleft()
                if current_id in visited:
                    continue
                
                visited.add(current_id)
                
                # Find records for this target
                if current_id in self.target_index:
                    for record_id in self.target_index[current_id]:
                        record = self.records[record_id]
                        attribution_chain.append({
                            'record': record.to_dict(),
                            'depth': len(attribution_chain)
                        })
                        
                        # Add input sources to queue
                        for source_id in record.input_sources:
                            if source_id not in visited:
                                queue.append(source_id)
            
            return attribution_chain
            
        except Exception as e:
            self.logger.error(f"Error getting attribution chain: {str(e)}")
            return []
    
    def get_confidence_history(self, target_id: str) -> List[Dict[str, Any]]:
        """
        Get the confidence evolution history for a knowledge item.
        
        Args:
            target_id: ID of the target knowledge item
            
        Returns:
            List of confidence changes over time
        """
        try:
            confidence_history = []
            
            if target_id in self.target_index:
                records = []
                for record_id in self.target_index[target_id]:
                    record = self.records[record_id]
                    if record.confidence_after is not None:
                        records.append(record)
                
                # Sort by timestamp
                records.sort(key=lambda r: r.timestamp)
                
                for record in records:
                    confidence_history.append({
                        'timestamp': record.timestamp,
                        'confidence_before': record.confidence_before,
                        'confidence_after': record.confidence_after,
                        'operation': record.operation_type,
                        'description': record.transformation_description
                    })
            
            return confidence_history
            
        except Exception as e:
            self.logger.error(f"Error getting confidence history: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about provenance tracking."""
        try:
            stats = {
                'total_records': len(self.records),
                'total_chains': len(self.chains),
                'total_snapshots': len(self.snapshots),
                'active_chains': len(self.active_chains),
                'operation_types': defaultdict(int),
                'target_types': defaultdict(int),
                'avg_chain_length': 0.0,
                'oldest_record': None,
                'newest_record': None
            }
            
            # Calculate operation and target type distributions
            for record in self.records.values():
                stats['operation_types'][record.operation_type] += 1
                stats['target_types'][record.target_type] += 1
            
            # Calculate average chain length
            if self.chains:
                total_length = sum(len(chain.records) for chain in self.chains.values())
                stats['avg_chain_length'] = total_length / len(self.chains)
            
            # Find oldest and newest records
            if self.temporal_index:
                stats['oldest_record'] = self.temporal_index[0][0]
                stats['newest_record'] = self.temporal_index[-1][0]
            
            return dict(stats)
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {str(e)}")
            return {}
    
    def export_provenance_data(self, 
                              target_ids: Optional[List[str]] = None,
                              time_window: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Export provenance data for backup or analysis.
        
        Args:
            target_ids: Optional list of specific targets to export
            time_window: Optional time window to export
            
        Returns:
            Exported provenance data
        """
        try:
            export_data = {
                'metadata': {
                    'export_time': time.time(),
                    'version': '2.0',
                    'total_records': len(self.records)
                },
                'records': [],
                'chains': [],
                'snapshots': []
            }
            
            # Filter records
            records_to_export = []
            for record in self.records.values():
                # Filter by target IDs
                if target_ids and record.target_id not in target_ids:
                    continue
                
                # Filter by time window
                if time_window:
                    start_time, end_time = time_window
                    if not (start_time <= record.timestamp <= end_time):
                        continue
                
                records_to_export.append(record)
            
            export_data['records'] = [r.to_dict() for r in records_to_export]
            export_data['chains'] = [c.to_dict() for c in self.chains.values()]
            export_data['snapshots'] = [
                {
                    'snapshot_id': s.snapshot_id,
                    'timestamp': s.timestamp,
                    'metadata': s.metadata
                } for s in self.snapshots.values()
            ]
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error exporting provenance data: {str(e)}")
            return {}
    
    # Private helper methods
    
    def _update_indices(self, record: ProvenanceRecord):
        """Update all indices with a new record."""
        # Target index
        self.target_index[record.target_id].add(record.record_id)
        
        # Session index
        if record.source_session_id:
            self.session_index[record.source_session_id].add(record.record_id)
        
        # Temporal index (keep sorted)
        self.temporal_index.append((record.timestamp, record.record_id))
        self.temporal_index.sort(key=lambda x: x[0])
        
        # Dependency graph
        for source_id in record.input_sources:
            self.dependency_graph[record.target_id].add(source_id)
    
    def _emit_provenance_event(self, record: ProvenanceRecord):
        """Emit a provenance event."""
        if self.event_callback:
            event = ProvenanceEvent(
                provenance_record=record,
                data={
                    'operation': record.operation_type,
                    'target_type': record.target_type
                }
            )
            self.event_callback(event)
    
    def _check_snapshot_needed(self):
        """Check if a new snapshot is needed."""
        if time.time() - self.last_snapshot_time > self.snapshot_interval:
            # This would trigger a snapshot creation in the main system
            self.logger.info("Automatic snapshot recommended")
    
    def _cleanup_old_records(self):
        """Clean up old records if we exceed the maximum history size."""
        if len(self.records) > self.max_history_size:
            # Remove oldest 10% of records
            records_to_remove = int(self.max_history_size * 0.1)
            oldest_records = sorted(self.temporal_index[:records_to_remove])
            
            for _, record_id in oldest_records:
                if record_id in self.records:
                    record = self.records[record_id]
                    
                    # Remove from indices
                    self.target_index[record.target_id].discard(record_id)
                    if record.source_session_id:
                        self.session_index[record.source_session_id].discard(record_id)
                    
                    # Remove from records
                    del self.records[record_id]
            
            # Update temporal index
            self.temporal_index = self.temporal_index[records_to_remove:]
    
    def _backward_trace(self, target_id: str, max_depth: int, time_window: Optional[Tuple[float, float]]) -> Dict[str, Any]:
        """Perform backward provenance trace."""
        trace_result = {
            'target_id': target_id,
            'trace_type': 'backward',
            'nodes': [],
            'edges': [],
            'depth_reached': 0
        }
        
        visited = set()
        queue = deque([(target_id, 0)])
        
        while queue and trace_result['depth_reached'] < max_depth:
            current_id, depth = queue.popleft()
            if current_id in visited:
                continue
            
            visited.add(current_id)
            trace_result['depth_reached'] = max(trace_result['depth_reached'], depth)
            
            # Add node to trace
            trace_result['nodes'].append({
                'id': current_id,
                'depth': depth,
                'type': 'knowledge_item'
            })
            
            # Find records that created/modified this item
            if current_id in self.target_index:
                for record_id in self.target_index[current_id]:
                    record = self.records[record_id]
                    
                    # Apply time window filter
                    if time_window:
                        start_time, end_time = time_window
                        if not (start_time <= record.timestamp <= end_time):
                            continue
                    
                    # Add sources to queue
                    for source_id in record.input_sources:
                        if source_id not in visited:
                            queue.append((source_id, depth + 1))
                            
                            # Add edge
                            trace_result['edges'].append({
                                'source': source_id,
                                'target': current_id,
                                'record_id': record_id,
                                'operation': record.operation_type
                            })
        
        return trace_result
    
    def _forward_trace(self, target_id: str, max_depth: int, time_window: Optional[Tuple[float, float]]) -> Dict[str, Any]:
        """Perform forward provenance trace."""
        trace_result = {
            'target_id': target_id,
            'trace_type': 'forward',
            'nodes': [],
            'edges': [],
            'depth_reached': 0
        }
        
        visited = set()
        queue = deque([(target_id, 0)])
        
        while queue and trace_result['depth_reached'] < max_depth:
            current_id, depth = queue.popleft()
            if current_id in visited:
                continue
            
            visited.add(current_id)
            trace_result['depth_reached'] = max(trace_result['depth_reached'], depth)
            
            # Add node to trace
            trace_result['nodes'].append({
                'id': current_id,
                'depth': depth,
                'type': 'knowledge_item'
            })
            
            # Find records that used this item as input
            for record_id, record in self.records.items():
                if current_id in record.input_sources:
                    # Apply time window filter
                    if time_window:
                        start_time, end_time = time_window
                        if not (start_time <= record.timestamp <= end_time):
                            continue
                    
                    if record.target_id not in visited:
                        queue.append((record.target_id, depth + 1))
                        
                        # Add edge
                        trace_result['edges'].append({
                            'source': current_id,
                            'target': record.target_id,
                            'record_id': record_id,
                            'operation': record.operation_type
                        })
        
        return trace_result
    
    def _influence_analysis(self, target_id: str, time_window: Optional[Tuple[float, float]]) -> Dict[str, Any]:
        """Analyze what influenced a particular knowledge item."""
        influence_result = {
            'target_id': target_id,
            'direct_influences': [],
            'indirect_influences': [],
            'confidence_influences': [],
            'temporal_influences': []
        }
        
        # Direct influences (immediate sources)
        if target_id in self.target_index:
            for record_id in self.target_index[target_id]:
                record = self.records[record_id]
                
                # Apply time window filter
                if time_window:
                    start_time, end_time = time_window
                    if not (start_time <= record.timestamp <= end_time):
                        continue
                
                influence_result['direct_influences'].append({
                    'record_id': record_id,
                    'sources': record.input_sources,
                    'operation': record.operation_type,
                    'timestamp': record.timestamp,
                    'confidence_change': {
                        'before': record.confidence_before,
                        'after': record.confidence_after
                    }
                })
        
        # Additional analysis would go here for indirect influences, etc.
        
        return influence_result
    
    def _dependency_graph(self, target_id: str, max_depth: int) -> Dict[str, Any]:
        """Build dependency graph for a target."""
        dependency_result = {
            'target_id': target_id,
            'nodes': set(),
            'edges': [],
            'levels': defaultdict(set)
        }
        
        visited = set()
        queue = deque([(target_id, 0)])
        
        while queue and max_depth > 0:
            current_id, depth = queue.popleft()
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            dependency_result['nodes'].add(current_id)
            dependency_result['levels'][depth].add(current_id)
            
            # Add dependencies
            if current_id in self.dependency_graph:
                for dep_id in self.dependency_graph[current_id]:
                    dependency_result['edges'].append({
                        'source': dep_id,
                        'target': current_id,
                        'depth': depth
                    })
                    
                    if dep_id not in visited:
                        queue.append((dep_id, depth + 1))
        
        # Convert sets to lists for JSON serialization
        dependency_result['nodes'] = list(dependency_result['nodes'])
        dependency_result['levels'] = {k: list(v) for k, v in dependency_result['levels'].items()}
        
        return dependency_result
    
    def _temporal_evolution(self, target_id: str, time_window: Optional[Tuple[float, float]]) -> Dict[str, Any]:
        """Analyze temporal evolution of a knowledge item."""
        evolution_result = {
            'target_id': target_id,
            'timeline': [],
            'confidence_evolution': [],
            'operation_frequency': defaultdict(int),
            'time_span': None
        }
        
        if target_id in self.target_index:
            records = []
            for record_id in self.target_index[target_id]:
                record = self.records[record_id]
                
                # Apply time window filter
                if time_window:
                    start_time, end_time = time_window
                    if not (start_time <= record.timestamp <= end_time):
                        continue
                
                records.append(record)
            
            # Sort by timestamp
            records.sort(key=lambda r: r.timestamp)
            
            if records:
                evolution_result['time_span'] = {
                    'start': records[0].timestamp,
                    'end': records[-1].timestamp
                }
                
                for record in records:
                    evolution_result['timeline'].append({
                        'timestamp': record.timestamp,
                        'operation': record.operation_type,
                        'description': record.transformation_description,
                        'confidence_before': record.confidence_before,
                        'confidence_after': record.confidence_after
                    })
                    
                    if record.confidence_after is not None:
                        evolution_result['confidence_evolution'].append({
                            'timestamp': record.timestamp,
                            'confidence': record.confidence_after
                        })
                    
                    evolution_result['operation_frequency'][record.operation_type] += 1
        
        # Convert defaultdict to regular dict
        evolution_result['operation_frequency'] = dict(evolution_result['operation_frequency'])
        
        return evolution_result