"""
Unit tests for the ExplanationBasedLearner component.

This module contains tests for the Explanation-Based Learner (EBL) component
of the Learning System.
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Set, Optional

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode, ConnectiveNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.coordinator import InferenceCoordinator
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode
from godelOS.learning_system.explanation_based_learner import (
    ExplanationBasedLearner, 
    OperationalityConfig, 
    GeneralizedExplanation
)


class TestExplanationBasedLearner(unittest.TestCase):
    """Test cases for the ExplanationBasedLearner class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.kr_system_interface = MagicMock(spec=KnowledgeStoreInterface)
        self.inference_engine = MagicMock(spec=InferenceCoordinator)
        
        # Set up type system mock
        self.kr_system_interface.type_system.get_type.side_effect = self._mock_get_type
        
        # Set up unification engine mock
        self.kr_system_interface.unification_engine = MagicMock()
        
        # Create operationality config
        self.op_config = OperationalityConfig(
            operational_predicates={"isHuman", "isMan", "isWoman", "isMortal", "hasAttribute"},
            max_unfolding_depth=2
        )
        
        # Create ExplanationBasedLearner instance
        self.ebl = ExplanationBasedLearner(
            kr_system_interface=self.kr_system_interface,
            inference_engine=self.inference_engine,
            operationality_config=self.op_config
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
            if isinstance(arg, str) and arg.startswith("?"):
                # It's a variable
                digits = ''.join(c for c in arg if c.isdigit())
                var_id = int(digits) if digits else ord(arg[-1])
                var_type = self._mock_get_type("Person")
                arg_nodes.append(VariableNode(arg, var_id, var_type))
            elif isinstance(arg, VariableNode):
                # It's already a VariableNode
                arg_nodes.append(arg)
            else:
                # It's a constant
                const_type = self._mock_get_type("Person")
                arg_nodes.append(ConstantNode(arg, const_type))
        
        return ApplicationNode(predicate_node, arg_nodes, boolean_type)
    
    def _create_proof_object(self, goal, steps, used_axioms=None):
        """Helper method to create a ProofObject."""
        if used_axioms is None:
            used_axioms = set()
            
        return ProofObject(
            goal_achieved=True,
            conclusion_ast=goal,
            status_message="Proved",
            proof_steps=steps,
            used_axioms_rules=used_axioms,
            inference_engine_used="TestProver"
        )
    
    def test_operationality_config(self):
        """Test the OperationalityConfig class."""
        config = OperationalityConfig(
            operational_predicates={"isHuman", "isMan", "isMortal"},
            max_unfolding_depth=3
        )
        
        self.assertTrue(config.is_operational("isHuman"))
        self.assertTrue(config.is_operational("isMan"))
        self.assertTrue(config.is_operational("isMortal"))
        self.assertFalse(config.is_operational("isGreek"))
        self.assertFalse(config.is_operational("isPhilosopher"))
        
        self.assertEqual(config.max_unfolding_depth, 3)
    
    def test_generalized_explanation_to_logic_template(self):
        """Test conversion of a GeneralizedExplanation to a logic template."""
        # Create a simple generalized explanation
        goal = self._create_ast_node("isMortal", ["?p1"])
        premises = [self._create_ast_node("isHuman", ["?p1"])]
        
        gen_explanation = GeneralizedExplanation(
            goal=goal,
            premises=premises
        )
        
        # Convert to logic template
        template = gen_explanation.to_logic_template()
        
        # Verify that the template is an implication
        self.assertIsInstance(template, ConnectiveNode)
        self.assertEqual(template.connective_type, "IMPLIES")
        self.assertEqual(len(template.operands), 2)
        
        # Verify that the body and head are correct
        self.assertEqual(template.operands[0], premises[0])
        self.assertEqual(template.operands[1], goal)
        
        # Test with multiple premises
        premises.append(self._create_ast_node("hasAttribute", ["?p1", "rational"]))
        gen_explanation = GeneralizedExplanation(
            goal=goal,
            premises=premises
        )
        
        template = gen_explanation.to_logic_template()
        
        # Verify that the template is an implication
        self.assertIsInstance(template, ConnectiveNode)
        self.assertEqual(template.connective_type, "IMPLIES")
        
        # Verify that the body is a conjunction
        body = template.operands[0]
        self.assertIsInstance(body, ConnectiveNode)
        self.assertEqual(body.connective_type, "AND")
        self.assertEqual(len(body.operands), 2)
        
        # Verify that the head is correct
        self.assertEqual(template.operands[1], goal)
    
    def test_identify_constants(self):
        """Test the _identify_constants method."""
        # Create an AST node with constants
        ast_node = self._create_ast_node("isPhilosopher", ["Socrates"])
        
        # Identify constants
        constants = self.ebl._identify_constants(ast_node)
        
        # Verify that Socrates is identified as a constant
        self.assertIn("Socrates", constants)
        self.assertIsInstance(constants["Socrates"], ConstantNode)
        self.assertEqual(constants["Socrates"].name, "Socrates")
        
        # Test with multiple constants
        ast_node = self._create_ast_node("teaches", ["Socrates", "Plato"])
        constants = self.ebl._identify_constants(ast_node)
        
        self.assertIn("Socrates", constants)
        self.assertIn("Plato", constants)
        
        # Test with a ConnectiveNode
        premise1 = self._create_ast_node("isPhilosopher", ["Socrates"])
        premise2 = self._create_ast_node("isGreek", ["Socrates"])
        
        connective = ConnectiveNode(
            connective_type="AND",
            operands=[premise1, premise2],
            type_ref=premise1.type
        )
        
        constants = self.ebl._identify_constants(connective)
        
        self.assertIn("Socrates", constants)
        self.assertEqual(len(constants), 1)  # Socrates appears twice but should be counted once
    
    def test_variabilize_ast(self):
        """Test the _variabilize_ast method."""
        # Create an AST node with constants
        ast_node = self._create_ast_node("isPhilosopher", ["Socrates"])
        
        # Create a mapping from constants to variables
        var_type = self._mock_get_type("Person")
        variable = VariableNode("?p1", 1, var_type)
        constant_to_variable_map = {"Socrates": variable}
        
        # Variabilize the AST node
        variabilized = self.ebl._variabilize_ast(ast_node, constant_to_variable_map)
        
        # Verify that the constant was replaced with the variable
        self.assertIsInstance(variabilized, ApplicationNode)
        self.assertEqual(len(variabilized.arguments), 1)
        self.assertIsInstance(variabilized.arguments[0], VariableNode)
        self.assertEqual(variabilized.arguments[0].name, "?p1")
        
        # Test with a ConnectiveNode
        premise1 = self._create_ast_node("isPhilosopher", ["Socrates"])
        premise2 = self._create_ast_node("isGreek", ["Socrates"])
        
        connective = ConnectiveNode(
            connective_type="AND",
            operands=[premise1, premise2],
            type_ref=premise1.type
        )
        
        variabilized = self.ebl._variabilize_ast(connective, constant_to_variable_map)
        
        self.assertIsInstance(variabilized, ConnectiveNode)
        self.assertEqual(variabilized.connective_type, "AND")
        self.assertEqual(len(variabilized.operands), 2)
        
        # Verify that both occurrences of Socrates were replaced
        self.assertIsInstance(variabilized.operands[0].arguments[0], VariableNode)
        self.assertEqual(variabilized.operands[0].arguments[0].name, "?p1")
        self.assertIsInstance(variabilized.operands[1].arguments[0], VariableNode)
        self.assertEqual(variabilized.operands[1].arguments[0].name, "?p1")
    
    def test_is_operational(self):
        """Test the _is_operational method."""
        # Create an operational predicate
        operational_node = self._create_ast_node("isHuman", ["?p1"])
        
        # Create a non-operational predicate
        non_operational_node = self._create_ast_node("isGreek", ["?p1"])
        
        # Test operationality
        self.assertTrue(self.ebl._is_operational(operational_node))
        self.assertFalse(self.ebl._is_operational(non_operational_node))
        
        # Test with a ConnectiveNode
        connective = ConnectiveNode(
            connective_type="AND",
            operands=[operational_node, operational_node],
            type_ref=operational_node.type
        )
        
        self.assertTrue(self.ebl._is_operational(connective))
        
        mixed_connective = ConnectiveNode(
            connective_type="AND",
            operands=[operational_node, non_operational_node],
            type_ref=operational_node.type
        )
        
        self.assertFalse(self.ebl._is_operational(mixed_connective))
    
    def test_generalize_from_proof_object_simple(self):
        """Test generalization from a simple proof object."""
        # Create a simple proof for "isMortal(Socrates)" based on "isHuman(Socrates)"
        goal = self._create_ast_node("isMortal", ["Socrates"])
        
        # Create proof steps
        step0 = ProofStepNode(
            formula=self._create_ast_node("isHuman", ["Socrates"]),
            rule_name="Axiom",
            premises=[]
        )
        
        step1 = ProofStepNode(
            formula=goal,
            rule_name="Modus Ponens",
            premises=[0]
        )
        
        proof_steps = [step0, step1]
        
        # Create a rule that was used in the proof
        rule = ConnectiveNode(
            connective_type="IMPLIES",
            operands=[
                self._create_ast_node("isHuman", ["?x"]),
                self._create_ast_node("isMortal", ["?x"])
            ],
            type_ref=self._mock_get_type("Boolean")
        )
        
        used_axioms = {
            self._create_ast_node("isHuman", ["Socrates"]),
            rule
        }
        
        proof_object = self._create_proof_object(goal, proof_steps, used_axioms)
        
        # Mock the extract_explanation method to return our proof steps
        with patch.object(self.ebl, '_extract_explanation', return_value={0: step0, 1: step1}):
            # Mock the identify_leaf_steps method to return step0
            with patch.object(self.ebl, '_identify_leaf_steps', return_value=[0]):
                # Call generalize_from_proof_object
                result = self.ebl.generalize_from_proof_object(proof_object)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ConnectiveNode)
        self.assertEqual(result.connective_type, "IMPLIES")
        
        # Verify that the rule has been generalized
        body = result.operands[0]
        head = result.operands[1]
        
        self.assertIsInstance(body, ApplicationNode)
        self.assertIsInstance(body.operator, ConstantNode)
        self.assertEqual(body.operator.name, "isHuman")
        
        self.assertIsInstance(head, ApplicationNode)
        self.assertIsInstance(head.operator, ConstantNode)
        self.assertEqual(head.operator.name, "isMortal")
        
        # Verify that the constant has been replaced with a variable
        self.assertIsInstance(body.arguments[0], VariableNode)
        self.assertIsInstance(head.arguments[0], VariableNode)
        
        # Verify that the same variable is used in both places
        self.assertEqual(body.arguments[0].name, head.arguments[0].name)
    
    def test_generalize_from_proof_object_complex(self):
        """Test generalization from a more complex proof object."""
        # Create a proof for "isGreekPhilosopher(Socrates)" based on "isGreek(Socrates)" and "isPhilosopher(Socrates)"
        goal = self._create_ast_node("isGreekPhilosopher", ["Socrates"])
        
        # Create proof steps
        step0 = ProofStepNode(
            formula=self._create_ast_node("isGreek", ["Socrates"]),
            rule_name="Axiom",
            premises=[]
        )
        
        step1 = ProofStepNode(
            formula=self._create_ast_node("isPhilosopher", ["Socrates"]),
            rule_name="Axiom",
            premises=[]
        )
        
        step2 = ProofStepNode(
            formula=goal,
            rule_name="Conjunction Elimination",
            premises=[0, 1]
        )
        
        proof_steps = [step0, step1, step2]
        
        # Create rules that were used in the proof
        rule = ConnectiveNode(
            connective_type="IMPLIES",
            operands=[
                ConnectiveNode(
                    connective_type="AND",
                    operands=[
                        self._create_ast_node("isGreek", ["?x"]),
                        self._create_ast_node("isPhilosopher", ["?x"])
                    ],
                    type_ref=self._mock_get_type("Boolean")
                ),
                self._create_ast_node("isGreekPhilosopher", ["?x"])
            ],
            type_ref=self._mock_get_type("Boolean")
        )
        
        used_axioms = {
            self._create_ast_node("isGreek", ["Socrates"]),
            self._create_ast_node("isPhilosopher", ["Socrates"]),
            rule
        }
        
        proof_object = self._create_proof_object(goal, proof_steps, used_axioms)
        
        # Mock the extract_explanation method to return our proof steps
        with patch.object(self.ebl, '_extract_explanation', return_value={0: step0, 1: step1, 2: step2}):
            # Mock the identify_leaf_steps method to return step0 and step1
            with patch.object(self.ebl, '_identify_leaf_steps', return_value=[0, 1]):
                # Mock the unfolding process to make isGreek and isPhilosopher operational
                with patch.object(self.ebl, '_is_operational', side_effect=lambda x: True):
                    # Call generalize_from_proof_object
                    result = self.ebl.generalize_from_proof_object(proof_object)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ConnectiveNode)
        self.assertEqual(result.connective_type, "IMPLIES")
        
        # Verify that the rule has been generalized
        body = result.operands[0]
        head = result.operands[1]
        
        # The body should be a conjunction of isGreek and isPhilosopher
        self.assertIsInstance(body, ConnectiveNode)
        self.assertEqual(body.connective_type, "AND")
        self.assertEqual(len(body.operands), 2)
        
        # Verify the head
        self.assertIsInstance(head, ApplicationNode)
        self.assertIsInstance(head.operator, ConstantNode)
        self.assertEqual(head.operator.name, "isGreekPhilosopher")
        
        # Verify that the constant has been replaced with a variable
        self.assertIsInstance(head.arguments[0], VariableNode)
        
        # Verify that the same variable is used in all places
        var_name = head.arguments[0].name
        self.assertIsInstance(body.operands[0].arguments[0], VariableNode)
        self.assertEqual(body.operands[0].arguments[0].name, var_name)
        self.assertIsInstance(body.operands[1].arguments[0], VariableNode)
        self.assertEqual(body.operands[1].arguments[0].name, var_name)
    
    def test_generalize_from_unsuccessful_proof(self):
        """Test that generalization fails for unsuccessful proofs."""
        # Create an unsuccessful proof
        goal = self._create_ast_node("isMortal", ["Socrates"])
        
        proof_object = ProofObject(
            goal_achieved=False,
            conclusion_ast=None,
            status_message="Failed",
            proof_steps=[],
            used_axioms_rules=set(),
            inference_engine_used="TestProver"
        )
        
        # Call generalize_from_proof_object
        result = self.ebl.generalize_from_proof_object(proof_object)
        
        # Verify that generalization failed
        self.assertIsNone(result)
    
    def test_ensure_operationality(self):
        """Test the _ensure_operationality method."""
        # Create a generalized explanation with non-operational premises
        goal = self._create_ast_node("isMortal", ["?p1"])
        non_operational_premise = self._create_ast_node("isGreek", ["?p1"])
        
        gen_explanation = GeneralizedExplanation(
            goal=goal,
            premises=[non_operational_premise]
        )
        
        # Mock the _is_operational method to return False for isGreek
        with patch.object(self.ebl, '_is_operational', side_effect=lambda x: x.operator.name != "isGreek"):
            # Mock the _unfold_premise method to return operational premises
            operational_premise = self._create_ast_node("isHuman", ["?p1"])
            with patch.object(self.ebl, '_unfold_premise', return_value=[operational_premise]):
                # Call _ensure_operationality
                result = self.ebl._ensure_operationality(gen_explanation)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result.goal, goal)
        self.assertEqual(len(result.premises), 1)
        self.assertEqual(result.premises[0], operational_premise)
    
    def test_unfold_premise(self):
        """Test the _unfold_premise method."""
        # Create a non-operational premise
        premise = self._create_ast_node("isGreek", ["?p1"])
        
        # Create a mapping from constants to variables
        var_type = self._mock_get_type("Person")
        variable = VariableNode("?p1", 1, var_type)
        constant_to_variable_map = {"Socrates": variable}
        
        # Mock the knowledge store query to return a definition
        definition = ConnectiveNode(
            connective_type="IMPLIES",
            operands=[
                self._create_ast_node("livesIn", ["?x", "Greece"]),
                self._create_ast_node("isGreek", ["?x"])
            ],
            type_ref=self._mock_get_type("Boolean")
        )
        mock_binding = MagicMock()
        mock_binding.get.return_value = definition
        self.kr_system_interface.query_statements_match_pattern.return_value = [mock_binding]
        
        # Mock the unification engine to return successful unification
        # var_id for "?x" is ord('x')=120 since it has no digits
        var_x_id = ord('x')
        var_x = VariableNode("?x", var_x_id, var_type)
        self.kr_system_interface.unification_engine.unify.return_value = (
            {var_x_id: variable},  # Bindings
            []  # No errors
        )
        
        # Call _unfold_premise
        result = self.ebl._unfold_premise(premise, constant_to_variable_map)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ApplicationNode)
        self.assertEqual(result[0].operator.name, "livesIn")
        self.assertEqual(len(result[0].arguments), 2)
        self.assertEqual(result[0].arguments[0], variable)
        self.assertEqual(result[0].arguments[1].name, "Greece")


if __name__ == '__main__':
    unittest.main()