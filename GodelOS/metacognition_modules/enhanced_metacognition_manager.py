"""
Enhanced Metacognition Manager with Autonomous Knowledge Acquisition.

This module extends the existing metacognition system with autonomous knowledge
acquisition capabilities and real-time stream of consciousness visibility.
"""

import asyncio
import logging
import time
import json
import sys
import os
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

# Add GödelOS to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

try:
    from godelOS.metacognition.manager import MetacognitionManager as BaseMetacognitionManager
    GODELOS_AVAILABLE = True
except ImportError:
    # Fallback for testing without full GödelOS
    BaseMetacognitionManager = object
    GODELOS_AVAILABLE = False

from backend.metacognition_modules.cognitive_models import (
    KnowledgeGap, CognitiveEvent, AcquisitionPlan, AcquisitionResult,
    CognitiveEventType, GranularityLevel
)
from backend.metacognition_modules.knowledge_gap_detector import KnowledgeGapDetector
from backend.metacognition_modules.autonomous_knowledge_acquisition import AutonomousKnowledgeAcquisition
from backend.metacognition_modules.stream_coordinator import StreamOfConsciousnessCoordinator

logger = logging.getLogger(__name__)


@dataclass
class AutonomousLearningConfig:
    """Configuration for autonomous learning capabilities."""
    enabled: bool = True
    gap_detection_interval: int = 300  # seconds
    confidence_threshold: float = 0.7
    auto_approval_threshold: float = 0.8
    max_concurrent_acquisitions: int = 3
    
    
@dataclass
class CognitiveStreamingConfig:
    """Configuration for cognitive streaming capabilities."""
    enabled: bool = True
    default_granularity: GranularityLevel = GranularityLevel.STANDARD
    max_event_rate: int = 100  # events per second
    buffer_size: int = 1000
    websocket_timeout: int = 30


class EnhancedMetacognitionManager(BaseMetacognitionManager):
    """
    Enhanced Metacognition Manager with autonomous knowledge acquisition
    and real-time cognitive streaming capabilities.
    
    This class provides:
    - Autonomous knowledge gap detection and filling
    - Real-time stream of consciousness visibility
    - Question-triggered learning processes
    - Configurable cognitive transparency
    """
    
    def __init__(
        self,
        websocket_manager=None,
        knowledge_store=None,
        query_processor=None,
        config=None,
        autonomous_config: Optional[AutonomousLearningConfig] = None,
        streaming_config: Optional[CognitiveStreamingConfig] = None,
        **kwargs
    ):
        """
        Initialize the enhanced metacognition manager.
        
        Args:
            websocket_manager: WebSocket manager for real-time streaming
            knowledge_store: Knowledge storage interface
            query_processor: Query processing system
            config: Configuration dictionary
            autonomous_config: Configuration for autonomous learning
            streaming_config: Configuration for cognitive streaming
        """
        # Initialize base class if available
        if GODELOS_AVAILABLE and hasattr(super(), '__init__'):
            # For testing or when base class needs different args, skip super init
            try:
                if 'kr_system_interface' in kwargs or 'type_system' in kwargs:
                    super().__init__(**kwargs)
            except Exception as e:
                logger.warning(f"Base class initialization failed: {e}")
        
        self.websocket_manager = websocket_manager
        self.knowledge_store = knowledge_store
        self.query_processor = query_processor
        self.config = config or {}
        
        # Configuration
        self.autonomous_config = autonomous_config or AutonomousLearningConfig()
        self.streaming_config = streaming_config or CognitiveStreamingConfig()
        
        # Core components
        self.knowledge_gap_detector = KnowledgeGapDetector(
            knowledge_store=knowledge_store,
            confidence_threshold=self.autonomous_config.confidence_threshold
        )
        
        self.autonomous_knowledge_acquisition = AutonomousKnowledgeAcquisition(
            knowledge_store=knowledge_store,
            gap_detector=self.knowledge_gap_detector
        )
        
        self.stream_coordinator = StreamOfConsciousnessCoordinator(
            websocket_manager=websocket_manager,
            config=streaming_config
        )
        
        # State tracking
        self.active_acquisitions: Dict[str, AcquisitionPlan] = {}
        self.detected_gaps: List[KnowledgeGap] = []
        self.acquisition_history: List[AcquisitionResult] = []
        
        # Metacognitive cycle state
        self.current_cycle_id: Optional[str] = None
        self.cycle_start_time: Optional[float] = None
        self.is_running = False
        self.is_initialized = False  # Required by base class
        self.godelos_integration = None  # GödelOS integration instance
        
        # Async task management
        self.background_tasks: Set[asyncio.Task] = set()
        
        logger.info("EnhancedMetacognitionManager initialized")
    
    async def initialize(self, godelos_integration=None):
        """
        Initialize the enhanced metacognition manager with optional GödelOS integration.
        
        Args:
            godelos_integration: Optional GödelOS integration instance
        """
        try:
            # Initialize base class if available and has initialize method
            if GODELOS_AVAILABLE and hasattr(super(), 'initialize'):
                try:
                    # Call base initialize without parameters
                    await super().initialize()
                except Exception as base_init_error:
                    logger.warning(f"Base class initialization failed: {base_init_error}")
                    # Set required attributes manually
                    self.is_initialized = True
            else:
                # Set initialized flag if no base class
                self.is_initialized = True
            
            # Store GödelOS integration if provided
            if godelos_integration:
                self.godelos_integration = godelos_integration
                logger.info("GödelOS integration provided to enhanced metacognition manager")
            else:
                self.godelos_integration = None
                logger.info("Enhanced metacognition manager initialized without GödelOS integration")
            
            # Start the enhanced manager
            await self.start()
            
            logger.info("Enhanced metacognition manager initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced metacognition manager: {e}")
            raise
    
    async def start(self) -> bool:
        """
        Start the enhanced metacognition manager.
        
        Returns:
            True if started successfully
        """
        if self.is_running:
            logger.warning("Enhanced metacognition manager already running")
            return True
        
        try:
            # Start core components
            await self.stream_coordinator.start()
            
            # Connect stream coordinator to WebSocket manager
            if self.websocket_manager and hasattr(self.websocket_manager, 'set_stream_coordinator'):
                self.websocket_manager.set_stream_coordinator(self.stream_coordinator)
                logger.info("Stream coordinator connected to WebSocket manager")
            
            # Start autonomous learning if enabled
            if self.autonomous_config.enabled:
                await self._start_autonomous_learning()
            
            # Start cognitive streaming if enabled
            if self.streaming_config.enabled:
                await self._start_cognitive_streaming()
            
            self.is_running = True
            
            # Emit startup event
            await self._emit_cognitive_event(
                CognitiveEventType.SYSTEM_STARTUP,
                {"component": "EnhancedMetacognitionManager"},
                GranularityLevel.STANDARD
            )
            
            logger.info("Enhanced metacognition manager started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start enhanced metacognition manager: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop the enhanced metacognition manager."""
        if not self.is_running:
            return
        
        # Emit shutdown event
        await self._emit_cognitive_event(
            CognitiveEventType.SYSTEM_SHUTDOWN,
            {"component": "EnhancedMetacognitionManager"},
            GranularityLevel.STANDARD
        )
        
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Stop components
        await self.stream_coordinator.stop()
        
        self.is_running = False
        logger.info("Enhanced metacognition manager stopped")
    
    async def process_query_with_learning(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query with automatic knowledge acquisition if needed.
        
        Args:
            query: The query to process
            context: Optional context for processing
            
        Returns:
            Query processing results with acquisition metadata
        """
        cycle_id = str(uuid.uuid4())
        self.current_cycle_id = cycle_id
        self.cycle_start_time = time.time()
        
        # Emit query start event
        await self._emit_cognitive_event(
            CognitiveEventType.QUERY_STARTED,
            {"query": query, "cycle_id": cycle_id},
            GranularityLevel.STANDARD
        )
        
        try:
            # Process the query
            if self.query_processor:
                result = await self.query_processor.process_query(query, context)
            else:
                result = {"response": "No query processor available", "confidence": 0.0}
            
            # Check for knowledge gaps
            gaps = await self.knowledge_gap_detector.detect_gaps_from_query(
                query, result
            )
            
            if gaps:
                await self._emit_cognitive_event(
                    CognitiveEventType.GAPS_DETECTED,
                    {"gaps": [gap.to_dict() for gap in gaps], "query": query},
                    GranularityLevel.DETAILED
                )
                
                # Trigger autonomous acquisition if enabled
                if self.autonomous_config.enabled:
                    await self._trigger_knowledge_acquisition(gaps)
            
            # Emit query completion
            processing_time = time.time() - self.cycle_start_time
            await self._emit_cognitive_event(
                CognitiveEventType.QUERY_COMPLETED,
                {
                    "cycle_id": cycle_id,
                    "processing_time": processing_time,
                    "gaps_detected": len(gaps),
                    "confidence": result.get("confidence", 0.0)
                },
                GranularityLevel.STANDARD
            )
            
            # Add acquisition metadata to result
            result["metacognition"] = {
                "cycle_id": cycle_id,
                "gaps_detected": len(gaps),
                "processing_time": processing_time,
                "active_acquisitions": len(self.active_acquisitions)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query with learning: {e}")
            await self._emit_cognitive_event(
                CognitiveEventType.ERROR,
                {"error": str(e), "query": query},
                GranularityLevel.MINIMAL
            )
            raise
    
    async def configure_autonomous_learning(
        self,
        config: AutonomousLearningConfig
    ) -> bool:
        """
        Configure autonomous learning settings.
        
        Args:
            config: New autonomous learning configuration
            
        Returns:
            True if configuration was successful
        """
        try:
            self.autonomous_config = config
            
            # Update gap detector configuration
            self.knowledge_gap_detector.confidence_threshold = config.confidence_threshold
            
            await self._emit_cognitive_event(
                CognitiveEventType.CONFIGURATION_CHANGED,
                {"component": "autonomous_learning", "config": config.__dict__},
                GranularityLevel.STANDARD
            )
            
            logger.info("Autonomous learning configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure autonomous learning: {e}")
            return False
    
    async def configure_cognitive_streaming(
        self,
        config: CognitiveStreamingConfig
    ) -> bool:
        """
        Configure cognitive streaming settings.
        
        Args:
            config: New cognitive streaming configuration
            
        Returns:
            True if configuration was successful
        """
        try:
            self.streaming_config = config
            
            # Update stream coordinator configuration
            await self.stream_coordinator.configure(config)
            
            await self._emit_cognitive_event(
                CognitiveEventType.CONFIGURATION_CHANGED,
                {"component": "cognitive_streaming", "config": config.__dict__},
                GranularityLevel.STANDARD
            )
            
            logger.info("Cognitive streaming configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure cognitive streaming: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the enhanced metacognition manager.
        
        Returns:
            Status information dictionary
        """
        return {
            "is_running": self.is_running,
            "autonomous_learning": {
                "enabled": self.autonomous_config.enabled,
                "active_acquisitions": len(self.active_acquisitions),
                "detected_gaps": len(self.detected_gaps),
                "acquisition_history_size": len(self.acquisition_history)
            },
            "cognitive_streaming": {
                "enabled": self.streaming_config.enabled,
                "connected_clients": await self.stream_coordinator.get_client_count(),
                "events_per_second": await self.stream_coordinator.get_event_rate()
            },
            "current_cycle": {
                "cycle_id": self.current_cycle_id,
                "elapsed_time": (
                    time.time() - self.cycle_start_time 
                    if self.cycle_start_time else None
                )
            }
        }
    
    # Private methods
    
    async def _start_autonomous_learning(self) -> None:
        """Start autonomous learning background tasks."""
        # Start gap detection task
        gap_detection_task = asyncio.create_task(
            self._gap_detection_loop()
        )
        self.background_tasks.add(gap_detection_task)
        
        logger.info("Autonomous learning started")
    
    async def _start_cognitive_streaming(self) -> None:
        """Start cognitive streaming capabilities."""
        # Stream coordinator is already started in start() method
        logger.info("Cognitive streaming started")
    
    async def _gap_detection_loop(self) -> None:
        """Background loop for autonomous gap detection."""
        while self.is_running:
            try:
                # Detect gaps autonomously
                gaps = await self.knowledge_gap_detector.detect_autonomous_gaps()
                
                if gaps:
                    self.detected_gaps.extend(gaps)
                    
                    await self._emit_cognitive_event(
                        CognitiveEventType.AUTONOMOUS_GAPS_DETECTED,
                        {"gaps": [gap.to_dict() for gap in gaps]},
                        GranularityLevel.DETAILED
                    )
                    
                    # Trigger acquisition for high-priority gaps
                    high_priority_gaps = [g for g in gaps if g.priority > 0.7]
                    if high_priority_gaps:
                        await self._trigger_knowledge_acquisition(high_priority_gaps)
                
                # Wait for next detection cycle
                await asyncio.sleep(self.autonomous_config.gap_detection_interval)
                
            except Exception as e:
                logger.error(f"Error in gap detection loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _trigger_knowledge_acquisition(
        self,
        gaps: List[KnowledgeGap]
    ) -> None:
        """
        Trigger knowledge acquisition for detected gaps.
        
        Args:
            gaps: List of knowledge gaps to address
        """
        for gap in gaps:
            # Check if we're under the concurrent acquisition limit
            if len(self.active_acquisitions) >= self.autonomous_config.max_concurrent_acquisitions:
                logger.warning("Maximum concurrent acquisitions reached, queuing gap")
                continue
            
            # Create acquisition plan
            plan = await self.autonomous_knowledge_acquisition.create_acquisition_plan(gap)
            
            if plan:
                # Check if plan should be auto-approved
                if plan.priority >= self.autonomous_config.auto_approval_threshold:
                    plan.approved = True
                
                # Start acquisition if approved
                if plan.approved:
                    self.active_acquisitions[plan.plan_id] = plan
                    
                    # Execute acquisition plan asynchronously
                    asyncio.create_task(self._execute_acquisition_plan(plan))

    async def _emit_cognitive_event(self, event_type: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """
        Emit a cognitive event to the WebSocket manager for real-time streaming.
        
        Args:
            event_type: Type of cognitive event
            data: Event data
            metadata: Optional metadata for the event
        """
        try:
            if self.websocket_manager and hasattr(self.websocket_manager, 'emit_cognitive_event'):
                event = {
                    "type": event_type,
                    "data": data,
                    "metadata": metadata or {},
                    "timestamp": time.time(),
                    "source": "enhanced_metacognition_manager"
                }
                await self.websocket_manager.emit_cognitive_event(event)
        except Exception as e:
            logger.warning(f"Failed to emit cognitive event {event_type}: {e}")

    async def _execute_acquisition_plan(self, plan):
        """Execute an autonomous knowledge acquisition plan."""
        # Implementation placeholder for autonomous knowledge acquisition
        logger.info(f"Executing acquisition plan: {plan.plan_id}")
