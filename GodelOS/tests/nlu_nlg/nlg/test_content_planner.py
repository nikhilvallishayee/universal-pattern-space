"""
Unit tests for the ContentPlanner module.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode
)
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType

from godelOS.nlu_nlg.nlg.content_planner import (
    ContentPlanner, MessageSpecification, ContentElement, MessageType
)


class TestContentPlanner(unittest.TestCase):
    """Test cases for the ContentPlanner class."""
    
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
        
        # Create the content planner
        self.content_planner = ContentPlanner(self.type_system)
    
    def test_plan_content_with_constant_node(self):
        """Test planning content with a ConstantNode."""
        # Create a constant node
        constant_node = ConstantNode(
            name="John",
            type_ref=self.entity_type,
            value=None,
            metadata={"source": "test"}
        )
        
        # Plan content
        message_spec = self.content_planner.plan_content([constant_node])
        
        # Check that the message specification is correct
        self.assertIsInstance(message_spec, MessageSpecification)
        self.assertEqual(message_spec.message_type, MessageType.STATEMENT)
        self.assertEqual(len(message_spec.main_content), 1)
        
        # Check the content element
        content_element = message_spec.main_content[0]
        self.assertEqual(content_element.content_type, "entity")
        self.assertEqual(content_element.properties["name"], "John")
        self.assertEqual(content_element.source_node, constant_node)
    
    def test_plan_content_with_application_node(self):
        """Test planning content with an ApplicationNode."""
        # Create an operator node
        operator = ConstantNode(
            name="chase",
            type_ref=self.entity_type,
            value=None
        )
        
        # Create argument nodes
        arg1 = ConstantNode(
            name="cat",
            type_ref=self.entity_type,
            value=None
        )
        
        arg2 = ConstantNode(
            name="mouse",
            type_ref=self.entity_type,
            value=None
        )
        
        # Create an application node
        application_node = ApplicationNode(
            operator=operator,
            arguments=[arg1, arg2],
            type_ref=self.proposition_type
        )
        
        # Plan content
        message_spec = self.content_planner.plan_content([application_node])
        
        # Check that the message specification is correct
        self.assertIsInstance(message_spec, MessageSpecification)
        self.assertEqual(message_spec.message_type, MessageType.STATEMENT)
        
        # Check that there are main content elements
        self.assertGreater(len(message_spec.main_content), 0)
        
        # Find the application content element
        application_element = None
        for element in message_spec.main_content:
            if element.content_type == "predication" and element.source_node == application_node:
                application_element = element
                break
        
        # Check the application element
        self.assertIsNotNone(application_element)
        self.assertEqual(application_element.properties["operator"], "chase")
    
    def test_plan_content_with_quantifier_node(self):
        """Test planning content with a QuantifierNode."""
        # Create a variable node
        variable = VariableNode(
            name="x",
            var_id=1,
            type_ref=self.entity_type
        )
        
        # Create a constant node for the scope
        constant = ConstantNode(
            name="human",
            type_ref=self.entity_type,
            value=None
        )
        
        # Create an application node for the scope
        application = ApplicationNode(
            operator=constant,
            arguments=[variable],
            type_ref=self.proposition_type
        )
        
        # Create a quantifier node
        quantifier_node = QuantifierNode(
            quantifier_type="FORALL",
            bound_variables=[variable],
            scope=application,
            type_ref=self.proposition_type
        )
        
        # Plan content
        message_spec = self.content_planner.plan_content([quantifier_node])
        
        # Check that the message specification is correct
        self.assertIsInstance(message_spec, MessageSpecification)
        self.assertEqual(message_spec.message_type, MessageType.STATEMENT)
        
        # Check that there are main content elements
        self.assertGreater(len(message_spec.main_content), 0)
        
        # Find the quantifier content element
        quantifier_element = None
        for element in message_spec.main_content:
            if element.content_type == "quantification" and element.source_node == quantifier_node:
                quantifier_element = element
                break
        
        # Check the quantifier element
        self.assertIsNotNone(quantifier_element)
        self.assertEqual(quantifier_element.properties["quantifier_type"], "FORALL")
    
    def test_plan_content_with_connective_node(self):
        """Test planning content with a ConnectiveNode."""
        # Create constant nodes for the operands
        constant1 = ConstantNode(
            name="sunny",
            type_ref=self.proposition_type,
            value=None
        )
        
        constant2 = ConstantNode(
            name="warm",
            type_ref=self.proposition_type,
            value=None
        )
        
        # Create a connective node
        connective_node = ConnectiveNode(
            connective_type="AND",
            operands=[constant1, constant2],
            type_ref=self.proposition_type
        )
        
        # Plan content
        message_spec = self.content_planner.plan_content([connective_node])
        
        # Check that the message specification is correct
        self.assertIsInstance(message_spec, MessageSpecification)
        self.assertEqual(message_spec.message_type, MessageType.STATEMENT)
        
        # Check that there are main content elements
        self.assertGreater(len(message_spec.main_content), 0)
        
        # Find the connective content element
        connective_element = None
        for element in message_spec.main_content:
            if element.content_type == "connective" and element.source_node == connective_node:
                connective_element = element
                break
        
        # Check the connective element
        self.assertIsNotNone(connective_element)
        self.assertEqual(connective_element.properties["connective_type"], "AND")
    
    def test_plan_content_with_modal_op_node(self):
        """Test planning content with a ModalOpNode."""
        # Create a constant node for the proposition
        proposition = ConstantNode(
            name="raining",
            type_ref=self.proposition_type,
            value=None
        )
        
        # Create a constant node for the agent
        agent = ConstantNode(
            name="John",
            type_ref=self.entity_type,
            value=None
        )
        
        # Create a modal operator node
        modal_op_node = ModalOpNode(
            modal_operator="BELIEVES",
            proposition=proposition,
            agent_or_world=agent,
            type_ref=self.proposition_type
        )
        
        # Plan content
        message_spec = self.content_planner.plan_content([modal_op_node])
        
        # Check that the message specification is correct
        self.assertIsInstance(message_spec, MessageSpecification)
        self.assertEqual(message_spec.message_type, MessageType.BELIEF)
        
        # Check that there are main content elements
        self.assertGreater(len(message_spec.main_content), 0)
        
        # Find the modal operator content element
        modal_op_element = None
        for element in message_spec.main_content:
            if element.content_type == "modal_operation" and element.source_node == modal_op_node:
                modal_op_element = element
                break
        
        # Check the modal operator element
        self.assertIsNotNone(modal_op_element)
        self.assertEqual(modal_op_element.properties["modal_operator"], "BELIEVES")
    
    def test_determine_message_type(self):
        """Test determining the message type based on AST nodes."""
        # Create a constant node
        constant_node = ConstantNode(
            name="John",
            type_ref=self.entity_type,
            value=None
        )
        
        # Create a modal operator node for belief
        belief_node = ModalOpNode(
            modal_operator="BELIEVES",
            proposition=constant_node,
            agent_or_world=None,
            type_ref=self.proposition_type
        )
        
        # Create a modal operator node for knowledge
        knowledge_node = ModalOpNode(
            modal_operator="KNOWS",
            proposition=constant_node,
            agent_or_world=None,
            type_ref=self.proposition_type
        )
        
        # Create a connective node for negation
        negation_node = ConnectiveNode(
            connective_type="NOT",
            operands=[constant_node],
            type_ref=self.proposition_type
        )
        
        # Create a connective node for implication
        implication_node = ConnectiveNode(
            connective_type="IMPLIES",
            operands=[constant_node, constant_node],
            type_ref=self.proposition_type
        )
        
        # Test determining message types
        self.assertEqual(
            self.content_planner._determine_message_type([constant_node]),
            MessageType.STATEMENT
        )
        
        self.assertEqual(
            self.content_planner._determine_message_type([belief_node]),
            MessageType.BELIEF
        )
        
        self.assertEqual(
            self.content_planner._determine_message_type([knowledge_node]),
            MessageType.KNOWLEDGE
        )
        
        self.assertEqual(
            self.content_planner._determine_message_type([negation_node]),
            MessageType.NEGATION
        )
        
        self.assertEqual(
            self.content_planner._determine_message_type([implication_node]),
            MessageType.CONDITIONAL
        )


if __name__ == '__main__':
    unittest.main()