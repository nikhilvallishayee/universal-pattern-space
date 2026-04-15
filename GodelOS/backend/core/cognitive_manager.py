#!/usr/bin/env python3
"""
GödelOS Cognitive Manager

This module provides comprehensive cognitive orchestration, session management,
and intelligent reasoning coordination for the GödelOS system.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum

# Import consciousness engine
from .consciousness_engine import ConsciousnessEngine, ConsciousnessState
from .cognitive_transparency import transparency_engine
from .errors import CognitiveError, ExternalServiceError
from .coordination import CoordinationEvent, SimpleCoordinator
from .enhanced_coordination import (
    EnhancedCoordinator, EnhancedCoordinationEvent, EnhancedCoordinationDecision,
    ComponentType, ComponentStatus, CoordinationContext, CoordinationAction
)
from .cognitive_orchestrator import (
    CognitiveOrchestrator, CognitiveProcess, ProcessPriority, ProcessState
)
from .circuit_breaker import circuit_breaker_manager, CircuitBreakerOpenException
from .metacognitive_monitor import metacognitive_monitor
from .autonomous_learning import autonomous_learning_system
from .knowledge_graph_evolution import knowledge_graph_evolution
from .phenomenal_experience import phenomenal_experience_generator
from .query_replay_harness import replay_harness, ProcessingStep

logger = logging.getLogger(__name__)


class CognitiveProcessType(Enum):
    """Types of cognitive processes."""
    QUERY_PROCESSING = "query_processing"
    KNOWLEDGE_INTEGRATION = "knowledge_integration"
    AUTONOMOUS_REASONING = "autonomous_reasoning"
    SELF_REFLECTION = "self_reflection"
    KNOWLEDGE_GAP_ANALYSIS = "knowledge_gap_analysis"


@dataclass
class CognitiveResponse:
    """Response from cognitive processing."""
    session_id: str
    response: Dict[str, Any]
    reasoning_trace: List[Dict[str, Any]]
    knowledge_used: List[str]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflectionResult:
    """Result of cognitive reflection."""
    insights: List[str]
    improvements: List[str]
    confidence_adjustment: float
    knowledge_gaps_identified: List[str]
    learning_opportunities: List[str]


@dataclass
class KnowledgeGap:
    """Represents an identified knowledge gap."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: str = "medium"  # low, medium, high, critical
    domain: str = ""
    search_criteria: Dict[str, Any] = field(default_factory=dict)
    identified_at: datetime = field(default_factory=datetime.now)
    status: str = "identified"  # identified, researching, resolved
    confidence: float = 1.0


async def _safe_transparency_log(log_method_name: str, *args, **kwargs):
    """Safely log to transparency engine if available"""
    if transparency_engine:
        try:
            log_method = getattr(transparency_engine, log_method_name, None)
            if log_method:
                if asyncio.iscoroutinefunction(log_method):
                    await log_method(*args, **kwargs)
                else:
                    log_method(*args, **kwargs)
        except Exception as e:
            logger.debug(f"Transparency logging skipped ({log_method_name}): {type(e).__name__} - {e}")


class CognitiveManager:
    """
    Central orchestrator for all cognitive processes in GodelOS.
    
    Responsibilities:
    - Coordinate LLM interactions with knowledge context
    - Manage cognitive transparency and self-reflection
    - Route requests between reasoning engines
    - Maintain cognitive state and memory coherence
    - Orchestrate autonomous reasoning processes
    """
    
    def __init__(self, 
                 godelos_integration=None,
                 llm_driver=None,
                 knowledge_pipeline=None,
                 websocket_manager=None):
        self.godelos_integration = godelos_integration
        self.llm_driver = llm_driver
        self.knowledge_pipeline = knowledge_pipeline
        self.websocket_manager = websocket_manager
        
        # Configuration - MUST be set before any component initialization
        self.max_reasoning_depth = 10
        self.min_confidence_threshold = 0.6
        self.enable_autonomous_reasoning = True
        self.enable_self_reflection = True
        
        # Initialize consciousness engine
        self.consciousness_engine = ConsciousnessEngine(
            llm_driver=llm_driver,
            knowledge_pipeline=knowledge_pipeline,
            websocket_manager=websocket_manager
        )
        
        # Initialize enhanced coordination system
        self.enhanced_coordinator = EnhancedCoordinator(
            min_confidence=self.min_confidence_threshold,
            websocket_manager=websocket_manager
        )
        
        # Initialize cognitive orchestrator
        self.cognitive_orchestrator = CognitiveOrchestrator(
            websocket_manager=websocket_manager
        )
        
        # Register cognitive components with enhanced coordinator
        self._register_cognitive_components()
        
        # Initialize meta-cognitive monitor
        metacognitive_monitor.llm_driver = llm_driver
        logger.info("Meta-cognitive monitor initialized with LLM driver")
        
        # Initialize autonomous learning system
        autonomous_learning_system.llm_driver = llm_driver
        logger.info("Autonomous learning system initialized with LLM driver")
        
        # Initialize knowledge graph evolution system
        knowledge_graph_evolution.llm_driver = llm_driver
        logger.info("Knowledge graph evolution system initialized with LLM driver")
        
        # Initialize phenomenal experience generator
        phenomenal_experience_generator.llm_driver = llm_driver
        logger.info("Phenomenal experience generator initialized with LLM driver")
        
        # Cognitive state management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.reasoning_traces: Dict[str, List[Dict[str, Any]]] = {}
        self.knowledge_gaps: Dict[str, KnowledgeGap] = {}
        self.coordination_events = deque(maxlen=200)
        
        # Performance metrics
        self.processing_metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "average_processing_time": 0.0,
            "knowledge_items_created": 0,
            "gaps_identified": 0,
            "gaps_resolved": 0
        }
        
        logger.info("CognitiveManager initialized")

        # Lightweight coordinator for cross-component nudges
        try:
            self.coordinator = SimpleCoordinator(min_confidence=self.min_confidence_threshold)
        except Exception:
            self.coordinator = None

    def _register_cognitive_components(self):
        """Register cognitive components with the enhanced coordinator."""
        try:
            # Register core components
            self.enhanced_coordinator.register_component(
                ComponentType.LLM_DRIVER, "llm_driver", 
                self.llm_driver, ["reasoning", "text_generation", "consciousness_assessment"]
            )
            
            self.enhanced_coordinator.register_component(
                ComponentType.KNOWLEDGE_PIPELINE, "knowledge_pipeline",
                self.knowledge_pipeline, ["knowledge_retrieval", "context_integration"]
            )
            
            self.enhanced_coordinator.register_component(
                ComponentType.CONSCIOUSNESS_ENGINE, "consciousness_engine",
                self.consciousness_engine, ["consciousness_assessment", "self_awareness"]
            )
            
            self.enhanced_coordinator.register_component(
                ComponentType.METACOGNITIVE_MONITOR, "metacognitive_monitor",
                metacognitive_monitor, ["self_monitoring", "reflection"]
            )
            
            self.enhanced_coordinator.register_component(
                ComponentType.AUTONOMOUS_LEARNING, "autonomous_learning",
                autonomous_learning_system, ["pattern_learning", "adaptation"]
            )
            
            self.enhanced_coordinator.register_component(
                ComponentType.KNOWLEDGE_GRAPH, "knowledge_graph_evolution",
                knowledge_graph_evolution, ["graph_evolution", "relationship_learning"]
            )
            
            self.enhanced_coordinator.register_component(
                ComponentType.PHENOMENAL_EXPERIENCE, "phenomenal_experience",
                phenomenal_experience_generator, ["experience_generation", "qualia_modeling"]
            )
            
            logger.info("🔗 Successfully registered all cognitive components")
            
        except Exception as e:
            logger.error(f"❌ Failed to register cognitive components: {e}")

    async def _coordinate_cognitive_process(self, query: str, context: Dict[str, Any], 
                                          confidence: float) -> EnhancedCoordinationDecision:
        """Coordinate cognitive processing using enhanced coordination."""
        try:
            # Create component status snapshot
            component_states = {}
            for name, status in self.enhanced_coordinator.health_monitor.component_statuses.items():
                component_states[name] = status
            
            # Create coordination context
            coordination_context = CoordinationContext(
                session_id=context.get("session_id", str(uuid.uuid4())),
                query=query,
                confidence=confidence,
                component_states=component_states,
                historical_data=context,
                constraints=context.get("constraints", {}),
                preferences=context.get("preferences", {})
            )
            
            # Create coordination event
            event = EnhancedCoordinationEvent(
                name="cognitive_process_coordination",
                context=coordination_context,
                component_source="cognitive_manager",
                urgency="normal",
                tags=["cognitive_processing", "coordination"]
            )
            
            # Get coordination decision
            decision = await self.enhanced_coordinator.notify(event)
            
            logger.info(f"🎯 Coordination decision: {decision.action.value} (confidence: {decision.confidence:.2f})")
            return decision
            
        except Exception as e:
            logger.error(f"❌ Coordination error: {e}")
            # Return safe fallback
            return EnhancedCoordinationDecision(
                action=CoordinationAction.PROCEED,
                rationale=f"Fallback due to coordination error: {e}",
                confidence=0.5
            )

    async def _with_retries(self, op_fn, *, retries: int = 2, delay: float = 0.5, backoff: float = 2.0, op_name: str = "operation", service_type: str = "default"):
        """Run an async operation with circuit breaker protection and retry/backoff.

        Args:
            op_fn: zero-arg callable returning an awaitable
            retries: number of retries (not counting first attempt)
            delay: initial delay between attempts (seconds)
            backoff: multiplier for delay after each failure
            op_name: label used for logging/telemetry
            service_type: type of service for circuit breaker config
        Returns:
            Result of the awaited operation
        Raises:
            Last exception if all attempts fail or circuit breaker is open
        """
        # Determine operation type for timeout policy
        operation_type = "default"
        if "llm" in op_name.lower():
            operation_type = "llm_call"
        elif "knowledge" in op_name.lower():
            operation_type = "knowledge_retrieval"
        elif "consciousness" in op_name.lower():
            operation_type = "consciousness_assessment"
        elif "vector" in op_name.lower():
            operation_type = "vector_search"
        elif "reflection" in op_name.lower():
            operation_type = "reflection"
        
        # Use circuit breaker for protected execution
        try:
            return await circuit_breaker_manager.protected_call(
                service_name=op_name,
                service_type=service_type,
                operation_type=operation_type,
                func=self._retry_with_backoff,
                op_fn=op_fn,
                retries=retries,
                delay=delay,
                backoff=backoff,
                op_name=op_name
            )
        except CircuitBreakerOpenException as e:
            logger.error(f"🚫 Circuit breaker open for {op_name}: {e}")
            # Try fallback if available
            return await self._handle_circuit_breaker_open(op_name, op_fn)
    
    async def _retry_with_backoff(self, op_fn, retries: int, delay: float, backoff: float, op_name: str):
        """Internal retry logic with backoff."""
        attempt = 0
        last_exc = None
        current_delay = delay
        while attempt <= retries:
            try:
                return await op_fn()
            except Exception as e:
                last_exc = e
                attempt += 1
                logger.warning(f"{op_name} failed (attempt {attempt}/{retries + 1}): {e}")
                # Broadcast non-fatal failure event to WS clients if available
                try:
                    if self.websocket_manager and attempt <= retries:
                        err = ExternalServiceError(
                            code=op_name,
                            message=str(e),
                            recoverable=True,
                            details={"attempt": attempt, "max_attempts": retries + 1},
                            service="llm" if "llm" in op_name else "external",
                            operation=op_name,
                        )
                        await self.websocket_manager.broadcast_cognitive_update({
                            "type": "recoverable_error",
                            "operation": op_name,
                            "attempt": attempt,
                            "max_attempts": retries + 1,
                            "error": err.to_dict(),
                        })
                except Exception:
                    # Do not let telemetry failures bubble up
                    pass
                if attempt <= retries:
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        # Exhausted retries
        assert last_exc is not None
        raise last_exc
    
    async def _handle_circuit_breaker_open(self, op_name: str, op_fn):
        """Handle circuit breaker open scenarios with fallbacks."""
        logger.warning(f"🔄 Attempting fallback for {op_name}")
        
        # Try to provide fallback responses
        if "llm" in op_name.lower():
            return await self._llm_fallback()
        elif "consciousness" in op_name.lower():
            return await self._consciousness_fallback()
        elif "knowledge" in op_name.lower():
            return await self._knowledge_fallback()
        else:
            # Generic fallback
            raise ExternalServiceError(
                code="circuit_breaker_open",
                message=f"Service {op_name} is temporarily unavailable",
                recoverable=True,
                service=op_name,
                operation="fallback"
            )
    
    async def _llm_fallback(self) -> Dict[str, Any]:
        """Fallback response when LLM is unavailable."""
        return {
            "response": "I'm currently experiencing technical difficulties with my language processing. Please try again in a moment.",
            "confidence": 0.1,
            "fallback": True,
            "reasoning": "LLM service unavailable - using fallback response"
        }
    
    async def _consciousness_fallback(self) -> Dict[str, Any]:
        """Fallback consciousness assessment."""
        return {
            "awareness_level": 0.5,
            "self_reflection_depth": 1,
            "autonomous_goals": [],
            "cognitive_integration": 0.3,
            "manifest_behaviors": ["fallback_mode"],
            "fallback": True
        }
    
    async def _knowledge_fallback(self) -> Dict[str, Any]:
        """Fallback knowledge retrieval."""
        return {
            "knowledge_items": [],
            "context": "Knowledge retrieval temporarily unavailable",
            "confidence": 0.1,
            "fallback": True
        }

    async def initialize(self) -> bool:
        """Initialize the cognitive manager and all subsystems."""
        try:
            logger.info("Initializing CognitiveManager...")
            
            # Initialize knowledge pipeline if available
            if self.knowledge_pipeline and hasattr(self.knowledge_pipeline, 'initialize'):
                await self.knowledge_pipeline.initialize()
            
            # Initialize LLM driver if available
            if self.llm_driver and hasattr(self.llm_driver, 'initialize'):
                await self.llm_driver.initialize()
            
            logger.info("✅ CognitiveManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize CognitiveManager: {e}")
            return False
    
    async def process_query(self, 
                          query: str, 
                          context: Optional[Dict] = None,
                          process_type: CognitiveProcessType = CognitiveProcessType.QUERY_PROCESSING,
                          correlation_id: Optional[str] = None,
                          enable_recording: bool = True) -> CognitiveResponse:
        """
        Process a query through the complete cognitive pipeline.
        
        Args:
            query: The input query or prompt
            context: Optional context information
            process_type: Type of cognitive processing to perform
            correlation_id: Optional correlation ID for tracking
            enable_recording: Whether to enable replay recording
            
        Returns:
            CognitiveResponse with results and reasoning trace
        """
        session_id = str(uuid.uuid4())
        start_time = time.time()
        context = context or {}
        
        # Generate correlation ID if not provided
        if correlation_id is None:
            correlation_id = f"cog_{uuid.uuid4().hex[:12]}"
        
        # Start recording if enabled
        recording_id = None
        if enable_recording:
            recording_id = replay_harness.start_recording(
                query=query,
                context=context,
                correlation_id=correlation_id,
                tags=[process_type.value, "cognitive_processing"]
            )
        
        try:
            logger.info(f"🧠 Processing query (session: {session_id[:8]}...): {query[:100]}...")
            
            # Record query received step
            if enable_recording:
                replay_harness.record_step(
                    correlation_id=correlation_id,
                    step_type=ProcessingStep.QUERY_RECEIVED,
                    input_data={"query": query, "context": context, "process_type": process_type.value},
                    output_data={"session_id": session_id},
                    duration_ms=0,
                    metadata={"recording_id": recording_id}
                )
            
            # Initialize session
            self.active_sessions[session_id] = {
                "query": query,
                "context": context,
                "process_type": process_type,
                "start_time": start_time,
                "status": "processing",
                "correlation_id": correlation_id,
                "recording_id": recording_id
            }
            
            reasoning_trace = []
            
            # Step 1: Context gathering
            step_start = time.time()
            reasoning_trace.append({
                "step": 1,
                "action": "context_gathering",
                "timestamp": step_start,
                "description": "Gathering knowledge context for query"
            })
            
            knowledge_context = await self._gather_knowledge_context(query, context)
            reasoning_trace[-1]["result"] = knowledge_context
            
            # Record context gathering step
            if enable_recording:
                replay_harness.record_step(
                    correlation_id=correlation_id,
                    step_type=ProcessingStep.KNOWLEDGE_RETRIEVAL,
                    input_data={"query": query, "context": context},
                    output_data=knowledge_context,
                    duration_ms=(time.time() - step_start) * 1000,
                    metadata={"step": 1, "action": "context_gathering"}
                )
            
            # Step 2: Initial reasoning
            step_start = time.time()
            reasoning_trace.append({
                "step": 2,
                "action": "initial_reasoning",
                "timestamp": step_start,
                "description": "Performing initial cognitive processing"
            })
            
            initial_response = await self._perform_initial_reasoning(query, knowledge_context, context)
            reasoning_trace[-1]["result"] = initial_response
            
            # Record initial reasoning step
            if enable_recording:
                replay_harness.record_step(
                    correlation_id=correlation_id,
                    step_type=ProcessingStep.COGNITIVE_ANALYSIS,
                    input_data={"query": query, "knowledge_context": knowledge_context},
                    output_data=initial_response,
                    duration_ms=(time.time() - step_start) * 1000,
                    metadata={"step": 2, "action": "initial_reasoning"}
                )

            # Step 3: Enhanced coordination evaluation
            reasoning_trace.append({
                "step": 3,
                "action": "coordination_evaluation",
                "timestamp": time.time(),
                "description": "Evaluating cognitive coordination needs"
            })
            
            # Get coordination decision
            coordination_decision = await self._coordinate_cognitive_process(
                query, context, initial_response.get("confidence", 0.5)
            )
            reasoning_trace[-1]["result"] = coordination_decision.to_dict()
            
            # Apply coordination decision
            if coordination_decision.action == CoordinationAction.AUGMENT_CONTEXT:
                logger.info("🔄 Augmenting context based on coordination decision")
                augmented_context = await self._augment_context(
                    knowledge_context, coordination_decision.params
                )
                # Re-process with augmented context
                initial_response = await self._perform_initial_reasoning(
                    query, augmented_context, context
                )
                
            elif coordination_decision.action == CoordinationAction.TRIGGER_REFLECTION:
                logger.info("🤔 Triggering reflection based on coordination decision")
                reflection_result = await self._trigger_self_reflection(
                    query, initial_response, coordination_decision.params
                )
                initial_response["reflection"] = reflection_result
                
            elif coordination_decision.action == CoordinationAction.ROUTE_TO_SPECIALIST:
                logger.info("🎯 Routing to specialist based on coordination decision")
                specialist_result = await self._route_to_specialist(
                    query, initial_response, coordination_decision.params
                )
                initial_response.update(specialist_result)

            # Coordination hook: evaluate initial result and record decision
            try:
                if self.coordinator is not None:
                    event = CoordinationEvent(
                        name="initial_reasoning_complete",
                        data={
                            "confidence": initial_response.get("confidence", 0.0),
                            "knowledge_context": knowledge_context,
                        },
                    )
                    decision = await self.coordinator.notify(event)
                    reasoning_trace[-1]["coordination_decision"] = decision.to_dict()
                    # If augmentation advised, best-effort merge extra context and note it
                    if decision.action == "augment_context":
                        augmented = await self._augment_context(query, knowledge_context)
                        # Merge sources/entities/relationships shallowly
                        for key in ("sources", "entities", "relationships"):
                            if key in augmented:
                                base_list = knowledge_context.get(key, []) or []
                                add_list = augmented.get(key, []) or []
                                knowledge_context[key] = base_list + [x for x in add_list if x not in base_list]
                        reasoning_trace[-1]["context_augmentation"] = {
                            "performed": augmented.get("augmentation", False),
                            "added_sources": len(augmented.get("sources", []) or []),
                            "added_entities": len(augmented.get("entities", []) or []),
                            "added_relationships": len(augmented.get("relationships", []) or []),
                        }
                    # Record coordination event telemetry
                    try:
                        self.coordination_events.append({
                            "timestamp": time.time(),
                            "session_id": session_id,
                            "decision": decision.to_dict(),
                            "confidence": float(initial_response.get("confidence", 0.0) or 0.0),
                            "augmentation": bool(reasoning_trace[-1].get("context_augmentation", {}).get("performed", False)),
                            "query_preview": (query or "")[:120],
                        })
                    except Exception:
                        pass
            except Exception:
                # Non-fatal: coordination is advisory
                pass
            
            # Step 3: Knowledge integration
            reasoning_trace.append({
                "step": 3,
                "action": "knowledge_integration",
                "timestamp": time.time(),
                "description": "Integrating new knowledge from reasoning"
            })
            
            integration_result = await self._integrate_knowledge(initial_response, session_id)
            reasoning_trace[-1]["result"] = integration_result
            
            # Step 4: Self-reflection (if enabled)
            if self.enable_self_reflection:
                reasoning_trace.append({
                    "step": 4,
                    "action": "self_reflection",
                    "timestamp": time.time(),
                    "description": "Reflecting on reasoning quality and gaps"
                })
                
                reflection = await self._perform_self_reflection(reasoning_trace, initial_response)
                reasoning_trace[-1]["result"] = reflection
            
            # Step 5: Response generation
            reasoning_trace.append({
                "step": 5,
                "action": "response_generation",
                "timestamp": time.time(),
                "description": "Generating final structured response"
            })
            
            final_response = await self._generate_response(initial_response, reasoning_trace)
            reasoning_trace[-1]["result"] = final_response
            
            # Step 6: Transparency logging
            await self._log_cognitive_transparency(session_id, reasoning_trace, final_response)
            
            processing_time = time.time() - start_time
            
            # Update metrics
            self.processing_metrics["total_queries"] += 1
            self.processing_metrics["successful_queries"] += 1
            self.processing_metrics["average_processing_time"] = (
                (self.processing_metrics["average_processing_time"] * (self.processing_metrics["total_queries"] - 1) +
                 processing_time) / self.processing_metrics["total_queries"]
            )
            
            # Store reasoning trace
            self.reasoning_traces[session_id] = reasoning_trace
            
            # Update session status
            self.active_sessions[session_id]["status"] = "completed"
            self.active_sessions[session_id]["processing_time"] = processing_time
            
            # Create cognitive response
            cognitive_response = CognitiveResponse(
                session_id=session_id,
                response=final_response,
                reasoning_trace=reasoning_trace,
                knowledge_used=knowledge_context.get("sources", []),
                confidence=final_response.get("confidence", 0.8),
                processing_time=processing_time,
                metadata={
                    "process_type": process_type.value,
                    "steps_completed": len(reasoning_trace),
                    "knowledge_items_created": integration_result.get("items_created", 0),
                    "gaps_identified": len(reflection.insights if self.enable_self_reflection else [])
                }
            )
            
            # Broadcast update via WebSocket
            if self.websocket_manager:
                await self.websocket_manager.broadcast_cognitive_update({
                    "type": "cognitive_processing_complete",
                    "session_id": session_id,
                    "processing_time": processing_time,
                    "confidence": cognitive_response.confidence,
                    "knowledge_used": len(cognitive_response.knowledge_used)
                })
            
            logger.info(f"✅ Query processed successfully (session: {session_id[:8]}...) in {processing_time:.2f}s")
            
            # Finish recording
            if enable_recording and recording_id:
                replay_harness.record_step(
                    correlation_id=correlation_id,
                    step_type=ProcessingStep.QUERY_COMPLETED,
                    input_data={"session_id": session_id},
                    output_data=final_response,
                    duration_ms=processing_time * 1000,
                    metadata={"total_steps": len(reasoning_trace)}
                )
                replay_harness.finish_recording(correlation_id, final_response)
            
            return cognitive_response
            
        except Exception as e:
            logger.error(f"❌ Error processing query (session: {session_id[:8]}...): {e}")
            self.processing_metrics["total_queries"] += 1
            
            # Record error if recording was enabled
            if enable_recording and correlation_id:
                replay_harness.record_step(
                    correlation_id=correlation_id,
                    step_type=ProcessingStep.QUERY_COMPLETED,
                    input_data={"session_id": session_id},
                    output_data={"error": str(e)},
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={"error": True},
                    error=str(e)
                )
                replay_harness.finish_recording(correlation_id, {"error": str(e), "status": "error"})
            
            # Update session status
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["status"] = "error"
                self.active_sessions[session_id]["error"] = str(e)
            
            # Return error response
            return CognitiveResponse(
                session_id=session_id,
                response={"error": str(e), "status": "error"},
                reasoning_trace=[],
                knowledge_used=[],
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": True}
            )
    
    async def reflect_on_reasoning(self, reasoning_trace: List[Dict[str, Any]]) -> ReflectionResult:
        """
        Perform self-reflection on a reasoning trace to identify improvements and gaps.
        
        Args:
            reasoning_trace: The reasoning steps to reflect upon
            
        Returns:
            ReflectionResult with insights and improvements
        """
        try:
            insights = []
            improvements = []
            knowledge_gaps = []
            learning_opportunities = []
            
            # Analyze reasoning depth and quality
            reasoning_depth = len(reasoning_trace)
            if reasoning_depth < 3:
                improvements.append("Reasoning could be more thorough with additional steps")
            
            # Analyze confidence patterns
            confidences = [step.get("result", {}).get("confidence", 1.0) for step in reasoning_trace]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            
            if avg_confidence < 0.7:
                insights.append("Low confidence indicates potential knowledge gaps or uncertainty")
                knowledge_gaps.append("Domain-specific knowledge may be insufficient")
            
            # Analyze knowledge integration
            integration_steps = [step for step in reasoning_trace if step.get("action") == "knowledge_integration"]
            if not integration_steps:
                improvements.append("Knowledge integration step missing or insufficient")
            
            # Identify learning opportunities
            if reasoning_depth >= 5:
                learning_opportunities.append("Complex reasoning completed - extract patterns for future use")
            
            confidence_adjustment = 0.0
            if avg_confidence > 0.8:
                confidence_adjustment = 0.1  # Boost confidence for high-quality reasoning
            elif avg_confidence < 0.5:
                confidence_adjustment = -0.1  # Reduce confidence for poor reasoning
            
            return ReflectionResult(
                insights=insights,
                improvements=improvements,
                confidence_adjustment=confidence_adjustment,
                knowledge_gaps_identified=knowledge_gaps,
                learning_opportunities=learning_opportunities
            )
            
        except Exception as e:
            logger.error(f"Error in reflection: {e}")
            return ReflectionResult(
                insights=[f"Reflection error: {e}"],
                improvements=["Fix reflection process"],
                confidence_adjustment=-0.2,
                knowledge_gaps_identified=["Reflection capability"],
                learning_opportunities=[]
            )
    
    async def update_knowledge_state(self, new_information: Dict[str, Any]) -> None:
        """
        Update the knowledge state with new information.
        
        Args:
            new_information: Dictionary containing new knowledge to integrate
        """
        try:
            logger.info("🔄 Updating knowledge state...")
            
            # Extract entities and relationships from new information
            if self.knowledge_pipeline:
                await self.knowledge_pipeline.process_text_document(
                    content=new_information.get("content", ""),
                    title=new_information.get("title", "Cognitive Update"),
                    metadata=new_information.get("metadata", {})
                )
                
                self.processing_metrics["knowledge_items_created"] += 1
            
            # Update cognitive transparency if available
            if hasattr(self, '_update_cognitive_transparency'):
                await self._update_cognitive_transparency(new_information)
            
            logger.info("✅ Knowledge state updated successfully")
            
        except Exception as e:
            logger.error(f"❌ Error updating knowledge state: {e}")
    
    async def identify_knowledge_gaps(self) -> List[KnowledgeGap]:
        """
        Identify knowledge gaps in the current system state.
        
        Returns:
            List of identified knowledge gaps
        """
        try:
            logger.info("🔍 Identifying knowledge gaps...")
            
            gaps = []
            
            # Analyze query patterns for missing knowledge
            if len(self.reasoning_traces) > 0:
                # Look for patterns in low-confidence responses
                low_confidence_sessions = [
                    session_id for session_id, trace in self.reasoning_traces.items()
                    if any(step.get("result", {}).get("confidence", 1.0) < 0.6 for step in trace)
                ]
                
                if low_confidence_sessions:
                    gap = KnowledgeGap(
                        description="Recurring low-confidence responses indicate knowledge gaps",
                        priority="high",
                        domain="general",
                        search_criteria={"confidence_threshold": 0.6},
                        confidence=0.8
                    )
                    gaps.append(gap)
                    self.knowledge_gaps[gap.id] = gap
            
            # Analyze knowledge pipeline statistics
            if self.knowledge_pipeline:
                try:
                    stats = self.knowledge_pipeline.get_statistics()
                    entities_count = stats.get("total_entities", 0)
                    relationships_count = stats.get("total_relationships", 0)
                    
                    if relationships_count < entities_count * 0.5:
                        gap = KnowledgeGap(
                            description="Low relationship density in knowledge graph",
                            priority="medium",
                            domain="knowledge_structure",
                            search_criteria={"relationship_density": "low"},
                            confidence=0.7
                        )
                        gaps.append(gap)
                        self.knowledge_gaps[gap.id] = gap
                except Exception as e:
                    logger.warning(f"Could not analyze knowledge pipeline stats: {e}")
            
            # Domain-specific gap analysis
            common_domains = ["science", "technology", "philosophy", "mathematics"]
            for domain in common_domains:
                domain_queries = sum(1 for session in self.active_sessions.values() 
                                   if domain.lower() in session.get("query", "").lower())
                
                if domain_queries > 2:  # If we've had multiple queries in this domain
                    gap = KnowledgeGap(
                        description=f"Increased activity in {domain} domain suggests knowledge expansion needed",
                        priority="medium",
                        domain=domain,
                        search_criteria={"domain": domain, "expand": True},
                        confidence=0.6
                    )
                    gaps.append(gap)
                    self.knowledge_gaps[gap.id] = gap
            
            self.processing_metrics["gaps_identified"] += len(gaps)
            
            logger.info(f"✅ Identified {len(gaps)} knowledge gaps")
            return gaps
            
        except Exception as e:
            logger.error(f"❌ Error identifying knowledge gaps: {e}")
            return []
    
    async def get_cognitive_state(self) -> Dict[str, Any]:
        """Get comprehensive cognitive state information."""
        try:
            state = {
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "active_sessions": len(self.active_sessions),
                "processing_metrics": self.processing_metrics.copy(),
                "knowledge_gaps": len(self.knowledge_gaps),
                "configuration": {
                    "max_reasoning_depth": self.max_reasoning_depth,
                    "min_confidence_threshold": self.min_confidence_threshold,
                    "autonomous_reasoning_enabled": self.enable_autonomous_reasoning,
                    "self_reflection_enabled": self.enable_self_reflection
                },
                "subsystems": {
                    "godelos_integration": self.godelos_integration is not None,
                    "llm_driver": self.llm_driver is not None,
                    "knowledge_pipeline": self.knowledge_pipeline is not None,
                    "websocket_manager": self.websocket_manager is not None
                }
            }
            
            # Add recent session information
            recent_sessions = list(self.active_sessions.items())[-5:]  # Last 5 sessions
            state["recent_sessions"] = [
                {
                    "session_id": session_id[:8] + "...",
                    "status": session_data.get("status", "unknown"),
                    "process_type": session_data.get("process_type", {}).get("value", "unknown"),
                    "processing_time": session_data.get("processing_time", 0)
                }
                for session_id, session_data in recent_sessions
            ]
            
            return state
            
        except Exception as e:
            logger.error(f"Error getting cognitive state: {e}")
            return {"error": str(e), "status": "error"}
    
    # Private helper methods
    
    async def _gather_knowledge_context(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather relevant knowledge context for a query."""
        try:
            knowledge_context = {"sources": [], "entities": [], "relationships": []}
            
            if self.knowledge_pipeline:
                # Search for relevant knowledge
                search_results = await self.knowledge_pipeline.search_knowledge(query)
                knowledge_context["sources"] = search_results.get("sources", [])
                knowledge_context["entities"] = search_results.get("entities", [])
                knowledge_context["relationships"] = search_results.get("relationships", [])
            
            # Add context from GodelOS integration
            if self.godelos_integration:
                try:
                    godelos_context = await self.godelos_integration.get_query_context(query)
                    knowledge_context.update(godelos_context)
                except Exception as e:
                    logger.warning(f"Could not get GodelOS context: {e}")
            
            return knowledge_context
            
        except Exception as e:
            logger.error(f"Error gathering knowledge context: {e}")
            return {"sources": [], "entities": [], "relationships": [], "error": str(e)}
    
    async def _perform_initial_reasoning(self, query: str, knowledge_context: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform initial cognitive reasoning."""
        try:
            reasoning_result = {
                "query": query,
                "response": "Processing query through cognitive architecture...",
                "confidence": 0.7,
                "reasoning_steps": [],
                "knowledge_integration": {}
            }
            
            # Use LLM driver if available
            if self.llm_driver:
                try:
                    # Prepare state for LLM
                    llm_state = {
                        "query": query,
                        "context": context,
                        "knowledge_context": knowledge_context
                    }

                    async def _run_llm():
                        return await self.llm_driver.assess_consciousness_and_direct(llm_state)

                    llm_result = await self._with_retries(_run_llm, retries=2, delay=0.4, backoff=1.8, op_name="llm_assess_consciousness_and_direct")
                    reasoning_result.update({
                        "response": llm_result.get("response", reasoning_result["response"]),
                        "confidence": llm_result.get("confidence", reasoning_result["confidence"]),
                        "reasoning_steps": llm_result.get("reasoning_steps", []),
                        "llm_directives": llm_result.get("directives_executed", [])
                    })
                except Exception as e:
                    logger.warning(f"LLM reasoning failed after retries, using fallback: {e}")
            
            # Use GodelOS integration as fallback
            elif self.godelos_integration:
                try:
                    godelos_result = await self.godelos_integration.process_query({
                        "query": query,
                        "context": context,
                        "include_reasoning": True
                    })
                    reasoning_result.update({
                        "response": godelos_result.get("answer", reasoning_result["response"]),
                        "confidence": godelos_result.get("confidence", reasoning_result["confidence"]),
                        "reasoning_steps": godelos_result.get("reasoning", [])
                    })
                except Exception as e:
                    logger.warning(f"GodelOS reasoning failed: {e}")
            
            return reasoning_result
            
        except Exception as e:
            logger.error(f"Error in initial reasoning: {e}")
            return {
                "query": query,
                "response": f"Error in reasoning: {e}",
                "confidence": 0.0,
                "reasoning_steps": [],
                "error": str(e)
            }

    async def _augment_context(self, query: str, knowledge_context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to augment knowledge context when confidence is low.

        Non-fatal best-effort: returns additional context dict to merge.
        """
        try:
            if self.knowledge_pipeline and hasattr(self.knowledge_pipeline, 'search_knowledge'):
                results = await self.knowledge_pipeline.search_knowledge(query)
                return {
                    "sources": results.get("sources", []),
                    "entities": results.get("entities", []),
                    "relationships": results.get("relationships", []),
                    "augmentation": True,
                }
        except Exception as e:
            logger.warning(f"Context augmentation failed: {e}")
        return {"augmentation": False}

    # Public: coordination telemetry
    def get_recent_coordination_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            if limit <= 0:
                return []
            data = list(self.coordination_events)
            return data[-limit:]
        except Exception:
            return []
    
    async def _integrate_knowledge(self, reasoning_result: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Integrate new knowledge from reasoning results."""
        try:
            integration_result = {"items_created": 0, "relationships_created": 0}
            
            # Extract knowledge from reasoning
            response_text = reasoning_result.get("response", "")
            if response_text and len(response_text) > 50:  # Only process substantial responses
                
                # Create knowledge document
                knowledge_doc = {
                    "content": response_text,
                    "title": f"Cognitive Response - Session {session_id[:8]}",
                    "metadata": {
                        "session_id": session_id,
                        "confidence": reasoning_result.get("confidence", 0.7),
                        "reasoning_steps": len(reasoning_result.get("reasoning_steps", [])),
                        "source": "cognitive_processing"
                    }
                }
                
                # Process through knowledge pipeline
                if self.knowledge_pipeline:
                    process_result = await self.knowledge_pipeline.process_text_document(
                        content=knowledge_doc["content"],
                        title=knowledge_doc["title"],
                        metadata=knowledge_doc["metadata"]
                    )
                    
                    integration_result["items_created"] = process_result.get("entities_extracted", 0)
                    integration_result["relationships_created"] = process_result.get("relationships_extracted", 0)
            
            return integration_result
            
        except Exception as e:
            logger.error(f"Error integrating knowledge: {e}")
            return {"items_created": 0, "relationships_created": 0, "error": str(e)}
    
    async def _perform_self_reflection(self, reasoning_trace: List[Dict[str, Any]], reasoning_result: Dict[str, Any]) -> ReflectionResult:
        """Perform self-reflection on the reasoning process."""
        try:
            return await self.reflect_on_reasoning(reasoning_trace)
        except Exception as e:
            logger.error(f"Error in self-reflection: {e}")
            return ReflectionResult(
                insights=[f"Self-reflection error: {e}"],
                improvements=["Fix self-reflection process"],
                confidence_adjustment=-0.1,
                knowledge_gaps_identified=["Self-reflection capability"],
                learning_opportunities=[]
            )
    
    async def _generate_response(self, reasoning_result: Dict[str, Any], reasoning_trace: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate the final structured response."""
        try:
            response = {
                "answer": reasoning_result.get("response", "No response generated"),
                "confidence": reasoning_result.get("confidence", 0.5),
                "reasoning": reasoning_result.get("reasoning_steps", []),
                "knowledge_used": reasoning_result.get("knowledge_integration", {}),
                "processing_metadata": {
                    "total_steps": len(reasoning_trace),
                    "processing_time": reasoning_trace[-1]["timestamp"] - reasoning_trace[0]["timestamp"] if reasoning_trace else 0,
                    "cognitive_processes": [step["action"] for step in reasoning_trace]
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "answer": f"Error generating response: {e}",
                "confidence": 0.0,
                "reasoning": [],
                "knowledge_used": {},
                "error": str(e)
            }
    
    async def _log_cognitive_transparency(self, session_id: str, reasoning_trace: List[Dict[str, Any]], response: Dict[str, Any]) -> None:
        """Log cognitive transparency information."""
        try:
            transparency_log = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "reasoning_trace": reasoning_trace,
                "final_response": response,
                "transparency_metadata": {
                    "total_steps": len(reasoning_trace),
                    "confidence": response.get("confidence", 0.0),
                    "knowledge_sources": len(response.get("knowledge_used", {})),
                    "cognitive_processes": [step["action"] for step in reasoning_trace]
                }
            }
            
            # Log to file or database
            logger.info(f"💡 Cognitive transparency logged for session {session_id[:8]}...")
            
            # Broadcast transparency update
            if self.websocket_manager:
                await self.websocket_manager.broadcast_cognitive_update({
                    "type": "transparency_update",
                    "session_id": session_id,
                    "transparency_data": transparency_log["transparency_metadata"]
                })
            
        except Exception as e:
            logger.error(f"Error logging cognitive transparency: {e}")
    
    # === Consciousness Engine Integration ===
    
    async def assess_consciousness(self, context: Dict[str, Any] = None) -> ConsciousnessState:
        """Assess current consciousness state using the consciousness engine"""
        consciousness_state = await self.consciousness_engine.assess_consciousness_state(context)
        
        # Log transparency event
        await _safe_transparency_log("log_consciousness_assessment", 
            assessment_data={
                "awareness_level": consciousness_state.awareness_level,
                "self_reflection_depth": consciousness_state.self_reflection_depth,
                "autonomous_goals": consciousness_state.autonomous_goals,
                "cognitive_integration": consciousness_state.cognitive_integration,
                "manifest_behaviors": consciousness_state.manifest_behaviors
            },
            reasoning="Systematic consciousness assessment using integrated cognitive state analysis"
        )
        
        return consciousness_state
    
    async def get_consciousness_summary(self) -> Dict[str, Any]:
        """Get comprehensive consciousness summary"""
        return await self.consciousness_engine.get_consciousness_summary()
    
    async def initiate_autonomous_goals(self, context: str = None) -> List[str]:
        """Generate autonomous goals based on current consciousness state"""
        goals = await self.consciousness_engine.initiate_autonomous_goal_generation(context)
        
        # Log transparency event (if transparency engine is available)
        await _safe_transparency_log("log_autonomous_goal_creation", 
            goals=goals,
            context={"input_context": context, "consciousness_driven": True},
            reasoning="Autonomous goal generation based on current consciousness state and identified learning opportunities"
        )
        
        return goals
    
    async def get_consciousness_trajectory(self) -> Dict[str, Any]:
        """Get consciousness development trajectory analysis"""
        summary = await self.consciousness_engine.get_consciousness_summary()
        return summary.get('consciousness_trajectory', {})
    
    def get_current_consciousness_state(self) -> ConsciousnessState:
        """Get current consciousness state without assessment"""
        return self.consciousness_engine.current_state
    
    async def trigger_consciousness_assessment(self) -> Dict[str, Any]:
        """Manually trigger consciousness assessment and return results"""
        consciousness_state = await self.assess_consciousness()
        
        # Log consciousness assessment
        logger.info(f"Consciousness Assessment - Awareness: {consciousness_state.awareness_level:.2f}, "
                   f"Reflection: {consciousness_state.self_reflection_depth}, "
                   f"Goals: {len(consciousness_state.autonomous_goals)}")
        
        return {
            'consciousness_state': consciousness_state,
            'assessment_timestamp': consciousness_state.timestamp,
            'consciousness_level': self.consciousness_engine._categorize_consciousness_level(),
            'autonomous_goals': consciousness_state.autonomous_goals,
            'manifest_behaviors': consciousness_state.manifest_behaviors
        }
    
    # Meta-cognitive methods
    async def initiate_meta_cognitive_monitoring(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate comprehensive meta-cognitive monitoring"""
        try:
            meta_state = await metacognitive_monitor.initiate_self_monitoring(context)
            
            # Log transparency event
            await _safe_transparency_log("log_meta_cognitive_reflection", 
                reflection_data={
                    "self_awareness_level": meta_state.self_awareness_level,
                    "reflection_depth": meta_state.reflection_depth,
                    "recursive_loops": meta_state.recursive_loops,
                    "cognitive_load": meta_state.cognitive_load
                },
                depth=meta_state.reflection_depth,
                reasoning="Initiated comprehensive meta-cognitive monitoring of cognitive processes"
            )
            
            return {
                "meta_cognitive_state": asdict(meta_state),
                "monitoring_initiated": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error initiating meta-cognitive monitoring: {e}")
            return {"error": str(e), "monitoring_initiated": False}
    
    async def perform_meta_cognitive_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep meta-cognitive analysis"""
        try:
            analysis = await metacognitive_monitor.perform_meta_cognitive_analysis(query, context)
            
            # Log transparency event for meta-cognitive analysis
            await _safe_transparency_log("log_meta_cognitive_reflection", 
                reflection_data=analysis,
                depth=analysis.get("self_reference_depth", 1),
                reasoning="Deep meta-cognitive analysis performed on query and cognitive processes"
            )
            
            return analysis
        except Exception as e:
            logger.error(f"Error in meta-cognitive analysis: {e}")
            return {"error": str(e)}
    
    async def assess_self_awareness(self) -> Dict[str, Any]:
        """Assess current self-awareness level"""
        try:
            assessment = await metacognitive_monitor.assess_self_awareness()
            
            # Log transparency event
            await _safe_transparency_log("log_meta_cognitive_reflection", 
                reflection_data=assessment,
                depth=3,  # Self-awareness assessment is deep reflection
                reasoning="Comprehensive self-awareness assessment conducted"
            )
            
            return assessment
        except Exception as e:
            logger.error(f"Error in self-awareness assessment: {e}")
            return {"error": str(e)}
    
    async def get_meta_cognitive_summary(self) -> Dict[str, Any]:
        """Get comprehensive meta-cognitive summary"""
        try:
            return await metacognitive_monitor.get_meta_cognitive_summary()
        except Exception as e:
            logger.error(f"Error getting meta-cognitive summary: {e}")
            return {"error": str(e)}
    
    # Autonomous learning methods
    async def analyze_knowledge_gaps(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze and identify knowledge gaps for autonomous learning"""
        try:
            gaps = await autonomous_learning_system.analyze_knowledge_gaps(context or {})
            
            # Log transparency event
            await _safe_transparency_log("log_knowledge_integration", 
                domains=list(set([gap.domain.value for gap in gaps])),
                connections=len(gaps),
                novel_insights=[gap.gap_description for gap in gaps[:3]],
                reasoning="Identified knowledge gaps through systematic analysis for autonomous learning focus"
            )
            
            return {
                "knowledge_gaps": [asdict(gap) for gap in gaps],
                "gap_count": len(gaps),
                "domains_affected": list(set([gap.domain.value for gap in gaps])),
                "critical_gaps": [asdict(gap) for gap in gaps if gap.severity > 0.7],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error analyzing knowledge gaps: {e}")
            return {"error": str(e)}
    
    async def generate_autonomous_learning_goals(self, 
                                               focus_domains: List[str] = None,
                                               urgency: str = "medium") -> Dict[str, Any]:
        """Generate autonomous learning goals based on current state"""
        try:
            # Convert string domains to enum if provided
            domain_enums = []
            if focus_domains:
                from .autonomous_learning import LearningDomain
                for domain_str in focus_domains:
                    try:
                        domain_enums.append(LearningDomain(domain_str.lower()))
                    except ValueError:
                        continue
            
            goals = await autonomous_learning_system.generate_autonomous_learning_goals(
                focus_domains=domain_enums or None,
                urgency_level=urgency
            )
            
            # Log transparency event
            await _safe_transparency_log("log_autonomous_goal_creation", 
                goals=[goal.description for goal in goals],
                context={
                    "focus_domains": focus_domains,
                    "urgency": urgency,
                    "learning_driven": True
                },
                reasoning="Generated autonomous learning goals based on identified knowledge gaps and learning priorities"
            )
            
            return {
                "learning_goals": [autonomous_learning_system._serialize_goal(goal) for goal in goals],
                "goal_count": len(goals),
                "domains_covered": list(set([goal.domain.value for goal in goals])),
                "total_estimated_hours": sum(goal.estimated_duration for goal in goals),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating autonomous learning goals: {e}")
            return {"error": str(e)}
    
    async def create_learning_plan(self, goal_ids: List[str] = None) -> Dict[str, Any]:
        """Create comprehensive learning plan"""
        try:
            # Get goals if specific IDs provided
            goals = None
            if goal_ids:
                goals = [autonomous_learning_system.active_goals.get(goal_id) for goal_id in goal_ids]
                goals = [goal for goal in goals if goal is not None]
            
            plan = await autonomous_learning_system.create_learning_plan(goals)
            
            return {
                "learning_plan": asdict(plan),
                "plan_id": plan.id,
                "goals_included": len(plan.goals),
                "estimated_duration": plan.estimated_total_duration,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error creating learning plan: {e}")
            return {"error": str(e)}
    
    async def assess_learning_skills(self, domains: List[str] = None) -> Dict[str, Any]:
        """Assess current skill levels across learning domains"""
        try:
            # Convert string domains to enum if provided
            domain_enums = None
            if domains:
                from .autonomous_learning import LearningDomain
                domain_enums = []
                for domain_str in domains:
                    try:
                        domain_enums.append(LearningDomain(domain_str.lower()))
                    except ValueError:
                        continue
            
            assessments = await autonomous_learning_system.assess_current_skills(domain_enums)
            
            return {
                "skill_assessments": {domain.value: asdict(assessment) for domain, assessment in assessments.items()},
                "domains_assessed": len(assessments),
                "average_skill_level": sum(assessment.current_level for assessment in assessments.values()) / len(assessments) if assessments else 0.0,
                "improvement_needed": sum(assessment.improvement_needed for assessment in assessments.values()),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error assessing learning skills: {e}")
            return {"error": str(e)}
    
    async def track_learning_progress(self, goal_id: str, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track progress on a learning goal"""
        try:
            success = await autonomous_learning_system.track_learning_progress(goal_id, progress_data)
            
            return {
                "goal_id": goal_id,
                "progress_updated": success,
                "progress_data": progress_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error tracking learning progress: {e}")
            return {"error": str(e)}
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Generate insights about learning patterns and effectiveness"""
        try:
            insights = await autonomous_learning_system.generate_learning_insights()
            
            return {
                "learning_insights": insights,
                "insight_count": len(insights.get("insights", [])),
                "recommendations_count": len(insights.get("recommendations", [])),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting learning insights: {e}")
            return {"error": str(e)}
    
    async def get_autonomous_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of autonomous learning system"""
        try:
            return await autonomous_learning_system.get_learning_summary()
        except Exception as e:
            logger.error(f"Error getting autonomous learning summary: {e}")
            return {"error": str(e)}
    
    # Knowledge Graph Evolution Methods
    
    async def evolve_knowledge_graph(self, 
                                   trigger: str,
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger knowledge graph evolution based on new information or patterns"""
        try:
            from .knowledge_graph_evolution import EvolutionTrigger
            
            # Convert string trigger to enum
            trigger_enum = EvolutionTrigger(trigger.lower()) if isinstance(trigger, str) else trigger
            
            result = await knowledge_graph_evolution.evolve_knowledge_graph(
                trigger=trigger_enum,
                context=context or {}
            )
            
            # Log transparency event
            await _safe_transparency_log("log_cognitive_event", 
                event_type="knowledge_graph_evolution",
                content=f"Knowledge graph evolved due to {trigger}",
                metadata={
                    "trigger": trigger,
                    "evolution_id": result.get("evolution_id"),
                    "changes_count": len(result.get("changes_made", {})),
                    "validation_score": result.get("validation_score", 0)
                },
                reasoning="Knowledge graph evolution triggered to adapt cognitive structure"
            )
            
            return result
        except Exception as e:
            logger.error(f"Error evolving knowledge graph: {e}")
            return {"error": str(e)}
    
    async def add_knowledge_concept(self, 
                                  concept_data: Dict[str, Any],
                                  auto_connect: bool = True) -> Dict[str, Any]:
        """Add a new concept to the knowledge graph"""
        try:
            concept = await knowledge_graph_evolution.add_concept(
                concept_data=concept_data,
                auto_connect=auto_connect
            )
            
            # Log transparency event
            await _safe_transparency_log("log_cognitive_event", 
                event_type="concept_addition",
                content=f"New concept added: {concept.name}",
                metadata={
                    "concept_id": concept.id,
                    "concept_type": concept.concept_type,
                    "activation_strength": concept.activation_strength,
                    "auto_connect": auto_connect
                },
                reasoning="New concept integrated into knowledge graph structure"
            )
            
            # Automatically trigger phenomenal experience for bidirectional integration
            logger.info(f"Attempting to auto-trigger phenomenal experience for concept: {concept.name}")
            from .phenomenal_experience import ExperienceType
            
            trigger_context = {
                "trigger_source": "knowledge_graph_addition",
                "concept_id": concept.id,
                "concept_name": concept.name,
                "concept_type": concept.concept_type,
                "auto_triggered": True,
                "description": f"Knowledge concept '{concept.name}' integrated into graph"
            }
            
            pe_result = await phenomenal_experience_generator.generate_experience(
                trigger_context=trigger_context,
                experience_type=ExperienceType.COGNITIVE,
                desired_intensity=concept.activation_strength
            )
            logger.info(f"Auto-triggered phenomenal experience: {pe_result.id}")
            
            return {
                "concept_id": concept.id,
                "concept_name": concept.name,
                "concept_type": concept.concept_type,
                "activation_strength": concept.activation_strength,
                "status": concept.status.value,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error adding knowledge concept: {e}")
            return {"error": str(e)}
    
    async def create_knowledge_relationship(self,
                                          source_concept: str,
                                          target_concept: str,
                                          relationship_type: str,
                                          strength: float = 0.5,
                                          evidence: List[str] = None) -> Dict[str, Any]:
        """Create a relationship between knowledge concepts"""
        try:
            from .knowledge_graph_evolution import RelationshipType
            
            # Convert string to enum
            rel_type = RelationshipType(relationship_type.lower())
            
            relationship = await knowledge_graph_evolution.create_relationship(
                source_id=source_concept,
                target_id=target_concept,
                relationship_type=rel_type,
                strength=strength,
                evidence=evidence or []
            )
            
            # Log transparency event
            await _safe_transparency_log("log_cognitive_event", 
                event_type="relationship_creation",
                content=f"Relationship created: {source_concept} -> {target_concept} ({relationship_type})",
                metadata={
                    "relationship_id": relationship.id,
                    "relationship_type": relationship_type,
                    "strength": strength,
                    "bidirectional": relationship.bidirectional
                },
                reasoning="Knowledge relationship established to enhance cognitive connections"
            )
            
            # Automatically trigger phenomenal experience for bidirectional integration
            try:
                from .phenomenal_experience import ExperienceType
                
                trigger_context = {
                    "trigger_source": "knowledge_graph_relationship",
                    "relationship_id": relationship.id,
                    "source_concept": source_concept,
                    "target_concept": target_concept,
                    "relationship_type": relationship_type,
                    "auto_triggered": True,
                    "description": f"Knowledge relationship '{relationship_type}' created between concepts"
                }
                
                pe_result = await phenomenal_experience_generator.generate_experience(
                    trigger_context=trigger_context,
                    experience_type=ExperienceType.COGNITIVE,
                    desired_intensity=strength
                )
                logger.info(f"Auto-triggered phenomenal experience for relationship creation: {pe_result.id}")
            except Exception as pe_error:
                logger.warning(f"Failed to auto-trigger phenomenal experience for relationship creation: {pe_error}")
            
            return {
                "relationship_id": relationship.id,
                "source_concept": source_concept,
                "target_concept": target_concept,
                "relationship_type": relationship_type,
                "strength": strength,
                "confidence": relationship.confidence,
                "bidirectional": relationship.bidirectional,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error creating knowledge relationship: {e}")
            return {"error": str(e)}
    
    async def detect_emergent_patterns(self) -> Dict[str, Any]:
        """Detect emergent patterns in the knowledge graph"""
        try:
            patterns = await knowledge_graph_evolution.detect_emergent_patterns()
            
            # Log transparency event
            await _safe_transparency_log("log_cognitive_event", 
                event_type="pattern_detection",
                content=f"Detected {len(patterns)} emergent patterns in knowledge graph",
                metadata={
                    "patterns_found": len(patterns),
                    "pattern_types": [p.pattern_type for p in patterns],
                    "average_strength": sum(p.strength for p in patterns) / len(patterns) if patterns else 0
                },
                reasoning="Pattern detection executed to identify emerging knowledge structures"
            )
            
            return {
                "patterns_detected": len(patterns),
                "patterns": [
                    {
                        "id": pattern.id,
                        "type": pattern.pattern_type,
                        "description": pattern.description,
                        "strength": pattern.strength,
                        "confidence": pattern.confidence,
                        "concepts_involved": len(pattern.involved_concepts),
                        "relationships_involved": len(pattern.involved_relationships)
                    }
                    for pattern in patterns
                ],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error detecting emergent patterns: {e}")
            return {"error": str(e)}
    
    async def get_concept_neighborhood(self, 
                                    concept_id: str,
                                    depth: int = 2) -> Dict[str, Any]:
        """Get the neighborhood of concepts around a given concept"""
        try:
            neighborhood = await knowledge_graph_evolution.get_concept_neighborhood(
                concept_id=concept_id,
                depth=depth
            )
            
            # Log transparency event
            await _safe_transparency_log("log_cognitive_event", 
                event_type="neighborhood_analysis",
                content=f"Analyzed neighborhood for concept {concept_id} at depth {depth}",
                metadata={
                    "concept_id": concept_id,
                    "depth": depth,
                    "neighborhood_size": neighborhood.get("neighborhood_size", 0),
                    "neighborhood_density": neighborhood.get("neighborhood_density", 0)
                },
                reasoning="Concept neighborhood analysis to understand local knowledge structure"
            )
            
            return neighborhood
        except Exception as e:
            logger.error(f"Error getting concept neighborhood: {e}")
            return {"error": str(e)}
    
    async def get_knowledge_graph_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of knowledge graph evolution"""
        try:
            return await knowledge_graph_evolution.get_evolution_summary()
        except Exception as e:
            logger.error(f"Error getting knowledge graph summary: {e}")
            return {"error": str(e)}

    # Bidirectional Cognitive Architecture Integration Methods
    
    async def evolve_knowledge_graph_with_experience_trigger(self, 
                                                          trigger: str,
                                                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evolve knowledge graph and automatically trigger corresponding phenomenal experiences"""
        try:
            # First evolve the knowledge graph
            kg_result = await self.evolve_knowledge_graph(trigger, context)
            
            if kg_result.get("error"):
                return kg_result
            
            # Automatically trigger corresponding phenomenal experiences
            experience_results = []
            
            # Map KG evolution triggers to experience types
            trigger_to_experience_map = {
                "new_information": "cognitive",
                "pattern_discovery": "attention", 
                "concept_formation": "metacognitive",
                "relationship_strengthening": "cognitive",
                "memory_consolidation": "memory",
                "insight_generation": "imaginative",
                "contradiction_resolution": "metacognitive",
                "knowledge_integration": "cognitive",
                "learning_reinforcement": "attention",
                "novel_connection": "imaginative",
                "research_question": "cognitive",
                "evidence_gathering": "attention",
                "theory_formation": "metacognitive"
            }
            
            # Get appropriate experience type
            experience_type = trigger_to_experience_map.get(trigger, "cognitive")
            
            # Generate experience based on KG evolution
            experience_context = {
                "trigger_source": "knowledge_graph_evolution",
                "kg_evolution_id": kg_result.get("evolution_id"),
                "concepts_involved": kg_result.get("concepts_involved", []),
                "evolution_type": trigger,
                "knowledge_context": context or {}
            }
            
            # Generate the triggered experience
            experience = await phenomenal_experience_generator.generate_experience(
                trigger_context=experience_context,
                experience_type=experience_type,
                desired_intensity=0.7
            )
            
            experience_results.append({
                "experience_id": experience.id,
                "experience_type": experience.experience_type.value,
                "triggered_by": trigger,
                "narrative": experience.narrative_description
            })
            
            # Log integrated cognitive event
            await _safe_transparency_log("log_cognitive_event", 
                event_type="integrated_kg_pe_evolution",
                content=f"Knowledge graph evolution '{trigger}' triggered phenomenal experience '{experience_type}'",
                metadata={
                    "kg_evolution_id": kg_result.get("evolution_id"),
                    "experience_id": experience.id,
                    "trigger": trigger,
                    "experience_type": experience_type,
                    "integration_mode": "automatic"
                },
                reasoning="Bidirectional cognitive architecture integration: KG evolution automatically triggered corresponding phenomenal experience"
            )
            
            return {
                **kg_result,
                "triggered_experiences": experience_results,
                "integration_status": "successful",
                "bidirectional": True
            }
            
        except Exception as e:
            logger.error(f"Error in integrated KG evolution with experience trigger: {e}")
            return {"error": str(e)}
    
    async def generate_experience_with_kg_evolution(self,
                                                  experience_type: str,
                                                  trigger_context: str,
                                                  desired_intensity: float = 0.5,
                                                  context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate phenomenal experience and automatically trigger corresponding KG evolution"""
        try:
            # Create trigger context for the experience
            experience_trigger_context = {
                "description": trigger_context,
                "trigger_source": "external_request",
                "desired_intensity": desired_intensity,
                **(context or {})
            }
            
            # Convert string experience type to enum
            from backend.core.phenomenal_experience import ExperienceType
            if isinstance(experience_type, str):
                try:
                    experience_type_enum = ExperienceType(experience_type.lower())
                except ValueError:
                    # Fallback to cognitive if invalid type
                    experience_type_enum = ExperienceType.COGNITIVE
            else:
                experience_type_enum = experience_type
            
            # First generate the phenomenal experience with proper type
            experience = await phenomenal_experience_generator.generate_experience(
                trigger_context=experience_trigger_context,
                experience_type=experience_type_enum,
                desired_intensity=desired_intensity
            )
            
            # Automatically trigger corresponding KG evolution
            kg_results = []
            
            # Map experience types to KG evolution triggers
            experience_to_kg_map = {
                "cognitive": "new_information",
                "metacognitive": "emergent_concept", 
                "attention": "pattern_recognition",  # Fixed: was pattern_discovery
                "memory": "learning_feedback",       # Fixed: was memory_consolidation
                "imaginative": "emergent_concept",   # Fixed: was novel_connection
                "emotional": "usage_frequency",     # Fixed: was relationship_strengthening
                "social": "new_information",        # Fixed: was knowledge_integration
                "temporal": "temporal_decay",
                "spatial": "pattern_recognition",   # Fixed: was pattern_discovery
                "sensory": "new_information"
            }
            
            # Get appropriate KG trigger
            kg_trigger = experience_to_kg_map.get(experience_type, "new_information")
            
            # Create KG evolution context from experience
            kg_context = {
                "trigger_source": "phenomenal_experience",
                "experience_id": experience.id,
                "experience_narrative": experience.narrative_description,
                "associated_concepts": experience.associated_concepts,
                "causal_triggers": experience.causal_triggers,
                "experience_context": context or {}
            }
            
            # Trigger KG evolution
            kg_result = await self.evolve_knowledge_graph(kg_trigger, kg_context)
            
            if not kg_result.get("error"):
                kg_results.append({
                    "evolution_id": kg_result.get("evolution_id"),
                    "trigger": kg_trigger,
                    "triggered_by_experience": experience.id,
                    "concepts_involved": kg_result.get("concepts_involved", [])
                })
            
            # Log integrated cognitive event
            await _safe_transparency_log("log_cognitive_event", 
                event_type="integrated_pe_kg_evolution",
                content=f"Phenomenal experience '{experience_type}' triggered knowledge graph evolution '{kg_trigger}'",
                metadata={
                    "experience_id": experience.id,
                    "kg_evolution_id": kg_result.get("evolution_id"),
                    "experience_type": experience_type,
                    "kg_trigger": kg_trigger,
                    "integration_mode": "automatic"
                },
                reasoning="Bidirectional cognitive architecture integration: phenomenal experience automatically triggered corresponding KG evolution"
            )
            
            return {
                "experience": {
                    "id": experience.id,
                    "type": experience.experience_type.value,
                    "narrative": experience.narrative_description,
                    "vividness": experience.vividness,
                    "coherence": experience.coherence
                },
                "triggered_kg_evolutions": kg_results,
                "integration_status": "successful",
                "bidirectional": True
            }
            
        except Exception as e:
            logger.error(f"Error in integrated experience generation with KG evolution: {e}")
            return {"error": str(e)}
    
    async def process_cognitive_loop(self,
                                   initial_trigger: str,
                                   trigger_type: str = "knowledge",  # "knowledge" or "experience"
                                   loop_depth: int = 3,
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a full cognitive loop with bidirectional KG-PE integration"""
        try:
            loop_results = []
            current_context = context or {}
            
            for step in range(loop_depth):
                step_result = {
                    "step": step + 1,
                    "timestamp": datetime.now().isoformat()
                }
                
                if trigger_type == "knowledge" or step % 2 == 0:
                    # KG evolution step that triggers experiences
                    kg_trigger = initial_trigger if step == 0 else "knowledge_integration"
                    result = await self.evolve_knowledge_graph_with_experience_trigger(
                        kg_trigger, current_context
                    )
                    step_result["type"] = "kg_evolution_with_experience"
                    step_result["primary_trigger"] = kg_trigger
                    
                else:
                    # Experience generation step that triggers KG evolution
                    exp_type = "metacognitive" if step > 1 else "cognitive" 
                    result = await self.generate_experience_with_kg_evolution(
                        exp_type, f"Cognitive loop step {step + 1}", 0.6, current_context
                    )
                    step_result["type"] = "experience_with_kg_evolution"
                    step_result["primary_trigger"] = exp_type
                
                step_result["result"] = result
                step_result["integration_successful"] = not result.get("error") and result.get("bidirectional")
                
                # Update context for next iteration
                if result.get("triggered_experiences"):
                    current_context["previous_experiences"] = [
                        exp["experience_id"] for exp in result["triggered_experiences"]
                    ]
                if result.get("triggered_kg_evolutions"):
                    current_context["previous_evolutions"] = [
                        evo["evolution_id"] for evo in result["triggered_kg_evolutions"]
                    ]
                
                loop_results.append(step_result)
                
                # Break if there was an error
                if result.get("error"):
                    break
            
            # Calculate overall cognitive coherence
            successful_steps = sum(1 for step in loop_results if step["integration_successful"])
            coherence_score = successful_steps / len(loop_results) if loop_results else 0
            
            # Log cognitive loop completion
            await _safe_transparency_log("log_cognitive_event", 
                event_type="cognitive_loop_completion",
                content=f"Completed cognitive loop with {successful_steps}/{len(loop_results)} successful integrations",
                metadata={
                    "initial_trigger": initial_trigger,
                    "trigger_type": trigger_type,
                    "loop_depth": loop_depth,
                    "successful_steps": successful_steps,
                    "coherence_score": coherence_score,
                    "total_steps": len(loop_results)
                },
                reasoning="Full bidirectional cognitive architecture loop demonstrating integrated KG-PE functioning"
            )
            
            return {
                "loop_id": f"cognitive_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "steps": loop_results,
                "coherence_score": coherence_score,
                "successful_integrations": successful_steps,
                "total_steps": len(loop_results),
                "status": "completed" if coherence_score > 0.5 else "degraded"
            }
            
        except Exception as e:
            logger.error(f"Error in cognitive loop processing: {e}")
            return {"error": str(e)}
    
    # Enhanced coordination helper methods
    
    async def _augment_context(self, knowledge_context: Dict[str, Any], 
                             augmentation_params: Dict[str, Any]) -> Dict[str, Any]:
        """Augment context based on coordination decision."""
        try:
            augmented_context = knowledge_context.copy()
            sources = augmentation_params.get("sources", [])
            depth = augmentation_params.get("depth", "shallow")
            
            logger.info(f"🔍 Augmenting context with sources: {sources}")
            
            # Knowledge graph augmentation
            if "knowledge_graph" in sources:
                try:
                    graph_context = await knowledge_graph_evolution.get_related_concepts(
                        knowledge_context.get("entities", [])
                    )
                    augmented_context["graph_relationships"] = graph_context
                except Exception as e:
                    logger.warning(f"Knowledge graph augmentation failed: {e}")
            
            # Web search augmentation
            if "web_search" in sources and self.knowledge_pipeline:
                try:
                    web_results = await self.knowledge_pipeline.search_external_sources(
                        knowledge_context.get("query", "")
                    )
                    augmented_context["external_sources"] = web_results
                except Exception as e:
                    logger.warning(f"Web search augmentation failed: {e}")
            
            # Deep context augmentation
            if depth == "deep":
                try:
                    # Get historical context from similar queries
                    similar_sessions = await self._find_similar_sessions(
                        knowledge_context.get("query", "")
                    )
                    augmented_context["historical_context"] = similar_sessions
                except Exception as e:
                    logger.warning(f"Deep context augmentation failed: {e}")
            
            return augmented_context
            
        except Exception as e:
            logger.error(f"❌ Error augmenting context: {e}")
            return knowledge_context
    
    async def _trigger_self_reflection(self, query: str, initial_response: Dict[str, Any], 
                                     reflection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger self-reflection process."""
        try:
            depth = reflection_params.get("depth", "shallow")
            
            logger.info(f"🤔 Triggering self-reflection (depth: {depth})")
            
            reflection_context = {
                "query": query,
                "initial_response": initial_response,
                "reflection_depth": depth,
                "timestamp": time.time()
            }
            
            # Use metacognitive monitor for reflection
            if hasattr(metacognitive_monitor, 'assess_reasoning_quality'):
                quality_assessment = await metacognitive_monitor.assess_reasoning_quality(
                    reasoning_trace=initial_response.get("reasoning_trace", []),
                    confidence=initial_response.get("confidence", 0.5)
                )
                reflection_context["quality_assessment"] = quality_assessment
            
            # Deep reflection involves consciousness assessment
            if depth == "deep" and self.consciousness_engine:
                consciousness_state = await self.consciousness_engine.assess_consciousness_state(
                    context=reflection_context
                )
                reflection_context["consciousness_assessment"] = consciousness_state
            
            # Generate reflection insights
            reflection_insights = []
            
            if initial_response.get("confidence", 0) < 0.7:
                reflection_insights.append("Low confidence suggests need for additional knowledge or reasoning")
            
            if len(initial_response.get("reasoning_trace", [])) < 3:
                reflection_insights.append("Shallow reasoning trace indicates potential for deeper analysis")
            
            reflection_context["insights"] = reflection_insights
            
            return reflection_context
            
        except Exception as e:
            logger.error(f"❌ Error in self-reflection: {e}")
            return {"error": str(e), "reflection_failed": True}
    
    async def _route_to_specialist(self, query: str, initial_response: Dict[str, Any], 
                                 routing_params: Dict[str, Any]) -> Dict[str, Any]:
        """Route query to specialist components."""
        try:
            specialist = routing_params.get("specialist", "general")
            avoid_components = routing_params.get("avoid_components", [])
            
            logger.info(f"🎯 Routing to specialist: {specialist}")
            
            specialist_result = initial_response.copy()
            
            # Scientific reasoning specialist
            if specialist == "scientific_reasoning":
                try:
                    # Use enhanced reasoning for scientific queries
                    if self.llm_driver:
                        scientific_prompt = f"""
                        As a scientific reasoning specialist, analyze this query with rigorous methodology:
                        
                        Query: {query}
                        
                        Please provide:
                        1. Scientific domain classification
                        2. Key concepts and principles involved
                        3. Evidence-based reasoning
                        4. Potential hypotheses or explanations
                        5. Experimental or observational suggestions
                        """
                        
                        specialist_response = await self._with_retries(
                            lambda: self.llm_driver.generate_response(scientific_prompt),
                            op_name="scientific_reasoning_specialist",
                            service_type="llm"
                        )
                        
                        specialist_result["specialist_analysis"] = specialist_response
                        specialist_result["specialist_type"] = "scientific_reasoning"
                        
                except Exception as e:
                    logger.warning(f"Scientific reasoning specialist failed: {e}")
            
            # Mathematical reasoning specialist
            elif specialist == "mathematical_reasoning":
                try:
                    if self.llm_driver:
                        math_prompt = f"""
                        As a mathematical reasoning specialist, analyze this query:
                        
                        Query: {query}
                        
                        Please provide:
                        1. Mathematical concepts involved
                        2. Formal representation if applicable
                        3. Step-by-step logical reasoning
                        4. Verification methods
                        5. Alternative approaches
                        """
                        
                        specialist_response = await self._with_retries(
                            lambda: self.llm_driver.generate_response(math_prompt),
                            op_name="mathematical_reasoning_specialist",
                            service_type="llm"
                        )
                        
                        specialist_result["specialist_analysis"] = specialist_response
                        specialist_result["specialist_type"] = "mathematical_reasoning"
                        
                except Exception as e:
                    logger.warning(f"Mathematical reasoning specialist failed: {e}")
            
            # Philosophical reasoning specialist
            elif specialist == "philosophical_reasoning":
                try:
                    if self.llm_driver:
                        phil_prompt = f"""
                        As a philosophical reasoning specialist, analyze this query:
                        
                        Query: {query}
                        
                        Please provide:
                        1. Philosophical domains and traditions relevant
                        2. Key arguments and counterarguments
                        3. Logical structure analysis
                        4. Ethical considerations if applicable
                        5. Broader implications and connections
                        """
                        
                        specialist_response = await self._with_retries(
                            lambda: self.llm_driver.generate_response(phil_prompt),
                            op_name="philosophical_reasoning_specialist",
                            service_type="llm"
                        )
                        
                        specialist_result["specialist_analysis"] = specialist_response
                        specialist_result["specialist_type"] = "philosophical_reasoning"
                        
                except Exception as e:
                    logger.warning(f"Philosophical reasoning specialist failed: {e}")
            
            return specialist_result
            
        except Exception as e:
            logger.error(f"❌ Error routing to specialist: {e}")
            return initial_response
    
    async def _find_similar_sessions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar historical sessions for context."""
        try:
            similar_sessions = []
            query_words = set(query.lower().split())
            
            for session_id, session_data in self.active_sessions.items():
                session_query = session_data.get("query", "")
                session_words = set(session_query.lower().split())
                
                # Simple similarity based on word overlap
                overlap = len(query_words.intersection(session_words))
                if overlap > 1:  # At least 2 words in common
                    similarity = overlap / len(query_words.union(session_words))
                    
                    similar_sessions.append({
                        "session_id": session_id[:8] + "...",
                        "query": session_query[:100] + "..." if len(session_query) > 100 else session_query,
                        "similarity": similarity,
                        "context": session_data.get("context", {})
                    })
            
            # Sort by similarity and return top results
            similar_sessions.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_sessions[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error finding similar sessions: {e}")
            return []


# Global instance
cognitive_manager: Optional[CognitiveManager] = None


async def get_cognitive_manager(godelos_integration=None, llm_driver=None, knowledge_pipeline=None, websocket_manager=None) -> CognitiveManager:
    """Get or create the global cognitive manager instance."""
    global cognitive_manager
    
    if cognitive_manager is None:
        cognitive_manager = CognitiveManager(
            godelos_integration=godelos_integration,
            llm_driver=llm_driver,
            knowledge_pipeline=knowledge_pipeline,
            websocket_manager=websocket_manager
        )
        await cognitive_manager.initialize()
    
    return cognitive_manager
