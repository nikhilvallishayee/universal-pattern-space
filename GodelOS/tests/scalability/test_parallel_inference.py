"""
Unit tests for the Parallel Inference Manager.

This module contains tests for the ParallelInferenceManager, InferenceTask,
TaskResult, and various work distribution strategy classes.
"""

import unittest
import time
from unittest.mock import MagicMock, patch

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.type_system.types import Type
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.inference_engine.base_prover import BaseProver
from godelOS.inference_engine.proof_object import ProofObject

from godelOS.scalability.parallel_inference import (
    ParallelInferenceManager,
    InferenceTask,
    TaskResult,
    TaskPriority,
    WorkDistributionStrategy,
    RoundRobinStrategy,
    PriorityBasedStrategy,
    WorkStealingStrategy
)


class TestInferenceTask(unittest.TestCase):
    """Test cases for the InferenceTask class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create a query
        self.x = VariableNode("?x", "x", self.entity_type)
        self.person = ConstantNode("Person", "Person", self.entity_type)
        self.is_a = ConstantNode("is_a", "is_a", self.entity_type)
        self.query = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
        
        # Create a task
        self.task_id = "task1"
        self.context_ids = ["TEST"]
        self.priority = TaskPriority.HIGH
        self.timeout = 10.0
        self.task = InferenceTask(self.task_id, self.query, self.context_ids, self.priority, self.timeout)
    
    def test_initialization(self):
        """Test initialization of an inference task."""
        # Check if the task is initialized correctly
        self.assertEqual(self.task.task_id, self.task_id)
        self.assertEqual(self.task.query, self.query)
        self.assertEqual(self.task.context_ids, self.context_ids)
        self.assertEqual(self.task.priority, self.priority)
        self.assertEqual(self.task.timeout, self.timeout)
        self.assertIsNone(self.task.started_at)
        self.assertIsNone(self.task.completed_at)
        self.assertIsNone(self.task.result)
        self.assertIsNone(self.task.error)
    
    def test_comparison(self):
        """Test comparing tasks by priority."""
        # Create tasks with different priorities
        high_priority_task = InferenceTask("high", self.query, self.context_ids, TaskPriority.HIGH)
        medium_priority_task = InferenceTask("medium", self.query, self.context_ids, TaskPriority.MEDIUM)
        low_priority_task = InferenceTask("low", self.query, self.context_ids, TaskPriority.LOW)
        
        # Check if tasks are compared correctly
        # Higher priority tasks come first in priority queue, so HIGH < MEDIUM < LOW
        self.assertLess(high_priority_task, medium_priority_task)
        self.assertLess(medium_priority_task, low_priority_task)
        self.assertLess(high_priority_task, low_priority_task)
    
    def test_get_status(self):
        """Test getting the status of a task."""
        # Check initial status
        self.assertEqual(self.task.get_status(), "pending")
        
        # Set started_at
        self.task.started_at = time.time()
        self.assertEqual(self.task.get_status(), "running")
        
        # Set completed_at
        self.task.completed_at = time.time()
        self.assertEqual(self.task.get_status(), "completed")
    
    def test_get_duration(self):
        """Test getting the duration of a task execution."""
        # Check duration for a pending task
        self.assertIsNone(self.task.get_duration())
        
        # Set started_at
        self.task.started_at = time.time()
        self.assertIsNotNone(self.task.get_duration())
        
        # Set completed_at
        self.task.completed_at = self.task.started_at + 5.0
        self.assertEqual(self.task.get_duration(), 5.0)
    
    def test_is_expired(self):
        """Test checking if a task has expired."""
        # Check if a task with no timeout never expires
        task_no_timeout = InferenceTask("no_timeout", self.query, self.context_ids, timeout=None)
        self.assertFalse(task_no_timeout.is_expired())
        
        # Check if a pending task doesn't expire
        self.assertFalse(self.task.is_expired())
        
        # Set started_at to a time that would make the task expired
        self.task.started_at = time.time() - 20.0  # 20 seconds ago, timeout is 10 seconds
        self.assertTrue(self.task.is_expired())


class TestTaskResult(unittest.TestCase):
    """Test cases for the TaskResult class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a task result
        self.task_id = "task1"
        self.result = MagicMock(spec=ProofObject)
        self.task_result = TaskResult(self.task_id, self.result)
        
        # Create a task result with an error
        self.error = Exception("Test error")
        self.error_result = TaskResult(self.task_id, None, self.error)
    
    def test_initialization(self):
        """Test initialization of a task result."""
        # Check if the task result is initialized correctly
        self.assertEqual(self.task_result.task_id, self.task_id)
        self.assertEqual(self.task_result.result, self.result)
        self.assertIsNone(self.task_result.error)
        self.assertGreater(self.task_result.completed_at, 0)
        
        # Check if the error result is initialized correctly
        self.assertEqual(self.error_result.task_id, self.task_id)
        self.assertIsNone(self.error_result.result)
        self.assertEqual(self.error_result.error, self.error)
    
    def test_is_success(self):
        """Test checking if a task result is successful."""
        # Check if a successful result is detected correctly
        self.assertTrue(self.task_result.is_success())
        
        # Check if an error result is detected correctly
        self.assertFalse(self.error_result.is_success())
    
    def test_str_representation(self):
        """Test string representation of a task result."""
        # Check if the string representation is correct for a successful result
        self.assertIn("success", str(self.task_result))
        self.assertIn(self.task_id, str(self.task_result))
        
        # Check if the string representation is correct for an error result
        self.assertIn("error", str(self.error_result))
        self.assertIn(self.task_id, str(self.error_result))
        self.assertIn("Test error", str(self.error_result))


class TestWorkDistributionStrategies(unittest.TestCase):
    """Test cases for the work distribution strategy classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create a query
        self.x = VariableNode("?x", "x", self.entity_type)
        self.person = ConstantNode("Person", "Person", self.entity_type)
        self.is_a = ConstantNode("is_a", "is_a", self.entity_type)
        self.query = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
        
        # Create tasks with different priorities
        self.tasks = [
            InferenceTask("task1", self.query, ["TEST"], TaskPriority.HIGH),
            InferenceTask("task2", self.query, ["TEST"], TaskPriority.MEDIUM),
            InferenceTask("task3", self.query, ["TEST"], TaskPriority.LOW),
            InferenceTask("task4", self.query, ["TEST"], TaskPriority.MEDIUM),
            InferenceTask("task5", self.query, ["TEST"], TaskPriority.HIGH)
        ]
        
        # Create strategies
        self.round_robin = RoundRobinStrategy()
        self.priority_based = PriorityBasedStrategy()
        self.work_stealing = WorkStealingStrategy()
    
    def test_round_robin_strategy(self):
        """Test the round-robin work distribution strategy."""
        # Distribute tasks among 2 workers
        worker_tasks = self.round_robin.distribute(self.tasks, 2)
        
        # Check if the tasks are distributed correctly
        self.assertEqual(len(worker_tasks), 2)
        self.assertEqual(len(worker_tasks[0]), 3)  # Worker 0 gets tasks 0, 2, 4
        self.assertEqual(len(worker_tasks[1]), 2)  # Worker 1 gets tasks 1, 3
        
        # Check if the tasks are assigned to the correct workers
        self.assertEqual(worker_tasks[0][0].task_id, "task1")
        self.assertEqual(worker_tasks[0][1].task_id, "task3")
        self.assertEqual(worker_tasks[0][2].task_id, "task5")
        self.assertEqual(worker_tasks[1][0].task_id, "task2")
        self.assertEqual(worker_tasks[1][1].task_id, "task4")
    
    def test_priority_based_strategy(self):
        """Test the priority-based work distribution strategy."""
        # Distribute tasks among 2 workers
        worker_tasks = self.priority_based.distribute(self.tasks, 2)
        
        # Check if the tasks are distributed correctly
        self.assertEqual(len(worker_tasks), 2)
        
        # Check if high priority tasks are assigned first
        high_priority_tasks = [task for task in self.tasks if task.priority == TaskPriority.HIGH]
        for worker_task_list in worker_tasks:
            for high_task in high_priority_tasks:
                found = False
                for worker_task in worker_task_list:
                    if worker_task.task_id == high_task.task_id:
                        found = True
                        break
                if found:
                    break
            else:
                self.fail("High priority task not assigned to any worker")
    
    def test_work_stealing_strategy(self):
        """Test the work-stealing distribution strategy."""
        # Distribute tasks among 2 workers
        worker_tasks = self.work_stealing.distribute(self.tasks, 2)
        
        # Check if the tasks are distributed correctly
        self.assertEqual(len(worker_tasks), 2)
        
        # Check if all tasks are assigned
        assigned_tasks = []
        for worker_task_list in worker_tasks:
            assigned_tasks.extend([task.task_id for task in worker_task_list])
        
        self.assertEqual(len(assigned_tasks), len(self.tasks))
        for task in self.tasks:
            self.assertIn(task.task_id, assigned_tasks)


class TestParallelInferenceManager(unittest.TestCase):
    """Test cases for the ParallelInferenceManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock prover
        self.prover = MagicMock(spec=BaseProver)
        
        # Set up the prover to return a mock proof object
        self.proof_object = MagicMock(spec=ProofObject)
        self.proof_object.is_proven = True
        self.prover.prove.return_value = self.proof_object
        
        # Create a parallel inference manager
        self.manager = ParallelInferenceManager(self.prover, max_workers=2, strategy_type="priority")
        
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create a query
        self.x = VariableNode("?x", "x", self.entity_type)
        self.person = ConstantNode("Person", "Person", self.entity_type)
        self.is_a = ConstantNode("is_a", "is_a", self.entity_type)
        self.query = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Shut down the parallel inference manager
        self.manager.shutdown(wait=False)
    
    def test_submit_task(self):
        """Test submitting an inference task."""
        # Submit a task
        task_id = self.manager.submit_task(self.query, ["TEST"], TaskPriority.HIGH)
        
        # Check if the task is submitted correctly
        self.assertIsNotNone(task_id)
        self.assertEqual(self.manager.total_tasks_submitted, 1)
        self.assertEqual(self.manager.task_queue.qsize(), 1)
    
    def test_process_tasks(self):
        """Test processing inference tasks."""
        # Submit tasks
        task_id1 = self.manager.submit_task(self.query, ["TEST"], TaskPriority.HIGH)
        task_id2 = self.manager.submit_task(self.query, ["TEST"], TaskPriority.MEDIUM)
        
        # Process tasks
        self.manager.process_tasks()
        
        # Wait for tasks to complete
        time.sleep(0.1)
        
        # Check if the tasks are processed correctly
        self.assertEqual(self.manager.total_tasks_submitted, 2)
        self.assertEqual(self.manager.task_queue.qsize(), 0)
        self.assertEqual(len(self.manager.active_tasks), 0)
        self.assertEqual(len(self.manager.completed_tasks), 2)
        self.assertEqual(self.manager.total_tasks_completed, 2)
        
        # Check if the prover was called correctly
        self.assertEqual(self.prover.prove.call_count, 2)
        self.prover.prove.assert_any_call(self.query, ["TEST"])
    
    def test_get_task_result(self):
        """Test getting the result of an inference task."""
        # Submit a task
        task_id = self.manager.submit_task(self.query, ["TEST"])
        
        # Process tasks
        self.manager.process_tasks()
        
        # Wait for the task to complete
        time.sleep(0.1)
        
        # Get the task result
        result = self.manager.get_task_result(task_id)
        
        # Check if the result is correct
        self.assertIsNotNone(result)
        self.assertEqual(result.is_success(), True)
        self.assertEqual(result.result, self.proof_object)
    
    def test_cancel_task(self):
        """Test canceling an inference task."""
        # Submit a task
        task_id = self.manager.submit_task(self.query, ["TEST"])
        
        # Cancel the task before processing
        cancelled = self.manager.cancel_task(task_id)
        
        # Check if the task was canceled
        self.assertFalse(cancelled)  # Task is still in the queue, not active
        
        # Process tasks
        self.manager.process_tasks()
        
        # Wait for the task to complete
        time.sleep(0.1)
        
        # Try to cancel the completed task
        cancelled = self.manager.cancel_task(task_id)
        
        # Check if the task was not canceled (already completed)
        self.assertFalse(cancelled)
    
    def test_get_task_status(self):
        """Test getting the status of an inference task."""
        # Submit a task
        task_id = self.manager.submit_task(self.query, ["TEST"])
        
        # Check status before processing
        status = self.manager.get_task_status(task_id)
        self.assertEqual(status, "pending")
        
        # Process tasks
        self.manager.process_tasks()
        
        # Wait for the task to complete
        time.sleep(0.1)
        
        # Check status after completion
        status = self.manager.get_task_status(task_id)
        self.assertEqual(status, "completed")
    
    def test_get_statistics(self):
        """Test getting statistics about the parallel inference manager."""
        # Submit and process some tasks
        self.manager.submit_task(self.query, ["TEST"])
        self.manager.submit_task(self.query, ["TEST"])
        self.manager.process_tasks()
        
        # Wait for tasks to complete
        time.sleep(0.1)
        
        # Get statistics
        stats = self.manager.get_statistics()
        
        # Check if the statistics are correct
        self.assertEqual(stats["total_tasks_submitted"], 2)
        self.assertEqual(stats["total_tasks_completed"], 2)
        self.assertEqual(stats["total_tasks_failed"], 0)
        self.assertEqual(stats["active_tasks"], 0)
        self.assertEqual(stats["queued_tasks"], 0)
        self.assertEqual(stats["completed_tasks"], 2)
    
    def test_batch_prove(self):
        """Test proving multiple queries in parallel."""
        # Create queries
        queries = [self.query, self.query]
        
        # Batch prove
        results = self.manager.batch_prove(queries, ["TEST"])
        
        # Check if the results are correct
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result, self.proof_object)
        
        # Check if the prover was called correctly
        self.assertEqual(self.prover.prove.call_count, 2)
        self.prover.prove.assert_any_call(self.query, ["TEST"])


if __name__ == "__main__":
    unittest.main()