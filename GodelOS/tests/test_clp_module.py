"""
Unit tests for the Constraint Logic Programming Module.

This module contains unit tests for the CLPModule class, which provides a declarative
framework for solving problems that combine logical deduction with constraint
satisfaction over specific domains.
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional, Set

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode, ConnectiveNode
)
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.base_prover import ResourceLimits
from godelOS.inference_engine.clp_module import (
    CLPModule, ConstraintVariable, ConstraintStore, DomainStore, 
    ConstraintSolver, FiniteDomainSolver, CLPClause
)


class TestCLPModule(unittest.TestCase):
    """Tests for the CLPModule class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock KnowledgeStoreInterface
        self.kr_system_interface = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create a mock TypeSystemManager
        self.type_system = MagicMock(spec=TypeSystemManager)
        
        # Create a mock UnificationEngine
        self.unification_engine = MagicMock(spec=UnificationEngine)
        
        # Create a CLPModule with the mocks
        self.clp_module = CLPModule(
            self.kr_system_interface,
            self.unification_engine
        )
        
        # Create types for testing
        self.bool_type = AtomicType("Boolean")
        self.int_type = AtomicType("Integer")
        
        # Create constants and variables for testing
        self.true_const = ConstantNode("true", self.bool_type, True)
        self.false_const = ConstantNode("false", self.bool_type, False)
        self.zero_const = ConstantNode("0", self.int_type, 0)
        self.one_const = ConstantNode("1", self.int_type, 1)
        self.two_const = ConstantNode("2", self.int_type, 2)
        self.three_const = ConstantNode("3", self.int_type, 3)
        self.x_var = VariableNode("X", 1, self.int_type)
        self.y_var = VariableNode("Y", 2, self.int_type)
        self.z_var = VariableNode("Z", 3, self.int_type)
        
        # Create functions for testing
        self.plus_func = ConstantNode("+", FunctionType([self.int_type, self.int_type], self.int_type))
        self.less_func = ConstantNode("<", FunctionType([self.int_type, self.int_type], self.bool_type))
        self.eq_func = ConstantNode("=", FunctionType([self.int_type, self.int_type], self.bool_type))
    
    def test_capabilities(self):
        """Test the capabilities of the CLPModule."""
        capabilities = self.clp_module.capabilities
        
        self.assertTrue(capabilities["constraint_solving"])
        self.assertTrue(capabilities["first_order_logic"])
        self.assertTrue(capabilities["arithmetic"])
        self.assertFalse(capabilities["modal_logic"])
        self.assertFalse(capabilities["higher_order_logic"])
    
    def test_constraint_variable(self):
        """Test the ConstraintVariable class."""
        # Test with explicit domain values
        cv1 = ConstraintVariable(self.x_var, "FD")
        cv1.set_domain_values({1, 2, 3, 4, 5})
        
        self.assertEqual(cv1.get_size(), 5)
        self.assertFalse(cv1.is_singleton())
        self.assertIsNone(cv1.get_value())
        
        # Test with domain range
        cv2 = ConstraintVariable(self.y_var, "FD", 1, 5)
        
        self.assertEqual(cv2.get_size(), 5)
        self.assertFalse(cv2.is_singleton())
        self.assertIsNone(cv2.get_value())
        
        # Test singleton domain
        cv3 = ConstraintVariable(self.z_var, "FD", 3, 3)
        
        self.assertEqual(cv3.get_size(), 1)
        self.assertTrue(cv3.is_singleton())
        self.assertEqual(cv3.get_value(), 3)
        
        # Test domain intersection
        cv4 = ConstraintVariable(self.x_var, "FD", 1, 10)
        cv5 = ConstraintVariable(self.x_var, "FD", 5, 15)
        
        cv4.intersect(cv5)
        self.assertEqual(cv4.domain_min, 5)
        self.assertEqual(cv4.domain_max, 10)
    
    def test_constraint_store(self):
        """Test the ConstraintStore class."""
        store = ConstraintStore()
        
        # Create a constraint: X < Y
        constraint = ApplicationNode(self.less_func, [self.x_var, self.y_var], self.bool_type)
        
        # Add the constraint to the store
        result = store.add_constraint(constraint)
        
        self.assertTrue(result)
        self.assertEqual(len(store.get_constraints()), 1)
        
        # Add the same constraint again
        result = store.add_constraint(constraint)
        
        self.assertFalse(result)
        self.assertEqual(len(store.get_constraints()), 1)
        
        # Test wake-up queue
        self.assertEqual(store.get_next_constraint_to_wake_up(), constraint)
        self.assertIsNone(store.get_next_constraint_to_wake_up())
        
        # Test wake-up all
        store.wake_up_all()
        self.assertEqual(store.get_next_constraint_to_wake_up(), constraint)
    
    def test_domain_store(self):
        """Test the DomainStore class."""
        store = DomainStore()
        
        # Create domains
        domain1 = ConstraintVariable(self.x_var, "FD", 1, 10)
        domain2 = ConstraintVariable(self.y_var, "FD", 5, 15)
        
        # Set domains
        result1 = store.set_domain(self.x_var, domain1)
        result2 = store.set_domain(self.y_var, domain2)
        
        self.assertTrue(result1)
        self.assertTrue(result2)
        
        # Get domains
        self.assertEqual(store.get_domain(self.x_var), domain1)
        self.assertEqual(store.get_domain(self.y_var), domain2)
        
        # Test changed variables
        changed_vars = store.get_changed_variables()
        self.assertEqual(len(changed_vars), 2)
        self.assertIn(self.x_var.var_id, changed_vars)
        self.assertIn(self.y_var.var_id, changed_vars)
        
        # Clear changed variables
        store.clear_changed_variables()
        self.assertEqual(len(store.get_changed_variables()), 0)
        
        # Test update domain
        result = store.update_domain(self.x_var, "FD", 5, 8)
        
        self.assertTrue(result)
        updated_domain = store.get_domain(self.x_var)
        self.assertEqual(updated_domain.domain_min, 5)
        self.assertEqual(updated_domain.domain_max, 8)
        
        # Test get all variables
        variables = store.get_all_variables()
        self.assertEqual(len(variables), 2)
        self.assertIn(self.x_var, variables)
        self.assertIn(self.y_var, variables)
    
    def test_finite_domain_solver(self):
        """Test the FiniteDomainSolver class."""
        solver = FiniteDomainSolver()
        domain_store = DomainStore()
        
        # Set up domains
        domain_x = ConstraintVariable(self.x_var, "FD", 1, 5)
        domain_y = ConstraintVariable(self.y_var, "FD", 1, 5)
        
        domain_store.set_domain(self.x_var, domain_x)
        domain_store.set_domain(self.y_var, domain_y)
        
        # Test equality constraint: X = Y
        eq_constraint = ApplicationNode(self.eq_func, [self.x_var, self.y_var], self.bool_type)
        
        self.assertTrue(solver.can_handle_constraint(eq_constraint))
        self.assertTrue(solver.propagate(eq_constraint, domain_store))
        
        # Test inequality constraint: X < Y
        lt_constraint = ApplicationNode(self.less_func, [self.x_var, self.y_var], self.bool_type)
        
        self.assertTrue(solver.can_handle_constraint(lt_constraint))
        self.assertTrue(solver.propagate(lt_constraint, domain_store))
        
        # Test with a constant: X = 3
        eq_const_constraint = ApplicationNode(self.eq_func, [self.x_var, self.three_const], self.bool_type)
        
        self.assertTrue(solver.can_handle_constraint(eq_const_constraint))
        self.assertTrue(solver.propagate(eq_const_constraint, domain_store))
        
        # Check that X's domain is now a singleton
        x_domain = domain_store.get_domain(self.x_var)
        self.assertTrue(x_domain.is_singleton())
        self.assertEqual(x_domain.get_value(), 3)
    
    def test_clp_clause(self):
        """Test the CLPClause class."""
        # Create a fact: p(a).
        p_func = ConstantNode("p", FunctionType([self.int_type], self.bool_type))
        p_a = ApplicationNode(p_func, [self.one_const], self.bool_type)
        
        fact = CLPClause(p_a, [], [])
        
        self.assertTrue(fact.is_fact())
        self.assertFalse(fact.is_query())
        
        # Create a rule: q(X) :- p(X), X > 0.
        q_func = ConstantNode("q", FunctionType([self.int_type], self.bool_type))
        q_x = ApplicationNode(q_func, [self.x_var], self.bool_type)
        p_x = ApplicationNode(p_func, [self.x_var], self.bool_type)
        x_gt_0 = ApplicationNode(self.less_func, [self.zero_const, self.x_var], self.bool_type)
        
        rule = CLPClause(q_x, [p_x], [x_gt_0])
        
        self.assertFalse(rule.is_fact())
        self.assertFalse(rule.is_query())
        
        # Create a query: ?- q(X), X < 5.
        query = CLPClause(None, [q_x], [ApplicationNode(self.less_func, [self.x_var, self.three_const], self.bool_type)])
        
        self.assertFalse(query.is_fact())
        self.assertTrue(query.is_query())
    
    @patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_constraints')
    def test_can_handle(self, mock_contains_constraints):
        """Test the can_handle method."""
        # Set up the mock to return True
        mock_contains_constraints.return_value = True
        
        # Create a goal and context
        goal = ApplicationNode(self.eq_func, [self.x_var, self.y_var], self.bool_type)
        context = {ApplicationNode(self.less_func, [self.x_var, self.three_const], self.bool_type)}
        
        # Test can_handle
        self.assertTrue(self.clp_module.can_handle(goal, context))
        
        # Set up the mock to return False
        mock_contains_constraints.return_value = False
        
        # Test can_handle
        self.assertFalse(self.clp_module.can_handle(goal, context))
    
    def test_parse_program(self):
        """Test the _parse_program method."""
        # Create a fact: p(1).
        p_func = ConstantNode("p", FunctionType([self.int_type], self.bool_type))
        p_1 = ApplicationNode(p_func, [self.one_const], self.bool_type)
        
        # Create a rule: q(X) :- p(X), X > 0.
        q_func = ConstantNode("q", FunctionType([self.int_type], self.bool_type))
        q_x = ApplicationNode(q_func, [self.x_var], self.bool_type)
        p_x = ApplicationNode(p_func, [self.x_var], self.bool_type)
        x_gt_0 = ApplicationNode(self.less_func, [self.zero_const, self.x_var], self.bool_type)
        
        # Create the rule as an implication: p(X) & (X > 0) -> q(X)
        body = ConnectiveNode("AND", [p_x, x_gt_0], self.bool_type)
        rule = ConnectiveNode("IMPLIES", [body, q_x], self.bool_type)
        
        # Parse the program
        with patch.object(self.clp_module, '_is_constraint', side_effect=lambda x: x == x_gt_0):
            clauses = self.clp_module._parse_program({p_1, rule})
        
        # Check the results
        self.assertEqual(len(clauses), 2)
        
        # Find fact and rule regardless of iteration order
        facts = [c for c in clauses if c.is_fact()]
        rules = [c for c in clauses if not c.is_fact() and not c.is_query()]
        
        # Check the fact
        self.assertEqual(len(facts), 1)
        fact = facts[0]
        self.assertTrue(fact.is_fact())
        self.assertEqual(fact.head, p_1)
        
        # Check the rule
        self.assertEqual(len(rules), 1)
        rule_clause = rules[0]
        self.assertEqual(rule_clause.head, q_x)
        self.assertEqual(len(rule_clause.body), 1)
        self.assertEqual(rule_clause.body[0], p_x)
        self.assertEqual(len(rule_clause.constraints), 1)
        self.assertEqual(rule_clause.constraints[0], x_gt_0)
    
    def test_parse_query(self):
        """Test the _parse_query method."""
        # Create a query: ?- q(X), X < 3.
        q_func = ConstantNode("q", FunctionType([self.int_type], self.bool_type))
        q_x = ApplicationNode(q_func, [self.x_var], self.bool_type)
        x_lt_3 = ApplicationNode(self.less_func, [self.x_var, self.three_const], self.bool_type)
        
        # Create the query as a conjunction: q(X) & (X < 3)
        query = ConnectiveNode("AND", [q_x, x_lt_3], self.bool_type)
        
        # Parse the query
        with patch.object(self.clp_module, '_is_constraint', side_effect=lambda x: x == x_lt_3):
            query_clause = self.clp_module._parse_query(query)
        
        # Check the results
        self.assertTrue(query_clause.is_query())
        self.assertEqual(len(query_clause.body), 1)
        self.assertEqual(query_clause.body[0], q_x)
        self.assertEqual(len(query_clause.constraints), 1)
        self.assertEqual(query_clause.constraints[0], x_lt_3)
    
    def test_is_constraint(self):
        """Test the _is_constraint method."""
        # Create a constraint: X < 3
        constraint = ApplicationNode(self.less_func, [self.x_var, self.three_const], self.bool_type)
        
        # Create a non-constraint: q(X)
        q_func = ConstantNode("q", FunctionType([self.int_type], self.bool_type))
        non_constraint = ApplicationNode(q_func, [self.x_var], self.bool_type)
        
        # Test with a mock solver that recognises standard FD constraint names
        fd_names = {'=', '!=', '<', '<=', '>', '>=', 'AllDifferent', 'SumEquals'}
        mock_solver = MagicMock(spec=ConstraintSolver)
        mock_solver.can_handle_constraint.side_effect = (
            lambda ast: isinstance(ast, ApplicationNode)
            and isinstance(ast.operator, ConstantNode)
            and ast.operator.name in fd_names
        )
        
        self.clp_module.solver_registry = {"FD": mock_solver}
        
        # Test is_constraint
        self.assertTrue(self.clp_module._is_constraint(constraint))
        self.assertFalse(self.clp_module._is_constraint(non_constraint))
    
    def test_initialize_domains(self):
        """Test the _initialize_domains method."""
        # Create a query: ?- q(X), X < 3, Y > 0.
        q_func = ConstantNode("q", FunctionType([self.int_type], self.bool_type))
        q_x = ApplicationNode(q_func, [self.x_var], self.bool_type)
        x_lt_3 = ApplicationNode(self.less_func, [self.x_var, self.three_const], self.bool_type)
        y_gt_0 = ApplicationNode(self.less_func, [self.zero_const, self.y_var], self.bool_type)
        
        # Create the query clause
        query_clause = CLPClause(None, [q_x], [x_lt_3, y_gt_0])
        
        # Initialize domains
        domain_store = DomainStore()
        self.clp_module._initialize_domains(query_clause, domain_store)
        
        # Check that domains were initialized for X and Y
        x_domain = domain_store.get_domain(self.x_var)
        y_domain = domain_store.get_domain(self.y_var)
        
        self.assertIsNotNone(x_domain)
        self.assertIsNotNone(y_domain)
        self.assertEqual(x_domain.domain_type, "FD")
        self.assertEqual(y_domain.domain_type, "FD")
    
    def test_propagate_constraints(self):
        """Test the _propagate_constraints method."""
        # Create constraints: X < 3, Y > 0
        x_lt_3 = ApplicationNode(self.less_func, [self.x_var, self.three_const], self.bool_type)
        y_gt_0 = ApplicationNode(self.less_func, [self.zero_const, self.y_var], self.bool_type)
        
        # Set up stores
        constraint_store = ConstraintStore()
        domain_store = DomainStore()
        
        # Add constraints to the store
        constraint_store.add_constraint(x_lt_3)
        constraint_store.add_constraint(y_gt_0)
        
        # Set up domains
        domain_x = ConstraintVariable(self.x_var, "FD", 1, 5)
        domain_y = ConstraintVariable(self.y_var, "FD", 0, 5)
        
        domain_store.set_domain(self.x_var, domain_x)
        domain_store.set_domain(self.y_var, domain_y)
        
        # Create a mock solver that can handle the constraints
        mock_solver = MagicMock(spec=ConstraintSolver)
        mock_solver.can_handle_constraint.return_value = True
        mock_solver.propagate.return_value = True
        
        self.clp_module.solver_registry = {"FD": mock_solver}
        
        # Propagate constraints
        result = self.clp_module._propagate_constraints(constraint_store, domain_store)
        
        # Check the result
        self.assertTrue(result)
        self.assertEqual(mock_solver.propagate.call_count, 2)
    
    def test_label_variables(self):
        """Test the _label_variables method."""
        # Set up domain store
        domain_store = DomainStore()
        
        # Set up domains
        domain_x = ConstraintVariable(self.x_var, "FD", 1, 1)  # Singleton domain
        domain_y = ConstraintVariable(self.y_var, "FD", 1, 3)  # Non-singleton domain
        
        domain_store.set_domain(self.x_var, domain_x)
        domain_store.set_domain(self.y_var, domain_y)
        
        # Label variables
        solutions = self.clp_module._label_variables(domain_store, 10, "default")
        
        # Check the results
        self.assertEqual(len(solutions), 3)  # One solution for each value of Y
        
        # Check the first solution
        solution1 = solutions[0]
        self.assertEqual(len(solution1), 2)  # X and Y
        self.assertEqual(solution1[self.x_var].value, 1)
        self.assertEqual(solution1[self.y_var].value, 1)
        
        # Check the second solution
        solution2 = solutions[1]
        self.assertEqual(solution2[self.x_var].value, 1)
        self.assertEqual(solution2[self.y_var].value, 2)
        
        # Check the third solution
        solution3 = solutions[2]
        self.assertEqual(solution3[self.x_var].value, 1)
        self.assertEqual(solution3[self.y_var].value, 3)
    
    def test_select_variable(self):
        """Test the _select_variable method."""
        # Set up domain store
        domain_store = DomainStore()
        
        # Set up domains
        domain_x = ConstraintVariable(self.x_var, "FD", 1, 5)  # 5 values
        domain_y = ConstraintVariable(self.y_var, "FD", 1, 3)  # 3 values
        domain_z = ConstraintVariable(self.z_var, "FD", 1, 10)  # 10 values
        
        domain_store.set_domain(self.x_var, domain_x)
        domain_store.set_domain(self.y_var, domain_y)
        domain_store.set_domain(self.z_var, domain_z)
        
        # Test default strategy
        selected_var = self.clp_module._select_variable([self.x_var, self.y_var, self.z_var], domain_store, "default")
        self.assertEqual(selected_var, self.x_var)  # First variable
        
        # Test first_fail strategy
        selected_var = self.clp_module._select_variable([self.x_var, self.y_var, self.z_var], domain_store, "first_fail")
        self.assertEqual(selected_var, self.y_var)  # Smallest domain
    
    def test_get_values(self):
        """Test the _get_values method."""
        # Set up domain with explicit values
        domain1 = ConstraintVariable(self.x_var, "FD")
        domain1.set_domain_values({3, 1, 5, 2, 4})
        
        # Test default strategy
        values1 = self.clp_module._get_values(domain1, "default")
        self.assertEqual(len(values1), 5)
        
        # Test min strategy
        values2 = self.clp_module._get_values(domain1, "min")
        self.assertEqual(values2, [1, 2, 3, 4, 5])
        
        # Test max strategy
        values3 = self.clp_module._get_values(domain1, "max")
        self.assertEqual(values3, [5, 4, 3, 2, 1])
        
        # Set up domain with range
        domain2 = ConstraintVariable(self.y_var, "FD", 1, 5)
        
        # Test default strategy
        values4 = self.clp_module._get_values(domain2, "default")
        self.assertEqual(len(values4), 5)
        self.assertEqual(set(values4), {1, 2, 3, 4, 5})


if __name__ == '__main__':
    unittest.main()