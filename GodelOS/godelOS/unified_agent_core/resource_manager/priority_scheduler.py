"""
Priority Scheduler Implementation for GodelOS

This module implements the PriorityScheduler class, which is responsible for
scheduling tasks based on priority and managing resource allocation for the
UnifiedAgentCore.
"""

import logging
import time
import asyncio
import heapq
from typing import Dict, List, Optional, Any, Tuple

from godelOS.unified_agent_core.resource_manager.interfaces import (
    ResourceRequirements, ResourceAllocation, ResourcePriority,
    PrioritySchedulerInterface
)

logger = logging.getLogger(__name__)


class TaskDependency:
    """Class representing a dependency between tasks."""
    
    def __init__(self, source_id: str, target_id: str, dependency_type: str = "completion"):
        """
        Initialize a task dependency.
        
        Args:
            source_id: The ID of the source task (dependent)
            target_id: The ID of the target task (dependency)
            dependency_type: The type of dependency (completion, start, resource)
        """
        self.source_id = source_id
        self.target_id = target_id
        self.dependency_type = dependency_type
        self.created_at = time.time()
        self.satisfied = False
        self.satisfied_at: Optional[float] = None
    
    def satisfy(self) -> None:
        """Mark the dependency as satisfied."""
        self.satisfied = True
        self.satisfied_at = time.time()


class Task:
    """Class representing a task to be scheduled."""
    
    def __init__(self, task_id: str, data: Dict[str, Any], requirements: ResourceRequirements):
        """
        Initialize a task.
        
        Args:
            task_id: The ID of the task
            data: The task data
            requirements: The resource requirements for the task
        """
        self.id = task_id
        self.data = data
        self.requirements = requirements
        self.priority = requirements.priority
        self.created_at = time.time()
        self.scheduled_at: Optional[float] = None
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.allocation: Optional[ResourceAllocation] = None
        self.status = "pending"  # pending, scheduled, running, completed, failed, preempted
        self.result: Optional[Dict[str, Any]] = None
        
        # Advanced scheduling attributes
        self.deadline: Optional[float] = requirements.deadline
        self.dependencies: List[TaskDependency] = []
        self.dependents: List[str] = []  # IDs of tasks that depend on this task
        self.importance: float = 0.5  # Task importance (0.0 to 1.0)
        self.urgency: float = 0.5  # Task urgency (0.0 to 1.0)
        self.fairness_factor: float = 1.0  # Fairness adjustment factor
        self.resource_efficiency: float = 1.0  # Resource usage efficiency
        self.estimated_duration: Optional[float] = data.get("estimated_duration")
        self.actual_duration: Optional[float] = None
        self.user_id: Optional[str] = data.get("user_id")
        self.group_id: Optional[str] = data.get("group_id")
        self.tags: List[str] = data.get("tags", [])
        self.preemption_count: int = 0  # Number of times this task has been preempted
        self.retry_count: int = 0  # Number of times this task has been retried
    
    def get_effective_priority(self) -> float:
        """
        Get the effective priority using multi-factor calculation.
        
        Factors:
        - Base priority (from ResourcePriority enum)
        - Waiting time (starvation prevention)
        - Deadline proximity
        - Importance and urgency
        - Fairness adjustments
        - Dependency status
        
        Returns:
            The effective priority value (higher is more important)
        """
        # Map enum to numeric priority
        priority_values = {
            ResourcePriority.CRITICAL: 100,
            ResourcePriority.HIGH: 80,
            ResourcePriority.MEDIUM: 60,
            ResourcePriority.LOW: 40,
            ResourcePriority.BACKGROUND: 20
        }
        
        base_priority = priority_values.get(self.priority, 50)
        
        # Calculate factors
        current_time = time.time()
        
        # Starvation prevention factor
        wait_time = current_time - self.created_at
        wait_factor = min(1.0, wait_time / 3600)  # Max boost after 1 hour
        starvation_boost = 20 * wait_factor
        
        # Deadline factor (higher boost as deadline approaches)
        deadline_boost = 0
        if self.deadline:
            time_to_deadline = max(0, self.deadline - current_time)
            if time_to_deadline > 0:
                # Exponential boost as deadline approaches
                deadline_factor = max(0, 1.0 - (time_to_deadline / 3600))  # Normalize to 1 hour
                deadline_boost = 30 * (deadline_factor ** 2)  # Quadratic boost
            else:
                # Past deadline, maximum boost
                deadline_boost = 50
        
        # Importance and urgency factor
        importance_urgency_boost = 15 * (self.importance * 0.4 + self.urgency * 0.6)
        
        # Fairness adjustment
        fairness_adjustment = 10 * (self.fairness_factor - 1.0)
        
        # Dependency status (boost if all dependencies are satisfied)
        dependency_boost = 0
        if self.dependencies and all(dep.satisfied for dep in self.dependencies):
            dependency_boost = 10
        
        # Preemption penalty (reduce priority if task has been preempted many times)
        preemption_penalty = min(15, self.preemption_count * 5)
        
        # Calculate final effective priority
        effective_priority = (
            base_priority +
            starvation_boost +
            deadline_boost +
            importance_urgency_boost +
            fairness_adjustment +
            dependency_boost -
            preemption_penalty
        )
        
        return effective_priority
    
    def get_urgency_score(self) -> float:
        """
        Calculate the urgency score for deadline-aware scheduling.
        
        Returns:
            Urgency score (0.0 to 1.0, higher means more urgent)
        """
        if not self.deadline:
            return self.urgency
        
        current_time = time.time()
        time_to_deadline = max(0, self.deadline - current_time)
        
        # Calculate urgency based on deadline
        if time_to_deadline <= 0:
            # Past deadline
            return 1.0
        
        # Exponential urgency as deadline approaches
        estimated_time = self.estimated_duration or 600  # Default 10 minutes
        urgency_factor = 1.0 - (time_to_deadline / (estimated_time * 3))
        
        return max(self.urgency, min(1.0, urgency_factor))
    
    def add_dependency(self, target_id: str, dependency_type: str = "completion") -> None:
        """
        Add a dependency to this task.
        
        Args:
            target_id: The ID of the target task (dependency)
            dependency_type: The type of dependency
        """
        dependency = TaskDependency(self.id, target_id, dependency_type)
        self.dependencies.append(dependency)
    
    def are_dependencies_satisfied(self) -> bool:
        """
        Check if all dependencies are satisfied.
        
        Returns:
            True if all dependencies are satisfied or there are no dependencies
        """
        if not self.dependencies:
            return True
        
        return all(dep.satisfied for dep in self.dependencies)
    
    def calculate_resource_efficiency(self) -> float:
        """
        Calculate resource efficiency based on resource usage and results.
        
        Returns:
            Resource efficiency score (higher is better)
        """
        if not self.completed_at or not self.started_at:
            return self.resource_efficiency
        
        # Calculate actual duration
        self.actual_duration = self.completed_at - self.started_at
        
        # Calculate efficiency based on estimated vs actual duration
        if self.estimated_duration and self.actual_duration:
            duration_ratio = self.estimated_duration / self.actual_duration
            return min(2.0, max(0.5, duration_ratio))
        
        return self.resource_efficiency
    
    def __lt__(self, other: 'Task') -> bool:
        """Compare tasks for priority queue ordering."""
        return self.get_effective_priority() > other.get_effective_priority()


class SchedulingPolicy:
    """Class representing a scheduling policy."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize a scheduling policy.
        
        Args:
            name: The name of the policy
            config: Policy configuration
        """
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.weight = config.get("weight", 1.0)
    
    def apply(self, tasks: List[Task], system_load: Dict[str, float]) -> List[Task]:
        """
        Apply the scheduling policy to sort tasks.
        
        Args:
            tasks: List of tasks to schedule
            system_load: Current system load information
            
        Returns:
            Sorted list of tasks
        """
        return tasks  # Default implementation does nothing


class DeadlinePolicy(SchedulingPolicy):
    """Deadline-aware scheduling policy."""
    
    def apply(self, tasks: List[Task], system_load: Dict[str, float]) -> List[Task]:
        """Sort tasks by deadline proximity."""
        if not self.enabled:
            return tasks
            
        # Sort by urgency score (accounts for deadline)
        return sorted(tasks, key=lambda t: t.get_urgency_score(), reverse=True)


class FairnessPolicy(SchedulingPolicy):
    """Fair scheduling policy to prevent starvation."""
    
    def apply(self, tasks: List[Task], system_load: Dict[str, float]) -> List[Task]:
        """Adjust task fairness factors based on waiting time and user/group."""
        if not self.enabled:
            return tasks
            
        current_time = time.time()
        
        # Group tasks by user and group
        user_tasks: Dict[str, List[Task]] = {}
        group_tasks: Dict[str, List[Task]] = {}
        
        for task in tasks:
            if task.user_id:
                if task.user_id not in user_tasks:
                    user_tasks[task.user_id] = []
                user_tasks[task.user_id].append(task)
                
            if task.group_id:
                if task.group_id not in group_tasks:
                    group_tasks[task.group_id] = []
                group_tasks[task.group_id].append(task)
        
        # Calculate fairness adjustments
        for user_id, user_task_list in user_tasks.items():
            # Users with many pending tasks get fairness boost
            if len(user_task_list) > 3:
                for task in user_task_list:
                    task.fairness_factor = min(2.0, task.fairness_factor * 1.2)
        
        # Apply waiting time adjustments
        long_wait_threshold = self.config.get("long_wait_threshold", 1800)  # 30 minutes
        for task in tasks:
            wait_time = current_time - task.created_at
            if wait_time > long_wait_threshold:
                # Significant boost for long-waiting tasks
                task.fairness_factor = min(3.0, task.fairness_factor * 1.5)
        
        return tasks


class DependencyPolicy(SchedulingPolicy):
    """Task dependency management policy."""
    
    def apply(self, tasks: List[Task], system_load: Dict[str, float]) -> List[Task]:
        """Prioritize tasks with satisfied dependencies."""
        if not self.enabled:
            return tasks
            
        # Separate tasks with satisfied dependencies
        satisfied = [t for t in tasks if t.are_dependencies_satisfied()]
        unsatisfied = [t for t in tasks if not t.are_dependencies_satisfied()]
        
        # Sort each group by effective priority
        satisfied.sort(key=lambda t: t.get_effective_priority(), reverse=True)
        unsatisfied.sort(key=lambda t: t.get_effective_priority(), reverse=True)
        
        # Satisfied dependencies come first
        return satisfied + unsatisfied


class LoadBalancingPolicy(SchedulingPolicy):
    """Adaptive scheduling based on system load."""
    
    def apply(self, tasks: List[Task], system_load: Dict[str, float]) -> List[Task]:
        """Adjust scheduling based on current system load."""
        if not self.enabled:
            return tasks
            
        # High load: prioritize lightweight tasks
        if system_load.get("cpu", 0) > 0.8 or system_load.get("memory", 0) > 0.8:
            # Sort by resource requirements (ascending)
            return sorted(tasks, key=lambda t: t.requirements.compute + t.requirements.memory)
            
        # Low load: prioritize resource-intensive tasks
        elif system_load.get("cpu", 0) < 0.3 and system_load.get("memory", 0) < 0.3:
            # Sort by resource requirements (descending)
            return sorted(tasks, key=lambda t: -(t.requirements.compute + t.requirements.memory))
            
        return tasks


class PriorityScheduler(PrioritySchedulerInterface):
    """
    PriorityScheduler implementation for GodelOS.
    
    The PriorityScheduler is responsible for scheduling tasks based on priority
    and managing resource allocation for the UnifiedAgentCore.
    
    Features:
    - Multi-factor priority calculation
    - Deadline-aware scheduling
    - Fair scheduling with starvation prevention
    - Task dependency management
    - Adaptive scheduling based on system load
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the priority scheduler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize task tracking
        self.tasks: Dict[str, Task] = {}
        self.pending_tasks: List[Task] = []  # Priority queue (heapq)
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.dependencies: Dict[str, List[TaskDependency]] = {}  # target_id -> [dependencies]
        
        # Initialize scheduling parameters
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 10)
        self.preemption_enabled = self.config.get("preemption_enabled", True)
        self.task_timeout = self.config.get("task_timeout", 3600)  # 1 hour default
        self.fairness_enabled = self.config.get("fairness_enabled", True)
        self.dependency_tracking_enabled = self.config.get("dependency_tracking_enabled", True)
        self.adaptive_scheduling_enabled = self.config.get("adaptive_scheduling_enabled", True)
        
        # Initialize scheduling policies
        self.policies = {
            "deadline": DeadlinePolicy("deadline", self.config.get("deadline_policy", {"enabled": True, "weight": 1.0})),
            "fairness": FairnessPolicy("fairness", self.config.get("fairness_policy", {"enabled": True, "weight": 0.8})),
            "dependency": DependencyPolicy("dependency", self.config.get("dependency_policy", {"enabled": True, "weight": 1.2})),
            "load_balancing": LoadBalancingPolicy("load_balancing", self.config.get("load_balancing_policy", {"enabled": True, "weight": 0.7}))
        }
        
        # Initialize system load tracking
        self.system_load: Dict[str, float] = {
            "cpu": 0.0,
            "memory": 0.0,
            "io": 0.0,
            "network": 0.0
        }
        self.load_history: List[Dict[str, float]] = []
        self.max_load_history = self.config.get("max_load_history", 20)
        
        # Initialize statistics
        self.statistics: Dict[str, Any] = {
            "tasks_scheduled": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_preempted": 0,
            "avg_waiting_time": 0.0,
            "avg_execution_time": 0.0
        }
        
        # Initialize lock
        self.lock = asyncio.Lock()
    
    async def schedule(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Schedule tasks based on priority.
        
        Args:
            tasks: List of tasks to schedule
            
        Returns:
            List of scheduled tasks with resource allocations
        """
        async with self.lock:
            scheduled_tasks = []
            
            # Process each task
            for task_data in tasks:
                # Extract task information
                task_id = task_data.get("id", f"task_{int(time.time())}_{len(self.tasks)}")
                requirements_data = task_data.get("requirements", {})
                
                # Create resource requirements
                requirements = ResourceRequirements(
                    compute=requirements_data.get("compute", 0.1),
                    memory=requirements_data.get("memory", 0.1),
                    attention=requirements_data.get("attention", 0.1),
                    network=requirements_data.get("network", 0.0),
                    storage=requirements_data.get("storage", 0.0),
                    priority=ResourcePriority(requirements_data.get("priority", "medium")),
                    deadline=requirements_data.get("deadline")
                )
                
                # Create task
                task = Task(task_id, task_data, requirements)
                
                # Add to task tracking
                self.tasks[task_id] = task
                heapq.heappush(self.pending_tasks, task)
                
                # Update task status
                task.status = "pending"
                
                # Add to result
                scheduled_tasks.append({
                    "id": task_id,
                    "status": "pending",
                    "effective_priority": task.get_effective_priority(),
                    "created_at": task.created_at
                })
            
            # Try to schedule pending tasks
            await self._schedule_pending_tasks()
            
            return scheduled_tasks
    
    async def preempt(self, high_priority_task: Dict[str, Any]) -> bool:
        """
        Preempt lower priority tasks for a high priority task.
        
        Args:
            high_priority_task: The high priority task
            
        Returns:
            True if preemption was successful, False otherwise
        """
        if not self.preemption_enabled:
            logger.warning("Preemption is disabled")
            return False
        
        async with self.lock:
            # Extract task information
            task_id = high_priority_task.get("id", f"task_{int(time.time())}_{len(self.tasks)}")
            requirements_data = high_priority_task.get("requirements", {})
            
            # Ensure task has high priority
            priority_str = requirements_data.get("priority", "high")
            if priority_str not in ["high", "critical"]:
                logger.warning(f"Cannot preempt for task {task_id}: not high priority")
                return False
            
            # Create resource requirements
            requirements = ResourceRequirements(
                compute=requirements_data.get("compute", 0.1),
                memory=requirements_data.get("memory", 0.1),
                attention=requirements_data.get("attention", 0.1),
                network=requirements_data.get("network", 0.0),
                storage=requirements_data.get("storage", 0.0),
                priority=ResourcePriority(priority_str),
                deadline=requirements_data.get("deadline")
            )
            
            # Create task
            task = Task(task_id, high_priority_task, requirements)
            
            # Add to task tracking
            self.tasks[task_id] = task
            
            # Find tasks to preempt
            preempted_tasks = await self._find_tasks_to_preempt(task)
            
            if not preempted_tasks:
                logger.warning(f"No suitable tasks found to preempt for task {task_id}")
                
                # Add to pending tasks
                heapq.heappush(self.pending_tasks, task)
                task.status = "pending"
                
                return False
            
            # Preempt tasks
            for preempted_task in preempted_tasks:
                # Update status
                preempted_task.status = "preempted"
                
                # Remove from running tasks
                if preempted_task.id in self.running_tasks:
                    del self.running_tasks[preempted_task.id]
                
                # Add back to pending tasks
                heapq.heappush(self.pending_tasks, preempted_task)
                
                logger.info(f"Preempted task {preempted_task.id} for high priority task {task_id}")
            
            # Schedule the high priority task
            task.status = "scheduled"
            task.scheduled_at = time.time()
            self.running_tasks[task_id] = task
            
            logger.info(f"Scheduled high priority task {task_id} after preempting {len(preempted_tasks)} tasks")
            
            return True
    
    async def get_schedule(self) -> List[Dict[str, Any]]:
        """
        Get the current task schedule.
        
        Returns:
            List of scheduled tasks
        """
        async with self.lock:
            # Check for timed out tasks
            await self._check_timeouts()
            
            # Build schedule information
            schedule = []
            
            # Add running tasks
            for task in self.running_tasks.values():
                schedule.append({
                    "id": task.id,
                    "status": task.status,
                    "priority": task.priority.value,
                    "effective_priority": task.get_effective_priority(),
                    "created_at": task.created_at,
                    "scheduled_at": task.scheduled_at,
                    "started_at": task.started_at,
                    "running_time": time.time() - (task.started_at or task.scheduled_at or task.created_at)
                })
            
            # Add top pending tasks
            pending_copy = self.pending_tasks.copy()
            pending_copy.sort()  # Sort by priority
            
            for task in pending_copy[:10]:  # Show top 10 pending tasks
                schedule.append({
                    "id": task.id,
                    "status": task.status,
                    "priority": task.priority.value,
                    "effective_priority": task.get_effective_priority(),
                    "created_at": task.created_at,
                    "waiting_time": time.time() - task.created_at
                })
            
            return schedule
    
    async def update_task_status(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: The ID of the task
            status: The new status
            result: Optional task result
            
        Returns:
            True if the task status was updated, False otherwise
        """
        async with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not found")
                return False
            
            task = self.tasks[task_id]
            old_status = task.status
            
            # Update status
            task.status = status
            
            # Update timestamps and tracking
            if status == "running" and task.started_at is None:
                task.started_at = time.time()
            
            elif status in ["completed", "failed"]:
                task.completed_at = time.time()
                task.result = result
                
                # Move from running to completed
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
                
                self.completed_tasks[task_id] = task
                
                # Schedule next task
                await self._schedule_pending_tasks()
            
            logger.debug(f"Updated task {task_id} status: {old_status} -> {status}")
            return True
    
    async def _schedule_pending_tasks(self) -> None:
        """
        Schedule pending tasks using advanced scheduling algorithms.
        
        Features:
        - Multi-factor priority calculation
        - Deadline-aware scheduling
        - Fair scheduling with starvation prevention
        - Task dependency management
        - Adaptive scheduling based on system load
        """
        # Check if we can schedule more tasks
        if not self.pending_tasks or len(self.running_tasks) >= self.max_concurrent_tasks:
            return
            
        # Update system load information
        await self._update_system_load()
        
        # Create a copy of pending tasks for policy application
        pending_copy = self.pending_tasks.copy()
        
        # Apply scheduling policies
        for policy in self.policies.values():
            pending_copy = policy.apply(pending_copy, self.system_load)
        
        # Rebuild priority queue with policy-adjusted tasks
        self.pending_tasks = []
        for task in pending_copy:
            heapq.heappush(self.pending_tasks, task)
        
        # Schedule tasks
        scheduled_count = 0
        while len(self.running_tasks) < self.max_concurrent_tasks and self.pending_tasks:
            # Get highest priority task
            task = heapq.heappop(self.pending_tasks)
            
            # Check if dependencies are satisfied
            if self.dependency_tracking_enabled and not task.are_dependencies_satisfied():
                # Put task back in queue and continue
                heapq.heappush(self.pending_tasks, task)
                continue
            
            # Schedule task
            task.status = "scheduled"
            task.scheduled_at = time.time()
            self.running_tasks[task.id] = task
            scheduled_count += 1
            
            # Update statistics
            self.statistics["tasks_scheduled"] += 1
            
            logger.debug(f"Scheduled task {task.id} with priority {task.priority.value}, effective priority {task.get_effective_priority():.2f}")
        
        if scheduled_count > 0:
            logger.info(f"Scheduled {scheduled_count} tasks")
    
    async def _update_system_load(self) -> None:
        """Update system load information for adaptive scheduling."""
        # Calculate system load based on running tasks
        cpu_load = sum(task.requirements.compute for task in self.running_tasks.values())
        memory_load = sum(task.requirements.memory for task in self.running_tasks.values())
        
        # Update system load
        self.system_load = {
            "cpu": min(1.0, cpu_load),
            "memory": min(1.0, memory_load),
            "io": self.system_load.get("io", 0.0),  # Maintain previous value
            "network": self.system_load.get("network", 0.0)  # Maintain previous value
        }
        
        # Update load history
        self.load_history.append(self.system_load.copy())
        if len(self.load_history) > self.max_load_history:
            self.load_history = self.load_history[-self.max_load_history:]
    
    async def _find_tasks_to_preempt(self, high_priority_task: Task) -> List[Task]:
        """
        Find tasks to preempt for a high priority task.
        
        Args:
            high_priority_task: The high priority task
            
        Returns:
            List of tasks to preempt
        """
        # Calculate resources needed
        resources_needed = {
            "compute": high_priority_task.requirements.compute,
            "memory": high_priority_task.requirements.memory,
            "attention": high_priority_task.requirements.attention
        }
        
        # Sort running tasks by priority (lowest first)
        sorted_tasks = sorted(
            self.running_tasks.values(),
            key=lambda t: t.get_effective_priority()
        )
        
        # Find tasks to preempt
        tasks_to_preempt = []
        resources_freed = {
            "compute": 0.0,
            "memory": 0.0,
            "attention": 0.0
        }
        
        for task in sorted_tasks:
            # Skip tasks with higher or equal priority
            if task.get_effective_priority() >= high_priority_task.get_effective_priority():
                continue
            
            # Add task to preemption list
            tasks_to_preempt.append(task)
            
            # Update freed resources
            resources_freed["compute"] += task.requirements.compute
            resources_freed["memory"] += task.requirements.memory
            resources_freed["attention"] += task.requirements.attention
            
            # Check if we have enough resources
            if all(resources_freed[r] >= resources_needed[r] for r in resources_needed):
                break
        
        # Check if we found enough resources
        if not all(resources_freed[r] >= resources_needed[r] for r in resources_needed):
            return []  # Not enough resources
        
        return tasks_to_preempt
    
    async def _check_timeouts(self) -> None:
        """Check for timed out tasks and handle them."""
        current_time = time.time()
        timed_out_tasks = []
        
        # Find timed out tasks
        for task_id, task in self.running_tasks.items():
            if task.started_at and current_time - task.started_at > self.task_timeout:
                timed_out_tasks.append(task_id)
        
        # Handle timed out tasks
        for task_id in timed_out_tasks:
            await self.update_task_status(task_id, "failed", {"error": "Task timed out"})
            logger.warning(f"Task {task_id} timed out after {self.task_timeout} seconds")
    
    async def add_task_dependency(self, source_id: str, target_id: str, dependency_type: str = "completion") -> bool:
        """
        Add a dependency between tasks.
        
        Args:
            source_id: The ID of the source task (dependent)
            target_id: The ID of the target task (dependency)
            dependency_type: The type of dependency
            
        Returns:
            True if the dependency was added, False otherwise
        """
        async with self.lock:
            # Check if tasks exist
            if source_id not in self.tasks:
                logger.warning(f"Source task {source_id} not found")
                return False
                
            if target_id not in self.tasks:
                logger.warning(f"Target task {target_id} not found")
                return False
            
            # Get tasks
            source_task = self.tasks[source_id]
            target_task = self.tasks[target_id]
            
            # Add dependency
            source_task.add_dependency(target_id, dependency_type)
            
            # Add to dependency tracking
            if target_id not in self.dependencies:
                self.dependencies[target_id] = []
            
            dependency = TaskDependency(source_id, target_id, dependency_type)
            self.dependencies[target_id].append(dependency)
            
            # Add to target's dependents list
            target_task.dependents.append(source_id)
            
            logger.debug(f"Added dependency: {source_id} depends on {target_id} ({dependency_type})")
            return True
    
    async def satisfy_dependencies(self, task_id: str) -> int:
        """
        Satisfy all dependencies on a task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            Number of dependencies satisfied
        """
        async with self.lock:
            if task_id not in self.dependencies:
                return 0
            
            # Get dependencies
            dependencies = self.dependencies[task_id]
            
            # Mark as satisfied
            for dependency in dependencies:
                dependency.satisfy()
                
                # Update source task's dependency
                if dependency.source_id in self.tasks:
                    source_task = self.tasks[dependency.source_id]
                    for dep in source_task.dependencies:
                        if dep.target_id == task_id:
                            dep.satisfied = True
                            dep.satisfied_at = time.time()
            
            # Count satisfied dependencies
            satisfied_count = sum(1 for dep in dependencies if dep.satisfied)
            
            logger.debug(f"Satisfied {satisfied_count} dependencies on task {task_id}")
            return satisfied_count
    
    async def get_task_dependencies(self, task_id: str) -> Dict[str, Any]:
        """
        Get dependency information for a task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            Dictionary with dependency information
        """
        async with self.lock:
            if task_id not in self.tasks:
                return {"error": "Task not found"}
            
            task = self.tasks[task_id]
            
            # Get dependencies (tasks this task depends on)
            dependencies = [
                {
                    "target_id": dep.target_id,
                    "type": dep.dependency_type,
                    "satisfied": dep.satisfied,
                    "satisfied_at": dep.satisfied_at
                }
                for dep in task.dependencies
            ]
            
            # Get dependents (tasks that depend on this task)
            dependents = task.dependents
            
            return {
                "task_id": task_id,
                "dependencies": dependencies,
                "dependents": dependents,
                "all_dependencies_satisfied": task.are_dependencies_satisfied()
            }
    
    async def get_scheduler_statistics(self) -> Dict[str, Any]:
        """
        Get scheduler statistics.
        
        Returns:
            Dictionary with scheduler statistics
        """
        async with self.lock:
            # Update average times
            total_waiting_time = 0
            waiting_count = 0
            
            for task in self.tasks.values():
                if task.scheduled_at:
                    waiting_time = task.scheduled_at - task.created_at
                    total_waiting_time += waiting_time
                    waiting_count += 1
            
            total_execution_time = 0
            execution_count = 0
            
            for task in self.completed_tasks.values():
                if task.completed_at and task.started_at:
                    execution_time = task.completed_at - task.started_at
                    total_execution_time += execution_time
                    execution_count += 1
            
            # Update statistics
            if waiting_count > 0:
                self.statistics["avg_waiting_time"] = total_waiting_time / waiting_count
            
            if execution_count > 0:
                self.statistics["avg_execution_time"] = total_execution_time / execution_count
            
            # Add current state information
            current_state = {
                "pending_tasks": len(self.pending_tasks),
                "running_tasks": len(self.running_tasks),
                "completed_tasks": len(self.completed_tasks),
                "system_load": self.system_load
            }
            
            return {**self.statistics, **current_state}