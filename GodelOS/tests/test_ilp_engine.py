"""
Unit tests for the ILPEngine component.

This module contains tests for the Inductive Logic Programming Engine (ILPEngine)
component of the Learning System.
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Set

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode, ConnectiveNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.coordinator import InferenceCoordinator
from godelOS.inference_engine.proof_object import ProofObject
from godelOS.learning_system.ilp_engine import ILPEngine, LanguageBias, ModeDeclaration, Clause


class TestILPEngine(unittest.TestCase):
    """Test cases for the ILPEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.kr_system_interface = MagicMock(spec=KnowledgeStoreInterface)
        self.inference_engine = MagicMock(spec=InferenceCoordinator)
        
        # Set up type system mock
        self.kr_system_interface.type_system.get_type.side_effect = self._mock_get_type
        
        # Create ILPEngine instance with language bias
        self.language_bias = LanguageBias(
            max_clause_length=3,
            max_variables=5,
            allow_recursion=False
        )
        
        # Add mode declarations
        person_type = self._mock_get_type("Person")
        
        parent_mode = ModeDeclaration(
            predicate_name="parent",
            arg_modes=["+", "-"],
            arg_types=["Person", "Person"]
        )
        
        father_mode = ModeDeclaration(
            predicate_name="father",
            arg_modes=["+", "-"],
            arg_types=["Person", "Person"]
        )
        
        mother_mode = ModeDeclaration(
            predicate_name="mother",
            arg_modes=["+", "-"],
            arg_types=["Person", "Person"]
        )
        
        self.language_bias.add_mode_declaration(parent_mode)
        self.language_bias.add_mode_declaration(father_mode)
        self.language_bias.add_mode_declaration(mother_mode)
        
        self.ilp_engine = ILPEngine(
            kr_system_interface=self.kr_system_interface,
            inference_engine=self.inference_engine,
            language_bias=self.language_bias
        )
    
    def _mock_get_type(self, type_name):
        """Mock implementation of type_system.get_type."""
        mock_type = MagicMock()
        mock_type.name = type_name
        return mock_type
    
    def _create_ast_node(self, predicate, args):
        """Helper method to create an ApplicationNode."""
        predicate_type = self._mock_get_type("Predicate")
        boolean_type = self._mock_get_type("Boolean")
        
        predicate_node = ConstantNode(predicate, predicate_type)
        arg_nodes = []
        
        for arg in args:
            if arg.startswith("?"):
                # It's a variable
                var_id = int(arg[2:])  # Extract ID from "?V1", "?V2", etc.
                var_type = self._mock_get_type("Person")
                arg_nodes.append(VariableNode(arg, var_id, var_type))
            else:
                # It's a constant
                const_type = self._mock_get_type("Person")
                arg_nodes.append(ConstantNode(arg, const_type))
        
        return ApplicationNode(predicate_node, arg_nodes, boolean_type)
    
    def test_mode_declaration_validation(self):
        """Test that mode declarations are properly validated."""
        # Test valid mode declaration
        valid_mode = ModeDeclaration(
            predicate_name="test",
            arg_modes=["+", "-", "#"],
            arg_types=["Type1", "Type2", "Type3"]
        )
        self.assertEqual(valid_mode.predicate_name, "test")
        
        # Test invalid mode declaration (mismatched arg_modes and arg_types)
        with self.assertRaises(ValueError):
            ModeDeclaration(
                predicate_name="test",
                arg_modes=["+", "-"],
                arg_types=["Type1"]
            )
        
        # Test invalid mode declaration (invalid arg_mode)
        with self.assertRaises(ValueError):
            ModeDeclaration(
                predicate_name="test",
                arg_modes=["+", "x"],
                arg_types=["Type1", "Type2"]
            )
    
    def test_clause_to_ast(self):
        """Test conversion of a Clause to an AST_Node."""
        # Create a simple clause: parent(X, Y) :- father(X, Y)
        head = self._create_ast_node("parent", ["?V1", "?V2"])
        body = [self._create_ast_node("father", ["?V1", "?V2"])]
        
        clause = Clause(head=head, body=body)
        clause_ast = clause.to_ast()
        
        # Verify that the AST is an implication
        self.assertIsInstance(clause_ast, ConnectiveNode)
        self.assertEqual(clause_ast.connective_type, "IMPLIES")
        self.assertEqual(len(clause_ast.operands), 2)
        
        # Verify that the head and body are correct
        self.assertEqual(clause_ast.operands[1], head)
        self.assertEqual(clause_ast.operands[0], body[0])
        
        # Test a clause with an empty body
        empty_body_clause = Clause(head=head)
        empty_body_ast = empty_body_clause.to_ast()
        
        # Verify that the AST is just the head
        self.assertEqual(empty_body_ast, head)
        
        # Test a clause with multiple body literals
        multi_body = body + [self._create_ast_node("mother", ["?V3", "?V2"])]
        multi_body_clause = Clause(head=head, body=multi_body)
        multi_body_ast = multi_body_clause.to_ast()
        
        # Verify that the AST is an implication with a conjunction in the body
        self.assertIsInstance(multi_body_ast, ConnectiveNode)
        self.assertEqual(multi_body_ast.connective_type, "IMPLIES")
        self.assertEqual(len(multi_body_ast.operands), 2)
        
        body_conjunction = multi_body_ast.operands[0]
        self.assertIsInstance(body_conjunction, ConnectiveNode)
        self.assertEqual(body_conjunction.connective_type, "AND")
        self.assertEqual(len(body_conjunction.operands), 2)
    
    def test_check_coverage(self):
        """Test the _check_coverage method."""
        # Create a clause and an example
        clause_ast = self._create_ast_node("parent", ["john", "bob"])
        example_ast = self._create_ast_node("parent", ["john", "bob"])
        background_knowledge = set()
        
        # Mock the inference engine's submit_goal method
        proof_result = ProofObject.create_success(example_ast)
        self.inference_engine.submit_goal.return_value = proof_result
        
        # Check coverage
        result = self.ilp_engine._check_coverage(clause_ast, example_ast, background_knowledge)
        
        # Verify that the inference engine was called correctly
        self.inference_engine.submit_goal.assert_called_once()
        call_args = self.inference_engine.submit_goal.call_args[0]
        self.assertEqual(call_args[0], example_ast)
        self.assertIn(clause_ast, call_args[1])
        
        # Verify the result
        self.assertTrue(result)
        
        # Test negative coverage
        self.inference_engine.submit_goal.reset_mock()
        proof_result = ProofObject.create_failure("Not proved")
        self.inference_engine.submit_goal.return_value = proof_result
        
        result = self.ilp_engine._check_coverage(clause_ast, example_ast, background_knowledge)
        
        self.assertFalse(result)
    
    def test_is_redundant(self):
        """Test the _is_redundant method."""
        # Create a clause with duplicate literals
        head = self._create_ast_node("parent", ["?V1", "?V2"])
        body = [
            self._create_ast_node("father", ["?V1", "?V2"]),
            self._create_ast_node("father", ["?V1", "?V2"])
        ]
        
        redundant_clause = Clause(head=head, body=body)
        
        # Test redundancy check
        self.assertTrue(self.ilp_engine._is_redundant(redundant_clause))
        
        # Create a non-redundant clause
        non_redundant_body = [
            self._create_ast_node("father", ["?V1", "?V2"]),
            self._create_ast_node("mother", ["?V3", "?V2"])
        ]
        
        non_redundant_clause = Clause(head=head, body=non_redundant_body)
        
        # Test redundancy check
        self.assertFalse(self.ilp_engine._is_redundant(non_redundant_clause))
    
    def test_contains_recursion(self):
        """Test the _contains_recursion method."""
        # Create a recursive clause: parent(X, Y) :- parent(X, Z)
        head = self._create_ast_node("parent", ["?V1", "?V2"])
        recursive_body = [self._create_ast_node("parent", ["?V1", "?V3"])]
        
        recursive_clause = Clause(head=head, body=recursive_body)
        
        # Test recursion check
        self.assertTrue(self.ilp_engine._contains_recursion(recursive_clause))
        
        # Create a non-recursive clause
        non_recursive_body = [self._create_ast_node("father", ["?V1", "?V2"])]
        
        non_recursive_clause = Clause(head=head, body=non_recursive_body)
        
        # Test recursion check
        self.assertFalse(self.ilp_engine._contains_recursion(non_recursive_clause))
    
    @patch('godelOS.learning_system.ilp_engine.ILPEngine._get_background_knowledge')
    @patch('godelOS.learning_system.ilp_engine.ILPEngine._find_best_clause')
    def test_induce_rules(self, mock_find_best_clause, mock_get_background_knowledge):
        """Test the induce_rules method."""
        # Set up test data
        target_predicate = self._create_ast_node("grandparent", ["?V1", "?V2"])
        
        positive_examples = {
            self._create_ast_node("grandparent", ["john", "alice"]),
            self._create_ast_node("grandparent", ["mary", "bob"])
        }
        
        negative_examples = {
            self._create_ast_node("grandparent", ["bob", "john"]),
            self._create_ast_node("grandparent", ["alice", "mary"])
        }
        
        background_knowledge = {
            self._create_ast_node("parent", ["john", "bob"]),
            self._create_ast_node("parent", ["bob", "alice"]),
            self._create_ast_node("parent", ["mary", "alice"]),
            self._create_ast_node("parent", ["alice", "bob"])
        }
        
        # Mock _get_background_knowledge to return our test data
        mock_get_background_knowledge.return_value = background_knowledge
        
        # Create a mock clause and its AST representation
        clause1 = Clause(
            head=target_predicate,
            body=[
                self._create_ast_node("parent", ["?V1", "?V3"]),
                self._create_ast_node("parent", ["?V3", "?V2"])
            ]
        )
        
        clause1_ast = clause1.to_ast()
        
        # Mock _find_best_clause to return our test clause once, then None
        mock_find_best_clause.side_effect = [clause1, None]
        
        # Mock _get_coverage to simulate that clause1 covers all positive examples
        with patch('godelOS.learning_system.ilp_engine.ILPEngine._get_coverage') as mock_get_coverage:
            mock_get_coverage.return_value = (positive_examples, set())
            
            # Call induce_rules
            result = self.ilp_engine.induce_rules(
                target_predicate_signature=target_predicate,
                positive_examples=positive_examples,
                negative_examples=negative_examples,
                background_context_id="TRUTHS"
            )
        
        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], clause1_ast)
        
        # Verify that _find_best_clause was called with the correct arguments
        mock_find_best_clause.assert_called_with(
            target_predicate,
            positive_examples,
            negative_examples,
            background_knowledge
        )
        
        # Verify that _get_background_knowledge was called with the correct context ID
        mock_get_background_knowledge.assert_called_with("TRUTHS")


if __name__ == '__main__':
    unittest.main()