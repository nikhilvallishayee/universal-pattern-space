"""
Reasoning Stream Tracker for the Cognitive Transparency system.

This module handles real-time tracking and streaming of reasoning processes,
implementing hierarchical tracking with adaptive detail levels.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Callable
from concurrent.futures import ThreadPoolExecutor

from godelOS.cognitive_transparency.models import (
    ReasoningStep, ReasoningSession, StepType, DetailLevel, 
    TransparencyLevel, StepEvent, EventCallback
)

logger = logging.getLogger(__name__)


class StreamBuffer:
    """Buffer for batching reasoning steps before streaming."""
    
    def __init__(self, max_size: int = 100, flush_interval_ms: int = 50):
        self.max_size = max_size
        self.flush_interval_ms = flush_interval_ms
        self.buffer = deque()
        self.last_flush = time.time()
        self._lock = asyncio.Lock()
    
    async def add_step(self, step: ReasoningStep) -> bool:
        """Add a step to the buffer. Returns True if buffer should be flushed."""
        async with self._lock:
            self.buffer.append(step)
            
            # Check if we should flush
            should_flush = (
                len(self.buffer) >= self.max_size or
                (time.time() - self.last_flush) * 1000 >= self.flush_interval_ms or
                step.importance_score > 0.8  # Always flush high-importance steps
            )
            
            return should_flush
    
    async def flush(self) -> List[ReasoningStep]:
        """Flush and return all buffered steps."""
        async with self._lock:
            steps = list(self.buffer)
            self.buffer.clear()
            self.last_flush = time.time()
            return steps


class ReasoningStreamTracker:
    """
    Tracks reasoning processes in real-time with hierarchical detail levels.
    
    Implements adaptive tracking where critical reasoning gets detailed tracking
    while routine operations are summarized for performance.
    """
    
    def __init__(self, websocket_manager=None):
        """
        Initialize the stream tracker.
        
        Args:
            websocket_manager: WebSocket manager for real-time streaming
        """
        self.websocket_manager = websocket_manager
        self.active_sessions: Dict[str, ReasoningSession] = {}
        self.stream_buffers: Dict[str, StreamBuffer] = {}
        self.event_callbacks: List[EventCallback] = []
        self.step_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Configuration
        self.buffer_size = 100
        self.batch_interval_ms = 50
        self.high_importance_threshold = 0.7
        self.low_importance_threshold = 0.3
        
        # Performance tracking
        self.step_counts = defaultdict(int)
        self.processing_times = defaultdict(list)
        
        # Background task for periodic flushing
        self._flush_task = None
        self._running = False
        
        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def start(self) -> None:
        """Start the stream tracker."""
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("ReasoningStreamTracker started")
    
    async def stop(self) -> None:
        """Stop the stream tracker."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush all remaining buffers
        for session_id in list(self.stream_buffers.keys()):
            await self._flush_session_buffer(session_id)
        
        self.executor.shutdown(wait=True)
        logger.info("ReasoningStreamTracker stopped")
    
    async def create_session(self, session: ReasoningSession) -> None:
        """Register a new reasoning session for tracking."""
        self.active_sessions[session.session_id] = session
        self.stream_buffers[session.session_id] = StreamBuffer(
            max_size=self.buffer_size,
            flush_interval_ms=self.batch_interval_ms
        )
        
        logger.debug(f"Created tracking session: {session.session_id}")
        
        # Notify callbacks
        await self._emit_event(StepEvent(
            session_id=session.session_id,
            event_type="session_created",
            data={"session": session.to_dict()}
        ))
    
    async def track_reasoning_step(self, step: ReasoningStep, session_id: str) -> None:
        """
        Track a reasoning step with adaptive detail level.
        
        Args:
            step: The reasoning step to track
            session_id: ID of the reasoning session
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Unknown session ID: {session_id}")
            return
        
        start_time = time.time()
        
        try:
            # Calculate importance and detail level
            step.detail_level = self._calculate_detail_level(step)
            step.importance_score = self._calculate_importance_score(step)
            
            # Update session trace
            session = self.active_sessions[session_id]
            session.trace.add_step(step)
            
            # Update performance tracking
            self.step_counts[step.step_type] += 1
            
            # Handle based on detail level and importance
            if step.detail_level == DetailLevel.HIGH or step.importance_score > self.high_importance_threshold:
                # Stream immediately for critical steps
                await self._stream_immediately(step, session_id)
            else:
                # Buffer for batch streaming
                buffer = self.stream_buffers.get(session_id)
                if buffer:
                    should_flush = await buffer.add_step(step)
                    if should_flush:
                        await self._flush_session_buffer(session_id)
            
            # Record processing time
            processing_time = (time.time() - start_time) * 1000
            step.processing_time_ms = processing_time
            self.processing_times[step.step_type].append(processing_time)
            
            logger.debug(f"Tracked step {step.step_id} in session {session_id}")
            
        except Exception as e:
            logger.error(f"Error tracking reasoning step: {e}")
    
    def _calculate_detail_level(self, step: ReasoningStep) -> DetailLevel:
        """
        Calculate the appropriate detail level for a reasoning step.
        
        Implements hierarchical tracking logic:
        - HIGH: Novel inferences, contradictions, uncertainty, complex operations
        - MEDIUM: Standard reasoning steps
        - LOW: Routine operations, cached results, simple unifications
        """
        # Critical reasoning always gets high detail
        if step.step_type in [
            StepType.NOVEL_INFERENCE,
            StepType.CONTRADICTION_RESOLUTION,
            StepType.HYPOTHESIS_GENERATION,
            StepType.BELIEF_REVISION,
            StepType.METACOGNITIVE_REFLECTION
        ]:
            return DetailLevel.HIGH
        
        # Low confidence indicates uncertainty - needs detailed tracking
        if step.confidence < 0.7:
            return DetailLevel.HIGH
        
        # Routine operations get low detail
        if step.step_type in [
            StepType.CACHE_HIT,
            StepType.SIMPLE_UNIFICATION,
            StepType.PATTERN_MATCHING
        ]:
            return DetailLevel.LOW
        
        # Complex operations get medium detail by default
        if step.step_type in [
            StepType.ANALOGICAL_REASONING,
            StepType.DECISION_MAKING
        ]:
            return DetailLevel.MEDIUM
        
        # Default to medium detail
        return DetailLevel.MEDIUM
    
    def _calculate_importance_score(self, step: ReasoningStep) -> float:
        """
        Calculate importance score for a reasoning step.
        
        Factors considered:
        - Step type criticality
        - Confidence level
        - Processing complexity
        - Novelty indicators
        """
        base_importance = {
            StepType.NOVEL_INFERENCE: 0.9,
            StepType.CONTRADICTION_RESOLUTION: 0.9,
            StepType.HYPOTHESIS_GENERATION: 0.8,
            StepType.BELIEF_REVISION: 0.8,
            StepType.METACOGNITIVE_REFLECTION: 0.8,
            StepType.ANALOGICAL_REASONING: 0.7,
            StepType.DECISION_MAKING: 0.7,
            StepType.INFERENCE: 0.6,
            StepType.EVALUATION: 0.5,
            StepType.KNOWLEDGE_RETRIEVAL: 0.4,
            StepType.UNIFICATION: 0.4,
            StepType.PATTERN_MATCHING: 0.3,
            StepType.CACHE_HIT: 0.1,
            StepType.SIMPLE_UNIFICATION: 0.1
        }.get(step.step_type, 0.5)
        
        # Adjust based on confidence (low confidence = higher importance)
        confidence_factor = 1.0 - (step.confidence * 0.3)
        
        # Adjust based on processing time (longer = more complex = more important)
        time_factor = min(step.processing_time_ms / 1000.0, 0.3)  # Cap at 0.3
        
        # Calculate final importance
        importance = min(base_importance + confidence_factor + time_factor, 1.0)
        
        return importance
    
    async def _stream_immediately(self, step: ReasoningStep, session_id: str) -> None:
        """Stream a single step immediately via WebSocket."""
        if not self.websocket_manager:
            return
        
        try:
            event = StepEvent(
                session_id=session_id,
                step=step,
                data={"immediate": True}
            )
            
            await self.websocket_manager.broadcast_to_session(
                session_id,
                {
                    "type": "reasoning_step",
                    "data": step.to_dict(),
                    "immediate": True
                }
            )
            
            # Emit to callbacks
            await self._emit_event(event)
            
        except Exception as e:
            logger.error(f"Error streaming step immediately: {e}")
    
    async def _flush_session_buffer(self, session_id: str) -> None:
        """Flush the buffer for a specific session."""
        buffer = self.stream_buffers.get(session_id)
        if not buffer:
            return
        
        steps = await buffer.flush()
        if not steps:
            return
        
        try:
            # Stream batched steps
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "reasoning_steps_batch",
                        "data": [step.to_dict() for step in steps],
                        "batch_size": len(steps)
                    }
                )
            
            # Emit batch event
            await self._emit_event(StepEvent(
                session_id=session_id,
                event_type="steps_batch",
                data={
                    "steps": [step.to_dict() for step in steps],
                    "batch_size": len(steps)
                }
            ))
            
            logger.debug(f"Flushed {len(steps)} steps for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error flushing session buffer: {e}")
    
    async def _periodic_flush(self) -> None:
        """Periodically flush all session buffers."""
        while self._running:
            try:
                # Flush all session buffers
                for session_id in list(self.stream_buffers.keys()):
                    await self._flush_session_buffer(session_id)
                
                # Wait for next flush interval
                await asyncio.sleep(self.batch_interval_ms / 1000.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
                await asyncio.sleep(1.0)  # Back off on error
    
    async def complete_session(self, session_id: str) -> None:
        """Mark a session as completed and perform final cleanup."""
        if session_id not in self.active_sessions:
            return
        
        # Final flush
        await self._flush_session_buffer(session_id)
        
        # Update session status
        session = self.active_sessions[session_id]
        session.complete()
        
        # Clean up
        if session_id in self.stream_buffers:
            del self.stream_buffers[session_id]
        
        logger.debug(f"Completed tracking session: {session_id}")
        
        # Emit completion event
        await self._emit_event(StepEvent(
            session_id=session_id,
            event_type="session_completed",
            data={"session": session.to_dict()}
        ))
    
    async def _emit_event(self, event: StepEvent) -> None:
        """Emit an event to all registered callbacks."""
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    # Run in executor for non-async callbacks
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor, callback, event
                    )
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def register_event_callback(self, callback: EventCallback) -> None:
        """Register a callback for transparency events."""
        self.event_callbacks.append(callback)
    
    def unregister_event_callback(self, callback: EventCallback) -> None:
        """Unregister an event callback."""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    def get_session_statistics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific session."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        trace = session.trace
        
        # Calculate statistics
        step_type_counts = defaultdict(int)
        detail_level_counts = defaultdict(int)
        confidence_scores = []
        importance_scores = []
        
        for step in trace.steps:
            step_type_counts[step.step_type.value] += 1
            detail_level_counts[step.detail_level.value] += 1
            confidence_scores.append(step.confidence)
            importance_scores.append(step.importance_score)
        
        return {
            "session_id": session_id,
            "total_steps": len(trace.steps),
            "duration_ms": session.get_duration_ms(),
            "step_type_counts": dict(step_type_counts),
            "detail_level_counts": dict(detail_level_counts),
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            "average_importance": sum(importance_scores) / len(importance_scores) if importance_scores else 0.0,
            "decision_points": len(trace.decision_points)
        }
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global tracking statistics."""
        return {
            "active_sessions": len(self.active_sessions),
            "total_step_counts": dict(self.step_counts),
            "average_processing_times": {
                step_type.value: sum(times) / len(times) if times else 0.0
                for step_type, times in self.processing_times.items()
            }
        }