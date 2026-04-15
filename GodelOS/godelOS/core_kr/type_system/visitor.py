"""
Type checking and inference visitor for AST nodes.

This module defines a visitor for type checking and inference of AST nodes.
"""

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from godelOS.core_kr.ast.nodes import (
    AST_Node, ASTVisitor, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode, LambdaNode, DefinitionNode
)
from godelOS.core_kr.type_system.types import Type, FunctionType
from godelOS.core_kr.type_system.environment import TypeEnvironment

if TYPE_CHECKING:
    from godelOS.core_kr.type_system.manager import TypeSystemManager


class Error:
    """Simple error class for type checking/inference errors."""
    
    def __init__(self, message: str, node: Optional[AST_Node] = None):
        self.message = message
        self.node = node
    
    def __str__(self) -> str:
        return self.message


class TypeInferenceVisitor(ASTVisitor[Tuple[Optional[Type], List[Error]]]):
    """
    Visitor for inferring the types of AST nodes.
    
    This visitor implements the visitor pattern to traverse the AST and infer
    the types of nodes based on their structure and the types of their components.
    """
    
    def __init__(self, type_system: 'TypeSystemManager', environment: TypeEnvironment):
        """
        Initialize a type inference visitor.
        
        Args:
            type_system: The type system manager to use for type checking
            environment: The type environment to use for variable lookups
        """
        self.type_system = type_system
        self.environment = environment
    
    def visit_constant(self, node: ConstantNode) -> Tuple[Optional[Type], List[Error]]:
        """
        Infer the type of a constant node.
        
        For constants, the type is already stored in the node.
        
        Args:
            node: The constant node
            
        Returns:
            The type of the constant and an empty list of errors
        """
        return node.type, []
    
    def visit_variable(self, node: VariableNode) -> Tuple[Optional[Type], List[Error]]:
        """
        Infer the type of a variable node.
        
        For variables, look up the type in the environment.
        
        Args:
            node: The variable node
            
        Returns:
            The type of the variable and a list of errors
        """
        var_type = self.environment.get_type(node)
        if var_type is None:
            # If not in environment, use the type stored in the node
            var_type = node.type
            if var_type is None:
                return None, [Error(f"Cannot determine type for variable {node.name}", node)]
        return var_type, []
    
    def visit_application(self, node: ApplicationNode) -> Tuple[Optional[Type], List[Error]]:
        """
        Infer the type of an application node.
        
        For applications, check that the operator has a function type
        and the arguments match the expected types.
        
        Args:
            node: The application node
            
        Returns:
            The type of the application and a list of errors
        """
        # Infer the type of the operator
        op_type, op_errors = node.operator.accept(self)
        if op_errors:
            return None, op_errors
        
        if not isinstance(op_type, FunctionType):
            return None, [Error(f"Operator {node.operator} is not a function", node.operator)]
        
        # Check that the number of arguments matches
        if len(node.arguments) != len(op_type.arg_types):
            return None, [Error(
                f"Function expects {len(op_type.arg_types)} arguments, got {len(node.arguments)}", 
                node
            )]
        
        # Check each argument type
        for i, arg in enumerate(node.arguments):
            arg_type, arg_errors = arg.accept(self)
            if arg_errors:
                return None, arg_errors
            
            if arg_type is None:
                return None, [Error(f"Cannot determine type for argument {i+1}", arg)]
            
            if not self.type_system.is_subtype(arg_type, op_type.arg_types[i]):
                return None, [Error(
                    f"Argument {i+1} has type {arg_type}, expected {op_type.arg_types[i]}", 
                    arg
                )]
        
        # The type of the application is the return type of the function
        return op_type.return_type, []
    
    def visit_quantifier(self, node: QuantifierNode) -> Tuple[Optional[Type], List[Error]]:
        """
        Infer the type of a quantifier node.
        
        For quantifiers, check that the scope is a boolean expression
        and return boolean type.
        
        Args:
            node: The quantifier node
            
        Returns:
            The type of the quantifier and a list of errors
        """
        boolean_type = self.type_system.get_type("Boolean")
        if boolean_type is None:
            return None, [Error("Boolean type not defined in type system", node)]
        
        # Create a new environment with the bound variables
        new_env = self.environment.extend()
        for var in node.bound_variables:
            new_env.set_type(var, var.type)
        
        # Create a new visitor with the extended environment
        new_visitor = TypeInferenceVisitor(self.type_system, new_env)
        
        # Check that the scope is a boolean expression
        scope_type, scope_errors = node.scope.accept(new_visitor)
        if scope_errors:
            return None, scope_errors
        
        if scope_type is None:
            return None, [Error("Cannot determine type for quantifier scope", node.scope)]
        
        if not self.type_system.is_subtype(scope_type, boolean_type):
            return None, [Error(
                f"Quantifier scope has type {scope_type}, expected {boolean_type}", 
                node.scope
            )]
        
        # Quantifiers always return boolean
        return boolean_type, []
    
    def visit_connective(self, node: ConnectiveNode) -> Tuple[Optional[Type], List[Error]]:
        """
        Infer the type of a connective node.
        
        For connectives, check that all operands are boolean expressions
        and return boolean type.
        
        Args:
            node: The connective node
            
        Returns:
            The type of the connective and a list of errors
        """
        boolean_type = self.type_system.get_type("Boolean")
        if boolean_type is None:
            return None, [Error("Boolean type not defined in type system", node)]
        
        for operand in node.operands:
            operand_type, operand_errors = operand.accept(self)
            if operand_errors:
                return None, operand_errors
            
            if operand_type is None:
                return None, [Error("Cannot determine type for connective operand", operand)]
            
            if not self.type_system.is_subtype(operand_type, boolean_type):
                return None, [Error(
                    f"Connective operand has type {operand_type}, expected {boolean_type}", 
                    operand
                )]
        
        # Connectives always return boolean
        return boolean_type, []
    
    def visit_modal_op(self, node: ModalOpNode) -> Tuple[Optional[Type], List[Error]]:
        """
        Infer the type of a modal operator node.
        
        For modal operators, check that the proposition is a boolean expression
        and return boolean type.
        
        Args:
            node: The modal operator node
            
        Returns:
            The type of the modal operator and a list of errors
        """
        boolean_type = self.type_system.get_type("Boolean")
        if boolean_type is None:
            return None, [Error("Boolean type not defined in type system", node)]
        
        # Check that the proposition is a boolean expression
        prop_type, prop_errors = node.proposition.accept(self)
        if prop_errors:
            return None, prop_errors
        
        if prop_type is None:
            return None, [Error("Cannot determine type for modal proposition", node.proposition)]
        
        if not self.type_system.is_subtype(prop_type, boolean_type):
            return None, [Error(
                f"Modal proposition has type {prop_type}, expected {boolean_type}", 
                node.proposition
            )]
        
        # If there's an agent or world, check its type (typically Entity or Agent)
        if node.agent_or_world:
            # The type depends on the modal operator
            # For epistemic operators (KNOWS, BELIEVES), the agent should be an Agent
            if node.modal_operator in ["KNOWS", "BELIEVES"]:
                agent_type = self.type_system.get_type("Agent")
                if agent_type is None:
                    return None, [Error("Agent type not defined in type system", node)]
                
                agent_world_type, agent_world_errors = node.agent_or_world.accept(self)
                if agent_world_errors:
                    return None, agent_world_errors
                
                if agent_world_type is None:
                    return None, [Error("Cannot determine type for modal agent/world", node.agent_or_world)]
                
                if not self.type_system.is_subtype(agent_world_type, agent_type):
                    return None, [Error(
                        f"Modal agent has type {agent_world_type}, expected {agent_type}", 
                        node.agent_or_world
                    )]
        
        # Modal operators always return boolean
        return boolean_type, []
    
    def visit_lambda(self, node: LambdaNode) -> Tuple[Optional[Type], List[Error]]:
        """
        Infer the type of a lambda node.
        
        For lambda expressions, create a new environment with the bound variables
        and infer the type of the body.
        
        Args:
            node: The lambda node
            
        Returns:
            The type of the lambda and a list of errors
        """
        # Create a new environment with the bound variables
        new_env = self.environment.extend()
        for var in node.bound_variables:
            new_env.set_type(var, var.type)
        
        # Create a new visitor with the extended environment
        new_visitor = TypeInferenceVisitor(self.type_system, new_env)
        
        # Infer the type of the body
        body_type, body_errors = node.body.accept(new_visitor)
        if body_errors:
            return None, body_errors
        
        if body_type is None:
            return None, [Error("Cannot determine type for lambda body", node.body)]
        
        # The type of the lambda is a function from the bound variables' types to the body type
        arg_types = [var.type for var in node.bound_variables]
        return FunctionType(arg_types, body_type), []
    
    def visit_definition(self, node: DefinitionNode) -> Tuple[Optional[Type], List[Error]]:
        """
        Infer the type of a definition node.
        
        For definitions, infer the type of the definition body and check that
        it matches the defined symbol type.
        
        Args:
            node: The definition node
            
        Returns:
            The type of the definition and a list of errors
        """
        # Infer the type of the definition body
        body_type, body_errors = node.definition_body_ast.accept(self)
        if body_errors:
            return None, body_errors
        
        if body_type is None:
            return None, [Error("Cannot determine type for definition body", node.definition_body_ast)]
        
        # Check that the body type matches the defined symbol type
        if not self.type_system.is_subtype(body_type, node.defined_symbol_type):
            return None, [Error(
                f"Definition body has type {body_type}, but symbol is defined with type {node.defined_symbol_type}",
                node
            )]
        
        # The type of the definition is the defined symbol type
        return node.defined_symbol_type, []


class TypeCheckingVisitor(ASTVisitor[List[Error]]):
    """
    Visitor for checking that AST nodes have the expected types.
    
    This visitor implements the visitor pattern to traverse the AST and check
    that nodes have the expected types.
    """
    
    def __init__(self, type_system: 'TypeSystemManager', environment: TypeEnvironment, expected_type: Type):
        """
        Initialize a type checking visitor.
        
        Args:
            type_system: The type system manager to use for type checking
            environment: The type environment to use for variable lookups
            expected_type: The expected type for the node
        """
        self.type_system = type_system
        self.environment = environment
        self.expected_type = expected_type
        self.inference_visitor = TypeInferenceVisitor(type_system, environment)
    
    def visit_constant(self, node: ConstantNode) -> List[Error]:
        """
        Check that a constant node has the expected type.
        
        Args:
            node: The constant node
            
        Returns:
            A list of errors, empty if the node has the expected type
        """
        if not self.type_system.is_subtype(node.type, self.expected_type):
            return [Error(f"Constant {node.name} has type {node.type}, expected {self.expected_type}", node)]
        return []
    
    def visit_variable(self, node: VariableNode) -> List[Error]:
        """
        Check that a variable node has the expected type.
        
        Args:
            node: The variable node
            
        Returns:
            A list of errors, empty if the node has the expected type
        """
        var_type, var_errors = self.inference_visitor.visit_variable(node)
        if var_errors:
            return var_errors
        
        if var_type is None:
            return [Error(f"Cannot determine type for variable {node.name}", node)]
        
        if not self.type_system.is_subtype(var_type, self.expected_type):
            return [Error(f"Variable {node.name} has type {var_type}, expected {self.expected_type}", node)]
        
        return []
    
    def visit_application(self, node: ApplicationNode) -> List[Error]:
        """
        Check that an application node has the expected type.
        
        Args:
            node: The application node
            
        Returns:
            A list of errors, empty if the node has the expected type
        """
        app_type, app_errors = self.inference_visitor.visit_application(node)
        if app_errors:
            return app_errors
        
        if app_type is None:
            return [Error(f"Cannot determine type for application {node}", node)]
        
        if not self.type_system.is_subtype(app_type, self.expected_type):
            return [Error(f"Application has type {app_type}, expected {self.expected_type}", node)]
        
        return []
    
    def visit_quantifier(self, node: QuantifierNode) -> List[Error]:
        """
        Check that a quantifier node has the expected type.
        
        Args:
            node: The quantifier node
            
        Returns:
            A list of errors, empty if the node has the expected type
        """
        quant_type, quant_errors = self.inference_visitor.visit_quantifier(node)
        if quant_errors:
            return quant_errors
        
        if quant_type is None:
            return [Error(f"Cannot determine type for quantifier {node}", node)]
        
        if not self.type_system.is_subtype(quant_type, self.expected_type):
            return [Error(f"Quantifier has type {quant_type}, expected {self.expected_type}", node)]
        
        return []
    
    def visit_connective(self, node: ConnectiveNode) -> List[Error]:
        """
        Check that a connective node has the expected type.
        
        Args:
            node: The connective node
            
        Returns:
            A list of errors, empty if the node has the expected type
        """
        conn_type, conn_errors = self.inference_visitor.visit_connective(node)
        if conn_errors:
            return conn_errors
        
        if conn_type is None:
            return [Error(f"Cannot determine type for connective {node}", node)]
        
        if not self.type_system.is_subtype(conn_type, self.expected_type):
            return [Error(f"Connective has type {conn_type}, expected {self.expected_type}", node)]
        
        return []
    
    def visit_modal_op(self, node: ModalOpNode) -> List[Error]:
        """
        Check that a modal operator node has the expected type.
        
        Args:
            node: The modal operator node
            
        Returns:
            A list of errors, empty if the node has the expected type
        """
        modal_type, modal_errors = self.inference_visitor.visit_modal_op(node)
        if modal_errors:
            return modal_errors
        
        if modal_type is None:
            return [Error(f"Cannot determine type for modal operator {node}", node)]
        
        if not self.type_system.is_subtype(modal_type, self.expected_type):
            return [Error(f"Modal operator has type {modal_type}, expected {self.expected_type}", node)]
        
        return []
    
    def visit_lambda(self, node: LambdaNode) -> List[Error]:
        """
        Check that a lambda node has the expected type.
        
        Args:
            node: The lambda node
            
        Returns:
            A list of errors, empty if the node has the expected type
        """
        lambda_type, lambda_errors = self.inference_visitor.visit_lambda(node)
        if lambda_errors:
            return lambda_errors
        
        if lambda_type is None:
            return [Error(f"Cannot determine type for lambda {node}", node)]
        
        if not self.type_system.is_subtype(lambda_type, self.expected_type):
            return [Error(f"Lambda has type {lambda_type}, expected {self.expected_type}", node)]
        
        return []
    
    def visit_definition(self, node: DefinitionNode) -> List[Error]:
        """
        Check that a definition node has the expected type.
        
        Args:
            node: The definition node
            
        Returns:
            A list of errors, empty if the node has the expected type
        """
        def_type, def_errors = self.inference_visitor.visit_definition(node)
        if def_errors:
            return def_errors
        
        if def_type is None:
            return [Error(f"Cannot determine type for definition {node}", node)]
        
        if not self.type_system.is_subtype(def_type, self.expected_type):
            return [Error(f"Definition has type {def_type}, expected {self.expected_type}", node)]
        
        return []