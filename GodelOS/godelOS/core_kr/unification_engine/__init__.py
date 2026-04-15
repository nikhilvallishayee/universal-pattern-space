"""
Unification Engine.

This module is responsible for determining if two logical expressions (ASTs)
can be made syntactically identical by substituting variables with terms.
"""

from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.unification_engine.result import UnificationResult, Error

__all__ = ["UnificationEngine", "UnificationResult", "Error"]