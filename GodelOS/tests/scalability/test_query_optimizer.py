"""
Unit tests for the Query Optimizer.

This module contains tests for the QueryOptimizer, QueryStatistics, and QueryPlan classes.
"""

import unittest
from unittest.mock import MagicMock, patch

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.type_system.types import Type
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface

from godelOS.scalability.query_optimizer import QueryOptimizer, QueryStatistics, QueryPlan


class TestQueryPlan(unittest.TestCase):
    """Test cases for the QueryPlan class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create a query pattern
        self.x = VariableNode("?x", "x", self.entity_type)
        self.person = ConstantNode("Person", "Person", self.entity_type)
        self.is_a = ConstantNode("is_a", "is_a", self.entity_type)
        self.query_pattern = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
        
        # Create a query plan
        self.context_ids = ["TEST"]
        self.variables_to_bind = [self.x]
        self.plan = QueryPlan(self.query_pattern, self.context_ids, self.variables_to_bind)
    
    def test_initialization(self):
        """Test initialization of a query plan."""
        # Check if the plan is initialized correctly
        self.assertEqual(self.plan.original_query_pattern, self.query_pattern)
        self.assertEqual(self.plan.optimized_query_pattern, self.query_pattern)
        self.assertEqual(self.plan.context_ids, self.context_ids)
        self.assertEqual(self.plan.variables_to_bind, self.variables_to_bind)
        self.assertEqual(self.plan.estimated_cost, float('inf'))
    
    def test_str_representation(self):
        """Test string representation of a query plan."""
        # Set a cost for the plan
        self.plan.estimated_cost = 10.5
        
        # Check if the string representation is correct
        expected_str = f"QueryPlan(pattern={self.query_pattern}, contexts={self.context_ids}, cost=10.5)"
        self.assertEqual(str(self.plan), expected_str)


class TestQueryStatistics(unittest.TestCase):
    """Test cases for the QueryStatistics class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock knowledge store
        self.knowledge_store = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create query statistics
        self.statistics = QueryStatistics(self.knowledge_store)
        
        # Set up predicate counts
        self.statistics.predicate_counts = {
            "is_a": 100,
            "has_color": 50,
            "has_size": 30
        }
        
        # Set up constant counts
        self.statistics.constant_counts = {
            "Person": 20,
            "Car": 15,
            "Red": 10,
            "Blue": 5
        }
        
        # Set up type counts
        self.statistics.type_counts = {
            "Entity": 100,
            "Relation": 50
        }
    
    def test_get_predicate_selectivity(self):
        """Test getting the selectivity of a predicate."""
        # Check if the selectivity is calculated correctly
        selectivity = self.statistics.get_predicate_selectivity("is_a")
        expected_selectivity = 100 / (100 + 50 + 30)
        self.assertAlmostEqual(selectivity, expected_selectivity)
        
        # Check if the selectivity of an unknown predicate is correct
        selectivity = self.statistics.get_predicate_selectivity("unknown")
        self.assertEqual(selectivity, 0.0)
    
    def test_get_constant_selectivity(self):
        """Test getting the selectivity of a constant."""
        # Check if the selectivity is calculated correctly
        selectivity = self.statistics.get_constant_selectivity("Person")
        expected_selectivity = 20 / (20 + 15 + 10 + 5)
        self.assertAlmostEqual(selectivity, expected_selectivity)
        
        # Check if the selectivity of an unknown constant is correct
        selectivity = self.statistics.get_constant_selectivity("unknown")
        self.assertEqual(selectivity, 0.0)
    
    def test_get_type_selectivity(self):
        """Test getting the selectivity of a type."""
        # Check if the selectivity is calculated correctly
        selectivity = self.statistics.get_type_selectivity("Entity")
        expected_selectivity = 100 / (100 + 50)
        self.assertAlmostEqual(selectivity, expected_selectivity)
        
        # Check if the selectivity of an unknown type is correct
        selectivity = self.statistics.get_type_selectivity("unknown")
        self.assertEqual(selectivity, 0.0)
    
    def test_record_and_get_query_time(self):
        """Test recording and getting query execution time."""
        # Record some execution times
        query_hash = "test_query"
        self.statistics.record_query_time(query_hash, 0.1)
        self.statistics.record_query_time(query_hash, 0.2)
        self.statistics.record_query_time(query_hash, 0.3)
        
        # Check if the average execution time is calculated correctly
        avg_time = self.statistics.get_average_query_time(query_hash)
        self.assertAlmostEqual(avg_time, 0.2)
        
        # Check if the average execution time of an unknown query is correct
        avg_time = self.statistics.get_average_query_time("unknown")
        self.assertIsNone(avg_time)


class TestQueryOptimizer(unittest.TestCase):
    """Test cases for the QueryOptimizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock knowledge store
        self.knowledge_store = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create a query optimizer
        self.optimizer = QueryOptimizer(self.knowledge_store)
        
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create a query pattern
        self.x = VariableNode("?x", "x", self.entity_type)
        self.person = ConstantNode("Person", "Person", self.entity_type)
        self.is_a = ConstantNode("is_a", "is_a", self.entity_type)
        self.query_pattern = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
        
        # Set up mock returns
        self.knowledge_store.query_statements_match_pattern.return_value = ["result1", "result2"]
    
    def test_optimize_query(self):
        """Test optimizing a query."""
        # Optimize the query
        plan = self.optimizer.optimize_query(self.query_pattern, ["TEST"], [self.x])
        
        # Check if the plan is created correctly
        self.assertEqual(plan.original_query_pattern, self.query_pattern)
        self.assertEqual(plan.context_ids, ["TEST"])
        self.assertEqual(plan.variables_to_bind, [self.x])
        self.assertLess(plan.estimated_cost, float('inf'))
    
    def test_execute_optimized_query(self):
        """Test executing an optimized query."""
        # Create a query plan
        plan = QueryPlan(self.query_pattern, ["TEST"], [self.x])
        
        # Execute the plan
        results = self.optimizer.execute_optimized_query(plan)
        
        # Check if the query was executed correctly
        self.knowledge_store.query_statements_match_pattern.assert_called_once_with(
            plan.optimized_query_pattern, plan.context_ids, plan.variables_to_bind)
        
        # Check if the results are correct
        self.assertEqual(results, ["result1", "result2"])
    
    def test_estimate_query_cost(self):
        """Test estimating the cost of a query."""
        # Create a query plan
        plan = QueryPlan(self.query_pattern, ["TEST"], [self.x])
        
        # Estimate the cost
        cost = self.optimizer._estimate_query_cost(plan)
        
        # Check if the cost is a positive number
        self.assertGreater(cost, 0)
    
    def test_estimate_pattern_complexity(self):
        """Test estimating the complexity of a pattern."""
        # Estimate the complexity of a variable
        complexity = self.optimizer._estimate_pattern_complexity(self.x)
        self.assertEqual(complexity, 10.0)
        
        # Estimate the complexity of a constant
        complexity = self.optimizer._estimate_pattern_complexity(self.person)
        self.assertEqual(complexity, 1.0)
        
        # Estimate the complexity of an application node
        complexity = self.optimizer._estimate_pattern_complexity(self.query_pattern)
        self.assertGreater(complexity, 0)


if __name__ == "__main__":
    unittest.main()