"""
Core Knowledge Representation (KR) System.

This module is the heart of GödelOS, responsible for representing, storing,
and managing all forms of knowledge. It defines the syntax and semantics of
the agent's internal language and provides foundational operations for
knowledge manipulation.
"""

from godelOS.core_kr.ast import AST_Node
from godelOS.core_kr.formal_logic_parser import FormalLogicParser
from godelOS.core_kr.type_system import TypeSystemManager
from godelOS.core_kr.unification_engine import UnificationEngine
from godelOS.core_kr.knowledge_store import KnowledgeStoreInterface
from godelOS.core_kr.probabilistic_logic import ProbabilisticLogicModule
from godelOS.core_kr.belief_revision import BeliefRevisionSystem

__all__ = [
    "AST_Node",
    "FormalLogicParser",
    "TypeSystemManager",
    "UnificationEngine",
    "KnowledgeStoreInterface",
    "ProbabilisticLogicModule",
    "BeliefRevisionSystem",
]