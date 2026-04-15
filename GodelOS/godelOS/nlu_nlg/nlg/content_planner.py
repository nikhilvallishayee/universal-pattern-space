"""
Content Planner (CP) for GödelOS NLG Pipeline.

This module provides the ContentPlanner class that takes AST nodes from the KR System
as input, determines what information to include in the output, and organizes content
into a coherent structure.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union, cast
from dataclasses import dataclass, field
import logging
from enum import Enum, auto
from collections import defaultdict

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode, LambdaNode, DefinitionNode
)
from godelOS.core_kr.type_system.manager import TypeSystemManager


class MessageType(Enum):
    """Enumeration of message types that can be generated."""
    STATEMENT = auto()          # Declarative statement
    QUESTION = auto()           # Question
    COMMAND = auto()            # Command or request
    DEFINITION = auto()         # Definition of a term
    EXPLANATION = auto()        # Explanation of a concept
    DESCRIPTION = auto()        # Description of an entity or situation
    COMPARISON = auto()         # Comparison between entities
    CONDITIONAL = auto()        # Conditional statement (if-then)
    NEGATION = auto()           # Negation of a statement
    POSSIBILITY = auto()        # Statement about possibility
    NECESSITY = auto()          # Statement about necessity
    BELIEF = auto()             # Statement about belief
    KNOWLEDGE = auto()          # Statement about knowledge


@dataclass
class ContentElement:
    """
    Represents a single element of content to be expressed.
    
    A content element is a piece of information that will be expressed
    in the generated text, such as an entity, a property, or a relation.
    """
    id: str
    content_type: str  # e.g., "entity", "property", "relation", "event"
    source_node: AST_Node
    properties: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0  # How important this element is (for content selection)
    
    def add_property(self, name: str, value: Any) -> None:
        """Add a property to this content element."""
        self.properties[name] = value


@dataclass
class MessageSpecification:
    """
    Represents a specification for a message to be generated.
    
    A message specification outlines the content to be expressed,
    including the main content elements, their relationships,
    and the overall message structure.
    """
    message_type: MessageType
    main_content: List[ContentElement] = field(default_factory=list)
    supporting_content: List[ContentElement] = field(default_factory=list)
    discourse_relations: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)
    temporal_ordering: List[str] = field(default_factory=list)  # IDs of content elements in temporal order
    focus_elements: List[str] = field(default_factory=list)  # IDs of content elements to focus on
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_main_content(self, element: ContentElement) -> None:
        """Add a main content element to the message specification."""
        self.main_content.append(element)
    
    def add_supporting_content(self, element: ContentElement) -> None:
        """Add a supporting content element to the message specification."""
        self.supporting_content.append(element)
    
    def add_discourse_relation(self, relation_type: str, source_id: str, target_id: str) -> None:
        """Add a discourse relation between content elements."""
        if relation_type not in self.discourse_relations:
            self.discourse_relations[relation_type] = []
        self.discourse_relations[relation_type].append((source_id, target_id))
    
    def add_temporal_ordering(self, element_id: str) -> None:
        """Add a content element to the temporal ordering."""
        if element_id not in self.temporal_ordering:
            self.temporal_ordering.append(element_id)
    
    def add_focus_element(self, element_id: str) -> None:
        """Add a content element to the focus elements."""
        if element_id not in self.focus_elements:
            self.focus_elements.append(element_id)


class ContentPlanner:
    """
    Content Planner for the NLG Pipeline.
    
    This class takes AST nodes from the KR System as input, determines what
    information to include in the output, and organizes content into a coherent
    structure represented as a MessageSpecification.
    """
    
    def __init__(self, type_system: TypeSystemManager):
        """
        Initialize the content planner.
        
        Args:
            type_system: The type system manager for type validation and inference
        """
        self.type_system = type_system
        self.logger = logging.getLogger(__name__)
    
    def plan_content(self, ast_nodes: List[AST_Node], 
                    context: Optional[Dict[str, Any]] = None) -> MessageSpecification:
        """
        Plan the content to be expressed based on the input AST nodes.
        
        Args:
            ast_nodes: The AST nodes representing the formal logical content
            context: Optional context information for content planning
            
        Returns:
            A MessageSpecification outlining the content to be expressed
        """
        context = context or {}
        
        # Determine the message type based on the AST nodes
        message_type = self._determine_message_type(ast_nodes)
        
        # Create a message specification
        message_spec = MessageSpecification(message_type=message_type)
        
        # Process each AST node to extract content elements
        for node in ast_nodes:
            self._process_node(node, message_spec)
        
        # Determine relationships between content elements
        self._determine_relationships(message_spec)
        
        # Determine the temporal ordering of content elements
        self._determine_temporal_ordering(message_spec)
        
        # Determine the focus elements
        self._determine_focus(message_spec, context)
        
        return message_spec
    
    def _determine_message_type(self, ast_nodes: List[AST_Node]) -> MessageType:
        """
        Determine the type of message to be generated based on the AST nodes.
        
        Args:
            ast_nodes: The AST nodes representing the formal logical content
            
        Returns:
            The determined message type
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would use more complex logic
        
        # Check if there's a definition node
        if any(isinstance(node, DefinitionNode) for node in ast_nodes):
            return MessageType.DEFINITION
        
        # Check if there's a modal operator node for belief or knowledge
        # Check top-level nodes first
        for node in ast_nodes:
            if isinstance(node, ModalOpNode):
                if node.modal_operator == "BELIEVES":
                    return MessageType.BELIEF
                elif node.modal_operator == "KNOWS":
                    return MessageType.KNOWLEDGE
                elif node.modal_operator == "POSSIBLE_WORLD_TRUTH":
                    return MessageType.POSSIBILITY
        
        # Check if there's a connective node for negation
        for node in ast_nodes:
            if isinstance(node, ConnectiveNode) and node.connective_type == "NOT":
                return MessageType.NEGATION
        
        # Check if there's a connective node for conditionals
        for node in ast_nodes:
            if isinstance(node, ConnectiveNode) and node.connective_type == "IMPLIES":
                return MessageType.CONDITIONAL
        
        # Recursively check child nodes of connectives for modal operators
        for node in ast_nodes:
            if isinstance(node, ConnectiveNode) and node.operands:
                child_type = self._determine_message_type(node.operands)
                if child_type != MessageType.STATEMENT:
                    return child_type
        
        # Default to statement
        return MessageType.STATEMENT
    
    def _process_node(self, node: AST_Node, message_spec: MessageSpecification) -> str:
        """
        Process an AST node to extract content elements.
        
        Args:
            node: The AST node to process
            message_spec: The message specification to update
            
        Returns:
            The ID of the created content element
        """
        # Generate a unique ID for this content element
        element_id = f"element_{len(message_spec.main_content) + len(message_spec.supporting_content)}"
        
        if isinstance(node, ConstantNode):
            # Create a content element for the constant
            element = ContentElement(
                id=element_id,
                content_type="entity",
                source_node=node,
                properties={"name": node.name, "value": node.value}
            )
            message_spec.add_main_content(element)
        
        elif isinstance(node, VariableNode):
            # Create a content element for the variable
            element = ContentElement(
                id=element_id,
                content_type="variable",
                source_node=node,
                properties={"name": node.name}
            )
            message_spec.add_supporting_content(element)
        
        elif isinstance(node, ApplicationNode):
            # Create a content element for the application
            element = ContentElement(
                id=element_id,
                content_type="predication",
                source_node=node,
                properties={"operator": self._get_operator_name(node.operator)}
            )
            message_spec.add_main_content(element)
            
            # Process the arguments
            for i, arg in enumerate(node.arguments):
                child_id = self._process_node(arg, message_spec)
                message_spec.add_discourse_relation("argument", element_id, child_id)
        
        elif isinstance(node, QuantifierNode):
            # Create a content element for the quantifier
            element = ContentElement(
                id=element_id,
                content_type="quantification",
                source_node=node,
                properties={"quantifier_type": node.quantifier_type}
            )
            message_spec.add_main_content(element)
            
            # Process the bound variables
            for i, var in enumerate(node.bound_variables):
                var_element_id = f"{element_id}_var_{i}"
                var_element = ContentElement(
                    id=var_element_id,
                    content_type="bound_variable",
                    source_node=var,
                    properties={"name": var.name}
                )
                message_spec.add_supporting_content(var_element)
                message_spec.add_discourse_relation("binding", element_id, var_element_id)
            
            # Process the scope
            child_id = self._process_node(node.scope, message_spec)
            message_spec.add_discourse_relation("scope", element_id, child_id)
        
        elif isinstance(node, ConnectiveNode):
            # Create a content element for the connective
            element = ContentElement(
                id=element_id,
                content_type="connective",
                source_node=node,
                properties={"connective_type": node.connective_type}
            )
            message_spec.add_main_content(element)
            
            # Process the operands
            for i, op in enumerate(node.operands):
                child_id = self._process_node(op, message_spec)
                message_spec.add_discourse_relation("operand", element_id, child_id)
        
        elif isinstance(node, ModalOpNode):
            # Create a content element for the modal operator
            element = ContentElement(
                id=element_id,
                content_type="modal_operation",
                source_node=node,
                properties={"modal_operator": node.modal_operator}
            )
            message_spec.add_main_content(element)
            
            # Process the proposition
            child_id = self._process_node(node.proposition, message_spec)
            message_spec.add_discourse_relation("proposition", element_id, child_id)
            
            # Process the agent or world if present
            if node.agent_or_world:
                agent_id = self._process_node(node.agent_or_world, message_spec)
                message_spec.add_discourse_relation("agent", element_id, agent_id)
        
        elif isinstance(node, LambdaNode):
            # Create a content element for the lambda abstraction
            element = ContentElement(
                id=element_id,
                content_type="lambda_abstraction",
                source_node=node,
                properties={"bound_variable_count": len(node.bound_variables)}
            )
            message_spec.add_main_content(element)
            
            # Process bound variables
            for var in node.bound_variables:
                var_id = self._process_node(var, message_spec)
                message_spec.add_discourse_relation("binding", element_id, var_id)
            
            # Process lambda body
            body_id = self._process_node(node.body, message_spec)
            message_spec.add_discourse_relation("body", element_id, body_id)
        
        elif isinstance(node, DefinitionNode):
            # Create a content element for the definition
            element = ContentElement(
                id=element_id,
                content_type="definition",
                source_node=node,
                properties={"defined_symbol_name": node.defined_symbol_name}
            )
            message_spec.add_main_content(element)
            
            # Process definition body
            body_id = self._process_node(node.definition_body_ast, message_spec)
            message_spec.add_discourse_relation("definition_body", element_id, body_id)
        
        else:
            raise ValueError(
                f"Unsupported AST node type '{type(node).__name__}' while processing "
                f"content element '{element_id}'"
            )
        
        return element_id
    
    def _get_operator_name(self, operator: AST_Node) -> str:
        """
        Get the name of an operator node.
        
        Args:
            operator: The operator node
            
        Returns:
            The name of the operator
        """
        if isinstance(operator, ConstantNode):
            return operator.name
        elif isinstance(operator, VariableNode):
            return operator.name
        else:
            return "unknown_operator"
    
    def _determine_relationships(self, message_spec: MessageSpecification) -> None:
        """
        Determine relationships between content elements.
        
        Args:
            message_spec: The message specification to update
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would use more complex logic to
        # determine relationships like causality, contrast, elaboration, etc.
        
        # For now, we just use the discourse relations already added during processing
        pass
    
    def _determine_temporal_ordering(self, message_spec: MessageSpecification) -> None:
        """
        Determine the temporal ordering of content elements.
        
        Args:
            message_spec: The message specification to update
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would analyze temporal markers,
        # tense information, and event ordering
        
        # For now, just add all main content elements in the order they appear
        for element in message_spec.main_content:
            message_spec.add_temporal_ordering(element.id)
    
    def _determine_focus(self, message_spec: MessageSpecification, 
                        context: Dict[str, Any]) -> None:
        """
        Determine the focus elements based on the context.
        
        Args:
            message_spec: The message specification to update
            context: Context information for content planning
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would consider discourse history,
        # user queries, and information structure
        
        # For now, just focus on the first main content element
        if message_spec.main_content:
            message_spec.add_focus_element(message_spec.main_content[0].id)
