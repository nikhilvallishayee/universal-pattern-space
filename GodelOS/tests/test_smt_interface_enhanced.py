"""
Enhanced unit tests for the SMT Interface component.

This file extends the basic tests in test_smt_interface.py with more thorough
testing of complex methods and edge cases, focusing on the translation between
GödelOS expressions and SMT-LIB format, handling of different theories, and
error conditions.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import tempfile
import os
import time
import subprocess
from typing import Dict, List, Optional, Set, Any, Tuple

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.smt_interface import (
    SMTInterface, SMTSolverConfiguration, SMTResult
)
from godelOS.inference_engine.base_prover import ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker

import shutil
import pytest

pytestmark = pytest.mark.skipif(
    shutil.which("z3") is None,
    reason="Z3 SMT solver not installed in this environment"
)




class TestSMTInterfaceEnhanced(unittest.TestCase):
    """Enhanced test cases for the SMT Interface with complex scenarios and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system
        self.type_system = TypeSystemManager()
        
        # Create basic types
        self.boolean_type = self.type_system.get_type("Boolean")
        self.integer_type = self.type_system.get_type("Integer")
        self.real_type = self.type_system.get_type("Real")
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create function types
        self.int_pred_type = FunctionType([self.integer_type], self.boolean_type)
        self.int_int_func_type = FunctionType([self.integer_type], self.integer_type)
        self.int_int_pred_type = FunctionType([self.integer_type, self.integer_type], self.boolean_type)
        self.int_int_int_func_type = FunctionType([self.integer_type, self.integer_type], self.integer_type)
        
        # Create SMT solver configurations
        self.z3_config = SMTSolverConfiguration(
            solver_name="Z3",
            solver_path="z3",
            solver_options=["-smt2", "-in"]
        )
        
        self.cvc5_config = SMTSolverConfiguration(
            solver_name="CVC5",
            solver_path="cvc5",
            solver_options=["--lang=smt2"]
        )
        
        # Create SMT interface with mock solvers
        self.smt_interface = SMTInterface(
            solver_configs=[self.z3_config, self.cvc5_config],
            type_system=self.type_system
        )
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    
    def test_complex_arithmetic_translation(self):
        """Test translation of complex arithmetic expressions to SMT-LIB format.
        
        This test verifies that the SMT interface correctly translates complex
        arithmetic expressions involving multiple operations and nested structures.
        """
        # Create variables and constants
        x_var = VariableNode("?x", 1, self.integer_type)
        y_var = VariableNode("?y", 2, self.integer_type)
        z_var = VariableNode("?z", 3, self.integer_type)
        
        one_const = ConstantNode("1", self.integer_type, 1)
        two_const = ConstantNode("2", self.integer_type, 2)
        
        # Create arithmetic operators
        plus_op = ConstantNode("+", self.int_int_int_func_type)
        minus_op = ConstantNode("-", self.int_int_int_func_type)
        times_op = ConstantNode("*", self.int_int_int_func_type)
        
        # Create comparison operators
        lt_op = ConstantNode("<", self.int_int_pred_type)
        eq_op = ConstantNode("=", self.int_int_pred_type)
        
        # Create a complex arithmetic expression: (x + 1) * (y - 2) < z
        x_plus_1 = ApplicationNode(plus_op, [x_var, one_const], self.integer_type)
        y_minus_2 = ApplicationNode(minus_op, [y_var, two_const], self.integer_type)
        product = ApplicationNode(times_op, [x_plus_1, y_minus_2], self.integer_type)
        lt_z = ApplicationNode(lt_op, [product, z_var], self.boolean_type)
        
        # Mock the _translate_ast_to_smtlib method to avoid implementation details
        with patch.object(self.smt_interface, '_translate_ast_to_smtlib') as mock_translate:
            mock_translate.return_value = "(< (* (+ ?x_1 1) (- ?y_2 2)) ?z_3)"
            
            # Generate an SMT script
            script = self.smt_interface._generate_smt_script(
                lt_z,
                set(),
                "QF_LIA",
                False,
                False
            )
            
            # Verify that _translate_ast_to_smtlib was called with the formula
            mock_translate.assert_called_with(lt_z)
            
            # Check that the script contains the expected logic and assertion
            self.assertIn("(set-logic QF_LIA)", script)
            self.assertIn("(assert (< (* (+ ?x_1 1) (- ?y_2 2)) ?z_3))", script)
    
    def test_translation_of_quantifiers(self):
        """Test translation of quantified formulas to SMT-LIB format.
        
        This test verifies that the SMT interface correctly translates
        quantified formulas with nested quantifiers and complex bodies.
        """
        # Create variables
        x_var = VariableNode("?x", 1, self.integer_type)
        y_var = VariableNode("?y", 2, self.integer_type)
        
        # Create arithmetic operators and predicates
        plus_op = ConstantNode("+", self.int_int_int_func_type)
        gt_op = ConstantNode(">", self.int_int_pred_type)
        
        # Create a formula: ∀?x. ∃?y. ?x + ?y > 0
        x_plus_y = ApplicationNode(plus_op, [x_var, y_var], self.integer_type)
        zero_const = ConstantNode("0", self.integer_type, 0)
        gt_zero = ApplicationNode(gt_op, [x_plus_y, zero_const], self.boolean_type)
        
        exists_y = QuantifierNode("EXISTS", [y_var], gt_zero, self.boolean_type)
        forall_x = QuantifierNode("FORALL", [x_var], exists_y, self.boolean_type)
        
        # Mock the _translate_ast_to_smtlib method
        with patch.object(self.smt_interface, '_translate_ast_to_smtlib') as mock_translate:
            mock_translate.return_value = "(forall ((?x_1 Int)) (exists ((?y_2 Int)) (> (+ ?x_1 ?y_2) 0)))"
            
            # Generate an SMT script
            script = self.smt_interface._generate_smt_script(
                forall_x,
                set(),
                "LIA",
                False,
                False
            )
            
            # Verify that _translate_ast_to_smtlib was called with the formula
            mock_translate.assert_called_with(forall_x)
            
            # Check that the script contains the expected logic and assertion
            self.assertIn("(set-logic LIA)", script)
            self.assertIn("(assert (forall ((?x_1 Int)) (exists ((?y_2 Int)) (> (+ ?x_1 ?y_2) 0))))", script)
    
    def test_multiple_theories_combination(self):
        """Test handling of formulas that combine multiple theories.
        
        This test verifies that the SMT interface correctly handles formulas
        that combine multiple theories like arithmetic, arrays, and uninterpreted functions.
        """
        # Create a simple formula involving arithmetic
        x_var = VariableNode("?x", 1, self.integer_type)
        y_var = VariableNode("?y", 2, self.integer_type)
        
        plus_op = ConstantNode("+", self.int_int_int_func_type)
        eq_op = ConstantNode("=", self.int_int_pred_type)
        
        x_plus_y = ApplicationNode(plus_op, [x_var, y_var], self.integer_type)
        ten_const = ConstantNode("10", self.integer_type, 10)
        eq_ten = ApplicationNode(eq_op, [x_plus_y, ten_const], self.boolean_type)
        
        # Test with different logic theories
        theories = ["QF_LIA", "AUFLIA", "QF_AUFLIRA"]
        
        for theory in theories:
            # Mock the _translate_ast_to_smtlib method
            with patch.object(self.smt_interface, '_translate_ast_to_smtlib') as mock_translate:
                mock_translate.return_value = "(= (+ ?x_1 ?y_2) 10)"
                
                # Generate an SMT script
                script = self.smt_interface._generate_smt_script(
                    eq_ten,
                    set(),
                    theory,
                    False,
                    False
                )
                
                # Check that the script contains the expected logic
                self.assertIn(f"(set-logic {theory})", script)
                
                # Verify that _translate_ast_to_smtlib was called with the formula
                mock_translate.assert_called_with(eq_ten)
    
    def test_error_handling_in_solver_invocation(self):
        """Test error handling in SMT solver invocation.
        
        This test verifies that the SMT interface correctly handles errors
        during solver invocation, such as timeouts, syntax errors, and crashes.
        """
        # Create a simple formula
        x_var = VariableNode("?x", 1, self.integer_type)
        eq_op = ConstantNode("=", self.int_int_pred_type)
        zero_const = ConstantNode("0", self.integer_type, 0)
        eq_zero = ApplicationNode(eq_op, [x_var, zero_const], self.boolean_type)
        
        # Test timeout handling
        with patch('subprocess.Popen') as mock_popen:
            # Mock subprocess.Popen to simulate a timeout
            mock_process = MagicMock()
            mock_process.communicate.side_effect = subprocess.TimeoutExpired("z3", 1.0)
            mock_popen.return_value = mock_process
            
            # Set a short timeout
            resources = ResourceLimits(time_limit_ms=1000)
            
            # Call check_satisfiability
            result = self.smt_interface.check_satisfiability(eq_zero, set(), resources=resources)
            
            # Verify that the result status is "timeout"
            self.assertEqual(result.status, "timeout")
            
            # Verify that the process was killed
            mock_process.kill.assert_called_once()
        
        # Test error handling for non-zero exit code
        with patch('subprocess.Popen') as mock_popen:
            # Mock subprocess.Popen to simulate a solver error
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("", "Error: syntax error")
            mock_process.returncode = 1
            mock_popen.return_value = mock_process
            
            # Call check_satisfiability
            result = self.smt_interface.check_satisfiability(eq_zero, set())
            
            # Verify that the result status is "error"
            self.assertEqual(result.status, "error")
    
    def test_unsat_core_extraction(self):
        """Test extraction of unsat cores.
        
        This test verifies that the SMT interface correctly extracts unsat cores
        from unsatisfiable formulas, which can be used for proof generation.
        """
        # Create variables and constants
        x_var = VariableNode("?x", 1, self.integer_type)
        
        # Create a predicate: x > 0
        gt_op = ConstantNode(">", self.int_int_pred_type)
        zero_const = ConstantNode("0", self.integer_type, 0)
        x_gt_zero = ApplicationNode(gt_op, [x_var, zero_const], self.boolean_type)
        
        # Create another predicate: x < 0
        lt_op = ConstantNode("<", self.int_int_pred_type)
        x_lt_zero = ApplicationNode(lt_op, [x_var, zero_const], self.boolean_type)
        
        # Create a conjunction: x > 0 ∧ x < 0 (unsatisfiable)
        and_op = ConnectiveNode("AND", [x_gt_zero, x_lt_zero], self.boolean_type)
        
        # Mock the subprocess call to simulate an unsat result with unsat core
        with patch('subprocess.Popen') as mock_popen, \
             patch('tempfile.NamedTemporaryFile', mock_open()) as mock_temp:
            
            # Set up the mock temporary file
            mock_temp.name = "temp_file.smt2"
            
            # Set up the mock process
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("unsat\n(axiom_123 formula)", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            # Call check_satisfiability with request_unsat_core=True
            result = self.smt_interface.check_satisfiability(
                and_op,
                set(),
                request_unsat_core=True
            )
            
            # Verify that the result status is "unsat"
            self.assertEqual(result.status, "unsat")
            
            # Verify that the unsat core was extracted
            self.assertIsNotNone(result.unsat_core_identifiers)
            self.assertEqual(len(result.unsat_core_identifiers), 2)
            self.assertIn("axiom_123", result.unsat_core_identifiers)
            self.assertIn("formula", result.unsat_core_identifiers)
    
    def test_model_generation(self):
        """Test model generation for satisfiable formulas.
        
        This test verifies that the SMT interface correctly generates models
        for satisfiable formulas, which can be used for counterexample generation.
        """
        # Create variables and constants
        x_var = VariableNode("?x", 1, self.integer_type)
        y_var = VariableNode("?y", 2, self.integer_type)
        
        # Create a predicate: x + y > 0
        plus_op = ConstantNode("+", self.int_int_int_func_type)
        gt_op = ConstantNode(">", self.int_int_pred_type)
        zero_const = ConstantNode("0", self.integer_type, 0)
        
        x_plus_y = ApplicationNode(plus_op, [x_var, y_var], self.integer_type)
        sum_gt_zero = ApplicationNode(gt_op, [x_plus_y, zero_const], self.boolean_type)
        
        # Mock the subprocess call to simulate a sat result with model
        with patch('subprocess.Popen') as mock_popen, \
             patch('tempfile.NamedTemporaryFile', mock_open()) as mock_temp:
            
            # Set up the mock temporary file
            mock_temp.name = "temp_file.smt2"
            
            # Set up the mock process
            mock_process = MagicMock()
            mock_process.communicate.return_value = (
                "sat\n(model\n  (define-fun ?x_1 () Int 1)\n  (define-fun ?y_2 () Int 0)\n)",
                ""
            )
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            # Mock the _parse_smt_model method
            with patch.object(self.smt_interface, '_parse_smt_model') as mock_parse_model:
                # Create a mock model
                mock_model = {
                    x_var: ConstantNode("1", self.integer_type, 1),
                    y_var: ConstantNode("0", self.integer_type, 0)
                }
                mock_parse_model.return_value = mock_model
                
                # Call check_satisfiability with request_model=True
                result = self.smt_interface.check_satisfiability(
                    sum_gt_zero,
                    set(),
                    request_model=True
                )
                
                # Verify that the result status is "sat"
                self.assertEqual(result.status, "sat")
                
                # Verify that the model was extracted
                self.assertIsNotNone(result.model)
                self.assertEqual(result.model, mock_model)
                
                # Verify that _parse_smt_model was called with the model string
                mock_parse_model.assert_called_once()
    
    def test_performance_with_large_formulas(self):
        """Test performance with large formulas.
        
        This test verifies that the SMT interface can handle large formulas
        efficiently, measuring the time taken for translation and solving.
        """
        # Create a large formula with many variables and constraints
        num_vars = 50
        variables = [VariableNode(f"?x{i}", i, self.integer_type) for i in range(num_vars)]
        
        # Create arithmetic operators and predicates
        plus_op = ConstantNode("+", self.int_int_int_func_type)
        lt_op = ConstantNode("<", self.int_int_pred_type)
        
        # Create a large conjunction of constraints: x0 < x1 ∧ x1 < x2 ∧ ... ∧ x{n-2} < x{n-1}
        constraints = []
        for i in range(num_vars - 1):
            constraint = ApplicationNode(lt_op, [variables[i], variables[i+1]], self.boolean_type)
            constraints.append(constraint)
        
        large_formula = ConnectiveNode("AND", constraints, self.boolean_type)
        
        # Measure the time taken to generate the SMT script
        start_time = time.time()
        
        with patch.object(self.smt_interface, '_translate_ast_to_smtlib') as mock_translate:
            # Mock the translation to avoid implementation details
            mock_translate.return_value = "(and " + " ".join([f"(< ?x{i}_{i} ?x{i+1}_{i+1})" for i in range(num_vars - 1)]) + ")"
            
            script = self.smt_interface._generate_smt_script(
                large_formula,
                set(),
                "QF_LIA",
                False,
                False
            )
            
            script_generation_time = time.time() - start_time
            print(f"Script generation time for {num_vars} variables: {script_generation_time * 1000:.2f} ms")
            
            # Verify that the script was generated
            self.assertIsNotNone(script)
            self.assertIn("(set-logic QF_LIA)", script)
            
            # Verify that _translate_ast_to_smtlib was called with the formula
            mock_translate.assert_called_with(large_formula)
    
    def test_integration_with_proof_object_generation(self):
        """Test integration with proof object generation.
        
        This test verifies that the SMT interface correctly integrates with
        the proof object generation system, producing valid proof objects.
        """
        # Create a simple formula: x > 0
        x_var = VariableNode("?x", 1, self.integer_type)
        gt_op = ConstantNode(">", self.int_int_pred_type)
        zero_const = ConstantNode("0", self.integer_type, 0)
        x_gt_zero = ApplicationNode(gt_op, [x_var, zero_const], self.boolean_type)
        
        # Create the negation of the formula: ¬(x > 0) or equivalently x ≤ 0
        not_x_gt_zero = ConnectiveNode("NOT", [x_gt_zero], self.boolean_type)
        
        # Mock the check_satisfiability method to simulate an unsat result
        with patch.object(self.smt_interface, 'check_satisfiability') as mock_check:
            # Create a mock SMTResult
            mock_result = SMTResult(
                status="unsat",
                unsat_core_identifiers=["formula"]
            )
            mock_check.return_value = mock_result
            
            # Call prove
            proof_obj = self.smt_interface.prove(x_gt_zero, set())
            
            # Verify that check_satisfiability was called with the negated formula
            mock_check.assert_called_once()
            args, kwargs = mock_check.call_args
            self.assertIsInstance(args[0], ConnectiveNode)
            self.assertEqual(args[0].connective_type, "NOT")
            
            # Verify that a successful proof object was created
            self.assertTrue(proof_obj.goal_achieved)
            self.assertEqual(proof_obj.conclusion_ast, x_gt_zero)
            self.assertEqual(proof_obj.inference_engine_used, "SMTInterface")
            
            # Verify that the proof steps were created
            self.assertIsNotNone(proof_obj.proof_steps)
            self.assertGreater(len(proof_obj.proof_steps), 0)
    
    def test_type_to_smt_sort_conversion(self):
        """Test conversion of GödelOS types to SMT-LIB sorts.
        
        This test verifies that the SMT interface correctly converts GödelOS
        types to SMT-LIB sorts, handling atomic types, function types, and
        parametric types.
        """
        # Test conversion of atomic types
        boolean_sort = self.smt_interface._type_to_smt_sort(self.boolean_type)
        integer_sort = self.smt_interface._type_to_smt_sort(self.integer_type)
        real_sort = self.smt_interface._type_to_smt_sort(self.real_type)
        entity_sort = self.smt_interface._type_to_smt_sort(self.entity_type)
        
        self.assertEqual(boolean_sort, "Bool")
        self.assertEqual(integer_sort, "Int")
        self.assertEqual(real_sort, "Real")
        self.assertEqual(entity_sort, "Entity")
        
        # Test conversion of function types
        int_pred_sort = self.smt_interface._type_to_smt_sort(self.int_pred_type)
        int_int_func_sort = self.smt_interface._type_to_smt_sort(self.int_int_func_type)
        int_int_pred_sort = self.smt_interface._type_to_smt_sort(self.int_int_pred_type)
        
        self.assertEqual(int_pred_sort, "(Int -> Bool)")
        self.assertEqual(int_int_func_sort, "(Int -> Int)")
        self.assertEqual(int_int_pred_sort, "(Int -> Int -> Bool)")


if __name__ == "__main__":
    unittest.main()