"""
Formalizer (F) for GödelOS NLU Pipeline.

This module provides functionality for:
1. Converting Intermediate Semantic Representation (ISR) to HOL AST nodes
2. Handling quantification, logical operators, and predicates
3. Resolving remaining ambiguities

It serves as the third stage in the NLU pipeline, converting semantic
representations into formal logical structures compatible with the KR System.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union, cast
from dataclasses import dataclass, field
import logging
import re

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode
)
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import Type, AtomicType, FunctionType

from godelOS.nlu_nlg.nlu.semantic_interpreter import (
    IntermediateSemanticRepresentation, SemanticNode, Predicate, 
    SemanticArgument, SemanticRelation, LogicalOperator, RelationType, SemanticRole
)


@dataclass
class FormalizationContext:
    """
    Context for the formalization process.
    
    Maintains state and mappings during the conversion of ISR to HOL AST.
    """
    type_system: TypeSystemManager
    variable_counter: int = 0
    entity_to_var: Dict[str, VariableNode] = field(default_factory=dict)
    entity_to_const: Dict[str, ConstantNode] = field(default_factory=dict)
    predicate_to_const: Dict[str, ConstantNode] = field(default_factory=dict)
    
    # Type references for convenience
    entity_type: Optional[Type] = None
    boolean_type: Optional[Type] = None
    proposition_type: Optional[Type] = None
    
    def __post_init__(self):
        """Initialize type references."""
        self.entity_type = self.type_system.get_type("Entity")
        self.boolean_type = self.type_system.get_type("Boolean")
        self.proposition_type = self.type_system.get_type("Proposition")
    
    def get_new_variable(self, name_hint: str, type_ref: Type) -> VariableNode:
        """
        Create a new variable with a unique ID.
        
        Args:
            name_hint: A hint for the variable name
            type_ref: The type of the variable
            
        Returns:
            A new VariableNode
        """
        # Sanitize the name hint
        sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '', name_hint.lower())
        if not sanitized_name:
            sanitized_name = "x"
        
        # Create a new variable
        var_id = self.variable_counter
        self.variable_counter += 1
        
        return VariableNode(f"?{sanitized_name}_{var_id}", var_id, type_ref)


class Formalizer:
    """
    Converts Intermediate Semantic Representation to HOL AST nodes.
    
    This class is responsible for translating the semantic representation
    produced by the SemanticInterpreter into formal logical structures
    compatible with the KR System.
    """
    
    def __init__(self, type_system: TypeSystemManager):
        """
        Initialize the formalizer.
        
        Args:
            type_system: The type system manager for type validation and inference
        """
        self.type_system = type_system
        self.logger = logging.getLogger(__name__)
    
    def formalize(self, isr: IntermediateSemanticRepresentation) -> List[AST_Node]:
        """
        Convert the ISR to HOL AST nodes.
        
        Args:
            isr: The Intermediate Semantic Representation
            
        Returns:
            A list of AST nodes representing the formalized logical expressions
        """
        # Create the formalization context
        context = FormalizationContext(type_system=self.type_system)
        
        # Formalize each root node in the ISR
        ast_nodes = []
        for root_node in isr.root_nodes:
            ast_node = self._formalize_node(root_node, context)
            if ast_node:
                ast_nodes.append(ast_node)
        
        return ast_nodes
    
    def _formalize_node(self, node: SemanticNode, context: FormalizationContext) -> Optional[AST_Node]:
        """
        Formalize a semantic node to an AST node.
        
        Args:
            node: The semantic node to formalize
            context: The formalization context
            
        Returns:
            An AST node, or None if formalization failed
        """
        if node.node_type == "predicate":
            return self._formalize_predicate(node, context)
        elif node.node_type == "entity":
            return self._formalize_entity(node, context)
        elif node.node_type == "logical_expression":
            return self._formalize_logical_expression(node, context)
        else:
            self.logger.warning(f"Unknown node type: {node.node_type}")
            return None
    
    def _formalize_predicate(self, node: SemanticNode, context: FormalizationContext) -> Optional[AST_Node]:
        """
        Formalize a predicate node to an AST node.
        
        Args:
            node: The predicate node to formalize
            context: The formalization context
            
        Returns:
            An AST node, or None if formalization failed
        """
        if not node.content or not isinstance(node.content, Predicate):
            self.logger.warning("Predicate node has no content or content is not a Predicate")
            return None
        
        predicate = cast(Predicate, node.content)
        
        # Get or create a constant for the predicate
        if predicate.lemma in context.predicate_to_const:
            pred_const = context.predicate_to_const[predicate.lemma]
        else:
            # Determine the type of the predicate
            arg_types = []
            for arg in predicate.arguments:
                arg_types.append(context.entity_type or self.type_system.get_type("Entity"))
            
            # Create a function type for the predicate
            if context.boolean_type:
                pred_type = FunctionType(arg_types, context.boolean_type)
            else:
                # Fallback to using the proposition type
                pred_type = context.proposition_type or self.type_system.get_type("Proposition")
            
            # Create a constant for the predicate
            pred_const = ConstantNode(predicate.lemma, pred_type)
            context.predicate_to_const[predicate.lemma] = pred_const
        
        # Formalize the arguments
        arg_nodes = []
        for arg in predicate.arguments:
            # Find the corresponding entity node
            entity_node = None
            for relation in node.relations:
                if isinstance(relation.target, SemanticNode) and relation.target.content == arg:
                    entity_node = relation.target
                    break
            
            # If we found the entity node, formalize it
            if entity_node:
                arg_node = self._formalize_entity(entity_node, context)
                if arg_node:
                    arg_nodes.append(arg_node)
            else:
                # If we didn't find the entity node, create a new variable
                var_node = context.get_new_variable(
                    arg.text,
                    context.entity_type or self.type_system.get_type("Entity")
                )
                arg_nodes.append(var_node)
        
        # Create an application node for the predicate
        app_node = ApplicationNode(
            pred_const,
            arg_nodes,
            context.boolean_type or context.proposition_type or self.type_system.get_type("Proposition")
        )
        
        # Handle negation
        if predicate.negated:
            return ConnectiveNode(
                "NOT",
                [app_node],
                context.proposition_type or self.type_system.get_type("Proposition")
            )
        
        # Handle modality
        if predicate.modality:
            if predicate.modality == "possible":
                return ModalOpNode(
                    "POSSIBLE_WORLD_TRUTH",
                    app_node,
                    context.proposition_type or self.type_system.get_type("Proposition")
                )
            elif predicate.modality == "necessary":
                return ModalOpNode(
                    "NECESSARY",
                    app_node,
                    context.proposition_type or self.type_system.get_type("Proposition")
                )
            elif predicate.modality == "obligatory":
                return ModalOpNode(
                    "OBLIGATORY",
                    app_node,
                    context.proposition_type or self.type_system.get_type("Proposition")
                )
        
        return app_node
    
    def _formalize_entity(self, node: SemanticNode, context: FormalizationContext) -> Optional[AST_Node]:
        """
        Formalize an entity node to an AST node.
        
        Args:
            node: The entity node to formalize
            context: The formalization context
            
        Returns:
            An AST node, or None if formalization failed
        """
        if not node.content or not isinstance(node.content, SemanticArgument):
            self.logger.warning("Entity node has no content or content is not a SemanticArgument")
            return None
        
        entity = cast(SemanticArgument, node.content)
        
        # Check if we already have a variable or constant for this entity
        if node.id in context.entity_to_var:
            return context.entity_to_var[node.id]
        if node.id in context.entity_to_const:
            return context.entity_to_const[node.id]
        
        # Determine if the entity should be a variable or a constant
        if entity.entity and entity.entity.label:
            # Named entities are typically constants
            const_node = ConstantNode(
                entity.text,
                context.entity_type or self.type_system.get_type("Entity")
            )
            context.entity_to_const[node.id] = const_node
            return const_node
        else:
            # Other entities are typically variables
            var_node = context.get_new_variable(
                entity.text,
                context.entity_type or self.type_system.get_type("Entity")
            )
            context.entity_to_var[node.id] = var_node
            return var_node
    
    def _formalize_logical_expression(self, node: SemanticNode, context: FormalizationContext) -> Optional[AST_Node]:
        """
        Formalize a logical expression node to an AST node.
        
        Args:
            node: The logical expression node to formalize
            context: The formalization context
            
        Returns:
            An AST node, or None if formalization failed
        """
        if not node.operator:
            self.logger.warning("Logical expression node has no operator")
            return None
        
        # Formalize the children
        child_nodes = []
        for child in node.children:
            child_node = self._formalize_node(child, context)
            if child_node:
                child_nodes.append(child_node)
        
        # If no children were formalized, return None
        if not child_nodes:
            self.logger.warning("No children were formalized for logical expression")
            return None
        
        # Create the appropriate node based on the operator
        if node.operator == LogicalOperator.AND:
            return ConnectiveNode(
                "AND",
                child_nodes,
                context.proposition_type or self.type_system.get_type("Proposition")
            )
        elif node.operator == LogicalOperator.OR:
            return ConnectiveNode(
                "OR",
                child_nodes,
                context.proposition_type or self.type_system.get_type("Proposition")
            )
        elif node.operator == LogicalOperator.NOT:
            return ConnectiveNode(
                "NOT",
                child_nodes,
                context.proposition_type or self.type_system.get_type("Proposition")
            )
        elif node.operator == LogicalOperator.IMPLIES:
            return ConnectiveNode(
                "IMPLIES",
                child_nodes,
                context.proposition_type or self.type_system.get_type("Proposition")
            )
        elif node.operator == LogicalOperator.EQUIVALENT:
            return ConnectiveNode(
                "EQUIV",
                child_nodes,
                context.proposition_type or self.type_system.get_type("Proposition")
            )
        elif node.operator == LogicalOperator.FORALL:
            # For quantifiers, we need to extract the variables
            if len(child_nodes) < 2:
                self.logger.warning("Not enough children for FORALL quantifier")
                return None
            
            # The first child should be a variable
            if not isinstance(child_nodes[0], VariableNode):
                self.logger.warning("First child of FORALL is not a variable")
                return None
            
            # The rest of the children form the scope
            if len(child_nodes) == 2:
                scope = child_nodes[1]
            else:
                # If there are multiple children in the scope, combine them with AND
                scope = ConnectiveNode(
                    "AND",
                    child_nodes[1:],
                    context.proposition_type or self.type_system.get_type("Proposition")
                )
            
            return QuantifierNode(
                "FORALL",
                [child_nodes[0]],
                scope,
                context.proposition_type or self.type_system.get_type("Proposition")
            )
        elif node.operator == LogicalOperator.EXISTS:
            # For quantifiers, we need to extract the variables
            if len(child_nodes) < 2:
                self.logger.warning("Not enough children for EXISTS quantifier")
                return None
            
            # The first child should be a variable
            if not isinstance(child_nodes[0], VariableNode):
                self.logger.warning("First child of EXISTS is not a variable")
                return None
            
            # The rest of the children form the scope
            if len(child_nodes) == 2:
                scope = child_nodes[1]
            else:
                # If there are multiple children in the scope, combine them with AND
                scope = ConnectiveNode(
                    "AND",
                    child_nodes[1:],
                    context.proposition_type or self.type_system.get_type("Proposition")
                )
            
            return QuantifierNode(
                "EXISTS",
                [child_nodes[0]],
                scope,
                context.proposition_type or self.type_system.get_type("Proposition")
            )
        
        self.logger.warning(f"Unknown logical operator: {node.operator}")
        return None


def create_ast_from_isr(isr: IntermediateSemanticRepresentation, type_system: TypeSystemManager) -> List[AST_Node]:
    """
    Create AST nodes from an Intermediate Semantic Representation.
    
    This is a convenience function that creates a Formalizer and uses it to
    convert the ISR to AST nodes.
    
    Args:
        isr: The Intermediate Semantic Representation
        type_system: The type system manager
        
    Returns:
        A list of AST nodes representing the formalized logical expressions
    """
    formalizer = Formalizer(type_system)
    return formalizer.formalize(isr)