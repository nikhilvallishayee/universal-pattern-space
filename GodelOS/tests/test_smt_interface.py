"""
Unit tests for the SMT Interface.

This module contains unit tests for the SMTInterface class, which interfaces with
external SMT (Satisfiability Modulo Theories) solvers like Z3, CVC5, Yices.
"""

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
import subprocess
from typing import Dict, List, Optional, Set

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode, ConnectiveNode, QuantifierNode
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.inference_engine.base_prover import ResourceLimits
from godelOS.inference_engine.smt_interface import (
    SMTInterface, SMTSolverConfiguration, SMTResult
)


class TestSMTInterface(unittest.TestCase):
    """Tests for the SMTInterface class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock KnowledgeStoreInterface
        self.kr_system_interface = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create a mock TypeSystemManager
        self.type_system = MagicMock(spec=TypeSystemManager)
        
        # Create a mock solver configuration
        self.solver_config = SMTSolverConfiguration(
            solver_name="MockSolver",
            solver_path="mock_solver",
            solver_options=["--produce-models", "--produce-unsat-cores"]
        )
        
        # Create an SMTInterface with the mock solver
        self.smt_interface = SMTInterface(
            [self.solver_config],
            self.type_system
        )
        
        # Create types for testing
        self.bool_type = AtomicType("Boolean")
        self.int_type = AtomicType("Integer")
        self.real_type = AtomicType("Real")
        self.entity_type = AtomicType("Entity")
        
        # Create constants and variables for testing
        self.true_const = ConstantNode("true", self.bool_type, True)
        self.false_const = ConstantNode("false", self.bool_type, False)
        self.zero_const = ConstantNode("0", self.int_type, 0)
        self.one_const = ConstantNode("1", self.int_type, 1)
        self.a_const = ConstantNode("a", self.entity_type)
        self.b_const = ConstantNode("b", self.entity_type)
        self.x_var = VariableNode("x", 1, self.int_type)
        self.y_var = VariableNode("y", 2, self.int_type)
        
        # Create functions for testing
        self.plus_func = ConstantNode("+", FunctionType([self.int_type, self.int_type], self.int_type))
        self.less_func = ConstantNode("<", FunctionType([self.int_type, self.int_type], self.bool_type))
    
    def test_capabilities(self):
        """Test the capabilities of the SMTInterface."""
        capabilities = self.smt_interface.capabilities
        
        self.assertTrue(capabilities["arithmetic"])
        self.assertTrue(capabilities["equality"])
        self.assertTrue(capabilities["uninterpreted_functions"])
        self.assertTrue(capabilities["propositional_logic"])
        self.assertTrue(capabilities["first_order_logic"])
        self.assertFalse(capabilities["modal_logic"])
        self.assertFalse(capabilities["higher_order_logic"])
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Create an arithmetic formula: x + 1 < y
        x_plus_1 = ApplicationNode(self.plus_func, [self.x_var, self.one_const], self.int_type)
        less_than = ApplicationNode(self.less_func, [x_plus_1, self.y_var], self.bool_type)
        
        # Create a simple context: {true}
        context = {self.true_const}
        
        # Mock the coordinator methods
        with patch('godelOS.inference_engine.coordinator.InferenceCoordinator._contains_arithmetic', return_value=True):
            # The interface should be able to handle this goal and context
            self.assertTrue(self.smt_interface.can_handle(less_than, context))
    
    def test_type_to_smt_sort(self):
        """Test converting GödelOS types to SMT-LIB sorts."""
        # Test basic types
        self.assertEqual(self.smt_interface._type_to_smt_sort(self.bool_type), "Bool")
        self.assertEqual(self.smt_interface._type_to_smt_sort(self.int_type), "Int")
        self.assertEqual(self.smt_interface._type_to_smt_sort(self.real_type), "Real")
        self.assertEqual(self.smt_interface._type_to_smt_sort(self.entity_type), "Entity")
        
        # Test function types
        func_type = FunctionType([self.int_type, self.int_type], self.int_type)
        self.assertEqual(self.smt_interface._type_to_smt_sort(func_type), "(Int -> Int -> Int)")
    
    def test_translate_ast_to_smtlib(self):
        """Test translating AST nodes to SMT-LIB format."""
        # Test constants
        self.assertEqual(self.smt_interface._translate_ast_to_smtlib(self.true_const), "true")
        self.assertEqual(self.smt_interface._translate_ast_to_smtlib(self.false_const), "false")
        self.assertEqual(self.smt_interface._translate_ast_to_smtlib(self.zero_const), "0")
        
        # Test variables
        self.assertEqual(self.smt_interface._translate_ast_to_smtlib(self.x_var), "x_1")
        self.assertEqual(self.smt_interface._translate_ast_to_smtlib(self.y_var), "y_2")
        
        # Test application
        x_plus_1 = ApplicationNode(self.plus_func, [self.x_var, self.one_const], self.int_type)
        self.assertEqual(self.smt_interface._translate_ast_to_smtlib(x_plus_1), "(+ x_1 1)")
        
        # Test connectives
        not_x_eq_y = ConnectiveNode("NOT", [
            ConnectiveNode("EQUIV", [self.x_var, self.y_var], self.bool_type)
        ], self.bool_type)
        self.assertEqual(self.smt_interface._translate_ast_to_smtlib(not_x_eq_y), "(not (= x_1 y_2))")
        
        # Test quantifiers
        forall_x = QuantifierNode(
            "FORALL",
            [self.x_var],
            ApplicationNode(self.less_func, [self.x_var, self.y_var], self.bool_type),
            self.bool_type
        )
        self.assertEqual(
            self.smt_interface._translate_ast_to_smtlib(forall_x),
            "(forall ((x_1 Int)) (< x_1 y_2))"
        )
    
    def test_generate_smt_script(self):
        """Test generating an SMT-LIB script."""
        # Create a simple formula: x + 1 < y
        x_plus_1 = ApplicationNode(self.plus_func, [self.x_var, self.one_const], self.int_type)
        less_than = ApplicationNode(self.less_func, [x_plus_1, self.y_var], self.bool_type)
        
        # Create a context with one axiom: x >= 0
        geq_func = ConstantNode(">=", FunctionType([self.int_type, self.int_type], self.bool_type))
        x_geq_0 = ApplicationNode(geq_func, [self.x_var, self.zero_const], self.bool_type)
        context = {x_geq_0}
        
        # Generate the SMT-LIB script
        script = self.smt_interface._generate_smt_script(
            less_than,
            context,
            "QF_LIA",  # Quantifier-Free Linear Integer Arithmetic
            True,      # Request model
            True       # Request unsat core
        )
        
        # Check that the script contains the expected elements
        self.assertIn("(set-logic QF_LIA)", script)
        self.assertIn("(declare-const x_1 Int)", script)
        self.assertIn("(declare-const y_2 Int)", script)
        self.assertIn("(assert (! (>= x_1 0) :named", script)  # Axiom with name
        self.assertIn("(assert (! (< (+ x_1 1) y_2) :named formula))", script)
        self.assertIn("(check-sat)", script)
        self.assertIn("(get-model)", script)
        self.assertIn("(get-unsat-core)", script)
    
    @patch('subprocess.Popen')
    def test_check_satisfiability(self, mock_popen):
        """Test checking satisfiability with an SMT solver."""
        # Mock the subprocess.Popen to return a satisfiable result
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("sat\n(model\n(define-fun x () Int 0)\n(define-fun y () Int 2)\n)", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Create a simple formula: x + 1 < y
        x_plus_1 = ApplicationNode(self.plus_func, [self.x_var, self.one_const], self.int_type)
        less_than = ApplicationNode(self.less_func, [x_plus_1, self.y_var], self.bool_type)
        
        # Check satisfiability
        result = self.smt_interface.check_satisfiability(
            less_than,
            set(),
            "QF_LIA",
            True,
            False
        )
        
        # Verify the result
        self.assertEqual(result.status, "sat")
        
        # Verify that the subprocess was called with the correct arguments
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertEqual(kwargs["stdout"], subprocess.PIPE)
        self.assertEqual(kwargs["stderr"], subprocess.PIPE)
        self.assertEqual(kwargs["text"], True)
    
    @patch('subprocess.Popen')
    def test_prove_valid(self, mock_popen):
        """Test proving a valid formula."""
        # Mock the subprocess.Popen to return an unsatisfiable result
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("unsat\n(unsat-core formula axiom_123)", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Create a tautology: x = x
        eq_func = ConstantNode("=", FunctionType([self.int_type, self.int_type], self.bool_type))
        x_eq_x = ApplicationNode(eq_func, [self.x_var, self.x_var], self.bool_type)
        
        # Prove the formula
        result = self.smt_interface.prove(x_eq_x, set())
        
        # Verify the result
        self.assertTrue(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "SMTInterface")
        
        # Verify that the subprocess was called with the correct arguments
        mock_popen.assert_called_once()
    
    @patch('subprocess.Popen')
    def test_prove_invalid(self, mock_popen):
        """Test proving an invalid formula."""
        # Mock the subprocess.Popen to return a satisfiable result
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("sat\n(model\n(define-fun x () Int 0)\n(define-fun y () Int 1)\n)", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Create a non-tautology: x = y
        eq_func = ConstantNode("=", FunctionType([self.int_type, self.int_type], self.bool_type))
        x_eq_y = ApplicationNode(eq_func, [self.x_var, self.y_var], self.bool_type)
        
        # Prove the formula
        result = self.smt_interface.prove(x_eq_y, set())
        
        # Verify the result
        self.assertFalse(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "SMTInterface")
        
        # Verify that the subprocess was called with the correct arguments
        mock_popen.assert_called_once()
    
    @patch('subprocess.Popen')
    def test_prove_with_context(self, mock_popen):
        """Test proving a formula with context."""
        # Mock the subprocess.Popen to return an unsatisfiable result
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("unsat\n(unsat-core formula axiom_123)", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Create a formula: x + 1 < y
        x_plus_1 = ApplicationNode(self.plus_func, [self.x_var, self.one_const], self.int_type)
        less_than = ApplicationNode(self.less_func, [x_plus_1, self.y_var], self.bool_type)
        
        # Create context: x = 0 and y = 2
        eq_func = ConstantNode("=", FunctionType([self.int_type, self.int_type], self.bool_type))
        x_eq_0 = ApplicationNode(eq_func, [self.x_var, self.zero_const], self.bool_type)
        y_eq_2 = ApplicationNode(eq_func, [self.y_var, ConstantNode("2", self.int_type, 2)], self.bool_type)
        context = {x_eq_0, y_eq_2}
        
        # Prove the formula
        result = self.smt_interface.prove(less_than, context)
        
        # Verify the result
        self.assertTrue(result.goal_achieved)
        self.assertEqual(result.inference_engine_used, "SMTInterface")
        
        # Verify that the subprocess was called with the correct arguments
        mock_popen.assert_called_once()


if __name__ == '__main__':
    unittest.main()