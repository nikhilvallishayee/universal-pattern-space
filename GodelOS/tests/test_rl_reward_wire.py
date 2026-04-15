"""
Tests for the RL reward wire in _run_self_model_loop().

Covers:
  1. No RL module attached → wire is a safe no-op, loop still works.
  2. RL module attached → learn_from_transition is called with correct args.
  3. RL module raises → exception is swallowed, loop still works.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

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


# ── 1. No RL module → safe no-op ────────────────────────────────────


@pytest.mark.unit
def test_self_model_loop_no_rl_module():
    """Loop completes normally when _meta_control_rl is absent."""
    engine = _make_engine()
    # Ensure attribute does not exist
    assert not hasattr(engine, "_meta_control_rl") or engine._meta_control_rl is None
    # Should run without error
    engine._run_self_model_loop("I am certain about this answer.")
    # Feedback may or may not have been enqueued — just verify no crash


# ── 2. RL module present → learn_from_transition called ──────────────


@pytest.mark.unit
def test_self_model_loop_rl_module_called():
    """When _meta_control_rl is set, learn_from_transition is invoked."""
    engine = _make_engine()

    mock_rl = MagicMock()
    mock_rl.get_state_features.return_value = [0.1, 0.2, 0.3]
    engine._meta_control_rl = mock_rl

    engine._run_self_model_loop("I am certain about this answer.")

    # The extractor should find at least one claim, triggering RL
    mock_rl.learn_from_transition.assert_called()
    call_kwargs = mock_rl.learn_from_transition.call_args.kwargs
    # reward is -contradiction_score (negative value)
    assert call_kwargs["reward"] <= 0
    assert call_kwargs["episode_done"] is False


# ── 3. RL module raises → exception swallowed ───────────────────────


@pytest.mark.unit
def test_self_model_loop_rl_module_exception():
    """When RL module raises, the loop still completes."""
    engine = _make_engine()

    mock_rl = MagicMock()
    mock_rl.get_state_features.side_effect = RuntimeError("boom")
    engine._meta_control_rl = mock_rl

    # Should not raise
    engine._run_self_model_loop("I am certain about this answer.")
