"""
Core data models for cognitive streaming and autonomous knowledge acquisition.

This module defines the fundamental data structures used throughout the
enhanced metacognition system.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
import uuid


class CognitiveEventType(Enum):
    """Types of cognitive events that can be streamed."""
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIGURATION_CHANGED = "configuration_changed"
    ERROR = "error"
    
    # Query processing events
    QUERY_STARTED = "query_started"
    QUERY_COMPLETED = "query_completed"
    QUERY_FAILED = "query_failed"
    
    # Knowledge gap events
    KNOWLEDGE_GAP = "knowledge_gap"
    GAPS_DETECTED = "gaps_detected"
    AUTONOMOUS_GAPS_DETECTED = "autonomous_gaps_detected"
    GAP_ANALYSIS_COMPLETED = "gap_analysis_completed"
    
    # Knowledge acquisition events
    ACQUISITION_PLANNED = "acquisition_planned"
    ACQUISITION_STARTED = "acquisition_started"
    ACQUISITION_COMPLETED = "acquisition_completed"
    ACQUISITION_FAILED = "acquisition_failed"
    
    # Metacognitive cycle events
    CYCLE_STARTED = "cycle_started"
    MONITORING_PHASE = "monitoring_phase"
    DIAGNOSING_PHASE = "diagnosing_phase"
    PLANNING_PHASE = "planning_phase"
    MODIFYING_PHASE = "modifying_phase"
    CYCLE_COMPLETED = "cycle_completed"
    REFLECTION = "reflection"
    
    # External API events
    EXTERNAL_EVENT = "external_event"


class GranularityLevel(Enum):
    """Granularity levels for cognitive event streaming."""
    MINIMAL = "minimal"      # Only critical events
    STANDARD = "standard"    # Important events and decisions
    DETAILED = "detailed"    # Detailed process information
    DEBUG = "debug"          # All internal operations


class KnowledgeGapType(Enum):
    """Types of knowledge gaps that can be detected."""
    CONCEPT_MISSING = "concept_missing"           # Missing concept definitions
    RELATIONSHIP_INCOMPLETE = "relationship_incomplete"  # Missing relationships
    PROPERTY_UNKNOWN = "property_unknown"         # Unknown properties
    CONTEXT_INSUFFICIENT = "context_insufficient" # Insufficient context
    CONFIDENCE_LOW = "confidence_low"             # Low confidence responses


class AcquisitionStrategy(Enum):
    """Strategies for knowledge acquisition."""
    CONCEPT_EXPANSION = "concept_expansion"       # Expand concept knowledge
    RELATIONSHIP_DISCOVERY = "relationship_discovery"  # Discover relationships
    EXTERNAL_SEARCH = "external_search"          # Search external sources
    ANALOGICAL_INFERENCE = "analogical_inference"  # Use analogical reasoning


@dataclass
class KnowledgeGap:
    """Represents a detected knowledge gap."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: KnowledgeGapType = KnowledgeGapType.CONCEPT_MISSING
    detected_at: datetime = field(default_factory=datetime.now)
    priority: float = 0.5  # 0.0 to 1.0
    
    # Query context
    query: Optional[str] = None
    confidence: Optional[float] = None
    
    # Gap details
    missing_concepts: List[str] = field(default_factory=list)
    incomplete_relationships: List[Dict[str, Any]] = field(default_factory=list)
    context_requirements: List[str] = field(default_factory=list)
    
    # Acquisition suggestions
    suggested_acquisitions: List[AcquisitionStrategy] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        result['detected_at'] = self.detected_at.isoformat()
        result['type'] = self.type.value
        result['suggested_acquisitions'] = [s.value for s in self.suggested_acquisitions]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGap':
        """Create from dictionary representation."""
        data = data.copy()
        data['detected_at'] = datetime.fromisoformat(data['detected_at'])
        data['type'] = KnowledgeGapType(data['type'])
        data['suggested_acquisitions'] = [
            AcquisitionStrategy(s) for s in data['suggested_acquisitions']
        ]
        return cls(**data)


@dataclass
class CognitiveEvent:
    """Represents a cognitive event for streaming."""
    # Required fields first
    type: CognitiveEventType
    
    # Optional fields with defaults
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    granularity_level: GranularityLevel = GranularityLevel.STANDARD
    processing_context: Optional[str] = None
    sequence_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'event_id': self.event_id,
            'type': self.type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'source': self.source,
            'granularity_level': self.granularity_level.value,
            'processing_context': self.processing_context,
            'sequence_number': self.sequence_number
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CognitiveEvent':
        """Create from dictionary representation."""
        data = data.copy()
        data['type'] = CognitiveEventType(data['type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['granularity_level'] = GranularityLevel(data['granularity_level'])
        return cls(**data)


@dataclass
class AcquisitionPlan:
    """Represents a plan for knowledge acquisition."""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy: AcquisitionStrategy = AcquisitionStrategy.CONCEPT_EXPANSION
    priority: float = 0.5  # 0.0 to 1.0
    
    # Gap reference (can be None for general plans)
    gap: Optional[KnowledgeGap] = None
    
    # Plan details
    estimated_duration: float = 30.0  # seconds
    required_resources: List[str] = field(default_factory=list)
    acquisition_steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # Approval and execution
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        result['gap'] = self.gap.to_dict() if self.gap else None
        result['strategy'] = self.strategy.value
        result['created_at'] = self.created_at.isoformat()
        if self.approved_at:
            result['approved_at'] = self.approved_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AcquisitionPlan':
        """Create from dictionary representation."""
        data = data.copy()
        data['gap'] = KnowledgeGap.from_dict(data['gap'])
        data['strategy'] = AcquisitionStrategy(data['strategy'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('approved_at'):
            data['approved_at'] = datetime.fromisoformat(data['approved_at'])
        return cls(**data)


@dataclass
class AcquisitionResult:
    """Represents the result of a knowledge acquisition attempt."""
    plan_id: str
    success: bool
    execution_time: float  # seconds
    
    # Results
    acquired_concepts: List[Dict[str, Any]] = field(default_factory=list)
    acquired_relationships: List[Dict[str, Any]] = field(default_factory=list)
    
    # Error information
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Metadata
    completed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        result['completed_at'] = self.completed_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AcquisitionResult':
        """Create from dictionary representation."""
        data = data.copy()
        data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


@dataclass
class StreamingMetrics:
    """Metrics for cognitive event streaming performance."""
    events_per_second: float = 0.0
    connected_clients: int = 0
    total_events_sent: int = 0
    total_events_dropped: int = 0
    average_latency_ms: float = 0.0
    buffer_utilization: float = 0.0
    
    # Error tracking
    connection_errors: int = 0
    serialization_errors: int = 0
    
    # Timestamp
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        result['last_updated'] = self.last_updated.isoformat()
        return result


@dataclass
class AutonomousLearningMetrics:
    """Metrics for autonomous learning performance."""
    gaps_detected_total: int = 0
    gaps_resolved_total: int = 0
    active_acquisitions: int = 0
    
    # Success rates by strategy
    strategy_success_rates: Dict[str, float] = field(default_factory=dict)
    
    # Performance metrics
    average_gap_detection_time: float = 0.0
    average_acquisition_time: float = 0.0
    
    # Error tracking
    detection_failures: int = 0
    acquisition_failures: int = 0
    
    # Timestamp
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        result['last_updated'] = self.last_updated.isoformat()
        return result


# Utility functions

def serialize_cognitive_event(event: CognitiveEvent) -> str:
    """Serialize a cognitive event to JSON string."""
    return json.dumps(event.to_dict(), default=str)


def deserialize_cognitive_event(data: str) -> CognitiveEvent:
    """Deserialize a cognitive event from JSON string."""
    return CognitiveEvent.from_dict(json.loads(data))


def filter_events_by_granularity(
    events: List[CognitiveEvent],
    max_granularity: GranularityLevel
) -> List[CognitiveEvent]:
    """
    Filter events based on maximum granularity level.
    
    Args:
        events: List of cognitive events
        max_granularity: Maximum granularity level to include
        
    Returns:
        Filtered list of events
    """
    granularity_order = {
        GranularityLevel.MINIMAL: 0,
        GranularityLevel.STANDARD: 1,
        GranularityLevel.DETAILED: 2,
        GranularityLevel.DEBUG: 3
    }
    
    max_level = granularity_order[max_granularity]
    
    return [
        event for event in events
        if granularity_order[event.granularity_level] <= max_level
    ]


def create_gap_from_query_result(
    query: str,
    result: Dict[str, Any],
    confidence_threshold: float = 0.7
) -> Optional[KnowledgeGap]:
    """
    Create a knowledge gap from a query processing result.
    
    Args:
        query: The original query
        result: Query processing result
        confidence_threshold: Minimum confidence threshold
        
    Returns:
        KnowledgeGap if gap detected, None otherwise
    """
    confidence = result.get('confidence', 0.0)
    
    if confidence < confidence_threshold:
        gap_type = KnowledgeGapType.CONFIDENCE_LOW
        
        # Determine more specific gap type based on result
        if 'missing_concepts' in result:
            gap_type = KnowledgeGapType.CONCEPT_MISSING
        elif 'incomplete_relationships' in result:
            gap_type = KnowledgeGapType.RELATIONSHIP_INCOMPLETE
        elif 'insufficient_context' in result:
            gap_type = KnowledgeGapType.CONTEXT_INSUFFICIENT
        
        return KnowledgeGap(
            type=gap_type,
            query=query,
            confidence=confidence,
            priority=1.0 - confidence,  # Lower confidence = higher priority
            missing_concepts=result.get('missing_concepts', []),
            incomplete_relationships=result.get('incomplete_relationships', []),
            context_requirements=result.get('context_requirements', []),
            suggested_acquisitions=[
                AcquisitionStrategy.CONCEPT_EXPANSION,
                AcquisitionStrategy.RELATIONSHIP_DISCOVERY
            ]
        )
    
    return None
