"""
Unit tests for the Persistent Knowledge Base Backend & Router.

This module contains tests for the PersistentKBBackend, FileBasedKBBackend,
SQLiteKBBackend, and KBRouter classes.
"""

import os
import tempfile
import unittest
import shutil
from unittest.mock import MagicMock, patch

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.type_system.types import Type
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.unification_engine.engine import UnificationEngine

from godelOS.scalability.persistent_kb import (
    PersistentKBBackend,
    FileBasedKBBackend,
    SQLiteKBBackend,
    KBRouter
)


class TestFileBasedKBBackend(unittest.TestCase):
    """Test cases for the FileBasedKBBackend class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for the test
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        self.type_system.register_type("Relation", None)
        
        # Create a unification engine
        self.unification_engine = UnificationEngine(self.type_system)
        
        # Create a file-based KB backend
        self.kb = FileBasedKBBackend(self.unification_engine, self.temp_dir, auto_persist=True)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        self.relation_type = self.type_system.get_type("Relation")
        
        # Create a test context
        self.kb.create_context("TEST", None, "test")
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_create_context(self):
        """Test creating a context."""
        # Create a new context
        self.kb.create_context("TEST2", "TEST", "test")
        
        # Check if the context exists
        contexts = self.kb.list_contexts()
        self.assertIn("TEST2", contexts)
        
        # Check if the parent context is set correctly
        self.assertEqual(self.kb._contexts["TEST2"]["parent"], "TEST")
    
    def test_add_statement(self):
        """Test adding a statement."""
        # Create a statement
        person = ConstantNode("Person", self.entity_type, "Person")
        john = ConstantNode("John", self.entity_type, "John")
        is_a = ConstantNode("is_a", self.relation_type, "is_a")
        statement = ApplicationNode(is_a, [john, person], self.entity_type)
        
        # Add the statement
        result = self.kb.add_statement(statement, "TEST")
        
        # Check if the statement was added
        self.assertTrue(result)
        
        # Check if the statement exists
        exists = self.kb.statement_exists(statement, ["TEST"])
        self.assertTrue(exists)
    
    def test_retract_statement(self):
        """Test retracting a statement."""
        # Create a statement
        person = ConstantNode("Person", self.entity_type, "Person")
        john = ConstantNode("John", self.entity_type, "John")
        is_a = ConstantNode("is_a", self.relation_type, "is_a")
        statement = ApplicationNode(is_a, [john, person], self.entity_type)
        
        # Add the statement
        self.kb.add_statement(statement, "TEST")
        
        # Retract the statement
        result = self.kb.retract_statement(statement, "TEST")
        
        # Check if the statement was retracted
        self.assertTrue(result)
        
        # Check if the statement no longer exists
        exists = self.kb.statement_exists(statement, ["TEST"])
        self.assertFalse(exists)
    
    def test_query_statements_match_pattern(self):
        """Test querying statements matching a pattern."""
        # Create statements
        person = ConstantNode("Person", self.entity_type, "Person")
        john = ConstantNode("John", self.entity_type, "John")
        mary = ConstantNode("Mary", self.entity_type, "Mary")
        is_a = ConstantNode("is_a", self.relation_type, "is_a")
        
        statement1 = ApplicationNode(is_a, [john, person], self.entity_type)
        statement2 = ApplicationNode(is_a, [mary, person], self.entity_type)
        
        # Add the statements
        self.kb.add_statement(statement1, "TEST")
        self.kb.add_statement(statement2, "TEST")
        
        # Create a query pattern with a variable
        x = VariableNode("?x", "x", self.entity_type)
        query = ApplicationNode(is_a, [x, person], self.entity_type)
        
        # Query statements matching the pattern
        results = self.kb.query_statements_match_pattern(query, ["TEST"])
        
        # Check if the results are correct
        self.assertEqual(len(results), 2)
        
        # Check if the variable bindings are correct
        bindings = set()
        for result in results:
            for var, value in result.items():
                if var.var_id == "x":
                    bindings.add(value.name)
        
        self.assertEqual(bindings, {"John", "Mary"})
    
    def test_persist_and_load(self):
        """Test persisting and loading the knowledge store."""
        # Create a statement
        person = ConstantNode("Person", self.entity_type, "Person")
        john = ConstantNode("John", self.entity_type, "John")
        is_a = ConstantNode("is_a", self.relation_type, "is_a")
        statement = ApplicationNode(is_a, [john, person], self.entity_type)
        
        # Add the statement
        self.kb.add_statement(statement, "TEST")
        
        # Create a new KB backend that loads from the same directory
        kb2 = FileBasedKBBackend(self.unification_engine, self.temp_dir)
        
        # Check if the statement exists in the new KB
        exists = kb2.statement_exists(statement, ["TEST"])
        self.assertTrue(exists)
    
    def test_transactions(self):
        """Test transactions."""
        # Create a statement
        person = ConstantNode("Person", self.entity_type, "Person")
        john = ConstantNode("John", self.entity_type, "John")
        is_a = ConstantNode("is_a", self.relation_type, "is_a")
        statement = ApplicationNode(is_a, [john, person], self.entity_type)
        
        # Begin a transaction
        self.kb.begin_transaction()
        
        # Add the statement
        self.kb.add_statement(statement, "TEST")
        
        # Check if the statement exists
        exists = self.kb.statement_exists(statement, ["TEST"])
        self.assertTrue(exists)
        
        # Rollback the transaction
        self.kb.rollback_transaction()
        
        # Check if the statement no longer exists
        exists = self.kb.statement_exists(statement, ["TEST"])
        self.assertFalse(exists)
        
        # Begin another transaction
        self.kb.begin_transaction()
        
        # Add the statement again
        self.kb.add_statement(statement, "TEST")
        
        # Commit the transaction
        self.kb.commit_transaction()
        
        # Check if the statement exists
        exists = self.kb.statement_exists(statement, ["TEST"])
        self.assertTrue(exists)


class TestSQLiteKBBackend(unittest.TestCase):
    """Test cases for the SQLiteKBBackend class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for the test
        fd, self.db_path = tempfile.mkstemp()
        os.close(fd)
        
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        self.type_system.register_type("Relation", None)
        
        # Create a unification engine
        self.unification_engine = UnificationEngine(self.type_system)
        
        # Create a SQLite KB backend
        self.kb = SQLiteKBBackend(self.unification_engine, self.db_path)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        self.relation_type = self.type_system.get_type("Relation")
        
        # Create a test context
        self.kb.create_context("TEST", None, "test")
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary file
        os.unlink(self.db_path)
    
    def test_create_context(self):
        """Test creating a context."""
        # Create a new context
        self.kb.create_context("TEST2", "TEST", "test")
        
        # Check if the context exists
        contexts = self.kb.list_contexts()
        self.assertIn("TEST2", contexts)
    
    def test_add_statement(self):
        """Test adding a statement."""
        # Create a statement
        person = ConstantNode("Person", self.entity_type, "Person")
        john = ConstantNode("John", self.entity_type, "John")
        is_a = ConstantNode("is_a", self.relation_type, "is_a")
        statement = ApplicationNode(is_a, [john, person], self.entity_type)
        
        # Add the statement
        result = self.kb.add_statement(statement, "TEST")
        
        # Check if the statement was added
        self.assertTrue(result)
        
        # Check if the statement exists
        exists = self.kb.statement_exists(statement, ["TEST"])
        self.assertTrue(exists)


class TestKBRouter(unittest.TestCase):
    """Test cases for the KBRouter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock backends
        self.default_backend = MagicMock(spec=PersistentKBBackend)
        self.backend1 = MagicMock(spec=PersistentKBBackend)
        self.backend2 = MagicMock(spec=PersistentKBBackend)
        
        # Create a router
        self.router = KBRouter(self.default_backend)
        
        # Register backends
        self.router.register_backend("backend1", self.backend1)
        self.router.register_backend("backend2", self.backend2)
        
        # Map contexts to backends
        self.router.map_context_to_backend("context1", "backend1")
        self.router.map_context_to_backend("context2", "backend2")
    
    def test_get_backend_for_context(self):
        """Test getting the backend for a context."""
        # Check if the correct backend is returned for each context
        self.assertEqual(self.router.get_backend_for_context("context1"), self.backend1)
        self.assertEqual(self.router.get_backend_for_context("context2"), self.backend2)
        self.assertEqual(self.router.get_backend_for_context("unknown"), self.default_backend)
    
    def test_add_statement(self):
        """Test adding a statement."""
        # Create a mock statement
        statement = MagicMock(spec=AST_Node)
        
        # Add the statement to context1
        self.router.add_statement(statement, "context1")
        
        # Check if the statement was added to the correct backend
        self.backend1.add_statement.assert_called_once_with(statement, "context1", None)
        self.backend2.add_statement.assert_not_called()
        self.default_backend.add_statement.assert_not_called()
    
    def test_query_statements_match_pattern(self):
        """Test querying statements matching a pattern."""
        # Create a mock query pattern
        query = MagicMock(spec=AST_Node)
        
        # Set up mock returns
        self.backend1.query_statements_match_pattern.return_value = ["result1"]
        self.backend2.query_statements_match_pattern.return_value = ["result2"]
        
        # Query statements matching the pattern in both contexts
        results = self.router.query_statements_match_pattern(query, ["context1", "context2"])
        
        # Check if the query was sent to the correct backends
        self.backend1.query_statements_match_pattern.assert_called_once_with(query, ["context1"], None)
        self.backend2.query_statements_match_pattern.assert_called_once_with(query, ["context2"], None)
        self.default_backend.query_statements_match_pattern.assert_not_called()
        
        # Check if the results are combined correctly
        self.assertEqual(results, ["result1", "result2"])


if __name__ == "__main__":
    unittest.main()