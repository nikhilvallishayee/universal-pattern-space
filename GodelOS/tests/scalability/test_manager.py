"""
Unit tests for the Scalability Manager.

This module contains tests for the ScalabilityManager and ScalabilityConfig classes.
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.type_system.types import Type
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.inference_engine.base_prover import BaseProver
from godelOS.inference_engine.proof_object import ProofObject

from godelOS.scalability.manager import ScalabilityManager, ScalabilityConfig, StorageBackendType
from godelOS.scalability.persistent_kb import PersistentKBBackend, FileBasedKBBackend, SQLiteKBBackend, KBRouter
from godelOS.scalability.query_optimizer import QueryOptimizer
from godelOS.scalability.rule_compiler import RuleCompiler
from godelOS.scalability.parallel_inference import ParallelInferenceManager, TaskPriority
from godelOS.scalability.caching import CachingMemoizationLayer, EvictionPolicy


class TestScalabilityConfig(unittest.TestCase):
    """Test cases for the ScalabilityConfig class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a scalability configuration
        self.config = ScalabilityConfig()
    
    def test_initialization(self):
        """Test initialization of a scalability configuration."""
        # Check if the configuration is initialized with default values
        self.assertEqual(self.config.storage_backend_type, StorageBackendType.FILE_BASED)
        self.assertTrue(os.path.join(os.getcwd(), "data", "kb_storage") in self.config.storage_dir)
        self.assertTrue(os.path.join(os.getcwd(), "data", "kb.db") in self.config.db_path)
        self.assertTrue(self.config.auto_persist)
        self.assertTrue(self.config.enable_query_optimization)
        self.assertTrue(self.config.enable_rule_compilation)
        self.assertEqual(self.config.max_inference_workers, 4)
        self.assertEqual(self.config.inference_strategy, "priority")
        self.assertEqual(self.config.max_cache_size, 10000)
        self.assertEqual(self.config.cache_eviction_policy, EvictionPolicy.LRU)
        self.assertEqual(self.config.cache_ttl, 3600)
    
    def test_str_representation(self):
        """Test string representation of a scalability configuration."""
        # Check if the string representation includes all configuration options
        str_repr = str(self.config)
        self.assertIn("storage_backend_type", str_repr)
        self.assertIn("storage_dir", str_repr)
        self.assertIn("db_path", str_repr)
        self.assertIn("auto_persist", str_repr)
        self.assertIn("enable_query_optimization", str_repr)
        self.assertIn("enable_rule_compilation", str_repr)
        self.assertIn("max_inference_workers", str_repr)
        self.assertIn("inference_strategy", str_repr)
        self.assertIn("max_cache_size", str_repr)
        self.assertIn("cache_eviction_policy", str_repr)
        self.assertIn("cache_ttl", str_repr)


class TestScalabilityManager(unittest.TestCase):
    """Test cases for the ScalabilityManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for the test
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create a mock prover
        self.prover = MagicMock(spec=BaseProver)
        
        # Set up the prover to return a mock proof object
        self.proof_object = MagicMock(spec=ProofObject)
        self.proof_object.is_proven = True
        self.prover.prove.return_value = self.proof_object
        
        # Create a configuration
        self.config = ScalabilityConfig()
        self.config.storage_dir = os.path.join(self.temp_dir, "kb_storage")
        self.config.db_path = os.path.join(self.temp_dir, "kb.db")
        
        # Create a scalability manager
        self.manager = ScalabilityManager(self.type_system, self.prover, self.config)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create a statement
        self.person = ConstantNode("Person", self.entity_type, "Person")
        self.john = ConstantNode("John", self.entity_type, "John")
        self.is_a = ConstantNode("is_a", self.entity_type, "is_a")
        self.statement = ApplicationNode(self.is_a, [self.john, self.person], self.entity_type)
        
        # Create a query
        self.x = VariableNode("?x", "x", self.entity_type)
        self.query = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Shut down the scalability manager
        self.manager.shutdown()
        
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test initialization of a scalability manager."""
        # Check if the manager is initialized correctly
        self.assertEqual(self.manager.type_system, self.type_system)
        self.assertEqual(self.manager.prover, self.prover)
        self.assertEqual(self.manager.config, self.config)
        
        # Check if the components are initialized
        self.assertIsInstance(self.manager.caching_layer, CachingMemoizationLayer)
        self.assertIsInstance(self.manager.kb_router, KBRouter)
        self.assertIsInstance(self.manager.query_optimizer, QueryOptimizer)
        self.assertIsInstance(self.manager.rule_compiler, RuleCompiler)
        self.assertIsInstance(self.manager.parallel_inference_manager, ParallelInferenceManager)
    
    def test_add_statement(self):
        """Test adding a statement."""
        # Mock the KB router
        self.manager.kb_router = MagicMock(spec=KBRouter)
        self.manager.kb_router.add_statement.return_value = True
        
        # Add a statement
        result = self.manager.add_statement(self.statement, "TEST")
        
        # Check if the statement was added
        self.assertTrue(result)
        self.manager.kb_router.add_statement.assert_called_once_with(self.statement, "TEST", None)
    
    def test_retract_statement(self):
        """Test retracting a statement."""
        # Mock the KB router
        self.manager.kb_router = MagicMock(spec=KBRouter)
        self.manager.kb_router.retract_statement.return_value = True
        
        # Retract a statement
        result = self.manager.retract_statement(self.statement, "TEST")
        
        # Check if the statement was retracted
        self.assertTrue(result)
        self.manager.kb_router.retract_statement.assert_called_once_with(self.statement, "TEST")
    
    def test_query_statements_match_pattern(self):
        """Test querying statements matching a pattern."""
        # Mock the query optimizer and KB router
        self.manager.query_optimizer = MagicMock(spec=QueryOptimizer)
        self.manager.kb_router = MagicMock(spec=KBRouter)
        
        mock_plan = MagicMock()
        self.manager.query_optimizer.optimize_query.return_value = mock_plan
        self.manager.kb_router.query_statements_match_pattern.return_value = ["result1", "result2"]
        
        # Query statements
        results = self.manager.query_statements_match_pattern(self.query, ["TEST"], [self.x])
        
        # Check if the query was executed
        self.assertEqual(results, ["result1", "result2"])
        self.manager.query_optimizer.optimize_query.assert_called_once_with(self.query, ["TEST"], [self.x])
        self.manager.kb_router.query_statements_match_pattern.assert_called_once_with(self.query, ["TEST"], [self.x])
    
    def test_statement_exists(self):
        """Test checking if a statement exists."""
        # Mock the KB router
        self.manager.kb_router = MagicMock(spec=KBRouter)
        self.manager.kb_router.statement_exists.return_value = True
        
        # Check if a statement exists
        result = self.manager.statement_exists(self.statement, ["TEST"])
        
        # Check if the statement exists
        self.assertTrue(result)
        self.manager.kb_router.statement_exists.assert_called_once_with(self.statement, ["TEST"])
    
    def test_create_context(self):
        """Test creating a context."""
        # Mock the KB router
        self.manager.kb_router = MagicMock(spec=KBRouter)
        
        # Create a context
        self.manager.create_context("TEST", None, "test")
        
        # Check if the context was created
        self.manager.kb_router.create_context.assert_called_once_with("TEST", None, "test", None)
    
    def test_delete_context(self):
        """Test deleting a context."""
        # Mock the KB router
        self.manager.kb_router = MagicMock(spec=KBRouter)
        
        # Delete a context
        self.manager.delete_context("TEST")
        
        # Check if the context was deleted
        self.manager.kb_router.delete_context.assert_called_once_with("TEST")
    
    def test_list_contexts(self):
        """Test listing contexts."""
        # Mock the KB router
        self.manager.kb_router = MagicMock(spec=KBRouter)
        self.manager.kb_router.list_contexts.return_value = ["TEST1", "TEST2"]
        
        # List contexts
        contexts = self.manager.list_contexts()
        
        # Check if the contexts are listed
        self.assertEqual(contexts, ["TEST1", "TEST2"])
        self.manager.kb_router.list_contexts.assert_called_once()
    
    def test_compile_rule(self):
        """Test compiling a rule."""
        # Mock the rule compiler
        self.manager.rule_compiler = MagicMock(spec=RuleCompiler)
        self.manager.rule_compiler.compile_rule.return_value = "rule1"
        
        # Compile a rule
        rule_id = self.manager.compile_rule(self.statement)
        
        # Check if the rule was compiled
        self.assertEqual(rule_id, "rule1")
        self.manager.rule_compiler.compile_rule.assert_called_once_with(self.statement, None)
    
    def test_execute_rule(self):
        """Test executing a rule."""
        # Mock the rule compiler
        self.manager.rule_compiler = MagicMock(spec=RuleCompiler)
        self.manager.rule_compiler.execute_rule.return_value = ["result1", "result2"]
        
        # Execute a rule
        results = self.manager.execute_rule("rule1", ["TEST"])
        
        # Check if the rule was executed
        self.assertEqual(results, ["result1", "result2"])
        self.manager.rule_compiler.execute_rule.assert_called_once_with("rule1", ["TEST"])
    
    def test_submit_inference_task(self):
        """Test submitting an inference task."""
        # Mock the parallel inference manager
        self.manager.parallel_inference_manager = MagicMock(spec=ParallelInferenceManager)
        self.manager.parallel_inference_manager.submit_task.return_value = "task1"
        
        # Submit a task
        task_id = self.manager.submit_inference_task(self.query, ["TEST"], TaskPriority.HIGH)
        
        # Check if the task was submitted
        self.assertEqual(task_id, "task1")
        self.manager.parallel_inference_manager.submit_task.assert_called_once_with(
            self.query, ["TEST"], TaskPriority.HIGH, None)
    
    def test_process_inference_tasks(self):
        """Test processing inference tasks."""
        # Mock the parallel inference manager
        self.manager.parallel_inference_manager = MagicMock(spec=ParallelInferenceManager)
        
        # Process tasks
        self.manager.process_inference_tasks(5)
        
        # Check if the tasks were processed
        self.manager.parallel_inference_manager.process_tasks.assert_called_once_with(5)
    
    def test_get_inference_task_result(self):
        """Test getting the result of an inference task."""
        # Mock the parallel inference manager
        self.manager.parallel_inference_manager = MagicMock(spec=ParallelInferenceManager)
        mock_result = MagicMock()
        mock_result.is_success.return_value = True
        mock_result.result = self.proof_object
        self.manager.parallel_inference_manager.get_task_result.return_value = mock_result
        
        # Get the task result
        result = self.manager.get_inference_task_result("task1", True)
        
        # Check if the result is correct
        self.assertEqual(result, self.proof_object)
        self.manager.parallel_inference_manager.get_task_result.assert_called_once_with("task1", True)
    
    def test_batch_prove(self):
        """Test proving multiple queries in parallel."""
        # Mock the parallel inference manager
        self.manager.parallel_inference_manager = MagicMock(spec=ParallelInferenceManager)
        self.manager.parallel_inference_manager.batch_prove.return_value = [self.proof_object, self.proof_object]
        
        # Batch prove
        results = self.manager.batch_prove([self.query, self.query], ["TEST"])
        
        # Check if the results are correct
        self.assertEqual(results, [self.proof_object, self.proof_object])
        self.manager.parallel_inference_manager.batch_prove.assert_called_once_with([self.query, self.query], ["TEST"])
    
    def test_clear_caches(self):
        """Test clearing all caches."""
        # Mock the caching layer
        self.manager.caching_layer = MagicMock(spec=CachingMemoizationLayer)
        
        # Clear caches
        self.manager.clear_caches()
        
        # Check if the caches were cleared
        self.manager.caching_layer.clear.assert_called_once()
    
    def test_get_cache_statistics(self):
        """Test getting statistics about the cache."""
        # Mock the caching layer
        self.manager.caching_layer = MagicMock(spec=CachingMemoizationLayer)
        self.manager.caching_layer.size.return_value = 5
        
        # Get cache statistics
        stats = self.manager.get_cache_statistics()
        
        # Check if the statistics are correct
        self.assertEqual(stats["size"], 5)
        self.assertEqual(stats["max_size"], self.config.max_cache_size)
        self.assertEqual(stats["eviction_policy"], self.config.cache_eviction_policy)
        self.assertEqual(stats["ttl"], self.config.cache_ttl)
    
    def test_get_inference_statistics(self):
        """Test getting statistics about the parallel inference manager."""
        # Mock the parallel inference manager
        self.manager.parallel_inference_manager = MagicMock(spec=ParallelInferenceManager)
        mock_stats = {"total_tasks": 10, "completed_tasks": 5}
        self.manager.parallel_inference_manager.get_statistics.return_value = mock_stats
        
        # Get inference statistics
        stats = self.manager.get_inference_statistics()
        
        # Check if the statistics are correct
        self.assertEqual(stats, mock_stats)
        self.manager.parallel_inference_manager.get_statistics.assert_called_once()
    
    def test_shutdown(self):
        """Test shutting down the scalability components."""
        # Mock the components
        self.manager.parallel_inference_manager = MagicMock(spec=ParallelInferenceManager)
        self.manager.kb_backends = {
            "default": MagicMock(spec=PersistentKBBackend)
        }
        
        # Shutdown
        self.manager.shutdown()
        
        # Check if the components were shut down
        self.manager.parallel_inference_manager.shutdown.assert_called_once()
        self.manager.kb_backends["default"].persist.assert_called_once()


if __name__ == "__main__":
    unittest.main()