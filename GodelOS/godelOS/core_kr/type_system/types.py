"""
Type definitions for the GödelOS type system.

This module defines the various types used in the GödelOS type system,
including atomic types, function types, type variables, and parametric types.
"""

from typing import Dict, List, Optional, Set
from abc import ABC, abstractmethod


class Type(ABC):
    """
    Base class for all types in the GödelOS type system.
    """
    
    @abstractmethod
    def is_subtype_of(self, other_type: 'Type', type_system: 'TypeSystemManager') -> bool:
        """
        Check if this type is a subtype of another type.
        
        Args:
            other_type: The type to check against
            type_system: The type system manager to use for the check
            
        Returns:
            True if this type is a subtype of other_type, False otherwise
        """
        pass
    
    @abstractmethod
    def substitute_type_vars(self, bindings: Dict['TypeVariable', 'Type']) -> 'Type':
        """
        Substitute type variables in this type according to the given bindings.
        
        Args:
            bindings: A mapping from type variables to types
            
        Returns:
            A new type with the substitutions applied
        """
        pass


class AtomicType(Type):
    """
    A basic, non-decomposable type.
    
    Examples: Entity, Agent, Integer, Boolean, String.
    """
    
    def __init__(self, name: str):
        """
        Initialize an atomic type.
        
        Args:
            name: The name of the type
        """
        self._name = name
    
    @property
    def name(self) -> str:
        """Get the name of the type."""
        return self._name
    
    def is_subtype_of(self, other_type: 'Type', type_system: 'TypeSystemManager') -> bool:
        """
        Check if this atomic type is a subtype of another type.
        
        Args:
            other_type: The type to check against
            type_system: The type system manager to use for the check
            
        Returns:
            True if this type is a subtype of other_type, False otherwise
        """
        # An atomic type is a subtype of another type if:
        # 1. They are the same type
        # 2. The other type is also an atomic type and this type is a subtype of it in the hierarchy
        # 3. The other type is a type variable that can be bound to this type (handled by TypeVariable)
        
        if self == other_type:
            return True
            
        if isinstance(other_type, AtomicType):
            return type_system.is_subtype(self, other_type)
            
        return False
    
    def substitute_type_vars(self, bindings: Dict['TypeVariable', 'Type']) -> 'Type':
        """
        Substitute type variables in this type according to the given bindings.
        
        For atomic types, this is a no-op since they don't contain type variables.
        
        Args:
            bindings: A mapping from type variables to types
            
        Returns:
            This type unchanged
        """
        return self
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AtomicType):
            return False
        return self._name == other._name
    
    def __hash__(self) -> int:
        return hash(("AtomicType", self._name))
    
    def __str__(self) -> str:
        return self._name
    
    def __repr__(self) -> str:
        return f"AtomicType({self._name})"


class FunctionType(Type):
    """
    A type representing a function from argument types to a return type.
    
    Examples: (Entity, Entity) -> Boolean, () -> Integer.
    """
    
    def __init__(self, arg_types: List[Type], return_type: Type):
        """
        Initialize a function type.
        
        Args:
            arg_types: The types of the arguments
            return_type: The return type
        """
        self._arg_types = tuple(arg_types)  # Make immutable
        self._return_type = return_type
    
    @property
    def arg_types(self) -> List[Type]:
        """Get the argument types."""
        return list(self._arg_types)
    
    @property
    def return_type(self) -> Type:
        """Get the return type."""
        return self._return_type
    
    def is_subtype_of(self, other_type: 'Type', type_system: 'TypeSystemManager') -> bool:
        """
        Check if this function type is a subtype of another type.
        
        For function types, this follows the contravariant/covariant rule:
        (S1,...,Sn) -> T is a subtype of (R1,...,Rn) -> U if
        - R1 is a subtype of S1, ..., Rn is a subtype of Sn (contravariant in argument types)
        - T is a subtype of U (covariant in return type)
        
        Args:
            other_type: The type to check against
            type_system: The type system manager to use for the check
            
        Returns:
            True if this type is a subtype of other_type, False otherwise
        """
        # A function type is a subtype of another type if:
        # 1. They are the same type
        # 2. The other type is also a function type with the same number of arguments,
        #    and the subtyping relationship holds for arguments (contravariant) and return type (covariant)
        
        if self == other_type:
            return True
            
        if not isinstance(other_type, FunctionType):
            return False
        
        if len(self._arg_types) != len(other_type._arg_types):
            return False
        
        # Contravariant in argument types
        for i in range(len(self._arg_types)):
            if not other_type._arg_types[i].is_subtype_of(self._arg_types[i], type_system):
                return False
        
        # Covariant in return type
        return self._return_type.is_subtype_of(other_type._return_type, type_system)
    
    def substitute_type_vars(self, bindings: Dict['TypeVariable', 'Type']) -> 'Type':
        """
        Substitute type variables in this type according to the given bindings.
        
        Args:
            bindings: A mapping from type variables to types
            
        Returns:
            A new function type with the substitutions applied
        """
        new_arg_types = [arg_type.substitute_type_vars(bindings) for arg_type in self._arg_types]
        new_return_type = self._return_type.substitute_type_vars(bindings)
        return FunctionType(new_arg_types, new_return_type)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FunctionType):
            return False
        return (self._arg_types == other._arg_types and 
                self._return_type == other._return_type)
    
    def __hash__(self) -> int:
        return hash(("FunctionType", self._arg_types, self._return_type))
    
    def __str__(self) -> str:
        args_str = ", ".join(str(arg_type) for arg_type in self._arg_types)
        return f"({args_str}) -> {self._return_type}"
    
    def __repr__(self) -> str:
        return f"FunctionType({self._arg_types}, {self._return_type})"


class TypeVariable(Type):
    """
    A type variable, used for parametric polymorphism.
    
    Examples: ?T, ?U.
    """
    
    def __init__(self, name: str):
        """
        Initialize a type variable.
        
        Args:
            name: The name of the type variable
        """
        self._name = name
    
    @property
    def name(self) -> str:
        """Get the name of the type variable."""
        return self._name
    
    def is_subtype_of(self, other_type: 'Type', type_system: 'TypeSystemManager') -> bool:
        """
        Check if this type variable is a subtype of another type.
        
        A type variable is a subtype of another type if it is the same type variable.
        
        Args:
            other_type: The type to check against
            type_system: The type system manager to use for the check
            
        Returns:
            True if this type is a subtype of other_type, False otherwise
        """
        return self == other_type
    
    def substitute_type_vars(self, bindings: Dict['TypeVariable', 'Type']) -> 'Type':
        """
        Substitute this type variable according to the given bindings.
        
        Args:
            bindings: A mapping from type variables to types
            
        Returns:
            The type bound to this type variable, or this type variable if not bound
        """
        return bindings.get(self, self)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TypeVariable):
            return False
        return self._name == other._name
    
    def __hash__(self) -> int:
        return hash(("TypeVariable", self._name))
    
    def __str__(self) -> str:
        return f"?{self._name}"
    
    def __repr__(self) -> str:
        return f"TypeVariable({self._name})"


class ParametricType(Type):
    """
    Base class for parametric types.
    
    This is an abstract base class that serves as a common parent for
    ParametricTypeConstructor and InstantiatedParametricType.
    """
    
    def __init__(self, name: str, type_params: List['TypeVariable']):
        self._name = name
        self._type_params = tuple(type_params)
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def type_params(self) -> List['TypeVariable']:
        return list(self._type_params)
    
    def get_type_params(self) -> List['TypeVariable']:
        return list(self._type_params)
    
    def is_subtype_of(self, other_type: 'Type', type_system: 'TypeSystemManager') -> bool:
        return self == other_type
    
    def substitute_type_vars(self, bindings: Dict['TypeVariable', 'Type']) -> 'Type':
        return self
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, ParametricType) and self._name == other._name and self._type_params == other._type_params
    
    def __hash__(self) -> int:
        return hash(("ParametricType", self._name, self._type_params))
    
    def __str__(self) -> str:
        params_str = ", ".join(str(param) for param in self._type_params)
        return f"{self._name}[{params_str}]"
    
    def __repr__(self) -> str:
        return f"ParametricType({self._name}, {self._type_params})"


class ParametricTypeConstructor(ParametricType):
    """
    A type constructor for parametric types.
    
    Examples: List, Map, Option.
    """
    
    def __init__(self, name: str, type_params: List[TypeVariable]):
        """
        Initialize a parametric type constructor.
        
        Args:
            name: The name of the type constructor
            type_params: The type parameters
        """
        self._name = name
        self._type_params = tuple(type_params)  # Make immutable
    
    @property
    def name(self) -> str:
        """Get the name of the type constructor."""
        return self._name
    
    @property
    def type_params(self) -> List['TypeVariable']:
        """Get the type parameters."""
        return list(self._type_params)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ParametricTypeConstructor):
            return False
        return (self._name == other._name and 
                self._type_params == other._type_params)
    
    def __hash__(self) -> int:
        return hash(("ParametricTypeConstructor", self._name, self._type_params))
    
    def __str__(self) -> str:
        params_str = ", ".join(str(param) for param in self._type_params)
        return f"{self._name}[{params_str}]"
    
    def __repr__(self) -> str:
        return f"ParametricTypeConstructor({self._name}, {self._type_params})"
        
    def get_type_params(self) -> List['TypeVariable']:
        """
        Get the type parameters of this parametric type constructor.
        
        Returns:
            A list of type variables representing the type parameters
        """
        return list(self._type_params)


class InstantiatedParametricType(ParametricType):
    """
    A parametric type with concrete type arguments.
    
    Examples: List[Integer], Map[String, Entity].
    """
    
    def __init__(self, constructor: ParametricTypeConstructor, actual_type_args: List[Type]):
        """
        Initialize an instantiated parametric type.
        
        Args:
            constructor: The parametric type constructor
            actual_type_args: The actual type arguments
        """
        if len(actual_type_args) != len(constructor.type_params):
            raise ValueError(f"Expected {len(constructor.type_params)} type arguments, got {len(actual_type_args)}")
        
        self._constructor = constructor
        self._actual_type_args = tuple(actual_type_args)  # Make immutable
    
    @property
    def constructor(self) -> ParametricTypeConstructor:
        """Get the parametric type constructor."""
        return self._constructor
    
    @property
    def actual_type_args(self) -> List[Type]:
        """Get the actual type arguments."""
        return list(self._actual_type_args)
    
    def is_subtype_of(self, other_type: 'Type', type_system: 'TypeSystemManager') -> bool:
        """
        Check if this instantiated parametric type is a subtype of another type.
        
        Args:
            other_type: The type to check against
            type_system: The type system manager to use for the check
            
        Returns:
            True if this type is a subtype of other_type, False otherwise
        """
        # An instantiated parametric type is a subtype of another type if:
        # 1. They are the same type
        # 2. The other type is also an instantiated parametric type with the same constructor,
        #    and the type arguments are compatible according to their variance
        # 3. There's an explicit subtyping relationship defined in the type system
        
        if self == other_type:
            return True
            
        if isinstance(other_type, InstantiatedParametricType):
            if self._constructor != other_type._constructor:
                return False
            
            # Check if the type arguments are compatible
            # This depends on the variance of the type parameters
            # For simplicity, we assume invariance here (exact match required)
            if len(self._actual_type_args) != len(other_type._actual_type_args):
                return False
                
            for i in range(len(self._actual_type_args)):
                # For invariant parameters, types must be equal
                if self._actual_type_args[i] != other_type._actual_type_args[i]:
                    return False
            
            return True
        
        # Check if there's an explicit subtyping relationship in the type system
        return type_system.is_subtype(self, other_type)
    
    def substitute_type_vars(self, bindings: Dict['TypeVariable', 'Type']) -> 'Type':
        """
        Substitute type variables in this type according to the given bindings.
        
        Args:
            bindings: A mapping from type variables to types
            
        Returns:
            A new instantiated parametric type with the substitutions applied
        """
        new_type_args = [arg.substitute_type_vars(bindings) for arg in self._actual_type_args]
        return InstantiatedParametricType(self._constructor, new_type_args)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InstantiatedParametricType):
            return False
        return (self._constructor == other._constructor and 
                self._actual_type_args == other._actual_type_args)
    
    def __hash__(self) -> int:
        return hash(("InstantiatedParametricType", self._constructor, self._actual_type_args))
    
    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self._actual_type_args)
        return f"{self._constructor.name}[{args_str}]"
    
    def __repr__(self) -> str:
        return f"InstantiatedParametricType({self._constructor}, {self._actual_type_args})"
        
    def get_type_params(self) -> List['TypeVariable']:
        """
        Get the type parameters of this instantiated parametric type.
        
        Returns:
            A list of type variables representing the type parameters
        """
        return self._constructor.get_type_params()
