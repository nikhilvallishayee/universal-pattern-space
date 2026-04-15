"""
Cognitive Transparency Manager for the GödelOS system.

This module implements the central orchestrator for cognitive transparency operations,
coordinating reasoning stream tracking, session management, and transparency level configuration.
"""

import asyncio
import logging
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Callable
from collections import defaultdict

from godelOS.cognitive_transparency.models import (
    ReasoningStep, ReasoningSession, ReasoningSummary, DecisionPoint,
    TransparencyLevel, StepType, DetailLevel, OperationStatus,
    ReasoningStepBuilder, SessionEvent, EventCallback
)
from godelOS.cognitive_transparency.stream_tracker import ReasoningStreamTracker

logger = logging.getLogger(__name__)


class CognitiveTransparencyManager:
    """
    Central manager for cognitive transparency operations.
    
    This class orchestrates all transparency-related functionality including:
    - Reasoning session management
    - Real-time step tracking and streaming
    - Transparency level configuration
    - Cross-component coordination
    - Performance monitoring
    """
    
    def __init__(self, websocket_manager=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Cognitive Transparency Manager.
        
        Args:
            websocket_manager: WebSocket manager for real-time streaming
            config: Configuration dictionary
        """
        self.websocket_manager = websocket_manager
        self.config = config or {}
        
        # Core components
        self.stream_tracker = ReasoningStreamTracker(websocket_manager)
        
        # Session management
        self.active_sessions: Dict[str, ReasoningSession] = {}
        self.completed_sessions: Dict[str, ReasoningSession] = {}
        self.session_history_limit = self.config.get('session_history_limit', 1000)
        
        # Transparency configuration
        self.default_transparency_level = TransparencyLevel(
            self.config.get('default_transparency_level', 'standard')
        )
        self.global_transparency_level = self.default_transparency_level
        
        # Event management
        self.event_callbacks: List[EventCallback] = []
        self.session_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Performance tracking
        self.session_count = 0
        self.total_steps_tracked = 0
        self.average_session_duration = 0.0
        
        # State management
        self.is_initialized = False
        self.is_running = False
        
        # Configuration
        self.max_concurrent_sessions = self.config.get('max_concurrent_sessions', 100)
        self.session_timeout_seconds = self.config.get('session_timeout_seconds', 3600)
        
        # Background tasks
        self._cleanup_task = None
        
        logger.info("CognitiveTransparencyManager initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the transparency manager and all components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize stream tracker
            await self.stream_tracker.start()
            
            # Register for stream tracker events
            self.stream_tracker.register_event_callback(self._handle_stream_event)
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            
            self.is_initialized = True
            self.is_running = True
            
            logger.info("CognitiveTransparencyManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize CognitiveTransparencyManager: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the transparency manager and cleanup resources."""
        self.is_running = False
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Complete all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self.complete_reasoning_session(session_id)
        
        # Shutdown stream tracker
        await self.stream_tracker.stop()
        
        logger.info("CognitiveTransparencyManager shutdown complete")
    
    async def start_reasoning_session(
        self,
        session_id: Optional[str] = None,
        transparency_level: Optional[TransparencyLevel] = None,
        query: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new reasoning session with transparency tracking.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            transparency_level: Transparency level for this session
            query: The query or task being reasoned about
            context: Additional context for the session
            
        Returns:
            The session ID
        """
        if not self.is_running:
            raise RuntimeError("CognitiveTransparencyManager is not running")
        
        # Check session limits
        if len(self.active_sessions) >= self.max_concurrent_sessions:
            # Clean up oldest sessions if at limit
            await self._cleanup_oldest_sessions(1)
        
        # Generate secure session ID if not provided
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex}_{secrets.token_hex(8)}"
        
        # Use provided transparency level or default
        if not transparency_level:
            transparency_level = self.global_transparency_level
        
        # Create new session
        session = ReasoningSession(
            session_id=session_id,
            transparency_level=transparency_level,
            query=query,
            context=context or {}
        )
        
        # Start the session
        session.start()
        
        # Register with stream tracker
        await self.stream_tracker.create_session(session)
        
        # Store session
        self.active_sessions[session_id] = session
        self.session_count += 1
        
        logger.info(f"Started reasoning session: {session_id}")
        
        # Emit session started event
        await self._emit_session_event("session_started", session)
        
        return session_id
    
    async def emit_reasoning_step(
        self,
        step: ReasoningStep,
        session_id: str
    ) -> None:
        """
        Emit a reasoning step for tracking and streaming.
        
        Args:
            step: The reasoning step to track
            session_id: ID of the session this step belongs to
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Attempted to emit step for unknown session: {session_id}")
            return
        
        # Track the step
        await self.stream_tracker.track_reasoning_step(step, session_id)
        self.total_steps_tracked += 1
        
        logger.debug(f"Emitted reasoning step {step.step_id} for session {session_id}")
    
    async def emit_decision_point(
        self,
        decision: DecisionPoint,
        session_id: str
    ) -> None:
        """
        Emit a decision point for tracking.
        
        Args:
            decision: The decision point to track
            session_id: ID of the session this decision belongs to
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Attempted to emit decision for unknown session: {session_id}")
            return
        
        # Add to session trace
        session = self.active_sessions[session_id]
        session.trace.add_decision_point(decision)
        
        # Stream decision point if websocket available
        if self.websocket_manager:
            try:
                await self.websocket_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "decision_point",
                        "data": decision.to_dict()
                    }
                )
            except Exception as e:
                logger.error(f"Error streaming decision point: {e}")
        
        logger.debug(f"Emitted decision point {decision.decision_id} for session {session_id}")
    
    async def complete_reasoning_session(
        self,
        session_id: str,
        summary: Optional[ReasoningSummary] = None
    ) -> None:
        """
        Complete a reasoning session and generate summary.
        
        Args:
            session_id: ID of the session to complete
            summary: Optional pre-generated summary
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Attempted to complete unknown session: {session_id}")
            return
        
        session = self.active_sessions[session_id]
        
        # Generate summary if not provided
        if not summary:
            summary = await self._generate_session_summary(session)
        
        # Complete the session
        session.complete(summary)
        
        # Complete tracking
        await self.stream_tracker.complete_session(session_id)
        
        # Move to completed sessions
        self.completed_sessions[session_id] = session
        del self.active_sessions[session_id]
        
        # Maintain history limit
        if len(self.completed_sessions) > self.session_history_limit:
            oldest_session_id = min(
                self.completed_sessions.keys(),
                key=lambda sid: self.completed_sessions[sid].start_time
            )
            del self.completed_sessions[oldest_session_id]
        
        # Update performance metrics
        self._update_performance_metrics(session)
        
        logger.info(f"Completed reasoning session: {session_id}")
        
        # Emit session completed event
        await self._emit_session_event("session_completed", session)
    
    async def get_reasoning_trace(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the complete reasoning trace for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dictionary containing the complete trace or None if not found
        """
        # Check active sessions first
        session = self.active_sessions.get(session_id)
        if not session:
            # Check completed sessions
            session = self.completed_sessions.get(session_id)
        
        if not session:
            return None
        
        return session.to_dict()
    
    async def configure_transparency_level(self, level: TransparencyLevel) -> None:
        """
        Configure the global transparency level.
        
        Args:
            level: New transparency level
        """
        old_level = self.global_transparency_level
        self.global_transparency_level = level
        
        logger.info(f"Changed global transparency level from {old_level.value} to {level.value}")
        
        # Emit configuration change event
        await self._emit_event({
            "type": "transparency_level_changed",
            "old_level": old_level.value,
            "new_level": level.value,
            "timestamp": time.time()
        })
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get information about all active sessions.
        
        Returns:
            List of active session dictionaries
        """
        return [session.to_dict() for session in self.active_sessions.values()]
    
    async def get_session_statistics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed statistics for a specific session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Statistics dictionary or None if session not found
        """
        # Try stream tracker first (more detailed stats)
        stats = self.stream_tracker.get_session_statistics(session_id)
        if stats:
            return stats
        
        # Fallback to basic session info
        session = self.active_sessions.get(session_id) or self.completed_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "status": session.status.value,
            "duration_ms": session.get_duration_ms(),
            "total_steps": len(session.trace.steps),
            "decision_points": len(session.trace.decision_points),
            "transparency_level": session.transparency_level.value
        }
    
    def create_reasoning_step(self) -> ReasoningStepBuilder:
        """
        Create a new reasoning step using the builder pattern.
        
        Returns:
            ReasoningStepBuilder instance
        """
        return ReasoningStepBuilder()
    
    def register_event_callback(self, callback: EventCallback) -> None:
        """Register a callback for transparency events."""
        self.event_callbacks.append(callback)
    
    def unregister_event_callback(self, callback: EventCallback) -> None:
        """Unregister an event callback."""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    async def _generate_session_summary(self, session: ReasoningSession) -> ReasoningSummary:
        """Generate a summary for a completed session."""
        trace = session.trace
        
        # Calculate key metrics
        total_steps = len(trace.steps)
        processing_time = session.get_duration_ms()
        
        # Calculate average confidence
        confidences = [step.confidence for step in trace.steps]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 1.0
        
        # Extract key insights (high importance steps)
        key_insights = [
            step.description for step in trace.steps
            if step.importance_score > 0.7 and step.description
        ]
        
        # Performance metrics
        performance_metrics = {
            "steps_per_second": total_steps / (processing_time / 1000.0) if processing_time > 0 else 0.0,
            "average_step_confidence": avg_confidence,
            "high_importance_steps": len([s for s in trace.steps if s.importance_score > 0.7]),
            "decision_points": len(trace.decision_points)
        }
        
        # Knowledge sources (simplified - would be more sophisticated in full implementation)
        knowledge_sources = list(set([
            step.context.get('knowledge_source', 'unknown')
            for step in trace.steps
            if step.context.get('knowledge_source')
        ]))
        
        # Novel discoveries (steps marked as novel)
        novel_discoveries = [
            step.description for step in trace.steps
            if step.step_type == StepType.NOVEL_INFERENCE and step.description
        ]
        
        return ReasoningSummary(
            session_id=session.session_id,
            total_steps=total_steps,
            processing_time_ms=processing_time,
            confidence=avg_confidence,
            key_insights=key_insights[:10],  # Limit to top 10
            performance_metrics=performance_metrics,
            decision_points=[dp.decision_id for dp in trace.decision_points],
            knowledge_sources=knowledge_sources,
            novel_discoveries=novel_discoveries
        )
    
    async def _handle_stream_event(self, event) -> None:
        """Handle events from the stream tracker."""
        # Forward to registered callbacks
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    async def _emit_session_event(self, event_type: str, session: ReasoningSession) -> None:
        """Emit a session-related event."""
        event = SessionEvent(
            session_id=session.session_id,
            event_type=event_type,
            session=session,
            data={"session": session.to_dict()}
        )
        
        await self._handle_stream_event(event)
    
    async def _emit_event(self, event_data: Dict[str, Any]) -> None:
        """Emit a general event."""
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_data)
                else:
                    callback(event_data)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def _update_performance_metrics(self, session: ReasoningSession) -> None:
        """Update global performance metrics based on completed session."""
        duration = session.get_duration_ms()
        
        # Update average session duration
        if self.session_count > 1:
            self.average_session_duration = (
                (self.average_session_duration * (self.session_count - 1) + duration) /
                self.session_count
            )
        else:
            self.average_session_duration = duration
    
    async def _cleanup_expired_sessions(self) -> None:
        """Background task to cleanup expired sessions."""
        while self.is_running:
            try:
                current_time = time.time()
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if (current_time - session.start_time) > self.session_timeout_seconds:
                        expired_sessions.append(session_id)
                
                # Complete expired sessions
                for session_id in expired_sessions:
                    logger.warning(f"Session {session_id} expired, completing...")
                    await self.complete_reasoning_session(session_id)
                
                # Sleep before next cleanup
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(60)  # Back off on error
    
    async def _cleanup_oldest_sessions(self, count: int) -> None:
        """Clean up the oldest active sessions."""
        if len(self.active_sessions) <= count:
            return
        
        # Sort by start time and complete oldest
        sorted_sessions = sorted(
            self.active_sessions.items(),
            key=lambda x: x[1].start_time
        )
        
        for i in range(count):
            session_id, _ = sorted_sessions[i]
            logger.info(f"Cleaning up oldest session: {session_id}")
            await self.complete_reasoning_session(session_id)
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global transparency system statistics."""
        stream_stats = self.stream_tracker.get_global_statistics()
        
        return {
            "total_sessions": self.session_count,
            "active_sessions": len(self.active_sessions),
            "completed_sessions": len(self.completed_sessions),
            "total_steps_tracked": self.total_steps_tracked,
            "average_session_duration_ms": self.average_session_duration,
            "global_transparency_level": self.global_transparency_level.value,
            "stream_tracker_stats": stream_stats,
            "is_running": self.is_running
        }