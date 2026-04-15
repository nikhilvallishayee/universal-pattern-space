"""
Tests for the AST module.
"""

import unittest

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import (
    AST_Node, ASTVisitor, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode, LambdaNode, DefinitionNode
)
from typing import Dict, List, TypeVar, Generic

T = TypeVar('T')


class TestASTNodes(unittest.TestCase):
    """Test cases for AST nodes."""
    
    def setUp(self):
        """Set up the test case."""
        self.type_system = TypeSystemManager()
        self.entity_type = self.type_system.get_type("Entity")
        self.boolean_type = self.type_system.get_type("Boolean")
    
    def test_constant_node(self):
        """Test ConstantNode."""
        # Create a constant node
        const = ConstantNode("Socrates", self.entity_type)
        
        # Check properties
        self.assertEqual(const.name, "Socrates")
        self.assertEqual(const.type, self.entity_type)
        self.assertIsNone(const.value)
        
        # Test equality
        const2 = ConstantNode("Socrates", self.entity_type)
        self.assertEqual(const, const2)
        
        const3 = ConstantNode("Plato", self.entity_type)
        self.assertNotEqual(const, const3)
    
    def test_variable_node(self):
        """Test VariableNode."""
        # Create a variable node
        var = VariableNode("?x", 1, self.entity_type)
        
        # Check properties
        self.assertEqual(var.name, "?x")
        self.assertEqual(var.var_id, 1)
        self.assertEqual(var.type, self.entity_type)
        
        # Test equality
        var2 = VariableNode("?x", 1, self.entity_type)
        self.assertEqual(var, var2)
        
        var3 = VariableNode("?x", 2, self.entity_type)
        self.assertNotEqual(var, var3)
    
    def test_application_node(self):
        """Test ApplicationNode."""
        # Create a predicate
        human_pred = ConstantNode("Human", self.boolean_type)
        
        # Create a constant
        socrates = ConstantNode("Socrates", self.entity_type)
        
        # Create an application node
        app = ApplicationNode(human_pred, [socrates], self.boolean_type)
        
        # Check properties
        self.assertEqual(app.operator, human_pred)
        self.assertEqual(len(app.arguments), 1)
        self.assertEqual(app.arguments[0], socrates)
        self.assertEqual(app.type, self.boolean_type)
        
        # Test equality
        app2 = ApplicationNode(human_pred, [socrates], self.boolean_type)
        self.assertEqual(app, app2)
        
        plato = ConstantNode("Plato", self.entity_type)
        app3 = ApplicationNode(human_pred, [plato], self.boolean_type)
        self.assertNotEqual(app, app3)
    
    def test_connective_node(self):
        """Test ConnectiveNode."""
        # Create predicates
        human_pred = ConstantNode("Human", self.boolean_type)
        mortal_pred = ConstantNode("Mortal", self.boolean_type)
        
        # Create a constant
        socrates = ConstantNode("Socrates", self.entity_type)
        
        # Create applications
        human_socrates = ApplicationNode(human_pred, [socrates], self.boolean_type)
        mortal_socrates = ApplicationNode(mortal_pred, [socrates], self.boolean_type)
        
        # Create a connective node
        conn = ConnectiveNode("IMPLIES", [human_socrates, mortal_socrates], self.boolean_type)
        
        # Check properties
        self.assertEqual(conn.connective_type, "IMPLIES")
        self.assertEqual(len(conn.operands), 2)
        self.assertEqual(conn.operands[0], human_socrates)
        self.assertEqual(conn.operands[1], mortal_socrates)
        self.assertEqual(conn.type, self.boolean_type)
        
        # Test equality
        conn2 = ConnectiveNode("IMPLIES", [human_socrates, mortal_socrates], self.boolean_type)
        self.assertEqual(conn, conn2)
        
        conn3 = ConnectiveNode("AND", [human_socrates, mortal_socrates], self.boolean_type)
        self.assertNotEqual(conn, conn3)
    
    def test_visitor_pattern(self):
        """Test the visitor pattern."""
        # Create a simple AST
        socrates = ConstantNode("Socrates", self.entity_type)
        human_pred = ConstantNode("Human", self.boolean_type)
        human_socrates = ApplicationNode(human_pred, [socrates], self.boolean_type)
        
        # Create a visitor that counts nodes
        class CountingVisitor(ASTVisitor[int]):
            def visit_constant(self, node: ConstantNode) -> int:
                return 1
                
            def visit_variable(self, node: VariableNode) -> int:
                return 1
                
            def visit_application(self, node: ApplicationNode) -> int:
                return 1 + node.operator.accept(self) + sum(arg.accept(self) for arg in node.arguments)
                
            def visit_quantifier(self, node: QuantifierNode) -> int:
                return 1 + len(node.bound_variables) + node.scope.accept(self)
                
            def visit_connective(self, node: ConnectiveNode) -> int:
                return 1 + sum(op.accept(self) for op in node.operands)
                
            def visit_modal_op(self, node: ModalOpNode) -> int:
                agent_count = node.agent_or_world.accept(self) if node.agent_or_world else 0
                return 1 + node.proposition.accept(self) + agent_count
                
            def visit_lambda(self, node: LambdaNode) -> int:
                return 1 + len(node.bound_variables) + node.body.accept(self)
                
            def visit_definition(self, node: DefinitionNode) -> int:
                return 1 + node.definition_body_ast.accept(self)
        
        visitor = CountingVisitor()
        count = human_socrates.accept(visitor)
        
        # The AST has 3 nodes: ApplicationNode, ConstantNode (Human), ConstantNode (Socrates)
        self.assertEqual(count, 3)
    
    def test_variable_substitution(self):
        """Test variable substitution."""
        # Create variables and constants
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        socrates = ConstantNode("Socrates", self.entity_type)
        plato = ConstantNode("Plato", self.entity_type)
        
        # Create a predicate
        loves_pred = ConstantNode("Loves", self.boolean_type)
        
        # Create an application: Loves(?x, ?y)
        loves_xy = ApplicationNode(loves_pred, [x_var, y_var], self.boolean_type)
        
        # Create a substitution: {?x -> Socrates, ?y -> Plato}
        substitution = {x_var: socrates, y_var: plato}
        
        # Apply the substitution
        result = loves_xy.substitute(substitution)
        
        # Check that the result is Loves(Socrates, Plato)
        self.assertIsInstance(result, ApplicationNode)
        self.assertEqual(result.operator, loves_pred)
        self.assertEqual(len(result.arguments), 2)
        self.assertEqual(result.arguments[0], socrates)
        self.assertEqual(result.arguments[1], plato)
        
        # Test substitution with quantifiers
        # Create a quantifier: ∀?x. Loves(?x, ?y)
        forall_x_loves_xy = QuantifierNode("FORALL", [x_var], loves_xy, self.boolean_type)
        
        # Apply the substitution: {?x -> Socrates, ?y -> Plato}
        # Since ?x is bound, only ?y should be substituted
        result = forall_x_loves_xy.substitute(substitution)
        
        # Check that the result is ∀?x. Loves(?x, Plato)
        self.assertIsInstance(result, QuantifierNode)
        self.assertEqual(result.quantifier_type, "FORALL")
        self.assertEqual(len(result.bound_variables), 1)
        self.assertEqual(result.bound_variables[0], x_var)
        
        loves_x_plato = result.scope
        self.assertIsInstance(loves_x_plato, ApplicationNode)
        self.assertEqual(loves_x_plato.operator, loves_pred)
        self.assertEqual(loves_x_plato.arguments[0], x_var)  # ?x remains unchanged
        self.assertEqual(loves_x_plato.arguments[1], plato)  # ?y is substituted with Plato
    
    def test_contains_variable(self):
        """Test contains_variable method."""
        # Create variables and constants
        x_var = VariableNode("?x", 1, self.entity_type)
        y_var = VariableNode("?y", 2, self.entity_type)
        z_var = VariableNode("?z", 3, self.entity_type)
        socrates = ConstantNode("Socrates", self.entity_type)
        
        # Create a predicate
        loves_pred = ConstantNode("Loves", self.boolean_type)
        
        # Create an application: Loves(?x, ?y)
        loves_xy = ApplicationNode(loves_pred, [x_var, y_var], self.boolean_type)
        
        # Check that loves_xy contains ?x and ?y but not ?z or Socrates
        self.assertTrue(loves_xy.contains_variable(x_var))
        self.assertTrue(loves_xy.contains_variable(y_var))
        self.assertFalse(loves_xy.contains_variable(z_var))
        
        # Constants never contain variables
        self.assertFalse(socrates.contains_variable(x_var))
        
        # Create a quantifier: ∀?x. Loves(?x, ?y)
        forall_x_loves_xy = QuantifierNode("FORALL", [x_var], loves_xy, self.boolean_type)
        
        # Check that forall_x_loves_xy contains ?y but not ?x (because ?x is bound)
        self.assertFalse(forall_x_loves_xy.contains_variable(x_var))
        self.assertTrue(forall_x_loves_xy.contains_variable(y_var))
    
    def test_metadata(self):
        """Test metadata handling."""
        # Create a node with metadata
        metadata = {"source": "user", "confidence": 0.9}
        socrates = ConstantNode("Socrates", self.entity_type, metadata=metadata)
        
        # Check that the metadata is correctly stored
        self.assertEqual(socrates.metadata["source"], "user")
        self.assertEqual(socrates.metadata["confidence"], 0.9)
        
        # Check that metadata is copied, not referenced
        socrates.metadata["source"] = "modified"
        self.assertEqual(socrates.metadata["source"], "user")  # Original metadata unchanged
        
        # Test with_metadata method
        socrates2 = socrates.with_metadata(confidence=0.8, new_field="test")
        self.assertEqual(socrates2.metadata["source"], "user")  # Original field preserved
        self.assertEqual(socrates2.metadata["confidence"], 0.8)  # Updated field
        self.assertEqual(socrates2.metadata["new_field"], "test")  # New field added
        
        # Original node should be unchanged
        self.assertEqual(socrates.metadata["confidence"], 0.9)
        self.assertNotIn("new_field", socrates.metadata)


if __name__ == '__main__':
    unittest.main()