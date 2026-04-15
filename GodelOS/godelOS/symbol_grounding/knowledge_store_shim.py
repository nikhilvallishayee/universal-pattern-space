"""
Knowledge Store Shim — intercepts ``add_statement()`` calls on a
``KnowledgeStoreInterface`` to measure symbol prediction error at
activation time and feed results into ``PredictionErrorTracker``.

This module never modifies the underlying knowledge store or the
grounder — it is a transparent wrapper whose measurement activity
is always secondary to correct statement insertion.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from godelOS.core_kr.ast.nodes import AST_Node, ApplicationNode, ConstantNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.symbol_grounding.prediction_error_tracker import PredictionErrorTracker
from godelOS.symbol_grounding.symbol_grounding_associator import SymbolGroundingAssociator

logger = logging.getLogger(__name__)


class KnowledgeStoreShim:
    """Transparent wrapper around ``KnowledgeStoreInterface`` that
    intercepts ``add_statement()`` to drive grounding prediction-error
    measurement.

    All methods other than ``add_statement()`` are delegated unchanged
    to the base instance via ``__getattr__``.
    """

    def __init__(
        self,
        base: KnowledgeStoreInterface,
        grounder: SymbolGroundingAssociator,
        tracker: PredictionErrorTracker,
    ) -> None:
        self._base = base
        self._grounder = grounder
        self._tracker = tracker

        # Observation context for the next activation measurement
        self._observed_features: Optional[Dict[str, Any]] = None
        self._modality: str = "visual_features"

        # Internal counters
        self._measurements_recorded: int = 0
        self._skipped_no_context: int = 0
        self._skipped_cold_start: int = 0

    # ── delegation ────────────────────────────────────────────────────

    def __getattr__(self, name: str) -> Any:
        """Delegate every attribute not explicitly defined to the base."""
        return getattr(self._base, name)

    # ── intercepted method ────────────────────────────────────────────

    def add_statement(self, *args: Any, **kwargs: Any) -> bool:
        """Delegate to the base, then attempt a grounding measurement."""
        result = self._base.add_statement(*args, **kwargs)

        try:
            self._measure(args, kwargs)
        except Exception:
            logger.warning(
                "KnowledgeStoreShim: measurement failed — continuing",
                exc_info=True,
            )

        return result

    # ── observation context ───────────────────────────────────────────

    def set_observation_context(
        self,
        observed_features: Dict[str, Any],
        modality: str = "visual_features",
    ) -> None:
        """Set the observation features for the next activation measurement."""
        self._observed_features = observed_features
        self._modality = modality

    def clear_observation_context(self) -> None:
        """Clear the observation context."""
        self._observed_features = None

    # ── stats ─────────────────────────────────────────────────────────

    @property
    def tracker(self) -> PredictionErrorTracker:
        """Public accessor for the underlying tracker."""
        return self._tracker

    @property
    def measurement_stats(self) -> Dict[str, int]:
        return {
            "measurements_recorded": self._measurements_recorded,
            "skipped_no_context": self._skipped_no_context,
            "skipped_cold_start": self._skipped_cold_start,
        }

    # ── internals ─────────────────────────────────────────────────────

    def _measure(self, args: tuple, kwargs: dict) -> None:
        """Attempt to measure prediction error for the added statement."""
        if self._observed_features is None:
            self._skipped_no_context += 1
            return

        # Extract symbol AST ID from the statement
        statement_ast = args[0] if args else kwargs.get("statement_ast")
        symbol_id = self._extract_symbol_id(statement_ast)
        if symbol_id is None:
            self._skipped_no_context += 1
            return

        error = self._grounder.measure_prediction_error_at_activation(
            symbol_id, self._observed_features, self._modality
        )

        if error is None:
            # Cold start — no grounding link for this symbol/modality
            self._skipped_cold_start += 1
            return

        self._tracker.record(error)
        self._measurements_recorded += 1
        logger.debug("SGQ(%s, t) = %.4f", symbol_id, error.error_norm)

    @staticmethod
    def _extract_symbol_id(statement_ast: Optional[AST_Node]) -> Optional[str]:
        """Best-effort extraction of a symbol identifier from an AST node.

        * ``ApplicationNode`` → the operator's ``.name`` (predicate name).
        * ``ConstantNode`` → the constant's ``.name``.
        * Everything else → ``None`` (cold-start handling covers this).
        """
        if statement_ast is None:
            return None
        if isinstance(statement_ast, ApplicationNode):
            op = statement_ast.operator
            if hasattr(op, "name"):
                return op.name
            return None
        if isinstance(statement_ast, ConstantNode):
            return statement_ast.name
        # Fallback: try a generic .name attribute
        if hasattr(statement_ast, "name"):
            return statement_ast.name
        return None
