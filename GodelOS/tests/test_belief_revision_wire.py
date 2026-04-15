"""
Tests for the belief revision wire in _run_self_model_loop().

Covers:
  1. No belief revision module attached → wire is a safe no-op, loop still works.
  2. Belief revision module attached → revise_belief_set is called with correct args.
  3. Belief revision module raises → exception is swallowed, loop still works.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from godelOS.core_kr.ast.nodes import ConnectiveNode
from godelOS.symbol_grounding.prediction_error_tracker import PredictionErrorTracker
from godelOS.symbol_grounding.symbol_grounding_associator import (
    GroundingPredictionError,
)


def _make_tracker(error_norms):
    tracker = PredictionErrorTracker(window_size=200)
    for i, norm in enumerate(error_norms):
        tracker.record(
            GroundingPredictionError(
                symbol_ast_id=f"sym_{i}",
                modality="visual_features",
                timestamp=time.time() + i * 0.01,
                error_norm=norm,
            )
        )
    return tracker


def _make_engine():
    """Return a minimal UnifiedConsciousnessEngine with no WS/LLM."""
    from backend.core.unified_consciousness_engine import UnifiedConsciousnessEngine

    engine = UnifiedConsciousnessEngine(websocket_manager=None, llm_driver=None)
    # Pre-load tracker with high error so contradictions trigger
    engine._prediction_error_tracker = _make_tracker([0.55] * 30)
    return engine


# ── 1. No belief revision module → safe no-op ───────────────────────


@pytest.mark.unit
def test_self_model_loop_no_belief_revision():
    """Loop completes normally when _belief_revision is absent."""
    engine = _make_engine()
    # Ensure attribute does not exist
    assert not hasattr(engine, "_belief_revision") or engine._belief_revision is None
    # Should run without error
    engine._run_self_model_loop("I am certain about this answer.")
    # Feedback may or may not have been enqueued — just verify no crash


# ── 2. Belief revision module present → revise_belief_set called ─────


@pytest.mark.unit
def test_self_model_loop_belief_revision_called():
    """When _belief_revision is set, revise_belief_set is invoked."""
    engine = _make_engine()

    mock_br = MagicMock()
    engine._belief_revision = mock_br

    engine._run_self_model_loop("I am certain about this answer.")

    # The extractor should find at least one claim, triggering belief revision
    mock_br.revise_belief_set.assert_called()
    call_kwargs = mock_br.revise_belief_set.call_args.kwargs
    assert call_kwargs["belief_set_id"] == "SELF_MODEL_BELIEFS"
    assert isinstance(call_kwargs["new_belief_ast"], ConnectiveNode)
    assert call_kwargs["new_belief_ast"].connective_type == "NOT"
    # entrenchment_map value is the contradiction_score (a float)
    entrenchment_values = list(call_kwargs["entrenchment_map"].values())
    assert all(isinstance(v, float) for v in entrenchment_values)


# ── 3. Belief revision module raises → exception swallowed ───────────


@pytest.mark.unit
def test_self_model_loop_belief_revision_exception():
    """When belief revision module raises, the loop still completes."""
    engine = _make_engine()

    mock_br = MagicMock()
    mock_br.revise_belief_set.side_effect = RuntimeError("boom")
    engine._belief_revision = mock_br

    # Should not raise
    engine._run_self_model_loop("I am certain about this answer.")
