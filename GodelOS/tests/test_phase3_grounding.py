"""
Phase 3 integration tests — verify that fabricated measurements have been
replaced with real empirical data from ``PredictionErrorTracker``.

Run together with the earlier Phase-2 tests:

    pytest tests/test_phase3_integration.py \
           tests/test_grounding_prediction_error.py \
           tests/test_prediction_error_tracker.py -v
"""

import logging
import time
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field

from godelOS.symbol_grounding.symbol_grounding_associator import GroundingPredictionError
from godelOS.symbol_grounding.prediction_error_tracker import PredictionErrorTracker

from backend.core.phenomenal_experience import (
    PhenomenalExperienceGenerator,
    PhenomenalExperience,
    PhenomenalSurprise,
    QualiaPattern,
    QualiaModality,
    ExperienceType,
)
from backend.core.metacognitive_monitor import MetaCognitiveMonitor
from backend.core.unified_consciousness_engine import (
    UnifiedConsciousnessEngine,
    UnifiedConsciousnessState,
    PhaseTransition,
)


# ── helpers ───────────────────────────────────────────────────────────────

def _make_tracker(error_norms, sufficient=True, min_samples=20):
    """Build a PredictionErrorTracker pre-loaded with known error_norms."""
    tracker = PredictionErrorTracker(window_size=200)
    t = time.time()
    for i, norm in enumerate(error_norms):
        rec = GroundingPredictionError(
            symbol_ast_id=f"sym_{i % 5}",
            modality="visual",
            timestamp=t + i,
            error_norm=norm,
        )
        tracker.record(rec)
    return tracker


def _make_experience(**kwargs):
    """Build a minimal ``PhenomenalExperience`` for test purposes."""
    defaults = dict(
        id="test-exp",
        experience_type=ExperienceType.COGNITIVE,
        qualia_patterns=[
            QualiaPattern(
                id="qp-1",
                modality=QualiaModality.CONCEPTUAL,
                intensity=0.5,
                valence=0.0,
                complexity=0.5,
                duration=1.0,
            )
        ],
        coherence=0.7,
        vividness=0.6,
        attention_focus=0.5,
        background_context={},
        narrative_description="test",
        temporal_extent=(0.0, 1.0),
        causal_triggers=[],
        associated_concepts=[],
    )
    defaults.update(kwargs)
    return PhenomenalExperience(**defaults)


# ── Test 1: Phenomenal surprise uses tracker when available ──────────────

class TestPhenomenalSurpriseUsesTracker:
    def test_surprise_value_equals_tracker_mean(self):
        """When tracker is present and sufficient, surprise_value == tracker.mean_error_norm()."""
        norms = [0.10] * 25  # mean = 0.10
        tracker = _make_tracker(norms)
        gen = PhenomenalExperienceGenerator(prediction_error_tracker=tracker)
        # We need _predicted_features set (simulating a prior experience)
        gen._predicted_features = {"intensity": 0.5, "valence": 0.0, "coherence": 0.7, "vividness": 0.6}

        exp = _make_experience()
        surprise = gen._compute_phenomenal_surprise(exp)

        assert surprise is not None
        assert abs(surprise.surprise_value - 0.10) < 1e-9


# ── Test 2: Phenomenal surprise falls back gracefully ────────────────────

class TestPhenomenalSurpriseFallback:
    def test_fallback_logs_warning(self, caplog):
        """Without tracker, EMA fallback runs and logs a fabrication warning."""
        gen = PhenomenalExperienceGenerator()
        gen._predicted_features = {"intensity": 0.5, "valence": 0.0, "coherence": 0.7, "vividness": 0.6}
        exp = _make_experience()

        with caplog.at_level(logging.WARNING):
            surprise = gen._compute_phenomenal_surprise(exp)

        assert surprise is not None
        assert "fabricated qualia fallback" in caplog.text


# ── Test 3: Phase transition uses empirical thresholds ───────────────────

class TestPhaseTransitionEmpiricalThresholds:
    def test_super_critical_with_high_error(self):
        """Tracker shows transition to super-critical when error rises above 0.35."""
        # First half sub-critical, second half super-critical → transition detected
        norms = [0.05] * 13 + [0.40] * 12  # 25 total
        tracker = _make_tracker(norms)
        engine = UnifiedConsciousnessEngine()
        engine._prediction_error_tracker = tracker

        # Need a previous state in history
        prev_state = UnifiedConsciousnessState()
        prev_state.consciousness_score = 0.05
        engine.consciousness_history.append(prev_state)

        curr_state = UnifiedConsciousnessState()
        curr_state.consciousness_score = 0.50

        transition = engine.detect_phase_transition(curr_state)
        assert transition is not None
        assert transition.to_phase == "super-critical"
        assert transition.threshold_source == "empirical_bimodal_phase2"

    def test_sub_critical_with_low_error(self):
        """Tracker shows transition to sub-critical when error drops below 0.12."""
        # First half super-critical, second half sub-critical → transition detected
        norms = [0.40] * 13 + [0.06] * 12  # 25 total
        tracker = _make_tracker(norms)
        engine = UnifiedConsciousnessEngine()
        engine._prediction_error_tracker = tracker

        # Previous state must be in a different phase
        prev_state = UnifiedConsciousnessState()
        prev_state.consciousness_score = 0.50
        engine.consciousness_history.append(prev_state)

        curr_state = UnifiedConsciousnessState()
        curr_state.consciousness_score = 0.01

        transition = engine.detect_phase_transition(curr_state)
        assert transition is not None
        assert transition.to_phase == "sub-critical"
        assert transition.threshold_source == "empirical_bimodal_phase2"

    def test_heuristic_fallback_without_tracker(self):
        """Without tracker, fallback uses consciousness_score and heuristic source."""
        engine = UnifiedConsciousnessEngine()

        prev_state = UnifiedConsciousnessState()
        prev_state.consciousness_score = 0.05
        engine.consciousness_history.append(prev_state)

        curr_state = UnifiedConsciousnessState()
        curr_state.consciousness_score = 0.50  # > 0.35 threshold

        transition = engine.detect_phase_transition(curr_state)
        assert transition is not None
        assert transition.threshold_source == "heuristic_fallback"


# ── Test 4: Self-model accuracy tracks second-order error ────────────────

class TestSelfModelSecondOrderError:
    def test_accuracy_reflects_prediction_error_on_mean(self):
        """After two update_self_model() calls, accuracy reflects second-order error."""
        # Use a small window so we can fully replace the data
        tracker = PredictionErrorTracker(window_size=25)
        t = time.time()
        # Fill with mean=0.10
        for i in range(25):
            tracker.record(GroundingPredictionError(
                symbol_ast_id=f"sym_{i % 5}",
                modality="visual",
                timestamp=t + i,
                error_norm=0.10,
            ))
        monitor = MetaCognitiveMonitor(prediction_error_tracker=tracker)

        # First call — no prior prediction, accuracy = 1.0
        snap1 = monitor.update_self_model()
        assert snap1.accuracy == 1.0

        # Now fully replace the tracker data so mean is 0.20
        for i in range(25):
            tracker.record(GroundingPredictionError(
                symbol_ast_id=f"sym_{i % 5}",
                modality="visual",
                timestamp=t + 100 + i,
                error_norm=0.20,
            ))

        # Second call — predicted was 0.10, observed is now 0.20
        snap2 = monitor.update_self_model()
        # second_order_error = |0.20 - 0.10| = 0.10
        # accuracy = max(0, 1.0 - 0.10/0.35) ≈ 0.714
        expected = max(0.0, 1.0 - (0.10 / 0.35))
        assert abs(snap2.accuracy - expected) < 0.02

    def test_fallback_without_tracker(self):
        """Without tracker, self-model accuracy uses internal consistency."""
        monitor = MetaCognitiveMonitor()
        snap = monitor.update_self_model()
        assert snap.accuracy == 1.0  # first cycle default


# ── Test 5: is_grounded property ─────────────────────────────────────────

class TestIsGrounded:
    def test_false_without_tracker(self):
        gen = PhenomenalExperienceGenerator()
        assert gen.is_grounded is False

    def test_false_with_insufficient_tracker(self):
        tracker = _make_tracker([0.10] * 5)  # only 5 samples, min=20
        gen = PhenomenalExperienceGenerator(prediction_error_tracker=tracker)
        assert gen.is_grounded is False

    def test_true_with_sufficient_tracker(self):
        tracker = _make_tracker([0.10] * 25)
        gen = PhenomenalExperienceGenerator(prediction_error_tracker=tracker)
        assert gen.is_grounded is True
