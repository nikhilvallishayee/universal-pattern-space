"""
Cognitive Engine Implementation for GodelOS

This module implements the CognitiveEngine class, which integrates the thought stream,
reflection engine, ideation engine, and metacognitive monitor to provide cognitive
processing capabilities for the UnifiedAgentCore. The enhanced implementation includes
a sophisticated thought processing pipeline with parallel processing, resource
prioritization, and event-based communication between components.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
import asyncio
from collections import defaultdict
import heapq
import random

from godelOS.unified_agent_core.cognitive_engine.interfaces import (
    Thought, Reflection, Idea, CognitiveContext, AbstractCognitiveEngine
)
from godelOS.unified_agent_core.cognitive_engine.thought_stream import ThoughtStream
from godelOS.unified_agent_core.cognitive_engine.reflection_engine import ReflectionEngine
from godelOS.unified_agent_core.cognitive_engine.ideation_engine import IdeationEngine
from godelOS.unified_agent_core.cognitive_engine.metacognitive_monitor import MetacognitiveMonitor

logger = logging.getLogger(__name__)

# Event types for the event-based communication system
EVENT_THOUGHT_ADDED = "thought_added"
EVENT_THOUGHT_PROCESSED = "thought_processed"
EVENT_REFLECTION_CREATED = "reflection_created"
EVENT_IDEA_GENERATED = "idea_generated"
EVENT_COGNITIVE_STATE_UPDATED = "cognitive_state_updated"


class CognitiveEngine(AbstractCognitiveEngine):
    """
    Enhanced CognitiveEngine implementation for GodelOS.
    
    The CognitiveEngine integrates the thought stream, reflection engine, ideation engine,
    and metacognitive monitor to provide cognitive processing capabilities for the
    UnifiedAgentCore. The enhanced implementation includes:
    
    1. Parallel processing of multiple thoughts
    2. Prioritization of cognitive resources
    3. Integration with the knowledge store and resource manager
    4. Event-based communication between components
    5. Advanced thought processing pipeline
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the cognitive engine.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        
        self.config = config or {}
        
        # Initialize components
        self.thought_stream = ThoughtStream(
            max_capacity=self.config.get("thought_stream_capacity", 1000),
            forgetting_threshold=self.config.get("forgetting_threshold", 0.2),
            retention_period=self.config.get("retention_period", 86400),
            cluster_similarity_threshold=self.config.get("cluster_similarity_threshold", 0.6)
        )
        
        self.reflection_engine = ReflectionEngine()
        self.ideation_engine = IdeationEngine()
        self.metacognitive_monitor = MetacognitiveMonitor()
        
        # Initialize processing queues with priority support
        self.thought_priority_queue: List[Tuple[float, str, Thought]] = []  # [(priority, id, thought)]
        self.reflection_priority_queue: List[Tuple[float, str, Tuple[Thought, Reflection, CognitiveContext]]] = []
        self.ideation_priority_queue: List[Tuple[float, str, Tuple[Thought, Reflection, CognitiveContext]]] = []
        
        # Initialize parallel processing settings
        self.max_parallel_thoughts = self.config.get("max_parallel_thoughts", 3)
        self.max_parallel_reflections = self.config.get("max_parallel_reflections", 2)
        self.max_parallel_ideations = self.config.get("max_parallel_ideations", 2)
        
        # Initialize active processing tracking
        self.active_thought_tasks: Dict[str, asyncio.Task] = {}
        self.active_reflection_tasks: Dict[str, asyncio.Task] = {}
        self.active_ideation_tasks: Dict[str, asyncio.Task] = {}
        
        # Initialize processing tasks
        self.pipeline_manager_task = None
        self.resource_optimizer_task = None
        
        # Initialize event system
        self.event_listeners: Dict[str, List[Callable]] = defaultdict(list)
        
        # Initialize pipeline metrics
        self.pipeline_metrics = {
            "thoughts_processed": 0,
            "reflections_created": 0,
            "ideas_generated": 0,
            "pipeline_throughput": 0.0,
            "average_processing_time": 0.0,
            "total_processing_time": 0.0,
            "start_time": 0.0
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the cognitive engine with enhanced component integration.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self.is_initialized:
            logger.warning("CognitiveEngine is already initialized")
            return True
        
        try:
            logger.info("Initializing CognitiveEngine")
            
            # Ensure components are set up
            if not all([
                self.thought_stream,
                self.reflection_engine,
                self.ideation_engine,
                self.metacognitive_monitor,
                self.state,
                self.knowledge_store,
                self.resource_manager
            ]):
                logger.error("CognitiveEngine components not properly set up")
                return False
            
            # Set up knowledge store references for components
            if self.knowledge_store:
                if hasattr(self.reflection_engine, 'set_knowledge_store'):
                    self.reflection_engine.set_knowledge_store(self.knowledge_store)
                
                if hasattr(self.ideation_engine, 'set_knowledge_store'):
                    self.ideation_engine.set_knowledge_store(self.knowledge_store)
                
                if hasattr(self.metacognitive_monitor, 'set_knowledge_store'):
                    self.metacognitive_monitor.set_knowledge_store(self.knowledge_store)
            
            # Register event listeners
            self._register_event_listeners()
            
            # Initialize pipeline metrics
            self.pipeline_metrics["start_time"] = time.time()
            
            self.is_initialized = True
            logger.info("CognitiveEngine initialized successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing CognitiveEngine: {e}")
            return False
    
    async def start(self) -> bool:
        """
        Start the cognitive engine with enhanced parallel processing pipeline.
        
        Returns:
            True if the engine was started successfully, False otherwise
        """
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                return False
        
        if self.is_running:
            logger.warning("CognitiveEngine is already running")
            return True
        
        try:
            logger.info("Starting CognitiveEngine")
            
            # Start pipeline manager task
            self.pipeline_manager_task = asyncio.create_task(self._pipeline_manager())
            
            # Start resource optimizer task
            self.resource_optimizer_task = asyncio.create_task(self._resource_optimizer())
            
            # Reset pipeline metrics
            self.pipeline_metrics = {
                "thoughts_processed": 0,
                "reflections_created": 0,
                "ideas_generated": 0,
                "pipeline_throughput": 0.0,
                "average_processing_time": 0.0,
                "total_processing_time": 0.0,
                "start_time": time.time()
            }
            
            self.is_running = True
            logger.info("CognitiveEngine started successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error starting CognitiveEngine: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the cognitive engine and all parallel processing tasks.
        
        Returns:
            True if the engine was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("CognitiveEngine is not running")
            return True
        
        try:
            logger.info("Stopping CognitiveEngine")
            
            # Cancel pipeline manager task
            if self.pipeline_manager_task:
                self.pipeline_manager_task.cancel()
                try:
                    await self.pipeline_manager_task
                except asyncio.CancelledError:
                    pass
                self.pipeline_manager_task = None
            
            # Cancel resource optimizer task
            if self.resource_optimizer_task:
                self.resource_optimizer_task.cancel()
                try:
                    await self.resource_optimizer_task
                except asyncio.CancelledError:
                    pass
                self.resource_optimizer_task = None
            
            # Cancel all active thought processing tasks
            for task_id, task in list(self.active_thought_tasks.items()):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            self.active_thought_tasks.clear()
            
            # Cancel all active reflection tasks
            for task_id, task in list(self.active_reflection_tasks.items()):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            self.active_reflection_tasks.clear()
            
            # Cancel all active ideation tasks
            for task_id, task in list(self.active_ideation_tasks.items()):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            self.active_ideation_tasks.clear()
            
            # Clear priority queues
            self.thought_priority_queue.clear()
            self.reflection_priority_queue.clear()
            self.ideation_priority_queue.clear()
            
            # Calculate final metrics
            total_time = time.time() - self.pipeline_metrics["start_time"]
            if total_time > 0:
                self.pipeline_metrics["pipeline_throughput"] = (
                    self.pipeline_metrics["thoughts_processed"] / total_time
                )
            
            if self.pipeline_metrics["thoughts_processed"] > 0:
                self.pipeline_metrics["average_processing_time"] = (
                    self.pipeline_metrics["total_processing_time"] /
                    self.pipeline_metrics["thoughts_processed"]
                )
            
            logger.info(f"Pipeline metrics: {self.pipeline_metrics}")
            
            self.is_running = False
            logger.info("CognitiveEngine stopped successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error stopping CognitiveEngine: {e}")
            return False
    
    # Event system methods
    def _register_event_listeners(self) -> None:
        """Register event listeners for component communication."""
        # Register thought stream events
        self.register_event_listener(EVENT_THOUGHT_ADDED, self._on_thought_added)
        
        # Register reflection events
        self.register_event_listener(EVENT_REFLECTION_CREATED, self._on_reflection_created)
        
        # Register ideation events
        self.register_event_listener(EVENT_IDEA_GENERATED, self._on_idea_generated)
        
        # Register cognitive state events
        self.register_event_listener(EVENT_COGNITIVE_STATE_UPDATED, self._on_cognitive_state_updated)
    
    def register_event_listener(self, event_type: str, callback: Callable) -> None:
        """
        Register an event listener.
        
        Args:
            event_type: The type of event to listen for
            callback: The callback function to call when the event occurs
        """
        self.event_listeners[event_type].append(callback)
    
    def unregister_event_listener(self, event_type: str, callback: Callable) -> None:
        """
        Unregister an event listener.
        
        Args:
            event_type: The type of event to stop listening for
            callback: The callback function to remove
        """
        if event_type in self.event_listeners and callback in self.event_listeners[event_type]:
            self.event_listeners[event_type].remove(callback)
    
    async def trigger_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Trigger an event.
        
        Args:
            event_type: The type of event to trigger
            event_data: The event data
        """
        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_data)
                    else:
                        callback(event_data)
                except Exception as e:
                    logger.error(f"Error in event listener for {event_type}: {e}")
    
    # Event handlers
    async def _on_thought_added(self, event_data: Dict[str, Any]) -> None:
        """
        Handle thought added event.
        
        Args:
            event_data: The event data
        """
        thought = event_data.get("thought")
        if thought:
            # Add to thought priority queue
            priority = thought.priority
            heapq.heappush(self.thought_priority_queue, (-priority, thought.id, thought))
    
    async def _on_reflection_created(self, event_data: Dict[str, Any]) -> None:
        """
        Handle reflection created event.
        
        Args:
            event_data: The event data
        """
        thought = event_data.get("thought")
        reflection = event_data.get("reflection")
        context = event_data.get("context")
        
        if thought and reflection and context:
            # Check if ideation should be performed
            if reflection.should_ideate:
                # Add to ideation priority queue
                priority = reflection.priority if hasattr(reflection, "priority") else 0.5
                heapq.heappush(
                    self.ideation_priority_queue,
                    (-priority, str(uuid.uuid4()), (thought, reflection, context))
                )
    
    async def _on_idea_generated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle idea generated event.
        
        Args:
            event_data: The event data
        """
        idea = event_data.get("idea")
        if idea:
            # Store high-quality ideas in knowledge store
            if idea.utility_score > 0.7 and idea.novelty_score > 0.5:
                if self.knowledge_store:
                    try:
                        knowledge_item = {
                            "type": "hypothesis" if idea.novelty_score > 0.8 else "concept",
                            "content": {
                                "text": idea.content,
                                "source": "ideation",
                                "idea_id": idea.id
                            },
                            "confidence": idea.utility_score,
                            "metadata": {
                                "novelty_score": idea.novelty_score,
                                "utility_score": idea.utility_score
                            }
                        }
                        
                        await self.knowledge_store.store_knowledge(knowledge_item)
                        logger.debug(f"Stored idea {idea.id} in knowledge store")
                    except Exception as e:
                        logger.error(f"Error storing idea in knowledge store: {e}")
    
    async def _on_cognitive_state_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle cognitive state updated event.
        
        Args:
            event_data: The event data
        """
        cognitive_load = event_data.get("cognitive_load")
        if cognitive_load is not None:
            # Adjust parallel processing settings based on cognitive load
            if cognitive_load > 0.8:
                # High load, reduce parallelism
                self.max_parallel_thoughts = max(1, self.max_parallel_thoughts - 1)
                self.max_parallel_reflections = max(1, self.max_parallel_reflections - 1)
                self.max_parallel_ideations = max(1, self.max_parallel_ideations - 1)
            elif cognitive_load < 0.3:
                # Low load, increase parallelism
                self.max_parallel_thoughts = min(5, self.max_parallel_thoughts + 1)
                self.max_parallel_reflections = min(3, self.max_parallel_reflections + 1)
                self.max_parallel_ideations = min(3, self.max_parallel_ideations + 1)
    
    # Pipeline management methods
    async def _pipeline_manager(self) -> None:
        """
        Enhanced pipeline manager task that coordinates parallel processing of thoughts,
        reflections, and ideas with advanced flow control, priority management, and
        dynamic resource allocation.
        
        The pipeline implements a multi-stage processing flow:
        1. Thought processing with priority-based scheduling
        2. Reflection processing with context-aware execution
        3. Ideation processing with adaptive resource allocation
        4. Feedback loops for continuous optimization
        """
        logger.info("Starting pipeline manager task")
        
        try:
            # Initialize pipeline state
            pipeline_state = {
                "last_optimization_time": time.time(),
                "optimization_interval": 5.0,  # seconds
                "thought_throughput": 0,
                "reflection_throughput": 0,
                "ideation_throughput": 0,
                "bottleneck_detection": {
                    "thought_queue_size_history": deque(maxlen=10),
                    "reflection_queue_size_history": deque(maxlen=10),
                    "ideation_queue_size_history": deque(maxlen=10)
                },
                "flow_control": {
                    "thought_backpressure": False,
                    "reflection_backpressure": False,
                    "ideation_backpressure": False
                }
            }
            
            while True:
                # 1. Update pipeline metrics and state
                current_time = time.time()
                
                # Track queue sizes for bottleneck detection
                pipeline_state["bottleneck_detection"]["thought_queue_size_history"].append(
                    len(self.thought_priority_queue)
                )
                pipeline_state["bottleneck_detection"]["reflection_queue_size_history"].append(
                    len(self.reflection_priority_queue)
                )
                pipeline_state["bottleneck_detection"]["ideation_queue_size_history"].append(
                    len(self.ideation_priority_queue)
                )
                
                # 2. Detect bottlenecks and adjust flow control
                if current_time - pipeline_state["last_optimization_time"] > pipeline_state["optimization_interval"]:
                    await self._optimize_pipeline_flow(pipeline_state)
                    pipeline_state["last_optimization_time"] = current_time
                
                # 3. Process each stage with flow control
                
                # 3.1 Process thoughts with backpressure awareness
                if not pipeline_state["flow_control"]["thought_backpressure"]:
                    await self._process_thoughts_in_parallel()
                
                # 3.2 Process reflections with priority-based scheduling
                reflection_slots_available = self.max_parallel_reflections - len(self.active_reflection_tasks)
                if reflection_slots_available > 0 and not pipeline_state["flow_control"]["reflection_backpressure"]:
                    # Prioritize reflections based on cognitive context
                    await self._prioritize_reflections()
                    await self._process_reflections_in_parallel()
                
                # 3.3 Process ideations with adaptive resource allocation
                ideation_slots_available = self.max_parallel_ideations - len(self.active_ideation_tasks)
                if ideation_slots_available > 0 and not pipeline_state["flow_control"]["ideation_backpressure"]:
                    # Allocate resources based on idea quality potential
                    await self._allocate_ideation_resources()
                    await self._process_ideations_in_parallel()
                
                # 4. Perform cleanup and maintenance
                await self._cleanup_stalled_tasks()
                
                # Short sleep to prevent CPU hogging
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info("Pipeline manager task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in pipeline manager: {e}")
    
    async def _optimize_pipeline_flow(self, pipeline_state: Dict[str, Any]) -> None:
        """
        Optimize pipeline flow based on current state and bottleneck detection.
        
        Args:
            pipeline_state: The current pipeline state
        """
        # Calculate average queue sizes
        avg_thought_queue_size = sum(pipeline_state["bottleneck_detection"]["thought_queue_size_history"]) / max(1, len(pipeline_state["bottleneck_detection"]["thought_queue_size_history"]))
        avg_reflection_queue_size = sum(pipeline_state["bottleneck_detection"]["reflection_queue_size_history"]) / max(1, len(pipeline_state["bottleneck_detection"]["reflection_queue_size_history"]))
        avg_ideation_queue_size = sum(pipeline_state["bottleneck_detection"]["ideation_queue_size_history"]) / max(1, len(pipeline_state["bottleneck_detection"]["ideation_queue_size_history"]))
        
        # Get current cognitive load
        cognitive_load = 0.5  # Default value
        try:
            cognitive_load = await self.metacognitive_monitor.get_cognitive_load()
        except Exception as e:
            logger.error(f"Error getting cognitive load: {e}")
        
        # Detect bottlenecks and apply backpressure
        
        # If reflection queue is building up, slow down thought processing
        if avg_reflection_queue_size > 5 * self.max_parallel_reflections:
            pipeline_state["flow_control"]["thought_backpressure"] = True
        elif avg_reflection_queue_size < 2 * self.max_parallel_reflections:
            pipeline_state["flow_control"]["thought_backpressure"] = False
        
        # If ideation queue is building up, slow down reflection processing
        if avg_ideation_queue_size > 5 * self.max_parallel_ideations:
            pipeline_state["flow_control"]["reflection_backpressure"] = True
        elif avg_ideation_queue_size < 2 * self.max_parallel_ideations:
            pipeline_state["flow_control"]["reflection_backpressure"] = False
        
        # Adjust parallelism based on cognitive load and queue sizes
        if cognitive_load > 0.8:
            # High cognitive load, reduce parallelism
            self.max_parallel_thoughts = max(1, min(self.max_parallel_thoughts, 2))
            self.max_parallel_reflections = max(1, min(self.max_parallel_reflections, 1))
            self.max_parallel_ideations = max(1, min(self.max_parallel_ideations, 1))
        elif cognitive_load < 0.3 and avg_thought_queue_size > 3:
            # Low cognitive load with pending thoughts, increase parallelism
            self.max_parallel_thoughts = min(5, self.max_parallel_thoughts + 1)
            self.max_parallel_reflections = min(3, self.max_parallel_reflections + 1)
            self.max_parallel_ideations = min(3, self.max_parallel_ideations + 1)
        
        # Log pipeline state
        logger.debug(f"Pipeline state: cognitive_load={cognitive_load:.2f}, " +
                    f"thought_queue={avg_thought_queue_size:.1f}, " +
                    f"reflection_queue={avg_reflection_queue_size:.1f}, " +
                    f"ideation_queue={avg_ideation_queue_size:.1f}, " +
                    f"parallelism=({self.max_parallel_thoughts}, {self.max_parallel_reflections}, {self.max_parallel_ideations})")
    
    async def _prioritize_reflections(self) -> None:
        """
        Prioritize reflections based on cognitive context and thought characteristics.
        """
        if not self.reflection_priority_queue:
            return
        
        # Get current cognitive context
        context = self._create_cognitive_context()
        
        # Re-prioritize reflection queue
        new_queue = []
        
        while self.reflection_priority_queue:
            _, reflection_id, (thought, old_context) = heapq.heappop(self.reflection_priority_queue)
            
            # Calculate new priority based on:
            # 1. Original thought priority
            base_priority = thought.priority
            
            # 2. Relationship to current attention focus
            attention_bonus = 0.0
            if context.attention_focus and context.attention_focus.lower() in thought.content.lower():
                attention_bonus = 0.2
            
            # 3. Age of the thought (newer thoughts get higher priority)
            age_factor = 0.0
            if hasattr(thought, "created_at"):
                age = time.time() - thought.created_at
                age_factor = max(0.0, 0.3 * math.exp(-age / 3600))  # Exponential decay over hours
            
            # 4. Thought complexity (more complex thoughts get higher priority when cognitive load is low)
            complexity_bonus = 0.0
            cognitive_load = await self.metacognitive_monitor.get_cognitive_load()
            if cognitive_load < 0.4:
                # Estimate complexity (simplified)
                complexity = min(1.0, len(thought.content) / 500)
                complexity_bonus = 0.1 * complexity
            
            # Calculate final priority
            final_priority = base_priority + attention_bonus + age_factor + complexity_bonus
            
            # Add to new queue with updated priority
            heapq.heappush(new_queue, (-final_priority, reflection_id, (thought, context)))
        
        # Replace queue with re-prioritized queue
        self.reflection_priority_queue = new_queue
    
    async def _allocate_ideation_resources(self) -> None:
        """
        Allocate resources for ideation based on potential idea quality.
        """
        if not self.ideation_priority_queue:
            return
        
        # Get current resource allocation from metacognitive monitor
        try:
            resource_allocation = await self.metacognitive_monitor.optimize_cognitive_resources(self._create_cognitive_context())
            ideation_resources = resource_allocation.get("ideation", 0.3)
            
            # Adjust max parallel ideations based on available resources
            self.max_parallel_ideations = max(1, min(3, int(ideation_resources * 5)))
        except Exception as e:
            logger.error(f"Error optimizing cognitive resources: {e}")
    
    async def _cleanup_stalled_tasks(self) -> None:
        """
        Clean up stalled tasks that might be stuck.
        """
        current_time = time.time()
        
        # Check for stalled thought tasks (running for more than 30 seconds)
        for thought_id, task in list(self.active_thought_tasks.items()):
            if hasattr(task, "start_time") and current_time - task.start_time > 30:
                logger.warning(f"Cancelling stalled thought task {thought_id}")
                task.cancel()
                self.active_thought_tasks.pop(thought_id, None)
        
        # Check for stalled reflection tasks (running for more than 60 seconds)
        for reflection_id, task in list(self.active_reflection_tasks.items()):
            if hasattr(task, "start_time") and current_time - task.start_time > 60:
                logger.warning(f"Cancelling stalled reflection task {reflection_id}")
                task.cancel()
                self.active_reflection_tasks.pop(reflection_id, None)
        
        # Check for stalled ideation tasks (running for more than 90 seconds)
        for ideation_id, task in list(self.active_ideation_tasks.items()):
            if hasattr(task, "start_time") and current_time - task.start_time > 90:
                logger.warning(f"Cancelling stalled ideation task {ideation_id}")
                task.cancel()
                self.active_ideation_tasks.pop(ideation_id, None)
    
    async def _process_thoughts_in_parallel(self) -> None:
        """Process thoughts in parallel."""
        # Check if we can start more thought processing tasks
        while (len(self.active_thought_tasks) < self.max_parallel_thoughts and
               self.thought_priority_queue):
            
            # Get highest priority thought
            _, thought_id, thought = heapq.heappop(self.thought_priority_queue)
            
            # Start thought processing task
            task = asyncio.create_task(self._process_thought_task(thought))
            self.active_thought_tasks[thought_id] = task
            
            # Set callback to clean up when task completes
            task.add_done_callback(
                lambda t, tid=thought_id: self._on_thought_task_done(tid, t)
            )
    
    async def _process_reflections_in_parallel(self) -> None:
        """Process reflections in parallel."""
        # Check if we can start more reflection tasks
        while (len(self.active_reflection_tasks) < self.max_parallel_reflections and
               self.reflection_priority_queue):
            
            # Get highest priority reflection data
            _, reflection_id, (thought, context) = heapq.heappop(self.reflection_priority_queue)
            
            # Start reflection task
            task = asyncio.create_task(self._process_reflection_task(thought, context))
            self.active_reflection_tasks[reflection_id] = task
            
            # Set callback to clean up when task completes
            task.add_done_callback(
                lambda t, rid=reflection_id: self._on_reflection_task_done(rid, t)
            )
    
    async def _process_ideations_in_parallel(self) -> None:
        """Process ideations in parallel."""
        # Check if we can start more ideation tasks
        while (len(self.active_ideation_tasks) < self.max_parallel_ideations and
               self.ideation_priority_queue):
            
            # Get highest priority ideation data
            _, ideation_id, (thought, reflection, context) = heapq.heappop(self.ideation_priority_queue)
            
            # Start ideation task
            task = asyncio.create_task(self._process_ideation_task(thought, reflection, context))
            self.active_ideation_tasks[ideation_id] = task
            
            # Set callback to clean up when task completes
            task.add_done_callback(
                lambda t, iid=ideation_id: self._on_ideation_task_done(iid, t)
            )
    
    def _on_thought_task_done(self, thought_id: str, task: asyncio.Task) -> None:
        """
        Handle completion of a thought processing task.
        
        Args:
            thought_id: The ID of the processed thought
            task: The completed task
        """
        # Remove from active tasks
        self.active_thought_tasks.pop(thought_id, None)
        
        # Check for exceptions
        if not task.cancelled():
            try:
                task.result()
            except Exception as e:
                logger.error(f"Error in thought processing task: {e}")
    
    def _on_reflection_task_done(self, reflection_id: str, task: asyncio.Task) -> None:
        """
        Handle completion of a reflection task.
        
        Args:
            reflection_id: The ID of the reflection task
            task: The completed task
        """
        # Remove from active tasks
        self.active_reflection_tasks.pop(reflection_id, None)
        
        # Check for exceptions
        if not task.cancelled():
            try:
                task.result()
            except Exception as e:
                logger.error(f"Error in reflection task: {e}")
    
    def _on_ideation_task_done(self, ideation_id: str, task: asyncio.Task) -> None:
        """
        Handle completion of an ideation task.
        
        Args:
            ideation_id: The ID of the ideation task
            task: The completed task
        """
        # Remove from active tasks
        self.active_ideation_tasks.pop(ideation_id, None)
        
        # Check for exceptions
        if not task.cancelled():
            try:
                task.result()
            except Exception as e:
                logger.error(f"Error in ideation task: {e}")
    
    async def _resource_optimizer(self) -> None:
        """
        Resource optimizer task that monitors and optimizes resource allocation
        for cognitive processes.
        """
        logger.info("Starting resource optimizer task")
        
        try:
            while True:
                # Get current resource usage from resource manager
                if self.resource_manager:
                    try:
                        resource_usage = await self.resource_manager.get_resource_usage()
                        
                        # Adjust parallel processing based on resource usage
                        if resource_usage.get("cpu_usage", 0) > 80:
                            # High CPU usage, reduce parallelism
                            self.max_parallel_thoughts = max(1, self.max_parallel_thoughts - 1)
                            self.max_parallel_reflections = max(1, self.max_parallel_reflections - 1)
                            self.max_parallel_ideations = max(1, self.max_parallel_ideations - 1)
                        elif resource_usage.get("cpu_usage", 0) < 30:
                            # Low CPU usage, increase parallelism
                            self.max_parallel_thoughts = min(5, self.max_parallel_thoughts + 1)
                            self.max_parallel_reflections = min(3, self.max_parallel_reflections + 1)
                            self.max_parallel_ideations = min(3, self.max_parallel_ideations + 1)
                        
                        # Adjust memory allocation
                        memory_usage = resource_usage.get("memory_usage", 0)
                        if memory_usage > 80:
                            # High memory usage, trigger forgetting mechanism
                            await self.thought_stream._apply_forgetting_mechanism()
                    except Exception as e:
                        logger.error(f"Error getting resource usage: {e}")
                
                # Sleep for a while before next check
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Resource optimizer task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in resource optimizer: {e}")
    
    # Task processing methods
    async def _process_thought_task(self, thought: Thought) -> None:
        """
        Process a thought with enhanced knowledge integration and context-awareness.
        
        This enhanced implementation:
        1. Enriches thoughts with knowledge store information
        2. Performs contextual analysis for better reflection decisions
        3. Tracks thought processing metrics for optimization
        4. Implements adaptive priority adjustment
        
        Args:
            thought: The thought to process
        """
        start_time = time.time()
        task = asyncio.current_task()
        if task:
            setattr(task, "start_time", start_time)
        
        try:
            # 1. Create cognitive context with enhanced information
            context = self._create_cognitive_context()
            
            # 2. Enrich thought with knowledge store information
            await self._enrich_thought_with_knowledge(thought)
            
            # 3. Update metacognitive state
            await self.metacognitive_monitor.update_state(thought, None, context)
            
            # 4. Perform contextual analysis
            analysis_results = await self._analyze_thought_context(thought, context)
            
            # 5. Determine if reflection should be performed with enhanced criteria
            should_reflect = await self.metacognitive_monitor.should_reflect(thought, context)
            
            # 6. Apply adaptive priority adjustment based on analysis
            adjusted_priority = self._adjust_thought_priority(thought, analysis_results, context)
            
            if should_reflect:
                # Add to reflection priority queue with adjusted priority
                heapq.heappush(
                    self.reflection_priority_queue,
                    (-adjusted_priority, str(uuid.uuid4()), (thought, context))
                )
                
                # Log reflection decision with reason
                reflection_reason = analysis_results.get("reflection_reason", "Priority threshold exceeded")
                logger.debug(f"Thought {thought.id} queued for reflection: {reflection_reason}")
            else:
                logger.debug(f"Thought {thought.id} not queued for reflection: priority {thought.priority} below threshold")
            
            # 7. Store thought processing metrics for optimization
            processing_metrics = {
                "thought_id": thought.id,
                "thought_type": thought.type,
                "thought_priority": thought.priority,
                "adjusted_priority": adjusted_priority,
                "cognitive_load": context.cognitive_load,
                "processing_time": time.time() - start_time,
                "should_reflect": should_reflect,
                "timestamp": time.time()
            }
            
            # Store metrics in thought metadata for later analysis
            thought.metadata["processing_metrics"] = processing_metrics
            
            # 8. Trigger thought processed event with enhanced data
            await self.trigger_event(EVENT_THOUGHT_PROCESSED, {
                "thought": thought,
                "should_reflect": should_reflect,
                "context": context,
                "analysis_results": analysis_results,
                "processing_metrics": processing_metrics
            })
            
            # 9. Update pipeline metrics
            self.pipeline_metrics["thoughts_processed"] += 1
            processing_time = time.time() - start_time
            self.pipeline_metrics["total_processing_time"] += processing_time
            
            # 10. Record thought in knowledge store if significant
            if thought.priority > 0.7 or "important" in thought.metadata:
                await self._store_thought_in_knowledge(thought, processing_metrics)
                
        except Exception as e:
            logger.error(f"Error processing thought {thought.id}: {e}")
    
    async def _enrich_thought_with_knowledge(self, thought: Thought) -> None:
        """
        Enrich a thought with relevant information from the knowledge store.
        
        Args:
            thought: The thought to enrich
        """
        if not self.knowledge_store:
            return
            
        try:
            # Query knowledge store for relevant information
            query = {
                "content": thought.content,
                "type": thought.type,
                "max_results": 3,
                "min_confidence": 0.6
            }
            
            knowledge_items = await self.knowledge_store.query_knowledge(query)
            
            # Extract relevant information from knowledge items
            relevant_info = []
            if hasattr(knowledge_items, 'items'):
                for item in knowledge_items.items[:3]:
                    if hasattr(item, 'content') and item.content:
                        # Extract a summary or snippet of the content
                        content_summary = str(item.content)
                        if len(content_summary) > 100:
                            content_summary = content_summary[:97] + "..."
                            
                        relevant_info.append({
                            "type": getattr(item, 'type', 'unknown'),
                            "content": content_summary,
                            "confidence": getattr(item, 'confidence', 0.5),
                            "id": getattr(item, 'id', str(uuid.uuid4()))
                        })
            
            # Add relevant information to thought metadata
            if relevant_info:
                thought.metadata["knowledge_context"] = relevant_info
                
        except Exception as e:
            logger.error(f"Error enriching thought with knowledge: {e}")
    
    async def _analyze_thought_context(self, thought: Thought, context: CognitiveContext) -> Dict[str, Any]:
        """
        Analyze the thought in the current cognitive context.
        
        Args:
            thought: The thought to analyze
            context: The cognitive context
            
        Returns:
            Analysis results
        """
        results = {
            "novelty": 0.5,
            "relevance": 0.5,
            "complexity": 0.5,
            "reflection_reason": ""
        }
        
        # Analyze novelty by comparing with active thoughts
        if context.active_thoughts:
            novelty_scores = []
            for active_id in context.active_thoughts:
                if active_id == thought.id:
                    continue
                    
                # In a real implementation, we would retrieve the active thought
                # and calculate similarity. For now, use a random score.
                similarity = random.random()
                novelty_scores.append(1.0 - similarity)
                
            if novelty_scores:
                results["novelty"] = sum(novelty_scores) / len(novelty_scores)
        
        # Analyze relevance to current attention focus
        if context.attention_focus:
            if context.attention_focus.lower() in thought.content.lower():
                results["relevance"] = 0.8 + (0.2 * random.random())
                results["reflection_reason"] = "Highly relevant to current focus"
            else:
                results["relevance"] = 0.3 + (0.4 * random.random())
        
        # Analyze complexity based on content
        content_length = len(thought.content)
        sentence_count = len(re.split(r'[.!?]', thought.content))
        
        if sentence_count > 0:
            avg_sentence_length = content_length / sentence_count
            results["complexity"] = min(1.0, avg_sentence_length / 20)
            
            if results["complexity"] > 0.7:
                if not results["reflection_reason"]:
                    results["reflection_reason"] = "High complexity thought"
        
        return results
    
    def _adjust_thought_priority(self, thought: Thought, analysis_results: Dict[str, Any], context: CognitiveContext) -> float:
        """
        Adjust thought priority based on analysis results and context.
        
        Args:
            thought: The thought to adjust priority for
            analysis_results: The analysis results
            context: The cognitive context
            
        Returns:
            Adjusted priority
        """
        base_priority = thought.priority
        
        # Adjust based on novelty
        novelty_adjustment = 0.2 * (analysis_results.get("novelty", 0.5) - 0.5)
        
        # Adjust based on relevance
        relevance_adjustment = 0.3 * (analysis_results.get("relevance", 0.5) - 0.5)
        
        # Adjust based on complexity and cognitive load
        complexity = analysis_results.get("complexity", 0.5)
        if context.cognitive_load > 0.7:
            # When load is high, prioritize simpler thoughts
            complexity_adjustment = 0.2 * (0.5 - complexity)
        else:
            # When load is low, prioritize complex thoughts
            complexity_adjustment = 0.2 * (complexity - 0.5)
        
        # Calculate adjusted priority
        adjusted_priority = base_priority + novelty_adjustment + relevance_adjustment + complexity_adjustment
        
        # Ensure priority is in valid range
        adjusted_priority = max(0.1, min(1.0, adjusted_priority))
        
        return adjusted_priority
    
    async def _store_thought_in_knowledge(self, thought: Thought, metrics: Dict[str, Any]) -> None:
        """
        Store significant thoughts in the knowledge store.
        
        Args:
            thought: The thought to store
            metrics: Processing metrics
        """
        if not self.knowledge_store:
            return
            
        try:
            # Prepare knowledge item
            knowledge_item = {
                "type": "thought",
                "content": {
                    "text": thought.content,
                    "thought_type": thought.type,
                    "thought_id": thought.id
                },
                "confidence": thought.priority,
                "metadata": {
                    **thought.metadata,
                    "processing_metrics": metrics
                }
            }
            
            # Store in knowledge store
            await self.knowledge_store.store_knowledge(knowledge_item)
            logger.debug(f"Stored thought {thought.id} in knowledge store")
        except Exception as e:
            logger.error(f"Error storing thought in knowledge store: {e}")
    
    async def _process_reflection_task(self, thought: Thought, context: CognitiveContext) -> None:
        """
        Process a reflection with enhanced knowledge integration and multi-level reflection.
        
        This enhanced implementation:
        1. Provides context-aware reflection by integrating knowledge store information
        2. Implements multi-level reflection for deeper insights
        3. Detects contradictions and patterns across reflections
        4. Tracks reflection metrics for optimization
        
        Args:
            thought: The thought to reflect on
            context: The cognitive context
        """
        start_time = time.time()
        task = asyncio.current_task()
        if task:
            setattr(task, "start_time", start_time)
        
        try:
            # 1. Prepare reflection context with knowledge integration
            reflection_context = await self._prepare_reflection_context(thought, context)
            
            # 2. Perform primary reflection
            reflection = await self.reflection_engine.reflect(thought, reflection_context)
            
            # 3. Analyze reflection quality
            reflection_analysis = self._analyze_reflection_quality(reflection)
            reflection.metadata["quality_analysis"] = reflection_analysis
            
            # 4. Determine if meta-reflection is needed
            should_meta_reflect = False
            previous_reflections = []
            
            # Get previous reflections for this thought
            if hasattr(self.reflection_engine, "get_reflections_for_thought"):
                previous_reflections = await self.reflection_engine.get_reflections_for_thought(thought.id)
                
                # Check if we should perform meta-reflection
                if len(previous_reflections) >= 2:
                    should_meta_reflect = await self.metacognitive_monitor.should_meta_reflect(
                        previous_reflections + [reflection],
                        context
                    )
            
            # 5. Perform meta-reflection if needed
            if should_meta_reflect:
                meta_reflection = await self.reflection_engine.meta_reflect(
                    previous_reflections + [reflection],
                    context
                )
                
                # Store relationship between reflections and meta-reflection
                reflection.metadata["has_meta_reflection"] = True
                reflection.metadata["meta_reflection_id"] = meta_reflection.id
                
                logger.debug(f"Created meta-reflection {meta_reflection.id} for thought {thought.id}")
            
            # 6. Update metacognitive state with reflection
            await self.metacognitive_monitor.update_state(thought, reflection, context)
            
            # 7. Store significant reflections in knowledge store
            if reflection_analysis["overall_quality"] > 0.7:
                await self._store_reflection_in_knowledge(thought, reflection, reflection_analysis)
            
            # 8. Trigger reflection created event with enhanced data
            event_data = {
                "thought": thought,
                "reflection": reflection,
                "context": context,
                "quality_analysis": reflection_analysis,
                "processing_time": time.time() - start_time,
                "has_meta_reflection": should_meta_reflect
            }
            
            await self.trigger_event(EVENT_REFLECTION_CREATED, event_data)
            
            # 9. Update pipeline metrics
            self.pipeline_metrics["reflections_created"] += 1
            
            # 10. Log reflection insights
            if reflection.insights:
                insight_count = len(reflection.insights)
                logger.debug(f"Reflection {reflection.id} generated {insight_count} insights for thought {thought.id}")
                
                # Log a sample of insights
                if insight_count > 0:
                    sample_insight = reflection.insights[0]
                    logger.debug(f"Sample insight: {sample_insight[:100]}{'...' if len(sample_insight) > 100 else ''}")
            
        except Exception as e:
            logger.error(f"Error processing reflection for thought {thought.id}: {e}")
    
    async def _prepare_reflection_context(self, thought: Thought, context: CognitiveContext) -> Dict[str, Any]:
        """
        Prepare an enhanced context for reflection with knowledge integration.
        
        Args:
            thought: The thought to reflect on
            context: The base cognitive context
            
        Returns:
            Enhanced reflection context
        """
        # Start with base context
        reflection_context = {
            "cognitive_load": context.cognitive_load,
            "attention_focus": context.attention_focus,
            "active_thoughts": context.active_thoughts
        }
        
        # Add knowledge context if available
        if self.knowledge_store:
            try:
                # Query for related knowledge
                query = {
                    "content": thought.content,
                    "type": thought.type,
                    "max_results": 5,
                    "min_confidence": 0.5
                }
                
                knowledge_items = await self.knowledge_store.query_knowledge(query)
                
                # Extract relevant knowledge
                relevant_knowledge = []
                if hasattr(knowledge_items, 'items'):
                    for item in knowledge_items.items[:5]:
                        if hasattr(item, 'content'):
                            relevant_knowledge.append({
                                "type": getattr(item, 'type', 'unknown'),
                                "content": str(item.content)[:200],  # Limit length
                                "confidence": getattr(item, 'confidence', 0.5)
                            })
                
                reflection_context["knowledge_context"] = relevant_knowledge
            except Exception as e:
                logger.error(f"Error preparing knowledge context for reflection: {e}")
        
        # Add thought history context
        reflection_context["thought_history"] = await self._get_thought_history_context(thought)
        
        return reflection_context
    
    async def _get_thought_history_context(self, thought: Thought) -> List[Dict[str, Any]]:
        """
        Get historical context for a thought.
        
        Args:
            thought: The current thought
            
        Returns:
            List of historical thought summaries
        """
        history = []
        
        # In a real implementation, we would query the thought stream
        # for related thoughts. For now, return an empty list.
        
        return history
    
    def _analyze_reflection_quality(self, reflection: Reflection) -> Dict[str, float]:
        """
        Analyze the quality of a reflection.
        
        Args:
            reflection: The reflection to analyze
            
        Returns:
            Quality metrics
        """
        analysis = {
            "insight_quality": 0.5,
            "insight_diversity": 0.5,
            "contradiction_detection": 0.5,
            "overall_quality": 0.5
        }
        
        # Analyze insight quality
        if reflection.insights:
            # Count insights
            insight_count = len(reflection.insights)
            
            # Normalize insight count (0-10 scale)
            normalized_count = min(1.0, insight_count / 10)
            
            # Calculate average insight length
            avg_length = sum(len(insight) for insight in reflection.insights) / insight_count
            normalized_length = min(1.0, avg_length / 100)  # Normalize to [0, 1]
            
            # Calculate insight diversity
            unique_terms = set()
            for insight in reflection.insights:
                terms = re.findall(r'\b\w{5,}\b', insight.lower())
                unique_terms.update(terms)
            
            total_terms = sum(len(re.findall(r'\b\w{5,}\b', insight.lower())) for insight in reflection.insights)
            diversity = len(unique_terms) / max(1, total_terms)
            
            # Calculate insight quality
            analysis["insight_quality"] = 0.4 * normalized_count + 0.3 * normalized_length + 0.3 * diversity
            analysis["insight_diversity"] = diversity
        
        # Analyze contradiction detection
        contradictions = reflection.metadata.get("contradictions", [])
        if contradictions:
            analysis["contradiction_detection"] = min(1.0, len(contradictions) / 5)  # Up to 5 contradictions
        
        # Calculate overall quality
        analysis["overall_quality"] = (
            0.5 * analysis["insight_quality"] +
            0.3 * analysis["insight_diversity"] +
            0.2 * analysis["contradiction_detection"]
        )
        
        return analysis
    
    async def _store_reflection_in_knowledge(self, thought: Thought, reflection: Reflection, analysis: Dict[str, float]) -> None:
        """
        Store significant reflections in the knowledge store.
        
        Args:
            thought: The thought that was reflected on
            reflection: The reflection to store
            analysis: Quality analysis of the reflection
        """
        if not self.knowledge_store:
            return
            
        try:
            # Prepare knowledge item
            knowledge_item = {
                "type": "reflection",
                "content": {
                    "thought_id": thought.id,
                    "thought_content": thought.content,
                    "insights": reflection.insights,
                    "should_ideate": reflection.should_ideate
                },
                "confidence": analysis["overall_quality"],
                "metadata": {
                    "reflection_id": reflection.id,
                    "quality_analysis": analysis,
                    "timestamp": time.time()
                }
            }
            
            # Store in knowledge store
            await self.knowledge_store.store_knowledge(knowledge_item)
            logger.debug(f"Stored reflection {reflection.id} in knowledge store")
        except Exception as e:
            logger.error(f"Error storing reflection in knowledge store: {e}")
    
    async def _process_ideation_task(self, thought: Thought, reflection: Reflection, context: CognitiveContext) -> None:
        """
        Process ideation with enhanced creativity, evaluation, and feedback mechanisms.
        
        This enhanced implementation:
        1. Integrates knowledge store information for more informed ideation
        2. Implements creative combination strategies for idea generation
        3. Provides sophisticated evaluation of idea novelty and utility
        4. Includes feedback mechanisms for idea refinement
        5. Stores high-value ideas in the knowledge store
        
        Args:
            thought: The thought
            reflection: The reflection
            context: The cognitive context
        """
        start_time = time.time()
        task = asyncio.current_task()
        if task:
            setattr(task, "start_time", start_time)
        
        try:
            # 1. Prepare ideation context with knowledge integration
            ideation_context = await self._prepare_ideation_context(thought, reflection, context)
            
            # 2. Generate ideas with enhanced strategies
            ideas = await self.ideation_engine.generate_ideas(thought, reflection, ideation_context)
            
            # 3. Group ideas by generation method for analysis
            idea_groups = defaultdict(list)
            for idea in ideas:
                generation_method = idea.metadata.get("generation_method", "direct")
                idea_groups[generation_method].append(idea)
            
            # 4. Log idea generation statistics
            logger.debug(f"Generated {len(ideas)} ideas for thought {thought.id}: " +
                        f"{', '.join(f'{method}: {len(group)}' for method, group in idea_groups.items())}")
            
            # 5. Evaluate each idea with comprehensive metrics
            evaluated_ideas = []
            for idea in ideas:
                # Perform comprehensive evaluation
                evaluation = await self.ideation_engine.evaluate_idea(idea, ideation_context)
                
                # Store evaluation in idea metadata
                idea.metadata["evaluation"] = evaluation
                idea.metadata["processing_time"] = time.time() - start_time
                
                evaluated_ideas.append((idea, evaluation))
                
                # 6. Trigger idea generated event with enhanced data
                await self.trigger_event(EVENT_IDEA_GENERATED, {
                    "idea": idea,
                    "thought": thought,
                    "reflection": reflection,
                    "context": context,
                    "evaluation": evaluation
                })
            
            # 7. Identify high-value ideas for storage and refinement
            high_value_ideas = [
                idea for idea, eval in evaluated_ideas
                if eval["overall"] > 0.7 or (eval["novelty"] > 0.8 and eval["utility"] > 0.5)
            ]
            
            # 8. Store high-value ideas in knowledge store
            if high_value_ideas:
                await self._store_best_ideas(thought, reflection, high_value_ideas, context)
                
                # 9. Refine best idea if appropriate
                if len(high_value_ideas) > 0 and context.cognitive_load < 0.7:
                    best_idea = max(high_value_ideas, key=lambda i: i.metadata["evaluation"]["overall"])
                    
                    # Prepare feedback for refinement
                    feedback = self._generate_idea_feedback(best_idea)
                    
                    # Refine the idea
                    refined_idea = await self.ideation_engine.refine_idea(best_idea, feedback, context)
                    
                    # Evaluate refined idea
                    refined_evaluation = await self.ideation_engine.evaluate_idea(refined_idea, context)
                    refined_idea.metadata["evaluation"] = refined_evaluation
                    
                    # Log refinement results
                    improvement = refined_evaluation["overall"] - best_idea.metadata["evaluation"]["overall"]
                    logger.debug(f"Refined idea {best_idea.id} -> {refined_idea.id}, improvement: {improvement:.2f}")
                    
                    # Trigger event for refined idea
                    await self.trigger_event(EVENT_IDEA_GENERATED, {
                        "idea": refined_idea,
                        "thought": thought,
                        "reflection": reflection,
                        "context": context,
                        "evaluation": refined_evaluation,
                        "is_refined": True,
                        "original_idea_id": best_idea.id
                    })
                    
                    # Add refined idea to count
                    evaluated_ideas.append((refined_idea, refined_evaluation))
            
            # 10. Update pipeline metrics
            self.pipeline_metrics["ideas_generated"] += len(evaluated_ideas)
            
            # 11. Log ideation performance metrics
            if evaluated_ideas:
                avg_novelty = sum(eval["novelty"] for _, eval in evaluated_ideas) / len(evaluated_ideas)
                avg_utility = sum(eval["utility"] for _, eval in evaluated_ideas) / len(evaluated_ideas)
                max_overall = max(eval["overall"] for _, eval in evaluated_ideas)
                
                logger.debug(f"Ideation metrics for thought {thought.id}: " +
                           f"avg_novelty={avg_novelty:.2f}, avg_utility={avg_utility:.2f}, max_overall={max_overall:.2f}")
                
        except Exception as e:
            logger.error(f"Error processing ideation for thought {thought.id}: {e}")
    
    async def _prepare_ideation_context(self, thought: Thought, reflection: Reflection, context: CognitiveContext) -> Dict[str, Any]:
        """
        Prepare an enhanced context for ideation with knowledge integration.
        
        Args:
            thought: The thought
            reflection: The reflection
            context: The base cognitive context
            
        Returns:
            Enhanced ideation context
        """
        # Start with base context
        ideation_context = {
            "cognitive_load": context.cognitive_load,
            "attention_focus": context.attention_focus,
            "active_thoughts": context.active_thoughts
        }
        
        # Add reflection insights
        ideation_context["insights"] = reflection.insights if hasattr(reflection, "insights") else []
        
        # Add knowledge context if available
        if self.knowledge_store:
            try:
                # Query for related knowledge
                query = {
                    "content": thought.content,
                    "type": "concept,idea,hypothesis",  # Focus on creative knowledge types
                    "max_results": 5,
                    "min_confidence": 0.5
                }
                
                knowledge_items = await self.knowledge_store.query_knowledge(query)
                
                # Extract relevant knowledge
                relevant_knowledge = []
                if hasattr(knowledge_items, 'items'):
                    for item in knowledge_items.items[:5]:
                        if hasattr(item, 'content'):
                            relevant_knowledge.append({
                                "type": getattr(item, 'type', 'unknown'),
                                "content": str(item.content)[:200],  # Limit length
                                "confidence": getattr(item, 'confidence', 0.5)
                            })
                
                ideation_context["knowledge_context"] = relevant_knowledge
            except Exception as e:
                logger.error(f"Error preparing knowledge context for ideation: {e}")
        
        # Add creative domains for analogy generation
        ideation_context["creative_domains"] = [
            "nature", "technology", "art", "science", "business",
            "psychology", "history", "mathematics", "philosophy"
        ]
        
        return ideation_context
    
    def _generate_idea_feedback(self, idea: Idea) -> Dict[str, Any]:
        """
        Generate feedback for idea refinement.
        
        Args:
            idea: The idea to generate feedback for
            
        Returns:
            Feedback for refinement
        """
        evaluation = idea.metadata.get("evaluation", {})
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        # Analyze novelty
        novelty = evaluation.get("novelty", 0.5)
        if novelty > 0.8:
            strengths.append("highly novel concept")
        elif novelty < 0.3:
            weaknesses.append("lacks originality")
        
        # Analyze utility
        utility = evaluation.get("utility", 0.5)
        if utility > 0.8:
            strengths.append("highly practical application")
        elif utility < 0.3:
            weaknesses.append("limited practical value")
        
        # Analyze feasibility
        feasibility = evaluation.get("feasibility", 0.5)
        if feasibility > 0.8:
            strengths.append("easily implementable")
        elif feasibility < 0.3:
            weaknesses.append("implementation challenges")
        
        # Analyze complexity
        complexity = evaluation.get("complexity", 0.5)
        if complexity > 0.8:
            weaknesses.append("overly complex")
        
        # Generate feedback focus
        if weaknesses:
            focus = weaknesses[0]
        elif len(strengths) > 0:
            focus = f"build on {strengths[0]}"
        else:
            focus = "general improvement"
        
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "focus": focus,
            "evaluation": evaluation
        }
    
    async def _store_best_ideas(self, thought: Thought, reflection: Reflection, ideas: List[Idea], context: CognitiveContext) -> None:
        """
        Store high-value ideas in the knowledge store for future reference.
        
        Args:
            thought: The original thought
            reflection: The reflection that led to the ideas
            ideas: The high-value ideas to store
            context: The cognitive context
        """
        if not self.knowledge_store:
            return
            
        try:
            for idea in ideas:
                # Extract evaluation metrics
                evaluation = idea.metadata.get("evaluation", {})
                overall_score = evaluation.get("overall", 0.5)
                novelty_score = evaluation.get("novelty", 0.5)
                utility_score = evaluation.get("utility", 0.5)
                
                # Determine idea type based on scores
                if novelty_score > 0.8 and utility_score > 0.7:
                    idea_type = "breakthrough_idea"
                elif novelty_score > 0.7:
                    idea_type = "novel_concept"
                elif utility_score > 0.7:
                    idea_type = "practical_solution"
                else:
                    idea_type = "general_idea"
                
                # Prepare knowledge item
                knowledge_item = {
                    "type": idea_type,
                    "content": {
                        "text": idea.content,
                        "thought_id": thought.id,
                        "reflection_id": reflection.id,
                        "idea_id": idea.id
                    },
                    "confidence": overall_score,
                    "metadata": {
                        "novelty_score": novelty_score,
                        "utility_score": utility_score,
                        "evaluation": evaluation,
                        "generation_method": idea.metadata.get("generation_method", "direct"),
                        "timestamp": time.time(),
                        "context": {
                            "cognitive_load": context.cognitive_load,
                            "attention_focus": context.attention_focus
                        }
                    }
                }
                
                # Store in knowledge store
                await self.knowledge_store.store_knowledge(knowledge_item)
                logger.debug(f"Stored {idea_type} {idea.id} in knowledge store with score {overall_score:.2f}")
        except Exception as e:
            logger.error(f"Error storing ideas in knowledge store: {e}")
    
    async def process_thought(self, thought_data: Dict[str, Any], resources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a thought using the enhanced pipeline.
        
        Args:
            thought_data: The thought data
            resources: The resources allocated for processing
            
        Returns:
            The result of processing the thought
        """
        if not self.is_running:
            raise RuntimeError("CognitiveEngine is not running")
        
        logger.debug(f"Processing thought: {thought_data}")
        
        try:
            # Create thought object
            thought = self._create_thought_from_data(thought_data)
            
            # Allocate resources if provided
            if resources and self.resource_manager:
                await self.resource_manager.allocate_resources(thought.id, resources)
            
            # Add thought to stream
            success = await self.thought_stream.add_thought(thought)
            if not success:
                return {
                    "success": False,
                    "error": "Failed to add thought to stream"
                }
            
            # Create cognitive context
            context = self._create_cognitive_context()
            
            # Determine if reflection should be performed
            should_reflect = await self.metacognitive_monitor.should_reflect(thought, context)
            
            # Trigger thought added event
            await self.trigger_event(EVENT_THOUGHT_ADDED, {
                "thought": thought,
                "context": context
            })
            
            # Add to priority queue
            priority = thought.priority
            heapq.heappush(self.thought_priority_queue, (-priority, thought.id, thought))
            
            result = {
                "success": True,
                "thought_id": thought.id,
                "thought_type": thought.type,
                "should_reflect": should_reflect,
                "cognitive_load": await self.metacognitive_monitor.get_cognitive_load(),
                "pipeline_status": {
                    "active_thoughts": len(self.active_thought_tasks),
                    "active_reflections": len(self.active_reflection_tasks),
                    "active_ideations": len(self.active_ideation_tasks),
                    "thoughts_processed": self.pipeline_metrics["thoughts_processed"],
                    "reflections_created": self.pipeline_metrics["reflections_created"],
                    "ideas_generated": self.pipeline_metrics["ideas_generated"]
                },
                "timestamp": time.time()
            }
            
            # If reflection should be performed immediately, do it
            if should_reflect and self.config.get("reflect_immediately", True):
                reflection = await self.reflection_engine.reflect(thought, context)
                
                # Update metacognitive state with reflection
                await self.metacognitive_monitor.update_state(thought, reflection, context)
                
                # Trigger reflection created event
                await self.trigger_event(EVENT_REFLECTION_CREATED, {
                    "thought": thought,
                    "reflection": reflection,
                    "context": context
                })
                
                # Add reflection result
                result["reflection_id"] = reflection.id
                result["insights"] = reflection.insights
                result["should_ideate"] = reflection.should_ideate
                
                # If ideation should be performed, do it
                if reflection.should_ideate:
                    ideas = await self.ideation_engine.generate_ideas(thought, reflection, context)
                    
                    # Evaluate each idea
                    for idea in ideas:
                        await self.ideation_engine.evaluate_idea(idea, context)
                        
                        # Trigger idea generated event
                        await self.trigger_event(EVENT_IDEA_GENERATED, {
                            "idea": idea,
                            "thought": thought,
                            "reflection": reflection,
                            "context": context
                        })
                    
                    # Add ideation result
                    result["ideas"] = [
                        {
                            "id": idea.id,
                            "content": idea.content,
                            "novelty_score": idea.novelty_score,
                            "utility_score": idea.utility_score
                        }
                        for idea in ideas
                    ]
            
            return result
        except Exception as e:
            logger.error(f"Error processing thought: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_response(self, interaction: Dict[str, Any], initial_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a cognitive response to an interaction using the enhanced pipeline.
        
        Args:
            interaction: The interaction
            initial_response: The initial response
            
        Returns:
            The cognitive response
        """
        if not self.is_running:
            raise RuntimeError("CognitiveEngine is not running")
        
        logger.debug(f"Generating cognitive response for interaction")
        
        try:
            # Create a thought based on the interaction
            thought_data = {
                "content": f"Interaction: {interaction.get('content', '')}",
                "type": "interaction_response",
                "priority": 0.8,
                "metadata": {
                    "interaction_id": interaction.get("id", ""),
                    "interaction_type": interaction.get("type", ""),
                    "initial_response": initial_response
                }
            }
            
            # Allocate resources for thought processing
            resources = {
                "priority": "high",
                "timeout": 30.0,
                "max_reflections": 3,
                "max_ideations": 5
            }
            
            # Process the thought
            thought_result = await self.process_thought(thought_data, resources)
            
            # Generate enhanced cognitive response
            cognitive_response = {
                "thought_id": thought_result.get("thought_id"),
                "insights": [],
                "recommendations": [],
                "reasoning": [],
                "pipeline_status": thought_result.get("pipeline_status", {})
            }
            
            # Add insights from reflection if available
            if "insights" in thought_result:
                cognitive_response["insights"] = thought_result["insights"]
            
            # Add recommendations based on ideas if available
            if "ideas" in thought_result:
                for idea in thought_result["ideas"]:
                    if idea.get("utility_score", 0) > 0.7:
                        cognitive_response["recommendations"].append({
                            "content": idea["content"],
                            "confidence": idea["utility_score"],
                            "novelty": idea["novelty_score"]
                        })
            
            # If no insights or recommendations yet, try to get from knowledge store
            if not cognitive_response["insights"] and not cognitive_response["recommendations"]:
                # Query knowledge store for relevant information with context
                query = {
                    "content": {
                        "text": interaction.get("content", ""),
                        "type": interaction.get("type", "")
                    },
                    "context": {
                        "interaction_id": interaction.get("id", ""),
                        "interaction_type": interaction.get("type", "")
                    },
                    "max_results": 5,
                    "min_confidence": 0.6
                }
                
                if self.knowledge_store:
                    query_result = await self.knowledge_store.query_knowledge(query)
                    
                    # Extract insights from query results
                    if hasattr(query_result, "items"):
                        for item in query_result.items:
                            if hasattr(item, "content") and item.content:
                                # Add insight with confidence
                                confidence = getattr(item, "confidence", 0.5)
                                content_str = str(item.content)
                                
                                # Truncate long content
                                if len(content_str) > 100:
                                    content_str = content_str[:100] + "..."
                                
                                cognitive_response["insights"].append({
                                    "content": f"Related knowledge: {content_str}",
                                    "confidence": confidence,
                                    "source": getattr(item, "source", "knowledge_store")
                                })
            
            # Add reasoning based on metacognitive state
            cognitive_load = thought_result.get("cognitive_load", 0.0)
            cognitive_response["reasoning"].append({
                "step": "cognitive_load_assessment",
                "content": f"Current cognitive load: {cognitive_load:.2f}",
                "timestamp": time.time()
            })
            
            if cognitive_load > 0.8:
                cognitive_response["reasoning"].append({
                    "step": "resource_allocation",
                    "content": "High cognitive load detected, prioritizing essential processing",
                    "timestamp": time.time()
                })
            
            return cognitive_response
        except Exception as e:
            logger.error(f"Error generating cognitive response: {e}")
            return {
                "error": str(e),
                "pipeline_status": {
                    "error": True,
                    "error_type": type(e).__name__
                }
            }
    
    async def _thought_processor(self) -> None:
        """Background task for processing thoughts."""
        logger.info("Starting thought processor task")
        
        try:
            while True:
                # Get next thought from queue
                thought = await self.thought_queue.get()
                
                try:
                    # Create cognitive context
                    context = self._create_cognitive_context()
                    
                    # Update metacognitive state
                    await self.metacognitive_monitor.update_state(thought, None, context)
                    
                    # Determine if reflection should be performed
                    should_reflect = await self.metacognitive_monitor.should_reflect(thought, context)
                    
                    if should_reflect:
                        # Add to reflection queue
                        await self.reflection_queue.put((thought, context))
                except Exception as e:
                    logger.error(f"Error in thought processor: {e}")
                finally:
                    # Mark task as done
                    self.thought_queue.task_done()
        except asyncio.CancelledError:
            logger.info("Thought processor task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in thought processor: {e}")
    
    async def _reflection_processor(self) -> None:
        """Background task for processing reflections."""
        logger.info("Starting reflection processor task")
        
        try:
            while True:
                # Get next thought and context from queue
                thought, context = await self.reflection_queue.get()
                
                try:
                    # Perform reflection
                    reflection = await self.reflection_engine.reflect(thought, context)
                    
                    # Update metacognitive state with reflection
                    await self.metacognitive_monitor.update_state(thought, reflection, context)
                    
                    # If ideation should be performed, do it
                    if reflection.should_ideate:
                        ideas = await self.ideation_engine.generate_ideas(thought, reflection, context)
                        
                        # Evaluate ideas
                        for idea in ideas:
                            await self.ideation_engine.evaluate_idea(idea, context)
                        
                        # Store best ideas in knowledge store if appropriate
                        await self._store_best_ideas(thought, reflection, ideas, context)
                except Exception as e:
                    logger.error(f"Error in reflection processor: {e}")
                finally:
                    # Mark task as done
                    self.reflection_queue.task_done()
        except asyncio.CancelledError:
            logger.info("Reflection processor task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in reflection processor: {e}")
    
    def _create_thought_from_data(self, thought_data: Dict[str, Any]) -> Thought:
        """
        Create a Thought object from thought data.
        
        Args:
            thought_data: The thought data
            
        Returns:
            The created Thought object
        """
        return Thought(
            id=thought_data.get("id", ""),
            content=thought_data.get("content", ""),
            type=thought_data.get("type", "general"),
            priority=thought_data.get("priority", 0.5),
            metadata=thought_data.get("metadata", {})
        )
    
    def _create_cognitive_context(self) -> CognitiveContext:
        """
        Create a CognitiveContext object from current state.
        
        Returns:
            The created CognitiveContext object
        """
        # Get active thoughts from state
        active_thoughts = []
        if self.state and hasattr(self.state, "cognitive_context"):
            active_thoughts = getattr(self.state.cognitive_context, "active_thoughts", [])
        
        # Get attention focus from state
        attention_focus = ""
        if self.state and hasattr(self.state, "attention_focus"):
            attention_focus = getattr(self.state.attention_focus, "primary_focus", "")
        
        # Get cognitive load
        cognitive_load = 0.0
        if self.state and hasattr(self.state, "cognitive_context"):
            cognitive_load = getattr(self.state.cognitive_context, "cognitive_load", 0.0)
        
        return CognitiveContext(
            active_thoughts=active_thoughts,
            attention_focus=attention_focus,
            cognitive_load=cognitive_load
        )
    
    async def _store_best_ideas(self, thought: Thought, reflection: Reflection, ideas: List[Idea], context: CognitiveContext) -> None:
        """
        Store the best ideas in the knowledge store.
        
        Args:
            thought: The thought
            reflection: The reflection
            ideas: The generated ideas
            context: The cognitive context
        """
        if not self.knowledge_store:
            return
        
        # Filter for high-quality ideas
        good_ideas = [idea for idea in ideas if idea.utility_score > 0.7 and idea.novelty_score > 0.5]
        
        for idea in good_ideas:
            # Create knowledge item from idea
            knowledge_item = {
                "type": "hypothesis" if idea.novelty_score > 0.8 else "concept",
                "content": {
                    "text": idea.content,
                    "source": "ideation",
                    "thought_id": thought.id,
                    "reflection_id": reflection.id,
                    "idea_id": idea.id
                },
                "confidence": idea.utility_score,
                "metadata": {
                    "novelty_score": idea.novelty_score,
                    "utility_score": idea.utility_score,
                    "cognitive_context": {
                        "cognitive_load": context.cognitive_load,
                        "attention_focus": context.attention_focus
                    }
                }
            }
            
            # Store in knowledge store
            try:
                await self.knowledge_store.store_knowledge(knowledge_item)
                logger.debug(f"Stored idea {idea.id} in knowledge store")
            except Exception as e:
                logger.error(f"Error storing idea in knowledge store: {e}")