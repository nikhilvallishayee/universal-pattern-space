"""
Unification Result wrapper class.

This module provides a consistent interface for unification results,
abstracting away the different return types used internally.
"""

from typing import Dict, List, Optional
from godelOS.core_kr.ast.nodes import AST_Node, VariableNode


class Error:
    """An error during unification."""
    
    def __init__(self, message: str, node1: Optional[AST_Node] = None, node2: Optional[AST_Node] = None):
        """
        Initialize an error.
        
        Args:
            message: The error message
            node1: Optional first node involved in the error
            node2: Optional second node involved in the error
        """
        self.message = message
        self.node1 = node1
        self.node2 = node2
    
    def __str__(self) -> str:
        return self.message


class UnificationResult:
    """
    Wrapper class for unification results.
    
    Provides a consistent interface regardless of the internal representation
    used by the unification engine.
    """
    
    def __init__(self, success: bool, substitution: Optional[Dict[VariableNode, AST_Node]] = None, 
                 errors: Optional[List[Error]] = None):
        """
        Initialize a unification result.
        
        Args:
            success: Whether unification was successful
            substitution: The variable substitutions if successful
            errors: List of errors if unsuccessful
        """
        self._success = success
        self._substitution = substitution or {}
        self._errors = errors or []
    
    def is_success(self) -> bool:
        """Check if unification was successful."""
        return self._success
    
    @property
    def substitution(self) -> Dict[VariableNode, AST_Node]:
        """Get the variable substitutions."""
        return self._substitution
    
    @property
    def errors(self) -> List[Error]:
        """Get the list of errors."""
        return self._errors
    
    @classmethod
    def success(cls, substitution: Dict[VariableNode, AST_Node]) -> 'UnificationResult':
        """Create a successful unification result."""
        return cls(True, substitution)
    
    @classmethod
    def failure(cls, errors: List[Error]) -> 'UnificationResult':
        """Create a failed unification result."""
        return cls(False, None, errors)
    
    @classmethod
    def from_engine_result(cls, result, errors: Optional[List[Error]] = None) -> 'UnificationResult':
        """
        Create a UnificationResult from the various return types of the unification engine.
        
        Args:
            result: The result from the unification engine - can be:
                    - Dict[VariableNode, AST_Node] for enhanced tests
                    - Tuple[Dict[int, AST_Node], List[Error]] for regular tests 
                    - Tuple[None, List[Error]] for failed unification
                    - None for failed unification
            errors: Optional list of errors if not included in result
            
        Returns:
            UnificationResult object with consistent interface
        """
        if result is None:
            return cls.failure(errors or [])
        
        if isinstance(result, tuple):
            bindings, error_list = result
            if bindings is None:
                return cls.failure(error_list)
            
            # Convert ID-based bindings to VariableNode-based
            var_substitution = {}
            if isinstance(bindings, dict):
                for key, value in bindings.items():
                    if isinstance(key, int):
                        # Create a VariableNode for the ID
                        # In practice, we should have access to the original variable
                        # For now, create a temporary one
                        var = VariableNode(f"?var{key}", key, value.type if hasattr(value, 'type') else None)
                        var_substitution[var] = value
                    elif isinstance(key, VariableNode):
                        var_substitution[key] = value
                    else:
                        # Handle unexpected key types
                        continue
            
            return cls.success(var_substitution)
        
        elif isinstance(result, dict):
            # Enhanced test result - already has VariableNode keys
            return cls.success(result)
        
        else:
            # Unexpected result type
            return cls.failure(errors or [])
