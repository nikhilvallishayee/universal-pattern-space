#!/usr/bin/env python3
"""
Agentic Daemon System for GodelOS

Implements autonomous background processing and system evolution through
continuous learning, knowledge gap analysis, and self-directed improvement.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class DaemonType(Enum):
    """Types of agentic daemons."""
    KNOWLEDGE_GAP_DETECTOR = "knowledge_gap_detector"
    AUTONOMOUS_RESEARCHER = "autonomous_researcher"
    SYSTEM_OPTIMIZER = "system_optimizer"
    PATTERN_RECOGNIZER = "pattern_recognizer"
    CONTINUOUS_LEARNER = "continuous_learner"
    METACOGNITIVE_MONITOR = "metacognitive_monitor"
    GROUNDING_COHERENCE = "grounding_coherence"


class ProcessStatus(Enum):
    """Status of daemon processes."""
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class DaemonTask:
    """Represents a task for an agentic daemon."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    description: str = ""
    priority: int = 5  # 1-10, 10 being highest
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class DaemonMetrics:
    """Performance metrics for a daemon."""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_runtime: float = 0.0
    average_task_time: float = 0.0
    last_activity: Optional[datetime] = None
    discoveries_made: int = 0
    knowledge_items_created: int = 0


class AgenticDaemon:
    """Base class for autonomous daemon processes."""
    
    def __init__(self, 
                 daemon_type: DaemonType,
                 name: str,
                 cognitive_manager=None,
                 knowledge_pipeline=None,
                 websocket_manager=None):
        self.daemon_type = daemon_type
        self.name = name
        self.cognitive_manager = cognitive_manager
        self.knowledge_pipeline = knowledge_pipeline
        self.websocket_manager = websocket_manager
        
        # Process state
        self.status = ProcessStatus.INACTIVE
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.current_task: Optional[DaemonTask] = None
        self.metrics = DaemonMetrics()
        
        # Configuration
        self.max_concurrent_tasks = 3
        self.task_timeout = 300  # 5 minutes
        self.sleep_interval = 30  # 30 seconds between cycles
        self.enabled = True
        
        # Runtime state
        self.running_tasks: Set[str] = set()
        self.completed_tasks: Dict[str, DaemonTask] = {}
        self.error_count = 0
        self.last_error: Optional[str] = None
        
        logger.info(f"AgenticDaemon '{self.name}' ({self.daemon_type.value}) initialized")
    
    async def start(self) -> bool:
        """Start the daemon process."""
        try:
            if self.status != ProcessStatus.INACTIVE:
                logger.warning(f"Daemon {self.name} is already running")
                return False
            
            logger.info(f"🚀 Starting daemon: {self.name}")
            self.status = ProcessStatus.STARTING
            
            # Initialize daemon-specific components
            await self._initialize()
            
            self.status = ProcessStatus.ACTIVE
            
            # Start the main daemon loop
            asyncio.create_task(self._daemon_loop())
            
            logger.info(f"✅ Daemon {self.name} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start daemon {self.name}: {e}")
            self.status = ProcessStatus.ERROR
            self.last_error = str(e)
            return False
    
    async def stop(self) -> bool:
        """Stop the daemon process."""
        try:
            logger.info(f"🛑 Stopping daemon: {self.name}")
            self.status = ProcessStatus.STOPPING
            
            # Cancel running tasks
            for task_id in self.running_tasks.copy():
                await self._cancel_task(task_id)
            
            # Cleanup daemon-specific resources
            await self._cleanup()
            
            self.status = ProcessStatus.INACTIVE
            logger.info(f"✅ Daemon {self.name} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping daemon {self.name}: {e}")
            self.status = ProcessStatus.ERROR
            return False
    
    async def add_task(self, task: DaemonTask) -> bool:
        """Add a task to the daemon's queue."""
        try:
            if not self.enabled or self.status != ProcessStatus.ACTIVE:
                logger.warning(f"Cannot add task to inactive daemon {self.name}")
                return False
            
            await self.task_queue.put(task)
            logger.info(f"📝 Task added to daemon {self.name}: {task.description}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding task to daemon {self.name}: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        return {
            "name": self.name,
            "type": self.daemon_type.value,
            "status": self.status.value,
            "enabled": self.enabled,
            "current_task": self.current_task.description if self.current_task else None,
            "queue_size": self.task_queue.qsize(),
            "running_tasks": len(self.running_tasks),
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "total_runtime": self.metrics.total_runtime,
                "average_task_time": self.metrics.average_task_time,
                "last_activity": self.metrics.last_activity.isoformat() if self.metrics.last_activity else None,
                "discoveries_made": self.metrics.discoveries_made,
                "knowledge_items_created": self.metrics.knowledge_items_created
            },
            "error_count": self.error_count,
            "last_error": self.last_error
        }
    
    # Abstract methods to be implemented by specific daemons
    
    async def _initialize(self) -> None:
        """Initialize daemon-specific components."""
        pass
    
    async def _cleanup(self) -> None:
        """Cleanup daemon-specific resources."""
        pass
    
    async def _generate_autonomous_tasks(self) -> List[DaemonTask]:
        """Generate autonomous tasks based on system state."""
        return []
    
    async def _execute_task(self, task: DaemonTask) -> Dict[str, Any]:
        """Execute a specific task."""
        return {"status": "completed", "message": "Default task execution"}
    
    # Private methods
    
    async def _daemon_loop(self) -> None:
        """Main daemon processing loop."""
        while self.status == ProcessStatus.ACTIVE:
            try:
                # Generate autonomous tasks
                if self.enabled:
                    autonomous_tasks = await self._generate_autonomous_tasks()
                    for task in autonomous_tasks:
                        await self.task_queue.put(task)
                
                # Process queued tasks
                while not self.task_queue.empty() and len(self.running_tasks) < self.max_concurrent_tasks:
                    task = await self.task_queue.get()
                    asyncio.create_task(self._process_task(task))
                
                # Sleep before next cycle
                await asyncio.sleep(self.sleep_interval)
                
            except Exception as e:
                logger.error(f"Error in daemon loop for {self.name}: {e}")
                self.error_count += 1
                self.last_error = str(e)
                
                if self.error_count > 10:  # Stop daemon after too many errors
                    logger.error(f"Too many errors in daemon {self.name}, stopping")
                    self.status = ProcessStatus.ERROR
                    break
                
                await asyncio.sleep(self.sleep_interval * 2)  # Longer sleep on error
    
    async def _process_task(self, task: DaemonTask) -> None:
        """Process a single task."""
        start_time = time.time()
        task.started_at = datetime.now()
        task.status = "running"
        self.current_task = task
        self.running_tasks.add(task.id)
        
        try:
            logger.info(f"🔄 Daemon {self.name} executing task: {task.description}")
            
            # Execute the task with timeout
            result = await asyncio.wait_for(
                self._execute_task(task),
                timeout=self.task_timeout
            )
            
            # Update task status
            task.completed_at = datetime.now()
            task.status = "completed"
            task.result = result
            
            # Update metrics
            processing_time = time.time() - start_time
            self.metrics.tasks_completed += 1
            self.metrics.total_runtime += processing_time
            self.metrics.average_task_time = self.metrics.total_runtime / self.metrics.tasks_completed
            self.metrics.last_activity = datetime.now()
            
            # Check for discoveries or knowledge creation
            if result.get("discoveries_made", 0) > 0:
                self.metrics.discoveries_made += result["discoveries_made"]
            if result.get("knowledge_items_created", 0) > 0:
                self.metrics.knowledge_items_created += result["knowledge_items_created"]
            
            logger.info(f"✅ Daemon {self.name} completed task: {task.description} in {processing_time:.2f}s")
            
            # Broadcast update
            if self.websocket_manager:
                await self.websocket_manager.broadcast_cognitive_update({
                    "type": "daemon_task_completed",
                    "daemon": self.name,
                    "task": task.description,
                    "processing_time": processing_time,
                    "result": result
                })
            
        except asyncio.TimeoutError:
            task.status = "timeout"
            task.error = f"Task timed out after {self.task_timeout} seconds"
            self.metrics.tasks_failed += 1
            logger.warning(f"⏰ Task timeout in daemon {self.name}: {task.description}")
            
        except Exception as e:
            task.status = "error"
            task.error = str(e)
            self.metrics.tasks_failed += 1
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"❌ Task error in daemon {self.name}: {e}")
            
        finally:
            # Cleanup
            self.running_tasks.discard(task.id)
            self.completed_tasks[task.id] = task
            if self.current_task and self.current_task.id == task.id:
                self.current_task = None
            
            # Keep only recent completed tasks
            if len(self.completed_tasks) > 100:
                oldest_tasks = sorted(self.completed_tasks.items(), 
                                    key=lambda x: x[1].completed_at or datetime.min)
                for task_id, _ in oldest_tasks[:20]:  # Remove 20 oldest
                    del self.completed_tasks[task_id]
    
    async def _cancel_task(self, task_id: str) -> None:
        """Cancel a running task."""
        if task_id in self.running_tasks:
            logger.info(f"🚫 Canceling task {task_id} in daemon {self.name}")
            # Note: In a real implementation, you'd need to track and cancel the actual asyncio task
            self.running_tasks.discard(task_id)


class KnowledgeGapDetectorDaemon(AgenticDaemon):
    """Daemon for detecting knowledge gaps in the system."""
    
    def __init__(self, cognitive_manager=None, knowledge_pipeline=None, websocket_manager=None):
        super().__init__(
            daemon_type=DaemonType.KNOWLEDGE_GAP_DETECTOR,
            name="Knowledge Gap Detector",
            cognitive_manager=cognitive_manager,
            knowledge_pipeline=knowledge_pipeline,
            websocket_manager=websocket_manager
        )
        self.sleep_interval = 120  # Check every 2 minutes
    
    async def _generate_autonomous_tasks(self) -> List[DaemonTask]:
        """Generate tasks to detect knowledge gaps."""
        tasks = []
        
        # Regular gap analysis task
        if datetime.now().minute % 5 == 0:  # Every 5 minutes
            task = DaemonTask(
                type="gap_analysis",
                description="Analyze system for knowledge gaps",
                priority=7,
                parameters={"analysis_type": "comprehensive"}
            )
            tasks.append(task)
        
        return tasks
    
    async def _execute_task(self, task: DaemonTask) -> Dict[str, Any]:
        """Execute knowledge gap detection task."""
        try:
            if task.type == "gap_analysis":
                gaps = []
                
                if self.cognitive_manager:
                    gaps = await self.cognitive_manager.identify_knowledge_gaps()
                
                return {
                    "status": "completed",
                    "gaps_found": len(gaps),
                    "discoveries_made": len(gaps),
                    "gaps": [gap.__dict__ for gap in gaps]
                }
            
            return {"status": "completed", "message": "Unknown task type"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}


class AutonomousResearcherDaemon(AgenticDaemon):
    """Daemon for autonomous research and knowledge acquisition."""
    
    def __init__(self, cognitive_manager=None, knowledge_pipeline=None, websocket_manager=None):
        super().__init__(
            daemon_type=DaemonType.AUTONOMOUS_RESEARCHER,
            name="Autonomous Researcher",
            cognitive_manager=cognitive_manager,
            knowledge_pipeline=knowledge_pipeline,
            websocket_manager=websocket_manager
        )
        self.sleep_interval = 300  # Research every 5 minutes
    
    async def _generate_autonomous_tasks(self) -> List[DaemonTask]:
        """Generate autonomous research tasks."""
        tasks = []
        
        # Research based on identified gaps
        if self.cognitive_manager:
            gaps = await self.cognitive_manager.identify_knowledge_gaps()
            for gap in gaps[:3]:  # Research top 3 priority gaps
                task = DaemonTask(
                    type="research_gap",
                    description=f"Research knowledge gap: {gap.description[:50]}...",
                    priority=8,
                    parameters={"gap_id": gap.id, "domain": gap.domain}
                )
                tasks.append(task)
        
        return tasks
    
    async def _execute_task(self, task: DaemonTask) -> Dict[str, Any]:
        """Execute autonomous research task."""
        try:
            if task.type == "research_gap":
                # Simulate research process
                gap_id = task.parameters.get("gap_id")
                domain = task.parameters.get("domain", "general")
                
                # In a real implementation, this would:
                # 1. Search external knowledge sources
                # 2. Process and integrate findings
                # 3. Update knowledge base
                
                research_result = {
                    "sources_searched": ["wikipedia", "arxiv", "conceptnet"],
                    "documents_found": 5,
                    "entities_extracted": 12,
                    "relationships_discovered": 8
                }
                
                if self.knowledge_pipeline:
                    # Simulate knowledge integration
                    await self.knowledge_pipeline.process_text_document(
                        content=f"Research findings for {domain} domain gap",
                        title=f"Autonomous Research - {domain}",
                        metadata={"gap_id": gap_id, "source": "autonomous_research"}
                    )
                
                return {
                    "status": "completed",
                    "research_result": research_result,
                    "knowledge_items_created": research_result["entities_extracted"],
                    "discoveries_made": 1
                }
            
            return {"status": "completed", "message": "Unknown task type"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}


class SystemOptimizerDaemon(AgenticDaemon):
    """Daemon for system optimization and performance improvement."""
    
    def __init__(self, cognitive_manager=None, knowledge_pipeline=None, websocket_manager=None):
        super().__init__(
            daemon_type=DaemonType.SYSTEM_OPTIMIZER,
            name="System Optimizer",
            cognitive_manager=cognitive_manager,
            knowledge_pipeline=knowledge_pipeline,
            websocket_manager=websocket_manager
        )
        self.sleep_interval = 600  # Optimize every 10 minutes
    
    async def _generate_autonomous_tasks(self) -> List[DaemonTask]:
        """Generate system optimization tasks."""
        tasks = []
        
        # Performance analysis task
        task = DaemonTask(
            type="performance_analysis",
            description="Analyze system performance and identify optimizations",
            priority=6,
            parameters={"analysis_scope": "full_system"}
        )
        tasks.append(task)
        
        return tasks
    
    async def _execute_task(self, task: DaemonTask) -> Dict[str, Any]:
        """Execute system optimization task."""
        try:
            if task.type == "performance_analysis":
                # Analyze cognitive manager performance
                optimization_suggestions = []
                
                if self.cognitive_manager:
                    state = await self.cognitive_manager.get_cognitive_state()
                    metrics = state.get("processing_metrics", {})
                    
                    # Check average processing time
                    avg_time = metrics.get("average_processing_time", 0)
                    if avg_time > 5.0:  # More than 5 seconds
                        optimization_suggestions.append({
                            "component": "cognitive_manager",
                            "issue": "slow_processing",
                            "suggestion": "Consider caching frequent queries or optimizing reasoning depth"
                        })
                    
                    # Check success rate
                    total = metrics.get("total_queries", 1)
                    successful = metrics.get("successful_queries", 0)
                    success_rate = successful / total
                    if success_rate < 0.8:  # Less than 80% success
                        optimization_suggestions.append({
                            "component": "cognitive_manager",
                            "issue": "low_success_rate",
                            "suggestion": "Improve error handling and fallback mechanisms"
                        })
                
                return {
                    "status": "completed",
                    "optimizations_identified": len(optimization_suggestions),
                    "suggestions": optimization_suggestions,
                    "discoveries_made": len(optimization_suggestions)
                }
            
            return {"status": "completed", "message": "Unknown task type"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}


class AgenticDaemonSystem:
    """Manages the collection of agentic daemons."""
    
    def __init__(self, cognitive_manager=None, knowledge_pipeline=None, websocket_manager=None,
                 consciousness_engine=None):
        # Deferred import to avoid circular dependency (grounding_coherence_daemon
        # imports AgenticDaemon/DaemonTask/DaemonType from this module).
        from backend.core.grounding_coherence_daemon import GroundingCoherenceDaemon

        self.cognitive_manager = cognitive_manager
        self.knowledge_pipeline = knowledge_pipeline
        self.websocket_manager = websocket_manager
        self.consciousness_engine = consciousness_engine
        
        # Initialize daemons
        self.daemons: Dict[str, AgenticDaemon] = {
            "knowledge_gap_detector": KnowledgeGapDetectorDaemon(
                cognitive_manager, knowledge_pipeline, websocket_manager
            ),
            "autonomous_researcher": AutonomousResearcherDaemon(
                cognitive_manager, knowledge_pipeline, websocket_manager
            ),
            "system_optimizer": SystemOptimizerDaemon(
                cognitive_manager, knowledge_pipeline, websocket_manager
            ),
            "grounding_coherence": GroundingCoherenceDaemon(
                cognitive_manager, knowledge_pipeline, websocket_manager,
                consciousness_engine=consciousness_engine
            )
        }
        
        self.enabled = True
        self.startup_time = datetime.now()
        
        logger.info(f"AgenticDaemonSystem initialized with {len(self.daemons)} daemons")
    
    async def start_all(self) -> Dict[str, bool]:
        """Start all daemons."""
        results = {}
        
        for name, daemon in self.daemons.items():
            try:
                result = await daemon.start()
                results[name] = result
                logger.info(f"{'✅' if result else '❌'} Daemon {name}: {'started' if result else 'failed'}")
            except Exception as e:
                results[name] = False
                logger.error(f"❌ Error starting daemon {name}: {e}")
        
        return results
    
    async def stop_all(self) -> Dict[str, bool]:
        """Stop all daemons."""
        results = {}
        
        for name, daemon in self.daemons.items():
            try:
                result = await daemon.stop()
                results[name] = result
                logger.info(f"{'✅' if result else '❌'} Daemon {name}: {'stopped' if result else 'failed'}")
            except Exception as e:
                results[name] = False
                logger.error(f"❌ Error stopping daemon {name}: {e}")
        
        return results
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        daemon_statuses = {}
        
        for name, daemon in self.daemons.items():
            daemon_statuses[name] = await daemon.get_status()
        
        # Calculate aggregate metrics
        total_tasks_completed = sum(status["metrics"]["tasks_completed"] for status in daemon_statuses.values())
        total_discoveries = sum(status["metrics"]["discoveries_made"] for status in daemon_statuses.values())
        total_knowledge_items = sum(status["metrics"]["knowledge_items_created"] for status in daemon_statuses.values())
        
        active_daemons = sum(1 for status in daemon_statuses.values() if status["status"] == "active")
        
        return {
            "system_enabled": self.enabled,
            "startup_time": self.startup_time.isoformat(),
            "uptime_hours": (datetime.now() - self.startup_time).total_seconds() / 3600,
            "active_daemons": active_daemons,
            "total_daemons": len(self.daemons),
            "aggregate_metrics": {
                "total_tasks_completed": total_tasks_completed,
                "total_discoveries": total_discoveries,
                "total_knowledge_items_created": total_knowledge_items
            },
            "daemons": daemon_statuses
        }
    
    async def trigger_daemon(self, daemon_name: str, task_type: str, parameters: Dict[str, Any] = None) -> bool:
        """Manually trigger a specific daemon with a custom task."""
        if daemon_name not in self.daemons:
            logger.error(f"Unknown daemon: {daemon_name}")
            return False
        
        daemon = self.daemons[daemon_name]
        task = DaemonTask(
            type=task_type,
            description=f"Manual trigger: {task_type}",
            priority=9,
            parameters=parameters or {}
        )
        
        return await daemon.add_task(task)
    
    def enable_daemon(self, daemon_name: str) -> bool:
        """Enable a specific daemon."""
        if daemon_name in self.daemons:
            self.daemons[daemon_name].enabled = True
            logger.info(f"✅ Enabled daemon: {daemon_name}")
            return True
        return False
    
    def disable_daemon(self, daemon_name: str) -> bool:
        """Disable a specific daemon."""
        if daemon_name in self.daemons:
            self.daemons[daemon_name].enabled = False
            logger.info(f"🚫 Disabled daemon: {daemon_name}")
            return True
        return False


# Global instance
agentic_daemon_system: Optional[AgenticDaemonSystem] = None


async def get_agentic_daemon_system(cognitive_manager=None, knowledge_pipeline=None, websocket_manager=None,
                                    consciousness_engine=None) -> AgenticDaemonSystem:
    """Get or create the global agentic daemon system."""
    global agentic_daemon_system
    
    if agentic_daemon_system is None:
        agentic_daemon_system = AgenticDaemonSystem(
            cognitive_manager=cognitive_manager,
            knowledge_pipeline=knowledge_pipeline,
            websocket_manager=websocket_manager,
            consciousness_engine=consciousness_engine
        )
    
    return agentic_daemon_system
