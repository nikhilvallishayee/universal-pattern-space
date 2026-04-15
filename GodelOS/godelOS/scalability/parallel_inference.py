"""
Parallel Inference Manager (Module 6.4).

This module implements the ParallelInferenceManager class, which manages parallel
execution of inference tasks, manages a thread pool for inference tasks, implements
work distribution strategies, handles synchronization and result aggregation, and
provides an API that integrates with the Inference Engine.
"""

import threading
import queue
import time
import logging
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union, Generic, TypeVar
from enum import Enum

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode
from godelOS.inference_engine.base_prover import BaseProver
from godelOS.inference_engine.proof_object import ProofObject


T = TypeVar('T')  # Generic type for task result


class TaskPriority(Enum):
    """Enumeration of task priorities."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class InferenceTask:
    """
    Class representing an inference task.
    
    An inference task encapsulates a query to be processed by the inference engine.
    """
    
    def __init__(self, task_id: str, query: AST_Node, context_ids: List[str], 
                 priority: TaskPriority = TaskPriority.MEDIUM,
                 timeout: Optional[float] = None):
        """
        Initialize the inference task.
        
        Args:
            task_id: The ID of the task
            query: The query to process
            context_ids: The contexts to query
            priority: The priority of the task
            timeout: Optional timeout in seconds
        """
        self.task_id = task_id
        self.query = query
        self.context_ids = context_ids
        self.priority = priority
        self.timeout = timeout
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.result: Optional[ProofObject] = None
        self.error: Optional[Exception] = None
    
    def __lt__(self, other: 'InferenceTask') -> bool:
        """
        Compare tasks by priority.
        
        Args:
            other: The other task to compare with
            
        Returns:
            True if this task has higher priority than the other task
        """
        if not isinstance(other, InferenceTask):
            return NotImplemented
        
        # Higher priority tasks come first
        return self.priority.value > other.priority.value
    
    def __str__(self) -> str:
        """
        Get a string representation of the task.
        
        Returns:
            A string representation of the task
        """
        return f"InferenceTask(id={self.task_id}, priority={self.priority}, status={self.get_status()})"
    
    def get_status(self) -> str:
        """
        Get the status of the task.
        
        Returns:
            The status of the task
        """
        if self.completed_at:
            return "completed"
        if self.started_at:
            return "running"
        return "pending"
    
    def get_duration(self) -> Optional[float]:
        """
        Get the duration of the task execution.
        
        Returns:
            The duration in seconds, or None if the task is not completed
        """
        if not self.started_at:
            return None
        
        if self.completed_at:
            return self.completed_at - self.started_at
        
        return time.time() - self.started_at
    
    def is_expired(self) -> bool:
        """
        Check if the task has expired.
        
        Returns:
            True if the task has expired, False otherwise
        """
        if not self.timeout:
            return False
        
        if self.started_at:
            # Check if the task has been running for too long
            current_time = time.time()
            return (current_time - self.started_at) > self.timeout
        
        return False


class TaskResult(Generic[T]):
    """
    Class representing the result of a task.
    
    This class encapsulates the result of a task, including any errors
    that occurred during execution.
    """
    
    def __init__(self, task_id: str, result: Optional[T] = None, error: Optional[Exception] = None):
        """
        Initialize the task result.
        
        Args:
            task_id: The ID of the task
            result: The result of the task
            error: Optional error that occurred during execution
        """
        self.task_id = task_id
        self.result = result
        self.error = error
        self.completed_at = time.time()
    
    def is_success(self) -> bool:
        """
        Check if the task completed successfully.
        
        Returns:
            True if the task completed successfully, False otherwise
        """
        return self.error is None
    
    def __str__(self) -> str:
        """
        Get a string representation of the task result.
        
        Returns:
            A string representation of the task result
        """
        status = "success" if self.is_success() else f"error: {self.error}"
        return f"TaskResult(id={self.task_id}, status={status})"


class WorkDistributionStrategy:
    """
    Base class for work distribution strategies.
    
    A work distribution strategy defines how tasks are distributed among
    available workers.
    """
    
    def distribute(self, tasks: List[InferenceTask], num_workers: int) -> List[List[InferenceTask]]:
        """
        Distribute tasks among workers.
        
        Args:
            tasks: The tasks to distribute
            num_workers: The number of workers
            
        Returns:
            A list of task lists, one for each worker
        """
        raise NotImplementedError("Subclasses must implement distribute method")


class RoundRobinStrategy(WorkDistributionStrategy):
    """
    Round-robin work distribution strategy.
    
    This strategy distributes tasks evenly among workers in a round-robin fashion.
    """
    
    def distribute(self, tasks: List[InferenceTask], num_workers: int) -> List[List[InferenceTask]]:
        """
        Distribute tasks among workers in a round-robin fashion.
        
        Args:
            tasks: The tasks to distribute
            num_workers: The number of workers
            
        Returns:
            A list of task lists, one for each worker
        """
        if num_workers <= 0:
            raise ValueError("Number of workers must be positive")
        
        # Initialize empty task lists for each worker
        worker_tasks: List[List[InferenceTask]] = [[] for _ in range(num_workers)]
        
        # Distribute tasks in round-robin fashion
        for i, task in enumerate(tasks):
            worker_idx = i % num_workers
            worker_tasks[worker_idx].append(task)
        
        return worker_tasks


class PriorityBasedStrategy(WorkDistributionStrategy):
    """
    Priority-based work distribution strategy.
    
    This strategy distributes tasks based on their priority, with higher
    priority tasks assigned to workers first.
    """
    
    def distribute(self, tasks: List[InferenceTask], num_workers: int) -> List[List[InferenceTask]]:
        """
        Distribute tasks among workers based on priority.
        
        Args:
            tasks: The tasks to distribute
            num_workers: The number of workers
            
        Returns:
            A list of task lists, one for each worker
        """
        if num_workers <= 0:
            raise ValueError("Number of workers must be positive")
        
        # Sort tasks by priority (higher priority first)
        sorted_tasks = sorted(tasks, reverse=True)
        
        # Initialize empty task lists for each worker
        worker_tasks: List[List[InferenceTask]] = [[] for _ in range(num_workers)]
        
        # Distribute tasks to balance the load
        for task in sorted_tasks:
            # Find the worker with the fewest tasks
            min_tasks_worker = min(range(num_workers), key=lambda i: len(worker_tasks[i]))
            worker_tasks[min_tasks_worker].append(task)
        
        return worker_tasks


class WorkStealingStrategy(WorkDistributionStrategy):
    """
    Work-stealing distribution strategy.
    
    This strategy initially distributes tasks evenly, but allows workers
    to steal tasks from other workers when they run out of work.
    """
    
    def distribute(self, tasks: List[InferenceTask], num_workers: int) -> List[List[InferenceTask]]:
        """
        Distribute tasks among workers with work stealing.
        
        Args:
            tasks: The tasks to distribute
            num_workers: The number of workers
            
        Returns:
            A list of task lists, one for each worker
        """
        if num_workers <= 0:
            raise ValueError("Number of workers must be positive")
        
        # Sort tasks by priority (higher priority first)
        sorted_tasks = sorted(tasks, reverse=True)
        
        # Initialize empty task lists for each worker
        worker_tasks: List[List[InferenceTask]] = [[] for _ in range(num_workers)]
        
        # Distribute tasks in chunks to minimize stealing overhead
        chunk_size = max(1, len(sorted_tasks) // (num_workers * 2))
        chunks = [sorted_tasks[i:i+chunk_size] for i in range(0, len(sorted_tasks), chunk_size)]
        
        # Distribute chunks in round-robin fashion
        for i, chunk in enumerate(chunks):
            worker_idx = i % num_workers
            worker_tasks[worker_idx].extend(chunk)
        
        return worker_tasks


class ParallelInferenceManager:
    """
    Class for managing parallel execution of inference tasks.
    
    The ParallelInferenceManager manages a thread pool for inference tasks,
    implements work distribution strategies, handles synchronization and
    result aggregation, and provides an API that integrates with the
    Inference Engine.
    """
    
    def __init__(self, prover: BaseProver, max_workers: int = 4, 
                 strategy_type: str = "priority"):
        """
        Initialize the parallel inference manager.
        
        Args:
            prover: The prover to use for inference
            max_workers: The maximum number of worker threads
            strategy_type: The type of work distribution strategy to use
        """
        self.prover = prover
        self.max_workers = max_workers
        
        # Create thread pool
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Set work distribution strategy
        self.strategies = {
            "round_robin": RoundRobinStrategy(),
            "priority": PriorityBasedStrategy(),
            "work_stealing": WorkStealingStrategy()
        }
        
        if strategy_type not in self.strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        self.strategy = self.strategies[strategy_type]
        
        # Task management
        self.task_queue: queue.PriorityQueue[InferenceTask] = queue.PriorityQueue()
        self.active_tasks: Dict[str, Future] = {}
        self.completed_tasks: Dict[str, TaskResult[ProofObject]] = {}
        self.task_lock = threading.RLock()
        
        # Statistics
        self.total_tasks_submitted = 0
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def submit_task(self, query: AST_Node, context_ids: List[str], 
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   timeout: Optional[float] = None) -> str:
        """
        Submit an inference task.
        
        Args:
            query: The query to process
            context_ids: The contexts to query
            priority: The priority of the task
            timeout: Optional timeout in seconds
            
        Returns:
            The ID of the submitted task
        """
        with self.task_lock:
            # Generate a task ID
            task_id = f"task_{self.total_tasks_submitted}"
            
            # Create a task
            task = InferenceTask(task_id, query, context_ids, priority, timeout)
            
            # Add the task to the queue
            self.task_queue.put(task)
            
            # Update statistics
            self.total_tasks_submitted += 1
            
            self.logger.info(f"Submitted task {task_id} with priority {priority}")
            
            return task_id
    
    def process_tasks(self, batch_size: int = 10) -> None:
        """
        Process tasks in the queue.
        
        Args:
            batch_size: The maximum number of tasks to process in a batch
        """
        with self.task_lock:
            # Get tasks from the queue
            tasks = []
            while not self.task_queue.empty() and len(tasks) < batch_size:
                try:
                    task = self.task_queue.get_nowait()
                    tasks.append(task)
                except queue.Empty:
                    break
            
            if not tasks:
                return
            
            # Distribute tasks among workers
            worker_tasks = self.strategy.distribute(tasks, self.max_workers)
            
            # Submit tasks to the thread pool
            for worker_idx, worker_task_list in enumerate(worker_tasks):
                for task in worker_task_list:
                    self.logger.debug(f"Submitting task {task.task_id} to worker {worker_idx}")
                    future = self.executor.submit(self._execute_task, task)
                    self.active_tasks[task.task_id] = future
    
    def _execute_task(self, task: InferenceTask) -> TaskResult[ProofObject]:
        """
        Execute an inference task.
        
        Args:
            task: The task to execute
            
        Returns:
            The result of the task
        """
        # Mark the task as started
        task.started_at = time.time()
        
        try:
            # Execute the query
            proof_object = self.prover.prove(task.query, task.context_ids)
            
            # Mark the task as completed
            task.completed_at = time.time()
            task.result = proof_object
            
            # Create a task result
            result = TaskResult(task.task_id, proof_object)
            
            # Update statistics
            with self.task_lock:
                self.completed_tasks[task.task_id] = result
                self.total_tasks_completed += 1
                del self.active_tasks[task.task_id]
            
            self.logger.info(f"Task {task.task_id} completed successfully in {task.get_duration():.2f} seconds")
            
            return result
        
        except Exception as e:
            # Mark the task as completed with error
            task.completed_at = time.time()
            task.error = e
            
            # Create a task result with error
            result = TaskResult(task.task_id, None, e)
            
            # Update statistics
            with self.task_lock:
                self.completed_tasks[task.task_id] = result
                self.total_tasks_failed += 1
                del self.active_tasks[task.task_id]
            
            self.logger.error(f"Task {task.task_id} failed: {e}")
            
            return result
    
    def get_task_result(self, task_id: str, wait: bool = False) -> Optional[TaskResult[ProofObject]]:
        """
        Get the result of a task.
        
        Args:
            task_id: The ID of the task
            wait: Whether to wait for the task to complete
            
        Returns:
            The result of the task, or None if the task is not found or not completed
        """
        with self.task_lock:
            # Check if the task is completed
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            
            # Check if the task is active
            if task_id in self.active_tasks:
                if wait:
                    # Release the lock while waiting
                    self.task_lock.release()
                    try:
                        # Wait for the task to complete
                        result = self.active_tasks[task_id].result()
                        return result
                    finally:
                        # Reacquire the lock
                        self.task_lock.acquire()
                else:
                    return None
            
            # Task not found
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            True if the task was cancelled, False otherwise
        """
        with self.task_lock:
            # Check if the task is active
            if task_id in self.active_tasks:
                # Cancel the task
                cancelled = self.active_tasks[task_id].cancel()
                if cancelled:
                    del self.active_tasks[task_id]
                    self.logger.info(f"Task {task_id} cancelled")
                return cancelled
            
            # Task not found or already completed
            return False
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Get the status of a task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            The status of the task, or None if the task is not found
        """
        with self.task_lock:
            # Check if the task is completed
            if task_id in self.completed_tasks:
                result = self.completed_tasks[task_id]
                if result.is_success():
                    return "completed"
                else:
                    return "failed"
            
            # Check if the task is active
            if task_id in self.active_tasks:
                future = self.active_tasks[task_id]
                if future.done():
                    if future.cancelled():
                        return "cancelled"
                    elif future.exception():
                        return "failed"
                    else:
                        return "completed"
                else:
                    return "running"
            
            # Check if the task is in the queue
            for task in list(self.task_queue.queue):
                if task.task_id == task_id:
                    return "pending"
            
            # Task not found
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the parallel inference manager.
        
        Returns:
            A dictionary of statistics
        """
        with self.task_lock:
            return {
                "total_tasks_submitted": self.total_tasks_submitted,
                "total_tasks_completed": self.total_tasks_completed,
                "total_tasks_failed": self.total_tasks_failed,
                "active_tasks": len(self.active_tasks),
                "queued_tasks": self.task_queue.qsize(),
                "completed_tasks": len(self.completed_tasks)
            }
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shut down the parallel inference manager.
        
        Args:
            wait: Whether to wait for active tasks to complete
        """
        self.executor.shutdown(wait=wait)
        self.logger.info("Parallel inference manager shut down")
    
    def batch_prove(self, queries: List[AST_Node], context_ids: List[str]) -> List[ProofObject]:
        """
        Prove multiple queries in parallel.
        
        Args:
            queries: The queries to prove
            context_ids: The contexts to query
            
        Returns:
            A list of proof objects, one for each query
        """
        # Submit tasks
        task_ids = []
        for query in queries:
            task_id = self.submit_task(query, context_ids)
            task_ids.append(task_id)
        
        # Process tasks
        self.process_tasks(batch_size=len(queries))
        
        # Wait for all tasks to complete
        results = []
        for task_id in task_ids:
            result = self.get_task_result(task_id, wait=True)
            if result and result.is_success() and result.result:
                results.append(result.result)
            else:
                # If a task failed, add a failed proof object
                results.append(ProofObject(query=queries[task_ids.index(task_id)], is_proven=False))
        
        return results