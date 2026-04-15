"""
Persistent Knowledge Base Backend & Router (Module 6.1).

This module implements persistent storage backends for the knowledge base
and a router that can direct queries to the appropriate storage backend.
"""

import os
import json
import pickle
import threading
import sqlite3
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple, Any, DefaultDict, Type
from collections import defaultdict
import uuid

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreBackend
from godelOS.core_kr.unification_engine.engine import UnificationEngine


class PersistentKBBackend(KnowledgeStoreBackend, ABC):
    """
    Abstract base class for persistent knowledge store backends.
    
    This class extends the KnowledgeStoreBackend interface with methods
    for persisting data to disk and loading it back.
    """
    
    @abstractmethod
    def persist(self) -> bool:
        """
        Persist the knowledge store to disk.
        
        Returns:
            True if the operation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def load(self) -> bool:
        """
        Load the knowledge store from disk.
        
        Returns:
            True if the operation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        pass
    
    @abstractmethod
    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        pass
class FileBasedKBBackend(PersistentKBBackend):
    """
    File-based implementation of the persistent knowledge store backend.
    
    This class implements the PersistentKBBackend interface using files
    to persist data. It uses an in-memory store for fast access and
    periodically persists changes to disk.
    """
    
    def __init__(self, unification_engine: UnificationEngine, storage_dir: str, auto_persist: bool = True):
        """
        Initialize the file-based knowledge store.
        
        Args:
            unification_engine: The unification engine to use for pattern matching
            storage_dir: The directory to store the knowledge base files
            auto_persist: Whether to automatically persist changes to disk
        """
        self.unification_engine = unification_engine
        self.storage_dir = storage_dir
        self.auto_persist = auto_persist
        
        # Create the storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        self._lock = threading.RLock()  # Use RLock for thread safety
        
        # Main storage for statements by context
        self._statements: Dict[str, Set[AST_Node]] = {}
        
        # Context information
        self._contexts: Dict[str, Dict[str, Any]] = {}
        
        # Indexes for optimizing queries
        self._predicate_index: DefaultDict[str, DefaultDict[str, Set[AST_Node]]] = defaultdict(lambda: defaultdict(set))
        self._constant_index: DefaultDict[str, DefaultDict[str, Set[AST_Node]]] = defaultdict(lambda: defaultdict(set))
        self._type_index: DefaultDict[str, DefaultDict[str, Set[AST_Node]]] = defaultdict(lambda: defaultdict(set))
        
        # Transaction state
        self._in_transaction = False
        self._transaction_backup = None
        
        # Try to load existing data
        self.load()
    
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
            
            # Persist changes to disk if auto_persist is enabled
            if self.auto_persist and not self._in_transaction:
                self.persist()
            
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
            
            # Persist changes to disk if auto_persist is enabled
            if self.auto_persist and not self._in_transaction:
                self.persist()
            
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
        print(f"FileBasedKBBackend.query_statements_match_pattern called with pattern: {query_pattern_ast}")
        print(f"Context IDs: {context_ids}")
        print(f"Variables to bind: {variables_to_bind}")
        
        with self._lock:
            results = []
            
            for context_id in context_ids:
                if context_id not in self._contexts:
                    raise ValueError(f"Context {context_id} does not exist")
                
                if context_id not in self._statements:
                    print(f"Context {context_id} has no statements")
                    continue
                
                print(f"Context {context_id} has {len(self._statements[context_id])} statements")
                
                # Use indexes to optimize the query if possible
                candidate_statements = self._get_candidate_statements(query_pattern_ast, context_id)
                print(f"Found {len(candidate_statements)} candidate statements for context {context_id}")
                
                for statement in candidate_statements:
                    print(f"Checking statement: {statement}")
                    bindings, errors = self.unification_engine.unify(query_pattern_ast, statement)
                    print(f"Unification result: bindings={bindings}, errors={errors}")
                    
                    if bindings is not None:
                        print(f"Statement matched with bindings: {bindings}")
                        # Filter bindings to only include the variables to bind
                        if variables_to_bind:
                            filtered_bindings = {}
                            for var in variables_to_bind:
                                if var.var_id in bindings:
                                    filtered_bindings[var] = bindings[var.var_id]
                                    print(f"Binding variable {var} to {bindings[var.var_id]}")
                                else:
                                    print(f"Variable {var} not found in bindings")
                            results.append(filtered_bindings)
                        else:
                            # Convert var_id -> AST_Node to VariableNode -> AST_Node
                            var_bindings = {}
                            for var_id, ast_node in bindings.items():
                                # Create a new variable node with the same var_id
                                var_type = self.unification_engine.type_system.get_type("Entity") or ast_node.type
                                var = VariableNode(f"?var{var_id}", var_id, var_type)
                                var_bindings[var] = ast_node
                                print(f"Created binding for variable {var} to {ast_node}")
                            results.append(var_bindings)
            
            print(f"Returning {len(results)} results")
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
                "created_at": str(uuid.uuid4())  # Use a timestamp in a real implementation
            }
            
            # Persist changes to disk if auto_persist is enabled
            if self.auto_persist and not self._in_transaction:
                self.persist()
    
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
            
            # Persist changes to disk if auto_persist is enabled
            if self.auto_persist and not self._in_transaction:
                self.persist()
    
    def list_contexts(self) -> List[str]:
        """
        List all contexts.
        
        Returns:
            A list of context IDs
        """
        with self._lock:
            return list(self._contexts.keys())
    
    def persist(self) -> bool:
        """
        Persist the knowledge store to disk.
        
        Returns:
            True if the operation was successful, False otherwise
        """
        with self._lock:
            try:
                # Serialize contexts to JSON
                contexts_file = os.path.join(self.storage_dir, "contexts.json")
                with open(contexts_file, "w") as f:
                    json.dump(self._contexts, f, indent=2)
                
                # Serialize statements to pickle files by context
                for context_id, statements in self._statements.items():
                    context_dir = os.path.join(self.storage_dir, "contexts", context_id)
                    os.makedirs(context_dir, exist_ok=True)
                    
                    statements_file = os.path.join(context_dir, "statements.pickle")
                    with open(statements_file, "wb") as f:
                        pickle.dump(statements, f)
                
                return True
            except Exception as e:
                print(f"Error persisting knowledge store: {e}")
                return False
    
    def load(self) -> bool:
        """
        Load the knowledge store from disk.
        
        Returns:
            True if the operation was successful, False otherwise
        """
        with self._lock:
            try:
                # Load contexts from JSON
                contexts_file = os.path.join(self.storage_dir, "contexts.json")
                if os.path.exists(contexts_file):
                    with open(contexts_file, "r") as f:
                        self._contexts = json.load(f)
                
                # Load statements from pickle files by context
                contexts_dir = os.path.join(self.storage_dir, "contexts")
                if os.path.exists(contexts_dir):
                    for context_id in os.listdir(contexts_dir):
                        context_dir = os.path.join(contexts_dir, context_id)
                        if os.path.isdir(context_dir):
                            statements_file = os.path.join(context_dir, "statements.pickle")
                            if os.path.exists(statements_file):
                                with open(statements_file, "rb") as f:
                                    self._statements[context_id] = pickle.load(f)
                                    
                                    # Rebuild indexes
                                    for statement in self._statements[context_id]:
                                        self._index_statement(statement, context_id)
                
                return True
            except Exception as e:
                print(f"Error loading knowledge store: {e}")
                return False
    
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        with self._lock:
            if self._in_transaction:
                raise ValueError("Transaction already in progress")
            
            self._in_transaction = True
            
            # Create a backup of the current state
            self._transaction_backup = {
                "statements": {context_id: statements.copy() for context_id, statements in self._statements.items()},
                "contexts": self._contexts.copy(),
                "predicate_index": {pred: {ctx: stmts.copy() for ctx, stmts in ctx_dict.items()} 
                                   for pred, ctx_dict in self._predicate_index.items()},
                "constant_index": {const: {ctx: stmts.copy() for ctx, stmts in ctx_dict.items()} 
                                  for const, ctx_dict in self._constant_index.items()},
                "type_index": {type_name: {ctx: stmts.copy() for ctx, stmts in ctx_dict.items()} 
                              for type_name, ctx_dict in self._type_index.items()}
            }
    
    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        with self._lock:
            if not self._in_transaction:
                raise ValueError("No transaction in progress")
            
            self._in_transaction = False
            self._transaction_backup = None
            
            # Persist changes to disk if auto_persist is enabled
            if self.auto_persist:
                self.persist()
    
    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        with self._lock:
            if not self._in_transaction:
                raise ValueError("No transaction in progress")
            
            # Restore the backup
            self._statements = self._transaction_backup["statements"]
            self._contexts = self._transaction_backup["contexts"]
            
            # Restore indexes
            self._predicate_index.clear()
            self._constant_index.clear()
            self._type_index.clear()
            
            for pred, ctx_dict in self._transaction_backup["predicate_index"].items():
                for ctx, stmts in ctx_dict.items():
                    self._predicate_index[pred][ctx] = stmts
            
            for const, ctx_dict in self._transaction_backup["constant_index"].items():
                for ctx, stmts in ctx_dict.items():
                    self._constant_index[const][ctx] = stmts
            
            for type_name, ctx_dict in self._transaction_backup["type_index"].items():
                for ctx, stmts in ctx_dict.items():
                    self._type_index[type_name][ctx] = stmts
            
            self._in_transaction = False
            self._transaction_backup = None
    
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
class SQLiteKBBackend(PersistentKBBackend):
    """
    SQLite-based implementation of the persistent knowledge store backend.
    
    This class implements the PersistentKBBackend interface using SQLite
    for persistent storage.
    """
    
    def __init__(self, unification_engine: UnificationEngine, db_path: str):
        """
        Initialize the SQLite-based knowledge store.
        
        Args:
            unification_engine: The unification engine to use for pattern matching
            db_path: The path to the SQLite database file
        """
        self.unification_engine = unification_engine
        self.db_path = db_path
        
        # Create the database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self._lock = threading.RLock()  # Use RLock for thread safety
        
        # In-memory cache for faster access
        self._statements_cache: Dict[str, Set[AST_Node]] = {}
        self._contexts_cache: Dict[str, Dict[str, Any]] = {}
        
        # Initialize the database
        self._init_db()
        
        # Load contexts into memory
        self._load_contexts()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create contexts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contexts (
                    context_id TEXT PRIMARY KEY,
                    parent_context_id TEXT,
                    context_type TEXT,
                    created_at TEXT
                )
            ''')
            
            # Create statements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_id TEXT,
                    statement_data BLOB,
                    FOREIGN KEY (context_id) REFERENCES contexts (context_id)
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def _load_contexts(self) -> None:
        """Load contexts from the database into memory."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT context_id, parent_context_id, context_type, created_at FROM contexts")
            rows = cursor.fetchall()
            
            for row in rows:
                context_id, parent_context_id, context_type, created_at = row
                self._contexts_cache[context_id] = {
                    "parent": parent_context_id,
                    "type": context_type,
                    "created_at": created_at
                }
            
            conn.close()
    
    def _load_statements_for_context(self, context_id: str) -> None:
        """
        Load statements for a specific context from the database into memory.
        
        Args:
            context_id: The context ID to load statements for
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT statement_data FROM statements WHERE context_id = ?", (context_id,))
            rows = cursor.fetchall()
            
            self._statements_cache[context_id] = set()
            for row in rows:
                statement = pickle.loads(row[0])
                self._statements_cache[context_id].add(statement)
            
            conn.close()
    
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
            if context_id not in self._contexts_cache:
                raise ValueError(f"Context {context_id} does not exist")
            
            # Add metadata to the statement if provided
            if metadata:
                statement_ast = statement_ast.with_updated_metadata(metadata)
            
            # Check if the statement already exists in the context
            if self.statement_exists(statement_ast, [context_id]):
                return False
            
            # Load statements for this context if not already loaded
            if context_id not in self._statements_cache:
                self._load_statements_for_context(context_id)
            
            # Add the statement to the in-memory cache
            if context_id not in self._statements_cache:
                self._statements_cache[context_id] = set()
            self._statements_cache[context_id].add(statement_ast)
            
            # Persist the statement to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO statements (context_id, statement_data) VALUES (?, ?)",
                (context_id, pickle.dumps(statement_ast))
            )
            
            conn.commit()
            conn.close()
            
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
            if context_id not in self._contexts_cache:
                raise ValueError(f"Context {context_id} does not exist")
            
            # Load statements for this context if not already loaded
            if context_id not in self._statements_cache:
                self._load_statements_for_context(context_id)
            
            if context_id not in self._statements_cache:
                return False
            
            # Find statements matching the pattern
            matching_statements = []
            for statement in self._statements_cache[context_id]:
                bindings, errors = self.unification_engine.unify(statement_pattern_ast, statement)
                if bindings is not None:
                    matching_statements.append(statement)
            
            # Retract matching statements
            if not matching_statements:
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for statement in matching_statements:
                # Remove from in-memory cache
                self._statements_cache[context_id].remove(statement)
                
                # Remove from database
                cursor.execute(
                    "DELETE FROM statements WHERE context_id = ? AND statement_data = ?",
                    (context_id, pickle.dumps(statement))
                )
            
            conn.commit()
            conn.close()
            
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
                if context_id not in self._contexts_cache:
                    raise ValueError(f"Context {context_id} does not exist")
                
                # Load statements for this context if not already loaded
                if context_id not in self._statements_cache:
                    self._load_statements_for_context(context_id)
                
                if context_id not in self._statements_cache:
                    continue
                
                for statement in self._statements_cache[context_id]:
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
                            var_bindings = {}
                            for var_id, ast_node in bindings.items():
                                # Create a new variable node with the same var_id
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
                if context_id not in self._contexts_cache:
                    raise ValueError(f"Context {context_id} does not exist")
                
                # Load statements for this context if not already loaded
                if context_id not in self._statements_cache:
                    self._load_statements_for_context(context_id)
                
                if context_id not in self._statements_cache:
                    continue
                
                for statement in self._statements_cache[context_id]:
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
            if context_id in self._contexts_cache:
                raise ValueError(f"Context {context_id} already exists")
            
            if parent_context_id and parent_context_id not in self._contexts_cache:
                raise ValueError(f"Parent context {parent_context_id} does not exist")
            
            # Add to in-memory cache
            self._contexts_cache[context_id] = {
                "parent": parent_context_id,
                "type": context_type,
                "created_at": str(uuid.uuid4())
            }
            
            # Persist to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO contexts (context_id, parent_context_id, context_type, created_at) VALUES (?, ?, ?, ?)",
                (context_id, parent_context_id, context_type, self._contexts_cache[context_id]["created_at"])
            )
            
            conn.commit()
            conn.close()
    
    def delete_context(self, context_id: str) -> None:
        """
        Delete a context.
        
        Args:
            context_id: The ID of the context to delete
        """
        with self._lock:
            if context_id not in self._contexts_cache:
                raise ValueError(f"Context {context_id} does not exist")
            
            # Check if the context has child contexts
            for other_context_id, context_info in self._contexts_cache.items():
                if context_info.get("parent") == context_id:
                    raise ValueError(f"Cannot delete context {context_id} because it has child contexts")
            
            # Delete from in-memory cache
            del self._contexts_cache[context_id]
            if context_id in self._statements_cache:
                del self._statements_cache[context_id]
            
            # Delete from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM statements WHERE context_id = ?", (context_id,))
            cursor.execute("DELETE FROM contexts WHERE context_id = ?", (context_id,))
            
            conn.commit()
            conn.close()
    
    def list_contexts(self) -> List[str]:
        """
        List all contexts.
        
        Returns:
            A list of context IDs
        """
        with self._lock:
            return list(self._contexts_cache.keys())
    
    def persist(self) -> bool:
        """
        Persist the knowledge store to disk.
        
        In SQLite backend, this is a no-op since changes are persisted immediately.
        
        Returns:
            True always
        """
        return True
    
    def load(self) -> bool:
        """
        Load the knowledge store from disk.
        
        In SQLite backend, contexts are loaded at initialization,
        and statements are loaded on demand.
        
        Returns:
            True always
        """
        return True
    
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        with self._lock:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("BEGIN TRANSACTION")
    
    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        with self._lock:
            if hasattr(self, '_conn'):
                self._conn.commit()
                self._conn.close()
                delattr(self, '_conn')
            else:
                raise ValueError("No transaction in progress")
    
    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        with self._lock:
            if hasattr(self, '_conn'):
                self._conn.rollback()
                self._conn.close()
                delattr(self, '_conn')
                
                # Clear in-memory caches and reload from database
                self._statements_cache.clear()
                self._contexts_cache.clear()
                self._load_contexts()
            else:
                raise ValueError("No transaction in progress")


class KBRouter:
    """
    Router for directing queries to the appropriate knowledge store backend.
    
    This class manages multiple knowledge store backends and routes queries
    to the appropriate backend based on context or other criteria.
    """
    
    def __init__(self, default_backend: PersistentKBBackend):
        """
        Initialize the knowledge store router.
        
        Args:
            default_backend: The default backend to use
        """
        self.default_backend = default_backend
        self.backends: Dict[str, PersistentKBBackend] = {}
        self.context_to_backend: Dict[str, str] = {}
        self._lock = threading.RLock()
    
    def register_backend(self, backend_id: str, backend: PersistentKBBackend) -> None:
        """
        Register a backend with the router.
        
        Args:
            backend_id: The ID to use for the backend
            backend: The backend to register
        """
        with self._lock:
            self.backends[backend_id] = backend
    
    def map_context_to_backend(self, context_id: str, backend_id: str) -> None:
        """
        Map a context to a specific backend.
        
        Args:
            context_id: The context ID
            backend_id: The backend ID
        """
        with self._lock:
            if backend_id not in self.backends:
                raise ValueError(f"Backend {backend_id} is not registered")
            
            self.context_to_backend[context_id] = backend_id
    
    def get_backend_for_context(self, context_id: str) -> PersistentKBBackend:
        """
        Get the backend for a specific context.
        
        Args:
            context_id: The context ID
            
        Returns:
            The backend for the context
        """
        with self._lock:
            backend_id = self.context_to_backend.get(context_id)
            if backend_id:
                return self.backends[backend_id]
            return self.default_backend
    
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
        backend = self.get_backend_for_context(context_id)
        return backend.add_statement(statement_ast, context_id, metadata)
    
    def retract_statement(self, statement_pattern_ast: AST_Node, context_id: str) -> bool:
        """
        Retract a statement from the knowledge store.
        
        Args:
            statement_pattern_ast: The statement pattern to retract
            context_id: The context to retract the statement from
            
        Returns:
            True if the statement was retracted successfully, False otherwise
        """
        backend = self.get_backend_for_context(context_id)
        return backend.retract_statement(statement_pattern_ast, context_id)
    
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
        print(f"KBRouter.query_statements_match_pattern called with pattern: {query_pattern_ast}")
        print(f"Context IDs: {context_ids}")
        print(f"Variables to bind: {variables_to_bind}")
        
        results = []
        
        # Group contexts by backend
        contexts_by_backend: Dict[PersistentKBBackend, List[str]] = {}
        for context_id in context_ids:
            backend = self.get_backend_for_context(context_id)
            print(f"Backend for context {context_id}: {backend.__class__.__name__}")
            if backend not in contexts_by_backend:
                contexts_by_backend[backend] = []
            contexts_by_backend[backend].append(context_id)
        
        # Query each backend with its contexts
        for backend, backend_contexts in contexts_by_backend.items():
            print(f"Querying backend {backend.__class__.__name__} with contexts: {backend_contexts}")
            backend_results = backend.query_statements_match_pattern(
                query_pattern_ast, backend_contexts, variables_to_bind)
            print(f"Backend {backend.__class__.__name__} returned {len(backend_results)} results")
            results.extend(backend_results)
        
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
        # Group contexts by backend
        contexts_by_backend: Dict[PersistentKBBackend, List[str]] = {}
        for context_id in context_ids:
            backend = self.get_backend_for_context(context_id)
            if backend not in contexts_by_backend:
                contexts_by_backend[backend] = []
            contexts_by_backend[backend].append(context_id)
        
        # Check each backend with its contexts
        for backend, backend_contexts in contexts_by_backend.items():
            if backend.statement_exists(statement_ast, backend_contexts):
                return True
        
        return False
    
    def create_context(self, context_id: str, parent_context_id: Optional[str], context_type: str, backend_id: Optional[str] = None) -> None:
        """
        Create a new context.
        
        Args:
            context_id: The ID of the context
            parent_context_id: Optional parent context ID
            context_type: The type of the context
            backend_id: Optional backend ID to use for the context
        """
        if backend_id:
            if backend_id not in self.backends:
                raise ValueError(f"Backend {backend_id} is not registered")
            backend = self.backends[backend_id]
            self.map_context_to_backend(context_id, backend_id)
        else:
            # If parent context exists, use the same backend
            if parent_context_id:
                backend = self.get_backend_for_context(parent_context_id)
            else:
                backend = self.default_backend
        
        backend.create_context(context_id, parent_context_id, context_type)
    
    def delete_context(self, context_id: str) -> None:
        """
        Delete a context.
        
        Args:
            context_id: The ID of the context to delete
        """
        backend = self.get_backend_for_context(context_id)
        backend.delete_context(context_id)
        
        # Remove the context-to-backend mapping
        with self._lock:
            if context_id in self.context_to_backend:
                del self.context_to_backend[context_id]
    
    def list_contexts(self) -> List[str]:
        """
        List all contexts across all backends.
        
        Returns:
            A list of context IDs
        """
        contexts = []
        
        for backend in set([self.default_backend] + list(self.backends.values())):
            contexts.extend(backend.list_contexts())
        
        return contexts
    
    def begin_transaction(self) -> None:
        """Begin a transaction on all backends."""
        for backend in set([self.default_backend] + list(self.backends.values())):
            backend.begin_transaction()
    
    def commit_transaction(self) -> None:
        """Commit the current transaction on all backends."""
        for backend in set([self.default_backend] + list(self.backends.values())):
            backend.commit_transaction()
    
    def rollback_transaction(self) -> None:
        """Rollback the current transaction on all backends."""
        for backend in set([self.default_backend] + list(self.backends.values())):
            backend.rollback_transaction()