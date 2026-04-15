"""
Knowledge Store Interface implementation.

This module implements the KnowledgeStoreInterface class, which provides a unified API
for storing, retrieving, updating, and deleting knowledge from the underlying
knowledge base backend(s).
"""

from typing import Dict, List, Optional, Set, Tuple, Any, DefaultDict
import os
import uuid
import threading
from collections import defaultdict
from abc import ABC, abstractmethod

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode, ConnectiveNode
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.unification_engine.engine import UnificationEngine


class QueryResult:
    """
    Class representing the result of a query to the knowledge store.
    
    This class encapsulates the success status of a query and the variable bindings
    that satisfy the query.
    """
    
    def __init__(self, success: bool, bindings: List[Dict[VariableNode, AST_Node]] = None):
        """
        Initialize a query result.
        
        Args:
            success: Whether the query was successful
            bindings: List of variable bindings that satisfy the query
        """
        self.success = success
        self.bindings = bindings or []
    
    def __bool__(self) -> bool:
        """Return success status when used in boolean context."""
        return self.success
    
    def __len__(self) -> int:
        """Return the number of binding sets."""
        return len(self.bindings)
    
    def __iter__(self):
        """Iterate over binding sets."""
        return iter(self.bindings)
    
    def __getitem__(self, index: int) -> Dict[VariableNode, AST_Node]:
        """Get a specific binding set."""
        return self.bindings[index]


class KnowledgeStoreBackend(ABC):
    """
    Abstract base class for knowledge store backends.
    
    This class defines the interface that all knowledge store backends must implement.
    Concrete backends (in-memory, graph DB, triple store) should inherit from this class.
    """
    
    @abstractmethod
    def add_statement(self, statement_ast: AST_Node, context_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a statement to the knowledge store.
        
        Args:
            statement_ast: The statement to add
            context_id: The context to add the statement to
            metadata: Optional metadata for the statement
            
        Returns:
            True if the statement was added successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def retract_statement(self, statement_pattern_ast: AST_Node, context_id: str) -> bool:
        """
        Retract a statement from the knowledge store.
        
        Args:
            statement_pattern_ast: The statement pattern to retract
            context_id: The context to retract the statement from
            
        Returns:
            True if the statement was retracted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def query_statements_match_pattern(self, query_pattern_ast: AST_Node, 
                                      context_ids: List[str],
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
        pass
    
    @abstractmethod
    def statement_exists(self, statement_ast: AST_Node, context_ids: List[str]) -> bool:
        """
        Check if a statement exists in the knowledge store.
        
        Args:
            statement_ast: The statement to check
            context_ids: The contexts to check
            
        Returns:
            True if the statement exists, False otherwise
        """
        pass
    
    @abstractmethod
    def create_context(self, context_id: str, parent_context_id: Optional[str], context_type: str) -> None:
        """
        Create a new context.
        
        Args:
            context_id: The ID of the context
            parent_context_id: Optional parent context ID
            context_type: The type of the context
        """
        pass
    
    @abstractmethod
    def delete_context(self, context_id: str) -> None:
        """
        Delete a context.
        
        Args:
            context_id: The ID of the context to delete
        """
        pass
    
    @abstractmethod
    def list_contexts(self) -> List[str]:
        """
        List all contexts.
        
        Returns:
            A list of context IDs
        """
        pass
    
    def get_context_info(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a context.
        
        Args:
            context_id: The ID of the context
            
        Returns:
            A dict with keys ``parent`` and ``type``, or ``None``
            if the context does not exist.
        """
        return None  # default; concrete backends should override


class InMemoryKnowledgeStore(KnowledgeStoreBackend):
    """
    In-memory implementation of the knowledge store backend.
    
    This class implements the KnowledgeStoreBackend interface using in-memory
    data structures (dictionaries and sets).
    """
    
    def __init__(self, unification_engine: UnificationEngine):
        """
        Initialize the in-memory knowledge store.
        
        Args:
            unification_engine: The unification engine to use for pattern matching
        """
        self.unification_engine = unification_engine
        self._lock = threading.RLock()  # Use RLock for thread safety
        
        # Main storage for statements by context
        self._statements: Dict[str, Set[AST_Node]] = {}
        
        # Context information
        self._contexts: Dict[str, Dict[str, Any]] = {}
        
        # Indexes for optimizing queries
        self._predicate_index: DefaultDict[str, DefaultDict[str, Set[AST_Node]]] = defaultdict(lambda: defaultdict(set))
        self._constant_index: DefaultDict[str, DefaultDict[str, Set[AST_Node]]] = defaultdict(lambda: defaultdict(set))
        self._type_index: DefaultDict[str, DefaultDict[str, Set[AST_Node]]] = defaultdict(lambda: defaultdict(set))
    
    def add_statement(self, statement_ast: AST_Node, context_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a statement to the knowledge store.
        
        Args:
            statement_ast: The statement to add
            context_id: The context to add the statement to
            metadata: Optional metadata for the statement
            
        Returns:
            True if the statement was added successfully, False otherwise
        """
        with self._lock:
            if context_id not in self._contexts:
                raise ValueError(f"Context {context_id} does not exist")
            
            if context_id not in self._statements:
                self._statements[context_id] = set()
            
            # Add metadata to the statement if provided
            if metadata:
                statement_ast = statement_ast.with_updated_metadata(metadata)
            
            # Check if the statement already exists in the context
            if self.statement_exists(statement_ast, [context_id]):
                return False
            
            # Add the statement to the main storage
            self._statements[context_id].add(statement_ast)
            
            # Update indexes
            self._index_statement(statement_ast, context_id)
            
            return True
    
    def retract_statement(self, statement_pattern_ast: AST_Node, context_id: str) -> bool:
        """
        Retract a statement from the knowledge store.
        
        Args:
            statement_pattern_ast: The statement pattern to retract
            context_id: The context to retract the statement from
            
        Returns:
            True if the statement was retracted successfully, False otherwise
        """
        with self._lock:
            if context_id not in self._contexts:
                raise ValueError(f"Context {context_id} does not exist")
            
            if context_id not in self._statements:
                return False
            
            # Find statements matching the pattern
            matching_statements = []
            for statement in self._statements[context_id]:
                bindings, errors = self.unification_engine.unify(statement_pattern_ast, statement)
                if bindings is not None:
                    matching_statements.append(statement)
            
            # Retract matching statements
            if not matching_statements:
                return False
            
            for statement in matching_statements:
                self._statements[context_id].remove(statement)
                self._remove_from_indexes(statement, context_id)
            
            return True
    
    def query_statements_match_pattern(self, query_pattern_ast: AST_Node, 
                                      context_ids: List[str],
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
        with self._lock:
            results = []
            
            for context_id in context_ids:
                if context_id not in self._contexts:
                    raise ValueError(f"Context {context_id} does not exist")
                
                if context_id not in self._statements:
                    continue
                
                # Use indexes to optimize the query if possible
                candidate_statements = self._get_candidate_statements(query_pattern_ast, context_id)
                
                for statement in candidate_statements:
                    bindings, errors = self.unification_engine.unify(query_pattern_ast, statement)
                    if bindings is not None:
                        # Filter bindings to only include the variables to bind
                        if variables_to_bind:
                            filtered_bindings = {}
                            for var in variables_to_bind:
                                if var.var_id in bindings:
                                    filtered_bindings[var] = bindings[var.var_id]
                            results.append(filtered_bindings)
                        else:
                            # Convert var_id -> AST_Node to VariableNode -> AST_Node
                            # Build a map from var_id to the original VariableNode in the query pattern
                            query_vars = {}
                            self._collect_variables(query_pattern_ast, query_vars)
                            var_bindings = {}
                            for var_id, ast_node in bindings.items():
                                if var_id in query_vars:
                                    var_bindings[query_vars[var_id]] = ast_node
                                else:
                                    var_type = self.unification_engine.type_system.get_type("Entity") or ast_node.type
                                    var = VariableNode(f"?var{var_id}", var_id, var_type)
                                    var_bindings[var] = ast_node
                            results.append(var_bindings)
            
            return results
    
    def statement_exists(self, statement_ast: AST_Node, context_ids: List[str]) -> bool:
        """
        Check if a statement exists in the knowledge store.
        
        Args:
            statement_ast: The statement to check
            context_ids: The contexts to check
            
        Returns:
            True if the statement exists, False otherwise
        """
        with self._lock:
            for context_id in context_ids:
                if context_id not in self._contexts:
                    raise ValueError(f"Context {context_id} does not exist")
                
                if context_id not in self._statements:
                    continue
                
                # Use indexes to optimize the check if possible
                candidate_statements = self._get_candidate_statements(statement_ast, context_id)
                
                for statement in candidate_statements:
                    bindings, errors = self.unification_engine.unify(statement_ast, statement)
                    if bindings is not None:
                        return True
            
            return False
    
    def create_context(self, context_id: str, parent_context_id: Optional[str], context_type: str) -> None:
        """
        Create a new context.
        
        Args:
            context_id: The ID of the context
            parent_context_id: Optional parent context ID
            context_type: The type of the context
        """
        with self._lock:
            if context_id in self._contexts:
                raise ValueError(f"Context {context_id} already exists")
            
            if parent_context_id and parent_context_id not in self._contexts:
                raise ValueError(f"Parent context {parent_context_id} does not exist")
            
            self._contexts[context_id] = {
                "parent": parent_context_id,
                "type": context_type,
                "created_at": uuid.uuid4()  # Use a timestamp in a real implementation
            }
    
    def delete_context(self, context_id: str) -> None:
        """
        Delete a context.
        
        Args:
            context_id: The ID of the context to delete
        """
        with self._lock:
            if context_id not in self._contexts:
                raise ValueError(f"Context {context_id} does not exist")
            
            # Check if the context has child contexts
            for other_context_id, context_info in self._contexts.items():
                if context_info.get("parent") == context_id:
                    raise ValueError(f"Cannot delete context {context_id} because it has child contexts")
            
            # Delete the context
            del self._contexts[context_id]
            
            # Delete the statements in the context
            if context_id in self._statements:
                # Remove statements from indexes
                for statement in self._statements[context_id]:
                    self._remove_from_indexes(statement, context_id)
                
                # Delete the statements
                del self._statements[context_id]
    
    def list_contexts(self) -> List[str]:
        """
        List all contexts.
        
        Returns:
            A list of context IDs
        """
        with self._lock:
            return list(self._contexts.keys())
    
    def get_context_info(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Return metadata for *context_id*, or ``None`` if missing."""
        with self._lock:
            info = self._contexts.get(context_id)
            if info is None:
                return None
            return {"parent": info.get("parent"), "type": info.get("type", "generic")}
    
    def get_all_statements_in_context(self, context_id: str) -> Set[AST_Node]:
        """Return every statement stored in *context_id* without pattern matching."""
        with self._lock:
            if context_id not in self._contexts:
                raise ValueError(f"Context {context_id} does not exist")
            return set(self._statements.get(context_id, set()))
    
    def _collect_variables(self, node: AST_Node, var_map: Dict[int, VariableNode]) -> None:
        """Collect all VariableNodes from an AST, mapping var_id -> VariableNode."""
        if isinstance(node, VariableNode):
            var_map[node.var_id] = node
        elif isinstance(node, ApplicationNode):
            self._collect_variables(node.operator, var_map)
            for arg in node.arguments:
                self._collect_variables(arg, var_map)
        elif isinstance(node, ConnectiveNode):
            for operand in node.operands:
                self._collect_variables(operand, var_map)

    def _index_statement(self, statement: AST_Node, context_id: str) -> None:
        """
        Index a statement for faster queries.
        
        Args:
            statement: The statement to index
            context_id: The context of the statement
        """
        # Index by type
        self._type_index[statement.type.name][context_id].add(statement)
        
        # Index ApplicationNodes by predicate name and constants
        if isinstance(statement, ApplicationNode):
            # Index by predicate name
            if isinstance(statement.operator, ConstantNode):
                predicate_name = statement.operator.name
                self._predicate_index[predicate_name][context_id].add(statement)
            
            # Index by constants in the arguments
            for arg in statement.arguments:
                if isinstance(arg, ConstantNode):
                    constant_name = arg.name
                    self._constant_index[constant_name][context_id].add(statement)
    
    def _remove_from_indexes(self, statement: AST_Node, context_id: str) -> None:
        """
        Remove a statement from indexes.
        
        Args:
            statement: The statement to remove from indexes
            context_id: The context of the statement
        """
        # Remove from type index
        if statement.type.name in self._type_index and context_id in self._type_index[statement.type.name]:
            self._type_index[statement.type.name][context_id].discard(statement)
        
        # Remove from predicate index
        if isinstance(statement, ApplicationNode) and isinstance(statement.operator, ConstantNode):
            predicate_name = statement.operator.name
            if predicate_name in self._predicate_index and context_id in self._predicate_index[predicate_name]:
                self._predicate_index[predicate_name][context_id].discard(statement)
        
        # Remove from constant index
        if isinstance(statement, ApplicationNode):
            for arg in statement.arguments:
                if isinstance(arg, ConstantNode):
                    constant_name = arg.name
                    if constant_name in self._constant_index and context_id in self._constant_index[constant_name]:
                        self._constant_index[constant_name][context_id].discard(statement)
    
    def _get_candidate_statements(self, pattern: AST_Node, context_id: str) -> Set[AST_Node]:
        """
        Get candidate statements that might match a pattern.
        
        Uses indexes to narrow down the set of statements to check.
        
        Args:
            pattern: The pattern to match
            context_id: The context to search in
            
        Returns:
            A set of candidate statements
        """
        if context_id not in self._statements:
            return set()
        
        # If the pattern is an ApplicationNode with a constant predicate,
        # use the predicate index
        if isinstance(pattern, ApplicationNode) and isinstance(pattern.operator, ConstantNode):
            predicate_name = pattern.operator.name
            if predicate_name in self._predicate_index and context_id in self._predicate_index[predicate_name]:
                return self._predicate_index[predicate_name][context_id]
        
        # If the pattern has a specific type, use the type index
        if pattern.type.name in self._type_index and context_id in self._type_index[pattern.type.name]:
            return self._type_index[pattern.type.name][context_id]
        
        # If no indexes apply, return all statements in the context
        return self._statements[context_id]


class DynamicContextModel:
    """
    Model for dynamically determining which contexts to query based on the query pattern.
    
    This class is used to model the relationships between contexts and to determine
    which contexts should be queried for a given pattern.
    """
    
    def __init__(self, knowledge_store: 'KnowledgeStoreInterface'):
        """
        Initialize the dynamic context model.
        
        Args:
            knowledge_store: The knowledge store interface
        """
        self.knowledge_store = knowledge_store
    
    def get_relevant_contexts(self, query_pattern: AST_Node, base_contexts: List[str]) -> List[str]:
        """
        Get the relevant contexts for a query pattern.
        
        Args:
            query_pattern: The query pattern
            base_contexts: The base contexts to start from
            
        Returns:
            A list of relevant context IDs
        """
        # Start with the base contexts
        relevant_contexts = set(base_contexts)
        
        # Add child contexts of the base contexts
        for context_id in base_contexts:
            children = self._get_child_contexts(context_id)
            relevant_contexts.update(children)
        
        # Filter contexts based on the query pattern
        # This is a simplified implementation; a real implementation would use
        # more sophisticated rules to determine relevance
        
        return list(relevant_contexts)
    
    def _get_child_contexts(self, parent_context_id: str) -> List[str]:
        """
        Get the child contexts of a parent context.
        
        Args:
            parent_context_id: The parent context ID
            
        Returns:
            A list of child context IDs
        """
        children = []
        for context_id, context_info in self.knowledge_store._backend._contexts.items():
            if context_info.get("parent") == parent_context_id:
                children.append(context_id)
                # Recursively add grandchildren
                children.extend(self._get_child_contexts(context_id))
        return children


class CachingMemoizationLayer:
    """
    Caching and memoization layer for the knowledge store.
    
    This class provides caching and memoization for expensive operations
    in the knowledge store, such as queries and unification.
    """
    
    def __init__(self, max_cache_size: int = 1000):
        """
        Initialize the caching layer.
        
        Args:
            max_cache_size: The maximum number of items to cache
        """
        self.max_cache_size = max_cache_size
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if the key is not in the cache
        """
        with self._lock:
            return self._cache.get(key)
    
    def put(self, key: str, value: Any) -> None:
        """
        Put a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        with self._lock:
            # If the cache is full, remove the oldest item
            if len(self._cache) >= self.max_cache_size:
                # In a real implementation, we would use a more sophisticated
                # cache eviction policy, such as LRU
                self._cache.pop(next(iter(self._cache)))
            
            self._cache[key] = value
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate a cache entry.
        
        Args:
            key: The cache key to invalidate
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()


class KnowledgeStoreInterface:
    """
    Interface for storing, retrieving, updating, and deleting knowledge.
    
    This class abstracts away the specifics of the backend implementation
    (in-memory, graph DB, triple store) and provides a unified API for
    knowledge management.
    """
    
    # Class-level declarations so MagicMock(spec=...) sees them
    type_system: TypeSystemManager = None  # type: ignore[assignment]
    cache_manager: Optional[CachingMemoizationLayer] = None
    unification_engine: "UnificationEngine" = None  # type: ignore[assignment]
    
    def __init__(self, type_system: TypeSystemManager, 
                 cache_manager: Optional[CachingMemoizationLayer] = None,
                 backend: Optional[str] = None,
                 db_path: Optional[str] = None):
        """
        Initialize the knowledge store interface.
        
        Args:
            type_system: The type system manager
            cache_manager: Optional caching and memoization layer
            backend: Backend type (``"memory"`` or ``"chroma"``).  Defaults
                     to the ``KNOWLEDGE_STORE_BACKEND`` env-var, falling back
                     to ``"memory"``.
            db_path: Path for the persistent backend.  Only used when
                     *backend* is ``"chroma"``.  Defaults to the
                     ``KNOWLEDGE_STORE_PATH`` env-var, falling back to
                     ``"./data/chroma"``.
        """
        self.type_system = type_system
        self.cache_manager = cache_manager or CachingMemoizationLayer()
        self.unification_engine = UnificationEngine(type_system)
        
        # Resolve backend choice from explicit arg → env-var → default
        _valid_backends = {"memory", "chroma"}
        chosen_backend = (
            backend
            or os.environ.get("KNOWLEDGE_STORE_BACKEND", "memory")
        ).lower()

        if chosen_backend not in _valid_backends:
            import logging as _logging

            _logging.getLogger(__name__).warning(
                "Unknown KNOWLEDGE_STORE_BACKEND=%r; falling back to 'memory'",
                chosen_backend,
            )
            chosen_backend = "memory"

        if chosen_backend == "chroma":
            from godelOS.core_kr.knowledge_store.chroma_store import ChromaKnowledgeStore

            resolved_path = db_path or os.environ.get(
                "KNOWLEDGE_STORE_PATH", "./data/chroma"
            )
            self._backend: KnowledgeStoreBackend = ChromaKnowledgeStore(
                self.unification_engine, persist_directory=resolved_path
            )
        else:
            self._backend = InMemoryKnowledgeStore(self.unification_engine)
        
        # Initialize default contexts (only if they don't already exist,
        # which matters for a persisted ChromaDB backend across restarts).
        existing = set(self._backend.list_contexts())
        if "TRUTHS" not in existing:
            self._backend.create_context("TRUTHS", None, "truths")
        if "BELIEFS" not in existing:
            self._backend.create_context("BELIEFS", None, "beliefs")
        if "HYPOTHETICAL" not in existing:
            self._backend.create_context("HYPOTHETICAL", None, "hypothetical")
    
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
        # Invalidate any cached queries that might be affected by this addition
        if self.cache_manager:
            # In a real implementation, we would use a more sophisticated
            # cache invalidation strategy
            self.cache_manager.clear()
        
        return self._backend.add_statement(statement_ast, context_id, metadata)
    
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
        # Invalidate any cached queries that might be affected by this retraction
        if self.cache_manager:
            # In a real implementation, we would use a more sophisticated
            # cache invalidation strategy
            self.cache_manager.clear()
        
        return self._backend.retract_statement(statement_pattern_ast, context_id)
    
    def query_statements_match_pattern(self, query_pattern_ast: AST_Node, 
                                      context_ids: List[str] = ["TRUTHS"],
                                      dynamic_context_model: Optional[DynamicContextModel] = None,
                                      variables_to_bind: Optional[List[VariableNode]] = None) -> List[Dict[VariableNode, AST_Node]]:
        """
        Query statements matching a pattern.
        
        Args:
            query_pattern_ast: The query pattern
            context_ids: The contexts to query
            dynamic_context_model: Optional dynamic context model
            variables_to_bind: Optional list of variables to bind
            
        Returns:
            A list of variable bindings
        """
        # Check if the query result is cached
        cache_key = None
        if self.cache_manager:
            # Create a cache key based on the query parameters
            # In a real implementation, we would use a more sophisticated
            # cache key generation strategy
            cache_key = str(hash((str(query_pattern_ast), tuple(context_ids), 
                                  str(variables_to_bind))))
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        # If a dynamic context model is provided, use it to determine the contexts to query
        if dynamic_context_model:
            context_ids = dynamic_context_model.get_relevant_contexts(query_pattern_ast, context_ids)
        
        # Query the backend
        results = self._backend.query_statements_match_pattern(
            query_pattern_ast, context_ids, variables_to_bind)
        
        # Cache the result
        if self.cache_manager and cache_key:
            self.cache_manager.put(cache_key, results)
        
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
        cache_key = None
        if self.cache_manager:
            # Create a cache key based on the query parameters
            cache_key = str(hash((str(statement_ast), tuple(context_ids))))
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Check the backend
        result = self._backend.statement_exists(statement_ast, context_ids)
        
        # Cache the result
        if self.cache_manager and cache_key:
            self.cache_manager.put(cache_key, result)
        
        return result
    
    def create_context(self, context_id: str, parent_context_id: Optional[str] = None, 
                      context_type: str = "generic") -> None:
        """
        Create a new context.
        
        Args:
            context_id: The ID of the context
            parent_context_id: Optional parent context ID
            context_type: The type of the context
        """
        # Invalidate any cached queries that might be affected by this context creation
        if self.cache_manager:
            self.cache_manager.clear()
        
        self._backend.create_context(context_id, parent_context_id, context_type)
    
    def delete_context(self, context_id: str) -> None:
        """
        Delete a context.
        
        Args:
            context_id: The ID of the context to delete
        """
        # Invalidate any cached queries that might be affected by this context deletion
        if self.cache_manager:
            self.cache_manager.clear()
        
        self._backend.delete_context(context_id)
    
    def list_contexts(self) -> List[str]:
        """
        List all contexts.
        
        Returns:
            A list of context IDs
        """
        # Check if the result is cached
        cache_key = "list_contexts"
        if self.cache_manager:
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Get the contexts from the backend
        result = self._backend.list_contexts()
        
        # Cache the result
        if self.cache_manager:
            self.cache_manager.put(cache_key, result)
        
        return result
    
    def get_all_statements_in_context(self, context_id: str) -> Set[AST_Node]:
        """Return every statement stored in *context_id* without pattern matching."""
        return self._backend.get_all_statements_in_context(context_id)