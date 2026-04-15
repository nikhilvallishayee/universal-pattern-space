"""
Scalability Manager (Central coordinator for Module 6).

This module implements the ScalabilityManager class, which coordinates the different
scalability components, provides a unified API for the rest of GödelOS to interact with,
manages configuration of the scalability components, and handles initialization and
shutdown of components.
"""

import os
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Type
from enum import Enum

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.inference_engine.base_prover import BaseProver
from godelOS.inference_engine.proof_object import ProofObject

from godelOS.scalability.persistent_kb import PersistentKBBackend, FileBasedKBBackend, SQLiteKBBackend, KBRouter
from godelOS.scalability.query_optimizer import QueryOptimizer, QueryPlan
from godelOS.scalability.rule_compiler import RuleCompiler
from godelOS.scalability.parallel_inference import ParallelInferenceManager, TaskPriority
from godelOS.scalability.caching import CachingSystem, EvictionPolicy


class StorageBackendType(Enum):
    """Enumeration of storage backend types."""
    IN_MEMORY = 1
    FILE_BASED = 2
    SQLITE = 3


class ScalabilityConfig:
    """
    Configuration for the scalability components.
    
    This class encapsulates the configuration options for the various
    scalability components.
    """
    
    def __init__(self):
        """Initialize the scalability configuration with default values."""
        # Persistent KB configuration
        self.storage_backend_type = StorageBackendType.FILE_BASED
        self.storage_dir = os.path.join(os.getcwd(), "data", "kb_storage")
        self.db_path = os.path.join(os.getcwd(), "data", "kb.db")
        self.auto_persist = True
        
        # Query optimizer configuration
        self.enable_query_optimization = True
        
        # Rule compiler configuration
        self.enable_rule_compilation = True
        
        # Parallel inference configuration
        self.max_inference_workers = 4
        self.inference_strategy = "priority"
        
        # Caching configuration
        self.max_cache_size = 10000
        self.cache_eviction_policy = EvictionPolicy.LRU
        self.cache_ttl = 3600  # 1 hour
    
    def __str__(self) -> str:
        """
        Get a string representation of the configuration.
        
        Returns:
            A string representation of the configuration
        """
        return (
            f"ScalabilityConfig("
            f"storage_backend_type={self.storage_backend_type}, "
            f"storage_dir={self.storage_dir}, "
            f"db_path={self.db_path}, "
            f"auto_persist={self.auto_persist}, "
            f"enable_query_optimization={self.enable_query_optimization}, "
            f"enable_rule_compilation={self.enable_rule_compilation}, "
            f"max_inference_workers={self.max_inference_workers}, "
            f"inference_strategy={self.inference_strategy}, "
            f"max_cache_size={self.max_cache_size}, "
            f"cache_eviction_policy={self.cache_eviction_policy}, "
            f"cache_ttl={self.cache_ttl}"
            f")"
        )


class ScalabilityManager:
    """
    Central coordinator for the scalability components.
    
    The ScalabilityManager coordinates the different scalability components,
    provides a unified API for the rest of GödelOS to interact with, manages
    configuration of the scalability components, and handles initialization
    and shutdown of components.
    """
    
    def __init__(self, type_system: TypeSystemManager, prover: BaseProver, config: Optional[ScalabilityConfig] = None):
        """
        Initialize the scalability manager.
        
        Args:
            type_system: The type system manager
            prover: The base prover to use for inference
            config: Optional configuration for the scalability components
        """
        self.type_system = type_system
        self.prover = prover
        self.config = config or ScalabilityConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize the scalability components."""
        # Create directories if they don't exist
        os.makedirs(self.config.storage_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.config.db_path), exist_ok=True)
        
        # Initialize caching layer
        self.caching_layer = CachingSystem(
            max_size=self.config.max_cache_size,
            eviction_policy=self.config.cache_eviction_policy,
            default_ttl=self.config.cache_ttl
        )
        
        # Initialize knowledge store backends
        self.kb_backends = self._initialize_kb_backends()
        
        # Initialize KB router
        self.kb_router = KBRouter(self.kb_backends["default"])
        
        # Register backends with the router
        for backend_id, backend in self.kb_backends.items():
            if backend_id != "default":
                self.kb_router.register_backend(backend_id, backend)
        
        # Initialize query optimizer
        self.query_optimizer = QueryOptimizer(self.kb_router, self.type_system)
        
        # Initialize rule compiler
        self.rule_compiler = RuleCompiler(self.kb_router)
        
        # Initialize parallel inference manager
        self.parallel_inference_manager = ParallelInferenceManager(
            self.prover,
            max_workers=self.config.max_inference_workers,
            strategy_type=self.config.inference_strategy
        )
        
        self.logger.info("Scalability components initialized")
    
    def _initialize_kb_backends(self) -> Dict[str, PersistentKBBackend]:
        """
        Initialize the knowledge store backends.
        
        Returns:
            A dictionary of backend ID to backend instance
        """
        from godelOS.core_kr.unification_engine.engine import UnificationEngine
        
        # Create unification engine
        unification_engine = UnificationEngine(self.type_system)
        
        backends = {}
        
        # Create the default backend based on the configuration
        if self.config.storage_backend_type == StorageBackendType.FILE_BASED:
            backends["default"] = FileBasedKBBackend(
                unification_engine,
                self.config.storage_dir,
                self.config.auto_persist
            )
        elif self.config.storage_backend_type == StorageBackendType.SQLITE:
            backends["default"] = SQLiteKBBackend(
                unification_engine,
                self.config.db_path
            )
        else:
            # For IN_MEMORY, we use the FileBasedKBBackend with auto_persist=False
            backends["default"] = FileBasedKBBackend(
                unification_engine,
                self.config.storage_dir,
                False
            )
        
        return backends
    
    def add_statement(self, statement_ast: AST_Node, context_id: str = "TRUTHS", 
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a statement to the knowledge store.
        
        Args:
            statement_ast: The statement to add
            context_id: The context to add the statement to
            metadata: Optional metadata for the statement
            
        Returns:
            True if the statement was added successfully, False otherwise
        """
        # Check if the result is cached
        cache_key = f"add_statement:{statement_ast}:{context_id}"
        cached_result = self.caching_layer.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Add the statement
        result = self.kb_router.add_statement(statement_ast, context_id, metadata)
        
        # Cache the result
        self.caching_layer.put(cache_key, result)
        
        # Invalidate related caches
        self.caching_layer.invalidate()
        
        return result
    
    def retract_statement(self, statement_pattern_ast: AST_Node, 
                         context_id: str = "TRUTHS") -> bool:
        """
        Retract a statement from the knowledge store.
        
        Args:
            statement_pattern_ast: The statement pattern to retract
            context_id: The context to retract the statement from
            
        Returns:
            True if the statement was retracted successfully, False otherwise
        """
        # Retract the statement
        result = self.kb_router.retract_statement(statement_pattern_ast, context_id)
        
        # Invalidate caches
        self.caching_layer.invalidate()
        
        return result
    
    def query_statements_match_pattern(self, query_pattern_ast: AST_Node,
                                      context_ids: List[str] = ["TRUTHS"],
                                      variables_to_bind: Optional[List[VariableNode]] = None) -> List[Dict[VariableNode, AST_Node]]:
        """
        Query statements matching a pattern.
        
        Args:
            query_pattern_ast: The query pattern
            context_ids: The contexts to query
            variables_to_bind: Optional list of variables to bind
            
        Returns:
            A list of variable bindings
        """
        # Debug logging
        self.logger.debug(f"Query pattern: {query_pattern_ast}")
        self.logger.debug(f"Context IDs: {context_ids}")
        self.logger.debug(f"Variables to bind: {variables_to_bind}")
        
        # Check if the result is cached
        cache_key = f"query:{query_pattern_ast}:{context_ids}:{variables_to_bind}"
        cached_result = self.caching_layer.get(cache_key)
        if cached_result is not None:
            self.logger.debug(f"Cache hit! Returning cached result: {cached_result}")
            return cached_result
        
        # Optimize the query if enabled
        if self.config.enable_query_optimization:
            self.logger.debug("Query optimization enabled, optimizing query...")
            plan = self.query_optimizer.optimize_query(query_pattern_ast, context_ids, variables_to_bind)
            self.logger.debug(f"Optimized query plan: {plan}")
            # Use direct query instead of optimized query for now
            # results = self.query_optimizer.execute_optimized_query(plan)
            results = self.kb_router.query_statements_match_pattern(query_pattern_ast, context_ids, variables_to_bind)
        else:
            self.logger.debug("Query optimization disabled, executing query directly...")
            # Execute the query directly
            results = self.kb_router.query_statements_match_pattern(query_pattern_ast, context_ids, variables_to_bind)
        
        self.logger.debug(f"Query results: {results}")
        
        # Cache the result
        self.caching_layer.put(cache_key, results)
        
        return results
    
    def statement_exists(self, statement_ast: AST_Node, 
                        context_ids: List[str] = ["TRUTHS"]) -> bool:
        """
        Check if a statement exists in the knowledge store.
        
        Args:
            statement_ast: The statement to check
            context_ids: The contexts to check
            
        Returns:
            True if the statement exists, False otherwise
        """
        # Check if the result is cached
        cache_key = f"exists:{statement_ast}:{context_ids}"
        cached_result = self.caching_layer.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Check if the statement exists
        result = self.kb_router.statement_exists(statement_ast, context_ids)
        
        # Cache the result
        self.caching_layer.put(cache_key, result)
        
        return result
    
    def create_context(self, context_id: str, parent_context_id: Optional[str] = None, 
                      context_type: str = "generic", backend_id: Optional[str] = None) -> None:
        """
        Create a new context.
        
        Args:
            context_id: The ID of the context
            parent_context_id: Optional parent context ID
            context_type: The type of the context
            backend_id: Optional backend ID to use for the context
        """
        # Create the context
        self.kb_router.create_context(context_id, parent_context_id, context_type, backend_id)
        
        # Invalidate caches
        self.caching_layer.invalidate()
    
    def delete_context(self, context_id: str) -> None:
        """
        Delete a context.
        
        Args:
            context_id: The ID of the context to delete
        """
        # Delete the context
        self.kb_router.delete_context(context_id)
        
        # Invalidate caches
        self.caching_layer.invalidate()
    
    def list_contexts(self) -> List[str]:
        """
        List all contexts.
        
        Returns:
            A list of context IDs
        """
        # Check if the result is cached
        cache_key = "list_contexts"
        cached_result = self.caching_layer.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # List contexts
        result = self.kb_router.list_contexts()
        
        # Cache the result
        self.caching_layer.put(cache_key, result)
        
        return result
    
    def compile_rule(self, rule_ast: AST_Node, rule_id: Optional[str] = None) -> str:
        """
        Compile a rule.
        
        Args:
            rule_ast: The AST of the rule
            rule_id: Optional ID for the rule
            
        Returns:
            The ID of the compiled rule
        """
        if not self.config.enable_rule_compilation:
            raise ValueError("Rule compilation is disabled")
        
        return self.rule_compiler.compile_rule(rule_ast, rule_id)
    
    def execute_rule(self, rule_id: str, context_ids: List[str]) -> List[Dict[VariableNode, AST_Node]]:
        """
        Execute a compiled rule.
        
        Args:
            rule_id: The ID of the rule
            context_ids: The contexts to query
            
        Returns:
            The results of executing the rule
        """
        if not self.config.enable_rule_compilation:
            raise ValueError("Rule compilation is disabled")
        
        # Check if the result is cached
        cache_key = f"execute_rule:{rule_id}:{context_ids}"
        cached_result = self.caching_layer.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute the rule
        result = self.rule_compiler.execute_rule(rule_id, context_ids)
        
        # Cache the result
        self.caching_layer.put(cache_key, result)
        
        return result
    
    def submit_inference_task(self, query: AST_Node, context_ids: List[str], 
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
        return self.parallel_inference_manager.submit_task(query, context_ids, priority, timeout)
    
    def process_inference_tasks(self, batch_size: int = 10) -> None:
        """
        Process inference tasks in the queue.
        
        Args:
            batch_size: The maximum number of tasks to process in a batch
        """
        self.parallel_inference_manager.process_tasks(batch_size)
    
    def get_inference_task_result(self, task_id: str, wait: bool = False) -> Optional[Any]:
        """
        Get the result of an inference task.
        
        Args:
            task_id: The ID of the task
            wait: Whether to wait for the task to complete
            
        Returns:
            The result of the task, or None if the task is not found or not completed
        """
        result = self.parallel_inference_manager.get_task_result(task_id, wait)
        if result and result.is_success():
            return result.result
        return None
    
    def batch_prove(self, queries: List[AST_Node], context_ids: List[str]) -> List[ProofObject]:
        """
        Prove multiple queries in parallel.
        
        Args:
            queries: The queries to prove
            context_ids: The contexts to query
            
        Returns:
            A list of proof objects, one for each query
        """
        return self.parallel_inference_manager.batch_prove(queries, context_ids)
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self.caching_layer.clear()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            A dictionary of cache statistics
        """
        return {
            "size": self.caching_layer.size(),
            "max_size": self.config.max_cache_size,
            "eviction_policy": self.config.cache_eviction_policy,
            "ttl": self.config.cache_ttl
        }
    
    def get_inference_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the parallel inference manager.
        
        Returns:
            A dictionary of inference statistics
        """
        return self.parallel_inference_manager.get_statistics()
    
    def shutdown(self) -> None:
        """Shut down the scalability components."""
        # Shut down the parallel inference manager
        self.parallel_inference_manager.shutdown()
        
        # Persist any pending changes
        for backend_id, backend in self.kb_backends.items():
            if hasattr(backend, "persist"):
                backend.persist()
        
        self.logger.info("Scalability components shut down")