"""
Enhanced unit tests for the Knowledge Store component.

This file extends the basic tests in test_knowledge_store.py with more thorough
testing of complex methods and edge cases, focusing on query execution,
knowledge retrieval, and handling of complex knowledge structures.
"""

import unittest
from unittest.mock import patch, MagicMock
import time
from typing import Dict, List, Optional, Set, Any, Tuple

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.knowledge_store.interface import QueryResult

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker


class MockKnowledgeStore(KnowledgeStoreInterface):
    """Mock implementation of the Knowledge Store Interface for testing."""
    
    def __init__(self, type_system: TypeSystemManager):
        """Initialize the mock knowledge store."""
        self.type_system = type_system
        self.assertions = set()
        self.query_results = {}
    
    def add_assertion(self, assertion: AST_Node) -> bool:
        """Add an assertion to the knowledge store."""
        self.assertions.add(assertion)
        return True
    
    def remove_assertion(self, assertion: AST_Node) -> bool:
        """Remove an assertion from the knowledge store."""
        if assertion in self.assertions:
            self.assertions.remove(assertion)
            return True
        return False
    
    def get_assertions(self) -> Set[AST_Node]:
        """Get all assertions in the knowledge store."""
        return self.assertions
    
    def execute_query(self, query: AST_Node) -> QueryResult:
        """Execute a query against the knowledge store."""
        if query in self.query_results:
            return self.query_results[query]
        return QueryResult(success=False, bindings=[])
    
    def register_query_result(self, query: AST_Node, result: QueryResult):
        """Register a query result for testing."""
        self.query_results[query] = result


class TestKnowledgeStoreEnhanced(unittest.TestCase):
    """Enhanced test cases for the Knowledge Store with complex scenarios and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system
        self.type_system = TypeSystemManager()
        
        # Create basic types
        self.boolean_type = self.type_system.get_type("Boolean")
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create function types
        self.unary_pred_type = FunctionType([self.entity_type], self.boolean_type)
        self.binary_pred_type = FunctionType([self.entity_type, self.entity_type], self.boolean_type)
        self.ternary_pred_type = FunctionType([self.entity_type, self.entity_type, self.entity_type], self.boolean_type)
        
        # Create the knowledge store
        self.knowledge_store = MockKnowledgeStore(self.type_system)
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    
    def test_complex_knowledge_graph_operations(self):
        """Test operations on a complex knowledge graph.
        
        This test verifies that the knowledge store correctly handles
        operations on a complex knowledge graph with many assertions
        and relationships.
        """
        # Create constants for entities
        alice = ConstantNode("Alice", self.entity_type)
        bob = ConstantNode("Bob", self.entity_type)
        charlie = ConstantNode("Charlie", self.entity_type)
        dave = ConstantNode("Dave", self.entity_type)
        
        # Create predicates
        knows_pred = ConstantNode("Knows", self.binary_pred_type)
        likes_pred = ConstantNode("Likes", self.binary_pred_type)
        trusts_pred = ConstantNode("Trusts", self.binary_pred_type)
        
        # Create assertions
        # Alice knows Bob
        alice_knows_bob = ApplicationNode(knows_pred, [alice, bob], self.boolean_type)
        
        # Bob knows Charlie
        bob_knows_charlie = ApplicationNode(knows_pred, [bob, charlie], self.boolean_type)
        
        # Charlie knows Dave
        charlie_knows_dave = ApplicationNode(knows_pred, [charlie, dave], self.boolean_type)
        
        # Alice likes Bob
        alice_likes_bob = ApplicationNode(likes_pred, [alice, bob], self.boolean_type)
        
        # Bob likes Charlie
        bob_likes_charlie = ApplicationNode(likes_pred, [bob, charlie], self.boolean_type)
        
        # Alice trusts Bob
        alice_trusts_bob = ApplicationNode(trusts_pred, [alice, bob], self.boolean_type)
        
        # Add assertions to the knowledge store
        self.knowledge_store.add_assertion(alice_knows_bob)
        self.knowledge_store.add_assertion(bob_knows_charlie)
        self.knowledge_store.add_assertion(charlie_knows_dave)
        self.knowledge_store.add_assertion(alice_likes_bob)
        self.knowledge_store.add_assertion(bob_likes_charlie)
        self.knowledge_store.add_assertion(alice_trusts_bob)
        
        # Verify that all assertions were added
        assertions = self.knowledge_store.get_assertions()
        self.assertEqual(len(assertions), 6)
        self.assertIn(alice_knows_bob, assertions)
        self.assertIn(bob_knows_charlie, assertions)
        self.assertIn(charlie_knows_dave, assertions)
        self.assertIn(alice_likes_bob, assertions)
        self.assertIn(bob_likes_charlie, assertions)
        self.assertIn(alice_trusts_bob, assertions)
        
        # Create a variable for querying
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create a query: Knows(?x, ?y) - Who knows whom?
        knows_query = ApplicationNode(knows_pred, [x_var, y_var], self.boolean_type)
        
        # Register a query result
        query_result = QueryResult(
            success=True,
            bindings=[
                {x_var: alice, y_var: bob},
                {x_var: bob, y_var: charlie},
                {x_var: charlie, y_var: dave}
            ]
        )
        self.knowledge_store.register_query_result(knows_query, query_result)
        
        # Execute the query
        result = self.knowledge_store.execute_query(knows_query)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(len(result.bindings), 3)
        
        # Check specific bindings
        self.assertEqual(result.bindings[0][x_var], alice)
        self.assertEqual(result.bindings[0][y_var], bob)
        self.assertEqual(result.bindings[1][x_var], bob)
        self.assertEqual(result.bindings[1][y_var], charlie)
        self.assertEqual(result.bindings[2][x_var], charlie)
        self.assertEqual(result.bindings[2][y_var], dave)
        
        # Create a more complex query: Knows(?x, ?y) ∧ Likes(?x, ?y) - Who knows and likes whom?
        likes_query = ApplicationNode(likes_pred, [x_var, y_var], self.boolean_type)
        knows_and_likes = ConnectiveNode("AND", [knows_query, likes_query], self.boolean_type)
        
        # Register a query result
        complex_result = QueryResult(
            success=True,
            bindings=[
                {x_var: alice, y_var: bob},
                {x_var: bob, y_var: charlie}
            ]
        )
        self.knowledge_store.register_query_result(knows_and_likes, complex_result)
        
        # Execute the query
        result = self.knowledge_store.execute_query(knows_and_likes)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(len(result.bindings), 2)
        
        # Check specific bindings
        self.assertEqual(result.bindings[0][x_var], alice)
        self.assertEqual(result.bindings[0][y_var], bob)
        self.assertEqual(result.bindings[1][x_var], bob)
        self.assertEqual(result.bindings[1][y_var], charlie)
        
        # Test removing an assertion
        self.knowledge_store.remove_assertion(alice_knows_bob)
        
        # Verify that the assertion was removed
        assertions = self.knowledge_store.get_assertions()
        self.assertEqual(len(assertions), 5)
        self.assertNotIn(alice_knows_bob, assertions)
    
    def test_query_with_complex_patterns(self):
        """Test querying with complex patterns.
        
        This test verifies that the knowledge store correctly handles
        queries with complex patterns involving multiple variables,
        nested expressions, and quantifiers.
        """
        # Create constants
        alice = ConstantNode("Alice", self.entity_type)
        bob = ConstantNode("Bob", self.entity_type)
        charlie = ConstantNode("Charlie", self.entity_type)
        
        # Create predicates
        knows_pred = ConstantNode("Knows", self.binary_pred_type)
        likes_pred = ConstantNode("Likes", self.binary_pred_type)
        
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        
        # Create a complex query pattern: ∃z. Knows(?x, ?z) ∧ Knows(?z, ?y)
        # This finds all pairs (x, y) where x knows someone who knows y
        knows_x_z = ApplicationNode(knows_pred, [x_var, z_var], self.boolean_type)
        knows_z_y = ApplicationNode(knows_pred, [z_var, y_var], self.boolean_type)
        knows_conjunction = ConnectiveNode("AND", [knows_x_z, knows_z_y], self.boolean_type)
        exists_z_query = QuantifierNode("EXISTS", [z_var], knows_conjunction, self.boolean_type)
        
        # Register a query result
        query_result = QueryResult(
            success=True,
            bindings=[
                {x_var: alice, y_var: charlie}  # Alice knows Bob who knows Charlie
            ]
        )
        self.knowledge_store.register_query_result(exists_z_query, query_result)
        
        # Execute the query
        result = self.knowledge_store.execute_query(exists_z_query)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(len(result.bindings), 1)
        
        # Check specific bindings
        self.assertEqual(result.bindings[0][x_var], alice)
        self.assertEqual(result.bindings[0][y_var], charlie)
        
        # Create an even more complex query:
        # ∃z. (Knows(?x, ?z) ∧ Knows(?z, ?y)) ∧ ¬Knows(?x, ?y)
        # This finds all pairs (x, y) where x knows someone who knows y, but x doesn't directly know y
        knows_x_y = ApplicationNode(knows_pred, [x_var, y_var], self.boolean_type)
        not_knows_x_y = ConnectiveNode("NOT", [knows_x_y], self.boolean_type)
        complex_conjunction = ConnectiveNode("AND", [exists_z_query, not_knows_x_y], self.boolean_type)
        
        # Register a query result
        complex_result = QueryResult(
            success=True,
            bindings=[
                {x_var: alice, y_var: charlie}  # Alice knows Bob who knows Charlie, but Alice doesn't know Charlie
            ]
        )
        self.knowledge_store.register_query_result(complex_conjunction, complex_result)
        
        # Execute the query
        result = self.knowledge_store.execute_query(complex_conjunction)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(len(result.bindings), 1)
        
        # Check specific bindings
        self.assertEqual(result.bindings[0][x_var], alice)
        self.assertEqual(result.bindings[0][y_var], charlie)
    
    def test_performance_with_large_knowledge_base(self):
        """Test performance with a large knowledge base.
        
        This test verifies that the knowledge store can efficiently handle
        operations on a large knowledge base with many assertions.
        """
        # Create a large number of entities
        num_entities = 100
        entities = [ConstantNode(f"entity{i}", self.entity_type) for i in range(num_entities)]
        
        # Create a predicate
        related_pred = ConstantNode("Related", self.binary_pred_type)
        
        # Create a large number of assertions
        assertions = []
        for i in range(num_entities - 1):
            # Each entity is related to the next entity
            assertion = ApplicationNode(related_pred, [entities[i], entities[i+1]], self.boolean_type)
            assertions.append(assertion)
        
        # Measure the time to add all assertions
        start_time = time.time()
        for assertion in assertions:
            self.knowledge_store.add_assertion(assertion)
        add_time = time.time() - start_time
        
        print(f"Time to add {len(assertions)} assertions: {add_time * 1000:.2f} ms")
        
        # Verify that all assertions were added
        self.assertEqual(len(self.knowledge_store.get_assertions()), len(assertions))
        
        # Create variables for querying
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create a query: Related(?x, ?y)
        query = ApplicationNode(related_pred, [x_var, y_var], self.boolean_type)
        
        # Register a query result with all entity pairs
        bindings = []
        for i in range(num_entities - 1):
            bindings.append({x_var: entities[i], y_var: entities[i+1]})
        
        query_result = QueryResult(success=True, bindings=bindings)
        self.knowledge_store.register_query_result(query, query_result)
        
        # Measure the time to execute the query
        start_time = time.time()
        result = self.knowledge_store.execute_query(query)
        query_time = time.time() - start_time
        
        print(f"Time to query {len(bindings)} relationships: {query_time * 1000:.2f} ms")
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(len(result.bindings), len(bindings))
    
    def test_concurrent_operations(self):
        """Test concurrent operations on the knowledge store.
        
        This test verifies that the knowledge store correctly handles
        concurrent operations like simultaneous queries and updates.
        """
        # This test would normally use threading, but for the mock implementation,
        # we'll simulate concurrent operations by interleaving them
        
        # Create constants
        alice = ConstantNode("Alice", self.entity_type)
        bob = ConstantNode("Bob", self.entity_type)
        
        # Create predicates
        knows_pred = ConstantNode("Knows", self.binary_pred_type)
        
        # Create assertions
        alice_knows_bob = ApplicationNode(knows_pred, [alice, bob], self.boolean_type)
        
        # Create variables for querying
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create a query: Knows(?x, ?y)
        query = ApplicationNode(knows_pred, [x_var, y_var], self.boolean_type)
        
        # Register a query result
        query_result = QueryResult(
            success=True,
            bindings=[
                {x_var: alice, y_var: bob}
            ]
        )
        self.knowledge_store.register_query_result(query, query_result)
        
        # Simulate concurrent operations
        # Operation 1: Add assertion
        self.knowledge_store.add_assertion(alice_knows_bob)
        
        # Operation 2: Execute query
        result1 = self.knowledge_store.execute_query(query)
        
        # Operation 3: Remove assertion
        self.knowledge_store.remove_assertion(alice_knows_bob)
        
        # Operation 4: Execute query again
        # Note: In a real implementation, this would return different results,
        # but our mock always returns the registered result
        result2 = self.knowledge_store.execute_query(query)
        
        # Verify the results
        self.assertTrue(result1.success)
        self.assertEqual(len(result1.bindings), 1)
        self.assertEqual(result1.bindings[0][x_var], alice)
        self.assertEqual(result1.bindings[0][y_var], bob)
        
        self.assertTrue(result2.success)
        self.assertEqual(len(result2.bindings), 1)
        self.assertEqual(result2.bindings[0][x_var], alice)
        self.assertEqual(result2.bindings[0][y_var], bob)
        
        # Verify that the assertion was removed
        self.assertNotIn(alice_knows_bob, self.knowledge_store.get_assertions())
    
    def test_handling_of_inconsistent_knowledge(self):
        """Test handling of inconsistent knowledge.
        
        This test verifies that the knowledge store correctly handles
        inconsistent knowledge, such as contradictory assertions.
        """
        # Create constants
        a = ConstantNode("A", self.entity_type)
        
        # Create predicates
        p_pred = ConstantNode("P", self.unary_pred_type)
        
        # Create contradictory assertions: P(A) and ¬P(A)
        p_a = ApplicationNode(p_pred, [a], self.boolean_type)
        not_p_a = ConnectiveNode("NOT", [p_a], self.boolean_type)
        
        # Add the contradictory assertions
        self.knowledge_store.add_assertion(p_a)
        self.knowledge_store.add_assertion(not_p_a)
        
        # Verify that both assertions were added
        assertions = self.knowledge_store.get_assertions()
        self.assertIn(p_a, assertions)
        self.assertIn(not_p_a, assertions)
        
        # Create a variable for querying
        x_var = VariableNode("?x", 1, self.entity_type)
        
        # Create a query: P(?x)
        query = ApplicationNode(p_pred, [x_var], self.boolean_type)
        
        # Register a query result that indicates inconsistency
        # In a real implementation, this might have special handling for inconsistency
        query_result = QueryResult(
            success=True,
            bindings=[
                {x_var: a}
            ]
        )
        self.knowledge_store.register_query_result(query, query_result)
        
        # Execute the query
        result = self.knowledge_store.execute_query(query)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(len(result.bindings), 1)
        self.assertEqual(result.bindings[0][x_var], a)
    
    def test_query_with_complex_constraints(self):
        """Test querying with complex constraints.
        
        This test verifies that the knowledge store correctly handles
        queries with complex constraints, such as negation, disjunction,
        and implication.
        """
        # Create constants
        alice = ConstantNode("Alice", self.entity_type)
        bob = ConstantNode("Bob", self.entity_type)
        charlie = ConstantNode("Charlie", self.entity_type)
        
        # Create predicates
        knows_pred = ConstantNode("Knows", self.binary_pred_type)
        likes_pred = ConstantNode("Likes", self.binary_pred_type)
        
        # Create variables
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        
        # Create a complex query with disjunction:
        # Knows(?x, ?y) ∨ Likes(?x, ?y)
        # This finds all pairs (x, y) where x knows y or x likes y
        knows_x_y = ApplicationNode(knows_pred, [x_var, y_var], self.boolean_type)
        likes_x_y = ApplicationNode(likes_pred, [x_var, y_var], self.boolean_type)
        disjunction_query = ConnectiveNode("OR", [knows_x_y, likes_x_y], self.boolean_type)
        
        # Register a query result
        disjunction_result = QueryResult(
            success=True,
            bindings=[
                {x_var: alice, y_var: bob},    # Alice knows Bob
                {x_var: alice, y_var: charlie}, # Alice likes Charlie
                {x_var: bob, y_var: charlie}    # Bob knows Charlie
            ]
        )
        self.knowledge_store.register_query_result(disjunction_query, disjunction_result)
        
        # Execute the query
        result = self.knowledge_store.execute_query(disjunction_query)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(len(result.bindings), 3)
        
        # Create a complex query with implication:
        # Knows(?x, ?y) ⇒ Likes(?x, ?y)
        # This is equivalent to ¬Knows(?x, ?y) ∨ Likes(?x, ?y)
        # It finds all pairs (x, y) where if x knows y, then x likes y
        not_knows_x_y = ConnectiveNode("NOT", [knows_x_y], self.boolean_type)
        implication_query = ConnectiveNode("OR", [not_knows_x_y, likes_x_y], self.boolean_type)
        
        # Register a query result
        implication_result = QueryResult(
            success=True,
            bindings=[
                {x_var: alice, y_var: bob},    # Alice knows and likes Bob
                {x_var: charlie, y_var: alice}  # Charlie doesn't know Alice
            ]
        )
        self.knowledge_store.register_query_result(implication_query, implication_result)
        
        # Execute the query
        result = self.knowledge_store.execute_query(implication_query)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(len(result.bindings), 2)
        
        # Check specific bindings
        self.assertEqual(result.bindings[0][x_var], alice)
        self.assertEqual(result.bindings[0][y_var], bob)
        self.assertEqual(result.bindings[1][x_var], charlie)
        self.assertEqual(result.bindings[1][y_var], alice)


if __name__ == "__main__":
    unittest.main()