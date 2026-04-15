#!/usr/bin/env python3
"""
Tests for the self-referential GödelOS architecture components:

1. Phenomenal Surprise (Pn) — prediction error in self-modeling
2. Internal Observer Self-Model — SelfModelState tracking
3. Phase Transition Detection — qualitative shifts in coherence
4. State-Change Narration — converting state deltas into text
"""

import asyncio
import math
import pytest
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.phenomenal_experience import (
    PhenomenalExperienceGenerator,
    PhenomenalSurprise,
    ExperienceType,
)
from backend.core.metacognitive_monitor import (
    MetaCognitiveMonitor,
    SelfModelState,
)
from backend.core.unified_consciousness_engine import (
    UnifiedConsciousnessEngine,
    UnifiedConsciousnessState,
    PhaseTransition,
)


# ---------------------------------------------------------------------------
# Phenomenal Surprise (Pn)
# ---------------------------------------------------------------------------

class TestPhenomenalSurprise:
    """Validate that prediction error / surprise is computed correctly."""

    @pytest.fixture
    def generator(self):
        return PhenomenalExperienceGenerator()

    @pytest.mark.asyncio
    async def test_first_experience_has_no_surprise(self, generator):
        """The very first experience cannot be compared — surprise is None."""
        exp = await generator.generate_experience(
            {"source": "test", "importance": 0.5}
        )
        assert exp is not None
        # First experience: no prior prediction, so no surprise recorded
        assert generator.get_current_surprise() is None

    @pytest.mark.asyncio
    async def test_second_experience_produces_surprise(self, generator):
        """After one experience a prediction exists, so surprise is recorded."""
        await generator.generate_experience({"source": "test", "importance": 0.5})
        await generator.generate_experience({"source": "test", "importance": 0.5})
        surprise = generator.get_current_surprise()
        assert surprise is not None
        assert 0.0 <= surprise <= 1.0

    @pytest.mark.asyncio
    async def test_surprise_history_grows(self, generator):
        """Each experience after the first adds one entry to surprise_history."""
        for i in range(5):
            await generator.generate_experience({"source": "test", "importance": 0.3 + i * 0.1})
        history = generator.get_surprise_history()
        # First has no surprise, so 4 entries
        assert len(history) == 4
        for s in history:
            assert isinstance(s, PhenomenalSurprise)
            assert 0.0 <= s.surprise_value <= 1.0
            assert set(s.feature_errors.keys()) == {"intensity", "valence", "coherence", "vividness"}

    @pytest.mark.asyncio
    async def test_identical_context_yields_low_surprise(self, generator):
        """Repeated identical contexts should converge to low surprise."""
        ctx = {"source": "test", "importance": 0.5, "novelty": 0.5}
        for _ in range(10):
            await generator.generate_experience(ctx)
        recent = generator.get_surprise_history(limit=3)
        # With identical inputs the generator should produce very similar
        # experiences, so surprise should be low after warmup.
        for s in recent:
            assert s.surprise_value < 0.5

    @pytest.mark.asyncio
    async def test_surprise_has_valid_features(self, generator):
        """Predicted and actual features should contain all canonical keys."""
        await generator.generate_experience({"source": "a"})
        await generator.generate_experience({"source": "b"})
        s = generator.surprise_history[-1]
        for key in PhenomenalExperienceGenerator._FEATURE_KEYS:
            assert key in s.predicted_features
            assert key in s.actual_features


# ---------------------------------------------------------------------------
# Internal Observer Self-Model
# ---------------------------------------------------------------------------

class TestSelfModelState:
    """Validate the MetaCognitiveMonitor self-model tracking."""

    @pytest.fixture
    def monitor(self):
        return MetaCognitiveMonitor()

    def test_initial_update_accuracy_is_one(self, monitor):
        """First update has no prior prediction — accuracy defaults to 1.0."""
        snap = monitor.update_self_model()
        assert isinstance(snap, SelfModelState)
        assert snap.accuracy == 1.0
        assert monitor.get_self_model_accuracy() == 1.0

    def test_self_model_accuracy_updates(self, monitor):
        """After modifying state between updates, accuracy reflects the error."""
        monitor.update_self_model()
        # Manually perturb the state to create a prediction mismatch
        monitor.current_state.self_awareness_level = 0.9
        monitor.current_state.reflection_depth = 4
        snap = monitor.update_self_model()
        assert 0.0 <= snap.accuracy <= 1.0
        # Because state changed significantly vs. prediction, accuracy < 1
        assert snap.accuracy < 1.0

    def test_self_model_history_grows(self, monitor):
        """Each call to update_self_model appends to history."""
        for _ in range(5):
            monitor.update_self_model()
        assert len(monitor.self_model_history) == 5

    def test_observed_keys(self, monitor):
        """Observed dict contains the expected metric keys."""
        snap = monitor.update_self_model()
        for k in MetaCognitiveMonitor._SELF_MODEL_KEYS:
            assert k in snap.observed

    @pytest.mark.asyncio
    async def test_self_model_after_monitoring(self, monitor):
        """update_self_model works after initiate_self_monitoring."""
        await monitor.initiate_self_monitoring({"query": "test"})
        snap = monitor.update_self_model()
        assert isinstance(snap, SelfModelState)
        assert 0.0 <= snap.accuracy <= 1.0


# ---------------------------------------------------------------------------
# Phase Transition Detection
# ---------------------------------------------------------------------------

class TestPhaseTransitionDetection:
    """Validate phase transition detection in UnifiedConsciousnessEngine."""

    @pytest.fixture
    def engine(self):
        return UnifiedConsciousnessEngine()

    def test_no_transition_on_empty_history(self, engine):
        """No history ⇒ no transition."""
        state = UnifiedConsciousnessState()
        state.consciousness_score = 0.5
        assert engine.detect_phase_transition(state) is None

    def test_transition_detected_on_score_jump(self, engine):
        """A big score jump across a threshold should trigger a transition."""
        # Put a sub-critical state in history (below 0.12 threshold)
        prev = UnifiedConsciousnessState()
        prev.consciousness_score = 0.05
        engine.consciousness_history.append(prev)

        # Now create a super-critical state (above 0.35 threshold)
        curr = UnifiedConsciousnessState()
        curr.consciousness_score = 0.70
        transition = engine.detect_phase_transition(curr)
        assert transition is not None
        assert isinstance(transition, PhaseTransition)
        assert transition.from_phase == "sub-critical"
        assert transition.to_phase == "super-critical"
        assert transition.rate_of_change > 0

    def test_no_transition_within_same_phase(self, engine):
        """Small fluctuations within a phase should not trigger."""
        prev = UnifiedConsciousnessState()
        prev.consciousness_score = 0.50
        engine.consciousness_history.append(prev)

        curr = UnifiedConsciousnessState()
        curr.consciousness_score = 0.55
        assert engine.detect_phase_transition(curr) is None

    def test_transition_below_slope_not_detected(self, engine):
        """When slope is below minimum, even cross-threshold is ignored."""
        prev = UnifiedConsciousnessState()
        prev.consciousness_score = 0.349  # just below 0.35
        engine.consciousness_history.append(prev)

        curr = UnifiedConsciousnessState()
        curr.consciousness_score = 0.351  # just above 0.35
        assert engine.detect_phase_transition(curr) is None

    def test_phase_classification(self, engine):
        """Verify _classify_phase boundaries match engine thresholds (0.12, 0.35)."""
        assert engine._classify_phase(0.0) == "sub-critical"
        assert engine._classify_phase(0.11) == "sub-critical"
        assert engine._classify_phase(0.12) == "critical"
        assert engine._classify_phase(0.34) == "critical"
        assert engine._classify_phase(0.35) == "super-critical"
        assert engine._classify_phase(1.0) == "super-critical"

    def test_get_phase_transitions(self, engine):
        """get_phase_transitions returns recorded transitions."""
        prev = UnifiedConsciousnessState()
        prev.consciousness_score = 0.30
        engine.consciousness_history.append(prev)

        curr = UnifiedConsciousnessState()
        curr.consciousness_score = 0.70
        engine.detect_phase_transition(curr)
        pts = engine.get_phase_transitions()
        assert len(pts) == 1
        assert pts[0].narrative  # non-empty narrative


# ---------------------------------------------------------------------------
# State-Change Narration
# ---------------------------------------------------------------------------

class TestStateChangeNarration:
    """Validate that internal state changes produce textual narratives."""

    @pytest.fixture
    def engine(self):
        return UnifiedConsciousnessEngine()

    def test_no_narration_on_empty_history(self, engine):
        """Without history, nothing to narrate."""
        state = UnifiedConsciousnessState()
        assert engine.generate_state_change_narrative(state) is None

    def test_narration_on_score_change(self, engine):
        """A change in consciousness score should produce a narrative."""
        prev = UnifiedConsciousnessState()
        prev.consciousness_score = 0.50
        engine.consciousness_history.append(prev)

        curr = UnifiedConsciousnessState()
        curr.consciousness_score = 0.60
        entry = engine.generate_state_change_narrative(curr)
        assert entry is not None
        assert "rising" in entry["narrative"]
        assert entry["deltas"]["consciousness_score"] == pytest.approx(0.10, abs=1e-6)

    def test_narration_on_depth_change(self, engine):
        """A change in recursive depth triggers narration."""
        prev = UnifiedConsciousnessState()
        prev.consciousness_score = 0.50
        engine.consciousness_history.append(prev)

        curr = UnifiedConsciousnessState()
        curr.consciousness_score = 0.50
        curr.recursive_awareness["recursive_depth"] = 3
        entry = engine.generate_state_change_narrative(curr)
        assert entry is not None
        assert "deepening" in entry["narrative"]

    def test_no_narration_on_trivial_change(self, engine):
        """Tiny changes below threshold should not produce narration."""
        prev = UnifiedConsciousnessState()
        prev.consciousness_score = 0.500
        engine.consciousness_history.append(prev)

        curr = UnifiedConsciousnessState()
        curr.consciousness_score = 0.501
        assert engine.generate_state_change_narrative(curr) is None

    def test_narration_history_accumulates(self, engine):
        """Multiple noteworthy changes should accumulate narratives."""
        for score in [0.40, 0.50, 0.60, 0.70]:
            state = UnifiedConsciousnessState()
            state.consciousness_score = score
            engine.generate_state_change_narrative(state)
            engine.consciousness_history.append(state)

        narratives = engine.get_state_change_narratives()
        # First state has no prior → no narrative; rest should have one each
        assert len(narratives) == 3

    def test_get_state_change_narratives_with_limit(self, engine):
        """Limit parameter works as expected."""
        for score in [0.30, 0.50, 0.70, 0.90]:
            state = UnifiedConsciousnessState()
            state.consciousness_score = score
            engine.generate_state_change_narrative(state)
            engine.consciousness_history.append(state)

        assert len(engine.get_state_change_narratives(limit=2)) == 2
