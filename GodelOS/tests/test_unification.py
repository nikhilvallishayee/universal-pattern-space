"""
Tests for the Unification Engine.

This module contains comprehensive tests for the UnificationEngine, covering
both first-order and higher-order unification for all AST node types.
"""

import unittest

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import (
    ConstantNode, VariableNode, ApplicationNode, ConnectiveNode,
    QuantifierNode, ModalOpNode, LambdaNode, DefinitionNode
)
from godelOS.core_kr.type_system.types import FunctionType
from godelOS.core_kr.unification_engine.engine import UnificationEngine, Error


class TestUnificationEngine(unittest.TestCase):
    """Test cases for the UnificationEngine."""
    
    def setUp(self):
        """Set up the test case."""
        self.type_system = TypeSystemManager()
        self.unification_engine = UnificationEngine(self.type_system)
        
        # Get basic types
        self.entity_type = self.type_system.get_type("Entity")
        self.boolean_type = self.type_system.get_type("Boolean")
        
        # Create a function type (Entity -> Boolean)
        self.function_type = FunctionType([self.entity_type], self.boolean_type)
        
        # Create some constants
        self.socrates = ConstantNode("Socrates", self.entity_type)
        self.plato = ConstantNode("Plato", self.entity_type)
        
        # Create predicates
        self.human_pred = ConstantNode("Human", self.function_type)
        self.mortal_pred = ConstantNode("Mortal", self.function_type)
        
        # Create variables
        self.var_x = VariableNode("?x", 1, self.entity_type)
        self.var_y = VariableNode("?y", 2, self.entity_type)
        self.var_z = VariableNode("?z", 3, self.entity_type)
        self.var_p = VariableNode("?P", 4, self.function_type)
    
    def test_constant_unification(self):
        """Test unification of constants."""
        # Unify identical constants
        bindings, errors = self.unification_engine.unify(self.socrates, self.socrates)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 0)
        self.assertEqual(len(errors), 0)
        
        # Unify different constants
        bindings, errors = self.unification_engine.unify(self.socrates, self.plato)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
    
    def test_variable_constant_unification(self):
        """Test unification of variables with constants."""
        # Unify variable with constant
        bindings, errors = self.unification_engine.unify(self.var_x, self.socrates)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(bindings[self.var_x.var_id], self.socrates)
        
        # Unify constant with variable
        bindings, errors = self.unification_engine.unify(self.socrates, self.var_x)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(bindings[self.var_x.var_id], self.socrates)
    
    def test_variable_variable_unification(self):
        """Test unification of variables with variables."""
        # Unify two different variables
        bindings, errors = self.unification_engine.unify(self.var_x, self.var_y)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(errors), 0)
        
        # Unify a variable with itself
        bindings, errors = self.unification_engine.unify(self.var_x, self.var_x)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 0)
        self.assertEqual(len(errors), 0)
        
        # Test transitive unification
        # First, bind x to y
        bindings1, errors1 = self.unification_engine.unify(self.var_x, self.var_y)
        self.assertIsNotNone(bindings1)
        
        # Then, bind y to z with the existing bindings
        bindings2, errors2 = self.unification_engine.unify(self.var_y, self.var_z, bindings1)
        self.assertIsNotNone(bindings2)
        
        # Finally, check that x is bound to z
        self.assertEqual(bindings2[self.var_x.var_id], self.var_z)
    
    def test_application_unification(self):
        """Test unification of application nodes."""
        # Create applications
        human_socrates = ApplicationNode(self.human_pred, [self.socrates], self.boolean_type)
        human_plato = ApplicationNode(self.human_pred, [self.plato], self.boolean_type)
        mortal_socrates = ApplicationNode(self.mortal_pred, [self.socrates], self.boolean_type)
        
        # Create variable applications
        human_var_x = ApplicationNode(self.human_pred, [self.var_x], self.boolean_type)
        pred_var_socrates = ApplicationNode(self.var_p, [self.socrates], self.boolean_type)
        
        # Unify identical applications
        bindings, errors = self.unification_engine.unify(human_socrates, human_socrates)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 0)
        self.assertEqual(len(errors), 0)
        
        # Unify different applications with same predicate
        bindings, errors = self.unification_engine.unify(human_socrates, human_plato)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
        
        # Unify different applications with different predicates
        bindings, errors = self.unification_engine.unify(human_socrates, mortal_socrates)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
        
        # Unify variable application with constant application (argument variable)
        bindings, errors = self.unification_engine.unify(human_var_x, human_socrates)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(bindings[self.var_x.var_id], self.socrates)
        
        # Unify variable application with constant application (predicate variable)
        bindings, errors = self.unification_engine.unify(pred_var_socrates, human_socrates)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(bindings[self.var_p.var_id], self.human_pred)
    
    def test_occurs_check(self):
        """Test the occurs check for first-order unification."""
        # Create an application with a variable
        human_var_y = ApplicationNode(self.human_pred, [self.var_y], self.boolean_type)
        
        # Create a nested application with the same variable
        nested_app = ApplicationNode(
            self.human_pred,
            [ApplicationNode(self.human_pred, [self.var_x], self.boolean_type)],
            self.boolean_type
        )
        
        # Unify variable with application containing the same variable (should fail)
        bindings, errors = self.unification_engine.unify(self.var_x, nested_app)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
        print(f"Errors: {errors}")
        
        # Create a simple application with a different variable
        bindings, errors = self.unification_engine.unify(self.var_x, self.var_y)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(bindings[self.var_x.var_id], self.var_y)
    
    def test_connective_unification(self):
        """Test unification of connective nodes."""
        # Create atomic formulas
        human_socrates = ApplicationNode(self.human_pred, [self.socrates], self.boolean_type)
        mortal_socrates = ApplicationNode(self.mortal_pred, [self.socrates], self.boolean_type)
        human_plato = ApplicationNode(self.human_pred, [self.plato], self.boolean_type)
        human_var_x = ApplicationNode(self.human_pred, [self.var_x], self.boolean_type)
        
        # Create connectives
        and_conn1 = ConnectiveNode("AND", [human_socrates, mortal_socrates], self.boolean_type)
        and_conn2 = ConnectiveNode("AND", [human_socrates, mortal_socrates], self.boolean_type)
        and_conn3 = ConnectiveNode("AND", [human_plato, mortal_socrates], self.boolean_type)
        and_conn_var = ConnectiveNode("AND", [human_var_x, mortal_socrates], self.boolean_type)
        or_conn = ConnectiveNode("OR", [human_socrates, mortal_socrates], self.boolean_type)
        
        # Unify identical connectives
        bindings, errors = self.unification_engine.unify(and_conn1, and_conn2)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 0)
        self.assertEqual(len(errors), 0)
        
        # Unify different connective types
        bindings, errors = self.unification_engine.unify(and_conn1, or_conn)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
        
        # Unify connectives with different operands
        bindings, errors = self.unification_engine.unify(and_conn1, and_conn3)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
        
        # Unify connectives with variables
        bindings, errors = self.unification_engine.unify(and_conn_var, and_conn1)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(bindings[self.var_x.var_id], self.socrates)
    
    def test_quantifier_unification(self):
        """Test unification of quantifier nodes."""
        # Create bound variables
        bound_var1 = VariableNode("?x", 5, self.entity_type)
        bound_var2 = VariableNode("?y", 6, self.entity_type)
        
        # Create formulas with bound variables
        human_bound_var1 = ApplicationNode(self.human_pred, [bound_var1], self.boolean_type)
        human_bound_var2 = ApplicationNode(self.human_pred, [bound_var2], self.boolean_type)
        
        # Create quantifiers
        forall1 = QuantifierNode("FORALL", [bound_var1], human_bound_var1, self.boolean_type)
        forall2 = QuantifierNode("FORALL", [bound_var2], human_bound_var2, self.boolean_type)
        exists = QuantifierNode("EXISTS", [bound_var1], human_bound_var1, self.boolean_type)
        
        # Unify alpha-equivalent quantifiers
        bindings, errors = self.unification_engine.unify(forall1, forall2)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(errors), 0)
        
        # Unify different quantifier types
        bindings, errors = self.unification_engine.unify(forall1, exists)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
    
    def test_modal_op_unification(self):
        """Test unification of modal operator nodes."""
        # Create formulas
        human_socrates = ApplicationNode(self.human_pred, [self.socrates], self.boolean_type)
        human_plato = ApplicationNode(self.human_pred, [self.plato], self.boolean_type)
        human_var_x = ApplicationNode(self.human_pred, [self.var_x], self.boolean_type)
        
        # Create agents
        agent1 = ConstantNode("Agent1", self.entity_type)
        agent2 = ConstantNode("Agent2", self.entity_type)
        
        # Create modal operators
        knows1 = ModalOpNode("KNOWS", human_socrates, self.boolean_type, agent1)
        knows2 = ModalOpNode("KNOWS", human_socrates, self.boolean_type, agent1)
        knows3 = ModalOpNode("KNOWS", human_plato, self.boolean_type, agent1)
        knows4 = ModalOpNode("KNOWS", human_socrates, self.boolean_type, agent2)
        knows_var = ModalOpNode("KNOWS", human_var_x, self.boolean_type, agent1)
        believes = ModalOpNode("BELIEVES", human_socrates, self.boolean_type, agent1)
        
        # Unify identical modal operators
        bindings, errors = self.unification_engine.unify(knows1, knows2)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 0)
        self.assertEqual(len(errors), 0)
        
        # Unify different modal operator types
        bindings, errors = self.unification_engine.unify(knows1, believes)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
        
        # Unify modal operators with different propositions
        bindings, errors = self.unification_engine.unify(knows1, knows3)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
        
        # Unify modal operators with different agents
        bindings, errors = self.unification_engine.unify(knows1, knows4)
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
        
        # Unify modal operators with variables
        bindings, errors = self.unification_engine.unify(knows_var, knows1)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(bindings[self.var_x.var_id], self.socrates)
    
    def test_lambda_unification(self):
        """Test unification of lambda nodes (higher-order unification)."""
        # Create bound variables
        bound_var1 = VariableNode("?x", 5, self.entity_type)
        bound_var2 = VariableNode("?y", 6, self.entity_type)
        
        # Create lambda bodies
        human_bound_var1 = ApplicationNode(self.human_pred, [bound_var1], self.boolean_type)
        human_bound_var2 = ApplicationNode(self.human_pred, [bound_var2], self.boolean_type)
        mortal_bound_var1 = ApplicationNode(self.mortal_pred, [bound_var1], self.boolean_type)
        
        # Create lambda nodes
        lambda1 = LambdaNode([bound_var1], human_bound_var1, self.function_type)
        lambda2 = LambdaNode([bound_var2], human_bound_var2, self.function_type)
        lambda3 = LambdaNode([bound_var1], mortal_bound_var1, self.function_type)
        
        # Unify alpha-equivalent lambda nodes
        bindings, errors = self.unification_engine.unify(lambda1, lambda2, mode="HIGHER_ORDER")
        self.assertIsNotNone(bindings)
        self.assertEqual(len(errors), 0)
        
        # Unify different lambda nodes
        bindings, errors = self.unification_engine.unify(lambda1, lambda3, mode="HIGHER_ORDER")
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
        
        # Test that lambda unification requires HIGHER_ORDER mode
        bindings, errors = self.unification_engine.unify(lambda1, lambda2, mode="FIRST_ORDER")
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
    
    def test_definition_unification(self):
        """Test unification of definition nodes."""
        # Create definitions
        def1 = DefinitionNode(
            "Mortal",
            self.function_type,
            LambdaNode([self.var_x], ApplicationNode(self.mortal_pred, [self.var_x], self.boolean_type), self.function_type),
            self.function_type
        )
        
        def2 = DefinitionNode(
            "Mortal",
            self.function_type,
            LambdaNode([self.var_y], ApplicationNode(self.mortal_pred, [self.var_y], self.boolean_type), self.function_type),
            self.function_type
        )
        
        def3 = DefinitionNode(
            "Human",
            self.function_type,
            LambdaNode([self.var_x], ApplicationNode(self.human_pred, [self.var_x], self.boolean_type), self.function_type),
            self.function_type
        )
        
        # Unify alpha-equivalent definitions
        bindings, errors = self.unification_engine.unify(def1, def2, mode="HIGHER_ORDER")
        self.assertIsNotNone(bindings)
        self.assertEqual(len(errors), 0)
        
        # Unify different definitions
        bindings, errors = self.unification_engine.unify(def1, def3, mode="HIGHER_ORDER")
        self.assertIsNone(bindings)
        self.assertGreater(len(errors), 0)
    
    def test_higher_order_unification(self):
        """Test higher-order unification with variables in function positions."""
        # Create a higher-order variable
        var_f = VariableNode("?F", 7, self.function_type)
        
        # Create applications with the higher-order variable
        app_var_f = ApplicationNode(var_f, [self.socrates], self.boolean_type)
        
        # Create concrete applications
        human_socrates = ApplicationNode(self.human_pred, [self.socrates], self.boolean_type)
        
        # Unify variable application with concrete application
        bindings, errors = self.unification_engine.unify(app_var_f, human_socrates, mode="HIGHER_ORDER")
        self.assertIsNotNone(bindings)
        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(bindings[var_f.var_id], self.human_pred)


if __name__ == '__main__':
    unittest.main()