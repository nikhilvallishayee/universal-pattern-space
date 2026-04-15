"""
Type System Manager.

This module defines and manages the type hierarchy and performs type checking and inference.
"""

from godelOS.core_kr.type_system.types import (
    Type,
    AtomicType,
    FunctionType,
    TypeVariable,
    ParametricTypeConstructor,
    InstantiatedParametricType,
)
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.environment import TypeEnvironment
from godelOS.core_kr.type_system.visitor import (
    Error,
    TypeInferenceVisitor,
    TypeCheckingVisitor,
)

__all__ = [
    "Type",
    "AtomicType",
    "FunctionType",
    "TypeVariable",
    "ParametricTypeConstructor",
    "InstantiatedParametricType",
    "TypeSystemManager",
    "TypeEnvironment",
    "Error",
    "TypeInferenceVisitor",
    "TypeCheckingVisitor",
]