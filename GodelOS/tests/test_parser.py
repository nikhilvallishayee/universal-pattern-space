"""
Tests for the Formal Logic Parser module.
"""

import unittest

from godelOS.core_kr.type_system import TypeSystemManager
from godelOS.core_kr.formal_logic_parser import FormalLogicParser, Error
from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode, LambdaNode
)
from godelOS.core_kr.type_system.types import FunctionType


class TestFormalLogicParser(unittest.TestCase):
    """Test cases for the FormalLogicParser."""
    
    def setUp(self):
        """Set up the test case."""
        self.type_system = TypeSystemManager()
        self.parser = FormalLogicParser(self.type_system)
        
        # Define some common types and signatures for testing
        self.entity_type = self.type_system.get_type("Entity")
        self.boolean_type = self.type_system.get_type("Boolean")
        self.proposition_type = self.type_system.get_type("Proposition")
        
        # Define some function signatures
        self.type_system.define_function_signature("Human", ["Entity"], "Boolean")
        self.type_system.define_function_signature("Mortal", ["Entity"], "Boolean")
        self.type_system.define_function_signature("Loves", ["Entity", "Entity"], "Boolean")
    
    def test_parse_constant(self):
        """Test parsing constants."""
        # Parse a simple constant
        ast, errors = self.parser.parse("Socrates")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConstantNode)
        self.assertEqual(ast.name, "Socrates")
        self.assertEqual(ast.type, self.entity_type)
        
        # Parse a constant with type annotation
        ast, errors = self.parser.parse("Socrates:Entity")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConstantNode)
        self.assertEqual(ast.name, "Socrates")
        self.assertEqual(ast.type, self.entity_type)
        
        # Parse boolean constants
        ast, errors = self.parser.parse("True")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConstantNode)
        self.assertEqual(ast.name, "True")
        self.assertEqual(ast.type, self.boolean_type)
        self.assertEqual(ast.value, True)
        
        ast, errors = self.parser.parse("False")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConstantNode)
        self.assertEqual(ast.name, "False")
        self.assertEqual(ast.type, self.boolean_type)
        self.assertEqual(ast.value, False)
    
    def test_parse_variable(self):
        """Test parsing variables."""
        # Parse a simple variable
        ast, errors = self.parser.parse("?x")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, VariableNode)
        self.assertEqual(ast.name, "?x")
        self.assertEqual(ast.type, self.entity_type)
        
        # Parse a variable with type annotation
        ast, errors = self.parser.parse("?x:Entity")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, VariableNode)
        self.assertEqual(ast.name, "?x")
        self.assertEqual(ast.type, self.entity_type)
    
    def test_parse_application(self):
        """Test parsing function applications."""
        # Parse a simple predicate application
        ast, errors = self.parser.parse("Human(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ApplicationNode)
        self.assertIsInstance(ast.operator, ConstantNode)
        self.assertEqual(ast.operator.name, "Human")
        self.assertEqual(len(ast.arguments), 1)
        self.assertIsInstance(ast.arguments[0], ConstantNode)
        self.assertEqual(ast.arguments[0].name, "Socrates")
        self.assertEqual(ast.type, self.boolean_type)
        
        # Parse a binary predicate application
        ast, errors = self.parser.parse("Loves(Socrates, Plato)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ApplicationNode)
        self.assertIsInstance(ast.operator, ConstantNode)
        self.assertEqual(ast.operator.name, "Loves")
        self.assertEqual(len(ast.arguments), 2)
        self.assertIsInstance(ast.arguments[0], ConstantNode)
        self.assertEqual(ast.arguments[0].name, "Socrates")
        self.assertIsInstance(ast.arguments[1], ConstantNode)
        self.assertEqual(ast.arguments[1].name, "Plato")
        self.assertEqual(ast.type, self.boolean_type)
        
        # Parse nested applications
        ast, errors = self.parser.parse("Loves(Human(Socrates), Plato)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ApplicationNode)
        self.assertEqual(ast.operator.name, "Loves")
        self.assertEqual(len(ast.arguments), 2)
        self.assertIsInstance(ast.arguments[0], ApplicationNode)
        self.assertEqual(ast.arguments[0].operator.name, "Human")
        self.assertEqual(ast.arguments[0].arguments[0].name, "Socrates")
    
    def test_parse_connectives(self):
        """Test parsing logical connectives."""
        # Parse negation
        ast, errors = self.parser.parse("not Human(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConnectiveNode)
        self.assertEqual(ast.connective_type, "NOT")
        self.assertEqual(len(ast.operands), 1)
        self.assertIsInstance(ast.operands[0], ApplicationNode)
        self.assertEqual(ast.operands[0].operator.name, "Human")
        
        # Parse conjunction
        ast, errors = self.parser.parse("Human(Socrates) and Mortal(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConnectiveNode)
        self.assertEqual(ast.connective_type, "AND")
        self.assertEqual(len(ast.operands), 2)
        self.assertIsInstance(ast.operands[0], ApplicationNode)
        self.assertEqual(ast.operands[0].operator.name, "Human")
        self.assertIsInstance(ast.operands[1], ApplicationNode)
        self.assertEqual(ast.operands[1].operator.name, "Mortal")
        
        # Parse disjunction
        ast, errors = self.parser.parse("Human(Socrates) or Mortal(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConnectiveNode)
        self.assertEqual(ast.connective_type, "OR")
        
        # Parse implication
        ast, errors = self.parser.parse("Human(Socrates) implies Mortal(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConnectiveNode)
        self.assertEqual(ast.connective_type, "IMPLIES")
        
        # Parse equivalence
        ast, errors = self.parser.parse("Human(Socrates) equiv Mortal(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConnectiveNode)
        self.assertEqual(ast.connective_type, "EQUIV")
        
        # Parse complex nested expressions
        ast, errors = self.parser.parse("Human(Socrates) and (Mortal(Socrates) or Loves(Socrates, Plato))")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ConnectiveNode)
        self.assertEqual(ast.connective_type, "AND")
        self.assertIsInstance(ast.operands[1], ConnectiveNode)
        self.assertEqual(ast.operands[1].connective_type, "OR")
    
    def test_parse_quantifiers(self):
        """Test parsing quantifiers."""
        # Parse universal quantifier
        ast, errors = self.parser.parse("forall ?x. Human(?x) implies Mortal(?x)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, QuantifierNode)
        self.assertEqual(ast.quantifier_type, "FORALL")
        self.assertEqual(len(ast.bound_variables), 1)
        self.assertEqual(ast.bound_variables[0].name, "?x")
        self.assertIsInstance(ast.scope, ConnectiveNode)
        self.assertEqual(ast.scope.connective_type, "IMPLIES")
        
        # Parse existential quantifier
        ast, errors = self.parser.parse("exists ?x. Human(?x) and Loves(?x, Plato)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, QuantifierNode)
        self.assertEqual(ast.quantifier_type, "EXISTS")
        self.assertEqual(len(ast.bound_variables), 1)
        self.assertEqual(ast.bound_variables[0].name, "?x")
        self.assertIsInstance(ast.scope, ConnectiveNode)
        self.assertEqual(ast.scope.connective_type, "AND")
        
        # Parse quantifier with type annotation
        ast, errors = self.parser.parse("forall ?x:Entity. Human(?x)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, QuantifierNode)
        self.assertEqual(ast.quantifier_type, "FORALL")
        self.assertEqual(ast.bound_variables[0].name, "?x")
        self.assertEqual(ast.bound_variables[0].type, self.entity_type)
        
        # Parse nested quantifiers
        ast, errors = self.parser.parse("forall ?x. exists ?y. Loves(?x, ?y)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, QuantifierNode)
        self.assertEqual(ast.quantifier_type, "FORALL")
        self.assertIsInstance(ast.scope, QuantifierNode)
        self.assertEqual(ast.scope.quantifier_type, "EXISTS")
    
    def test_parse_modal_operators(self):
        """Test parsing modal operators."""
        # Parse knowledge operator
        ast, errors = self.parser.parse("knows Human(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ModalOpNode)
        self.assertEqual(ast.modal_operator, "KNOWS")
        self.assertIsInstance(ast.proposition, ApplicationNode)
        self.assertEqual(ast.proposition.operator.name, "Human")
        
        # Parse belief operator
        ast, errors = self.parser.parse("believes Human(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ModalOpNode)
        self.assertEqual(ast.modal_operator, "BELIEVES")
        
        # Parse possibility operator
        ast, errors = self.parser.parse("possible Human(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ModalOpNode)
        self.assertEqual(ast.modal_operator, "POSSIBLE")
        
        # Parse necessity operator
        ast, errors = self.parser.parse("necessary Human(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ModalOpNode)
        self.assertEqual(ast.modal_operator, "NECESSARY")
        
        # Parse with agent
        ast, errors = self.parser.parse("knows[Socrates] Human(Plato)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ModalOpNode)
        self.assertEqual(ast.modal_operator, "KNOWS")
        self.assertIsNotNone(ast.agent_or_world)
        self.assertEqual(ast.agent_or_world.name, "Socrates")
        
        # Parse probability operator
        ast, errors = self.parser.parse("prob Human(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ModalOpNode)
        self.assertEqual(ast.modal_operator, "PROBABILITY")
        
        # Parse probability with value
        ast, errors = self.parser.parse("prob[0.8] Human(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ModalOpNode)
        self.assertEqual(ast.modal_operator, "PROBABILITY")
        self.assertEqual(ast.metadata["probability"], 0.8)
        
        # Parse defeasibility operator
        ast, errors = self.parser.parse("defeasibly Human(Socrates)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ModalOpNode)
        self.assertEqual(ast.modal_operator, "DEFEASIBLE")
    
    def test_parse_lambda(self):
        """Test parsing lambda expressions."""
        # Parse simple lambda
        ast, errors = self.parser.parse("lambda ?x. Human(?x)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, LambdaNode)
        self.assertEqual(len(ast.bound_variables), 1)
        self.assertEqual(ast.bound_variables[0].name, "?x")
        self.assertIsInstance(ast.body, ApplicationNode)
        self.assertEqual(ast.body.operator.name, "Human")
        
        # Parse lambda with type annotation
        ast, errors = self.parser.parse("lambda ?x:Entity. Human(?x)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, LambdaNode)
        self.assertEqual(ast.bound_variables[0].name, "?x")
        self.assertEqual(ast.bound_variables[0].type, self.entity_type)
        
        # Parse lambda with multiple variables
        ast, errors = self.parser.parse("lambda ?x ?y. Loves(?x, ?y)")
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, LambdaNode)
        self.assertEqual(len(ast.bound_variables), 2)
        self.assertEqual(ast.bound_variables[0].name, "?x")
        self.assertEqual(ast.bound_variables[1].name, "?y")
        self.assertIsInstance(ast.body, ApplicationNode)
        self.assertEqual(ast.body.operator.name, "Loves")
    
    def test_parse_complex_expressions(self):
        """Test parsing complex expressions."""
        # Parse a complex expression with multiple features
        expr = "forall ?x:Entity. (Human(?x) implies (Mortal(?x) and exists ?y. Loves(?x, ?y)))"
        ast, errors = self.parser.parse(expr)
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, QuantifierNode)
        self.assertEqual(ast.quantifier_type, "FORALL")
        self.assertEqual(ast.bound_variables[0].name, "?x")
        self.assertEqual(ast.bound_variables[0].type, self.entity_type)
        
        # Check the implication structure
        self.assertIsInstance(ast.scope, ConnectiveNode)
        self.assertEqual(ast.scope.connective_type, "IMPLIES")
        
        # Check the right side of the implication (AND)
        right_side = ast.scope.operands[1]
        self.assertIsInstance(right_side, ConnectiveNode)
        self.assertEqual(right_side.connective_type, "AND")
        
        # Check the existential quantifier
        exists_expr = right_side.operands[1]
        self.assertIsInstance(exists_expr, QuantifierNode)
        self.assertEqual(exists_expr.quantifier_type, "EXISTS")
        self.assertEqual(exists_expr.bound_variables[0].name, "?y")
        
        # Parse a complex modal expression
        expr = "knows[Socrates] (forall ?x. Human(?x) implies Mortal(?x))"
        ast, errors = self.parser.parse(expr)
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ModalOpNode)
        self.assertEqual(ast.modal_operator, "KNOWS")
        self.assertEqual(ast.agent_or_world.name, "Socrates")
        self.assertIsInstance(ast.proposition, QuantifierNode)
    
    def test_parse_errors(self):
        """Test error handling during parsing."""
        # Test missing closing parenthesis
        ast, errors = self.parser.parse("Human(Socrates", raise_exceptions=False)
        self.assertIsNone(ast)
        self.assertGreater(len(errors), 0)
        
        # Test unknown type — parser returns None with errors
        ast, errors = self.parser.parse("Socrates:UnknownType", raise_exceptions=False)
        self.assertGreater(len(errors), 0)
        
        # Test invalid syntax
        ast, errors = self.parser.parse("Human Socrates)", raise_exceptions=False)
        self.assertIsNone(ast)
        self.assertGreater(len(errors), 0)
        
        # Test empty expression
        ast, errors = self.parser.parse("", raise_exceptions=False)
        self.assertIsNone(ast)
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()