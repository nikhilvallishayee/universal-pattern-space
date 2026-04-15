"""
Belief Revision System.

This module manages changes to the agent's belief set in a rational and consistent
manner when new information arrives, especially if it contradicts existing beliefs.

The system implements belief revision postulates (AGM postulates) and supports
operations like expansion, contraction, and revision. It also provides support
for argumentation frameworks for defeasible reasoning.
"""

from godelOS.core_kr.belief_revision.system import (
    BeliefRevisionSystem,
    RevisionStrategy,
    Argument,
    ArgumentationFramework
)

__all__ = [
    "BeliefRevisionSystem",
    "RevisionStrategy",
    "Argument",
    "ArgumentationFramework"
]