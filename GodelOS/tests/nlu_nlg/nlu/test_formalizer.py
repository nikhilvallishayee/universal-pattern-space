"""
Unit tests for the Formalizer module.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode
)
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType, FunctionType

from godelOS.nlu_nlg.nlu.semantic_interpreter import (
    IntermediateSemanticRepresentation, SemanticNode, Predicate, 
    SemanticArgument, SemanticRelation, LogicalOperator, RelationType, SemanticRole
)
from godelOS.nlu_nlg.nlu.formalizer import (
    Formalizer, FormalizationContext, create_ast_from_isr
)


class TestFormalizer(unittest.TestCase):
    """Test cases for the Formalizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock type system
        self.type_system = MagicMock(spec=TypeSystemManager)
        
        # Set up common types
        self.entity_type = AtomicType("Entity")
        self.boolean_type = AtomicType("Boolean")
        self.proposition_type = AtomicType("Proposition")
        
        # Configure the type system mock
        self.type_system.get_type.side_effect = lambda name: {
            "Entity": self.entity_type,
            "Boolean": self.boolean_type,
            "Proposition": self.proposition_type
        }.get(name)
        
        # Create the formalizer
        self.formalizer = Formalizer(self.type_system)
    
    def test_formalize_simple_predicate(self):
        """Test formalizing a simple predicate."""
        # Create a simple ISR with a predicate
        isr = self._create_simple_isr()
        
        # Formalize the ISR
        ast_nodes = self.formalizer.formalize(isr)
        
        # Check that we got at least one AST node
        self.assertGreater(len(ast_nodes), 0)
        
        # Check that the first node is an ApplicationNode
        self.assertIsInstance(ast_nodes[0], ApplicationNode)
        
        # Check that the operator is a ConstantNode for "chase"
        app_node = ast_nodes[0]
        self.assertIsInstance(app_node.operator, ConstantNode)
        self.assertEqual(app_node.operator.name, "chase")
        
        # Check that there are two arguments: cat and mouse
        self.assertEqual(len(app_node.arguments), 2)
        
        # Check that the first argument is for "cat"
        arg1 = app_node.arguments[0]
        self.assertTrue(isinstance(arg1, ConstantNode) or isinstance(arg1, VariableNode))
        
        # Check that the second argument is for "mouse"
        arg2 = app_node.arguments[1]
        self.assertTrue(isinstance(arg2, ConstantNode) or isinstance(arg2, VariableNode))
    
    def test_formalize_negated_predicate(self):
        """Test formalizing a negated predicate."""
        # Create an ISR with a negated predicate
        isr = self._create_negated_isr()
        
        # Formalize the ISR
        ast_nodes = self.formalizer.formalize(isr)
        
        # Check that we got at least one AST node
        self.assertGreater(len(ast_nodes), 0)
        
        # Check that the first node is a ConnectiveNode for NOT
        self.assertIsInstance(ast_nodes[0], ConnectiveNode)
        self.assertEqual(ast_nodes[0].connective_type, "NOT")
        
        # Check that the operand is an ApplicationNode
        self.assertEqual(len(ast_nodes[0].operands), 1)
        self.assertIsInstance(ast_nodes[0].operands[0], ApplicationNode)
        
        # Check that the ApplicationNode has "chase" as the operator
        app_node = ast_nodes[0].operands[0]
        self.assertIsInstance(app_node.operator, ConstantNode)
        self.assertEqual(app_node.operator.name, "chase")
    
    def test_formalize_modal_predicate(self):
        """Test formalizing a predicate with modality."""
        # Create an ISR with a modal predicate
        isr = self._create_modal_isr()
        
        # Formalize the ISR
        ast_nodes = self.formalizer.formalize(isr)
        
        # Check that we got at least one AST node
        self.assertGreater(len(ast_nodes), 0)
        
        # Check that the first node is a ModalOpNode
        self.assertIsInstance(ast_nodes[0], ModalOpNode)
        
        # Check that the modal operator is POSSIBLE_WORLD_TRUTH
        self.assertEqual(ast_nodes[0].modal_operator, "POSSIBLE_WORLD_TRUTH")
        
        # Check that the proposition is an ApplicationNode
        self.assertIsInstance(ast_nodes[0].proposition, ApplicationNode)
        
        # Check that the ApplicationNode has "chase" as the operator
        app_node = ast_nodes[0].proposition
        self.assertIsInstance(app_node.operator, ConstantNode)
        self.assertEqual(app_node.operator.name, "chase")
    
    def test_formalize_logical_expression(self):
        """Test formalizing a logical expression with AND."""
        # Create an ISR with a logical expression
        isr = self._create_logical_isr()
        
        # Formalize the ISR
        ast_nodes = self.formalizer.formalize(isr)
        
        # Check that we got at least one AST node
        self.assertGreater(len(ast_nodes), 0)
        
        # Check that the first node is a ConnectiveNode for AND
        self.assertIsInstance(ast_nodes[0], ConnectiveNode)
        self.assertEqual(ast_nodes[0].connective_type, "AND")
        
        # Check that there are two operands
        self.assertEqual(len(ast_nodes[0].operands), 2)
        
        # Check that both operands are ApplicationNodes
        self.assertIsInstance(ast_nodes[0].operands[0], ApplicationNode)
        self.assertIsInstance(ast_nodes[0].operands[1], ApplicationNode)
        
        # Check that the first ApplicationNode has "chase" as the operator
        app_node1 = ast_nodes[0].operands[0]
        self.assertIsInstance(app_node1.operator, ConstantNode)
        self.assertEqual(app_node1.operator.name, "chase")
        
        # Check that the second ApplicationNode has "catch" as the operator
        app_node2 = ast_nodes[0].operands[1]
        self.assertIsInstance(app_node2.operator, ConstantNode)
        self.assertEqual(app_node2.operator.name, "catch")
    
    def test_formalize_quantified_expression(self):
        """Test formalizing a quantified expression."""
        # Create an ISR with a quantified expression
        isr = self._create_quantified_isr()
        
        # Formalize the ISR
        ast_nodes = self.formalizer.formalize(isr)
        
        # Check that we got at least one AST node
        self.assertGreater(len(ast_nodes), 0)
        
        # Check that the first node is a QuantifierNode
        self.assertIsInstance(ast_nodes[0], QuantifierNode)
        
        # Check that the quantifier type is FORALL
        self.assertEqual(ast_nodes[0].quantifier_type, "FORALL")
        
        # Check that there is one bound variable
        self.assertEqual(len(ast_nodes[0].bound_variables), 1)
        
        # Check that the bound variable is a VariableNode
        self.assertIsInstance(ast_nodes[0].bound_variables[0], VariableNode)
        
        # Check that the scope is an ApplicationNode
        self.assertIsInstance(ast_nodes[0].scope, ApplicationNode)
        
        # Check that the ApplicationNode has "chase" as the operator
        app_node = ast_nodes[0].scope
        self.assertIsInstance(app_node.operator, ConstantNode)
        self.assertEqual(app_node.operator.name, "chase")
    
    def test_create_ast_from_isr(self):
        """Test the create_ast_from_isr convenience function."""
        # Create a simple ISR
        isr = self._create_simple_isr()
        
        # Create AST nodes from the ISR
        ast_nodes = create_ast_from_isr(isr, self.type_system)
        
        # Check that we got at least one AST node
        self.assertGreater(len(ast_nodes), 0)
        
        # Check that the first node is an ApplicationNode
        self.assertIsInstance(ast_nodes[0], ApplicationNode)
    
    def _create_simple_isr(self):
        """Create a simple ISR with a predicate 'chase(cat, mouse)'."""
        # Create the ISR
        isr = IntermediateSemanticRepresentation(text="The cat chased the mouse.")
        
        # Create a predicate
        predicate = Predicate(
            text="chased",
            lemma="chase",
            tense="past",
            aspect="simple"
        )
        
        # Create arguments
        agent = SemanticArgument(
            text="The cat",
            role=SemanticRole.AGENT
        )
        
        patient = SemanticArgument(
            text="the mouse",
            role=SemanticRole.PATIENT
        )
        
        # Add arguments to the predicate
        predicate.arguments = [agent, patient]
        
        # Create nodes
        pred_node = SemanticNode(
            id="pred_0",
            node_type="predicate",
            content=predicate
        )
        
        agent_node = SemanticNode(
            id="entity_0",
            node_type="entity",
            content=agent
        )
        
        patient_node = SemanticNode(
            id="entity_1",
            node_type="entity",
            content=patient
        )
        
        # Create relations
        agent_relation = SemanticRelation(
            relation_type=RelationType.AGENT_ACTION,
            source=pred_node,
            target=agent_node
        )
        
        patient_relation = SemanticRelation(
            relation_type=RelationType.ACTION_PATIENT,
            source=pred_node,
            target=patient_node
        )
        
        # Add relations to the predicate node
        pred_node.relations = [agent_relation, patient_relation]
        
        # Add nodes to the ISR
        isr.nodes = [pred_node, agent_node, patient_node]
        isr.root_nodes = [pred_node]
        
        # Add predicate and entities to the ISR
        isr.predicates["pred_0"] = predicate
        isr.entities["entity_0"] = agent
        isr.entities["entity_1"] = patient
        
        return isr
    
    def _create_negated_isr(self):
        """Create an ISR with a negated predicate 'NOT chase(cat, mouse)'."""
        # Start with a simple ISR
        isr = self._create_simple_isr()
        
        # Set the predicate to be negated
        isr.predicates["pred_0"].negated = True
        
        return isr
    
    def _create_modal_isr(self):
        """Create an ISR with a modal predicate 'POSSIBLE chase(cat, mouse)'."""
        # Start with a simple ISR
        isr = self._create_simple_isr()
        
        # Set the predicate to have a modality
        isr.predicates["pred_0"].modality = "possible"
        
        return isr
    
    def _create_logical_isr(self):
        """Create an ISR with a logical expression 'chase(cat, mouse) AND catch(cat, mouse)'."""
        # Start with a simple ISR
        isr = self._create_simple_isr()
        
        # Create a second predicate
        predicate2 = Predicate(
            text="caught",
            lemma="catch",
            tense="past",
            aspect="simple"
        )
        
        # Copy the arguments from the first predicate
        predicate2.arguments = isr.predicates["pred_0"].arguments.copy()
        
        # Create a node for the second predicate
        pred_node2 = SemanticNode(
            id="pred_1",
            node_type="predicate",
            content=predicate2
        )
        
        # Create a logical expression node
        logical_node = SemanticNode(
            id="logical_0",
            node_type="logical_expression",
            operator=LogicalOperator.AND,
            children=[isr.root_nodes[0], pred_node2]
        )
        
        # Update the ISR
        isr.nodes.append(pred_node2)
        isr.nodes.append(logical_node)
        isr.root_nodes = [logical_node]
        isr.predicates["pred_1"] = predicate2
        
        return isr
    
    def _create_quantified_isr(self):
        """Create an ISR with a quantified expression 'FORALL x. chase(x, mouse)'."""
        # Start with a simple ISR
        isr = self._create_simple_isr()
        
        # Modify the agent to be a variable
        agent = isr.entities["entity_0"]
        agent.text = "?x"
        
        # Create a quantifier node
        quantifier_node = SemanticNode(
            id="quant_0",
            node_type="logical_expression",
            operator=LogicalOperator.FORALL,
            children=[
                SemanticNode(
                    id="var_0",
                    node_type="entity",
                    content=agent
                ),
                isr.root_nodes[0]
            ]
        )
        
        # Update the ISR
        isr.nodes.append(quantifier_node)
        isr.root_nodes = [quantifier_node]
        
        return isr


if __name__ == '__main__':
    unittest.main()