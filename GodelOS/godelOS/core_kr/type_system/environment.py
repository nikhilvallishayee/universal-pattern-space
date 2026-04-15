"""
Type environment for type checking and inference.

This module defines the TypeEnvironment class, which maps variables to their types
during type checking and inference.
"""

from typing import Dict, Optional

from godelOS.core_kr.ast.nodes import VariableNode
from godelOS.core_kr.type_system.types import Type


class TypeEnvironment:
    """
    A mapping from variables to their types during type checking/inference.
    """
    
    def __init__(self, parent: Optional['TypeEnvironment'] = None):
        """
        Initialize a type environment.
        
        Args:
            parent: Optional parent environment for nested scopes
        """
        self._bindings: Dict[int, Type] = {}  # Maps var_id to Type
        self._parent = parent
        self._symbol_bindings: Dict[str, Type] = {}
    
    def get_type(self, var_node: VariableNode) -> Optional[Type]:
        """
        Get the type of a variable.
        
        Args:
            var_node: The variable node
            
        Returns:
            The type of the variable, or None if not found
        """
        var_id = var_node.var_id
        if var_id in self._bindings:
            return self._bindings[var_id]
        elif self._parent:
            return self._parent.get_type(var_node)
        else:
            return None
    
    def set_type(self, var_node: VariableNode, type_obj: Type) -> None:
        """
        Set the type of a variable.
        
        Args:
            var_node: The variable node
            type_obj: The type to set
        """
        self._bindings[var_node.var_id] = type_obj
    
    # Symbol-based API used in enhanced tests
    def add_binding(self, symbol: str, type_obj: Type) -> None:
        """Add or override a binding for a symbol name."""
        self._symbol_bindings[symbol] = type_obj
    
    def lookup(self, symbol: str) -> Type:
        """Lookup a symbol name, searching parent environments if necessary."""
        if symbol in self._symbol_bindings:
            return self._symbol_bindings[symbol]
        if self._parent:
            return self._parent.lookup(symbol)
        raise KeyError(symbol)
    
    def extend(self) -> 'TypeEnvironment':
        """
        Create a new environment that extends this one.
        
        Returns:
            A new environment with this one as parent
        """
        return TypeEnvironment(self)
    
    def merge(self, other: 'TypeEnvironment') -> None:
        """
        Merge another environment into this one.
        
        Args:
            other: The environment to merge
        """
        self._bindings.update(other._bindings)
        self._symbol_bindings.update(other._symbol_bindings)
    
    def copy(self) -> 'TypeEnvironment':
        """
        Create a copy of this environment.
        
        Returns:
            A new environment with the same bindings and parent
        """
        env = TypeEnvironment(self._parent)
        env._bindings = self._bindings.copy()
        env._symbol_bindings = self._symbol_bindings.copy()
        return env
    
    def __str__(self) -> str:
        bindings_str = ", ".join(f"{var_id}: {type_obj}" for var_id, type_obj in self._bindings.items())
        symbol_str = ", ".join(f"{name}: {type_obj}" for name, type_obj in self._symbol_bindings.items())
        if symbol_str:
            bindings_str = ", ".join(filter(None, [bindings_str, symbol_str]))
        parent_str = f" -> {self._parent}" if self._parent else ""
        return f"{{{bindings_str}}}{parent_str}"
    
    def __repr__(self) -> str:
        return f"TypeEnvironment({self._bindings}, parent={self._parent})"
