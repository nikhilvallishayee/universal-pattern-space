"""
AST Node classes for representing logical expressions.

This module defines the core AST node types used to represent logical expressions
in the GödelOS system, following the principles of immutability, typing, rich metadata,
and traversal support.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar, Generic, ForwardRef
from abc import ABC, abstractmethod
from copy import deepcopy

# Use string type annotation to break circular dependency
# Instead of: from godelOS.core_kr.type_system.types import Type
Type = ForwardRef('Type')

# Type variable for the visitor pattern return type
T = TypeVar('T')


class ASTVisitor(Generic[T], ABC):
    """
    Abstract visitor interface for AST nodes.
    
    This class defines the visitor interface for the visitor pattern.
    Concrete visitors should inherit from this class and implement
    the visit methods for each node type they want to handle.
    
    Type parameter T: The return type of the visit methods.
    """
    
    @abstractmethod
    def visit_constant(self, node: 'ConstantNode') -> T:
        """Visit a ConstantNode."""
        pass
    
    @abstractmethod
    def visit_variable(self, node: 'VariableNode') -> T:
        """Visit a VariableNode."""
        pass
    
    @abstractmethod
    def visit_application(self, node: 'ApplicationNode') -> T:
        """Visit an ApplicationNode."""
        pass
    
    @abstractmethod
    def visit_quantifier(self, node: 'QuantifierNode') -> T:
        """Visit a QuantifierNode."""
        pass
    
    @abstractmethod
    def visit_connective(self, node: 'ConnectiveNode') -> T:
        """Visit a ConnectiveNode."""
        pass
    
    @abstractmethod
    def visit_modal_op(self, node: 'ModalOpNode') -> T:
        """Visit a ModalOpNode."""
        pass
    
    @abstractmethod
    def visit_lambda(self, node: 'LambdaNode') -> T:
        """Visit a LambdaNode."""
        pass
    
    @abstractmethod
    def visit_definition(self, node: 'DefinitionNode') -> T:
        """Visit a DefinitionNode."""
        pass


class AST_Node(ABC):
    """
    Base class for all AST nodes.
    
    All AST nodes are immutable and carry type information and metadata.
    """
    
    def __init__(self, type_ref: 'Type', metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an AST node.
        
        Args:
            type_ref: Reference to the type of this node from TypeSystemManager
            metadata: Optional metadata (e.g., probability, source_location)
        """
        self._type = type_ref
        self._metadata = metadata or {}
    
    @property
    def type(self) -> 'Type':
        """Get the type of this node."""
        return self._type
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata of this node."""
        return self._metadata.copy()
    
    @abstractmethod
    def accept(self, visitor: ASTVisitor[T]) -> T:
        """
        Accept a visitor.
        
        This method implements the visitor pattern, allowing operations
        to be performed on the AST without modifying the node classes.
        
        Args:
            visitor: The visitor to accept
            
        Returns:
            The result of the visitor's visit method for this node
        """
        pass
    
    @abstractmethod
    def substitute(self, substitution: Dict['VariableNode', 'AST_Node']) -> 'AST_Node':
        """
        Substitute variables according to the given substitution.
        
        Args:
            substitution: A mapping from variables to their replacements
            
        Returns:
            A new AST node with the substitutions applied
        """
        pass
    
    @abstractmethod
    def contains_variable(self, variable: 'VariableNode') -> bool:
        """
        Check if this node contains the given variable.
        
        Args:
            variable: The variable to check for
            
        Returns:
            True if the variable is contained in this node, False otherwise
        """
        pass
    
    def with_metadata(self, **kwargs) -> 'AST_Node':
        """
        Create a new node with updated metadata.
        
        Args:
            **kwargs: Metadata key-value pairs to update
            
        Returns:
            A new node with the updated metadata
        """
        new_metadata = self.metadata
        new_metadata.update(kwargs)
        return self.with_updated_metadata(new_metadata)
    
    @abstractmethod
    def with_updated_metadata(self, metadata: Dict[str, Any]) -> 'AST_Node':
        """
        Create a new node with the given metadata.
        
        Args:
            metadata: The new metadata
            
        Returns:
            A new node with the given metadata
        """
        pass
    
    def __eq__(self, other: object) -> bool:
        """
        Structural equality based on content.
        
        Two AST nodes are equal if they have the same structure and content,
        regardless of their identity.
        """
        if not isinstance(other, AST_Node):
            return False
        return (self._type == other._type and
                self._metadata == other._metadata)
    
    def __hash__(self) -> int:
        """
        Hash based on content for use in sets/dicts.
        
        The hash is based on the node's content, not its identity.
        """
        return hash((self.__class__, self._type, frozenset(self._metadata.items())))


class ConstantNode(AST_Node):
    """
    Node representing a constant symbol or literal value.
    """
    
    def __init__(self, name: str, type_ref: 'Type', value: Any = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a constant node.
        
        Args:
            name: The name of the constant
            type_ref: Reference to the type of this constant
            value: Optional actual value if it's a literal (e.g., number, string)
            metadata: Optional metadata
        """
        super().__init__(type_ref, metadata)
        self._name = name
        self._value = value
    
    @property
    def name(self) -> str:
        """Get the name of the constant."""
        return self._name
    
    @property
    def value(self) -> Any:
        """Get the value of the constant if it's a literal."""
        return self._value
    
    def accept(self, visitor: ASTVisitor[T]) -> T:
        """Accept a visitor."""
        return visitor.visit_constant(self)
    
    def substitute(self, substitution: Dict['VariableNode', 'AST_Node']) -> 'AST_Node':
        """
        Substitute variables according to the given substitution.
        
        Constants don't contain variables, so this returns self.
        """
        return self
    
    def contains_variable(self, variable: 'VariableNode') -> bool:
        """
        Check if this node contains the given variable.
        
        Constants don't contain variables, so this always returns False.
        """
        return False
    
    def with_updated_metadata(self, metadata: Dict[str, Any]) -> 'ConstantNode':
        """Create a new node with the given metadata."""
        return ConstantNode(self._name, self._type, self._value, metadata)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConstantNode):
            return False
        return (super().__eq__(other) and
                self._name == other._name and
                self._value == other._value)
    
    def __hash__(self) -> int:
        return hash((super().__hash__(), self._name, self._value))
    
    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"ConstantNode(name='{self._name}', type={self._type})"


class VariableNode(AST_Node):
    """
    Node representing a variable, also used for bound variables in quantifiers/lambda.
    """
    
    def __init__(self, name: str, var_id: int, type_ref: 'Type',
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a variable node.
        
        Args:
            name: The name of the variable (e.g., "?x", "v1")
            var_id: Unique ID for this variable instance for alpha-equivalence
            type_ref: Reference to the type of this variable
            metadata: Optional metadata
        """
        super().__init__(type_ref, metadata)
        self._name = name
        self._var_id = var_id
    
    @property
    def name(self) -> str:
        """Get the name of the variable."""
        return self._name
    
    @property
    def var_id(self) -> int:
        """Get the unique ID of the variable."""
        return self._var_id
    
    def accept(self, visitor: ASTVisitor[T]) -> T:
        """Accept a visitor."""
        return visitor.visit_variable(self)
    
    def substitute(self, substitution: Dict['VariableNode', 'AST_Node']) -> 'AST_Node':
        """
        Substitute variables according to the given substitution.
        
        If this variable is in the substitution, return its replacement.
        Otherwise, return self.
        """
        for var, replacement in substitution.items():
            if self == var:
                return replacement
        return self
    
    def contains_variable(self, variable: 'VariableNode') -> bool:
        """
        Check if this node contains the given variable.
        
        Returns True if this variable is equal to the given variable.
        """
        return self == variable
    
    def with_updated_metadata(self, metadata: Dict[str, Any]) -> 'VariableNode':
        """Create a new node with the given metadata."""
        return VariableNode(self._name, self._var_id, self._type, metadata)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VariableNode):
            return False
        return (super().__eq__(other) and
                self._name == other._name and
                self._var_id == other._var_id)
    
    def __hash__(self) -> int:
        return hash((super().__hash__(), self._name, self._var_id))
    
    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"VariableNode(name='{self._name}', id={self._var_id}, type={self._type})"


class ApplicationNode(AST_Node):
    """
    Node representing a function or predicate application.
    """
    
    def __init__(self, operator: AST_Node, arguments: List[AST_Node], type_ref: 'Type', 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an application node.
        
        Args:
            operator: The operator being applied (e.g., PredicateNode, FunctionNode, or VariableNode for HOL)
            arguments: The arguments to the operator
            type_ref: Reference to the type of this application
            metadata: Optional metadata
        """
        super().__init__(type_ref, metadata)
        self._operator = operator
        self._arguments = tuple(arguments)  # Make immutable
    
    @property
    def operator(self) -> AST_Node:
        """Get the operator of the application."""
        return self._operator
    
    @property
    def arguments(self) -> Tuple[AST_Node, ...]:
        """Get the arguments of the application."""
        return self._arguments
    
    def accept(self, visitor: ASTVisitor[T]) -> T:
        """Accept a visitor."""
        return visitor.visit_application(self)
    
    def substitute(self, substitution: Dict['VariableNode', 'AST_Node']) -> 'ApplicationNode':
        """
        Substitute variables according to the given substitution.
        
        Returns a new ApplicationNode with substitutions applied to the operator and arguments.
        """
        new_operator = self._operator.substitute(substitution)
        new_arguments = tuple(arg.substitute(substitution) for arg in self._arguments)
        
        # Only create a new node if something changed
        if new_operator is self._operator and all(new_arg is old_arg for new_arg, old_arg in zip(new_arguments, self._arguments)):
            return self
        
        return ApplicationNode(new_operator, list(new_arguments), self._type, self._metadata.copy())
    
    def contains_variable(self, variable: 'VariableNode') -> bool:
        """
        Check if this node contains the given variable.
        
        Returns True if the operator or any argument contains the variable.
        """
        return (self._operator.contains_variable(variable) or
                any(arg.contains_variable(variable) for arg in self._arguments))
    
    def with_updated_metadata(self, metadata: Dict[str, Any]) -> 'ApplicationNode':
        """Create a new node with the given metadata."""
        return ApplicationNode(self._operator, list(self._arguments), self._type, metadata)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ApplicationNode):
            return False
        return (super().__eq__(other) and
                self._operator == other._operator and
                self._arguments == other._arguments)
    
    def __hash__(self) -> int:
        return hash((super().__hash__(), self._operator, self._arguments))
    
    def __str__(self) -> str:
        args_str = ", ".join(str(a) for a in self._arguments)
        return f"{self._operator}({args_str})"

    def __repr__(self) -> str:
        return f"ApplicationNode(operator={self._operator}, args={self._arguments})"


class QuantifierNode(AST_Node):
    """
    Node representing a quantifier (∀, ∃).
    """
    
    def __init__(self, quantifier_type: str, bound_variables: List[VariableNode], 
                 scope: AST_Node, type_ref: 'Type', 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a quantifier node.
        
        Args:
            quantifier_type: The type of quantifier ("FORALL", "EXISTS")
            bound_variables: List of variables bound by this quantifier
            scope: The sub-formula governed by this quantifier
            type_ref: Reference to the type of this quantifier
            metadata: Optional metadata
        """
        super().__init__(type_ref, metadata)
        self._quantifier_type = quantifier_type
        self._bound_variables = tuple(bound_variables)  # Make immutable
        self._scope = scope
    
    @property
    def quantifier_type(self) -> str:
        """Get the type of quantifier."""
        return self._quantifier_type
    
    @property
    def bound_variables(self) -> Tuple[VariableNode, ...]:
        """Get the bound variables of the quantifier."""
        return self._bound_variables
    
    @property
    def scope(self) -> AST_Node:
        """Get the scope of the quantifier."""
        return self._scope
    
    def accept(self, visitor: ASTVisitor[T]) -> T:
        """Accept a visitor."""
        return visitor.visit_quantifier(self)
    
    def substitute(self, substitution: Dict['VariableNode', 'AST_Node']) -> 'QuantifierNode':
        """
        Substitute variables according to the given substitution.
        
        Returns a new QuantifierNode with substitutions applied to the scope,
        but not to bound variables. Removes bound variables from the substitution.
        """
        # Create a new substitution without the bound variables
        filtered_substitution = {var: repl for var, repl in substitution.items()
                               if var not in self._bound_variables}
        
        # Only substitute in the scope if there are still substitutions to apply
        if filtered_substitution:
            new_scope = self._scope.substitute(filtered_substitution)
            if new_scope is not self._scope:
                return QuantifierNode(self._quantifier_type, list(self._bound_variables),
                                     new_scope, self._type, self._metadata.copy())
        
        return self
    
    def contains_variable(self, variable: 'VariableNode') -> bool:
        """
        Check if this node contains the given variable.
        
        Returns True if the scope contains the variable and it's not bound by this quantifier.
        """
        if variable in self._bound_variables:
            return False
        return self._scope.contains_variable(variable)
    
    def with_updated_metadata(self, metadata: Dict[str, Any]) -> 'QuantifierNode':
        """Create a new node with the given metadata."""
        return QuantifierNode(self._quantifier_type, list(self._bound_variables),
                             self._scope, self._type, metadata)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QuantifierNode):
            return False
        return (super().__eq__(other) and
                self._quantifier_type == other._quantifier_type and
                self._bound_variables == other._bound_variables and
                self._scope == other._scope)
    
    def __hash__(self) -> int:
        return hash((super().__hash__(), self._quantifier_type,
                    self._bound_variables, self._scope))
    
    def __str__(self) -> str:
        vars_str = ", ".join(str(v) for v in self._bound_variables)
        q = "∀" if self._quantifier_type == "FORALL" else "∃"
        return f"{q}{vars_str}.{self._scope}"

    def __repr__(self) -> str:
        return f"QuantifierNode(type='{self._quantifier_type}', vars={self._bound_variables})"


class ConnectiveNode(AST_Node):
    """
    Node representing a logical connective (¬, ∧, ∨, ⇒, ≡).
    """
    
    def __init__(self, connective_type: str, operands: List[AST_Node], type_ref: 'Type', 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a connective node.
        
        Args:
            connective_type: The type of connective ("NOT", "AND", "OR", "IMPLIES", "EQUIV")
            operands: The operands of the connective
            type_ref: Reference to the type of this connective
            metadata: Optional metadata
        """
        super().__init__(type_ref, metadata)
        self._connective_type = connective_type
        self._operands = tuple(operands)  # Make immutable
    
    @property
    def connective_type(self) -> str:
        """Get the type of connective."""
        return self._connective_type
    
    @property
    def operands(self) -> Tuple[AST_Node, ...]:
        """Get the operands of the connective."""
        return self._operands
    
    def accept(self, visitor: ASTVisitor[T]) -> T:
        """Accept a visitor."""
        return visitor.visit_connective(self)
    
    def substitute(self, substitution: Dict['VariableNode', 'AST_Node']) -> 'ConnectiveNode':
        """
        Substitute variables according to the given substitution.
        
        Returns a new ConnectiveNode with substitutions applied to all operands.
        """
        new_operands = tuple(op.substitute(substitution) for op in self._operands)
        
        # Only create a new node if something changed
        if all(new_op is old_op for new_op, old_op in zip(new_operands, self._operands)):
            return self
        
        return ConnectiveNode(self._connective_type, list(new_operands),
                             self._type, self._metadata.copy())
    
    def contains_variable(self, variable: 'VariableNode') -> bool:
        """
        Check if this node contains the given variable.
        
        Returns True if any operand contains the variable.
        """
        return any(op.contains_variable(variable) for op in self._operands)
    
    def with_updated_metadata(self, metadata: Dict[str, Any]) -> 'ConnectiveNode':
        """Create a new node with the given metadata."""
        return ConnectiveNode(self._connective_type, list(self._operands),
                             self._type, metadata)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConnectiveNode):
            return False
        return (super().__eq__(other) and
                self._connective_type == other._connective_type and
                self._operands == other._operands)
    
    def __hash__(self) -> int:
        return hash((super().__hash__(), self._connective_type, self._operands))
    
    def __str__(self) -> str:
        if self._connective_type == "NOT":
            return f"¬{self._operands[0]}"
        elif self._connective_type == "AND":
            return f"({' ∧ '.join(str(o) for o in self._operands)})"
        elif self._connective_type == "OR":
            return f"({' ∨ '.join(str(o) for o in self._operands)})"
        elif self._connective_type == "IMPLIES":
            return f"({self._operands[0]} → {self._operands[1]})"
        elif self._connective_type == "EQUIV":
            return f"({self._operands[0]} ↔ {self._operands[1]})"
        return f"{self._connective_type}({', '.join(str(o) for o in self._operands)})"

    def __repr__(self) -> str:
        return f"ConnectiveNode(type='{self._connective_type}', operands={self._operands})"


class ModalOpNode(AST_Node):
    """
    Node representing a modal operator (K, B, P, O, F, etc.).
    """
    
    def __init__(self, modal_operator: str, proposition: AST_Node, type_ref: 'Type', 
                 agent_or_world: Optional[AST_Node] = None, 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a modal operator node.
        
        Args:
            modal_operator: The modal operator ("KNOWS", "BELIEVES", "POSSIBLE_WORLD_TRUTH", "OBLIGATORY")
            proposition: The proposition to which the modal operator applies
            type_ref: Reference to the type of this modal operator
            agent_or_world: Optional agent or world for epistemic/deontic operators
            metadata: Optional metadata
        """
        super().__init__(type_ref, metadata)
        self._modal_operator = modal_operator
        self._proposition = proposition
        self._agent_or_world = agent_or_world
    
    @property
    def modal_operator(self) -> str:
        """Get the modal operator."""
        return self._modal_operator
    
    @property
    def proposition(self) -> AST_Node:
        """Get the proposition to which the modal operator applies."""
        return self._proposition
    
    @property
    def agent_or_world(self) -> Optional[AST_Node]:
        """Get the agent or world for epistemic/deontic operators."""
        return self._agent_or_world
    
    def accept(self, visitor: ASTVisitor[T]) -> T:
        """Accept a visitor."""
        return visitor.visit_modal_op(self)
    
    def substitute(self, substitution: Dict['VariableNode', 'AST_Node']) -> 'ModalOpNode':
        """
        Substitute variables according to the given substitution.
        
        Returns a new ModalOpNode with substitutions applied to the proposition and agent_or_world.
        """
        new_proposition = self._proposition.substitute(substitution)
        new_agent_or_world = self._agent_or_world.substitute(substitution) if self._agent_or_world else None
        
        # Only create a new node if something changed
        if (new_proposition is self._proposition and
            new_agent_or_world is self._agent_or_world):
            return self
        
        return ModalOpNode(self._modal_operator, new_proposition, self._type,
                          new_agent_or_world, self._metadata.copy())
    
    def contains_variable(self, variable: 'VariableNode') -> bool:
        """
        Check if this node contains the given variable.
        
        Returns True if the proposition or agent_or_world contains the variable.
        """
        return (self._proposition.contains_variable(variable) or
                (self._agent_or_world and self._agent_or_world.contains_variable(variable)))
    
    def with_updated_metadata(self, metadata: Dict[str, Any]) -> 'ModalOpNode':
        """Create a new node with the given metadata."""
        return ModalOpNode(self._modal_operator, self._proposition, self._type,
                          self._agent_or_world, metadata)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModalOpNode):
            return False
        return (super().__eq__(other) and
                self._modal_operator == other._modal_operator and
                self._proposition == other._proposition and
                self._agent_or_world == other._agent_or_world)
    
    def __hash__(self) -> int:
        return hash((super().__hash__(), self._modal_operator,
                    self._proposition, self._agent_or_world))
    
    def __str__(self) -> str:
        if self._agent_or_world:
            return f"{self._modal_operator}_{self._agent_or_world}({self._proposition})"
        return f"{self._modal_operator}({self._proposition})"

    def __repr__(self) -> str:
        return f"ModalOpNode(operator='{self._modal_operator}', prop={self._proposition})"


class LambdaNode(AST_Node):
    """
    Node representing a lambda abstraction (λx. P(x)).
    """
    
    def __init__(self, bound_variables: List[VariableNode], body: AST_Node, type_ref: 'Type', 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a lambda node.
        
        Args:
            bound_variables: List of variables bound by this lambda
            body: The body of the lambda
            type_ref: Reference to the type of this lambda
            metadata: Optional metadata
        """
        super().__init__(type_ref, metadata)
        self._bound_variables = tuple(bound_variables)  # Make immutable
        self._body = body
    
    @property
    def bound_variables(self) -> Tuple[VariableNode, ...]:
        """Get the bound variables of the lambda."""
        return self._bound_variables
    
    @property
    def body(self) -> AST_Node:
        """Get the body of the lambda."""
        return self._body
    
    def accept(self, visitor: ASTVisitor[T]) -> T:
        """Accept a visitor."""
        return visitor.visit_lambda(self)
    
    def substitute(self, substitution: Dict['VariableNode', 'AST_Node']) -> 'LambdaNode':
        """
        Substitute variables according to the given substitution.
        
        Returns a new LambdaNode with substitutions applied to the body,
        but not to bound variables. Removes bound variables from the substitution.
        """
        # Create a new substitution without the bound variables
        filtered_substitution = {var: repl for var, repl in substitution.items()
                               if var not in self._bound_variables}
        
        # Only substitute in the body if there are still substitutions to apply
        if filtered_substitution:
            new_body = self._body.substitute(filtered_substitution)
            if new_body is not self._body:
                return LambdaNode(list(self._bound_variables), new_body,
                                 self._type, self._metadata.copy())
        
        return self
    
    def contains_variable(self, variable: 'VariableNode') -> bool:
        """
        Check if this node contains the given variable.
        
        Returns True if the body contains the variable and it's not bound by this lambda.
        """
        if variable in self._bound_variables:
            return False
        return self._body.contains_variable(variable)
    
    def with_updated_metadata(self, metadata: Dict[str, Any]) -> 'LambdaNode':
        """Create a new node with the given metadata."""
        return LambdaNode(list(self._bound_variables), self._body, self._type, metadata)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LambdaNode):
            return False
        return (super().__eq__(other) and
                self._bound_variables == other._bound_variables and
                self._body == other._body)
    
    def __hash__(self) -> int:
        return hash((super().__hash__(), self._bound_variables, self._body))
    
    def __str__(self) -> str:
        vars_str = ", ".join(str(v) for v in self._bound_variables)
        return f"λ{vars_str}.{self._body}"

    def __repr__(self) -> str:
        return f"LambdaNode(vars={self._bound_variables}, body={self._body})"


class DefinitionNode(AST_Node):
    """
    Node representing a definition of a constant, function, or predicate.
    """
    
    def __init__(self, defined_symbol_name: str, defined_symbol_type: 'Type', 
                 definition_body_ast: AST_Node, type_ref: 'Type', 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a definition node.
        
        Args:
            defined_symbol_name: The name of the defined symbol
            defined_symbol_type: The type of the defined symbol
            definition_body_ast: The expression defining the symbol
            type_ref: Reference to the type of this definition
            metadata: Optional metadata
        """
        super().__init__(type_ref, metadata)
        self._defined_symbol_name = defined_symbol_name
        self._defined_symbol_type = defined_symbol_type
        self._definition_body_ast = definition_body_ast
    
    @property
    def defined_symbol_name(self) -> str:
        """Get the name of the defined symbol."""
        return self._defined_symbol_name
    
    @property
    def defined_symbol_type(self) -> 'Type':
        """Get the type of the defined symbol."""
        return self._defined_symbol_type
    
    @property
    def definition_body_ast(self) -> AST_Node:
        """Get the expression defining the symbol."""
        return self._definition_body_ast
    
    def accept(self, visitor: ASTVisitor[T]) -> T:
        """Accept a visitor."""
        return visitor.visit_definition(self)
    
    def substitute(self, substitution: Dict['VariableNode', 'AST_Node']) -> 'DefinitionNode':
        """
        Substitute variables according to the given substitution.
        
        Returns a new DefinitionNode with substitutions applied to the definition body.
        """
        new_body = self._definition_body_ast.substitute(substitution)
        
        # Only create a new node if something changed
        if new_body is not self._definition_body_ast:
            return DefinitionNode(self._defined_symbol_name, self._defined_symbol_type,
                                 new_body, self._type, self._metadata.copy())
        
        return self
    
    def contains_variable(self, variable: 'VariableNode') -> bool:
        """
        Check if this node contains the given variable.
        
        Returns True if the definition body contains the variable.
        """
        return self._definition_body_ast.contains_variable(variable)
    
    def with_updated_metadata(self, metadata: Dict[str, Any]) -> 'DefinitionNode':
        """Create a new node with the given metadata."""
        return DefinitionNode(self._defined_symbol_name, self._defined_symbol_type,
                             self._definition_body_ast, self._type, metadata)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DefinitionNode):
            return False
        return (super().__eq__(other) and
                self._defined_symbol_name == other._defined_symbol_name and
                self._defined_symbol_type == other._defined_symbol_type and
                self._definition_body_ast == other._definition_body_ast)
    
    def __hash__(self) -> int:
        return hash((super().__hash__(), self._defined_symbol_name,
                    self._defined_symbol_type, self._definition_body_ast))
    
    def __str__(self) -> str:
        return f"{self._defined_symbol_name} := {self._definition_body_ast}"

    def __repr__(self) -> str:
        return f"DefinitionNode(name='{self._defined_symbol_name}', body={self._definition_body_ast})"