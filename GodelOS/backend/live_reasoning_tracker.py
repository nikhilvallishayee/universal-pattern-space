"""
Live Reasoning Session Tracker

Tracks and manages live reasoning sessions, connecting transparency view
to actual LLM reasoning traces and cognitive processing steps.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque, Counter
from enum import Enum

logger = logging.getLogger(__name__)

class ReasoningStepType(Enum):
    """Types of reasoning steps."""
    QUERY_ANALYSIS = "query_analysis"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    INFERENCE = "inference"
    SYNTHESIS = "synthesis"
    VERIFICATION = "verification"
    RESPONSE_GENERATION = "response_generation"
    META_REFLECTION = "meta_reflection"
    CONTRADICTION_RESOLUTION = "contradiction_resolution"
    UNCERTAINTY_QUANTIFICATION = "uncertainty_quantification"

@dataclass
class ReasoningStep:
    """Represents a single step in a reasoning process."""
    id: str
    session_id: str
    step_type: ReasoningStepType
    timestamp: float
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float
    duration_ms: float
    metadata: Dict[str, Any]
    reasoning_trace: List[str]
    cognitive_load: float

@dataclass
class ReasoningSession:
    """Represents a complete reasoning session."""
    id: str
    query: str
    start_time: float
    end_time: Optional[float]
    status: str  # "active", "completed", "failed", "paused"
    steps: List[ReasoningStep]
    final_response: Optional[str]
    confidence_score: float
    total_inference_time_ms: float
    cognitive_metrics: Dict[str, Any]
    provenance_data: Dict[str, Any]
    knowledge_sources: List[str]
    meta_cognitive_insights: List[str]

@dataclass
class ProvenanceRecord:
    """Represents provenance information for knowledge items."""
    id: str
    item_id: str
    item_type: str
    source_session: str
    creation_time: float
    derivation_chain: List[str]
    confidence_history: List[Tuple[float, float]]  # (timestamp, confidence)
    modifications: List[Dict[str, Any]]
    verification_status: str
    quality_metrics: Dict[str, float]

class LiveReasoningTracker:
    """
    Tracks live reasoning sessions and provides transparency into
    cognitive processing for the transparency dashboard.
    """
    
    def __init__(self):
        """Initialize the live reasoning tracker."""
        self.active_sessions: Dict[str, ReasoningSession] = {}
        self.completed_sessions: deque = deque(maxlen=100)  # Keep last 100 sessions
        self.provenance_records: Dict[str, ProvenanceRecord] = {}
        self.session_analytics: Dict[str, Any] = defaultdict(list)
        self.websocket_manager = None
        self.llm_cognitive_driver = None
        self.godelos_integration = None
        
        # Analytics tracking
        self.total_queries_processed = 0
        self.total_reasoning_time = 0
        self.avg_session_duration = 0
        self.step_type_frequency = defaultdict(int)
        
    async def initialize(self, websocket_manager=None, llm_driver=None, godelos_integration=None):
        """Initialize the reasoning tracker with necessary components."""
        self.websocket_manager = websocket_manager
        self.llm_cognitive_driver = llm_driver
        self.godelos_integration = godelos_integration
        logger.info("🔄 Live Reasoning Tracker initialized")
    
    async def start_reasoning_session(self, query: str, metadata: Dict = None) -> str:
        """
        Start a new reasoning session.
        
        Args:
            query: The query or problem to reason about
            metadata: Additional context and metadata
            
        Returns:
            Session ID for the new reasoning session
        """
        session_id = f"reasoning_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        session = ReasoningSession(
            id=session_id,
            query=query,
            start_time=time.time(),
            end_time=None,
            status="active",
            steps=[],
            final_response=None,
            confidence_score=0.0,
            total_inference_time_ms=0.0,
            cognitive_metrics={
                "working_memory_usage": 0.0,
                "attention_focus": "initial_query_analysis",
                "metacognitive_awareness": 0.0,
                "uncertainty_level": 0.0
            },
            provenance_data={
                "query_source": metadata.get("source", "user_input"),
                "context_provided": bool(metadata),
                "reasoning_mode": metadata.get("mode", "standard")
            },
            knowledge_sources=[],
            meta_cognitive_insights=[]
        )
        
        self.active_sessions[session_id] = session
        self.total_queries_processed += 1
        
        # Broadcast session start
        await self._broadcast_reasoning_event({
            "type": "reasoning_session_started",
            "session_id": session_id,
            "query": query,
            "timestamp": time.time(),
            "metadata": metadata or {}
        })
        
        logger.info(f"🧠 Started reasoning session {session_id}: {query[:50]}...")
        return session_id
    
    async def add_reasoning_step(self, session_id: str, step_type: ReasoningStepType, 
                               description: str, inputs: Dict = None, outputs: Dict = None,
                               reasoning_trace: List[str] = None, duration_ms: float = 0,
                               confidence: float = 1.0, cognitive_load: float = 0.5) -> str:
        """
        Add a reasoning step to an active session.
        
        Args:
            session_id: ID of the reasoning session
            step_type: Type of reasoning step
            description: Human-readable description of the step
            inputs: Input data for this step
            outputs: Output data from this step
            reasoning_trace: Detailed reasoning trace
            duration_ms: Time taken for this step
            confidence: Confidence in this step's output
            cognitive_load: Estimated cognitive load (0-1)
            
        Returns:
            Step ID
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found or not active")
        
        step_id = f"step_{len(self.active_sessions[session_id].steps)}_{session_id[:8]}"
        
        step = ReasoningStep(
            id=step_id,
            session_id=session_id,
            step_type=step_type,
            timestamp=time.time(),
            description=description,
            inputs=inputs or {},
            outputs=outputs or {},
            confidence=confidence,
            duration_ms=duration_ms,
            metadata={},
            reasoning_trace=reasoning_trace or [],
            cognitive_load=cognitive_load
        )
        
        session = self.active_sessions[session_id]
        session.steps.append(step)
        session.total_inference_time_ms += duration_ms
        
        # Update cognitive metrics
        session.cognitive_metrics["working_memory_usage"] = min(len(session.steps) / 10.0, 1.0)
        session.cognitive_metrics["attention_focus"] = step_type.value
        session.cognitive_metrics["uncertainty_level"] = 1.0 - confidence
        
        # Update analytics
        self.step_type_frequency[step_type.value] += 1
        
        # Broadcast reasoning step
        await self._broadcast_reasoning_event({
            "type": "reasoning_step_added",
            "session_id": session_id,
            "step": asdict(step),
            "timestamp": time.time()
        })
        
        logger.debug(f"📝 Added reasoning step {step_id}: {step_type.value} - {description}")
        return step_id
    
    async def complete_reasoning_session(self, session_id: str, final_response: str, 
                                       confidence_score: float = 1.0, 
                                       meta_insights: List[str] = None) -> ReasoningSession:
        """
        Complete a reasoning session.
        
        Args:
            session_id: ID of the reasoning session
            final_response: Final response or conclusion
            confidence_score: Overall confidence in the response
            meta_insights: Meta-cognitive insights gained
            
        Returns:
            Completed reasoning session
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found or not active")
        
        session = self.active_sessions[session_id]
        session.end_time = time.time()
        session.status = "completed"
        session.final_response = final_response
        session.confidence_score = confidence_score
        session.meta_cognitive_insights = meta_insights or []
        
        # Calculate session duration
        session_duration = session.end_time - session.start_time
        self.total_reasoning_time += session_duration
        self.avg_session_duration = self.total_reasoning_time / max(self.total_queries_processed, 1)
        
        # Update cognitive metrics
        session.cognitive_metrics["metacognitive_awareness"] = len(session.meta_cognitive_insights) / 5.0
        
        # Move to completed sessions
        self.completed_sessions.append(session)
        del self.active_sessions[session_id]
        
        # Broadcast session completion
        await self._broadcast_reasoning_event({
            "type": "reasoning_session_completed",
            "session_id": session_id,
            "final_response": final_response,
            "confidence_score": confidence_score,
            "duration_seconds": session_duration,
            "steps_count": len(session.steps),
            "timestamp": time.time()
        })
        
        logger.info(f"✅ Completed reasoning session {session_id} - Duration: {session_duration:.2f}s")
        return session
    
    async def create_provenance_record(self, item_id: str, item_type: str, 
                                     source_session: str, derivation_chain: List[str] = None,
                                     quality_metrics: Dict[str, float] = None) -> str:
        """
        Create a provenance record for a knowledge item.
        
        Args:
            item_id: Unique identifier for the knowledge item
            item_type: Type of knowledge item
            source_session: Reasoning session that created this item
            derivation_chain: Chain of items this derives from
            quality_metrics: Quality assessment metrics
            
        Returns:
            Provenance record ID
        """
        provenance_id = f"prov_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        record = ProvenanceRecord(
            id=provenance_id,
            item_id=item_id,
            item_type=item_type,
            source_session=source_session,
            creation_time=time.time(),
            derivation_chain=derivation_chain or [],
            confidence_history=[(time.time(), 1.0)],
            modifications=[],
            verification_status="unverified",
            quality_metrics=quality_metrics or {}
        )
        
        self.provenance_records[provenance_id] = record
        
        # Broadcast provenance creation
        await self._broadcast_reasoning_event({
            "type": "provenance_record_created",
            "provenance_id": provenance_id,
            "item_id": item_id,
            "source_session": source_session,
            "timestamp": time.time()
        })
        
        return provenance_id
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all currently active reasoning sessions."""
        sessions = []
        for session in self.active_sessions.values():
            sessions.append({
                "id": session.id,
                "query": session.query,
                "start_time": session.start_time,
                "status": session.status,
                "steps_count": len(session.steps),
                "current_step": session.steps[-1].step_type.value if session.steps else "initializing",
                "confidence_score": session.confidence_score,
                "cognitive_metrics": session.cognitive_metrics,
                "duration_seconds": time.time() - session.start_time
            })
        return sessions
    
    async def get_recent_sessions(self, limit: int = 10) -> List[ReasoningSession]:
        """Get recent completed sessions."""
        # Return most recent completed sessions up to limit
        return list(self.completed_sessions)[-limit:] if self.completed_sessions else []
    
    async def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific reasoning session."""
        # Check active sessions first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
        else:
            # Check completed sessions
            session = next((s for s in self.completed_sessions if s.id == session_id), None)
        
        if not session:
            return None
        
        return {
            "session": asdict(session),
            "steps": [asdict(step) for step in session.steps],
            "analytics": await self._calculate_session_analytics(session)
        }
    
    async def get_reasoning_analytics(self) -> Dict[str, Any]:
        """Get comprehensive reasoning analytics."""
        active_count = len(self.active_sessions)
        completed_count = len(self.completed_sessions)
        
        # Calculate step type distribution
        total_steps = sum(self.step_type_frequency.values())
        step_distribution = {
            step_type: count / max(total_steps, 1) 
            for step_type, count in self.step_type_frequency.items()
        }
        
        # Get recent session performance
        recent_sessions = list(self.completed_sessions)[-10:] if self.completed_sessions else []
        avg_confidence = sum(s.confidence_score for s in recent_sessions) / max(len(recent_sessions), 1)
        avg_steps = sum(len(s.steps) for s in recent_sessions) / max(len(recent_sessions), 1)
        
        return {
            "session_counts": {
                "active": active_count,
                "completed": completed_count,
                "total_processed": self.total_queries_processed
            },
            "performance_metrics": {
                "avg_session_duration_seconds": self.avg_session_duration,
                "total_reasoning_time_seconds": self.total_reasoning_time,
                "avg_confidence_score": avg_confidence,
                "avg_steps_per_session": avg_steps
            },
            "step_distribution": step_distribution,
            "cognitive_patterns": await self._analyze_cognitive_patterns(),
            "provenance_statistics": {
                "total_records": len(self.provenance_records),
                "verified_items": sum(1 for r in self.provenance_records.values() 
                                    if r.verification_status == "verified")
            }
        }
    
    async def get_provenance_chain(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get the complete provenance chain for a knowledge item."""
        record = next((r for r in self.provenance_records.values() if r.item_id == item_id), None)
        if not record:
            return None
        
        # Build complete derivation chain with details
        chain_details = []
        for derived_item_id in record.derivation_chain:
            derived_record = next((r for r in self.provenance_records.values() 
                                 if r.item_id == derived_item_id), None)
            if derived_record:
                chain_details.append({
                    "item_id": derived_item_id,
                    "creation_time": derived_record.creation_time,
                    "source_session": derived_record.source_session,
                    "verification_status": derived_record.verification_status
                })
        
        return {
            "item_id": item_id,
            "provenance_record": asdict(record),
            "derivation_chain_details": chain_details,
            "lineage_depth": len(record.derivation_chain),
            "quality_assessment": record.quality_metrics
        }
    
    async def _calculate_session_analytics(self, session: ReasoningSession) -> Dict[str, Any]:
        """Calculate analytics for a specific reasoning session."""
        if not session.steps:
            return {}
        
        # Step timing analysis
        step_durations = [step.duration_ms for step in session.steps if step.duration_ms > 0]
        avg_step_duration = sum(step_durations) / max(len(step_durations), 1)
        
        # Confidence progression
        confidence_progression = [step.confidence for step in session.steps]
        confidence_trend = "improving" if confidence_progression[-1] > confidence_progression[0] else "declining"
        
        # Cognitive load analysis
        cognitive_loads = [step.cognitive_load for step in session.steps]
        avg_cognitive_load = sum(cognitive_loads) / len(cognitive_loads)
        
        return {
            "timing_analysis": {
                "total_duration_seconds": (session.end_time or time.time()) - session.start_time,
                "avg_step_duration_ms": avg_step_duration,
                "inference_time_ms": session.total_inference_time_ms
            },
            "confidence_analysis": {
                "progression": confidence_progression,
                "trend": confidence_trend,
                "final_confidence": session.confidence_score
            },
            "cognitive_analysis": {
                "avg_cognitive_load": avg_cognitive_load,
                "working_memory_peak": session.cognitive_metrics.get("working_memory_usage", 0),
                "meta_insights_count": len(session.meta_cognitive_insights)
            },
            "step_breakdown": {
                step_type.value: len([s for s in session.steps if s.step_type == step_type])
                for step_type in ReasoningStepType
            }
        }
    
    async def _analyze_cognitive_patterns(self) -> Dict[str, Any]:
        """Analyze cognitive patterns across all sessions."""
        if not self.completed_sessions:
            return {}
        
        sessions = list(self.completed_sessions)
        
        # Analyze common reasoning patterns
        common_step_sequences = defaultdict(int)
        for session in sessions:
            if len(session.steps) >= 2:
                for i in range(len(session.steps) - 1):
                    sequence = f"{session.steps[i].step_type.value} -> {session.steps[i+1].step_type.value}"
                    common_step_sequences[sequence] += 1
        
        # Find most common sequences
        top_sequences = sorted(common_step_sequences.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Analyze success patterns
        high_confidence_sessions = [s for s in sessions if s.confidence_score > 0.8]
        success_patterns = {}
        if high_confidence_sessions:
            success_patterns = {
                "avg_steps": sum(len(s.steps) for s in high_confidence_sessions) / len(high_confidence_sessions),
                "common_first_step": Counter(s.steps[0].step_type.value for s in high_confidence_sessions if s.steps).most_common(1),
                "avg_duration": sum((s.end_time - s.start_time) for s in high_confidence_sessions) / len(high_confidence_sessions)
            }
        
        return {
            "common_step_sequences": dict(top_sequences),
            "success_patterns": success_patterns,
            "avg_session_complexity": sum(len(s.steps) for s in sessions) / len(sessions)
        }
    
    async def _broadcast_reasoning_event(self, event: Dict[str, Any]):
        """Broadcast reasoning event to connected clients."""
        if self.websocket_manager and self.websocket_manager.has_connections():
            try:
                await self.websocket_manager.broadcast(event)
            except Exception as e:
                logger.warning(f"Failed to broadcast reasoning event: {e}")

# Global instance
live_reasoning_tracker = LiveReasoningTracker()