"""
Data models for the Cognitive Transparency system.

This module defines all the data structures used for tracking reasoning processes,
managing transparency levels, and representing cognitive operations.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from abc import ABC, abstractmethod


class TransparencyLevel(Enum):
    """Defines the level of transparency for reasoning operations."""
    MINIMAL = "minimal"  # Only high-level progress
    STANDARD = "standard"  # Hybrid approach - real-time progress + detailed post-analysis
    DETAILED = "detailed"  # Full real-time streaming
    MAXIMUM = "maximum"  # Complete transparency with all micro-steps


class StepType(Enum):
    """Types of reasoning steps that can be tracked."""
    INFERENCE = "inference"
    UNIFICATION = "unification"
    EVALUATION = "evaluation"
    PATTERN_MATCHING = "pattern_matching"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    DECISION_MAKING = "decision_making"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    BELIEF_REVISION = "belief_revision"
    ANALOGICAL_REASONING = "analogical_reasoning"
    METACOGNITIVE_REFLECTION = "metacognitive_reflection"
    
    # Special step types for hierarchical tracking
    NOVEL_INFERENCE = "novel_inference"
    CONTRADICTION_RESOLUTION = "contradiction_resolution"
    CACHE_HIT = "cache_hit"
    SIMPLE_UNIFICATION = "simple_unification"


class DetailLevel(Enum):
    """Level of detail for tracking individual reasoning steps."""
    LOW = "low"      # Summarized tracking for routine operations
    MEDIUM = "medium"  # Standard tracking
    HIGH = "high"    # Detailed tracking for critical reasoning


class OperationStatus(Enum):
    """Status of cognitive operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ReasoningStep:
    """Represents a single step in a reasoning process."""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    step_type: StepType = StepType.INFERENCE
    description: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    processing_time_ms: float = 0.0
    importance_score: float = 0.5  # For hierarchical tracking (0.0 - 1.0)
    detail_level: DetailLevel = DetailLevel.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)
    parent_step_id: Optional[str] = None
    child_step_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'step_id': self.step_id,
            'timestamp': self.timestamp,
            'step_type': self.step_type.value,
            'description': self.description,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'confidence': self.confidence,
            'processing_time_ms': self.processing_time_ms,
            'importance_score': self.importance_score,
            'detail_level': self.detail_level.value,
            'context': self.context,
            'parent_step_id': self.parent_step_id,
            'child_step_ids': self.child_step_ids
        }


@dataclass
class DecisionOption:
    """Represents an option in a decision point."""
    option_id: str
    description: str
    confidence: float
    expected_outcome: str
    cost_estimate: float = 0.0
    risk_level: float = 0.0


@dataclass
class DecisionPoint:
    """Represents a decision point in reasoning."""
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    context: str = ""
    options: List[DecisionOption] = field(default_factory=list)
    selected_option: Optional[str] = None
    justification: str = ""
    confidence: float = 1.0
    decision_criteria: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'decision_id': self.decision_id,
            'timestamp': self.timestamp,
            'context': self.context,
            'options': [
                {
                    'option_id': opt.option_id,
                    'description': opt.description,
                    'confidence': opt.confidence,
                    'expected_outcome': opt.expected_outcome,
                    'cost_estimate': opt.cost_estimate,
                    'risk_level': opt.risk_level
                } for opt in self.options
            ],
            'selected_option': self.selected_option,
            'justification': self.justification,
            'confidence': self.confidence,
            'decision_criteria': self.decision_criteria
        }


@dataclass
class ReasoningSummary:
    """Summary of a completed reasoning session."""
    session_id: str
    total_steps: int = 0
    processing_time_ms: float = 0.0
    confidence: float = 1.0
    key_insights: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    decision_points: List[str] = field(default_factory=list)
    knowledge_sources: List[str] = field(default_factory=list)
    novel_discoveries: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'total_steps': self.total_steps,
            'processing_time_ms': self.processing_time_ms,
            'confidence': self.confidence,
            'key_insights': self.key_insights,
            'performance_metrics': self.performance_metrics,
            'decision_points': self.decision_points,
            'knowledge_sources': self.knowledge_sources,
            'novel_discoveries': self.novel_discoveries
        }


@dataclass
class ReasoningTrace:
    """Complete trace of a reasoning session."""
    session_id: str
    steps: List[ReasoningStep] = field(default_factory=list)
    decision_points: List[DecisionPoint] = field(default_factory=list)
    summary: Optional[ReasoningSummary] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: ReasoningStep) -> None:
        """Add a reasoning step to the trace."""
        self.steps.append(step)
    
    def add_decision_point(self, decision: DecisionPoint) -> None:
        """Add a decision point to the trace."""
        self.decision_points.append(decision)
    
    def get_steps_by_type(self, step_type: StepType) -> List[ReasoningStep]:
        """Get all steps of a specific type."""
        return [step for step in self.steps if step.step_type == step_type]
    
    def get_critical_steps(self) -> List[ReasoningStep]:
        """Get steps marked as critical (high importance)."""
        return [step for step in self.steps if step.importance_score > 0.7]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'steps': [step.to_dict() for step in self.steps],
            'decision_points': [dp.to_dict() for dp in self.decision_points],
            'summary': self.summary.to_dict() if self.summary else None,
            'metadata': self.metadata
        }


@dataclass
class ReasoningSession:
    """Represents an active reasoning session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: OperationStatus = OperationStatus.PENDING
    transparency_level: TransparencyLevel = TransparencyLevel.STANDARD
    query: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    trace: ReasoningTrace = field(default_factory=lambda: ReasoningTrace(""))
    
    def __post_init__(self):
        """Initialize trace with session ID."""
        if not self.trace.session_id:
            self.trace.session_id = self.session_id
    
    def start(self) -> None:
        """Mark session as started."""
        self.status = OperationStatus.IN_PROGRESS
        self.start_time = time.time()
    
    def complete(self, summary: Optional[ReasoningSummary] = None) -> None:
        """Mark session as completed."""
        self.status = OperationStatus.COMPLETED
        self.end_time = time.time()
        if summary:
            self.trace.summary = summary
    
    def fail(self, error: str) -> None:
        """Mark session as failed."""
        self.status = OperationStatus.FAILED
        self.end_time = time.time()
        self.trace.metadata['error'] = error
    
    def get_duration_ms(self) -> float:
        """Get session duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status.value,
            'transparency_level': self.transparency_level.value,
            'query': self.query,
            'context': self.context,
            'duration_ms': self.get_duration_ms(),
            'trace': self.trace.to_dict()
        }


class ReasoningStepBuilder:
    """Builder pattern for creating reasoning steps with fluent interface."""
    
    def __init__(self):
        self._step = ReasoningStep()
    
    def with_type(self, step_type: StepType) -> 'ReasoningStepBuilder':
        self._step.step_type = step_type
        return self
    
    def with_description(self, description: str) -> 'ReasoningStepBuilder':
        self._step.description = description
        return self
    
    def with_input(self, input_data: Dict[str, Any]) -> 'ReasoningStepBuilder':
        self._step.input_data = input_data
        return self
    
    def with_output(self, output_data: Dict[str, Any]) -> 'ReasoningStepBuilder':
        self._step.output_data = output_data
        return self
    
    def with_confidence(self, confidence: float) -> 'ReasoningStepBuilder':
        self._step.confidence = confidence
        return self
    
    def with_importance(self, importance: float) -> 'ReasoningStepBuilder':
        self._step.importance_score = importance
        return self
    
    def with_detail_level(self, level: DetailLevel) -> 'ReasoningStepBuilder':
        self._step.detail_level = level
        return self
    
    def with_context(self, context: Dict[str, Any]) -> 'ReasoningStepBuilder':
        self._step.context = context
        return self
    
    def with_parent(self, parent_id: str) -> 'ReasoningStepBuilder':
        self._step.parent_step_id = parent_id
        return self
    
    def build(self) -> ReasoningStep:
        """Build and return the reasoning step."""
        step = self._step
        self._step = ReasoningStep()  # Reset for next use
        return step


# Event types for the transparency system
@dataclass
class TransparencyEvent:
    """Base class for transparency system events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""
    event_type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepEvent(TransparencyEvent):
    """Event for reasoning step updates."""
    step: ReasoningStep = field(default_factory=ReasoningStep)
    event_type: str = "step"


@dataclass
class DecisionEvent(TransparencyEvent):
    """Event for decision point updates."""
    decision: DecisionPoint = field(default_factory=DecisionPoint)
    event_type: str = "decision"


@dataclass
class SessionEvent(TransparencyEvent):
    """Event for session status updates."""
    session: ReasoningSession = field(default_factory=ReasoningSession)
    event_type: str = "session"


# Phase 2 Extensions: Knowledge Graph, Provenance, Autonomous Learning, Uncertainty

@dataclass
class KnowledgeNode:
    """Represents a node in the dynamic knowledge graph."""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    concept: str = ""
    node_type: str = "concept"  # concept, entity, relation, fact
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    creation_time: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    update_count: int = 0
    source_provenance: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'node_id': self.node_id,
            'concept': self.concept,
            'node_type': self.node_type,
            'properties': self.properties,
            'confidence': self.confidence,
            'creation_time': self.creation_time,
            'last_updated': self.last_updated,
            'update_count': self.update_count,
            'source_provenance': self.source_provenance
        }


@dataclass
class KnowledgeEdge:
    """Represents an edge in the dynamic knowledge graph."""
    edge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str = ""
    target_node_id: str = ""
    relation_type: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    strength: float = 1.0  # Relationship strength
    creation_time: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    source_provenance: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'edge_id': self.edge_id,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'relation_type': self.relation_type,
            'properties': self.properties,
            'confidence': self.confidence,
            'strength': self.strength,
            'creation_time': self.creation_time,
            'last_updated': self.last_updated,
            'source_provenance': self.source_provenance
        }


@dataclass
class ProvenanceRecord:
    """Tracks the provenance of knowledge and reasoning steps."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    operation_type: str = ""  # create, update, delete, infer, revise
    target_id: str = ""  # ID of the knowledge item being tracked
    target_type: str = ""  # node, edge, fact, rule
    source_reasoning_step_id: Optional[str] = None
    source_session_id: Optional[str] = None
    input_sources: List[str] = field(default_factory=list)
    transformation_description: str = ""
    confidence_before: Optional[float] = None
    confidence_after: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'record_id': self.record_id,
            'timestamp': self.timestamp,
            'operation_type': self.operation_type,
            'target_id': self.target_id,
            'target_type': self.target_type,
            'source_reasoning_step_id': self.source_reasoning_step_id,
            'source_session_id': self.source_session_id,
            'input_sources': self.input_sources,
            'transformation_description': self.transformation_description,
            'confidence_before': self.confidence_before,
            'confidence_after': self.confidence_after,
            'metadata': self.metadata
        }


@dataclass
class UncertaintyMetrics:
    """Quantifies uncertainty for reasoning steps and knowledge."""
    confidence: float = 1.0  # Overall confidence (0.0 - 1.0)
    epistemic_uncertainty: float = 0.0  # Uncertainty due to lack of knowledge
    aleatoric_uncertainty: float = 0.0  # Uncertainty due to inherent randomness
    model_uncertainty: float = 0.0  # Uncertainty in the reasoning model itself
    source_reliability: float = 1.0  # Reliability of information sources
    temporal_decay: float = 0.0  # Uncertainty increase over time
    contradiction_score: float = 0.0  # Measure of contradictory evidence
    evidence_strength: float = 1.0  # Strength of supporting evidence
    
    def overall_uncertainty(self) -> float:
        """Calculate overall uncertainty score."""
        return 1.0 - (self.confidence * self.source_reliability * self.evidence_strength *
                     (1.0 - self.contradiction_score) * (1.0 - self.temporal_decay))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'confidence': self.confidence,
            'epistemic_uncertainty': self.epistemic_uncertainty,
            'aleatoric_uncertainty': self.aleatoric_uncertainty,
            'model_uncertainty': self.model_uncertainty,
            'source_reliability': self.source_reliability,
            'temporal_decay': self.temporal_decay,
            'contradiction_score': self.contradiction_score,
            'evidence_strength': self.evidence_strength,
            'overall_uncertainty': self.overall_uncertainty()
        }


class LearningObjectiveType(Enum):
    """Types of autonomous learning objectives."""
    KNOWLEDGE_GAP_FILLING = "knowledge_gap_filling"
    HYPOTHESIS_TESTING = "hypothesis_testing"
    PATTERN_DISCOVERY = "pattern_discovery"
    CONTRADICTION_RESOLUTION = "contradiction_resolution"
    CONCEPT_REFINEMENT = "concept_refinement"
    RELATIONSHIP_DISCOVERY = "relationship_discovery"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


@dataclass
class LearningObjective:
    """Represents an autonomous learning objective."""
    objective_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    objective_type: LearningObjectiveType = LearningObjectiveType.KNOWLEDGE_GAP_FILLING
    description: str = ""
    priority: float = 0.5  # 0.0 - 1.0
    target_concepts: List[str] = field(default_factory=list)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    estimated_effort: float = 1.0  # Relative effort estimate
    creation_time: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    status: OperationStatus = OperationStatus.PENDING
    progress: float = 0.0  # 0.0 - 1.0
    results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'objective_id': self.objective_id,
            'objective_type': self.objective_type.value,
            'description': self.description,
            'priority': self.priority,
            'target_concepts': self.target_concepts,
            'success_criteria': self.success_criteria,
            'estimated_effort': self.estimated_effort,
            'creation_time': self.creation_time,
            'deadline': self.deadline,
            'status': self.status.value,
            'progress': self.progress,
            'results': self.results
        }


@dataclass
class LearningSession:
    """Represents an autonomous learning session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    objectives: List[str] = field(default_factory=list)  # Objective IDs
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: OperationStatus = OperationStatus.PENDING
    strategy: str = ""
    discoveries: List[str] = field(default_factory=list)
    knowledge_updates: List[str] = field(default_factory=list)  # Provenance record IDs
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    reasoning_sessions: List[str] = field(default_factory=list)  # Related reasoning session IDs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'objectives': self.objectives,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status.value,
            'strategy': self.strategy,
            'discoveries': self.discoveries,
            'knowledge_updates': self.knowledge_updates,
            'performance_metrics': self.performance_metrics,
            'reasoning_sessions': self.reasoning_sessions
        }


# Extended reasoning step with uncertainty and provenance
@dataclass
class EnhancedReasoningStep(ReasoningStep):
    """Extended reasoning step with Phase 2 features."""
    uncertainty_metrics: UncertaintyMetrics = field(default_factory=UncertaintyMetrics)
    provenance_records: List[str] = field(default_factory=list)  # Provenance record IDs
    knowledge_updates: List[str] = field(default_factory=list)  # Updated knowledge item IDs
    contradictions_detected: List[str] = field(default_factory=list)
    novel_insights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            'uncertainty_metrics': self.uncertainty_metrics.to_dict(),
            'provenance_records': self.provenance_records,
            'knowledge_updates': self.knowledge_updates,
            'contradictions_detected': self.contradictions_detected,
            'novel_insights': self.novel_insights
        })
        return base_dict


# Events for Phase 2 features
@dataclass
class KnowledgeGraphEvent(TransparencyEvent):
    """Event for knowledge graph updates."""
    event_type: str = "knowledge_graph"
    operation: str = ""  # node_added, node_updated, edge_added, edge_updated, etc.
    affected_nodes: List[str] = field(default_factory=list)
    affected_edges: List[str] = field(default_factory=list)


@dataclass
class ProvenanceEvent(TransparencyEvent):
    """Event for provenance tracking updates."""
    event_type: str = "provenance"
    provenance_record: ProvenanceRecord = field(default_factory=ProvenanceRecord)


@dataclass
class LearningEvent(TransparencyEvent):
    """Event for autonomous learning updates."""
    event_type: str = "learning"
    learning_session_id: str = ""
    objective_updates: List[str] = field(default_factory=list)


@dataclass
class UncertaintyEvent(TransparencyEvent):
    """Event for uncertainty metric updates."""
    event_type: str = "uncertainty"
    target_id: str = ""
    target_type: str = ""  # step, node, edge, fact
    uncertainty_metrics: UncertaintyMetrics = field(default_factory=UncertaintyMetrics)


# Type aliases for better code readability
EventCallback = Callable[[TransparencyEvent], None]
StepCallback = Callable[[ReasoningStep], None]
DecisionCallback = Callable[[DecisionPoint], None]
SessionCallback = Callable[[ReasoningSession], None]
KnowledgeGraphCallback = Callable[[KnowledgeGraphEvent], None]
ProvenanceCallback = Callable[[ProvenanceEvent], None]
LearningCallback = Callable[[LearningEvent], None]
UncertaintyCallback = Callable[[UncertaintyEvent], None]