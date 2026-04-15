#!/usr/bin/env python3
"""
Advanced Cognitive Process Orchestrator

This module implements sophisticated cognitive process orchestration with
state machines, dependency management, and advanced error recovery strategies.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class ProcessState(Enum):
    """States for cognitive processes."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


class ProcessPriority(Enum):
    """Priority levels for process scheduling."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class RecoveryStrategy(Enum):
    """Recovery strategies for failed processes."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ESCALATE = "escalate"
    COMPENSATE = "compensate"


@dataclass
class ProcessDependency:
    """Dependency between cognitive processes."""
    process_id: str
    dependency_type: str = "completion"  # completion, data, resource
    optional: bool = False
    timeout: Optional[float] = None


@dataclass
class ProcessMetrics:
    """Metrics for cognitive process execution."""
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    attempts: int = 1
    errors: List[str] = field(default_factory=list)
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


@dataclass
class CognitiveProcess:
    """Represents a cognitive process in the orchestration system."""
    id: str
    name: str
    process_type: str
    priority: ProcessPriority
    state: ProcessState = ProcessState.PENDING
    dependencies: List[ProcessDependency] = field(default_factory=list)
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    max_retries: int = 3
    timeout: Optional[float] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: Optional[ProcessMetrics] = None
    error_message: Optional[str] = None
    result: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = ProcessMetrics(start_time=time.time())


class ProcessExecutor:
    """Executes cognitive processes with proper lifecycle management."""
    
    def __init__(self, process_handlers: Dict[str, Callable]):
        self.process_handlers = process_handlers
        self.active_executions: Dict[str, asyncio.Task] = {}
        
    async def execute_process(self, process: CognitiveProcess) -> Any:
        """Execute a cognitive process with proper error handling."""
        process.state = ProcessState.INITIALIZING
        process.metrics.start_time = time.time()
        
        try:
            # Get the handler for this process type
            handler = self.process_handlers.get(process.process_type)
            if not handler:
                raise ValueError(f"No handler for process type: {process.process_type}")
            
            process.state = ProcessState.RUNNING
            logger.info(f"🚀 Executing process {process.name} (ID: {process.id})")
            
            # Execute with timeout if specified
            if process.timeout:
                result = await asyncio.wait_for(
                    handler(process), 
                    timeout=process.timeout
                )
            else:
                result = await handler(process)
            
            process.state = ProcessState.COMPLETED
            process.result = result
            process.metrics.end_time = time.time()
            process.metrics.duration = process.metrics.end_time - process.metrics.start_time
            
            logger.info(f"✅ Process {process.name} completed in {process.metrics.duration:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            process.state = ProcessState.FAILED
            process.error_message = f"Process timed out after {process.timeout}s"
            process.metrics.errors.append(process.error_message)
            logger.error(f"⏰ Process {process.name} timed out")
            raise
            
        except Exception as e:
            process.state = ProcessState.FAILED
            process.error_message = str(e)
            process.metrics.errors.append(process.error_message)
            process.metrics.attempts += 1
            logger.error(f"❌ Process {process.name} failed: {e}")
            raise


class DependencyResolver:
    """Resolves dependencies between cognitive processes."""
    
    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.completion_events: Dict[str, asyncio.Event] = {}
        
    def add_dependency(self, process_id: str, dependency: ProcessDependency):
        """Add a dependency relationship."""
        self.dependency_graph[process_id].add(dependency.process_id)
        
    def get_dependencies(self, process_id: str) -> Set[str]:
        """Get all dependencies for a process."""
        return self.dependency_graph.get(process_id, set())
        
    def is_ready(self, process: CognitiveProcess, completed_processes: Set[str]) -> bool:
        """Check if a process is ready to execute (all dependencies met)."""
        required_deps = {
            dep.process_id for dep in process.dependencies 
            if not dep.optional
        }
        return required_deps.issubset(completed_processes)
        
    def get_execution_order(self, processes: List[CognitiveProcess]) -> List[str]:
        """Get topologically sorted execution order for processes."""
        # Simple topological sort implementation
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        # Build graph
        for process in processes:
            for dep in process.dependencies:
                graph[dep.process_id].append(process.id)
                in_degree[process.id] += 1
        
        # Find processes with no dependencies
        queue = [p.id for p in processes if in_degree[p.id] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result


class ErrorRecoveryManager:
    """Manages error recovery strategies for cognitive processes."""
    
    def __init__(self):
        self.recovery_policies: Dict[str, Dict[str, Any]] = {}
        self.failure_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
    def register_recovery_policy(self, process_type: str, policy: Dict[str, Any]):
        """Register a recovery policy for a process type."""
        self.recovery_policies[process_type] = policy
        
    async def handle_failure(self, process: CognitiveProcess, exception: Exception) -> Dict[str, Any]:
        """Handle process failure with appropriate recovery strategy."""
        failure_record = {
            "timestamp": time.time(),
            "error": str(exception),
            "attempt": process.metrics.attempts,
            "process_id": process.id
        }
        self.failure_history[process.process_type].append(failure_record)
        
        policy = self.recovery_policies.get(process.process_type, {})
        strategy = process.recovery_strategy
        
        if strategy == RecoveryStrategy.RETRY and process.metrics.attempts < process.max_retries:
            delay = policy.get("retry_delay", 1.0) * (2 ** (process.metrics.attempts - 1))
            logger.info(f"🔄 Retrying process {process.name} in {delay}s (attempt {process.metrics.attempts + 1})")
            await asyncio.sleep(delay)
            return {"action": "retry", "delay": delay}
            
        elif strategy == RecoveryStrategy.FALLBACK:
            fallback_handler = policy.get("fallback_handler")
            if fallback_handler:
                logger.info(f"🔀 Using fallback for process {process.name}")
                try:
                    result = await fallback_handler(process)
                    return {"action": "fallback", "result": result}
                except Exception as e:
                    logger.error(f"Fallback failed for {process.name}: {e}")
                    
        elif strategy == RecoveryStrategy.COMPENSATE:
            compensation_handler = policy.get("compensation_handler")
            if compensation_handler:
                logger.info(f"⚖️ Compensating for process {process.name}")
                await compensation_handler(process, exception)
                return {"action": "compensate"}
                
        elif strategy == RecoveryStrategy.SKIP:
            logger.info(f"⏭️ Skipping failed process {process.name}")
            return {"action": "skip"}
            
        else:  # ESCALATE
            logger.error(f"🚨 Escalating failure of process {process.name}")
            return {"action": "escalate", "error": str(exception)}


class CognitiveOrchestrator:
    """
    Advanced orchestrator for cognitive processes with state management,
    dependency resolution, and sophisticated error recovery.
    """
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.processes: Dict[str, CognitiveProcess] = {}
        self.process_queues: Dict[ProcessPriority, deque] = {
            priority: deque() for priority in ProcessPriority
        }
        self.executor = ProcessExecutor({})
        self.dependency_resolver = DependencyResolver()
        self.error_recovery = ErrorRecoveryManager()
        self.active_workflows: Dict[str, List[str]] = {}
        self.workflow_state: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.orchestration_metrics = {
            "processes_executed": 0,
            "processes_failed": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "active_processes": 0,
            "queued_processes": 0
        }
        
        # Register default recovery policies
        self._register_default_policies()
        
    def _register_default_policies(self):
        """Register default recovery policies for common process types."""
        self.error_recovery.register_recovery_policy("llm_query", {
            "retry_delay": 1.0,
            "max_retries": 3,
            "fallback_handler": self._llm_fallback_handler
        })
        
        self.error_recovery.register_recovery_policy("knowledge_retrieval", {
            "retry_delay": 0.5,
            "max_retries": 2,
            "compensation_handler": self._knowledge_compensation_handler
        })
        
        self.error_recovery.register_recovery_policy("consciousness_assessment", {
            "retry_delay": 2.0,
            "max_retries": 2,
            "fallback_handler": self._consciousness_fallback_handler
        })
    
    async def _llm_fallback_handler(self, process: CognitiveProcess) -> Dict[str, Any]:
        """Fallback handler for LLM queries."""
        return {
            "response": f"Fallback response for query: {process.data.get('query', 'Unknown')}",
            "confidence": 0.3,
            "fallback": True
        }
    
    async def _knowledge_compensation_handler(self, process: CognitiveProcess, exception: Exception):
        """Compensation handler for knowledge retrieval failures."""
        logger.info(f"Compensating for knowledge retrieval failure: {exception}")
        # Could implement cache warming or alternative sources here
    
    async def _consciousness_fallback_handler(self, process: CognitiveProcess) -> Dict[str, Any]:
        """Fallback handler for consciousness assessment."""
        return {
            "awareness_level": 0.5,
            "self_reflection_depth": 1,
            "cognitive_integration": 0.4,
            "autonomous_goals": [],
            "manifest_behaviors": ["basic_processing"],
            "fallback": True
        }
    
    def register_process_handler(self, process_type: str, handler: Callable):
        """Register a handler for a specific process type."""
        self.executor.process_handlers[process_type] = handler
        
    def create_process(self, 
                      name: str,
                      process_type: str,
                      priority: ProcessPriority = ProcessPriority.NORMAL,
                      dependencies: List[ProcessDependency] = None,
                      recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
                      timeout: Optional[float] = None,
                      data: Dict[str, Any] = None,
                      metadata: Dict[str, Any] = None) -> str:
        """Create a new cognitive process."""
        process_id = str(uuid.uuid4())
        
        process = CognitiveProcess(
            id=process_id,
            name=name,
            process_type=process_type,
            priority=priority,
            dependencies=dependencies or [],
            recovery_strategy=recovery_strategy,
            timeout=timeout,
            data=data or {},
            metadata=metadata or {}
        )
        
        self.processes[process_id] = process
        self.process_queues[priority].append(process_id)
        
        # Register dependencies
        for dep in process.dependencies:
            self.dependency_resolver.add_dependency(process_id, dep)
        
        self.orchestration_metrics["queued_processes"] += 1
        
        logger.info(f"📋 Created process {name} (ID: {process_id})")
        return process_id
    
    def create_workflow(self, workflow_id: str, process_ids: List[str], metadata: Dict[str, Any] = None):
        """Create a workflow from multiple processes."""
        self.active_workflows[workflow_id] = process_ids
        self.workflow_state[workflow_id] = {
            "status": "pending",
            "created_at": datetime.now(),
            "metadata": metadata or {},
            "completed_processes": set(),
            "failed_processes": set()
        }
        
        logger.info(f"🔗 Created workflow {workflow_id} with {len(process_ids)} processes")
    
    async def execute_process(self, process_id: str) -> Any:
        """Execute a single process with full orchestration."""
        if process_id not in self.processes:
            raise ValueError(f"Process {process_id} not found")
        
        process = self.processes[process_id]
        
        # Check dependencies
        completed_processes = {
            pid for pid, p in self.processes.items() 
            if p.state == ProcessState.COMPLETED
        }
        
        if not self.dependency_resolver.is_ready(process, completed_processes):
            missing_deps = [
                dep.process_id for dep in process.dependencies
                if dep.process_id not in completed_processes and not dep.optional
            ]
            raise RuntimeError(f"Process {process_id} dependencies not met: {missing_deps}")
        
        self.orchestration_metrics["active_processes"] += 1
        self.orchestration_metrics["queued_processes"] -= 1
        
        try:
            # Broadcast process start
            if self.websocket_manager:
                await self.websocket_manager.broadcast_cognitive_update({
                    "type": "process_started",
                    "process_id": process_id,
                    "process_name": process.name,
                    "process_type": process.process_type,
                    "timestamp": time.time()
                })
            
            result = await self.executor.execute_process(process)
            
            self.orchestration_metrics["processes_executed"] += 1
            self.orchestration_metrics["total_execution_time"] += process.metrics.duration
            self.orchestration_metrics["average_execution_time"] = (
                self.orchestration_metrics["total_execution_time"] / 
                self.orchestration_metrics["processes_executed"]
            )
            
            # Broadcast process completion
            if self.websocket_manager:
                await self.websocket_manager.broadcast_cognitive_update({
                    "type": "process_completed",
                    "process_id": process_id,
                    "process_name": process.name,
                    "duration": process.metrics.duration,
                    "timestamp": time.time()
                })
            
            return result
            
        except Exception as e:
            self.orchestration_metrics["processes_failed"] += 1
            
            # Try recovery
            recovery_result = await self.error_recovery.handle_failure(process, e)
            
            if recovery_result.get("action") == "retry":
                return await self.execute_process(process_id)
            elif recovery_result.get("action") == "fallback":
                return recovery_result.get("result")
            else:
                # Broadcast process failure
                if self.websocket_manager:
                    await self.websocket_manager.broadcast_cognitive_update({
                        "type": "process_failed",
                        "process_id": process_id,
                        "process_name": process.name,
                        "error": str(e),
                        "recovery_action": recovery_result.get("action"),
                        "timestamp": time.time()
                    })
                raise
        finally:
            self.orchestration_metrics["active_processes"] -= 1
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a complete workflow with proper coordination."""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        process_ids = self.active_workflows[workflow_id]
        workflow_state = self.workflow_state[workflow_id]
        workflow_state["status"] = "running"
        workflow_state["start_time"] = time.time()
        
        logger.info(f"🎯 Executing workflow {workflow_id}")
        
        # Get execution order
        processes = [self.processes[pid] for pid in process_ids]
        execution_order = self.dependency_resolver.get_execution_order(processes)
        
        results = {}
        
        try:
            for process_id in execution_order:
                try:
                    result = await self.execute_process(process_id)
                    results[process_id] = result
                    workflow_state["completed_processes"].add(process_id)
                    
                except Exception as e:
                    workflow_state["failed_processes"].add(process_id)
                    logger.error(f"Process {process_id} failed in workflow {workflow_id}: {e}")
                    
                    # Check if we should continue or abort
                    process = self.processes[process_id]
                    if process.recovery_strategy == RecoveryStrategy.ESCALATE:
                        workflow_state["status"] = "failed"
                        workflow_state["error"] = str(e)
                        raise
            
            workflow_state["status"] = "completed"
            workflow_state["end_time"] = time.time()
            workflow_state["duration"] = workflow_state["end_time"] - workflow_state["start_time"]
            
            logger.info(f"✅ Workflow {workflow_id} completed in {workflow_state['duration']:.2f}s")
            
            return {
                "workflow_id": workflow_id,
                "status": workflow_state["status"],
                "results": results,
                "completed_processes": len(workflow_state["completed_processes"]),
                "failed_processes": len(workflow_state["failed_processes"]),
                "duration": workflow_state["duration"]
            }
            
        except Exception as e:
            workflow_state["status"] = "failed"
            workflow_state["error"] = str(e)
            logger.error(f"❌ Workflow {workflow_id} failed: {e}")
            raise
    
    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestration status."""
        active_processes = [
            {
                "id": p.id,
                "name": p.name,
                "type": p.process_type,
                "state": p.state.value,
                "priority": p.priority.value,
                "duration": time.time() - p.metrics.start_time if p.state == ProcessState.RUNNING else None
            }
            for p in self.processes.values()
            if p.state in [ProcessState.RUNNING, ProcessState.WAITING]
        ]
        
        return {
            "orchestration_metrics": self.orchestration_metrics,
            "active_processes": active_processes,
            "active_workflows": len(self.active_workflows),
            "process_queues": {
                priority.name: len(queue) 
                for priority, queue in self.process_queues.items()
            },
            "failure_history": dict(self.error_recovery.failure_history),
            "timestamp": datetime.now().isoformat()
        }
